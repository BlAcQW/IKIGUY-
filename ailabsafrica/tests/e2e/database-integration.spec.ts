import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Database Integration Tests', () => {
  let testUser: { email: string; password: string; userId: string };

  test.beforeAll(async () => {
    // Create test user
    testUser = await TestDataManager.createTestUser();
  });

  test.afterAll(async () => {
    // Clean up test user and all associated data
    if (testUser?.userId) {
      // Clean up all test assistants
      const testData = await TestDataManager.getTestData(testUser.userId);
      for (const assistant of testData) {
        await TestDataManager.cleanupTestAssistant(assistant.id);
      }
      
      // Clean up test user
      await TestDataManager.cleanupTestUser(testUser.userId);
    }
  });

  test('should persist assistant creation to database', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    const assistantName = `Test Assistant ${Date.now()}`;
    await FormHelpers.fillField(page, 'assistant-name-input', assistantName);
    await FormHelpers.fillField(page, 'assistant-description-input', 'Test description');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    await FormHelpers.fillField(page, 'first-message-textarea', 'Hello!');
    await FormHelpers.selectOption(page, 'voice-select', 'alloy');
    await FormHelpers.fillField(page, 'demo-url-input', 'https://example.com/test');
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
    
    // Verify data is persisted in database
    const testData = await TestDataManager.getTestData(testUser.userId);
    const createdAssistant = testData.find(assistant => assistant.assistant_name === assistantName);
    
    expect(createdAssistant).toBeDefined();
    expect(createdAssistant?.assistant_type).toBe('sales_cold_call');
    expect(createdAssistant?.demo_url).toBe('https://example.com/test');
    expect(createdAssistant?.status).toBe('active');
  });

  test('should persist assistant updates to database', async ({ page }) => {
    // Create a test assistant first
    const testAssistant = await TestDataManager.createTestAssistant(testUser.userId);
    
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Click edit button for the test assistant
    await page.click(`[data-testid="edit-button-${testAssistant.id}"]`);
    
    // Update assistant details
    const updatedName = `Updated Assistant ${Date.now()}`;
    await FormHelpers.fillField(page, 'assistant-name-input', updatedName);
    await FormHelpers.fillField(page, 'assistant-description-input', 'Updated description');
    
    // Save changes
    await FormHelpers.submitForm(page, 'save-changes-button');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant updated successfully');
    
    // Verify data is updated in database
    const testData = await TestDataManager.getTestData(testUser.userId);
    const updatedAssistant = testData.find(assistant => assistant.id === testAssistant.id);
    
    expect(updatedAssistant?.assistant_name).toBe(updatedName);
    expect(updatedAssistant?.assistant_description).toBe('Updated description');
  });

  test('should persist assistant deletion from database', async ({ page }) => {
    // Create a test assistant first
    const testAssistant = await TestDataManager.createTestAssistant(testUser.userId);
    
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Click delete button for the test assistant
    await page.click(`[data-testid="delete-button-${testAssistant.id}"]`);
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant deleted successfully');
    
    // Verify data is removed from database
    const testData = await TestDataManager.getTestData(testUser.userId);
    const deletedAssistant = testData.find(assistant => assistant.id === testAssistant.id);
    
    expect(deletedAssistant).toBeUndefined();
  });

  test('should persist configuration settings to database', async ({ page }) => {
    // Create a test assistant first
    const testAssistant = await TestDataManager.createTestAssistant(testUser.userId);
    
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Open configuration dialog
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Configure calendar integration
    await page.click('[data-testid="calendar-tab"]');
    await page.click('[data-testid="calendar-enabled-toggle"]');
    await FormHelpers.fillField(page, 'calendar-api-key', 'test-api-key');
    await FormHelpers.fillField(page, 'calendar-calendar-id', 'test-calendar-id');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
    
    // Verify configuration is persisted in database
    const { data: configData, error } = await TestDataManager.supabase
      .from('assistant_configurations')
      .select('*')
      .eq('assistant_id', testAssistant.id)
      .single();
    
    expect(error).toBeNull();
    expect(configData).toBeDefined();
    expect(configData.configuration).toHaveProperty('calendar');
    expect(configData.configuration.calendar.enabled).toBe(true);
    expect(configData.configuration.calendar.apiKey).toBe('test-api-key');
  });

  test('should handle form submission with validation errors', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Try to submit without required fields
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Check for validation errors
    await AssertionHelpers.isVisible(page, 'assistant-name-error');
    await AssertionHelpers.isVisible(page, 'assistant-type-error');
    
    // Verify no data was persisted
    const testData = await TestDataManager.getTestData(testUser.userId);
    const initialCount = testData.length;
    
    // Fill in required fields and submit
    await FormHelpers.fillField(page, 'assistant-name-input', 'Valid Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
    
    // Verify data was persisted
    const updatedTestData = await TestDataManager.getTestData(testUser.userId);
    expect(updatedTestData.length).toBe(initialCount + 1);
  });

  test('should handle concurrent form submissions', async ({ page, context }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    const assistantName = `Concurrent Test ${Date.now()}`;
    await FormHelpers.fillField(page, 'assistant-name-input', assistantName);
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Create a second page context
    const page2 = await context.newPage();
    await AuthHelpers.signIn(page2, testUser.email, testUser.password);
    await NavigationHelpers.goToCreateAssistant(page2);
    
    // Fill in different assistant details on second page
    const assistantName2 = `Concurrent Test 2 ${Date.now()}`;
    await FormHelpers.fillField(page2, 'assistant-name-input', assistantName2);
    await FormHelpers.selectOption(page2, 'assistant-type-select', 'customer_support');
    await FormHelpers.fillField(page2, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Submit both forms simultaneously
    await Promise.all([
      FormHelpers.submitForm(page, 'create-assistant-button'),
      FormHelpers.submitForm(page2, 'create-assistant-button')
    ]);
    
    // Wait for both success messages
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
    await AssertionHelpers.toastShown(page2, 'Assistant created successfully');
    
    // Verify both assistants were persisted
    const testData = await TestDataManager.getTestData(testUser.userId);
    const assistant1 = testData.find(assistant => assistant.assistant_name === assistantName);
    const assistant2 = testData.find(assistant => assistant.assistant_name === assistantName2);
    
    expect(assistant1).toBeDefined();
    expect(assistant2).toBeDefined();
    expect(assistant1?.assistant_type).toBe('sales_cold_call');
    expect(assistant2?.assistant_type).toBe('customer_support');
    
    await page2.close();
  });

  test('should handle database connection errors gracefully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    await FormHelpers.fillField(page, 'assistant-name-input', 'Test Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Simulate database connection error
    await page.route('**/create-assistant', route => {
      route.fulfill({ status: 503, body: 'Database connection failed' });
    });
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Check for error message
    await AssertionHelpers.toastShown(page, 'Database connection failed');
    
    // Verify no data was persisted
    const testData = await TestDataManager.getTestData(testUser.userId);
    const testAssistant = testData.find(assistant => assistant.assistant_name === 'Test Assistant');
    expect(testAssistant).toBeUndefined();
  });

  test('should perform proper cleanup after test failures', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    const assistantName = `Cleanup Test ${Date.now()}`;
    await FormHelpers.fillField(page, 'assistant-name-input', assistantName);
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    
    // Submit form
    await FormHelpers.submitForm(page, 'create-assistant-button');
    
    // Wait for success
    await AssertionHelpers.toastShown(page, 'Assistant created successfully');
    
    // Verify assistant was created
    const testData = await TestDataManager.getTestData(testUser.userId);
    const createdAssistant = testData.find(assistant => assistant.assistant_name === assistantName);
    expect(createdAssistant).toBeDefined();
    
    // Simulate test failure by throwing an error
    // This should trigger the cleanup in afterAll
    throw new Error('Simulated test failure');
  });
});
