import { chromium, FullConfig } from '@playwright/test';

/**
 * Global setup for B2C portal E2E tests.
 */
async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;

  console.log('🔧 Setting up B2C E2E environment...');
  console.log(`Base URL: ${baseURL}`);

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto(baseURL!);
    await page.waitForLoadState('networkidle');

    await page.context().storageState({ path: 'tests/e2e/.auth/user.json' });

    console.log('✅ B2C E2E setup complete');
  } catch (error) {
    console.error('❌ B2C E2E setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
