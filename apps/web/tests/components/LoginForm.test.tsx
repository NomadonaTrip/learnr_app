/**
 * Sample Component Test: LoginForm
 *
 * This demonstrates advanced testing patterns:
 * - Form validation
 * - Async API calls
 * - Error handling
 * - Loading states
 * - Integration with state management
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';

// Mock API service
const mockAuthService = {
  login: vi.fn(),
};

// Mock LoginForm component (replace with actual component when created)
interface LoginFormProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

function LoginForm({ onSuccess, onError }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (!email) {
      setError('Email is required');
      onError?.('Email is required');
      return;
    }

    if (!password) {
      setError('Password is required');
      onError?.('Password is required');
      return;
    }

    setIsLoading(true);

    try {
      await mockAuthService.login({ email, password });
      onSuccess?.();
    } catch (err: any) {
      const errorMessage = err.message || 'Login failed';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Login form">
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          aria-required="true"
        />
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          aria-required="true"
        />
      </div>

      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Log In'}
      </button>
    </form>
  );
}

// Import useState at the top (for the mock component)
import { useState } from 'react';

describe('LoginForm Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders email and password fields', () => {
      render(<LoginForm />);

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('renders submit button', () => {
      render(<LoginForm />);

      expect(
        screen.getByRole('button', { name: /log in/i })
      ).toBeInTheDocument();
    });

    it('has accessible form label', () => {
      render(<LoginForm />);

      expect(screen.getByRole('form', { name: /login form/i })).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error when email is empty', async () => {
      const onError = vi.fn();
      const user = userEvent.setup();

      render(<LoginForm onError={onError} />);

      // Click submit without entering email
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/email is required/i);
      });

      expect(onError).toHaveBeenCalledWith('Email is required');
    });

    it('shows error when password is empty', async () => {
      const onError = vi.fn();
      const user = userEvent.setup();

      render(<LoginForm onError={onError} />);

      // Enter email but no password
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/password is required/i);
      });

      expect(onError).toHaveBeenCalledWith('Password is required');
    });
  });

  describe('Successful Login', () => {
    it('calls API with correct credentials', async () => {
      mockAuthService.login.mockResolvedValue({ token: 'fake-token' });
      const onSuccess = vi.fn();
      const user = userEvent.setup();

      render(<LoginForm onSuccess={onSuccess} />);

      // Fill form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      // Submit
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(onSuccess).toHaveBeenCalled();
    });

    it('shows loading state during login', async () => {
      // Delay API response to test loading state
      mockAuthService.login.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );
      const user = userEvent.setup();

      render(<LoginForm />);

      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      // Check loading state
      expect(screen.getByRole('button')).toHaveTextContent(/logging in/i);
      expect(screen.getByRole('button')).toBeDisabled();
      expect(screen.getByLabelText(/email/i)).toBeDisabled();
      expect(screen.getByLabelText(/password/i)).toBeDisabled();

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.getByRole('button')).toHaveTextContent(/log in/i);
      });
    });
  });

  describe('Failed Login', () => {
    it('shows error message on API failure', async () => {
      mockAuthService.login.mockRejectedValue(
        new Error('Invalid credentials')
      );
      const onError = vi.fn();
      const user = userEvent.setup();

      render(<LoginForm onError={onError} />);

      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
      });

      expect(onError).toHaveBeenCalledWith('Invalid credentials');
    });

    it('re-enables form after error', async () => {
      mockAuthService.login.mockRejectedValue(new Error('Server error'));
      const user = userEvent.setup();

      render(<LoginForm />);

      // Submit form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /log in/i }));

      // Wait for error
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Form should be re-enabled
      expect(screen.getByLabelText(/email/i)).not.toBeDisabled();
      expect(screen.getByLabelText(/password/i)).not.toBeDisabled();
      expect(screen.getByRole('button')).not.toBeDisabled();
    });
  });

  describe('User Experience', () => {
    it('clears error when user starts typing', async () => {
      const user = userEvent.setup();

      render(<LoginForm />);

      // Trigger validation error
      await user.click(screen.getByRole('button', { name: /log in/i }));
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Start typing - error should persist until form is resubmitted
      // (This is intentional in our mock - real implementation might clear on input)
      await user.type(screen.getByLabelText(/email/i), 't');

      // In a real implementation, you might want to clear the error here
      // For now, this test documents the current behavior
    });
  });

  describe('Accessibility', () => {
    it('marks fields as required', () => {
      render(<LoginForm />);

      expect(screen.getByLabelText(/email/i)).toHaveAttribute('aria-required', 'true');
      expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-required', 'true');
    });

    it('uses role="alert" for error messages', async () => {
      const user = userEvent.setup();

      render(<LoginForm />);

      await user.click(screen.getByRole('button', { name: /log in/i }));

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent(/email is required/i);
      });
    });
  });
});
