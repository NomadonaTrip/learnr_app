import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Footer } from '../../../components/layout/Footer'

describe('Footer', () => {
  it('renders copyright notice with current year', () => {
    render(<Footer />)
    const currentYear = new Date().getFullYear()
    expect(screen.getByText(new RegExp(`© ${currentYear} LearnR`, 'i'))).toBeInTheDocument()
  })

  it('renders all required links', () => {
    render(<Footer />)

    expect(screen.getByRole('link', { name: /about/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /privacy policy/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /terms of service/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /contact/i })).toBeInTheDocument()
  })

  it('has accessible contentinfo landmark', () => {
    render(<Footer />)
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('has accessible footer navigation', () => {
    render(<Footer />)
    expect(screen.getByRole('navigation', { name: /footer navigation/i })).toBeInTheDocument()
  })

  it('links have correct href attributes', () => {
    render(<Footer />)

    expect(screen.getByRole('link', { name: /about/i })).toHaveAttribute('href', '/about')
    expect(screen.getByRole('link', { name: /privacy policy/i })).toHaveAttribute('href', '/privacy')
    expect(screen.getByRole('link', { name: /terms of service/i })).toHaveAttribute('href', '/terms')
    expect(screen.getByRole('link', { name: /contact/i })).toHaveAttribute('href', '/contact')
  })

  it('links have visible focus indicator classes', () => {
    render(<Footer />)
    const links = screen.getAllByRole('link')
    links.forEach((link) => {
      expect(link.className).toContain('focus-visible:ring')
    })
  })
})
