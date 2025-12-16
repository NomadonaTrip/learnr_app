import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ProgressIndicator } from '../components/onboarding/ProgressIndicator'
import { QuestionCourseSelection } from '../components/onboarding/QuestionCourseSelection'
import { getCourseDisplayName } from '../components/onboarding/courseData'
import { QuestionMotivation } from '../components/onboarding/QuestionMotivation'
import { QuestionFamiliarity } from '../components/onboarding/QuestionFamiliarity'
import { useOnboardingStorage } from '../hooks/useOnboardingStorage'
import {
  trackOnboardingStarted,
  trackOnboardingQuestionViewed,
  trackOnboardingQuestionAnswered,
  trackOnboardingCompleted,
} from '../services/analyticsService'

const TOTAL_QUESTIONS = 3

type QuestionNumber = 1 | 2 | 3

/**
 * Determine initial question based on existing answers (resume scenario).
 */
function getInitialQuestion(answers: {
  course?: string
  motivation?: string
  familiarity?: string
}): QuestionNumber {
  if (!answers.course) return 1
  if (!answers.motivation) return 2
  if (!answers.familiarity) return 3
  return 3
}

export function OnboardingPage() {
  const navigate = useNavigate()
  const { answers, setAnswer } = useOnboardingStorage()
  const [currentQuestion, setCurrentQuestion] = useState<QuestionNumber>(() =>
    getInitialQuestion(answers)
  )
  const questionContainerRef = useRef<HTMLDivElement>(null)
  const hasTrackedStart = useRef(false)

  // Track onboarding started and initial question view
  useEffect(() => {
    if (!hasTrackedStart.current) {
      trackOnboardingStarted()
      trackOnboardingQuestionViewed(`q${currentQuestion}`)
      hasTrackedStart.current = true
    }
  }, [currentQuestion])

  // Track question view on question change (after initial)
  useEffect(() => {
    if (hasTrackedStart.current) {
      trackOnboardingQuestionViewed(`q${currentQuestion}`)
    }
  }, [currentQuestion])

  // Focus management on question change
  useEffect(() => {
    if (questionContainerRef.current) {
      // Announce to screen readers
      questionContainerRef.current.focus()
    }
  }, [currentQuestion])

  const courseName = getCourseDisplayName(answers.course || '')

  // Check if current question has an answer
  const hasCurrentAnswer = (): boolean => {
    switch (currentQuestion) {
      case 1:
        return !!answers.course
      case 2:
        return !!answers.motivation
      case 3:
        return !!answers.familiarity
      default:
        return false
    }
  }

  const handleCourseSelect = (courseId: string) => {
    setAnswer('course', courseId)
    trackOnboardingQuestionAnswered('q1', courseId)
  }

  const handleMotivationSelect = (motivationId: string) => {
    setAnswer('motivation', motivationId)
    trackOnboardingQuestionAnswered('q2', motivationId)
  }

  const handleFamiliaritySelect = (familiarityId: string) => {
    setAnswer('familiarity', familiarityId)
    trackOnboardingQuestionAnswered('q3', familiarityId)
  }

  const handleBack = () => {
    if (currentQuestion > 1) {
      setCurrentQuestion((prev) => (prev - 1) as QuestionNumber)
    }
  }

  const handleContinue = () => {
    if (!hasCurrentAnswer()) return

    if (currentQuestion < TOTAL_QUESTIONS) {
      setCurrentQuestion((prev) => (prev + 1) as QuestionNumber)
    } else {
      // Completed all questions
      trackOnboardingCompleted({
        course: answers.course!,
        motivation: answers.motivation!,
        familiarity: answers.familiarity!,
        initialBeliefPrior: answers.initialBeliefPrior!,
      })
      navigate('/register')
    }
  }

  const renderQuestion = () => {
    switch (currentQuestion) {
      case 1:
        return (
          <QuestionCourseSelection
            value={answers.course}
            onChange={handleCourseSelect}
          />
        )
      case 2:
        return (
          <QuestionMotivation
            value={answers.motivation}
            onChange={handleMotivationSelect}
            courseName={courseName}
          />
        )
      case 3:
        return (
          <QuestionFamiliarity
            value={answers.familiarity}
            onChange={handleFamiliaritySelect}
            courseName={courseName}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-cream flex flex-col">
      {/* Main content area */}
      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
        <div className="w-full max-w-lg">
          {/* Progress indicator */}
          <div className="mb-8">
            <ProgressIndicator
              currentQuestion={currentQuestion}
              totalQuestions={TOTAL_QUESTIONS}
            />
          </div>

          {/* Question card with glassmorphism */}
          <div
            ref={questionContainerRef}
            tabIndex={-1}
            role="region"
            aria-live="polite"
            aria-label={`Question ${currentQuestion} of ${TOTAL_QUESTIONS}`}
            className="glass-card-solid p-8 sm:p-10 shadow-card animate-spring-in focus:outline-none"
          >
            {renderQuestion()}
          </div>

          {/* Navigation controls */}
          <div className="mt-8 flex items-center justify-between gap-4">
            {/* Back button - hidden on Q1 */}
            {currentQuestion > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                className="
                  py-3 px-6 text-base font-medium text-charcoal/70
                  rounded-card border-2 border-charcoal/10 bg-white/50
                  hover:bg-white hover:border-charcoal/20
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                  transition-all duration-150
                "
              >
                Back
              </button>
            ) : (
              <div /> // Spacer to maintain layout
            )}

            {/* Continue button */}
            <button
              type="button"
              onClick={handleContinue}
              disabled={!hasCurrentAnswer()}
              className={`
                py-3 px-8 text-base font-semibold rounded-card
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                transition-all duration-150
                ${
                  hasCurrentAnswer()
                    ? 'bg-primary-500 text-white hover:bg-primary-600 hover-lift shadow-glass hover:shadow-glass-hover'
                    : 'bg-charcoal/10 text-charcoal/40 cursor-not-allowed'
                }
              `}
            >
              Continue
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
