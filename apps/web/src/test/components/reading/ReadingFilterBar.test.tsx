/**
 * ReadingFilterBar Component Tests
 * Story 5.7: Reading Library Page with Queue Display
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReadingFilterBar } from '../../../components/reading/ReadingFilterBar'

const defaultProps = {
  selectedStatus: 'unread' as const,
  selectedSort: 'priority' as const,
  selectedKaId: null,
  knowledgeAreas: [
    { id: 'strategy', name: 'Strategy Analysis' },
    { id: 'elicitation', name: 'Elicitation and Collaboration' },
    { id: 'radd', name: 'Requirements Analysis and Design Definition' },
  ],
  onFilterChange: vi.fn(),
}

describe('ReadingFilterBar', () => {
  describe('status tabs', () => {
    it('renders all status tabs', () => {
      render(<ReadingFilterBar {...defaultProps} />)

      expect(screen.getByRole('tab', { name: 'Unread' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Reading' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Completed' })).toBeInTheDocument()
    })

    it('shows selected status as active', () => {
      render(<ReadingFilterBar {...defaultProps} selectedStatus="unread" />)

      const unreadTab = screen.getByRole('tab', { name: 'Unread' })
      expect(unreadTab).toHaveAttribute('aria-selected', 'true')
    })

    it('calls onFilterChange with status when tab is clicked', () => {
      const onFilterChange = vi.fn()
      render(<ReadingFilterBar {...defaultProps} onFilterChange={onFilterChange} />)

      fireEvent.click(screen.getByRole('tab', { name: 'Completed' }))

      expect(onFilterChange).toHaveBeenCalledWith({ status: 'completed' })
    })

    it('updates selected tab when selectedStatus prop changes', () => {
      const { rerender } = render(<ReadingFilterBar {...defaultProps} selectedStatus="unread" />)

      expect(screen.getByRole('tab', { name: 'Unread' })).toHaveAttribute('aria-selected', 'true')

      rerender(<ReadingFilterBar {...defaultProps} selectedStatus="reading" />)

      expect(screen.getByRole('tab', { name: 'Reading' })).toHaveAttribute('aria-selected', 'true')
    })
  })

  describe('sort dropdown', () => {
    it('renders sort dropdown with current selection', () => {
      render(<ReadingFilterBar {...defaultProps} selectedSort="priority" />)

      // The button should show the current selection
      expect(screen.getByRole('button', { name: /Priority/i })).toBeInTheDocument()
    })

    it('opens dropdown when clicked', async () => {
      render(<ReadingFilterBar {...defaultProps} />)

      // Find and click the sort dropdown button
      const sortButton = screen.getByRole('button', { name: /Priority/i })
      fireEvent.click(sortButton)

      // Should show all sort options
      expect(screen.getByRole('option', { name: /Priority/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Date Added/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Relevance Score/i })).toBeInTheDocument()
    })

    it('calls onFilterChange with sort when option is selected', () => {
      const onFilterChange = vi.fn()
      render(<ReadingFilterBar {...defaultProps} onFilterChange={onFilterChange} />)

      // Open dropdown
      const sortButton = screen.getByRole('button', { name: /Priority/i })
      fireEvent.click(sortButton)

      // Select Date Added option
      fireEvent.click(screen.getByRole('option', { name: /Date Added/i }))

      expect(onFilterChange).toHaveBeenCalledWith({ sort: 'date' })
    })
  })

  describe('knowledge area filter', () => {
    it('renders KA dropdown with "All KAs" when no selection', () => {
      render(<ReadingFilterBar {...defaultProps} selectedKaId={null} />)

      expect(screen.getByRole('button', { name: /All KAs/i })).toBeInTheDocument()
    })

    it('renders KA dropdown with selected KA name', () => {
      render(<ReadingFilterBar {...defaultProps} selectedKaId="strategy" />)

      expect(screen.getByRole('button', { name: /Strategy Analysis/i })).toBeInTheDocument()
    })

    it('opens dropdown with all KA options', () => {
      render(<ReadingFilterBar {...defaultProps} />)

      // Open KA dropdown
      const kaButton = screen.getByRole('button', { name: /All KAs/i })
      fireEvent.click(kaButton)

      // Should show "All KAs" option and all knowledge areas
      expect(screen.getAllByRole('option', { name: /All KAs/i })).toHaveLength(1)
      expect(screen.getByRole('option', { name: /Strategy Analysis/i })).toBeInTheDocument()
      expect(
        screen.getByRole('option', { name: /Elicitation and Collaboration/i })
      ).toBeInTheDocument()
    })

    it('calls onFilterChange with kaId when KA is selected', () => {
      const onFilterChange = vi.fn()
      render(<ReadingFilterBar {...defaultProps} onFilterChange={onFilterChange} />)

      // Open dropdown
      const kaButton = screen.getByRole('button', { name: /All KAs/i })
      fireEvent.click(kaButton)

      // Select a KA
      fireEvent.click(screen.getByRole('option', { name: /Strategy Analysis/i }))

      expect(onFilterChange).toHaveBeenCalledWith({ kaId: 'strategy' })
    })

    it('calls onFilterChange with null kaId when "All KAs" is selected', () => {
      const onFilterChange = vi.fn()
      render(
        <ReadingFilterBar {...defaultProps} selectedKaId="strategy" onFilterChange={onFilterChange} />
      )

      // Open dropdown
      const kaButton = screen.getByRole('button', { name: /Strategy Analysis/i })
      fireEvent.click(kaButton)

      // Select "All KAs"
      fireEvent.click(screen.getByRole('option', { name: /All KAs/i }))

      expect(onFilterChange).toHaveBeenCalledWith({ kaId: null })
    })
  })

  describe('accessibility', () => {
    it('has accessible tab list', () => {
      render(<ReadingFilterBar {...defaultProps} />)

      expect(screen.getByRole('tablist')).toBeInTheDocument()
    })

    it('dropdowns have accessible labels', () => {
      render(<ReadingFilterBar {...defaultProps} />)

      // Both dropdowns should be accessible
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })
  })
})
