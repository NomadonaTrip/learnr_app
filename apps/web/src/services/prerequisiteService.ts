import api from './api'

/**
 * A prerequisite that is currently blocking a concept from unlocking.
 * Mirrors backend schema `BlockingPrerequisite`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface BlockingPrerequisite {
  concept_id: string
  name: string
  current_mastery: number
  current_confidence: number
  required_mastery: number
  required_confidence: number
  responses_count: number
  progress_to_unlock: number
}

/**
 * Result of checking prerequisite mastery for a single concept.
 * Mirrors backend schema `GateCheckResult`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface GateCheckResult {
  concept_id: string
  concept_name: string
  is_unlocked: boolean
  blocking_prerequisites: BlockingPrerequisite[]
  closest_to_unlock: BlockingPrerequisite | null
  mastery_progress: number
  estimated_questions_to_unlock: number
}

/**
 * Unlock status for a single concept in a bulk query.
 * Mirrors backend schema `ConceptUnlockStatus`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface ConceptUnlockStatus {
  concept_id: string
  concept_name: string
  knowledge_area_id: string
  is_unlocked: boolean
  has_prerequisites: boolean
  prerequisite_count: number
  mastered_prerequisite_count: number
  mastery_progress: number
}

/**
 * Aggregated unlock status for a course or knowledge area.
 * Mirrors backend schema `BulkUnlockStatusResponse`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface BulkUnlockStatusResponse {
  knowledge_area_id: string | null
  total_concepts: number
  unlocked_count: number
  locked_count: number
  no_prerequisites_count: number
  concepts: ConceptUnlockStatus[]
}

/**
 * A single concept unlock event.
 * Mirrors backend schema `ConceptUnlockEventResponse`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface ConceptUnlockEvent {
  id: string
  user_id: string
  concept_id: string
  concept_name: string
  prerequisite_concept_id: string | null
  prerequisite_concept_name: string | null
  unlocked_at: string
}

/**
 * Lightweight concept-unlock item returned inline on session summaries.
 * Mirrors backend schema `SessionUnlockItem`. Story 4.11 AC 7 (Slice C).
 */
export interface SessionUnlockItem {
  concept_id: string
  concept_name: string
}

/**
 * Response listing recently unlocked concepts.
 * Mirrors backend schema `RecentUnlocksResponse`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface RecentUnlocksResponse {
  unlocks: ConceptUnlockEvent[]
  total_unlocked: number
}

/**
 * Response from attempting to access a locked concept.
 * Mirrors backend schema `OverrideAttemptResponse`.
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export interface OverrideAttemptResponse {
  concept_id: string
  concept_name: string
  was_locked: boolean
  override_allowed: boolean
  blocking_prerequisites: BlockingPrerequisite[]
  mastery_progress: number
  message: string
}

/**
 * Service for prerequisite / mastery-gate API calls.
 * Backend routes are mounted under `/concepts` (see routes/prerequisites.py).
 * Story 4.11: Prerequisite-Based Curriculum Navigation
 */
export const prerequisiteService = {
  /**
   * Get prerequisite mastery status for a single concept.
   * @param conceptId - Concept UUID
   * @returns Unlock status with blocking prerequisites and progress
   */
  async getPrerequisiteStatus(conceptId: string): Promise<GateCheckResult> {
    const response = await api.get<GateCheckResult>(
      `/concepts/${conceptId}/prerequisites/status`
    )
    return response.data
  },

  /**
   * Get unlock status for all concepts in a course (optionally filtered by KA).
   * @param courseId - Course UUID
   * @param kaId - Optional knowledge area ID filter
   * @returns Aggregated locked/unlocked counts and per-concept status
   */
  async getBulkUnlockStatus(
    courseId: string,
    kaId?: string
  ): Promise<BulkUnlockStatusResponse> {
    const response = await api.get<BulkUnlockStatusResponse>(
      '/concepts/unlock-status',
      { params: { course_id: courseId, ...(kaId ? { ka_id: kaId } : {}) } }
    )
    return response.data
  },

  /**
   * Get recently unlocked concepts for the current user.
   * @param limit - Maximum results to return (1-20, default 5)
   * @returns Recent unlock events
   */
  async getRecentUnlocks(limit = 5): Promise<RecentUnlocksResponse> {
    const response = await api.get<RecentUnlocksResponse>(
      '/concepts/recent-unlocks',
      { params: { limit } }
    )
    return response.data
  },

  /**
   * Attempt to access a locked concept (override). Always allowed; tracked for analytics.
   * @param conceptId - Concept UUID
   * @returns Override result with the concept's current lock status
   */
  async attemptLockedConcept(conceptId: string): Promise<OverrideAttemptResponse> {
    const response = await api.post<OverrideAttemptResponse>(
      `/concepts/${conceptId}/attempt-locked`
    )
    return response.data
  },
}
