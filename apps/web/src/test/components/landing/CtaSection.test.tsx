import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CtaSection } from '../../../components/landing/CtaSection'

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('CtaSection', () => {
  it('renders section heading', () => {
    renderWithRouter(<CtaSection />)
    expect(screen.getByRole('heading', { level: 2, name: /ready to start your journey/i })).toBeInTheDocument()
  })

  it('renders Start exam prep CTA button', () => {
    renderWithRouter(<CtaSection />)
    expect(screen.getByRole('button', { name: /start exam prep/i })).toBeInTheDocument()
  })

  it('calls onStartExamPrep callback when CTA is clicked', () => {
    const handleStartExamPrep = vi.fn()
    renderWithRouter(<CtaSection onStartExamPrep={handleStartExamPrep} />)

    fireEvent.click(screen.getByRole('button', { name: /start exam prep/i }))
    expect(handleStartExamPrep).toHaveBeenCalledTimes(1)
  })

  it('has accessible section with aria-labelledby', () => {
    renderWithRouter(<CtaSection />)
    const heading = screen.getByRole('heading', { level: 2, name: /ready to start your journey/i })
    const section = heading.closest('section')
    expect(section).toHaveAttribute('aria-labelledby', 'cta-heading')
  })

  it('CTA button has visible focus indicator classes', () => {
    renderWithRouter(<CtaSection />)
    const button = screen.getByRole('button', { name: /start exam prep/i })
    expect(button.className).toContain('focus-visible:ring')
  })
})
