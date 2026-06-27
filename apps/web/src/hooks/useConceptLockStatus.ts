import { useQuery } from '@tanstack/react-query'
import {
  prerequisiteService,
  GateCheckResult,
  BulkUnlockStatusResponse,
} from '../services/prerequisiteService'

/**
 * Query-key factory for prerequisite/unlock data.
 * Keeps cache keys consistent and invalidatable across the app.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export const conceptLockKeys = {
  all: ['concept-lock'] as const,
  status: (conceptId: string) => [...conceptLockKeys.all, 'status', conceptId] as const,
  bulk: (courseId: string, kaId?: string) =>
    [...conceptLockKeys.all, 'bulk', courseId, kaId ?? null] as const,
}

/**
 * Fetch the prerequisite lock status for a single concept.
 *
 * Use this to drive lock/unlock badges, "locked" gating on a concept,
 * and tooltips that list the blocking prerequisites (AC 4 & AC 5).
 *
 * @param conceptId - Concept UUID, or undefined/null to disable the query
 * @returns react-query result with `GateCheckResult`
 *
 * @example
 * const { data, isLoading } = useConceptLockStatus(conceptId)
 * if (data && !data.is_unlocked) showLockedBadge(data.blocking_prerequisites)
 */
export function useConceptLockStatus(conceptId: string | null | undefined) {
  return useQuery<GateCheckResult>({
    queryKey: conceptLockKeys.status(conceptId ?? ''),
    queryFn: () => prerequisiteService.getPrerequisiteStatus(conceptId as string),
    enabled: Boolean(conceptId),
    staleTime: 30_000,
  })
}

/**
 * Fetch unlock status for all concepts in a course (optionally a single KA).
 *
 * Use this for the curriculum/dashboard view that shows locked vs unlocked
 * counts and per-concept status (AC 10).
 *
 * @param courseId - Course UUID, or undefined/null to disable the query
 * @param kaId - Optional knowledge area filter
 * @returns react-query result with `BulkUnlockStatusResponse`
 */
export function useBulkUnlockStatus(
  courseId: string | null | undefined,
  kaId?: string
) {
  return useQuery<BulkUnlockStatusResponse>({
    queryKey: conceptLockKeys.bulk(courseId ?? '', kaId),
    queryFn: () => prerequisiteService.getBulkUnlockStatus(courseId as string, kaId),
    enabled: Boolean(courseId),
    staleTime: 30_000,
  })
}
