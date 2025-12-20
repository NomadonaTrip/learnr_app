"""
Integration tests for concept prerequisites.
Tests database constraints, API endpoints, and response times.
"""
import time
from uuid import uuid4

import pytest
from sqlalchemy import text

from src.models.concept import Concept
from src.models.concept_prerequisite import ConceptPrerequisite
from src.models.course import Course
from src.models.user import User
from src.repositories.concept_repository import ConceptRepository


@pytest.fixture
async def test_course(db_session, sample_course_data):
    """Create a test course."""
    course = Course(
        slug=f"test-{uuid4().hex[:8]}",
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts with prerequisites."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            description=f"Description for concept {i}",
            corpus_section_ref=f"3.{i}.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.2 + (i * 0.15),
            prerequisite_depth=i  # For testing
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def test_user(db_session):
    """Create a test user for authentication."""
    user = User(
        email=f"testuser-{uuid4().hex[:8]}@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.M1E0pV6SyqV9Gy"  # "password123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user):
    """Generate auth token for test user."""
    from src.utils.auth import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDatabaseConstraints:
    """Tests for database constraint enforcement."""

    @pytest.mark.asyncio
    async def test_table_creation(self, db_session):
        """Test that concept_prerequisites table is created."""
        result = await db_session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'concept_prerequisites'
            )
        """))
        exists = result.scalar()
        assert exists is True

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_concept(self, db_session, test_concepts):
        """Test that concept_id FK is enforced."""
        fake_id = uuid4()
        prereq = ConceptPrerequisite(
            concept_id=fake_id,  # Non-existent
            prerequisite_concept_id=test_concepts[0].id,
            strength=0.8,
            relationship_type="required"
        )
        db_session.add(prereq)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_prerequisite(self, db_session, test_concepts):
        """Test that prerequisite_concept_id FK is enforced."""
        fake_id = uuid4()
        prereq = ConceptPrerequisite(
            concept_id=test_concepts[0].id,
            prerequisite_concept_id=fake_id,  # Non-existent
            strength=0.8,
            relationship_type="required"
        )
        db_session.add(prereq)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="CHECK constraint only exists when using migrations, not Base.metadata.create_all()")
    async def test_self_loop_prevention(self, db_session, test_concepts):
        """Test that self-loops are prevented by CHECK constraint."""
        from sqlalchemy.exc import IntegrityError

        prereq = ConceptPrerequisite(
            concept_id=test_concepts[0].id,
            prerequisite_concept_id=test_concepts[0].id,  # Self-loop
            strength=0.8,
            relationship_type="required"
        )
        db_session.add(prereq)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_unique_constraint(self, db_session, test_concepts):
        """Test that duplicate relationships are prevented."""
        repo = ConceptRepository(db_session)

        # Add first relationship
        await repo.add_prerequisite(
            test_concepts[1].id, test_concepts[0].id, 0.8, "required"
        )
        await db_session.commit()

        # Try to add duplicate
        prereq = ConceptPrerequisite(
            concept_id=test_concepts[1].id,
            prerequisite_concept_id=test_concepts[0].id,
            strength=0.5,
            relationship_type="helpful"
        )
        db_session.add(prereq)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="CHECK constraint only exists when using migrations, not Base.metadata.create_all()")
    async def test_strength_range_constraint(self, db_session, test_concepts):
        """Test that strength is constrained to 0.0-1.0."""
        from sqlalchemy.exc import IntegrityError

        prereq = ConceptPrerequisite(
            concept_id=test_concepts[1].id,
            prerequisite_concept_id=test_concepts[0].id,
            strength=1.5,  # Out of range
            relationship_type="required"
        )
        db_session.add(prereq)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="CHECK constraint only exists when using migrations, not Base.metadata.create_all()")
    async def test_relationship_type_constraint(self, db_session, test_concepts):
        """Test that relationship_type is constrained to valid values."""
        from sqlalchemy.exc import IntegrityError

        prereq = ConceptPrerequisite(
            concept_id=test_concepts[1].id,
            prerequisite_concept_id=test_concepts[0].id,
            strength=0.8,
            relationship_type="invalid_type"  # Invalid
        )
        db_session.add(prereq)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_cascade_delete_concept(self, db_session, test_course, test_concepts):
        """Test that deleting a concept cascades to prerequisites."""
        repo = ConceptRepository(db_session)

        # Create prerequisites
        await repo.add_prerequisite(
            test_concepts[1].id, test_concepts[0].id, 0.8, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[0].id, 0.7, "helpful"
        )
        await db_session.commit()

        # Verify prerequisites exist
        prereqs_before = await repo.get_all_prerequisites_for_course(test_course.id)
        assert len(prereqs_before) == 2

        # Delete the concept that is a prerequisite
        await db_session.delete(test_concepts[0])
        await db_session.commit()

        # Prerequisites should be deleted
        prereqs_after = await repo.get_all_prerequisites_for_course(test_course.id)
        assert len(prereqs_after) == 0


class TestAPIEndpoints:
    """Tests for concept prerequisites API endpoints."""

    @pytest.mark.asyncio
    async def test_get_prerequisites_endpoint(
        self, client, db_session, test_concepts, auth_headers
    ):
        """Test GET /v1/concepts/{id}/prerequisites endpoint."""
        repo = ConceptRepository(db_session)

        # Create prerequisites
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[0].id, 0.9, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[1].id, 0.7, "helpful"
        )
        await db_session.commit()

        response = await client.get(
            f"/v1/concepts/{test_concepts[2].id}/prerequisites",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_prerequisites_not_found(self, client, auth_headers):
        """Test that 404 is returned for non-existent concept."""
        fake_id = uuid4()
        response = await client.get(
            f"/v1/concepts/{fake_id}/prerequisites",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_prerequisites_requires_auth(self, client, test_concepts):
        """Test that prerequisites endpoint requires authentication."""
        response = await client.get(
            f"/v1/concepts/{test_concepts[0].id}/prerequisites"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_prerequisite_chain_endpoint(
        self, client, db_session, test_concepts, auth_headers
    ):
        """Test GET /v1/concepts/{id}/prerequisites/chain endpoint."""
        repo = ConceptRepository(db_session)

        # Build chain: A <- B <- C <- D
        await repo.add_prerequisite(
            test_concepts[1].id, test_concepts[0].id, 0.9, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[1].id, 0.8, "required"
        )
        await repo.add_prerequisite(
            test_concepts[3].id, test_concepts[2].id, 0.7, "required"
        )
        await db_session.commit()

        response = await client.get(
            f"/v1/concepts/{test_concepts[3].id}/prerequisites/chain",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_concept_id"] == str(test_concepts[3].id)
        assert len(data["chain"]) == 3
        assert data["total_depth"] == 3

    @pytest.mark.asyncio
    async def test_get_dependents_endpoint(
        self, client, db_session, test_concepts, auth_headers
    ):
        """Test GET /v1/concepts/{id}/dependents endpoint."""
        repo = ConceptRepository(db_session)

        # B and C both depend on A
        await repo.add_prerequisite(
            test_concepts[1].id, test_concepts[0].id, 0.9, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[0].id, 0.8, "required"
        )
        await db_session.commit()

        response = await client.get(
            f"/v1/concepts/{test_concepts[0].id}/dependents",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_root_concepts_endpoint(
        self, client, db_session, test_course, test_concepts, auth_headers
    ):
        """Test GET /v1/concepts/roots/{course_id} endpoint."""
        repo = ConceptRepository(db_session)

        # Create some prerequisites (making some concepts non-root)
        await repo.add_prerequisite(
            test_concepts[1].id, test_concepts[0].id, 0.9, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[0].id, 0.8, "required"
        )
        await db_session.commit()

        response = await client.get(
            f"/v1/concepts/roots/{test_course.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Concepts 0, 3, 4 should be roots
        assert len(data) == 3


class TestPerformance:
    """Tests for API performance requirements."""

    @pytest.mark.asyncio
    async def test_prerequisites_response_time(
        self, client, db_session, test_concepts, auth_headers
    ):
        """Test that GET /prerequisites responds in <50ms."""
        repo = ConceptRepository(db_session)

        # Create some prerequisites
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[0].id, 0.9, "required"
        )
        await repo.add_prerequisite(
            test_concepts[2].id, test_concepts[1].id, 0.7, "helpful"
        )
        await db_session.commit()

        start = time.time()
        response = await client.get(
            f"/v1/concepts/{test_concepts[2].id}/prerequisites",
            headers=auth_headers
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 50, f"Response took {elapsed_ms:.2f}ms, expected <50ms"

    @pytest.mark.asyncio
    async def test_chain_query_response_time(
        self, client, db_session, test_concepts, auth_headers
    ):
        """Test that prerequisite chain query responds in <50ms."""
        repo = ConceptRepository(db_session)

        # Build deeper chain
        for i in range(1, 5):
            await repo.add_prerequisite(
                test_concepts[i].id, test_concepts[i-1].id, 0.8, "required"
            )
        await db_session.commit()

        start = time.time()
        response = await client.get(
            f"/v1/concepts/{test_concepts[4].id}/prerequisites/chain",
            headers=auth_headers
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 50, f"Response took {elapsed_ms:.2f}ms, expected <50ms"
