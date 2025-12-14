import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Navbar } from '../../../components/layout/Navbar'

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Navbar', () => {
  it('renders logo text', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByText('LearnR')).toBeInTheDocument()
  })

  it('renders Get Started CTA button', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument()
  })

  it('has accessible navigation landmark', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument()
  })

  it('logo link has accessible label', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByRole('link', { name: /learnr.*home/i })).toBeInTheDocument()
  })

  it('calls onGetStarted callback when CTA is clicked', () => {
    const handleGetStarted = vi.fn()
    renderWithRouter(<Navbar onGetStarted={handleGetStarted} />)

    fireEvent.click(screen.getByRole('button', { name: /get started/i }))
    expect(handleGetStarted).toHaveBeenCalledTimes(1)
  })

  it('Get Started button has visible focus indicator classes', () => {
    renderWithRouter(<Navbar />)
    const button = screen.getByRole('button', { name: /get started/i })
    expect(button.className).toContain('focus-visible:ring')
  })
})
