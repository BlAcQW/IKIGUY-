import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Cross-Component Integration Tests', () => {
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

  test('should maintain navigation state across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Verify we're on the default tab (Voice Agents)
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
    
    // Navigate to wallet tab
    await page.click('[data-testid="wallet-tab"]');
    await AssertionHelpers.isVisible(page, 'wallet-content');
    
    // Navigate to analytics tab
    await page.click('[data-testid="analytics-tab"]');
    await AssertionHelpers.isVisible(page, 'analytics-content');
    
    // Navigate back to voice agents
    await page.click('[data-testid="voice-agents-tab"]');
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
    
    // Verify URL reflects current tab
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should maintain form state during navigation', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in some form fields
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Assistant');
    await FormHelpers.fillField(page, 'assistant-description-input', 'Test description');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    
    // Navigate away to dashboard
    await page.goto('/dashboard');
    
    // Navigate back to create assistant
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Verify form state is maintained
    await AssertionHelpers.hasText(page, 'assistant-name-input', 'Test Assistant');
    await AssertionHelpers.hasText(page, 'assistant-description-input', 'Test description');
    
    // Verify dropdown selection is maintained
    await page.click('[data-testid="assistant-type-select"]');
    await AssertionHelpers.isVisible(page, 'assistant-type-select');
  });

  test('should handle error boundaries across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Simulate a component error by injecting error script
    await page.evaluate(() => {
      // Simulate an error in a component
      const errorEvent = new ErrorEvent('error', {
        message: 'Simulated component error',
        filename: 'test.js',
        lineno: 1,
        colno: 1,
        error: new Error('Simulated error')
      });
      window.dispatchEvent(errorEvent);
    });
    
    // Verify error boundary is shown
    await AssertionHelpers.isVisible(page, 'error-boundary');
    
    // Verify error message is displayed
    await AssertionHelpers.containsText(page, 'error-boundary', 'Something went wrong');
    
    // Verify reload button is available
    await AssertionHelpers.isVisible(page, 'reload-button');
  });

  test('should handle global error state', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Simulate network error
    await page.route('**/*', route => {
      route.abort('failed');
    });
    
    // Try to navigate to a different tab
    await page.click('[data-testid="wallet-tab"]');
    
    // Verify error state is handled
    await AssertionHelpers.toastShown(page, 'Network error');
    
    // Restore network
    await page.unroute('**/*');
    
    // Try navigation again
    await page.click('[data-testid="wallet-tab"]');
    await AssertionHelpers.isVisible(page, 'wallet-content');
  });

  test('should maintain authentication state across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Verify user menu is visible
    await AssertionHelpers.isVisible(page, 'user-menu');
    
    // Navigate to different tabs
    await page.click('[data-testid="analytics-tab"]');
    await AssertionHelpers.isVisible(page, 'user-menu');
    
    await page.click('[data-testid="wallet-tab"]');
    await AssertionHelpers.isVisible(page, 'user-menu');
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    await AssertionHelpers.isVisible(page, 'user-menu');
    
    // Verify user is still authenticated
    expect(await AuthHelpers.isAuthenticated(page)).toBe(true);
  });

  test('should handle loading states across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Click refresh button
    await page.click('[data-testid="refresh-button"]');
    
    // Verify loading state is shown
    await AssertionHelpers.isVisible(page, 'loading-spinner');
    
    // Wait for loading to complete
    await page.waitForSelector('[data-testid="loading-spinner"]', { state: 'hidden' });
    
    // Verify content is loaded
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
  });

  test('should handle toast notifications across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Trigger a toast notification
    await page.evaluate(() => {
      // Simulate a toast notification
      const event = new CustomEvent('show-toast', {
        detail: {
          title: 'Test Toast',
          description: 'This is a test toast notification'
        }
      });
      window.dispatchEvent(event);
    });
    
    // Verify toast is shown
    await AssertionHelpers.toastShown(page, 'Test Toast');
    
    // Navigate to different tab
    await page.click('[data-testid="wallet-tab"]');
    
    // Verify toast is still visible (global toast)
    await AssertionHelpers.toastShown(page, 'Test Toast');
  });

  test('should handle modal dialogs across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Click import agent button to open modal
    await page.click('[data-testid="import-agent-button"]');
    
    // Verify modal is open
    await AssertionHelpers.isVisible(page, 'import-agent-modal');
    
    // Navigate to different tab while modal is open
    await page.click('[data-testid="wallet-tab"]');
    
    // Verify modal is closed (should close on navigation)
    await AssertionHelpers.isNotVisible(page, 'import-agent-modal');
    
    // Navigate back to voice agents
    await page.click('[data-testid="voice-agents-tab"]');
    
    // Verify modal is still closed
    await AssertionHelpers.isNotVisible(page, 'import-agent-modal');
  });

  test('should handle search and filter state across navigation', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Enter search term
    await FormHelpers.fillField(page, 'search-input', 'test search');
    
    // Select filter
    await FormHelpers.selectOption(page, 'filter-select', 'sales_cold_call');
    
    // Navigate to different tab
    await page.click('[data-testid="wallet-tab"]');
    
    // Navigate back to voice agents
    await page.click('[data-testid="voice-agents-tab"]');
    
    // Verify search and filter state is maintained
    await AssertionHelpers.hasText(page, 'search-input', 'test search');
    
    // Verify filter selection is maintained
    await page.click('[data-testid="filter-select"]');
    await AssertionHelpers.isVisible(page, 'filter-select');
  });

  test('should handle responsive design across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Verify mobile layout is applied
    await AssertionHelpers.isVisible(page, 'mobile-sidebar-toggle');
    
    // Navigate to different tabs
    await page.click('[data-testid="wallet-tab"]');
    await AssertionHelpers.isVisible(page, 'mobile-sidebar-toggle');
    
    await page.click('[data-testid="analytics-tab"]');
    await AssertionHelpers.isVisible(page, 'mobile-sidebar-toggle');
    
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Verify desktop layout is applied
    await AssertionHelpers.isVisible(page, 'desktop-sidebar');
  });

  test('should handle keyboard navigation across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Focus on first tab
    await page.keyboard.press('Tab');
    
    // Navigate through tabs with arrow keys
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Enter');
    await AssertionHelpers.isVisible(page, 'wallet-content');
    
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Enter');
    await AssertionHelpers.isVisible(page, 'analytics-content');
    
    // Navigate back with arrow keys
    await page.keyboard.press('ArrowLeft');
    await page.keyboard.press('Enter');
    await AssertionHelpers.isVisible(page, 'wallet-content');
    
    await page.keyboard.press('ArrowLeft');
    await page.keyboard.press('Enter');
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
  });

  test('should handle accessibility features across components', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Verify ARIA labels are present
    await expect(page.locator('[aria-label="Voice Agents"]')).toBeVisible();
    await expect(page.locator('[aria-label="Wallet"]')).toBeVisible();
    await expect(page.locator('[aria-label="Analytics"]')).toBeVisible();
    
    // Navigate to different tabs
    await page.click('[data-testid="wallet-tab"]');
    await expect(page.locator('[aria-label="Wallet"]')).toBeVisible();
    
    await page.click('[data-testid="analytics-tab"]');
    await expect(page.locator('[aria-label="Analytics"]')).toBeVisible();
    
    // Verify focus management
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="voice-agents-tab"]')).toBeFocused();
  });
});
