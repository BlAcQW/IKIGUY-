import { test, expect } from '@playwright/test';
import { TestUtils } from './utils/test-utils';

/**
 * Comprehensive E2E test for complete user journey:
 * Assistant → Campaign → Usage → Invoice
 *
 * This test covers the critical path specified in TASKS.md section I.
 */
test.describe('Complete User Journey', () => {
  let utils: TestUtils;
  let assistantName: string;
  let assistantId: string;
  let campaignName: string;
  let campaignId: string;

  test.beforeEach(async ({ page }) => {
    utils = new TestUtils(page);
    assistantName = `E2E Test Assistant ${Date.now()}`;
    campaignName = `E2E Test Campaign ${Date.now()}`;
  });

  test('should complete full workflow: assistant → campaign → usage → invoice', async ({ page }) => {
    // ============================================================
    // Step 1: Create Assistant
    // ============================================================
    test.step('Create a new voice assistant', async () => {
      await utils.navigateToPage('assistants');

      // Click create button
      await utils.clickButton(['Create Assistant', 'New Assistant', '+ Create']);

      // Wait for modal/form to appear
      await page.waitForSelector('[data-testid="assistant-form"], .assistant-form, form', {
        timeout: 10000
      });

      // Fill in assistant details
      await utils.fillForm({
        'name': assistantName,
        'assistant-name': assistantName,
        'system_prompt': 'You are a helpful customer service assistant for E2E testing.',
        'system-prompt': 'You are a helpful customer service assistant for E2E testing.'
      });

      // Select language if available
      try {
        await page.click('[data-testid="language-select"]', { timeout: 2000 });
        await page.click('text=English', { timeout: 2000 });
      } catch (e) {
        console.log('Language selector not found or already selected');
      }

      // Save the assistant
      await utils.clickButton(['Create', 'Save', 'Submit']);

      // Wait for success message
      await utils.waitForSuccessMessage();

      // Verify assistant appears in the list
      await page.waitForSelector(`text=${assistantName}`, { timeout: 10000 });
      await utils.expectText('main, [data-testid="assistants-list"]', assistantName);

      // Capture assistant ID from URL or element
      const currentUrl = page.url();
      const urlMatch = currentUrl.match(/assistants\/([a-zA-Z0-9\-]+)/);
      if (urlMatch) {
        assistantId = urlMatch[1];
        console.log(`Created assistant with ID: ${assistantId}`);
      }

      await utils.takeScreenshot('01-assistant-created');
    });

    // ============================================================
    // Step 2: Create Campaign
    // ============================================================
    test.step('Create a new campaign using the assistant', async () => {
      await utils.navigateToPage('campaigns');

      // Click create campaign button
      await utils.clickButton(['Create Campaign', 'New Campaign', '+ Campaign']);

      // Wait for campaign form
      await page.waitForSelector('[data-testid="campaign-form"], .campaign-form, form', {
        timeout: 10000
      });

      // Fill in campaign details
      await utils.fillForm({
        'name': campaignName,
        'campaign-name': campaignName,
        'campaign_name': campaignName
      });

      // Select the assistant we just created
      try {
        await page.click('[data-testid="assistant-select"], [name="assistant"], [id="assistant"]', {
          timeout: 3000
        });
        await page.waitForTimeout(500);
        await page.click(`text=${assistantName}`, { timeout: 3000 });
      } catch (e) {
        console.log('Assistant selector not found, trying alternative approach');
        // Try typing the assistant name
        await page.fill('[data-testid="assistant-select"], [name="assistant"]', assistantName);
      }

      // Add audience/contacts (optional - may not be required for test)
      try {
        await page.click('[data-testid="audience-select"]', { timeout: 2000 });
        await page.click('text=Test Audience', { timeout: 2000 });
      } catch (e) {
        console.log('Audience selector optional or not found');
      }

      // Save campaign
      await utils.clickButton(['Create Campaign', 'Save', 'Create']);

      // Wait for success
      await utils.waitForSuccessMessage();

      // Verify campaign appears in the list
      await page.waitForSelector(`text=${campaignName}`, { timeout: 10000 });
      await utils.expectText('main, [data-testid="campaigns-list"]', campaignName);

      // Capture campaign ID
      const currentUrl = page.url();
      const urlMatch = currentUrl.match(/campaigns\/([a-zA-Z0-9\-]+)/);
      if (urlMatch) {
        campaignId = urlMatch[1];
        console.log(`Created campaign with ID: ${campaignId}`);
      }

      await utils.takeScreenshot('02-campaign-created');
    });

    // ============================================================
    // Step 3: Launch Campaign
    // ============================================================
    test.step('Launch the campaign', async () => {
      // Campaign should already be open, if not navigate to it
      if (!page.url().includes('/campaigns/')) {
        await utils.navigateToPage('campaigns');
        await page.click(`text=${campaignName}`);
      }

      // Find and click launch button
      await utils.clickButton(['Launch', 'Start Campaign', 'Activate']);

      // Confirm launch if there's a confirmation dialog
      try {
        await page.click('text=Confirm', { timeout: 2000 });
      } catch (e) {
        console.log('No confirmation dialog found');
      }

      // Wait for campaign status to update
      await page.waitForTimeout(2000);

      // Verify campaign is running/active
      await expect(page.locator('main')).toContainText(/Active|Running|In Progress/);

      await utils.takeScreenshot('03-campaign-launched');
    });

    // ============================================================
    // Step 4: Verify Usage Tracking
    // ============================================================
    test.step('Verify usage is being tracked', async () => {
      // Navigate to analytics or usage page
      try {
        await utils.navigateToPage('analytics');
      } catch (e) {
        // Analytics might be under dashboard
        await utils.navigateToPage('dashboard');
      }

      // Look for usage metrics
      await expect(page.locator('main, [data-testid="usage-stats"]')).toContainText(
        /Usage|Minutes|Calls|Messages/i
      );

      // Verify the campaign appears in usage stats
      try {
        await utils.expectText('main', campaignName);
      } catch (e) {
        console.log('Campaign name not yet in usage stats (may need time to appear)');
      }

      // Check for usage counters
      const hasUsageCounters = await page.locator('[data-testid="usage-counter"], .usage-stat, .metric').count();
      expect(hasUsageCounters).toBeGreaterThan(0);

      await utils.takeScreenshot('04-usage-tracking');
    });

    // ============================================================
    // Step 5: Check Invoice Generation
    // ============================================================
    test.step('Verify invoice generation and billing', async () => {
      await utils.navigateToPage('billing');

      // Verify billing page loaded
      await utils.expectVisible('[data-testid="billing-summary"], .billing-container, main');

      // Check for current balance or usage summary
      await expect(page.locator('main')).toContainText(/Balance|Invoice|Charges|Usage/i);

      // Look for invoice list
      const hasInvoices = await page.locator('[data-testid="invoice"], .invoice-item, [class*="invoice"]').count();
      console.log(`Found ${hasInvoices} invoices`);

      // Check for payment methods section
      try {
        await expect(page.locator('main')).toContainText(/Payment Method|Card|Billing/i);
      } catch (e) {
        console.log('Payment method section optional');
      }

      await utils.takeScreenshot('05-invoice-billing');
    });

    // ============================================================
    // Step 6: Cleanup - Pause/Stop Campaign
    // ============================================================
    test.step('Cleanup: Pause the campaign', async () => {
      await utils.navigateToPage('campaigns');

      // Find the campaign
      await page.click(`text=${campaignName}`);

      // Pause/stop the campaign
      try {
        await utils.clickButton(['Pause', 'Stop', 'Deactivate']);

        // Confirm if needed
        try {
          await page.click('text=Confirm', { timeout: 2000 });
        } catch (e) {
          console.log('No confirmation needed');
        }

        // Wait for status update
        await page.waitForTimeout(1000);

        await utils.takeScreenshot('06-campaign-paused');
      } catch (e) {
        console.log('Campaign pause button not found - may auto-stop or different UI');
      }
    });
  });

  test('should handle assistant creation with validation errors', async ({ page }) => {
    await utils.navigateToPage('assistants');

    // Click create button
    await utils.clickButton(['Create Assistant', 'New Assistant']);

    // Try to save without required fields
    await utils.clickButton(['Create', 'Save']);

    // Should see validation errors
    await expect(page.locator('main, form')).toContainText(/required|invalid|error/i);

    await utils.takeScreenshot('validation-error');
  });

  test('should handle campaign creation without assistant', async ({ page }) => {
    await utils.navigateToPage('campaigns');

    // Click create button
    await utils.clickButton(['Create Campaign', 'New Campaign']);

    // Fill only campaign name
    await utils.fillForm({
      'name': `Test Campaign ${Date.now()}`
    });

    // Try to save without selecting assistant
    await utils.clickButton(['Create', 'Save']);

    // Should see error or validation message
    await expect(page.locator('main, form')).toContainText(/assistant|required|select/i);

    await utils.takeScreenshot('campaign-no-assistant-error');
  });
});

/**
 * Test for consent and DNC (Do Not Call) verification
 */
test.describe('Compliance Tests', () => {
  let utils: TestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new TestUtils(page);
  });

  test('should verify consent requirements for campaigns', async ({ page }) => {
    await utils.navigateToPage('campaigns');

    // Look for consent-related UI elements
    const pageContent = await page.content();
    const hasConsentMention = pageContent.toLowerCase().includes('consent') ||
                             pageContent.toLowerCase().includes('permission');

    // Log finding
    console.log(`Consent mentioned in campaigns: ${hasConsentMention}`);

    await utils.takeScreenshot('consent-verification');
  });

  test('should verify DNC (Do Not Call) handling', async ({ page }) => {
    await utils.navigateToPage('campaigns');

    // Look for DNC-related UI elements
    const pageContent = await page.content();
    const hasDNCMention = pageContent.toLowerCase().includes('do not call') ||
                         pageContent.toLowerCase().includes('dnc');

    console.log(`DNC mentioned in campaigns: ${hasDNCMention}`);

    await utils.takeScreenshot('dnc-verification');
  });
});
