import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BenefitsSection } from '../../../components/landing/BenefitsSection'

describe('BenefitsSection', () => {
  it('renders section heading', () => {
    render(<BenefitsSection />)
    expect(screen.getByRole('heading', { level: 2, name: /achieve your goals/i })).toBeInTheDocument()
  })

  it('renders all 4 benefit cards', () => {
    render(<BenefitsSection />)

    expect(screen.getByText(/change your career with ease/i)).toBeInTheDocument()
    expect(screen.getByText(/ace that certification the first time/i)).toBeInTheDocument()
    expect(screen.getByText(/life-long learning made easy/i)).toBeInTheDocument()
    expect(screen.getByText(/get that promotion/i)).toBeInTheDocument()
  })

  it('renders descriptions for each benefit', () => {
    render(<BenefitsSection />)

    expect(screen.getByText(/build the skills employers are looking for/i)).toBeInTheDocument()
    expect(screen.getByText(/adaptive learning ensures you truly understand/i)).toBeInTheDocument()
    expect(screen.getByText(/stay current in your field/i)).toBeInTheDocument()
    expect(screen.getByText(/demonstrate proven competence/i)).toBeInTheDocument()
  })

  it('has accessible section with aria-labelledby', () => {
    render(<BenefitsSection />)
    const heading = screen.getByRole('heading', { level: 2, name: /achieve your goals/i })
    const section = heading.closest('section')
    expect(section).toHaveAttribute('aria-labelledby', 'benefits-heading')
  })

  it('benefit cards container has list role', () => {
    render(<BenefitsSection />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })

  it('each benefit card has listitem role', () => {
    render(<BenefitsSection />)
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(4)
  })
})
