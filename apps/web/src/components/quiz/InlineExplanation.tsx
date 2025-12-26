import { useRef, useEffect } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

interface InlineExplanationProps {
  explanation: string
  onNextQuestion: () => void
  isLastQuestion: boolean
}

/**
 * InlineExplanation Component
 *
 * Displays explanation text and Next Question button below answer options.
 * Animates in with fade + slide unless user prefers reduced motion.
 */
export function InlineExplanation({
  explanation,
  onNextQuestion,
  isLastQuestion,
}: InlineExplanationProps) {
  const prefersReducedMotion = useReducedMotion()
  const containerRef = useRef<HTMLDivElement>(null)

  // Focus the explanation container after animation completes (400ms total sequence)
  useEffect(() => {
    const timer = setTimeout(
      () => {
        containerRef.current?.focus()
      },
      prefersReducedMotion ? 0 : 250
    )
    return () => clearTimeout(timer)
  }, [prefersReducedMotion])

  return (
    <div
      ref={containerRef}
      tabIndex={-1}
      className={`mt-4 ${
        prefersReducedMotion ? '' : 'animate-fade-slide-in'
      }`}
      style={
        prefersReducedMotion
          ? undefined
          : {
              animationDelay: '200ms',
              animationFillMode: 'both',
            }
      }
    >
      {/* Explanation box */}
      <div
        className="bg-gray-50 border border-gray-200 rounded-[14px] p-4"
        aria-labelledby="explanation-heading"
      >
        <h4
          id="explanation-heading"
          className="text-sm font-medium text-gray-700 mb-2"
        >
          Explanation
        </h4>
        <p className="text-sm text-gray-800 leading-relaxed">{explanation}</p>
      </div>

      {/* Next Question button */}
      <div className="mt-4 flex justify-center">
        <button
          onClick={onNextQuestion}
          className="px-8 py-3 bg-primary-600 text-white rounded-[14px] font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          aria-label={
            isLastQuestion ? 'Finish quiz session' : 'Proceed to next question'
          }
        >
          {isLastQuestion ? 'Finish Session' : 'Next Question'}
        </button>
      </div>
    </div>
  )
}
