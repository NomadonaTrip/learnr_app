import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConceptLockTooltip } from '../ConceptLockTooltip'

describe('ConceptLockTooltip', () => {
  it('shows loading', () => {
    render(<ConceptLockTooltip isLoading error={false} blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText('Loading prerequisites…')).toBeInTheDocument()
  })

  it('shows error inline', () => {
    render(<ConceptLockTooltip isLoading={false} error blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText("Couldn't load prerequisites")).toBeInTheDocument()
  })

  it('lists blocking prerequisites and marks the closest', () => {
    render(
      <ConceptLockTooltip
        isLoading={false}
        error={false}
        blockingPrerequisites={[{ concept_id: 'a', name: 'Stakeholders' }, { concept_id: 'b', name: 'Scope' }]}
        closestName="Scope"
      />,
    )
    expect(screen.getByText('Stakeholders')).toBeInTheDocument()
    expect(screen.getByText(/Scope/)).toBeInTheDocument()
    expect(screen.getByText(/closest/i)).toBeInTheDocument()
  })

  it('shows all-met when there are no blockers', () => {
    render(<ConceptLockTooltip isLoading={false} error={false} blockingPrerequisites={[]} closestName={null} />)
    expect(screen.getByText('All prerequisites met')).toBeInTheDocument()
  })

  it('applies an optional id so a trigger can wire aria-describedby', () => {
    render(
      <ConceptLockTooltip
        isLoading={false}
        error={false}
        blockingPrerequisites={[]}
        closestName={null}
        id="concept-tooltip-1"
      />,
    )
    expect(screen.getByRole('tooltip')).toHaveAttribute('id', 'concept-tooltip-1')
  })
})
