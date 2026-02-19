import { test, expect } from '@playwright/test';

test.describe('User Authentication E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the home page
    await page.goto('/');
  });

  test('should allow user registration and login', async ({ page }) => {
    // Click on sign up button
    await page.getByRole('button', { name: /sign up/i }).click();

    // Fill in registration form
    await page.getByLabel('Email').fill('test-e2e@example.com');
    await page.getByLabel('Password').fill('TestPassword123!');
    await page.getByLabel('Confirm Password').fill('TestPassword123!');

    // Submit registration
    await page.getByRole('button', { name: /sign up/i }).click();

    // Wait for registration to complete
    await expect(page.getByText(/Account created successfully/)).toBeVisible({ timeout: 10000 });

    // Should be redirected to dashboard or login
    await expect(page.getByText(/Welcome/)).toBeVisible({ timeout: 5000 });
  });

  test('should handle login with valid credentials', async ({ page }) => {
    // Click on sign in button
    await page.getByRole('button', { name: /sign in/i }).click();

    // Fill in login form
    await page.getByLabel('Email').fill('test-e2e@example.com');
    await page.getByLabel('Password').fill('TestPassword123!');

    // Submit login
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for login to complete
    await expect(page.getByText(/Welcome/)).toBeVisible({ timeout: 10000 });

    // Verify we're on the dashboard
    await expect(page.getByText(/Dashboard/)).toBeVisible();
  });

  test('should handle login with invalid credentials', async ({ page }) => {
    // Click on sign in button
    await page.getByRole('button', { name: /sign in/i }).click();

    // Fill in login form with invalid credentials
    await page.getByLabel('Email').fill('invalid@example.com');
    await page.getByLabel('Password').fill('WrongPassword123!');

    // Submit login
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should show error message
    await expect(page.getByText(/Invalid email or password/)).toBeVisible({ timeout: 5000 });
  });

  test('should allow user logout', async ({ page }) => {
    // First login
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.getByLabel('Email').fill('test-e2e@example.com');
    await page.getByLabel('Password').fill('TestPassword123!');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for login to complete
    await expect(page.getByText(/Welcome/)).toBeVisible({ timeout: 10000 });

    // Click on user menu/logout
    await page.getByRole('button', { name: /user menu/i }).click();
    await page.getByRole('button', { name: /sign out/i }).click();

    // Should be logged out and redirected to home page
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should require authentication for protected routes', async ({ page }) => {
    // Try to access dashboard without being logged in
    await page.goto('/dashboard');

    // Should be redirected to login page
    await expect(page.getByText(/Sign in to your account/)).toBeVisible();
  });

  test('should handle password reset flow', async ({ page }) => {
    // Click on sign in button
    await page.getByRole('button', { name: /sign in/i }).click();

    // Click on forgot password link
    await page.getByRole('link', { name: /forgot password/i }).click();

    // Fill in email for password reset
    await page.getByLabel('Email').fill('test-e2e@example.com');

    // Submit password reset request
    await page.getByRole('button', { name: /send reset link/i }).click();

    // Should show success message
    await expect(page.getByText(/Password reset link sent/)).toBeVisible({ timeout: 5000 });
  });
});
