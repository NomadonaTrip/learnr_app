"""
Concept API endpoints.
Endpoints for accessing concept information and prerequisites.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.concept_repository import ConceptRepository
from src.schemas.concept import ConceptResponse
from src.schemas.concept_prerequisite import (
    PrerequisiteChainItem,
    PrerequisiteChainResponse,
    PrerequisiteWithConcept,
    RelationshipType,
    RootConceptResponse,
)

router = APIRouter(prefix="/concepts", tags=["Concepts"])


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


@router.get(
    "/{concept_id}/prerequisites",
    response_model=List[PrerequisiteWithConcept],
    summary="Get concept prerequisites",
    description="Returns direct prerequisites for a concept. Requires authentication.",
    responses={
        200: {"description": "Prerequisites retrieved successfully"},
        404: {"description": "Concept not found"},
    },
)
async def get_concept_prerequisites(
    concept_id: UUID,
    chain: bool = Query(
        False,
        description="If true, return full prerequisite chain (recursive)"
    ),
    depth: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Maximum depth for chain traversal (default 10)"
    ),
    repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> List[PrerequisiteWithConcept]:
    """
    Get prerequisites for a concept.

    By default returns direct prerequisites only.
    Use ?chain=true to get the full prerequisite chain recursively.
    Use ?depth=N to limit chain depth (max 10).
    """
    # Verify concept exists
    concept = await repo.get_by_id(concept_id)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept with ID '{concept_id}' not found",
                }
            },
        )

    if chain:
        # Get full prerequisite chain
        max_depth = depth or 10
        chain_data = await repo.get_prerequisite_chain(concept_id, max_depth)

        return [
            PrerequisiteWithConcept(
                concept_id=c.id,
                concept_name=c.name,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                prerequisite_depth=c.prerequisite_depth,
                strength=1.0,  # Chain doesn't have strength per-hop
                relationship_type=RelationshipType.REQUIRED,
            )
            for c, d in chain_data
        ]
    else:
        # Get direct prerequisites with strength/type
        prereqs = await repo.get_prerequisites_with_strength(concept_id)

        return [
            PrerequisiteWithConcept(
                concept_id=c.id,
                concept_name=c.name,
                knowledge_area_id=c.knowledge_area_id,
                difficulty_estimate=c.difficulty_estimate,
                prerequisite_depth=c.prerequisite_depth,
                strength=strength,
                relationship_type=RelationshipType(rel_type),
            )
            for c, strength, rel_type in prereqs
        ]


@router.get(
    "/{concept_id}/prerequisites/chain",
    response_model=PrerequisiteChainResponse,
    summary="Get full prerequisite chain",
    description="Returns the complete prerequisite chain for a concept with depth info.",
    responses={
        200: {"description": "Prerequisite chain retrieved successfully"},
        404: {"description": "Concept not found"},
    },
)
async def get_prerequisite_chain(
    concept_id: UUID,
    max_depth: int = Query(
        10,
        ge=1,
        le=10,
        description="Maximum depth to traverse"
    ),
    repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> PrerequisiteChainResponse:
    """
    Get the full prerequisite chain for a concept.

    Returns all prerequisites recursively up to max_depth levels,
    with each item including its distance from the target concept.
    """
    # Verify concept exists
    concept = await repo.get_by_id(concept_id)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept with ID '{concept_id}' not found",
                }
            },
        )

    # Get full chain with depths
    chain_data = await repo.get_prerequisite_chain(concept_id, max_depth)

    chain_items = [
        PrerequisiteChainItem(
            concept_id=c.id,
            concept_name=c.name,
            knowledge_area_id=c.knowledge_area_id,
            depth=d,
            strength=1.0,  # Aggregate strength not available in chain
            relationship_type=RelationshipType.REQUIRED,
        )
        for c, d in chain_data
    ]

    total_depth = max(item.depth for item in chain_items) if chain_items else 0

    return PrerequisiteChainResponse(
        target_concept_id=concept_id,
        target_concept_name=concept.name,
        chain=chain_items,
        total_depth=total_depth,
    )


@router.get(
    "/{concept_id}/dependents",
    response_model=List[ConceptResponse],
    summary="Get concepts that depend on this one",
    description="Returns concepts that have this concept as a prerequisite.",
    responses={
        200: {"description": "Dependents retrieved successfully"},
        404: {"description": "Concept not found"},
    },
)
async def get_concept_dependents(
    concept_id: UUID,
    repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> List[ConceptResponse]:
    """
    Get concepts that depend on this concept.

    Returns all concepts that list this concept as a prerequisite.
    """
    # Verify concept exists
    concept = await repo.get_by_id(concept_id)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept with ID '{concept_id}' not found",
                }
            },
        )

    dependents = await repo.get_dependents(concept_id)

    return [
        ConceptResponse(
            id=c.id,
            course_id=c.course_id,
            name=c.name,
            description=c.description,
            corpus_section_ref=c.corpus_section_ref,
            knowledge_area_id=c.knowledge_area_id,
            difficulty_estimate=c.difficulty_estimate,
            prerequisite_depth=c.prerequisite_depth,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in dependents
    ]


@router.get(
    "/roots/{course_id}",
    response_model=List[RootConceptResponse],
    summary="Get foundational concepts",
    description="Returns concepts with no prerequisites (root concepts).",
    responses={
        200: {"description": "Root concepts retrieved successfully"},
    },
)
async def get_root_concepts(
    course_id: UUID,
    repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> List[RootConceptResponse]:
    """
    Get foundational concepts for a course.

    Returns all concepts that have no prerequisites (root nodes in the graph).
    Includes count of concepts that depend on each root.
    """
    roots = await repo.get_root_concepts_with_dependent_count(course_id)

    return [
        RootConceptResponse(
            id=c.id,
            name=c.name,
            knowledge_area_id=c.knowledge_area_id,
            difficulty_estimate=c.difficulty_estimate,
            dependent_count=count,
        )
        for c, count in roots
    ]
