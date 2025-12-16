import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FeaturesSection } from '../../../components/landing/FeaturesSection'

describe('FeaturesSection', () => {
  it('renders section heading', () => {
    render(<FeaturesSection />)
    expect(screen.getByRole('heading', { level: 2, name: /how learnr works/i })).toBeInTheDocument()
  })

  it('renders all 3 feature cards', () => {
    render(<FeaturesSection />)

    expect(screen.getByText(/personalized learning path/i)).toBeInTheDocument()
    expect(screen.getByText(/complete concept mastery/i)).toBeInTheDocument()
    expect(screen.getByText(/proven competence growth/i)).toBeInTheDocument()
  })

  it('renders feature descriptions in plain language', () => {
    render(<FeaturesSection />)

    // Personalized learning description
    expect(screen.getByText(/your learning journey adapts to your unique strengths/i)).toBeInTheDocument()

    // Concept mastery description (BKT benefit)
    expect(screen.getByText(/never miss a topic/i)).toBeInTheDocument()

    // Competence growth description (IRT benefit)
    expect(screen.getByText(/watch your skills develop with precision-measured progress/i)).toBeInTheDocument()
  })

  it('has accessible section with aria-labelledby', () => {
    render(<FeaturesSection />)
    const heading = screen.getByRole('heading', { level: 2, name: /how learnr works/i })
    const section = heading.closest('section')
    expect(section).toHaveAttribute('aria-labelledby', 'features-heading')
  })

  it('feature cards container has list role', () => {
    render(<FeaturesSection />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })

  it('each feature card has listitem role', () => {
    render(<FeaturesSection />)
    const listItems = screen.getAllByRole('listitem')
    expect(listItems).toHaveLength(3)
  })
})
