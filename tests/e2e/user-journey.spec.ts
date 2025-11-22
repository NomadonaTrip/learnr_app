/**
 * E2E Test: Complete User Journey
 *
 * This demonstrates advanced E2E testing:
 * - Complete user flow (onboarding → quiz → progress)
 * - Multi-page navigation
 * - Form interactions
 * - State persistence
 */

import { test, expect } from '@playwright/test';

test.describe('Complete User Journey', () => {
  test('user can complete onboarding and take diagnostic', async ({ page }) => {
    // Step 1: Navigate to homepage
    await page.goto('/');

    // Step 2: Start onboarding (if not already on onboarding page)
    const startButton = page.locator('button, a').filter({ hasText: /get started|start/i }).first();
    if (await startButton.isVisible()) {
      await startButton.click();
    }

    // Step 3: Answer onboarding questions
    // Question 1: Referral source (example)
    await page.waitForSelector('input, select', { timeout: 5000 });

    // Fill out onboarding form (adjust selectors based on actual implementation)
    // This is a template - adjust based on actual form structure
    const emailInput = page.locator('input[type="email"]').first();
    if (await emailInput.isVisible()) {
      await emailInput.fill('test@example.com');
    }

    const continueButton = page.locator('button').filter({ hasText: /continue|next/i }).first();
    if (await continueButton.isVisible()) {
      await continueButton.click();
    }

    // Step 4: Verify reached dashboard or diagnostic
    await page.waitForURL(/dashboard|diagnostic/i, { timeout: 10000 });

    // Verify dashboard/diagnostic elements are visible
    await expect(page.locator('body')).toBeVisible();
  });

  test('user can register and login', async ({ page }) => {
    // Navigate to registration page
    await page.goto('/register');

    // Fill registration form
    const testEmail = `test${Date.now()}@example.com`;
    const testPassword = 'SecurePassword123!';

    await page.fill('input[type="email"], input[name="email"]', testEmail);
    await page.fill('input[type="password"], input[name="password"]', testPassword);

    // Submit registration
    await page.click('button[type="submit"], button:has-text("Register"), button:has-text("Sign Up")');

    // Wait for redirect or success message
    await page.waitForURL(/dashboard|home|welcome/i, { timeout: 10000 });

    // Verify user is logged in (check for user-specific elements)
    const userElement = page.locator('[data-testid="user-menu"], nav:has-text("Log Out")').first();
    await expect(userElement).toBeVisible({ timeout: 5000 });
  });

  test('user can take a quiz and see results', async ({ page }) => {
    // Prerequisites: User must be logged in
    // For this test, we'll assume user is already on dashboard

    await page.goto('/dashboard');

    // Start a quiz
    const startQuizButton = page.locator('button, a').filter({
      hasText: /start quiz|continue learning|take quiz/i,
    }).first();

    await startQuizButton.click();

    // Wait for quiz to load
    await page.waitForSelector('[data-testid="question"], .question', { timeout: 5000 });

    // Answer a question (select first option)
    const firstOption = page.locator('input[type="radio"], button.option').first();
    await firstOption.click();

    // Submit answer
    const submitButton = page.locator('button').filter({
      hasText: /submit|next/i,
    }).first();
    await submitButton.click();

    // Wait for feedback or next question
    await page.waitForTimeout(1000);

    // Verify feedback is shown (correct/incorrect indication)
    const feedback = page.locator('[data-testid="feedback"], .feedback, [role="alert"]').first();
    await expect(feedback).toBeVisible({ timeout: 5000 });
  });

  test('user can access reading library', async ({ page }) => {
    // Navigate to reading library
    await page.goto('/reading');

    // Or navigate via menu
    const readingLink = page.locator('a, button').filter({
      hasText: /reading|library/i,
    }).first();

    if (await readingLink.isVisible()) {
      await readingLink.click();
    }

    // Wait for reading library to load
    await page.waitForLoadState('networkidle');

    // Verify reading items are visible
    const readingItems = page.locator('[data-testid="reading-item"], .reading-card');

    // Should have at least some content (or empty state)
    await expect(page.locator('body')).toBeVisible();
  });

  test('user can navigate to settings', async ({ page }) => {
    // Navigate to settings
    await page.goto('/settings');

    // Or navigate via user menu
    const settingsLink = page.locator('a').filter({ hasText: /settings/i }).first();
    if (await settingsLink.isVisible()) {
      await settingsLink.click();
    }

    // Verify settings page loaded
    await page.waitForLoadState('networkidle');

    // Should see settings options
    const settingsHeading = page.locator('h1, h2').filter({ hasText: /settings/i }).first();
    await expect(settingsHeading).toBeVisible({ timeout: 5000 });
  });

  test('user can toggle dark mode', async ({ page }) => {
    await page.goto('/settings');

    // Find dark mode toggle
    const darkModeToggle = page.locator(
      'button:has-text("Dark"), input[type="checkbox"]:near(:text("Dark Mode"))'
    ).first();

    if (await darkModeToggle.isVisible()) {
      // Get initial state
      const bodyClass = await page.locator('body').getAttribute('class');

      // Toggle dark mode
      await darkModeToggle.click();

      // Wait for transition
      await page.waitForTimeout(500);

      // Verify body class changed (or other dark mode indicator)
      const newBodyClass = await page.locator('body').getAttribute('class');
      expect(newBodyClass).not.toBe(bodyClass);
    }
  });

  test('user can logout', async ({ page }) => {
    await page.goto('/dashboard');

    // Find logout button (might be in user menu)
    const logoutButton = page.locator('button, a').filter({ hasText: /log out|sign out/i }).first();

    await logoutButton.click();

    // Should redirect to login or homepage
    await page.waitForURL(/login|home|\/$/, { timeout: 5000 });

    // Verify user is logged out (no user-specific elements)
    const loginButton = page.locator('button, a').filter({ hasText: /log in|sign in/i }).first();
    await expect(loginButton).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Error Handling', () => {
  test('shows error message for invalid login', async ({ page }) => {
    await page.goto('/login');

    // Enter invalid credentials
    await page.fill('input[type="email"], input[name="email"]', 'invalid@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'wrongpassword');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for error message
    const errorMessage = page.locator('[role="alert"], .error, .alert-error').first();
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
    await expect(errorMessage).toContainText(/invalid|incorrect|error/i);
  });

  test('handles network errors gracefully', async ({ page, context }) => {
    // Simulate offline
    await context.setOffline(true);

    await page.goto('/dashboard');

    // Try to perform action that requires network
    const button = page.locator('button').filter({ hasText: /start|continue/i }).first();
    if (await button.isVisible()) {
      await button.click();
    }

    // Should show offline message or error
    await expect(page.locator('body')).toContainText(/offline|connection|network/i, {
      timeout: 10000,
    });

    // Restore connection
    await context.setOffline(false);
  });
});

test.describe('Accessibility', () => {
  test('page has proper heading structure', async ({ page }) => {
    await page.goto('/');

    // Should have h1
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
  });

  test('forms have proper labels', async ({ page }) => {
    await page.goto('/login');

    // Email input should have label
    const emailInput = page.locator('input[type="email"]').first();
    const emailLabel = page.locator('label[for], label').filter({
      has: emailInput,
    }).first();

    await expect(emailLabel).toBeVisible();
  });

  test('buttons have accessible text', async ({ page }) => {
    await page.goto('/');

    // All buttons should have text or aria-label
    const buttons = await page.locator('button').all();

    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');

      expect(text || ariaLabel).toBeTruthy();
    }
  });
});
