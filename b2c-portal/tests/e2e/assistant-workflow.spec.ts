import { test } from '@playwright/test';
import { TestUtils } from './utils/test-utils';

/**
 * E2E test for creating an assistant in the B2C portal
 */
test('should create a new assistant', async ({ page }) => {
  const utils = new TestUtils(page);
  await utils.navigateToPage('assistants');

  const name = `Test Assistant ${Date.now()}`;
  await utils.clickButton(['Create Assistant', 'Add Assistant', '+']);
  await utils.fillForm({ 'assistant-name': name });
  await utils.clickButton(['Create', 'Save']);
  await utils.waitForSuccessMessage();
  await utils.expectText('[data-testid="assistants-list"], .assistants-container', name);
});
