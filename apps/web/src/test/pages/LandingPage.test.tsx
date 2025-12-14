import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LandingPage } from '../../pages/LandingPage'

// Mock analytics service
vi.mock('../../services/analyticsService', () => ({
  trackLandingPageViewed: vi.fn(),
  trackLandingCtaClicked: vi.fn(),
  trackEvent: vi.fn(),
}))

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('LandingPage', () => {
  it('renders all major sections', () => {
    renderWithRouter(<LandingPage />)

    // Navbar
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument()

    // Hero section
    expect(screen.getByRole('heading', { level: 1, name: /master your certification exam/i })).toBeInTheDocument()

    // Benefits section
    expect(screen.getByRole('heading', { level: 2, name: /achieve your goals/i })).toBeInTheDocument()

    // Features section
    expect(screen.getByRole('heading', { level: 2, name: /how learnr works/i })).toBeInTheDocument()

    // CTA section
    expect(screen.getByRole('heading', { level: 2, name: /ready to start your journey/i })).toBeInTheDocument()

    // Footer
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('has skip link for accessibility', () => {
    renderWithRouter(<LandingPage />)
    expect(screen.getByRole('link', { name: /skip to main content/i })).toBeInTheDocument()
  })

  it('skip link targets main content', () => {
    renderWithRouter(<LandingPage />)
    const skipLink = screen.getByRole('link', { name: /skip to main content/i })
    expect(skipLink).toHaveAttribute('href', '#main-content')
  })

  it('has main content landmark with correct id', () => {
    renderWithRouter(<LandingPage />)
    const main = screen.getByRole('main')
    expect(main).toHaveAttribute('id', 'main-content')
  })

  it('uses warm cream background color', () => {
    renderWithRouter(<LandingPage />)
    const container = screen.getByRole('main').parentElement
    expect(container?.className).toContain('bg-cream')
  })

  it('renders multiple Start exam prep CTAs', () => {
    renderWithRouter(<LandingPage />)
    const ctaButtons = screen.getAllByRole('button', { name: /start exam prep/i })
    expect(ctaButtons.length).toBeGreaterThanOrEqual(2) // Hero + CTA section
  })

  it('has header element wrapping navbar', () => {
    renderWithRouter(<LandingPage />)
    const nav = screen.getByRole('navigation', { name: /main navigation/i })
    expect(nav.closest('header')).toBeInTheDocument()
  })
})
