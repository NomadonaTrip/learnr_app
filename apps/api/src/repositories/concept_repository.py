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
from src.schemas.concept import ConceptCreate
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
