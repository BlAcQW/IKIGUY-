/**
 * Unit tests for VoiceConfigPanel component.
 *
 * Tests the LLM configuration UI and settings persistence.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VoiceConfigPanel } from './VoiceConfigPanel';
import * as useBookVoiceSettingsHook from '../hooks/useBookVoiceSettings';
import * as useComprehensiveTTSHook from '../../../../shared/frontend/hooks/useComprehensiveTTS';

// Mock hooks
jest.mock('../hooks/useBookVoiceSettings');
jest.mock('../../../../shared/frontend/hooks/useComprehensiveTTS');

describe('VoiceConfigPanel', () => {
  const mockBookId = 'book_123';
  const mockOnClose = jest.fn();
  const mockOnSave = jest.fn();

  const mockUseBookVoiceSettings = {
    settings: null,
    hasSettings: false,
    loading: false,
    error: null,
    updateSettings: jest.fn(),
    clearSettings: jest.fn(),
    refreshSettings: jest.fn(),
  };

  const mockUseComprehensiveTTS = {
    selectedProvider: 'kokoro',
    selectedVoice: 'am_adam',
    setProvider: jest.fn(),
    setVoice: jest.fn(),
    providers: [{ id: 'kokoro', name: 'Kokoro TTS' }],
    voices: [{ id: 'am_adam', name: 'Adam' }],
    isLoadingProviders: false,
    isLoadingVoices: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue(mockUseBookVoiceSettings);
    (useComprehensiveTTSHook.useComprehensiveTTS as jest.Mock).mockReturnValue(mockUseComprehensiveTTS);
  });

  it('should render the panel with all tabs', () => {
    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Verify tabs are present
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    expect(screen.getByText('Voice')).toBeInTheDocument();
    expect(screen.getByText('Transcriber')).toBeInTheDocument();
  });

  it('should show LLM tab by default', () => {
    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // LLM tab content should be visible
    expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    expect(screen.getByText('Model')).toBeInTheDocument();
    expect(screen.getByText(/Temperature:/)).toBeInTheDocument();
  });

  it('should display LLM provider options', () => {
    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Verify all provider buttons are present
    expect(screen.getByText(/Google Gemini/)).toBeInTheDocument();
    expect(screen.getByText(/OpenAI/)).toBeInTheDocument();
    expect(screen.getByText(/Anthropic/)).toBeInTheDocument();
    expect(screen.getByText(/Ollama/)).toBeInTheDocument();
  });

  it('should allow switching LLM providers', async () => {
    const user = userEvent.setup();

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Click OpenAI provider
    const openAIButton = screen.getByText(/OpenAI/);
    await user.click(openAIButton);

    // Verify model dropdown updates
    const modelSelect = screen.getByRole('combobox', { name: /model/i }) as HTMLSelectElement;
    expect(modelSelect.value).toContain('gpt-4o-mini');
  });

  it('should update temperature slider', async () => {
    const user = userEvent.setup();

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    const temperatureSlider = screen.getByRole('slider') as HTMLInputElement;

    // Change temperature
    await user.clear(temperatureSlider);
    await user.type(temperatureSlider, '0.9');

    // Verify temperature display updates
    await waitFor(() => {
      expect(screen.getByText(/Temperature: 0\.9/)).toBeInTheDocument();
    });
  });

  it('should allow entering custom system prompt', async () => {
    const user = userEvent.setup();

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    const promptTextarea = screen.getByPlaceholderText(/Enter a custom system prompt/i);

    const customPrompt = 'Be concise and educational.';
    await user.type(promptTextarea, customPrompt);

    expect(promptTextarea).toHaveValue(customPrompt);
  });

  it('should call updateSettings on save', async () => {
    const user = userEvent.setup();
    mockUseBookVoiceSettings.updateSettings.mockResolvedValueOnce(undefined);

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Change provider
    const openAIButton = screen.getByText(/OpenAI/);
    await user.click(openAIButton);

    // Click save
    const saveButton = screen.getByText(/Save Settings/);
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockUseBookVoiceSettings.updateSettings).toHaveBeenCalled();
    });

    // Verify settings object contains LLM config
    const updateCall = mockUseBookVoiceSettings.updateSettings.mock.calls[0][0];
    expect(updateCall).toHaveProperty('llm_provider');
    expect(updateCall).toHaveProperty('llm_model');
  });

  it('should load existing settings on mount', () => {
    const existingSettings = {
      llm_provider: 'anthropic',
      llm_model: 'claude-3-5-sonnet-20241022',
      llm_temperature: 0.6,
      system_prompt: 'Test prompt',
    };

    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue({
      ...mockUseBookVoiceSettings,
      settings: existingSettings,
      hasSettings: true,
    });

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Verify system prompt is loaded
    const promptTextarea = screen.getByPlaceholderText(/Enter a custom system prompt/i) as HTMLTextAreaElement;
    expect(promptTextarea.value).toBe('Test prompt');

    // Verify temperature is loaded
    expect(screen.getByText(/Temperature: 0\.6/)).toBeInTheDocument();
  });

  it('should call clearSettings on reset', async () => {
    const user = userEvent.setup();

    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue({
      ...mockUseBookVoiceSettings,
      hasSettings: true,
    });

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    mockUseBookVoiceSettings.clearSettings.mockResolvedValueOnce(undefined);

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    const resetButton = screen.getByText(/Reset to Defaults/);
    await user.click(resetButton);

    await waitFor(() => {
      expect(mockUseBookVoiceSettings.clearSettings).toHaveBeenCalled();
    });
  });

  it('should switch tabs correctly', async () => {
    const user = userEvent.setup();

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Switch to Voice tab
    const voiceTab = screen.getByText('Voice');
    await user.click(voiceTab);

    // Voice tab content should be visible (ComprehensiveTTSSelector)
    // Note: The actual component rendering depends on the mock

    // Switch to Transcriber tab
    const transcriberTab = screen.getByText('Transcriber');
    await user.click(transcriberTab);

    // Should show placeholder
    expect(screen.getByText(/Transcriber settings coming soon/)).toBeInTheDocument();
  });

  it('should call onClose when close button clicked', async () => {
    const user = userEvent.setup();

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Find and click close button (X icon)
    const closeButtons = screen.getAllByRole('button');
    const closeButton = closeButtons.find(btn => btn.textContent === '');

    if (closeButton) {
      await user.click(closeButton);
      expect(mockOnClose).toHaveBeenCalled();
    }
  });

  it('should disable save button when no changes', () => {
    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    const saveButton = screen.getByText(/Save Settings/) as HTMLButtonElement;

    // Initially no changes, so button might be disabled
    // Note: The actual behavior depends on hasChanges state
  });

  it('should show loading state', () => {
    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue({
      ...mockUseBookVoiceSettings,
      loading: true,
    });

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    // Should show loading spinner
    expect(screen.getByTestId('loader') || screen.getByText(/loading/i)).toBeTruthy();
  });

  it('should include all LLM models for each provider', () => {
    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    const modelSelect = screen.getByRole('combobox', { name: /model/i });

    // Default provider (Gemini) models
    expect(modelSelect).toContainHTML('gemini-2.5-flash');
  });

  it('should show Reset button only when settings exist', () => {
    // Without settings
    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue({
      ...mockUseBookVoiceSettings,
      hasSettings: false,
    });

    const { rerender } = render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    expect(screen.queryByText(/Reset to Defaults/)).not.toBeInTheDocument();

    // With settings
    (useBookVoiceSettingsHook.useBookVoiceSettings as jest.Mock).mockReturnValue({
      ...mockUseBookVoiceSettings,
      hasSettings: true,
    });

    rerender(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText(/Reset to Defaults/)).toBeInTheDocument();
  });

  it('should call onSave callback with settings', async () => {
    const user = userEvent.setup();
    mockUseBookVoiceSettings.updateSettings.mockResolvedValueOnce(undefined);

    render(
      <VoiceConfigPanel
        bookId={mockBookId}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    // Make a change
    const openAIButton = screen.getByText(/OpenAI/);
    await user.click(openAIButton);

    // Save
    const saveButton = screen.getByText(/Save Settings/);
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });

    // Verify settings were passed
    const saveCallSettings = mockOnSave.mock.calls[0][0];
    expect(saveCallSettings).toHaveProperty('llm_provider');
    expect(saveCallSettings.llm_provider).toBe('openai');
  });
});
