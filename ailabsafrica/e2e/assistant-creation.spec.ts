import { test, expect } from '@playwright/test';

test.describe('Assistant Creation E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the create assistant page
    await page.goto('/create-assistant');
  });

  test('should create an assistant with all required fields', async ({ page }) => {
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'Create Voice AI Assistant' })).toBeVisible();

    // Fill in assistant name
    await page.getByLabel('Assistant Name').fill('Test E2E Assistant');

    // Fill in description
    await page.getByLabel('Short Description').fill('This is a test assistant created via E2E testing');

    // Fill in website URL
    await page.getByLabel('Website URL (optional, recommended)').fill('https://example.com');

    // Select assistant type
    await page.getByRole('combobox').first().click();
    await page.getByText('Help Desk').click();

    // Select voice (wait for voices to load)
    await page.waitForTimeout(1000); // Wait for voices to load
    await page.getByRole('combobox').nth(1).click();
    await page.getByText('Paige').click();

    // Verify the Next button is enabled
    await expect(page.getByRole('button', { name: 'Next' })).toBeEnabled();

    // Click Next to proceed to step 2
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on step 2 (template selection)
    await expect(page.getByText('Choose Template (Optional)')).toBeVisible();

    // Skip template selection and proceed to step 3
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on step 3 (knowledge base)
    await expect(page.getByText('Knowledge Base (Optional)')).toBeVisible();

    // Skip knowledge base and proceed to step 4
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on step 4 (system prompt)
    await expect(page.getByText('System Prompt')).toBeVisible();

    // Proceed to deployment
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify we're on the deployment step
    await expect(page.getByText('Deploy Assistant')).toBeVisible();

    // Click Deploy
    await page.getByRole('button', { name: 'Deploy' }).click();

    // Wait for deployment to complete
    await expect(page.getByText(/Creating Vapi assistant/)).toBeVisible();
    
    // Wait for success message or redirect
    await expect(page.getByText(/Assistant created successfully/)).toBeVisible({ timeout: 30000 });
  });

  test('should validate required fields before allowing form submission', async ({ page }) => {
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'Create Voice AI Assistant' })).toBeVisible();

    // Initially, Next button should be disabled
    await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();

    // Fill only assistant name
    await page.getByLabel('Assistant Name').fill('Test Assistant');
    await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();

    // Fill description
    await page.getByLabel('Short Description').fill('Test description');
    await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();

    // Wait for voices to load and select voice
    await page.waitForTimeout(1000);
    await page.getByRole('combobox').nth(1).click();
    await page.getByText('Paige').click();

    // Now Next button should be enabled
    await expect(page.getByRole('button', { name: 'Next' })).toBeEnabled();
  });

  test('should handle form validation errors', async ({ page }) => {
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'Create Voice AI Assistant' })).toBeVisible();

    // Try to submit with empty required fields
    await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();

    // Fill with invalid data (very short name)
    await page.getByLabel('Assistant Name').fill('A');
    await page.getByLabel('Short Description').fill('Test');
    
    // Wait for voices to load and select voice
    await page.waitForTimeout(1000);
    await page.getByRole('combobox').nth(1).click();
    await page.getByText('Paige').click();

    // Form should still be valid even with short names
    await expect(page.getByRole('button', { name: 'Next' })).toBeEnabled();
  });

  test('should persist form data across navigation', async ({ page }) => {
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'Create Voice AI Assistant' })).toBeVisible();

    // Fill in form data
    await page.getByLabel('Assistant Name').fill('Persistent Test Assistant');
    await page.getByLabel('Short Description').fill('This data should persist');
    await page.getByLabel('Website URL (optional, recommended)').fill('https://persistent-test.com');

    // Select assistant type
    await page.getByRole('combobox').first().click();
    await page.getByText('Survey').click();

    // Select voice
    await page.waitForTimeout(1000);
    await page.getByRole('combobox').nth(1).click();
    await page.getByText('Paige').click();

    // Navigate to next step
    await page.getByRole('button', { name: 'Next' }).click();

    // Navigate back
    await page.getByRole('button', { name: 'Previous' }).click();

    // Verify data persists
    await expect(page.getByLabel('Assistant Name')).toHaveValue('Persistent Test Assistant');
    await expect(page.getByLabel('Short Description')).toHaveValue('This data should persist');
    await expect(page.getByLabel('Website URL (optional, recommended)')).toHaveValue('https://persistent-test.com');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network failure
    await page.route('**/functions/list-vapi-voices', route => {
      route.abort('failed');
    });

    // Navigate to create assistant page
    await page.goto('/create-assistant');

    // Should show error message for voice loading failure
    await expect(page.getByText(/Failed to load voices/)).toBeVisible({ timeout: 5000 });
  });
});
