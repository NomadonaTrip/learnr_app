import { useState, useRef, useEffect } from 'react'
import clsx from 'clsx'
import type { DiagnosticQuestion, AnswerLetter } from '../../types/diagnostic'

const ANSWER_OPTIONS: AnswerLetter[] = ['A', 'B', 'C', 'D']

interface DiagnosticQuestionCardProps {
  question: DiagnosticQuestion
  onSubmit: (answer: AnswerLetter) => void
  isSubmitting: boolean
}

/**
 * Displays a single diagnostic question with answer options.
 * Uses pill buttons with radio semantics for accessibility.
 */
export function DiagnosticQuestionCard({
  question,
  onSubmit,
  isSubmitting,
}: DiagnosticQuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<AnswerLetter | null>(null)
  const [announcement, setAnnouncement] = useState('')
  const optionRefs = useRef<(HTMLInputElement | null)[]>([])

  // Reset selection when question changes
  useEffect(() => {
    setSelectedAnswer(null)
    // Focus first option on question load
    setTimeout(() => {
      optionRefs.current[0]?.focus()
    }, 100)
  }, [question.id])

  const handleOptionSelect = (letter: AnswerLetter) => {
    setSelectedAnswer(letter)
    setAnnouncement(`Selected option ${letter}`)
  }

  const handleSubmit = () => {
    if (selectedAnswer) {
      onSubmit(selectedAnswer)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    const optionCount = ANSWER_OPTIONS.length

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight': {
        e.preventDefault()
        const nextIndex = (index + 1) % optionCount
        optionRefs.current[nextIndex]?.focus()
        break
      }
      case 'ArrowUp':
      case 'ArrowLeft': {
        e.preventDefault()
        const prevIndex = (index - 1 + optionCount) % optionCount
        optionRefs.current[prevIndex]?.focus()
        break
      }
      case 'Enter':
      case ' ':
        e.preventDefault()
        handleOptionSelect(ANSWER_OPTIONS[index])
        break
    }
  }

  return (
    <article aria-labelledby="question-text" className="w-full">
      {/* Screen reader announcement for selection */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      <h2
        id="question-text"
        className="text-lg sm:text-xl font-medium text-gray-900 mb-6 leading-relaxed"
      >
        {question.question_text}
      </h2>

      <fieldset className="mb-6">
        <legend className="sr-only">
          Choose your answer for: {question.question_text}
        </legend>

        <div className="space-y-3">
          {ANSWER_OPTIONS.map((letter, index) => (
            <div key={letter} className="relative">
              <input
                ref={(el) => (optionRefs.current[index] = el)}
                type="radio"
                id={`answer-${letter}`}
                name="answer"
                value={letter}
                checked={selectedAnswer === letter}
                onChange={() => handleOptionSelect(letter)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className="sr-only peer"
                aria-describedby={`answer-label-${letter}`}
                disabled={isSubmitting}
              />
              <label
                id={`answer-label-${letter}`}
                htmlFor={`answer-${letter}`}
                className={clsx(
                  'flex items-start w-full p-4 rounded-card text-left transition-colors cursor-pointer',
                  'border-2 min-h-[44px]',
                  'peer-focus:ring-2 peer-focus:ring-primary-500 peer-focus:ring-offset-2',
                  selectedAnswer === letter
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300',
                  isSubmitting && 'opacity-50 cursor-not-allowed'
                )}
              >
                <span className="font-semibold text-gray-700 mr-3 shrink-0">
                  {letter}.
                </span>
                <span className="text-gray-900">
                  {question.options[letter]}
                </span>
              </label>
            </div>
          ))}
        </div>
      </fieldset>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!selectedAnswer || isSubmitting}
        aria-disabled={!selectedAnswer || isSubmitting}
        className={clsx(
          'w-full py-3 px-6 rounded-card font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          selectedAnswer && !isSubmitting
            ? 'bg-primary-600 text-white hover:bg-primary-700'
            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
        )}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Answer'}
      </button>
    </article>
  )
}
