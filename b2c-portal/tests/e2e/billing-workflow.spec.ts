import { test } from '@playwright/test';
import { TestUtils } from './utils/test-utils';

/**
 * E2E test for viewing billing information in the B2C portal
 */
test('should display billing information', async ({ page }) => {
  const utils = new TestUtils(page);
  await utils.navigateToPage('billing');
  await utils.expectVisible('[data-testid="billing-summary"], .billing-summary');
  await utils.takeScreenshot('billing-view');
});
