"""
Concept API endpoints.
Endpoints for accessing concept information and prerequisites.
"""
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from src.db.redis_client import get_redis
from src.db.session import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.repositories.concept_repository import ConceptRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.question_repository import QuestionRepository
from src.schemas.concept import (
    ConceptListParams,
    ConceptPrerequisitesResponse,
    ConceptQuestionsResponse,
    ConceptResponse,
    ConceptStatsResponse,
    PaginatedConceptResponse,
    QuestionSummary,
)
from src.schemas.concept_prerequisite import (
    PrerequisiteChainItem,
    PrerequisiteChainResponse,
    PrerequisiteWithConcept,
    RelationshipType,
    RootConceptResponse,
)

logger = get_logger(__name__)

router = APIRouter(tags=["Concepts"])

# Cache TTL for concept data (1 hour as per AC 8)
CONCEPT_CACHE_TTL = 3600


def get_concept_repository(db: AsyncSession = Depends(get_db)) -> ConceptRepository:
    """Dependency for ConceptRepository."""
    return ConceptRepository(db)


def get_course_repository(db: AsyncSession = Depends(get_db)) -> CourseRepository:
    """Dependency for CourseRepository."""
    return CourseRepository(db)


def get_question_repository(db: AsyncSession = Depends(get_db)) -> QuestionRepository:
    """Dependency for QuestionRepository."""
    return QuestionRepository(db)


async def get_course_id_by_slug(
    course_slug: str,
    course_repo: CourseRepository
) -> UUID:
    """Helper to get course_id by slug or raise 404."""
    course = await course_repo.get_by_slug(course_slug)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COURSE_NOT_FOUND",
                    "message": f"Course with slug '{course_slug}' not found",
                }
            },
        )
    return course.id


# ==================== Story 2.10: Course-Scoped Concept Endpoints ====================


@router.get(
    "/courses/{course_slug}/concepts",
    response_model=PaginatedConceptResponse,
    summary="List concepts for a course",
    description="Returns paginated list of concepts for a course with optional filters.",
    responses={
        200: {"description": "Concepts retrieved successfully"},
        404: {"description": "Course not found"},
    },
)
async def list_course_concepts(
    request: Request,
    course_slug: str,
    knowledge_area_id: str | None = Query(None, description="Filter by knowledge area"),
    search: str | None = Query(None, description="Search by concept name"),
    limit: int = Query(50, ge=1, le=200, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    current_user: User = Depends(get_current_user),
) -> PaginatedConceptResponse:
    """
    List all concepts for a course with optional filtering and pagination.

    Supports filtering by knowledge area and searching by name.
    Results are ordered by corpus section and name.
    Cached for 1 hour per AC 8.
    """
    start_time = time.time()

    # Build cache key (AC 8: keyed by course and params)
    cache_key = f"concepts:{course_slug}:list:{knowledge_area_id or 'all'}:{search or 'none'}:{limit}:{offset}"

    # Try to get from cache
    redis = await get_redis()
    cached_response = await redis.get(cache_key)
    if cached_response:
        logger.info("concept_list_cache_hit", cache_key=cache_key)
        return PaginatedConceptResponse.model_validate_json(cached_response)

    # Get course ID by slug
    course_id = await get_course_id_by_slug(course_slug, course_repo)

    # Build query params
    params = ConceptListParams(
        knowledge_area_id=knowledge_area_id,
        search=search,
        limit=limit,
        offset=offset
    )

    # Get filtered concepts from database
    concepts, total = await concept_repo.get_concepts_filtered(course_id, params)

    # Convert to response models
    items = [
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
        for c in concepts
    ]

    # Calculate has_more
    has_more = (offset + limit) < total

    # Log response time
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > 100:
        logger.warning(
            "slow_concept_list_query",
            course_slug=course_slug,
            elapsed_ms=round(elapsed_ms, 2),
            total_results=total
        )

    response = PaginatedConceptResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )

    # Cache response (AC 8: 1 hour TTL)
    await redis.setex(cache_key, CONCEPT_CACHE_TTL, response.model_dump_json())
    logger.info("concept_list_cache_set", cache_key=cache_key)

    return response


@router.get(
    "/courses/{course_slug}/concepts/stats",
    response_model=ConceptStatsResponse,
    summary="Get concept statistics for a course",
    description="Returns comprehensive statistics about concepts in a course.",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        404: {"description": "Course not found"},
    },
)
async def get_course_concept_stats(
    request: Request,
    course_slug: str,
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    current_user: User = Depends(get_current_user),
) -> ConceptStatsResponse:
    """
    Get comprehensive statistics for a course's concept corpus.

    Includes:
    - Total concept count
    - Breakdown by knowledge area
    - Breakdown by prerequisite depth
    - Average prerequisites per concept
    - Concepts with/without questions

    Cached for 1 hour per AC 8.
    """
    start_time = time.time()

    # Build cache key (AC 8: keyed by course)
    cache_key = f"concepts:{course_slug}:stats"

    # Try to get from cache
    redis = await get_redis()
    cached_response = await redis.get(cache_key)
    if cached_response:
        logger.info("concept_stats_cache_hit", cache_key=cache_key)
        return ConceptStatsResponse.model_validate_json(cached_response)

    # Get course ID by slug
    course_id = await get_course_id_by_slug(course_slug, course_repo)

    # Get statistics from database
    stats = await concept_repo.get_corpus_stats(course_id)

    # Log response time
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > 100:
        logger.warning(
            "slow_concept_stats_query",
            course_slug=course_slug,
            elapsed_ms=round(elapsed_ms, 2)
        )

    response = ConceptStatsResponse(
        course_id=course_id,
        total_concepts=stats["total_concepts"],
        by_knowledge_area=stats["by_knowledge_area"],
        by_depth=stats["by_depth"],
        average_prerequisites_per_concept=stats["average_prerequisites_per_concept"],
        concepts_with_questions=stats["concepts_with_questions"],
        concepts_without_questions=stats["concepts_without_questions"],
    )

    # Cache response (AC 8: 1 hour TTL)
    await redis.setex(cache_key, CONCEPT_CACHE_TTL, response.model_dump_json())
    logger.info("concept_stats_cache_set", cache_key=cache_key)

    return response


@router.get(
    "/courses/{course_slug}/concepts/{concept_id}",
    response_model=ConceptResponse,
    summary="Get a single concept",
    description="Returns detailed information about a specific concept.",
    responses={
        200: {"description": "Concept retrieved successfully"},
        404: {"description": "Concept or course not found"},
    },
)
async def get_course_concept(
    request: Request,
    course_slug: str,
    concept_id: UUID,
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    current_user: User = Depends(get_current_user),
) -> ConceptResponse:
    """
    Get detailed information about a specific concept.

    Verifies that the concept belongs to the specified course.
    """
    start_time = time.time()

    # Get course ID by slug
    course_id = await get_course_id_by_slug(course_slug, course_repo)

    # Get concept
    concept = await concept_repo.get_by_id(concept_id)
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

    # Verify concept belongs to course
    if concept.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_IN_COURSE",
                    "message": f"Concept does not belong to course '{course_slug}'",
                }
            },
        )

    # Log response time
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > 100:
        logger.warning(
            "slow_concept_get_query",
            course_slug=course_slug,
            concept_id=str(concept_id),
            elapsed_ms=round(elapsed_ms, 2)
        )

    return ConceptResponse(
        id=concept.id,
        course_id=concept.course_id,
        name=concept.name,
        description=concept.description,
        corpus_section_ref=concept.corpus_section_ref,
        knowledge_area_id=concept.knowledge_area_id,
        difficulty_estimate=concept.difficulty_estimate,
        prerequisite_depth=concept.prerequisite_depth,
        created_at=concept.created_at,
        updated_at=concept.updated_at,
    )


@router.get(
    "/courses/{course_slug}/concepts/{concept_id}/prerequisites",
    response_model=ConceptPrerequisitesResponse,
    summary="Get prerequisite chain for a concept",
    description="Returns all prerequisites for a concept within the course.",
    responses={
        200: {"description": "Prerequisites retrieved successfully"},
        404: {"description": "Concept or course not found"},
    },
)
async def get_course_concept_prerequisites(
    request: Request,
    course_slug: str,
    concept_id: UUID,
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    current_user: User = Depends(get_current_user),
) -> ConceptPrerequisitesResponse:
    """
    Get the full prerequisite chain for a concept.

    Returns all prerequisites recursively, ordered by depth (foundational first).
    Prerequisites are scoped to the same course.
    """
    start_time = time.time()

    # Get course ID by slug
    course_id = await get_course_id_by_slug(course_slug, course_repo)

    # Verify concept exists and belongs to course
    concept = await concept_repo.get_by_id(concept_id)
    if not concept or concept.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found in course '{course_slug}'",
                }
            },
        )

    # Get prerequisite chain within course
    prerequisites = await concept_repo.get_prerequisite_chain_for_course(
        course_id, concept_id
    )

    # Convert to response models
    prerequisite_responses = [
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
        for c in prerequisites
    ]

    depth = max((c.prerequisite_depth for c in prerequisites), default=0)

    # Log response time
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > 100:
        logger.warning(
            "slow_prerequisites_query",
            course_slug=course_slug,
            concept_id=str(concept_id),
            elapsed_ms=round(elapsed_ms, 2),
            prerequisite_count=len(prerequisites)
        )

    return ConceptPrerequisitesResponse(
        concept_id=concept_id,
        prerequisites=prerequisite_responses,
        depth=depth
    )


@router.get(
    "/courses/{course_slug}/concepts/{concept_id}/questions",
    response_model=ConceptQuestionsResponse,
    summary="Get questions for a concept",
    description="Returns question count and sample questions for a concept.",
    responses={
        200: {"description": "Questions retrieved successfully"},
        404: {"description": "Concept or course not found"},
    },
)
async def get_course_concept_questions(
    request: Request,
    course_slug: str,
    concept_id: UUID,
    sample_limit: int = Query(5, ge=1, le=20, description="Number of sample questions to return"),
    concept_repo: ConceptRepository = Depends(get_concept_repository),
    course_repo: CourseRepository = Depends(get_course_repository),
    question_repo: QuestionRepository = Depends(get_question_repository),
    current_user: User = Depends(get_current_user),
) -> ConceptQuestionsResponse:
    """
    Get questions for a concept.

    Returns total count and sample questions from the same course.
    Sample questions are randomly selected.
    """
    start_time = time.time()

    # Get course ID by slug
    course_id = await get_course_id_by_slug(course_slug, course_repo)

    # Verify concept exists and belongs to course
    concept = await concept_repo.get_by_id(concept_id)
    if not concept or concept.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found in course '{course_slug}'",
                }
            },
        )

    # Get question count
    question_count = await concept_repo.get_question_count_for_concept(
        course_id, concept_id
    )

    # Get sample questions (from same course)
    sample_questions_list = await question_repo.get_questions_by_concept(
        concept_id, course_id, sample_limit
    )

    # Convert to QuestionSummary with truncated text
    sample_questions = [
        QuestionSummary(
            id=q.id,
            question_text=q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
            difficulty=q.difficulty
        )
        for q in sample_questions_list
    ]

    # Log response time
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > 100:
        logger.warning(
            "slow_concept_questions_query",
            course_slug=course_slug,
            concept_id=str(concept_id),
            elapsed_ms=round(elapsed_ms, 2),
            question_count=question_count
        )

    return ConceptQuestionsResponse(
        concept_id=concept_id,
        question_count=question_count,
        sample_questions=sample_questions
    )


# ==================== Legacy Endpoints (from previous stories) ====================


@router.get(
    "/{concept_id}/prerequisites",
    response_model=list[PrerequisiteWithConcept],
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
    depth: int | None = Query(
        None,
        ge=1,
        le=10,
        description="Maximum depth for chain traversal (default 10)"
    ),
    repo: ConceptRepository = Depends(get_concept_repository),
    current_user: User = Depends(get_current_user),
) -> list[PrerequisiteWithConcept]:
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
    response_model=list[ConceptResponse],
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
) -> list[ConceptResponse]:
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
    response_model=list[RootConceptResponse],
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
) -> list[RootConceptResponse]:
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
