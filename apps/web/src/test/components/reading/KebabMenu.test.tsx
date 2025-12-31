/**
 * KebabMenu Component Tests
 * Story 5.12: Clear Completed Reading Materials
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { KebabMenu } from '../../../components/reading/KebabMenu'

describe('KebabMenu', () => {
  const defaultProps = {
    onRemove: vi.fn(),
  }

  describe('rendering', () => {
    it('renders the menu button', () => {
      render(<KebabMenu {...defaultProps} />)
      expect(screen.getByRole('button', { name: /card actions menu/i })).toBeInTheDocument()
    })

    it('renders ellipsis icon', () => {
      render(<KebabMenu {...defaultProps} />)
      const button = screen.getByRole('button')
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('menu is closed by default', () => {
      render(<KebabMenu {...defaultProps} />)
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has correct aria-label on button', () => {
      render(<KebabMenu {...defaultProps} />)
      expect(screen.getByLabelText('Card actions menu')).toBeInTheDocument()
    })

    it('button has minimum touch target size (44x44px)', () => {
      render(<KebabMenu {...defaultProps} />)
      const button = screen.getByRole('button')
      expect(button.className).toContain('w-11')
      expect(button.className).toContain('h-11')
    })
  })

  describe('interactions', () => {
    it('opens menu when button is clicked', async () => {
      render(<KebabMenu {...defaultProps} />)

      fireEvent.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument()
      })
    })

    it('shows "Remove from library" option in menu', async () => {
      render(<KebabMenu {...defaultProps} />)

      fireEvent.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByText('Remove from library')).toBeInTheDocument()
      })
    })

    it('calls onRemove when "Remove from library" is clicked', async () => {
      const onRemove = vi.fn()
      render(<KebabMenu onRemove={onRemove} />)

      fireEvent.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByText('Remove from library')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Remove from library'))

      expect(onRemove).toHaveBeenCalledTimes(1)
    })

    it('closes menu after item is clicked', async () => {
      const onRemove = vi.fn()
      render(<KebabMenu onRemove={onRemove} />)

      fireEvent.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('Remove from library'))

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument()
      })
    })
  })

  describe('menu item styling', () => {
    it('shows trash icon in menu item', async () => {
      render(<KebabMenu {...defaultProps} />)

      fireEvent.click(screen.getByRole('button'))

      await waitFor(() => {
        const menuItem = screen.getByText('Remove from library').closest('button')
        expect(menuItem).toBeInTheDocument()
        const svg = menuItem?.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })
  })

  describe('keyboard navigation', () => {
    it('opens menu with Enter key', async () => {
      render(<KebabMenu {...defaultProps} />)
      const button = screen.getByRole('button')

      fireEvent.keyDown(button, { key: 'Enter' })

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument()
      })
    })

    it('opens menu with Space key', async () => {
      render(<KebabMenu {...defaultProps} />)
      const button = screen.getByRole('button')

      fireEvent.keyDown(button, { key: ' ' })

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument()
      })
    })
  })
})
