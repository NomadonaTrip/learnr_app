"""
Concept repository for database operations on Concept model.
Implements repository pattern for data access with multi-course support.
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.concept import Concept
from src.models.concept_prerequisite import ConceptPrerequisite
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.schemas.concept import ConceptCreate, ConceptListParams
from src.schemas.concept_prerequisite import PrerequisiteCreate


class ConceptRepository:
    """Repository for Concept database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_concept(self, concept: ConceptCreate) -> Concept:
        """
        Create a new concept.

        Args:
            concept: ConceptCreate schema with concept data

        Returns:
            Created Concept model
        """
        db_concept = Concept(
            course_id=concept.course_id,
            name=concept.name,
            description=concept.description,
            corpus_section_ref=concept.corpus_section_ref,
            knowledge_area_id=concept.knowledge_area_id,
            difficulty_estimate=concept.difficulty_estimate,
            prerequisite_depth=concept.prerequisite_depth,
        )
        self.session.add(db_concept)
        await self.session.flush()
        await self.session.refresh(db_concept)
        return db_concept

    async def bulk_create(self, concepts: List[ConceptCreate]) -> int:
        """
        Bulk create concepts for efficiency.

        Args:
            concepts: List of ConceptCreate schemas

        Returns:
            Number of concepts created
        """
        db_concepts = [
            Concept(
                course_id=c.course_id,
                name=c.name,
                description=c.description,
                corpus_section_ref=c.corpus_section_ref,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                prerequisite_depth=c.prerequisite_depth,
            )
            for c in concepts
        ]
        self.session.add_all(db_concepts)
        await self.session.flush()
        return len(db_concepts)

    async def get_by_id(self, concept_id: UUID) -> Optional[Concept]:
        """
        Get a concept by its UUID.

        Args:
            concept_id: Concept UUID

        Returns:
            Concept model if found, None otherwise
        """
        result = await self.session.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, concept_ids: List[UUID]) -> List[Concept]:
        """
        Get multiple concepts by their UUIDs in a single query.

        Args:
            concept_ids: List of Concept UUIDs

        Returns:
            List of Concept models (may be fewer than input if some IDs don't exist)
        """
        if not concept_ids:
            return []

        result = await self.session.execute(
            select(Concept).where(Concept.id.in_(concept_ids))
        )
        return list(result.scalars().all())

    async def get_all_concepts(self, course_id: UUID) -> List[Concept]:
        """
        Get all concepts for a course.

        Args:
            course_id: Course UUID to filter by

        Returns:
            List of Concept models for the course
        """
        result = await self.session.execute(
            select(Concept)
            .where(Concept.course_id == course_id)
            .order_by(Concept.corpus_section_ref, Concept.name)
        )
        return list(result.scalars().all())

    async def get_concepts_by_ka(
        self, course_id: UUID, knowledge_area_id: str
    ) -> List[Concept]:
        """
        Get concepts for a specific knowledge area within a course.

        Args:
            course_id: Course UUID
            knowledge_area_id: Knowledge area ID (from course.knowledge_areas[].id)

        Returns:
            List of Concept models matching criteria
        """
        result = await self.session.execute(
            select(Concept)
            .where(Concept.course_id == course_id)
            .where(Concept.knowledge_area_id == knowledge_area_id)
            .order_by(Concept.corpus_section_ref, Concept.name)
        )
        return list(result.scalars().all())

    async def get_concept_count(self, course_id: UUID) -> int:
        """
        Get total concept count for a course.

        Args:
            course_id: Course UUID

        Returns:
            Total count of concepts
        """
        result = await self.session.execute(
            select(func.count(Concept.id)).where(Concept.course_id == course_id)
        )
        return result.scalar_one()

    async def get_concept_count_by_ka(self, course_id: UUID) -> Dict[str, int]:
        """
        Get concept count grouped by knowledge area for a course.

        Args:
            course_id: Course UUID

        Returns:
            Dictionary mapping knowledge_area_id to count
        """
        result = await self.session.execute(
            select(Concept.knowledge_area_id, func.count(Concept.id))
            .where(Concept.course_id == course_id)
            .group_by(Concept.knowledge_area_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_by_section_ref(
        self, course_id: UUID, section_ref: str
    ) -> List[Concept]:
        """
        Get concepts by corpus section reference.

        Args:
            course_id: Course UUID
            section_ref: Section reference (e.g., "3.2.1")

        Returns:
            List of Concept models for the section
        """
        result = await self.session.execute(
            select(Concept)
            .where(Concept.course_id == course_id)
            .where(Concept.corpus_section_ref == section_ref)
            .order_by(Concept.name)
        )
        return list(result.scalars().all())

    async def delete_all_for_course(self, course_id: UUID) -> int:
        """
        Delete all concepts for a course.
        Useful for re-extraction scenarios.

        Args:
            course_id: Course UUID

        Returns:
            Number of concepts deleted
        """
        result = await self.session.execute(
            delete(Concept).where(Concept.course_id == course_id)
        )
        return result.rowcount

    # ==================== Prerequisite Methods ====================

    async def get_prerequisites(self, concept_id: UUID) -> List[Concept]:
        """
        Get direct prerequisites for a concept.

        Args:
            concept_id: Concept UUID

        Returns:
            List of prerequisite Concept models
        """
        result = await self.session.execute(
            select(Concept)
            .join(
                ConceptPrerequisite,
                ConceptPrerequisite.prerequisite_concept_id == Concept.id
            )
            .where(ConceptPrerequisite.concept_id == concept_id)
            .order_by(Concept.name)
        )
        return list(result.scalars().all())

    async def get_prerequisites_with_strength(
        self, concept_id: UUID
    ) -> List[Tuple[Concept, float, str]]:
        """
        Get direct prerequisites with strength and relationship type.

        Args:
            concept_id: Concept UUID

        Returns:
            List of tuples (Concept, strength, relationship_type)
        """
        result = await self.session.execute(
            select(
                Concept,
                ConceptPrerequisite.strength,
                ConceptPrerequisite.relationship_type
            )
            .join(
                ConceptPrerequisite,
                ConceptPrerequisite.prerequisite_concept_id == Concept.id
            )
            .where(ConceptPrerequisite.concept_id == concept_id)
            .order_by(ConceptPrerequisite.strength.desc())
        )
        return list(result.all())

    async def get_prerequisite_chain(
        self, concept_id: UUID, max_depth: int = 10
    ) -> List[Tuple[Concept, int]]:
        """
        Get full prerequisite chain using recursive CTE.

        Args:
            concept_id: Target concept UUID
            max_depth: Maximum depth to traverse (default 10)

        Returns:
            List of tuples (Concept, depth) ordered by depth
        """
        # Use recursive CTE for efficient chain traversal
        cte_sql = text("""
            WITH RECURSIVE prereq_chain AS (
                -- Base case: direct prerequisites
                SELECT
                    cp.prerequisite_concept_id as concept_id,
                    1 as depth
                FROM concept_prerequisites cp
                WHERE cp.concept_id = :target_id

                UNION ALL

                -- Recursive case: prerequisites of prerequisites
                SELECT
                    cp.prerequisite_concept_id,
                    pc.depth + 1
                FROM concept_prerequisites cp
                INNER JOIN prereq_chain pc ON cp.concept_id = pc.concept_id
                WHERE pc.depth < :max_depth
            )
            SELECT DISTINCT ON (concept_id) concept_id, depth
            FROM prereq_chain
            ORDER BY concept_id, depth
        """)

        chain_result = await self.session.execute(
            cte_sql, {"target_id": str(concept_id), "max_depth": max_depth}
        )
        chain_data = chain_result.fetchall()

        if not chain_data:
            return []

        # Fetch concept details
        concept_ids = [row[0] for row in chain_data]
        depth_map = {row[0]: row[1] for row in chain_data}

        concepts_result = await self.session.execute(
            select(Concept).where(Concept.id.in_(concept_ids))
        )
        concepts = concepts_result.scalars().all()

        # Combine with depth info and sort
        result = [(c, depth_map[c.id]) for c in concepts]
        result.sort(key=lambda x: x[1])
        return result

    async def get_dependents(self, concept_id: UUID) -> List[Concept]:
        """
        Get concepts that depend on this concept (reverse lookup).

        Args:
            concept_id: Prerequisite concept UUID

        Returns:
            List of dependent Concept models
        """
        result = await self.session.execute(
            select(Concept)
            .join(
                ConceptPrerequisite,
                ConceptPrerequisite.concept_id == Concept.id
            )
            .where(ConceptPrerequisite.prerequisite_concept_id == concept_id)
            .order_by(Concept.name)
        )
        return list(result.scalars().all())

    async def add_prerequisite(
        self,
        concept_id: UUID,
        prereq_id: UUID,
        strength: float = 1.0,
        relationship_type: str = "required"
    ) -> ConceptPrerequisite:
        """
        Add a single prerequisite relationship.

        Args:
            concept_id: Target concept UUID
            prereq_id: Prerequisite concept UUID
            strength: Relationship strength (0.0-1.0)
            relationship_type: 'required', 'helpful', or 'related'

        Returns:
            Created ConceptPrerequisite model
        """
        prereq = ConceptPrerequisite(
            concept_id=concept_id,
            prerequisite_concept_id=prereq_id,
            strength=strength,
            relationship_type=relationship_type
        )
        self.session.add(prereq)
        await self.session.flush()
        return prereq

    async def bulk_add_prerequisites(
        self, prerequisites: List[PrerequisiteCreate]
    ) -> int:
        """
        Bulk add prerequisite relationships.

        Args:
            prerequisites: List of PrerequisiteCreate schemas

        Returns:
            Number of prerequisites created
        """
        db_prereqs = [
            ConceptPrerequisite(
                concept_id=p.concept_id,
                prerequisite_concept_id=p.prerequisite_concept_id,
                strength=p.strength,
                relationship_type=p.relationship_type.value
            )
            for p in prerequisites
        ]
        self.session.add_all(db_prereqs)
        await self.session.flush()
        return len(db_prereqs)

    async def get_root_concepts(self, course_id: UUID) -> List[Concept]:
        """
        Get concepts with no prerequisites (foundational concepts).

        Args:
            course_id: Course UUID

        Returns:
            List of root Concept models
        """
        # Subquery for concepts that have prerequisites
        has_prereqs = (
            select(ConceptPrerequisite.concept_id)
            .distinct()
            .scalar_subquery()
        )

        result = await self.session.execute(
            select(Concept)
            .where(Concept.course_id == course_id)
            .where(~Concept.id.in_(has_prereqs))
            .order_by(Concept.name)
        )
        return list(result.scalars().all())

    async def get_root_concepts_with_dependent_count(
        self, course_id: UUID
    ) -> List[Tuple[Concept, int]]:
        """
        Get root concepts with count of dependents.

        Args:
            course_id: Course UUID

        Returns:
            List of tuples (Concept, dependent_count)
        """
        # Subquery for concepts that have prerequisites
        has_prereqs = (
            select(ConceptPrerequisite.concept_id)
            .distinct()
            .scalar_subquery()
        )

        # Count dependents for each concept
        dependent_count = (
            select(func.count(ConceptPrerequisite.concept_id))
            .where(ConceptPrerequisite.prerequisite_concept_id == Concept.id)
            .correlate(Concept)
            .scalar_subquery()
        )

        result = await self.session.execute(
            select(Concept, dependent_count)
            .where(Concept.course_id == course_id)
            .where(~Concept.id.in_(has_prereqs))
            .order_by(dependent_count.desc(), Concept.name)
        )
        return list(result.all())

    async def delete_all_prerequisites_for_course(self, course_id: UUID) -> int:
        """
        Delete all prerequisite relationships for concepts in a course.

        Args:
            course_id: Course UUID

        Returns:
            Number of prerequisites deleted
        """
        # Get all concept IDs for the course
        concept_ids_query = select(Concept.id).where(Concept.course_id == course_id)

        result = await self.session.execute(
            delete(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id.in_(concept_ids_query)
            )
        )
        return result.rowcount

    async def update_prerequisite_depths(
        self, depth_map: Dict[UUID, int]
    ) -> int:
        """
        Bulk update prerequisite_depth for concepts.

        Args:
            depth_map: Dict mapping concept_id to prerequisite_depth

        Returns:
            Number of concepts updated
        """
        updated = 0
        for concept_id, depth in depth_map.items():
            result = await self.session.execute(
                update(Concept)
                .where(Concept.id == concept_id)
                .values(prerequisite_depth=depth)
            )
            updated += result.rowcount
        await self.session.flush()
        return updated

    async def get_all_prerequisites_for_course(
        self, course_id: UUID
    ) -> List[ConceptPrerequisite]:
        """
        Get all prerequisite relationships for a course.

        Args:
            course_id: Course UUID

        Returns:
            List of ConceptPrerequisite models
        """
        concept_ids_query = select(Concept.id).where(Concept.course_id == course_id)

        result = await self.session.execute(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id.in_(concept_ids_query)
            )
        )
        return list(result.scalars().all())

    # ==================== API Endpoint Methods (Story 2.10) ====================

    async def get_concepts_filtered(
        self, course_id: UUID, params: ConceptListParams
    ) -> Tuple[List[Concept], int]:
        """
        Get concepts with filtering, search, and pagination.

        Args:
            course_id: Course UUID
            params: Filter and pagination parameters

        Returns:
            Tuple of (concepts list, total count)
        """
        # Base query filtered by course
        query = select(Concept).where(Concept.course_id == course_id)

        # Apply knowledge area filter
        if params.knowledge_area_id:
            query = query.where(Concept.knowledge_area_id == params.knowledge_area_id)

        # Apply search filter (case-insensitive name search)
        if params.search:
            query = query.where(Concept.name.ilike(f"%{params.search}%"))

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply ordering and pagination
        query = query.order_by(Concept.corpus_section_ref, Concept.name)
        query = query.limit(params.limit).offset(params.offset)

        # Execute query
        result = await self.session.execute(query)
        concepts = list(result.scalars().all())

        return concepts, total

    async def get_prerequisite_chain_for_course(
        self, course_id: UUID, concept_id: UUID, max_depth: int = 10
    ) -> List[Concept]:
        """
        Get full prerequisite chain for a concept within a specific course.

        Args:
            course_id: Course UUID
            concept_id: Target concept UUID
            max_depth: Maximum depth to traverse (default 10)

        Returns:
            List of prerequisite Concepts ordered by depth
        """
        # Use recursive CTE with course filtering
        cte_sql = text("""
            WITH RECURSIVE prereq_chain AS (
                -- Base case: direct prerequisites within the course
                SELECT
                    c.id,
                    c.course_id,
                    c.name,
                    c.description,
                    c.corpus_section_ref,
                    c.knowledge_area_id,
                    c.difficulty_estimate,
                    c.prerequisite_depth,
                    c.created_at,
                    c.updated_at,
                    1 as chain_depth
                FROM concepts c
                INNER JOIN concept_prerequisites cp ON c.id = cp.prerequisite_concept_id
                WHERE cp.concept_id = :target_id
                  AND c.course_id = :course_id

                UNION ALL

                -- Recursive case: prerequisites of prerequisites within the course
                SELECT
                    c.id,
                    c.course_id,
                    c.name,
                    c.description,
                    c.corpus_section_ref,
                    c.knowledge_area_id,
                    c.difficulty_estimate,
                    c.prerequisite_depth,
                    c.created_at,
                    c.updated_at,
                    pc.chain_depth + 1
                FROM concepts c
                INNER JOIN concept_prerequisites cp ON c.id = cp.prerequisite_concept_id
                INNER JOIN prereq_chain pc ON cp.concept_id = pc.id
                WHERE pc.chain_depth < :max_depth
                  AND c.course_id = :course_id
            )
            SELECT DISTINCT ON (id) *
            FROM prereq_chain
            ORDER BY id, chain_depth, prerequisite_depth
        """)

        result = await self.session.execute(
            cte_sql,
            {"target_id": str(concept_id), "course_id": str(course_id), "max_depth": max_depth}
        )

        # Map results to Concept objects
        prerequisites = []
        for row in result:
            concept = Concept(
                id=row.id,
                course_id=row.course_id,
                name=row.name,
                description=row.description,
                corpus_section_ref=row.corpus_section_ref,
                knowledge_area_id=row.knowledge_area_id,
                difficulty_estimate=row.difficulty_estimate,
                prerequisite_depth=row.prerequisite_depth,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            prerequisites.append(concept)

        return prerequisites

    async def get_question_count_for_concept(
        self, course_id: UUID, concept_id: UUID
    ) -> int:
        """
        Get count of questions linked to a concept within a course.

        Args:
            course_id: Course UUID
            concept_id: Concept UUID

        Returns:
            Number of questions for this concept
        """
        result = await self.session.execute(
            select(func.count(QuestionConcept.question_id))
            .join(Question, QuestionConcept.question_id == Question.id)
            .where(QuestionConcept.concept_id == concept_id)
            .where(Question.course_id == course_id)
        )
        return result.scalar_one()

    async def get_corpus_stats(self, course_id: UUID) -> Dict:
        """
        Get comprehensive statistics for a course's concept corpus.

        Args:
            course_id: Course UUID

        Returns:
            Dictionary with statistics including:
            - total_concepts
            - by_knowledge_area (dict)
            - by_depth (dict)
            - average_prerequisites_per_concept
            - concepts_with_questions
            - concepts_without_questions
        """
        # Total concepts for course
        total_result = await self.session.execute(
            select(func.count(Concept.id)).where(Concept.course_id == course_id)
        )
        total = total_result.scalar_one()

        # By knowledge area
        ka_result = await self.session.execute(
            select(Concept.knowledge_area_id, func.count(Concept.id))
            .where(Concept.course_id == course_id)
            .group_by(Concept.knowledge_area_id)
        )
        by_ka = {row[0]: row[1] for row in ka_result.all()}

        # By prerequisite depth
        depth_result = await self.session.execute(
            select(Concept.prerequisite_depth, func.count(Concept.id))
            .where(Concept.course_id == course_id)
            .group_by(Concept.prerequisite_depth)
        )
        by_depth = {row[0]: row[1] for row in depth_result.all()}

        # Average prerequisites per concept for course
        avg_prereq_result = await self.session.execute(
            text("""
                SELECT AVG(prereq_count)
                FROM (
                    SELECT c.id, COUNT(cp.prerequisite_concept_id) as prereq_count
                    FROM concepts c
                    LEFT JOIN concept_prerequisites cp ON c.id = cp.concept_id
                    WHERE c.course_id = :course_id
                    GROUP BY c.id
                ) AS prereq_counts
            """),
            {"course_id": str(course_id)}
        )
        avg_prereq = avg_prereq_result.scalar_one() or 0.0

        # Concepts with questions (within same course)
        with_questions_result = await self.session.execute(
            select(func.count(func.distinct(QuestionConcept.concept_id)))
            .join(Concept, QuestionConcept.concept_id == Concept.id)
            .join(Question, QuestionConcept.question_id == Question.id)
            .where(Concept.course_id == course_id)
            .where(Question.course_id == course_id)
        )
        concepts_with_questions = with_questions_result.scalar_one()

        concepts_without_questions = total - concepts_with_questions

        return {
            "total_concepts": total,
            "by_knowledge_area": by_ka,
            "by_depth": by_depth,
            "average_prerequisites_per_concept": float(avg_prereq),
            "concepts_with_questions": concepts_with_questions,
            "concepts_without_questions": concepts_without_questions,
        }
