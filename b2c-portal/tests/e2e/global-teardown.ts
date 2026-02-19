import { chromium, FullConfig } from '@playwright/test';

/**
 * Global teardown for B2C portal E2E tests.
 */
async function globalTeardown(config: FullConfig) {
  const { baseURL } = config.projects[0].use;

  console.log('🧹 Cleaning up B2C E2E environment...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto(baseURL!);
    await page.waitForLoadState('networkidle');
    console.log('✅ B2C E2E cleanup complete');
  } catch (error) {
    console.error('❌ B2C E2E cleanup failed:', error);
  } finally {
    await browser.close();
  }
}

export default globalTeardown;
