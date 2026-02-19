import { Page, expect } from '@playwright/test';

/**
 * Test utilities for E2E tests
 */
export class TestUtils {
  constructor(private page: Page) {}

  async navigateToPage(pageName: string) {
    const pageMap: Record<string, string> = {
      dashboard: '/',
      assistants: '/assistants',
      campaigns: '/campaigns',
      billing: '/billing'
    };

    const path = pageMap[pageName.toLowerCase()];
    if (!path) {
      throw new Error(`Unknown page: ${pageName}`);
    }

    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForSelector('[data-testid="page-content"], main, .container', { timeout: 10000 });
  }

  async fillForm(formData: Record<string, string>) {
    for (const [field, value] of Object.entries(formData)) {
      const selector = `[data-testid="${field}"], [name="${field}"], [id="${field}"]`;
      await this.page.fill(selector, value);
    }
  }

  async clickButton(buttonText: string | string[], options?: { exact?: boolean }) {
    const texts = Array.isArray(buttonText) ? buttonText : [buttonText];

    for (const text of texts) {
      try {
        await this.page.click(`text=${text}`, options);
        return;
      } catch {
        try {
          await this.page.click(`[data-testid="${text}"]`);
          return;
        } catch {
          // continue
        }
      }
    }
    throw new Error(`Could not find button with text: ${texts.join(', ')}`);
  }

  async waitForSuccessMessage(timeout = 5000) {
    await this.page.waitForSelector('[data-testid="success-message"], .success, .toast-success, [role="alert"]', { timeout });
  }

  async expectText(selector: string, expected: string) {
    await expect(this.page.locator(selector)).toContainText(expected);
  }

  async expectVisible(selector: string) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}-${Date.now()}.png`, fullPage: true });
  }
}
