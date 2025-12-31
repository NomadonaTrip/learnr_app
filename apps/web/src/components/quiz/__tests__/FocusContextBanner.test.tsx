import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FocusContextBanner } from '../FocusContextBanner'

describe('FocusContextBanner', () => {
  describe('basic rendering', () => {
    it('renders KA focus type with correct label', () => {
      render(<FocusContextBanner focusType="ka" targetName="Elicitation" />)

      expect(screen.getByText('Focused Knowledge Area')).toBeInTheDocument()
      expect(screen.getByText('Elicitation')).toBeInTheDocument()
    })

    it('renders concept focus type with correct label', () => {
      render(<FocusContextBanner focusType="concept" targetName="Data Types" />)

      expect(screen.getByText('Focused Concept')).toBeInTheDocument()
      expect(screen.getByText('Data Types')).toBeInTheDocument()
    })

    it('has accessible banner role', () => {
      render(<FocusContextBanner focusType="ka" targetName="Test" />)

      expect(screen.getByRole('banner')).toBeInTheDocument()
      expect(screen.getByRole('banner')).toHaveAttribute(
        'aria-label',
        'Focused practice context'
      )
    })
  })

  describe('mastery display', () => {
    it('displays mastery percentage when provided', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.75}
        />
      )

      expect(screen.getByText('Mastery')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('applies green color for high mastery (>= 80%)', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.85}
        />
      )

      const masteryValue = screen.getByText('85%')
      expect(masteryValue).toHaveClass('text-green-600')
    })

    it('applies amber color for medium mastery (50-79%)', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.65}
        />
      )

      const masteryValue = screen.getByText('65%')
      expect(masteryValue).toHaveClass('text-amber-600')
    })

    it('applies red color for low mastery (< 50%)', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.3}
        />
      )

      const masteryValue = screen.getByText('30%')
      expect(masteryValue).toHaveClass('text-red-600')
    })

    it('does not show mastery when not provided', () => {
      render(<FocusContextBanner focusType="ka" targetName="Test" />)

      expect(screen.queryByText('Mastery')).not.toBeInTheDocument()
    })
  })

  describe('improvement display', () => {
    it('displays positive improvement with plus sign', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          improvement={0.15}
        />
      )

      expect(screen.getByText('Session')).toBeInTheDocument()
      expect(screen.getByText('+15%')).toBeInTheDocument()
    })

    it('displays negative improvement with minus sign', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          improvement={-0.1}
        />
      )

      expect(screen.getByText('-10%')).toBeInTheDocument()
    })

    it('displays zero improvement', () => {
      render(
        <FocusContextBanner focusType="ka" targetName="Test" improvement={0} />
      )

      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('applies green color for positive improvement', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          improvement={0.1}
        />
      )

      const improvementValue = screen.getByText('+10%')
      expect(improvementValue).toHaveClass('text-green-600')
    })

    it('applies red color for negative improvement', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          improvement={-0.05}
        />
      )

      const improvementValue = screen.getByText('-5%')
      expect(improvementValue).toHaveClass('text-red-600')
    })

    it('applies gray color for zero improvement', () => {
      render(
        <FocusContextBanner focusType="ka" targetName="Test" improvement={0} />
      )

      const improvementValue = screen.getByText('0%')
      expect(improvementValue).toHaveClass('text-gray-500')
    })
  })

  describe('questions in focus display', () => {
    it('displays questions in focus count when provided with other metrics', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.5}
          questionsInFocus={5}
        />
      )

      expect(screen.getByText('In Focus')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('does not show questions when count is 0', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          currentMastery={0.5}
          questionsInFocus={0}
        />
      )

      expect(screen.queryByText('In Focus')).not.toBeInTheDocument()
    })

    it('does not show metrics section when no mastery or improvement provided', () => {
      render(
        <FocusContextBanner
          focusType="ka"
          targetName="Test"
          questionsInFocus={5}
        />
      )

      // Metrics section not rendered without mastery or improvement
      expect(screen.queryByText('In Focus')).not.toBeInTheDocument()
    })
  })

  describe('combined metrics', () => {
    it('displays all metrics together', () => {
      render(
        <FocusContextBanner
          focusType="concept"
          targetName="Variables"
          currentMastery={0.72}
          improvement={0.12}
          questionsInFocus={3}
        />
      )

      expect(screen.getByText('Focused Concept')).toBeInTheDocument()
      expect(screen.getByText('Variables')).toBeInTheDocument()
      expect(screen.getByText('72%')).toBeInTheDocument()
      expect(screen.getByText('+12%')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })
})
