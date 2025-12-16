/**
 * Course data and utilities for onboarding.
 */

export interface Course {
  id: string
  name: string
  description: string
}

/**
 * Available courses for onboarding.
 * Note: Course IDs must match the slug in the backend database.
 */
export const COURSES: Course[] = [
  {
    id: 'cbap',
    name: 'Business Analysis',
    description: 'CBAP, CCBA, and ECBA certification prep',
  },
  // Future courses will be added here
]

/**
 * Course display names for dynamic text in Q2/Q3.
 */
export const COURSE_DISPLAY_NAMES: Record<string, string> = {
  'cbap': 'Business Analysis',
}

/**
 * Get the display name for a course.
 */
export function getCourseDisplayName(courseId: string): string {
  return COURSE_DISPLAY_NAMES[courseId] || 'this subject'
}
