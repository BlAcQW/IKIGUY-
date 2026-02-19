/**
 * End-to-end tests for the complete automation workflow.
 * Tests the full user journey from accessing automations to deploying configurations.
 */

import { test, expect } from '@playwright/test';

test.describe('Automation Workflow E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the automations page
    await page.goto('/automations');
  });

  test('should complete full automation setup workflow', async ({ page }) => {
    // Step 1: Verify automations page loads
    await expect(page.getByRole('heading', { name: 'Automations' })).toBeVisible();
    await expect(page.getByText('Streamline your business processes')).toBeVisible();

    // Step 2: Search and select healthcare industry
    await page.getByPlaceholder('Search industries...').fill('healthcare');
    await page.getByText('Healthcare').click();

    // Step 3: Verify templates page loads for healthcare
    await expect(page.getByRole('heading', { name: 'Healthcare Automations' })).toBeVisible();
    await expect(page.getByText('templates available')).toBeVisible();

    // Step 4: Select a template
    await page.getByText('Patient Appointment Reminders').first().click();

    // Step 5: Verify configuration page loads
    await expect(page.getByRole('heading', { name: 'Configure: Patient Appointment Reminders' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Overview' })).toBeVisible();

    // Step 6: Configure basic settings
    await page.getByLabel('Automation Name').fill('E2E Test Automation');
    await page.getByLabel('Description').fill('End-to-end test automation configuration');
    
    // Enable auto-start
    await page.getByLabel('Start automation immediately after setup').check();

    // Step 7: Configure required calendar integration
    await page.getByRole('tab', { name: 'Calendar Integration' }).click();
    
    await page.getByLabel('Calendar System').selectOption('Google Calendar');
    await page.getByLabel('API Endpoint').fill('https://api.google.com/calendar/v3');
    await page.getByLabel('Authentication Token').fill('test_auth_token_123');
    await page.getByLabel('Sync Frequency').selectOption('Every hour');

    // Test the connection
    await page.getByText('Test Connection').click();
    await expect(page.getByText('Testing Connection...')).toBeVisible();

    // Step 8: Configure optional SMS integration
    await page.getByRole('tab', { name: 'SMS Notifications' }).click();
    
    await page.getByLabel('SMS Provider').selectOption('Twilio');
    await page.getByLabel('API Key').fill('test_api_key_123');
    await page.getByLabel('Sender ID').fill('HOSPITAL');
    await page.getByLabel('Reminder Time').selectOption('24 hours before');

    // Test SMS connection
    await page.getByText('Test Connection').click();
    await expect(page.getByText('Testing Connection...')).toBeVisible();

    // Step 9: Go back to overview and save configuration
    await page.getByRole('tab', { name: 'Overview' }).click();
    await page.getByText('Save Configuration').click();

    // Step 10: Deploy the automation
    await expect(page.getByText('Deploy Automation')).not.toBeDisabled();
    await page.getByText('Deploy Automation').click();

    // Step 11: Verify success page or confirmation
    await expect(page.getByText('automation/success')).toBeVisible();
  });

  test('should filter industries by search term', async ({ page }) => {
    await page.getByPlaceholder('Search industries...').fill('financial');
    
    await expect(page.getByText('Financial Services')).toBeVisible();
    await expect(page.getByText('Healthcare')).not.toBeVisible();
    
    // Clear search
    await page.getByPlaceholder('Search industries...').clear();
    
    await expect(page.getByText('Healthcare')).toBeVisible();
    await expect(page.getByText('Financial Services')).toBeVisible();
  });

  test('should filter by popular industries', async ({ page }) => {
    await page.getByText('Popular').click();
    
    // Popular industries should be shown with "Popular" badges
    await expect(page.getByText('Popular').first()).toBeVisible();
  });

  test('should navigate to custom automation creation', async ({ page }) => {
    await page.getByText('Create Custom Automation').click();
    
    await expect(page).toHaveURL(/.*automations\/custom.*/);
  });

  test('should browse all templates', async ({ page }) => {
    await page.getByText('Browse All Templates').click();
    
    await expect(page).toHaveURL(/.*automations\/templates.*/);
    await expect(page.getByText('142+ pre-built automation templates')).toBeVisible();
  });

  test('should filter templates by complexity', async ({ page }) => {
    // Go to healthcare templates
    await page.getByText('Healthcare').click();
    
    // Filter by complexity
    await page.selectOption('select[name="complexity"]', 'Simple');
    
    // Should only show simple templates
    await expect(page.getByText('Simple')).toBeVisible();
    
    // Change to advanced
    await page.selectOption('select[name="complexity"]', 'Advanced');
    await expect(page.getByText('Advanced')).toBeVisible();
  });

  test('should show integration status correctly', async ({ page }) => {
    // Navigate to configuration
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    // Check integration status indicators
    await expect(page.getByText('Required')).toBeVisible();
    
    // Required integrations should show alert icon
    const calendarIntegration = page.getByText('Calendar Integration').locator('..');
    await expect(calendarIntegration.getByText('Required')).toBeVisible();
  });

  test('should prevent deployment without required integrations', async ({ page }) => {
    // Navigate to configuration
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    // Deploy button should be disabled
    await expect(page.getByText('Deploy Automation')).toBeDisabled();
    await expect(page.getByText('Complete required integrations to deploy')).toBeVisible();
  });

  test('should handle navigation breadcrumbs', async ({ page }) => {
    // Start navigation
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    // Should be able to go back using breadcrumb
    await page.getByRole('button', { name: 'Back' }).first().click();
    
    await expect(page.getByRole('heading', { name: 'Healthcare Automations' })).toBeVisible();
    
    // Go back to main page
    await page.getByRole('button', { name: 'Back' }).click();
    await expect(page.getByRole('heading', { name: 'Automations' })).toBeVisible();
  });

  test('should display template ratings and usage statistics', async ({ page }) => {
    await page.getByText('Healthcare').click();
    
    // Should show ratings and usage counts
    await expect(page.locator('[data-testid="rating"]').first()).toBeVisible();
    await expect(page.getByText(/\d+,\d+ users/)).toBeVisible();
    await expect(page.getByText(/\d+ min/)).toBeVisible();
  });

  test('should handle empty search results', async ({ page }) => {
    await page.getByPlaceholder('Search industries...').fill('nonexistent');
    
    await expect(page.getByText('No industries found')).toBeVisible();
    await expect(page.getByText('Try adjusting your search criteria')).toBeVisible();
    
    // Clear filters button should work
    await page.getByText('Clear Filters').click();
    await expect(page.getByText('Healthcare')).toBeVisible();
  });

  test('should show different complexity badges with correct colors', async ({ page }) => {
    await page.getByText('Healthcare').click();
    
    // Check for complexity badges
    const simpleBadge = page.getByText('Simple').first();
    const mediumBadge = page.getByText('Medium').first();
    const advancedBadge = page.getByText('Advanced').first();
    
    // These should have different styling based on complexity
    if (await simpleBadge.isVisible()) {
      await expect(simpleBadge).toHaveClass(/green/);
    }
    if (await mediumBadge.isVisible()) {
      await expect(mediumBadge).toHaveClass(/yellow/);
    }
    if (await advancedBadge.isVisible()) {
      await expect(advancedBadge).toHaveClass(/red/);
    }
  });
});

test.describe('Automation Configuration Edge Cases', () => {
  test('should handle form validation errors', async ({ page }) => {
    await page.goto('/automations');
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    // Try to save without required fields
    await page.getByRole('tab', { name: 'Calendar Integration' }).click();
    await page.getByText('Save Settings').click();
    
    // Should show validation errors
    await expect(page.getByText('API Endpoint')).toBeVisible();
    await expect(page.getByText('Authentication Token')).toBeVisible();
  });

  test('should persist configuration across tab switches', async ({ page }) => {
    await page.goto('/automations');
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    // Fill overview form
    await page.getByLabel('Automation Name').fill('Persistent Test');
    
    // Switch tabs
    await page.getByRole('tab', { name: 'Calendar Integration' }).click();
    await page.getByRole('tab', { name: 'Overview' }).click();
    
    // Should maintain the filled value
    await expect(page.getByLabel('Automation Name')).toHaveValue('Persistent Test');
  });

  test('should show loading states for async operations', async ({ page }) => {
    await page.goto('/automations');
    await page.getByText('Healthcare').click();
    await page.getByText('Patient Appointment Reminders').first().click();
    
    await page.getByRole('tab', { name: 'SMS Notifications' }).click();
    
    // Fill in required fields
    await page.getByLabel('SMS Provider').selectOption('Twilio');
    await page.getByLabel('API Key').fill('test_key');
    await page.getByLabel('Sender ID').fill('TEST');
    
    // Test connection should show loading state
    await page.getByText('Test Connection').click();
    await expect(page.getByText('Testing Connection...')).toBeVisible();
  });
});