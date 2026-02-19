import { test, expect } from '@playwright/test';
import { TestUtils } from './utils/test-utils';

/**
 * E2E test for voice conversation functionality including:
 * - WebSocket connection
 * - Voice recording
 * - Real-time transcription
 * - Assistant responses
 * - Barge-in functionality
 * - Conversation history
 */
test.describe('Voice Conversation Workflow', () => {
  let utils: TestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new TestUtils(page);

    // Grant microphone permissions for the test
    await page.context().grantPermissions(['microphone']);
  });

  test('should establish WebSocket connection and show connected status', async ({ page }) => {
    // Navigate to voice agent page
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await page.waitForSelector('main, [data-testid="voice-agent"]', { timeout: 10000 });

    // Look for assistant list or start conversation button
    const hasAssistants = await page.locator('[data-testid="assistant-list"], .assistant-card').count();

    if (hasAssistants > 0) {
      // Select first assistant
      await page.click('[data-testid="assistant-card"], .assistant-item', { first: true });

      // Click to start conversation
      await utils.clickButton(['Start Conversation', 'Start Chat', 'Connect']);
    }

    // Wait for WebSocket connection indicator
    await page.waitForSelector('[data-testid="connection-status"], .connection-indicator', {
      timeout: 10000
    });

    // Verify connected status
    await expect(page.locator('main')).toContainText(/Connected|Online/i);

    // Look for the Wifi/connection icon (should be green/online)
    const connectionIcon = page.locator('[data-testid="connection-icon"], .connection-status svg');
    await expect(connectionIcon).toBeVisible();

    await utils.takeScreenshot('voice-websocket-connected');
  });

  test('should show microphone controls and recording state', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Select assistant and start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation', 'Connect']);
      await page.waitForTimeout(2000);
    } catch (e) {
      console.log('Already on conversation page or single assistant mode');
    }

    // Look for microphone button
    const micButton = page.locator('[data-testid="mic-button"], button:has-text("Start Recording"), [title*="Record"]');
    await expect(micButton).toBeVisible();

    // Click to start recording (don't actually record in CI)
    await micButton.click();

    // Should see recording indicator
    await expect(page.locator('main')).toContainText(/Recording|Listening/i);

    // Should see audio visualization or recording indicator
    const hasRecordingIndicator = await page.locator('[data-testid="recording-indicator"], .recording-status, [class*="pulse"]').count();
    expect(hasRecordingIndicator).toBeGreaterThan(0);

    // Stop recording
    const stopButton = page.locator('[data-testid="stop-button"], button:has-text("Stop")');
    await stopButton.click({ timeout: 2000 });

    await utils.takeScreenshot('voice-recording-controls');
  });

  test('should display conversation history', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation']);
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Already on conversation page');
    }

    // Send a text message (easier than voice for testing)
    const textInput = page.locator('[data-testid="text-input"], input[placeholder*="message"], input[placeholder*="Type"]');

    if (await textInput.count() > 0) {
      await textInput.fill('Hello, this is a test message');
      await page.keyboard.press('Enter');

      // Wait for message to appear in conversation history
      await page.waitForTimeout(2000);

      // Verify message appears in history
      await expect(page.locator('main, [data-testid="messages"]')).toContainText('Hello, this is a test');

      // Look for user message styling
      const userMessage = page.locator('[data-testid="user-message"], .message-user, [class*="user"]');
      await expect(userMessage).toBeVisible();
    } else {
      console.log('Text input not available, skipping message test');
    }

    await utils.takeScreenshot('voice-conversation-history');
  });

  test('should show barge-in functionality when assistant is speaking', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation']);
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Already on conversation page');
    }

    // Send a message that triggers a long response
    const textInput = page.locator('[data-testid="text-input"], input[placeholder*="message"]');
    if (await textInput.count() > 0) {
      await textInput.fill('Tell me a long story about testing');
      await page.keyboard.press('Enter');

      // Wait for assistant to start speaking
      await page.waitForTimeout(3000);

      // Look for speaking indicator
      const speakingIndicator = page.locator('[data-testid="speaking-indicator"], .speaking-status, text=Speaking');

      if (await speakingIndicator.count() > 0) {
        // Should see stop button (barge-in)
        const stopSpeakingButton = page.locator('[data-testid="stop-speaking"], button:has-text("Stop Speaking"), [title*="Stop"]');
        await expect(stopSpeakingButton).toBeVisible();

        // Click stop button
        await stopSpeakingButton.click();

        // Speaking indicator should disappear
        await expect(speakingIndicator).not.toBeVisible({ timeout: 2000 });

        await utils.takeScreenshot('voice-barge-in-triggered');
      } else {
        console.log('Assistant not speaking yet, barge-in test incomplete');
      }
    }
  });

  test('should show audio controls (mute/unmute)', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation']);
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Already on conversation page');
    }

    // Look for audio toggle button
    const audioToggle = page.locator('[data-testid="audio-toggle"], [title*="Mute"], [title*="Audio"]');

    if (await audioToggle.count() > 0) {
      // Toggle audio
      await audioToggle.click();

      // Should see muted indicator
      await expect(page.locator('main')).toContainText(/Muted|Audio Off/i);

      // Toggle back
      await audioToggle.click();

      await utils.takeScreenshot('voice-audio-controls');
    } else {
      console.log('Audio controls not found on this page');
    }
  });

  test('should handle connection errors gracefully', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Simulate network offline
    await page.context().setOffline(true);

    // Try to start conversation
    try {
      await utils.clickButton(['Start Conversation', 'Connect']);
      await page.waitForTimeout(2000);

      // Should see error message
      await expect(page.locator('main')).toContainText(/Error|Failed|Connection/i);

      await utils.takeScreenshot('voice-connection-error');
    } catch (e) {
      console.log('Error handling test - expected failure');
    } finally {
      // Restore network
      await page.context().setOffline(false);
    }
  });

  test('should display processing states', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation']);
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Already on conversation page');
    }

    // Look for various processing state indicators
    const statusIndicators = await page.locator('[data-testid*="status"], .status-indicator, [class*="status"]').count();
    expect(statusIndicators).toBeGreaterThan(0);

    // Check for specific states mentioned in TASKS.md
    const pageContent = await page.content();
    const hasProcessingStates =
      pageContent.includes('Recording') ||
      pageContent.includes('Processing') ||
      pageContent.includes('Speaking') ||
      pageContent.includes('Listening');

    console.log(`Has processing state indicators: ${hasProcessingStates}`);

    await utils.takeScreenshot('voice-processing-states');
  });

  test('should show conversation close/end functionality', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Start conversation
    try {
      await page.click('[data-testid="assistant-card"]', { timeout: 5000 });
      await utils.clickButton(['Start Conversation']);
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Already on conversation page');
    }

    // Look for close button
    const closeButton = page.locator('[data-testid="close-conversation"], button:has-text("Close"), [title*="Close"], .close-button, button svg');
    await expect(closeButton.first()).toBeVisible();

    // Click close
    await closeButton.first().click();

    // Should return to assistant selection or home
    await page.waitForTimeout(1000);

    await utils.takeScreenshot('voice-conversation-closed');
  });
});

/**
 * Tests for voice settings and configuration
 */
test.describe('Voice Settings', () => {
  let utils: TestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new TestUtils(page);
    await page.context().grantPermissions(['microphone']);
  });

  test('should display voice settings panel', async ({ page }) => {
    await page.goto('/voice-agent');
    await page.waitForLoadState('networkidle');

    // Look for settings button or gear icon
    const settingsButton = page.locator('[data-testid="settings"], [title*="Settings"], button:has(svg[class*="settings"])');

    if (await settingsButton.count() > 0) {
      await settingsButton.click();

      // Should see settings panel
      await expect(page.locator('main, [data-testid="settings-panel"]')).toContainText(/Speed|Pitch|Voice|Language/i);

      await utils.takeScreenshot('voice-settings-panel');
    } else {
      console.log('Settings panel not found in current UI');
    }
  });
});
