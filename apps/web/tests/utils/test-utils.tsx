/**
 * Custom Test Utilities
 *
 * Wrapper around @testing-library/react with project-specific setup
 * (providers, routers, state, etc.)
 */

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

/**
 * All the providers wrapper
 *
 * Add your app's providers here (theme, i18n, auth, etc.)
 */
interface AllProvidersProps {
  children: React.ReactNode;
}

function AllProviders({ children }: AllProvidersProps) {
  return (
    <BrowserRouter>
      {/* Add other providers here as they're created:
        <ThemeProvider>
          <AuthProvider>
            <I18nProvider>
              {children}
            </I18nProvider>
          </AuthProvider>
        </ThemeProvider>
      */}
      {children}
    </BrowserRouter>
  );
}

/**
 * Custom render function with all providers
 */
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

/**
 * Custom render function without router (for components that don't need routing)
 */
function customRenderWithoutRouter(
  ui: ReactElement,
  options?: RenderOptions
) {
  return render(ui, options);
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react';

// Override render with custom render
export { customRender as render, customRenderWithoutRouter };

/**
 * Common test utilities
 */

/**
 * Wait for async updates to complete
 */
export const waitForNextUpdate = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Create mock user data
 */
export function createMockUser(overrides = {}) {
  return {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock question data
 */
export function createMockQuestion(overrides = {}) {
  return {
    id: '1',
    question_text: 'What is Business Analysis?',
    options: [
      { id: 'a', text: 'Option A' },
      { id: 'b', text: 'Option B' },
      { id: 'c', text: 'Option C' },
      { id: 'd', text: 'Option D' },
    ],
    correct_answer_id: 'a',
    knowledge_area: 'Business Analysis Planning',
    difficulty: 0.5,
    ...overrides,
  };
}

/**
 * Create mock session data
 */
export function createMockSession(overrides = {}) {
  return {
    id: '1',
    user_id: '1',
    started_at: '2025-01-01T00:00:00Z',
    questions_answered: 0,
    correct_count: 0,
    ...overrides,
  };
}
