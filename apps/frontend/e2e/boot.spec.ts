/**
 * Minimal E2E baseline (Appendix AL §47).
 *
 * The Foundation only proves that the application boots: the shell renders and an
 * anonymous visitor is routed to sign-in. No Company flow, no Event, no backend
 * dependency is exercised here.
 */

import { expect, test } from '@playwright/test';

test('the console boots and routes an anonymous visitor to sign-in', async ({ page }) => {
  const pageErrors: string[] = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));

  await page.goto('/');

  await expect(page).toHaveTitle('UAP Console');
  await expect(page.getByRole('heading', { name: 'Sign in to UAP Console' })).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test('unauthenticated deep links fall back to sign-in instead of a blank page', async ({ page }) => {
  await page.goto('/tenants/3f1a2b4c-5d6e-4f70-8192-a3b4c5d6e7f8/company');

  await expect(page.getByRole('heading', { name: 'Sign in to UAP Console' })).toBeVisible();
});
