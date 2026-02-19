import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Error Scenario Tests', () => {
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

  test('should handle network error recovery', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Simulate network error
    await page.route('**/*', route => {
      route.abort('failed');
    });
    
    // Try to refresh the page
    await page.click('[data-testid="refresh-button"]');
    
    // Verify error message is shown
    await AssertionHelpers.toastShown(page, 'Network error');
    
    // Restore network
    await page.unroute('**/*');
    
    // Try to refresh again
    await page.click('[data-testid="refresh-button"]');
    
    // Verify recovery is successful
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
  });

  test('should handle invalid data gracefully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in invalid data
    await FormHelpers.fillField(page, 'assistant-name-input', ''); // Empty name
    await FormHelpers.fillField(page, 'demo-url-input', 'invalid-url'); // Invalid URL
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify validation errors are shown
    await AssertionHelpers.isVisible(page, 'assistant-name-error');
    await AssertionHelpers.isVisible(page, 'demo-url-error');
    
    // Fill in valid data
    await FormHelpers.fillField(page, 'assistant-name-input', 'Valid Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    await FormHelpers.fillField(page, 'demo-url-input', 'https://example.com/valid');
    
    // Submit form again
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle session timeout', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Simulate session timeout by clearing auth tokens
    await page.evaluate(() => {
      localStorage.removeItem('supabase.auth.token');
      sessionStorage.clear();
    });
    
    // Try to perform an action that requires authentication
    await page.click('[data-testid="create-new-agent-button"]');
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/\/login/);
    
    // Verify session timeout message
    await AssertionHelpers.toastShown(page, 'Session expired');
  });

  test('should handle server errors gracefully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in valid data
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate server error
    await page.route('**/create-assistant', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify error message
    await AssertionHelpers.toastShown(page, 'Server error');
    
    // Restore normal behavior
    await page.unroute('**/create-assistant');
    
    // Submit form again
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle API rate limiting', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in valid data
    await FormHelpers.fillField(page, 'assistant-name-input', 'Rate Limited Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate rate limiting
    await page.route('**/create-assistant', route => {
      route.fulfill({ 
        status: 429, 
        body: JSON.stringify({ error: 'Rate limit exceeded' }),
        headers: { 'Retry-After': '60' }
      });
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify rate limit message
    await AssertionHelpers.toastShown(page, 'Rate limit exceeded');
    
    // Restore normal behavior
    await page.unroute('**/create-assistant');
    
    // Wait a bit and try again
    await page.waitForTimeout(1000);
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle malformed response data', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Simulate malformed response
    await page.route('**/custom_demos', route => {
      route.fulfill({ 
        status: 200, 
        body: 'Invalid JSON response',
        headers: { 'Content-Type': 'application/json' }
      });
    });
    
    // Try to refresh the page
    await page.click('[data-testid="refresh-button"]');
    
    // Verify error handling
    await AssertionHelpers.toastShown(page, 'Invalid response');
    
    // Restore normal behavior
    await page.unroute('**/custom_demos');
    
    // Try to refresh again
    await page.click('[data-testid="refresh-button"]');
    
    // Verify recovery
    await AssertionHelpers.isVisible(page, 'voice-agents-content');
  });

  test('should handle authentication errors', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Simulate authentication error
    await page.route('**/*', route => {
      if (route.request().headers()['authorization']) {
        route.fulfill({ status: 401, body: 'Unauthorized' });
      } else {
        route.continue();
      }
    });
    
    // Try to perform an authenticated action
    await page.click('[data-testid="create-new-agent-button"]');
    
    // Verify redirect to login
    await expect(page).toHaveURL(/\/login/);
    
    // Verify authentication error message
    await AssertionHelpers.toastShown(page, 'Authentication required');
    
    // Restore normal behavior
    await page.unroute('**/*');
  });

  test('should handle database connection errors', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in valid data
    await FormHelpers.fillField(page, 'assistant-name-input', 'Database Error Test');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate database connection error
    await page.route('**/create-assistant', route => {
      route.fulfill({ status: 503, body: 'Database connection failed' });
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify database error message
    await AssertionHelpers.toastShown(page, 'Database connection failed');
    
    // Restore normal behavior
    await page.unroute('**/create-assistant');
    
    // Submit form again
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle file upload errors', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in required fields
    await FormHelpers.fillField(page, 'assistant-name-input', 'File Upload Test');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate file upload error
    await page.route('**/storage/**', route => {
      route.fulfill({ status: 413, body: 'File too large' });
    });
    
    // Upload a file
    await FormHelpers.uploadFile(page, 'knowledge-base-upload', 'tests/e2e/fixtures/test-document.txt');
    
    // Verify file upload error
    await AssertionHelpers.toastShown(page, 'File too large');
    
    // Restore normal behavior
    await page.unroute('**/storage/**');
    
    // Submit form without file
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle concurrent modification errors', async ({ page, context }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Create a test assistant
    const testAssistant = await TestDataManager.createTestAssistant(testUser.userId);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Create a second page context
    const page2 = await context.newPage();
    await AuthHelpers.signIn(page2, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page2);
    
    // Try to delete the same assistant from both pages simultaneously
    await Promise.all([
      page.click(`[data-testid="delete-button-${testAssistant.id}"]`),
      page2.click(`[data-testid="delete-button-${testAssistant.id}"]`)
    ]);
    
    // Confirm deletion on both pages
    await Promise.all([
      page.click('[data-testid="confirm-delete-button"]'),
      page2.click('[data-testid="confirm-delete-button"]')
    ]);
    
    // One should succeed, one should fail
    const results = await Promise.all([
      page.waitForResponse('**/manage-assistant'),
      page2.waitForResponse('**/manage-assistant')
    ]);
    
    // Verify at least one deletion succeeded
    const successCount = results.filter(response => response.status() === 200).length;
    expect(successCount).toBeGreaterThan(0);
    
    await page2.close();
  });

  test('should handle timeout errors', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in valid data
    await FormHelpers.fillField(page, 'assistant-name-input', 'Timeout Test Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate timeout
    await page.route('**/create-assistant', route => {
      // Don't respond, let it timeout
      // route.continue() is not called
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for timeout
    await page.waitForTimeout(10000);
    
    // Verify timeout error
    await AssertionHelpers.toastShown(page, 'Request timeout');
    
    // Restore normal behavior
    await page.unroute('**/create-assistant');
    
    // Submit form again
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });

  test('should handle validation errors from server', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in data that might cause server-side validation errors
    await FormHelpers.fillField(page, 'assistant-name-input', 'a'.repeat(1000)); // Very long name
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate server-side validation error
    await page.route('**/create-assistant', route => {
      route.fulfill({ 
        status: 400, 
        body: JSON.stringify({ 
          error: 'Validation failed',
          details: { assistant_name: 'Name too long' }
        })
      });
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify server validation error
    await AssertionHelpers.toastShown(page, 'Validation failed');
    
    // Restore normal behavior
    await page.unroute('**/create-assistant');
    
    // Fix the data and submit again
    await FormHelpers.fillField(page, 'assistant-name-input', 'Valid Name');
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Verify success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
  });
});
