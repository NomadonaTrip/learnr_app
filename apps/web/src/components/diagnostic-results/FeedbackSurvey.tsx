import { useState } from 'react'
import clsx from 'clsx'

interface FeedbackSurveyProps {
  onSubmit: (rating: number, comment?: string) => void
  isSubmitting: boolean
  isSuccess: boolean
}

/**
 * Post-diagnostic feedback survey.
 * Collects accuracy rating (1-5 stars) and optional comment.
 */
export function FeedbackSurvey({
  onSubmit,
  isSubmitting,
  isSuccess,
}: FeedbackSurveyProps) {
  const [rating, setRating] = useState<number>(0)
  const [hoveredRating, setHoveredRating] = useState<number>(0)
  const [comment, setComment] = useState<string>('')
  const [showComment, setShowComment] = useState(false)

  if (isSuccess) {
    return (
      <section
        className="bg-green-50 border border-green-200 rounded-xl p-6"
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center gap-3">
          <svg
            className="w-6 h-6 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-green-700 font-medium">
            Thank you for your feedback! It helps us improve the diagnostic experience.
          </p>
        </div>
      </section>
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (rating === 0) return
    onSubmit(rating, comment.trim() || undefined)
  }

  return (
    <section
      className="bg-gray-50 rounded-xl p-6"
      aria-labelledby="feedback-title"
    >
      <h2 id="feedback-title" className="text-lg font-semibold text-gray-900 mb-2">
        How accurate does this feel?
      </h2>
      <p className="text-sm text-gray-600 mb-4">
        Your feedback helps us improve the diagnostic experience.
      </p>

      <form onSubmit={handleSubmit}>
        {/* Star rating */}
        <div className="mb-4">
          <fieldset>
            <legend className="sr-only">Rate the accuracy of your results (1-5 stars)</legend>
            <div className="flex gap-2" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((star) => {
                const isActive = star <= (hoveredRating || rating)
                return (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoveredRating(star)}
                    onMouseLeave={() => setHoveredRating(0)}
                    className={clsx(
                      'p-1 rounded-full transition-colors',
                      'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                      'hover:scale-110 transition-transform'
                    )}
                    role="radio"
                    aria-checked={star === rating}
                    aria-label={`${star} star${star !== 1 ? 's' : ''}`}
                  >
                    <svg
                      className={clsx(
                        'w-8 h-8 transition-colors',
                        isActive ? 'text-amber-400 fill-amber-400' : 'text-gray-300'
                      )}
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                      fill={isActive ? 'currentColor' : 'none'}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
                      />
                    </svg>
                  </button>
                )
              })}
            </div>
          </fieldset>
          {rating > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              {rating === 1 && "Not accurate at all"}
              {rating === 2 && "Slightly accurate"}
              {rating === 3 && "Moderately accurate"}
              {rating === 4 && "Mostly accurate"}
              {rating === 5 && "Very accurate"}
            </p>
          )}
        </div>

        {/* Optional comment toggle */}
        {!showComment && rating > 0 && (
          <button
            type="button"
            onClick={() => setShowComment(true)}
            className="text-sm text-primary-600 hover:text-primary-700 mb-4"
          >
            + Add a comment (optional)
          </button>
        )}

        {/* Comment textarea */}
        {showComment && (
          <div className="mb-4">
            <label htmlFor="feedback-comment" className="sr-only">
              Additional feedback (optional)
            </label>
            <textarea
              id="feedback-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Share any additional thoughts about the diagnostic..."
              maxLength={500}
              rows={3}
              className={clsx(
                'w-full px-4 py-2 rounded-lg border border-gray-300',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'text-sm resize-none'
              )}
            />
            <p className="text-xs text-gray-400 mt-1 text-right">
              {comment.length}/500
            </p>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={rating === 0 || isSubmitting}
          className={clsx(
            'px-4 py-2 rounded-lg font-medium text-sm',
            'transition-colors',
            rating > 0
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed',
            isSubmitting && 'opacity-70 cursor-wait'
          )}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </section>
  )
}
