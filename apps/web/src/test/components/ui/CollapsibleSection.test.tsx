import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { axe } from 'vitest-axe'
import { CollapsibleSection } from '../../../components/ui/CollapsibleSection'

describe('CollapsibleSection', () => {
  const defaultProps = {
    id: 'test-section',
    title: 'Test Section',
    children: <div data-testid="content">Section Content</div>,
  }

  describe('Initial rendering', () => {
    it('renders collapsed by default', () => {
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('renders expanded when defaultExpanded is true', () => {
      render(<CollapsibleSection {...defaultProps} defaultExpanded={true} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'true')
    })

    it('renders the title in the toggle button', () => {
      render(<CollapsibleSection {...defaultProps} />)

      expect(screen.getByText('Test Section')).toBeInTheDocument()
    })

    it('renders children content', () => {
      render(<CollapsibleSection {...defaultProps} />)

      expect(screen.getByTestId('content')).toBeInTheDocument()
    })
  })

  describe('Toggle functionality', () => {
    it('toggles aria-expanded on click', async () => {
      const user = userEvent.setup()
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })

      // Initially collapsed
      expect(toggle).toHaveAttribute('aria-expanded', 'false')

      // Click to expand
      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      // Click to collapse
      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('toggles on Enter key press', async () => {
      const user = userEvent.setup()
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      toggle.focus()

      expect(toggle).toHaveAttribute('aria-expanded', 'false')

      await user.keyboard('{Enter}')
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.keyboard('{Enter}')
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('toggles on Space key press', async () => {
      const user = userEvent.setup()
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
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
      render(<CollapsibleSection {...defaultProps} />)

      const content = screen.getByRole('region')
      expect(content).toHaveClass('max-h-0', 'opacity-0')
    })

    it('applies expanded styles when expanded', async () => {
      const user = userEvent.setup()
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      await user.click(toggle)

      const content = screen.getByRole('region')
      expect(content).toHaveClass('max-h-[2000px]', 'opacity-100')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes on toggle button', () => {
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })

      expect(toggle).toHaveAttribute('id', 'test-section-toggle')
      expect(toggle).toHaveAttribute('aria-controls', 'test-section-content')
      expect(toggle).toHaveAttribute('aria-expanded')
    })

    it('has proper ARIA attributes on content region', () => {
      render(<CollapsibleSection {...defaultProps} />)

      const content = screen.getByRole('region')

      expect(content).toHaveAttribute('id', 'test-section-content')
      expect(content).toHaveAttribute('aria-labelledby', 'test-section-toggle')
    })

    it('contains a chevron icon for visual indication', () => {
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      const svg = toggle.querySelector('svg')

      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('chevron has rotate class when expanded', async () => {
      const user = userEvent.setup()
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      const svg = toggle.querySelector('svg')

      // Initially no rotation
      expect(svg).not.toHaveClass('rotate-180')

      // Expand
      await user.click(toggle)
      expect(svg).toHaveClass('rotate-180')
    })

    it('has motion-reduce classes for reduced motion preference', () => {
      render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      const content = screen.getByRole('region')
      const svg = toggle.querySelector('svg')

      expect(toggle).toHaveClass('motion-reduce:transition-none')
      expect(content).toHaveClass('motion-reduce:transition-none')
      expect(svg).toHaveClass('motion-reduce:transition-none')
    })
  })

  describe('Custom className', () => {
    it('applies custom className to container', () => {
      render(<CollapsibleSection {...defaultProps} className="custom-class" />)

      const container = screen.getByRole('button', { name: /test section/i }).parentElement
      expect(container).toHaveClass('custom-class')
    })
  })

  describe('Axe accessibility', () => {
    it('has no accessibility violations when collapsed', async () => {
      const { container } = render(<CollapsibleSection {...defaultProps} />)
      const results = await axe(container)
      expect(results.violations).toEqual([])
    })

    it('has no accessibility violations when expanded', async () => {
      const user = userEvent.setup()
      const { container } = render(<CollapsibleSection {...defaultProps} />)

      const toggle = screen.getByRole('button', { name: /test section/i })
      await user.click(toggle)

      const results = await axe(container)
      expect(results.violations).toEqual([])
    })
  })
})
