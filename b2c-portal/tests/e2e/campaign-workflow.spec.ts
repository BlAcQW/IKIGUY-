import { test } from '@playwright/test';
import { TestUtils } from './utils/test-utils';

/**
 * E2E test for launching a campaign in the B2C portal
 */
test('should launch a campaign', async ({ page }) => {
  const utils = new TestUtils(page);
  await utils.navigateToPage('campaigns');

  const name = `Test Campaign ${Date.now()}`;
  await utils.clickButton(['Create Campaign', 'New Campaign']);
  await utils.fillForm({ 'campaign-name': name });
  await utils.clickButton(['Launch', 'Create']);
  await utils.waitForSuccessMessage();
  await utils.expectText('[data-testid="campaigns-list"], .campaigns-container', name);
});
