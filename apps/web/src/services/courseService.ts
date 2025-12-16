import api from './api'

/** Course detail from API */
export interface CourseDetail {
  id: string
  slug: string
  name: string
  description: string
  corpus_name: string
  knowledge_areas: {
    id: string
    name: string
    abbreviation: string
    color_hex: string
  }[]
  default_diagnostic_count: number
  mastery_threshold: number
  gap_threshold: number
  confidence_threshold: number
  icon_url: string | null
  color_hex: string | null
  is_active: boolean
  is_public: boolean
  created_at: string
  updated_at: string
}

interface CourseDetailResponse {
  data: CourseDetail
  meta: {
    timestamp: string
    version: string
  }
}

/**
 * Service for course API calls.
 */
export const courseService = {
  /**
   * Fetch course details by slug.
   * @param slug - Course slug (e.g., 'business-analysis')
   * @returns Course details including UUID
   */
  async fetchCourseBySlug(slug: string): Promise<CourseDetail> {
    const response = await api.get<CourseDetailResponse>(`/courses/${slug}`)
    return response.data.data
  },
}
