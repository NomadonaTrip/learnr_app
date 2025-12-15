import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PasswordStrengthIndicator } from '../../../components/account/PasswordStrengthIndicator'

describe('PasswordStrengthIndicator', () => {
  it('renders nothing when password is empty', () => {
    const { container } = render(<PasswordStrengthIndicator password="" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders strength bars when password is provided', () => {
    render(<PasswordStrengthIndicator password="test" />)

    // Should have 5 bars
    const bars = document.querySelectorAll('[aria-hidden="true"] > div')
    expect(bars.length).toBe(5)
  })

  it('displays "Weak" for weak passwords', () => {
    render(<PasswordStrengthIndicator password="abc" />)
    expect(screen.getByText('Weak')).toBeInTheDocument()
  })

  it('displays stronger rating for complex passwords', () => {
    render(<PasswordStrengthIndicator password="SecurePass123!" />)

    // Should show a strong rating
    const label = screen.getByText(/strong/i)
    expect(label).toBeInTheDocument()
  })

  it('has accessible status role', () => {
    render(<PasswordStrengthIndicator password="test" />)

    const status = screen.getByRole('status')
    expect(status).toBeInTheDocument()
  })

  it('includes screen reader text', () => {
    render(<PasswordStrengthIndicator password="test" />)

    expect(screen.getByText('Password strength:')).toBeInTheDocument()
  })

  it('updates when password changes', () => {
    const { rerender } = render(<PasswordStrengthIndicator password="abc" />)
    expect(screen.getByText('Weak')).toBeInTheDocument()

    rerender(<PasswordStrengthIndicator password="SecurePass123!" />)
    expect(screen.getByText(/strong/i)).toBeInTheDocument()
  })
})
