/**
 * Sample Component Test: Button
 *
 * This demonstrates basic component testing patterns:
 * - Rendering
 * - User interactions
 * - Props validation
 * - Accessibility
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';

// Mock Button component (replace with actual component when created)
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  type?: 'button' | 'submit' | 'reset';
}

function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  type = 'button',
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
      aria-label={typeof children === 'string' ? children : undefined}
    >
      {children}
    </button>
  );
}

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders with text content', () => {
      render(<Button>Click Me</Button>);
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
    });

    it('renders with correct variant class', () => {
      const { container } = render(<Button variant="primary">Primary</Button>);
      expect(container.querySelector('.btn-primary')).toBeInTheDocument();
    });

    it('renders as disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  describe('User Interactions', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<Button onClick={handleClick}>Click Me</Button>);

      await user.click(screen.getByRole('button'));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button onClick={handleClick} disabled>
          Disabled
        </Button>
      );

      await user.click(screen.getByRole('button'));

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('handles multiple clicks', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<Button onClick={handleClick}>Multi Click</Button>);

      const button = screen.getByRole('button');
      await user.click(button);
      await user.click(button);
      await user.click(button);

      expect(handleClick).toHaveBeenCalledTimes(3);
    });
  });

  describe('Accessibility', () => {
    it('has correct button role', () => {
      render(<Button>Accessible Button</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('has aria-label for text content', () => {
      render(<Button>Accessible</Button>);
      expect(screen.getByLabelText('Accessible')).toBeInTheDocument();
    });

    it('is keyboard accessible', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<Button onClick={handleClick}>Keyboard</Button>);

      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();

      // Press Enter
      await user.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalledTimes(1);

      // Press Space
      await user.keyboard(' ');
      expect(handleClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('Variants', () => {
    it.each([
      ['primary', 'btn-primary'],
      ['secondary', 'btn-secondary'],
      ['danger', 'btn-danger'],
    ])('renders %s variant with correct class', (variant, expectedClass) => {
      const { container } = render(
        <Button variant={variant as any}>{variant} button</Button>
      );
      expect(container.querySelector(`.${expectedClass}`)).toBeInTheDocument();
    });
  });

  describe('Form Integration', () => {
    it('has correct type attribute', () => {
      render(<Button type="submit">Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
    });

    it('defaults to type="button"', () => {
      render(<Button>Default Type</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'button');
    });
  });
});
