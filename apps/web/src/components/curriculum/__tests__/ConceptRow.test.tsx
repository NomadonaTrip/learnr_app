import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ConceptRow } from '../ConceptRow'
import type { ConceptUnlockStatus } from '../../../services/prerequisiteService'

const navigateMock = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => navigateMock,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Link: ({ to, children, ...rest }: any) => <a href={to} {...rest}>{children}</a>,
}))

const mutateAsyncMock = vi.fn()
vi.mock('../../../hooks/useConceptLockStatus', () => ({
  useConceptLockStatus: () => ({ data: undefined, isLoading: false, isError: false }),
  useAttemptLockedConcept: () => ({ mutateAsync: mutateAsyncMock, isPending: false }),
}))

function makeConcept(unlocked: boolean): ConceptUnlockStatus {
  return {
    concept_id: 'c-1', concept_name: 'Stakeholder Analysis', knowledge_area_id: 'ka-1',
    is_unlocked: unlocked, has_prerequisites: !unlocked,
    prerequisite_count: unlocked ? 0 : 2, mastered_prerequisite_count: 0,
    mastery_progress: unlocked ? 1 : 0.5,
  }
}

describe('ConceptRow', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the concept name and an unlocked badge', () => {
    render(<ConceptRow concept={makeConcept(true)} />)
    expect(screen.getByText('Stakeholder Analysis')).toBeInTheDocument()
    expect(screen.getByLabelText('Concept unlocked')).toBeInTheDocument()
  })

  it('navigates straight to focused quiz when unlocked', () => {
    render(<ConceptRow concept={makeConcept(true)} />)
    fireEvent.click(screen.getByRole('button', { name: /practice/i }))
    expect(navigateMock).toHaveBeenCalledWith(
      '/quiz?focus=concept&targets=c-1&name=Stakeholder%20Analysis',
    )
  })

  it('opens the confirm dialog when locked, then overrides and navigates', async () => {
    mutateAsyncMock.mockResolvedValue({})
    render(<ConceptRow concept={makeConcept(false)} />)
    fireEvent.click(screen.getByRole('button', { name: /practice/i }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /practice anyway/i }))
    await waitFor(() => expect(mutateAsyncMock).toHaveBeenCalledWith('c-1'))
    expect(navigateMock).toHaveBeenCalledWith(
      '/quiz?focus=concept&targets=c-1&name=Stakeholder%20Analysis',
    )
  })

  it('renders a "View map" link pointing to the concept graph route', () => {
    render(<ConceptRow concept={makeConcept(true)} />)
    const link = screen.getByRole('link', { name: /view map/i })
    expect(link).toHaveAttribute('href', '/curriculum/graph/c-1')
  })
})
