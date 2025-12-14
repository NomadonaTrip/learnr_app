import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { HeroSection } from '../../../components/landing/HeroSection'

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('HeroSection', () => {
  it('renders the headline', () => {
    renderWithRouter(<HeroSection />)
    expect(screen.getByRole('heading', { level: 1, name: /master your certification exam/i })).toBeInTheDocument()
  })

  it('renders the subtitle', () => {
    renderWithRouter(<HeroSection />)
    expect(screen.getByText(/personalized learning that adapts to you/i)).toBeInTheDocument()
  })

  it('renders Start exam prep CTA button', () => {
    renderWithRouter(<HeroSection />)
    expect(screen.getByRole('button', { name: /start exam prep/i })).toBeInTheDocument()
  })

  it('renders login link', () => {
    renderWithRouter(<HeroSection />)
    expect(screen.getByRole('button', { name: /i already have an account/i })).toBeInTheDocument()
  })

  it('calls onStartExamPrep callback when primary CTA is clicked', () => {
    const handleStartExamPrep = vi.fn()
    renderWithRouter(<HeroSection onStartExamPrep={handleStartExamPrep} />)

    fireEvent.click(screen.getByRole('button', { name: /start exam prep/i }))
    expect(handleStartExamPrep).toHaveBeenCalledTimes(1)
  })

  it('calls onLogin callback when secondary link is clicked', () => {
    const handleLogin = vi.fn()
    renderWithRouter(<HeroSection onLogin={handleLogin} />)

    fireEvent.click(screen.getByRole('button', { name: /i already have an account/i }))
    expect(handleLogin).toHaveBeenCalledTimes(1)
  })

  it('has accessible section with aria-labelledby', () => {
    renderWithRouter(<HeroSection />)
    const section = screen.getByRole('heading', { level: 1 }).closest('section')
    expect(section).toHaveAttribute('aria-labelledby', 'hero-heading')
  })

  it('CTA buttons have visible focus indicator classes', () => {
    renderWithRouter(<HeroSection />)
    const primaryButton = screen.getByRole('button', { name: /start exam prep/i })
    const secondaryButton = screen.getByRole('button', { name: /i already have an account/i })

    expect(primaryButton.className).toContain('focus-visible:ring')
    expect(secondaryButton.className).toContain('focus-visible:ring')
  })
})
