import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Template Configuration Flow', () => {
  let testUser: { email: string; password: string; userId: string };
  let testAssistant: any;

  test.beforeAll(async () => {
    // Create test user and assistant
    testUser = await TestDataManager.createTestUser();
    testAssistant = await TestDataManager.createTestAssistant(testUser.userId);
  });

  test.afterAll(async () => {
    // Clean up test data
    if (testAssistant?.id) {
      await TestDataManager.cleanupTestAssistant(testAssistant.id);
    }
    if (testUser?.userId) {
      await TestDataManager.cleanupTestUser(testUser.userId);
    }
  });

  test('should open configuration dialog for assistant', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Click configure button for the test assistant
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Verify configuration dialog opens
    await AssertionHelpers.isVisible(page, 'configuration-dialog');
    await AssertionHelpers.containsText(page, 'configuration-dialog-title', 'Configure Assistant');
  });

  test('should configure calendar integration', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to calendar tab
    await page.click('[data-testid="calendar-tab"]');
    
    // Enable calendar integration
    await page.click('[data-testid="calendar-enabled-toggle"]');
    
    // Fill in calendar settings
    await FormHelpers.fillField(page, 'calendar-api-key', 'test-api-key');
    await FormHelpers.fillField(page, 'calendar-calendar-id', 'test-calendar-id');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should configure email integration', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to email tab
    await page.click('[data-testid="email-tab"]');
    
    // Enable email integration
    await page.click('[data-testid="email-enabled-toggle"]');
    
    // Fill in email settings
    await FormHelpers.fillField(page, 'email-smtp-server', 'smtp.gmail.com');
    await FormHelpers.fillField(page, 'email-port', '587');
    await FormHelpers.fillField(page, 'email-username', 'test@example.com');
    await FormHelpers.fillField(page, 'email-password', 'test-password');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should configure chat integrations', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to chats tab
    await page.click('[data-testid="chats-tab"]');
    
    // Configure WhatsApp
    await page.click('[data-testid="whatsapp-enabled-toggle"]');
    await FormHelpers.fillField(page, 'whatsapp-api-key', 'whatsapp-api-key');
    await FormHelpers.fillField(page, 'whatsapp-phone-number', '+1234567890');
    
    // Configure SMS
    await page.click('[data-testid="sms-enabled-toggle"]');
    await FormHelpers.fillField(page, 'sms-api-key', 'sms-api-key');
    
    // Configure Telegram
    await page.click('[data-testid="telegram-enabled-toggle"]');
    await FormHelpers.fillField(page, 'telegram-bot-token', 'telegram-bot-token');
    
    // Configure Slack
    await page.click('[data-testid="slack-enabled-toggle"]');
    await FormHelpers.fillField(page, 'slack-webhook-url', 'https://hooks.slack.com/test');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should configure helpdesk integrations', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to helpdesk tab
    await page.click('[data-testid="helpdesk-tab"]');
    
    // Configure Freshdesk
    await page.click('[data-testid="freshdesk-enabled-toggle"]');
    await FormHelpers.fillField(page, 'freshdesk-domain', 'test.freshdesk.com');
    await FormHelpers.fillField(page, 'freshdesk-api-key', 'freshdesk-api-key');
    
    // Configure Intercom
    await page.click('[data-testid="intercom-enabled-toggle"]');
    await FormHelpers.fillField(page, 'intercom-access-token', 'intercom-access-token');
    
    // Configure Zendesk
    await page.click('[data-testid="zendesk-enabled-toggle"]');
    await FormHelpers.fillField(page, 'zendesk-domain', 'test.zendesk.com');
    await FormHelpers.fillField(page, 'zendesk-api-token', 'zendesk-api-token');
    await FormHelpers.fillField(page, 'zendesk-email', 'test@example.com');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should configure CRM integration', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to CRM tab
    await page.click('[data-testid="crm-tab"]');
    
    // Enable CRM integration
    await page.click('[data-testid="crm-enabled-toggle"]');
    
    // Select CRM type
    await FormHelpers.selectOption(page, 'crm-type-select', 'salesforce');
    
    // Fill in CRM settings
    await FormHelpers.fillField(page, 'crm-instance-url', 'https://test.salesforce.com');
    await FormHelpers.fillField(page, 'crm-client-id', 'crm-client-id');
    await FormHelpers.fillField(page, 'crm-client-secret', 'crm-client-secret');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should configure database integration', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to database tab
    await page.click('[data-testid="database-tab"]');
    
    // Enable database integration
    await page.click('[data-testid="database-enabled-toggle"]');
    
    // Select database type
    await FormHelpers.selectOption(page, 'database-type-select', 'postgresql');
    
    // Fill in database settings
    await FormHelpers.fillField(page, 'database-host', 'localhost');
    await FormHelpers.fillField(page, 'database-port', '5432');
    await FormHelpers.fillField(page, 'database-name', 'testdb');
    await FormHelpers.fillField(page, 'database-username', 'testuser');
    await FormHelpers.fillField(page, 'database-password', 'testpassword');
    
    // Save configuration
    await page.click('[data-testid="save-configuration-button"]');
    
    // Verify success message
    await AssertionHelpers.toastShown(page, 'Configuration saved successfully');
  });

  test('should validate required fields in configuration', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to calendar tab
    await page.click('[data-testid="calendar-tab"]');
    
    // Enable calendar integration
    await page.click('[data-testid="calendar-enabled-toggle"]');
    
    // Try to save without filling required fields
    await page.click('[data-testid="save-configuration-button"]');
    
    // Check for validation errors
    await AssertionHelpers.isVisible(page, 'calendar-api-key-error');
    await AssertionHelpers.isVisible(page, 'calendar-calendar-id-error');
  });

  test('should close configuration dialog', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Verify dialog is open
    await AssertionHelpers.isVisible(page, 'configuration-dialog');
    
    // Click close button
    await page.click('[data-testid="close-configuration-button"]');
    
    // Verify dialog is closed
    await AssertionHelpers.isNotVisible(page, 'configuration-dialog');
  });

  test('should handle configuration save errors', async ({ page }) => {
    // Sign in and open configuration
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    await NavigationHelpers.goToVoiceAgents(page);
    await page.click(`[data-testid="configure-button-${testAssistant.id}"]`);
    
    // Switch to calendar tab
    await page.click('[data-testid="calendar-tab"]');
    
    // Enable calendar integration
    await page.click('[data-testid="calendar-enabled-toggle"]');
    
    // Fill in invalid data
    await FormHelpers.fillField(page, 'calendar-api-key', 'invalid-key');
    await FormHelpers.fillField(page, 'calendar-calendar-id', 'invalid-id');
    
    // Simulate network error
    await page.route('**/manage-assistant-config', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    
    // Try to save
    await page.click('[data-testid="save-configuration-button"]');
    
    // Check for error message
    await AssertionHelpers.toastShown(page, 'Failed to save configuration');
  });
});
