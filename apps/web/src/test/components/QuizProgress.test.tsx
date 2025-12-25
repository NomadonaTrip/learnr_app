import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QuizProgress } from '../../components/quiz/QuizProgress'

describe('QuizProgress', () => {
  describe('question counter display', () => {
    it('displays current question number and target', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={5}
          totalAnswered={7}
        />
      )

      expect(screen.getByText('Question 8')).toBeInTheDocument()
      expect(screen.getByText('of 12')).toBeInTheDocument()
    })

    it('displays first question correctly', () => {
      render(
        <QuizProgress
          currentQuestionNumber={1}
          questionTarget={10}
          correctCount={0}
          totalAnswered={0}
        />
      )

      expect(screen.getByText('Question 1')).toBeInTheDocument()
      expect(screen.getByText('of 10')).toBeInTheDocument()
    })
  })

  describe('accuracy display', () => {
    it('displays accuracy when questions have been answered', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={5}
          totalAnswered={7}
        />
      )

      // 5/7 = 71%
      expect(screen.getByText('71%')).toBeInTheDocument()
      expect(screen.getByText('accuracy')).toBeInTheDocument()
    })

    it('does not display accuracy for first question', () => {
      render(
        <QuizProgress
          currentQuestionNumber={1}
          questionTarget={12}
          correctCount={0}
          totalAnswered={0}
        />
      )

      expect(screen.queryByText('accuracy')).not.toBeInTheDocument()
    })

    it('displays 100% accuracy when all answers correct', () => {
      render(
        <QuizProgress
          currentQuestionNumber={6}
          questionTarget={12}
          correctCount={5}
          totalAnswered={5}
        />
      )

      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  describe('progress bar', () => {
    it('has progressbar role with correct values', () => {
      render(
        <QuizProgress
          currentQuestionNumber={7}
          questionTarget={12}
          correctCount={4}
          totalAnswered={6}
        />
      )

      const progressbar = screen.getByRole('progressbar')
      expect(progressbar).toHaveAttribute('aria-valuenow', '50')
      expect(progressbar).toHaveAttribute('aria-valuemin', '0')
      expect(progressbar).toHaveAttribute('aria-valuemax', '100')
    })

    it('displays 0% at start of quiz', () => {
      render(
        <QuizProgress
          currentQuestionNumber={1}
          questionTarget={10}
          correctCount={0}
          totalAnswered={0}
        />
      )

      expect(screen.getByText('0% complete')).toBeInTheDocument()
    })

    it('displays correct percentage for mid-session', () => {
      render(
        <QuizProgress
          currentQuestionNumber={7}
          questionTarget={12}
          correctCount={4}
          totalAnswered={6}
        />
      )

      // (7-1)/12 = 50%
      expect(screen.getByText('50% complete')).toBeInTheDocument()
    })
  })

  describe('correct count display', () => {
    it('displays correct count out of total answered', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={5}
          totalAnswered={7}
        />
      )

      expect(screen.getByText('5/7 correct')).toBeInTheDocument()
    })

    it('displays 0/0 at start of quiz', () => {
      render(
        <QuizProgress
          currentQuestionNumber={1}
          questionTarget={12}
          correctCount={0}
          totalAnswered={0}
        />
      )

      expect(screen.getByText('0/0 correct')).toBeInTheDocument()
    })
  })

  describe('accuracy color coding', () => {
    it('displays green color for accuracy >= 70%', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={7}
          totalAnswered={10}
        />
      )

      // 7/10 = 70%
      const accuracyElement = screen.getByText('70%')
      expect(accuracyElement).toHaveClass('text-green-600')
    })

    it('displays orange color for accuracy 50-69%', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={5}
          totalAnswered={10}
        />
      )

      // 5/10 = 50%
      const accuracyElement = screen.getByText('50%')
      expect(accuracyElement).toHaveClass('text-orange-600')
    })

    it('displays red color for accuracy < 50%', () => {
      render(
        <QuizProgress
          currentQuestionNumber={8}
          questionTarget={12}
          correctCount={3}
          totalAnswered={10}
        />
      )

      // 3/10 = 30%
      const accuracyElement = screen.getByText('30%')
      expect(accuracyElement).toHaveClass('text-red-600')
    })
  })

  describe('accessibility', () => {
    it('has aria-label describing progress', () => {
      render(
        <QuizProgress
          currentQuestionNumber={7}
          questionTarget={12}
          correctCount={4}
          totalAnswered={6}
        />
      )

      const progressbar = screen.getByRole('progressbar')
      expect(progressbar).toHaveAttribute(
        'aria-label',
        'Quiz progress: 6 of 12 questions completed'
      )
    })
  })
})
