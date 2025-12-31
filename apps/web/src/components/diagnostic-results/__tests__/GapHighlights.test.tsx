import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GapHighlights } from '../GapHighlights'
import type { ConceptGap } from '../../../types/diagnostic'

const mockGaps: ConceptGap[] = [
  {
    concept_id: 'concept-1',
    name: 'Data Types',
    mastery_probability: 0.25,
    knowledge_area: 'Fundamentals',
  },
  {
    concept_id: 'concept-2',
    name: 'Variables',
    mastery_probability: 0.35,
    knowledge_area: 'Fundamentals',
  },
  {
    concept_id: 'concept-3',
    name: 'Functions',
    mastery_probability: 0.42,
    knowledge_area: 'Core Concepts',
  },
]

describe('GapHighlights', () => {
  describe('empty state', () => {
    it('shows congratulatory message when no gaps', () => {
      render(<GapHighlights gaps={[]} />)

      expect(screen.getByText('Knowledge Gaps')).toBeInTheDocument()
      expect(
        screen.getByText('Great news! No significant knowledge gaps were identified.')
      ).toBeInTheDocument()
    })
  })

  describe('with gaps', () => {
    it('displays gap list with names and mastery', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.getByText('Top Knowledge Gaps')).toBeInTheDocument()
      expect(screen.getByText('Data Types')).toBeInTheDocument()
      expect(screen.getByText('Variables')).toBeInTheDocument()
      expect(screen.getByText('Functions')).toBeInTheDocument()
      expect(screen.getByText('25%')).toBeInTheDocument()
      expect(screen.getByText('35%')).toBeInTheDocument()
      expect(screen.getByText('42%')).toBeInTheDocument()
    })

    it('shows knowledge area for each gap', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.getAllByText('Fundamentals')).toHaveLength(2)
      expect(screen.getByText('Core Concepts')).toBeInTheDocument()
    })

    it('shows gap count badge', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.getByText('3 gaps identified')).toBeInTheDocument()
    })

    it('respects maxDisplay prop', () => {
      const manyGaps = Array.from({ length: 15 }, (_, i) => ({
        concept_id: `concept-${i}`,
        name: `Concept ${i + 1}`,
        mastery_probability: 0.2 + i * 0.02,
        knowledge_area: 'Test Area',
      }))

      render(<GapHighlights gaps={manyGaps} maxDisplay={5} />)

      expect(screen.getByText('Showing top 5 of 15 identified gaps')).toBeInTheDocument()
      expect(screen.getByText('Concept 1')).toBeInTheDocument()
      expect(screen.getByText('Concept 5')).toBeInTheDocument()
      expect(screen.queryByText('Concept 6')).not.toBeInTheDocument()
    })
  })

  describe('Practice functionality', () => {
    it('shows Practice buttons when handler is provided', () => {
      const mockHandler = vi.fn()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      const practiceButtons = screen.getAllByRole('button', { name: /^Practice/ })
      // Should have individual practice buttons for each gap
      expect(practiceButtons.length).toBeGreaterThanOrEqual(3)
    })

    it('does not show Practice buttons when handler is not provided', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.queryByRole('button', { name: /Practice/ })).not.toBeInTheDocument()
    })

    it('calls handler with single concept ID when Practice button is clicked', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      const practiceDataTypes = screen.getByRole('button', { name: 'Practice Data Types' })
      await user.click(practiceDataTypes)

      expect(mockHandler).toHaveBeenCalledWith(['concept-1'])
    })

    it('shows checkboxes for multi-select when handler is provided', () => {
      const mockHandler = vi.fn()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(3)
    })

    it('does not show checkboxes when handler is not provided', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    })

    it('toggles selection when checkbox is clicked', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      const checkbox = screen.getByRole('checkbox', { name: 'Select Data Types for practice' })
      expect(checkbox).not.toBeChecked()

      await user.click(checkbox)
      expect(checkbox).toBeChecked()

      await user.click(checkbox)
      expect(checkbox).not.toBeChecked()
    })

    it('shows Practice Selected button when concepts are selected', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      // Initially no "Practice Selected" button
      expect(screen.queryByRole('button', { name: /Practice Selected/ })).not.toBeInTheDocument()

      // Select first checkbox
      const checkbox = screen.getByRole('checkbox', { name: 'Select Data Types for practice' })
      await user.click(checkbox)

      // Now should show Practice Selected button
      expect(screen.getByRole('button', { name: 'Practice 1 selected concepts' })).toBeInTheDocument()
      expect(screen.getByText('Practice Selected (1)')).toBeInTheDocument()
    })

    it('calls handler with all selected concept IDs when Practice Selected is clicked', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      // Select first two concepts
      await user.click(screen.getByRole('checkbox', { name: 'Select Data Types for practice' }))
      await user.click(screen.getByRole('checkbox', { name: 'Select Variables for practice' }))

      // Click Practice Selected
      const practiceSelectedBtn = screen.getByText('Practice Selected (2)')
      await user.click(practiceSelectedBtn)

      expect(mockHandler).toHaveBeenCalledTimes(1)
      expect(mockHandler).toHaveBeenCalledWith(
        expect.arrayContaining(['concept-1', 'concept-2'])
      )
    })

    it('shows Select All button when multiple gaps exist', () => {
      const mockHandler = vi.fn()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      expect(screen.getByText('Select All')).toBeInTheDocument()
    })

    it('selects all when Select All is clicked', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      await user.click(screen.getByText('Select All'))

      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeChecked()
      })
      expect(screen.getByText('Deselect All')).toBeInTheDocument()
    })

    it('deselects all when Deselect All is clicked', async () => {
      const mockHandler = vi.fn()
      const user = userEvent.setup()
      render(<GapHighlights gaps={mockGaps} onConceptPracticeClick={mockHandler} />)

      // First select all
      await user.click(screen.getByText('Select All'))

      // Then deselect all
      await user.click(screen.getByText('Deselect All'))

      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(checkbox => {
        expect(checkbox).not.toBeChecked()
      })
      expect(screen.getByText('Select All')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has accessible section with heading', () => {
      render(<GapHighlights gaps={mockGaps} />)

      // Section has aria-labelledby pointing to the heading
      const heading = screen.getByRole('heading', { name: 'Top Knowledge Gaps' })
      expect(heading).toHaveAttribute('id', 'gaps-title')
    })

    it('has accessible list of gaps', () => {
      render(<GapHighlights gaps={mockGaps} />)

      expect(screen.getByRole('list', { name: 'List of knowledge gaps' })).toBeInTheDocument()
    })

    it('has progress bars with proper ARIA attributes', () => {
      render(<GapHighlights gaps={mockGaps} />)

      const progressBars = screen.getAllByRole('progressbar')
      expect(progressBars).toHaveLength(3)

      const firstProgressBar = progressBars[0]
      expect(firstProgressBar).toHaveAttribute('aria-valuenow', '25')
      expect(firstProgressBar).toHaveAttribute('aria-valuemin', '0')
      expect(firstProgressBar).toHaveAttribute('aria-valuemax', '100')
    })
  })
})
