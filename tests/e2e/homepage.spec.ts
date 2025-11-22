/**
 * E2E Test: Homepage
 *
 * This demonstrates basic E2E testing patterns:
 * - Page navigation
 * - Element visibility
 * - Basic interactions
 */

import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Check that page loaded successfully
    await expect(page).toHaveTitle(/LearnR/i);
  });

  test('should display welcome message', async ({ page }) => {
    await page.goto('/');

    // Look for welcome or hero text
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
  });

  test('should have navigation menu', async ({ page }) => {
    await page.goto('/');

    // Check for navigation elements (adjust selectors based on actual implementation)
    const nav = page.locator('nav').first();
    await expect(nav).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Page should still be usable
    await expect(page.locator('body')).toBeVisible();

    // Check that content is readable (not cut off)
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
  });

  test('should load within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('load');

    const loadTime = Date.now() - startTime;

    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });
});
