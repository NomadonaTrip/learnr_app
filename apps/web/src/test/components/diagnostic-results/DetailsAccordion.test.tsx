import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { DetailsAccordion } from '../../../components/diagnostic-results/DetailsAccordion'
import type { KnowledgeAreaResult, ConceptGap, ConfidenceLevel } from '../../../types/diagnostic'

// Mock child components to isolate DetailsAccordion tests
vi.mock('../../../components/diagnostic-results/KnowledgeAreaBreakdown', () => ({
  KnowledgeAreaBreakdown: ({ areas }: { areas: KnowledgeAreaResult[] }) => (
    <div data-testid="knowledge-area-breakdown">KA Breakdown ({areas.length} areas)</div>
  ),
}))

vi.mock('../../../components/diagnostic-results/GapHighlights', () => ({
  GapHighlights: ({ gaps }: { gaps: ConceptGap[] }) => (
    <div data-testid="gap-highlights">Gaps ({gaps.length} gaps)</div>
  ),
}))

vi.mock('../../../components/diagnostic-results/UncertaintyCallout', () => ({
  UncertaintyCallout: ({
    uncertainCount,
    confidenceLevel,
  }: {
    uncertainCount: number
    confidenceLevel: ConfidenceLevel
    message: string
  }) => (
    <div data-testid="uncertainty-callout">
      Uncertainty ({uncertainCount}, {confidenceLevel})
    </div>
  ),
}))

describe('DetailsAccordion', () => {
  const mockAreas: KnowledgeAreaResult[] = [
    {
      ka: 'Business Analysis Planning',
      ka_id: 'ba-planning',
      concepts: 20,
      touched: 15,
      estimated_mastery: 0.75,
    },
    {
      ka: 'Elicitation',
      ka_id: 'elicitation',
      concepts: 18,
      touched: 12,
      estimated_mastery: 0.65,
    },
  ]

  const mockGaps: ConceptGap[] = [
    {
      concept_id: 'c1',
      name: 'Stakeholder Analysis',
      mastery_probability: 0.3,
      knowledge_area: 'BA Planning',
    },
    {
      concept_id: 'c2',
      name: 'Requirements Workshop',
      mastery_probability: 0.25,
      knowledge_area: 'Elicitation',
    },
  ]

  const defaultProps = {
    areas: mockAreas,
    gaps: mockGaps,
    uncertainCount: 5,
    confidenceLevel: 'developing' as ConfidenceLevel,
    message: 'Focus on BA Planning concepts',
  }

  describe('Rendering', () => {
    it('renders collapsed by default', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /view detailed breakdown/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('displays "View Detailed Breakdown" when collapsed', () => {
      render(<DetailsAccordion {...defaultProps} />)

      expect(screen.getByText('View Detailed Breakdown')).toBeInTheDocument()
    })

    it('displays "Hide Details" when expanded', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      await user.click(toggle)

      expect(screen.getByText('Hide Details')).toBeInTheDocument()
    })

    it('renders all child components when expanded', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      await user.click(toggle)

      expect(screen.getByTestId('knowledge-area-breakdown')).toBeInTheDocument()
      expect(screen.getByTestId('gap-highlights')).toBeInTheDocument()
      expect(screen.getByTestId('uncertainty-callout')).toBeInTheDocument()
    })
  })

  describe('Conditional rendering', () => {
    it('returns null when no content to display', () => {
      const { container } = render(
        <DetailsAccordion
          areas={[]}
          gaps={[]}
          uncertainCount={0}
          confidenceLevel="established"
          message=""
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('renders when only areas have content', () => {
      render(
        <DetailsAccordion
          areas={mockAreas}
          gaps={[]}
          uncertainCount={0}
          confidenceLevel="established"
          message=""
        />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('renders when only gaps have content', () => {
      render(
        <DetailsAccordion
          areas={[]}
          gaps={mockGaps}
          uncertainCount={0}
          confidenceLevel="established"
          message=""
        />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('renders when uncertainCount > 0 and confidence not established', () => {
      render(
        <DetailsAccordion
          areas={[]}
          gaps={[]}
          uncertainCount={5}
          confidenceLevel="developing"
          message=""
        />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('does not render uncertainty section when confidence is established', () => {
      const { container } = render(
        <DetailsAccordion
          areas={[]}
          gaps={[]}
          uncertainCount={5}
          confidenceLevel="established"
          message=""
        />
      )

      // Should return null because established confidence + no areas/gaps = no content
      expect(container.firstChild).toBeNull()
    })
  })

  describe('Toggle functionality', () => {
    it('toggles aria-expanded on click', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')

      expect(toggle).toHaveAttribute('aria-expanded', 'false')

      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('toggles on Enter key press', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      toggle.focus()

      expect(toggle).toHaveAttribute('aria-expanded', 'false')

      await user.keyboard('{Enter}')
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.keyboard('{Enter}')
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('toggles on Space key press', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      toggle.focus()

      expect(toggle).toHaveAttribute('aria-expanded', 'false')

      await user.keyboard(' ')
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.keyboard(' ')
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })
  })

  describe('Content visibility', () => {
    it('applies collapsed styles when collapsed', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const content = screen.getByRole('region')
      expect(content).toHaveClass('max-h-0', 'opacity-0')
    })

    it('applies expanded styles when expanded', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      await user.click(toggle)

      const content = screen.getByRole('region')
      expect(content).toHaveClass('max-h-[2000px]', 'opacity-100')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes on toggle button', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')

      expect(toggle).toHaveAttribute('id', 'details-accordion-toggle')
      expect(toggle).toHaveAttribute('aria-controls', 'details-accordion-content')
      expect(toggle).toHaveAttribute('aria-expanded')
    })

    it('has proper ARIA attributes on content region', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const content = screen.getByRole('region')

      expect(content).toHaveAttribute('id', 'details-accordion-content')
      expect(content).toHaveAttribute('aria-labelledby', 'details-accordion-toggle')
    })

    it('contains a chevron icon for visual indication', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      const svg = toggle.querySelector('svg')

      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('chevron has rotate class when expanded', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      const svg = toggle.querySelector('svg')

      expect(svg).not.toHaveClass('rotate-180')

      await user.click(toggle)
      expect(svg).toHaveClass('rotate-180')
    })

    it('has motion-reduce classes for reduced motion preference', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      const content = screen.getByRole('region')
      const svg = toggle.querySelector('svg')

      expect(toggle).toHaveClass('motion-reduce:transition-none')
      expect(content).toHaveClass('motion-reduce:transition-none')
      expect(svg).toHaveClass('motion-reduce:transition-none')
    })

    it('has minimum touch target size of 44px', () => {
      render(<DetailsAccordion {...defaultProps} />)

      const toggle = screen.getByRole('button')
      expect(toggle).toHaveClass('min-h-[44px]')
    })
  })

  describe('Props passed to children', () => {
    it('passes areas to KnowledgeAreaBreakdown', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      await user.click(screen.getByRole('button'))

      expect(screen.getByTestId('knowledge-area-breakdown')).toHaveTextContent('2 areas')
    })

    it('passes gaps to GapHighlights', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      await user.click(screen.getByRole('button'))

      expect(screen.getByTestId('gap-highlights')).toHaveTextContent('2 gaps')
    })

    it('passes uncertainty data to UncertaintyCallout', async () => {
      const user = userEvent.setup()
      render(<DetailsAccordion {...defaultProps} />)

      await user.click(screen.getByRole('button'))

      expect(screen.getByTestId('uncertainty-callout')).toHaveTextContent('5, developing')
    })
  })
})
