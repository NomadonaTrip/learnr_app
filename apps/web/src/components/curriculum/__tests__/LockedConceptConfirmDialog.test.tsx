import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LockedConceptConfirmDialog } from '../LockedConceptConfirmDialog'

describe('LockedConceptConfirmDialog', () => {
  const props = {
    conceptName: 'Strategy Analysis',
    blockingPrerequisites: [{ concept_id: 'a', name: 'Current State' }],
    isSubmitting: false,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  }
  beforeEach(() => vi.clearAllMocks())

  it('renders the concept name and blockers', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/Strategy Analysis/)).toBeInTheDocument()
    expect(screen.getByText('Current State')).toBeInTheDocument()
  })

  it('calls onConfirm when practice-anyway is clicked', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.click(screen.getByRole('button', { name: /practice anyway/i }))
    expect(props.onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when cancel is clicked', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(props.onCancel).toHaveBeenCalledTimes(1)
  })

  it('disables confirm while submitting', () => {
    render(<LockedConceptConfirmDialog {...props} isSubmitting />)
    expect(screen.getByRole('button', { name: /starting/i })).toBeDisabled()
  })

  it('autofocuses the dialog on open', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    expect(screen.getByRole('dialog')).toHaveFocus()
  })

  it('closes on Escape without tabbing in first', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(props.onCancel).toHaveBeenCalledTimes(1)
  })

  it('dismisses on backdrop click', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    const backdrop = screen.getByRole('dialog').parentElement as HTMLElement
    fireEvent.click(backdrop)
    expect(props.onCancel).toHaveBeenCalledTimes(1)
  })

  it('does not dismiss when clicking inside the dialog', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    fireEvent.click(screen.getByText(/Practice .* anyway\?/))
    expect(props.onCancel).not.toHaveBeenCalled()
  })

  it('labels the dialog via the heading (aria-labelledby)', () => {
    render(<LockedConceptConfirmDialog {...props} />)
    const labelledby = screen.getByRole('dialog').getAttribute('aria-labelledby')
    expect(labelledby).toBeTruthy()
    expect(document.getElementById(labelledby!)?.textContent).toMatch(/Strategy Analysis/)
  })
})
