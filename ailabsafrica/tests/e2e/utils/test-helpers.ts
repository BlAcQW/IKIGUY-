import { Page, expect } from '@playwright/test';
import { createClient } from '@supabase/supabase-js';

// Supabase client for test data management
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://ljzbzjgvwzivpmlmuxhx.supabase.co';
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Test data management utilities
 */
export class TestDataManager {
  /**
   * Create a test user and return credentials
   */
  static async createTestUser() {
    const testEmail = `test-${Date.now()}@example.com`;
    const testPassword = 'testpassword123';
    
    const { data: { user }, error } = await supabase.auth.admin.createUser({
      email: testEmail,
      password: testPassword,
      email_confirm: true,
    });

    if (error) throw error;

    return {
      email: testEmail,
      password: testPassword,
      userId: user?.id,
    };
  }

  /**
   * Clean up test user
   */
  static async cleanupTestUser(userId: string) {
    await supabase.auth.admin.deleteUser(userId);
  }

  /**
   * Create a test assistant
   */
  static async createTestAssistant(userId: string) {
    const { data, error } = await supabase
      .from('custom_demos')
      .insert({
        user_id: userId,
        assistant_name: `Test Assistant ${Date.now()}`,
        assistant_type: 'sales_cold_call',
        assistant_id: `test-assistant-${Date.now()}`,
        demo_url: 'https://example.com/test-demo',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  /**
   * Clean up test assistant
   */
  static async cleanupTestAssistant(assistantId: string) {
    await supabase
      .from('custom_demos')
      .delete()
      .eq('id', assistantId);
  }

  /**
   * Get all test data for a user
   */
  static async getTestData(userId: string) {
    const { data, error } = await supabase
      .from('custom_demos')
      .select('*')
      .eq('user_id', userId);

    if (error) throw error;
    return data;
  }
}

/**
 * Authentication helpers
 */
export class AuthHelpers {
  /**
   * Sign in a user via the UI
   */
  static async signIn(page: Page, email: string, password: string) {
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', email);
    await page.fill('[data-testid="password-input"]', password);
    await page.click('[data-testid="signin-button"]');
    
    // Wait for successful login
    await expect(page).toHaveURL(/\/dashboard/);
  }

  /**
   * Sign out a user via the UI
   */
  static async signOut(page: Page) {
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="signout-button"]');
    
    // Wait for redirect to login
    await expect(page).toHaveURL(/\/login/);
  }

  /**
   * Check if user is authenticated
   */
  static async isAuthenticated(page: Page): Promise<boolean> {
    try {
      await page.waitForSelector('[data-testid="dashboard"]', { timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Navigation helpers
 */
export class NavigationHelpers {
  /**
   * Navigate to dashboard
   */
  static async goToDashboard(page: Page) {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to create assistant page
   */
  static async goToCreateAssistant(page: Page) {
    await page.goto('/create-assistant');
    await page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to voice agents page
   */
  static async goToVoiceAgents(page: Page) {
    await page.goto('/dashboard');
    await page.click('[data-testid="voice-agents-tab"]');
    await page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to wallet page
   */
  static async goToWallet(page: Page) {
    await page.goto('/dashboard');
    await page.click('[data-testid="wallet-tab"]');
    await page.waitForLoadState('networkidle');
  }
}

/**
 * Form interaction helpers
 */
export class FormHelpers {
  /**
   * Fill a form field
   */
  static async fillField(page: Page, testId: string, value: string) {
    await page.fill(`[data-testid="${testId}"]`, value);
  }

  /**
   * Select an option from a dropdown
   */
  static async selectOption(page: Page, testId: string, value: string) {
    await page.click(`[data-testid="${testId}"]`);
    await page.click(`[data-value="${value}"]`);
  }

  /**
   * Upload a file
   */
  static async uploadFile(page: Page, testId: string, filePath: string) {
    await page.setInputFiles(`[data-testid="${testId}"]`, filePath);
  }

  /**
   * Submit a form
   */
  static async submitForm(page: Page, testId: string) {
    await page.click(`[data-testid="${testId}"]`);
  }
}

/**
 * Assertion helpers
 */
export class AssertionHelpers {
  /**
   * Check if element is visible
   */
  static async isVisible(page: Page, testId: string) {
    await expect(page.locator(`[data-testid="${testId}"]`)).toBeVisible();
  }

  /**
   * Check if element is not visible
   */
  static async isNotVisible(page: Page, testId: string) {
    await expect(page.locator(`[data-testid="${testId}"]`)).not.toBeVisible();
  }

  /**
   * Check if element has text
   */
  static async hasText(page: Page, testId: string, text: string) {
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveText(text);
  }

  /**
   * Check if element contains text
   */
  static async containsText(page: Page, testId: string, text: string) {
    await expect(page.locator(`[data-testid="${testId}"]`)).toContainText(text);
  }

  /**
   * Check if toast notification is shown
   */
  static async toastShown(page: Page, message: string) {
    await expect(page.locator(`[data-testid="toast"]`)).toContainText(message);
  }
}

/**
 * Performance helpers
 */
export class PerformanceHelpers {
  /**
   * Measure page load time
   */
  static async measurePageLoad(page: Page, url: string) {
    const startTime = Date.now();
    await page.goto(url);
    await page.waitForLoadState('networkidle');
    const endTime = Date.now();
    return endTime - startTime;
  }

  /**
   * Measure form submission time
   */
  static async measureFormSubmission(page: Page, formTestId: string) {
    const startTime = Date.now();
    await FormHelpers.submitForm(page, formTestId);
    await page.waitForLoadState('networkidle');
    const endTime = Date.now();
    return endTime - startTime;
  }
}
