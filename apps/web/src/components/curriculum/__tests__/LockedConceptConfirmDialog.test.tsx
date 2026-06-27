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
})
