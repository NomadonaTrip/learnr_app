/**
 * Unit tests for ReviewQuestion and ReviewFeedback components.
 * Story 4.9: Post-Session Review Mode
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReviewQuestion, ReviewFeedback } from '../ReviewQuestion'
import type { ReviewQuestionResponse, ReviewAnswerResponse } from '../../../services/reviewService'

// Mock useReducedMotion hook
vi.mock('../../../hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}))

describe('ReviewQuestion', () => {
  const defaultQuestion: ReviewQuestionResponse = {
    question_id: 'q-123',
    question_text: 'What is the primary benefit of adaptive learning?',
    options: {
      A: 'Fixed learning paths',
      B: 'Personalized content',
      C: 'Faster completion',
      D: 'Less content',
    },
    review_number: 1,
    total_to_review: 3,
  }

  const defaultProps = {
    question: defaultQuestion,
    selectedAnswer: null,
    onSelectAnswer: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('basic rendering', () => {
    it('renders the question card', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByLabelText('Review question card')).toBeInTheDocument()
    })

    it('displays review mode badge', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByText('Review Mode')).toBeInTheDocument()
    })

    it('displays question progress', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByText('Question 1 of 3')).toBeInTheDocument()
    })

    it('displays the question text', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByText('What is the primary benefit of adaptive learning?')).toBeInTheDocument()
    })

    it('displays all answer options', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByText('Fixed learning paths')).toBeInTheDocument()
      expect(screen.getByText('Personalized content')).toBeInTheDocument()
      expect(screen.getByText('Faster completion')).toBeInTheDocument()
      expect(screen.getByText('Less content')).toBeInTheDocument()
    })

    it('has radiogroup role for answer options', () => {
      render(<ReviewQuestion {...defaultProps} />)

      expect(screen.getByRole('radiogroup')).toBeInTheDocument()
    })
  })

  describe('answer selection', () => {
    it('calls onSelectAnswer when an option is clicked', () => {
      const onSelectAnswer = vi.fn()
      render(<ReviewQuestion {...defaultProps} onSelectAnswer={onSelectAnswer} />)

      fireEvent.click(screen.getByText('Personalized content'))

      expect(onSelectAnswer).toHaveBeenCalledWith('B')
    })

    it('shows selected state for chosen answer', () => {
      render(<ReviewQuestion {...defaultProps} selectedAnswer="B" />)

      const selectedOption = screen.getByRole('radio', { checked: true })
      expect(selectedOption).toBeInTheDocument()
    })

    it('does not call onSelectAnswer when feedback is showing', () => {
      const onSelectAnswer = vi.fn()
      const feedbackResult: ReviewAnswerResponse = {
        is_correct: true,
        was_reinforced: true,
        correct_answer: 'B',
        explanation: 'Personalized content adapts to the learner.',
        concepts_updated: [],
        feedback_message: 'Great improvement!',
        reading_link: null,
      }

      render(
        <ReviewQuestion
          {...defaultProps}
          onSelectAnswer={onSelectAnswer}
          showFeedback={true}
          feedbackResult={feedbackResult}
          selectedAnswer="B"
        />
      )

      fireEvent.click(screen.getByText('Personalized content'))

      expect(onSelectAnswer).not.toHaveBeenCalled()
    })
  })

  describe('feedback display', () => {
    const correctFeedback: ReviewAnswerResponse = {
      is_correct: true,
      was_reinforced: true,
      correct_answer: 'B',
      explanation: 'Personalized content adapts to the learner.',
      concepts_updated: [],
      feedback_message: 'Great improvement!',
      reading_link: null,
    }

    const incorrectFeedback: ReviewAnswerResponse = {
      is_correct: false,
      was_reinforced: false,
      correct_answer: 'B',
      explanation: 'Personalized content adapts to the learner.',
      concepts_updated: [],
      feedback_message: 'Still needs practice.',
      reading_link: '/reading?concept=adaptive',
    }

    it('highlights correct answer in green when feedback is shown', () => {
      render(
        <ReviewQuestion
          {...defaultProps}
          selectedAnswer="B"
          showFeedback={true}
          feedbackResult={correctFeedback}
        />
      )

      // The correct answer button should have green styling
      const correctButton = screen.getByLabelText(/Option B.*Correct answer/)
      expect(correctButton).toHaveClass('border-green-500')
    })

    it('highlights incorrect selection in red when feedback is shown', () => {
      render(
        <ReviewQuestion
          {...defaultProps}
          selectedAnswer="A"
          showFeedback={true}
          feedbackResult={incorrectFeedback}
        />
      )

      // The incorrect selection should have red styling
      const incorrectButton = screen.getByLabelText(/Option A.*Your incorrect selection/)
      expect(incorrectButton).toHaveClass('border-red-500')
    })

    it('provides screen reader announcement for feedback', () => {
      render(
        <ReviewQuestion
          {...defaultProps}
          selectedAnswer="B"
          showFeedback={true}
          feedbackResult={correctFeedback}
        />
      )

      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('disables all options when feedback is showing', () => {
      render(
        <ReviewQuestion
          {...defaultProps}
          selectedAnswer="B"
          showFeedback={true}
          feedbackResult={correctFeedback}
        />
      )

      const options = screen.getAllByRole('radio')
      options.forEach((option) => {
        expect(option).toHaveAttribute('aria-disabled', 'true')
      })
    })
  })
})

describe('ReviewFeedback', () => {
  const reinforcedResult: ReviewAnswerResponse = {
    is_correct: true,
    was_reinforced: true,
    correct_answer: 'B',
    explanation: 'Personalized content adapts to the learner.',
    concepts_updated: [
      { concept_id: 'c-1', name: 'Adaptive Learning', new_mastery: 0.85 },
    ],
    feedback_message: 'Great improvement! You got it right this time.',
    reading_link: null,
  }

  const stillIncorrectResult: ReviewAnswerResponse = {
    is_correct: false,
    was_reinforced: false,
    correct_answer: 'B',
    explanation: 'Personalized content adapts to the learner.',
    concepts_updated: [],
    feedback_message: 'Still needs practice. Review the material.',
    reading_link: '/reading?concept=adaptive',
  }

  describe('reinforced feedback', () => {
    it('shows reinforced badge when answer was reinforced', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.getByText('Reinforced!')).toBeInTheDocument()
    })

    it('displays feedback message', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.getByText('Great improvement! You got it right this time.')).toBeInTheDocument()
    })

    it('displays explanation', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.getByText('Personalized content adapts to the learner.')).toBeInTheDocument()
    })
  })

  describe('still incorrect feedback', () => {
    it('does not show reinforced badge for incorrect answer', () => {
      render(
        <ReviewFeedback
          feedbackResult={stillIncorrectResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.queryByText('Reinforced!')).not.toBeInTheDocument()
    })

    it('shows study link for incorrect answers', () => {
      render(
        <ReviewFeedback
          feedbackResult={stillIncorrectResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      const studyLink = screen.getByText('Study this concept')
      expect(studyLink).toBeInTheDocument()
      expect(studyLink.closest('a')).toHaveAttribute('href', '/reading?concept=adaptive')
    })
  })

  describe('navigation', () => {
    it('shows "Next Question" button when not last question', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.getByText('Next Question')).toBeInTheDocument()
    })

    it('shows "View Summary" button on last question', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={true}
        />
      )

      expect(screen.getByText('View Summary')).toBeInTheDocument()
    })

    it('calls onNextQuestion when button is clicked', () => {
      const onNextQuestion = vi.fn()
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={onNextQuestion}
          isLastQuestion={false}
        />
      )

      fireEvent.click(screen.getByText('Next Question'))

      expect(onNextQuestion).toHaveBeenCalledTimes(1)
    })
  })

  describe('accessibility', () => {
    it('has status role for live announcements', () => {
      render(
        <ReviewFeedback
          feedbackResult={reinforcedResult}
          onNextQuestion={vi.fn()}
          isLastQuestion={false}
        />
      )

      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })
})
