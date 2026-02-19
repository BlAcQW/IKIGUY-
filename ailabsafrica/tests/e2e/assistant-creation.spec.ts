import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Assistant Creation Flow', () => {
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

  test('should create a new assistant successfully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Sales Assistant');
    await FormHelpers.fillField(page, 'assistant-description-input', 'A test sales assistant for E2E testing');
    
    // Select assistant type
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    
    // Fill in system prompt
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful sales assistant.');
    
    // Fill in first message
    await FormHelpers.fillField(page, 'first-message-textarea', 'Hello! How can I help you today?');
    
    // Select voice
    await FormHelpers.selectOption(page, 'voice-select', 'alloy');
    
    // Fill in demo URL
    await FormHelpers.fillField(page, 'demo-url-input', 'https://example.com/test-demo');
    
    // Submit the form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for success message
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should validate required fields', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Try to submit without filling required fields
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Check for validation errors
    await AssertionHelpers.isVisible(page, 'assistant-name-error');
    await AssertionHelpers.isVisible(page, 'assistant-type-error');
    await AssertionHelpers.isVisible(page, 'system-prompt-error');
  });

  test('should handle file upload for knowledge base', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill required fields first
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Assistant with Files');
    await FormHelpers.fillField(page, 'assistant-type-select', 'customer_support');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Upload a test file
    await FormHelpers.uploadFile(page, 'knowledge-base-upload', 'tests/e2e/fixtures/test-document.txt');
    
    // Verify file is uploaded
    await AssertionHelpers.containsText(page, 'uploaded-files-list', 'test-document.txt');
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Assistant');
    await FormHelpers.fillField(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate network error by going offline
    await page.context().setOffline(true);
    
    // Try to submit
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Check for error message
    await AssertionHelpers.toastShown(page, 'Network error');
    
    // Go back online
    await page.context().setOffline(false);
    
    // Try to submit again
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Should succeed now
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should save progress automatically', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in some fields
    await FormHelpers.fillField(page, 'assistant-name-input', 'Auto-save Test Assistant');
    await FormHelpers.fillField(page, 'assistant-description-input', 'Testing auto-save functionality');
    
    // Wait for auto-save
    await page.waitForTimeout(2000);
    
    // Navigate away and back
    await page.goto('/dashboard');
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Check if fields are restored
    await AssertionHelpers.hasText(page, 'assistant-name-input', 'Auto-save Test Assistant');
    await AssertionHelpers.hasText(page, 'assistant-description-input', 'Testing auto-save functionality');
  });
});
