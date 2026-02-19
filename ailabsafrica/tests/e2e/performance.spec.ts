import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, PerformanceHelpers } from './utils/test-helpers';

test.describe('Performance Tests', () => {
  let testUser: { email: string; password: string; userId: string };

  test.beforeAll(async () => {
    // Create test user
    testUser = await TestDataManager.createTestUser();
  });

  test.afterAll(async () => {
    // Clean up test user
    if (testUser?.userId) {
      await TestDataManager.cleanupTestUser(testUser.userId);
    }
  });

  test('should load dashboard within performance budget', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Measure dashboard load time
    const loadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Performance budget: dashboard should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    console.log(`Dashboard load time: ${loadTime}ms`);
  });

  test('should load create assistant page within performance budget', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Measure create assistant page load time
    const loadTime = await PerformanceHelpers.measurePageLoad(page, '/create-assistant');
    
    // Performance budget: create assistant page should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
    
    console.log(`Create assistant page load time: ${loadTime}ms`);
  });

  test('should submit assistant creation form within performance budget', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Fill in assistant details
    await FormHelpers.fillField(page, 'assistant-name-input', 'Performance Test Assistant');
    await FormHelpers.selectOption(page, 'assistant-type-select', 'sales_cold_call');
    await FormHelpers.fillField(page, 'system-prompt-textarea', 'You are a helpful assistant.');
    await FormHelpers.fillField(page, 'first-message-textarea', 'Hello!');
    await FormHelpers.selectOption(page, 'voice-select', 'alloy');
    await FormHelpers.fillField(page, 'demo-url-input', 'https://example.com/test');
    
    // Measure form submission time
    const submissionTime = await PerformanceHelpers.measureFormSubmission(page, 'create-assistant-button');
    
    // Performance budget: form submission should complete within 5 seconds
    expect(submissionTime).toBeLessThan(5000);
    
    console.log(`Assistant creation form submission time: ${submissionTime}ms`);
  });

  test('should load voice agents list within performance budget', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Create some test assistants for realistic testing
    for (let i = 0; i < 5; i++) {
      await TestDataManager.createTestAssistant(testUser.userId);
    }
    
    // Measure voice agents page load time
    const loadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Performance budget: voice agents list should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
    
    console.log(`Voice agents list load time: ${loadTime}ms`);
  });

  test('should handle large datasets efficiently', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Create many test assistants to simulate large dataset
    const startTime = Date.now();
    for (let i = 0; i < 20; i++) {
      await TestDataManager.createTestAssistant(testUser.userId);
    }
    const creationTime = Date.now() - startTime;
    
    console.log(`Created 20 assistants in ${creationTime}ms`);
    
    // Measure page load time with large dataset
    const loadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Performance budget: should handle large datasets within 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    console.log(`Dashboard load time with 20+ assistants: ${loadTime}ms`);
  });

  test('should perform search operations efficiently', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Measure search operation time
    const startTime = Date.now();
    await FormHelpers.fillField(page, 'search-input', 'test');
    await page.waitForLoadState('networkidle');
    const searchTime = Date.now() - startTime;
    
    // Performance budget: search should complete within 1 second
    expect(searchTime).toBeLessThan(1000);
    
    console.log(`Search operation time: ${searchTime}ms`);
  });

  test('should handle concurrent operations efficiently', async ({ page, context }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Create multiple page contexts for concurrent operations
    const pages = [];
    for (let i = 0; i < 3; i++) {
      const newPage = await context.newPage();
      await AuthHelpers.signIn(newPage, testUser.email, testUser.password);
      pages.push(newPage);
    }
    
    // Perform concurrent operations
    const startTime = Date.now();
    await Promise.all([
      PerformanceHelpers.measurePageLoad(pages[0], '/dashboard'),
      PerformanceHelpers.measurePageLoad(pages[1], '/create-assistant'),
      PerformanceHelpers.measurePageLoad(pages[2], '/dashboard')
    ]);
    const concurrentTime = Date.now() - startTime;
    
    // Performance budget: concurrent operations should complete within 4 seconds
    expect(concurrentTime).toBeLessThan(4000);
    
    console.log(`Concurrent page loads time: ${concurrentTime}ms`);
    
    // Clean up
    for (const p of pages) {
      await p.close();
    }
  });

  test('should handle memory usage efficiently', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    // Perform multiple navigation operations
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="wallet-tab"]');
      await page.waitForLoadState('networkidle');
      await page.click('[data-testid="voice-agents-tab"]');
      await page.waitForLoadState('networkidle');
    }
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    // Calculate memory increase
    const memoryIncrease = finalMemory - initialMemory;
    
    // Performance budget: memory increase should be less than 50MB
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    
    console.log(`Memory increase after 10 navigation cycles: ${memoryIncrease / (1024 * 1024)}MB`);
  });

  test('should handle network latency gracefully', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Simulate slow network
    await page.route('**/*', route => {
      // Add 500ms delay to all requests
      setTimeout(() => {
        route.continue();
      }, 500);
    });
    
    // Measure page load time with slow network
    const loadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Performance budget: should handle slow network within 6 seconds
    expect(loadTime).toBeLessThan(6000);
    
    console.log(`Dashboard load time with slow network: ${loadTime}ms`);
    
    // Restore normal network
    await page.unroute('**/*');
  });

  test('should optimize database queries', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to voice agents
    await NavigationHelpers.goToVoiceAgents(page);
    
    // Measure initial load time
    const initialLoadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Refresh the page to test cached queries
    const refreshLoadTime = await PerformanceHelpers.measurePageLoad(page, '/dashboard');
    
    // Performance budget: refresh should be faster than initial load
    expect(refreshLoadTime).toBeLessThan(initialLoadTime);
    
    console.log(`Initial load time: ${initialLoadTime}ms`);
    console.log(`Refresh load time: ${refreshLoadTime}ms`);
    console.log(`Performance improvement: ${initialLoadTime - refreshLoadTime}ms`);
  });

  test('should handle image and asset loading efficiently', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to dashboard
    await NavigationHelpers.goToDashboard(page);
    
    // Measure time to load all images and assets
    const startTime = Date.now();
    
    // Wait for all images to load
    await page.waitForLoadState('networkidle');
    
    // Check if all images are loaded
    const imageLoadStatus = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img'));
      return images.every(img => img.complete);
    });
    
    const assetLoadTime = Date.now() - startTime;
    
    // Performance budget: all assets should load within 3 seconds
    expect(assetLoadTime).toBeLessThan(3000);
    expect(imageLoadStatus).toBe(true);
    
    console.log(`Asset loading time: ${assetLoadTime}ms`);
    console.log(`All images loaded: ${imageLoadStatus}`);
  });

  test('should handle form validation efficiently', async ({ page }) => {
    // Sign in
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Navigate to create assistant page
    await NavigationHelpers.goToCreateAssistant(page);
    
    // Measure form validation time
    const startTime = Date.now();
    
    // Fill in a field and trigger validation
    await FormHelpers.fillField(page, 'assistant-name-input', '');
    await page.keyboard.press('Tab'); // Trigger blur event
    
    // Wait for validation to complete
    await page.waitForSelector('[data-testid="assistant-name-error"]', { timeout: 1000 });
    
    const validationTime = Date.now() - startTime;
    
    // Performance budget: form validation should complete within 500ms
    expect(validationTime).toBeLessThan(500);
    
    console.log(`Form validation time: ${validationTime}ms`);
  });
});
