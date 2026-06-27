import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConceptLockBadge } from '../ConceptLockBadge'

describe('ConceptLockBadge', () => {
  it('renders an unlocked badge', () => {
    render(<ConceptLockBadge isUnlocked />)
    expect(screen.getByLabelText('Concept unlocked')).toBeInTheDocument()
    expect(screen.getByText('Unlocked')).toBeInTheDocument()
  })

  it('renders a locked badge', () => {
    render(<ConceptLockBadge isUnlocked={false} />)
    expect(screen.getByLabelText('Concept locked')).toBeInTheDocument()
    expect(screen.getByText('Locked')).toBeInTheDocument()
  })
})
