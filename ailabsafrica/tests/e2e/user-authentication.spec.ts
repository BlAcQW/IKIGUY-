import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('User Authentication Flow', () => {
  let testUser: { email: string; password: string; userId: string };

  test.beforeAll(async () => {
    // Create test user
    testUser = await TestDataManager.createTestUser();
  });

  test.afterAll(async () => {
    // Clean up test user
    if (testUser?.userId) {
      await TestDataManager.cleanupTestUser(testUser.userId);
    }
  });

  test('should sign in successfully with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Fill in credentials
    await page.fill('[data-testid="email-input"]', testUser.email);
    await page.fill('[data-testid="password-input"]', testUser.password);
    
    // Submit form
    await page.click('[data-testid="signin-button"]');
    
    // Wait for successful login
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Verify user is authenticated
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Fill in invalid credentials
    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    
    // Submit form
    await page.click('[data-testid="signin-button"]');
    
    // Check for error message
    await AssertionHelpers.toastShown(page, 'Invalid credentials');
    
    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should validate required fields on login', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Try to submit without filling fields
    await page.click('[data-testid="signin-button"]');
    
    // Check for validation errors
    await AssertionHelpers.isVisible(page, 'email-error');
    await AssertionHelpers.isVisible(page, 'password-error');
  });

  test('should sign out successfully', async ({ page }) => {
    // Sign in first
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Click user menu
    await page.click('[data-testid="user-menu"]');
    
    // Click sign out
    await page.click('[data-testid="signout-button"]');
    
    // Wait for redirect to login
    await expect(page).toHaveURL(/\/login/);
    
    // Verify user is not authenticated
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');
    
    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should handle session timeout', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Simulate session timeout by clearing localStorage
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Try to navigate to a protected page
    await page.goto('/dashboard');
    
    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should remember user after page refresh', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Refresh the page
    await page.reload();
    
    // Should still be authenticated and on dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should handle password reset flow', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Click forgot password link
    await page.click('[data-testid="forgot-password-link"]');
    
    // Should navigate to password reset page
    await expect(page).toHaveURL(/\/reset-password/);
    
    // Fill in email
    await page.fill('[data-testid="email-input"]', testUser.email);
    
    // Submit form
    await page.click('[data-testid="reset-password-button"]');
    
    // Check for success message
    await AssertionHelpers.toastShown(page, 'Password reset email sent');
  });

  test('should handle email verification flow', async ({ page }) => {
    // Create a new unverified user
    const unverifiedUser = await TestDataManager.createTestUser();
    
    try {
      // Navigate to login page
      await page.goto('/login');
      
      // Try to sign in with unverified user
      await page.fill('[data-testid="email-input"]', unverifiedUser.email);
      await page.fill('[data-testid="password-input"]', unverifiedUser.password);
      await page.click('[data-testid="signin-button"]');
      
      // Should show verification required message
      await AssertionHelpers.toastShown(page, 'Please verify your email');
      
    } finally {
      // Clean up
      await TestDataManager.cleanupTestUser(unverifiedUser.userId);
    }
  });
});
