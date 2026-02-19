import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AssistantConfiguration } from './AssistantConfiguration';
import { Assistant } from './AssistantList';

describe('AssistantConfiguration', () => {
  const mockAssistant: Assistant = {
    id: 'test-123',
    name: 'Test Assistant',
    description: 'Test Description',
    status: 'active',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    user_id: 'user-123',
    // Model config
    llm_provider: 'openai',
    llm_model: 'gpt-4o',
    system_prompt: 'You are a helpful assistant',
    first_message: 'Hello, how can I help?',
    // Voice config
    tts_provider: 'openai',
    tts_voice: 'alloy',
    language: 'en',
    country: 'US',
    // STT config
    stt_provider: 'openai',
    stt_model: 'whisper-large-v3',
    // Voice parameters
    stability: 0.5,
    clarity_similarity: 0.5,
    speed: 1.0,
    style_exaggeration: 0.5,
    optimize_streaming_latency: 1
  };

  const mockOnConfigurationChange = vi.fn();
  const mockOnPublish = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(
      <AssistantConfiguration
        assistant={mockAssistant}
        onConfigurationChange={mockOnConfigurationChange}
        onPublish={mockOnPublish}
      />
    );
    
    expect(screen.getByText('Language Model Configuration')).toBeInTheDocument();
  });

  it('should display message when no assistant is selected', () => {
    render(
      <AssistantConfiguration
        assistant={null}
        onConfigurationChange={mockOnConfigurationChange}
        onPublish={mockOnPublish}
      />
    );
    
    expect(screen.getByText('Select an assistant to configure')).toBeInTheDocument();
  });

  describe('Dynamic Model Selection', () => {
    it('should update LLM models when provider changes', async () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      // Find provider select - it's the first select element
      const selects = container.querySelectorAll('select');
      const providerSelect = selects[0] as HTMLSelectElement;
      expect(providerSelect).toBeTruthy();
      expect(providerSelect.value).toBe('openai');

      // Change to Anthropic
      fireEvent.change(providerSelect, { target: { value: 'anthropic' } });

      await waitFor(() => {
        expect(mockOnConfigurationChange).toHaveBeenCalledWith({
          llm_provider: 'anthropic',
          llm_model: 'claude-3-5-sonnet' // First model in anthropic list
        });
      });
    });

    it('should show correct models for OpenAI provider', () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      const modelSelect = container.querySelectorAll('select')[1] as HTMLSelectElement;
      const options = Array.from(modelSelect.options);
      
      expect(options.map(o => o.value)).toContain('gpt-4o');
      expect(options.map(o => o.value)).toContain('gpt-4o-mini');
      expect(options.map(o => o.value)).toContain('gpt-4-turbo');
      expect(options.map(o => o.value)).toContain('gpt-3.5-turbo');
    });

    it('should show correct models for Anthropic provider', () => {
      const anthropicAssistant = { ...mockAssistant, llm_provider: 'anthropic', llm_model: 'claude-3-5-sonnet' };
      
      const { container } = render(
        <AssistantConfiguration
          assistant={anthropicAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      const modelSelect = container.querySelectorAll('select')[1] as HTMLSelectElement;
      const options = Array.from(modelSelect.options);
      
      expect(options.map(o => o.value)).toContain('claude-3-5-sonnet');
      expect(options.map(o => o.value)).toContain('claude-3-opus');
      expect(options.map(o => o.value)).toContain('claude-3-sonnet');
      expect(options.map(o => o.value)).toContain('claude-3-haiku');
    });
  });

  describe('Dynamic Voice Selection', () => {
    it('should update TTS voices when provider changes', async () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      // Switch to Voice tab
      const voiceTab = screen.getByText('Voice');
      fireEvent.click(voiceTab);

      await waitFor(() => {
        expect(screen.getByText('Voice Configuration')).toBeInTheDocument();
      });

      // Find TTS provider select - it's the first select in voice tab
      const selects = container.querySelectorAll('select');
      const ttsProviderSelect = selects[0] as HTMLSelectElement;
      expect(ttsProviderSelect).toBeTruthy();
      
      // Change to ElevenLabs
      fireEvent.change(ttsProviderSelect, { target: { value: 'elevenlabs' } });

      await waitFor(() => {
        expect(mockOnConfigurationChange).toHaveBeenCalledWith({
          tts_provider: 'elevenlabs',
          tts_voice: 'adam' // First voice in elevenlabs list
        });
      });
    });

    it('should show correct voices for Meta MMS provider', async () => {
      const metaAssistant = { ...mockAssistant, tts_provider: 'meta_mms', tts_voice: 'mms-tts-aka' };
      
      const { container } = render(
        <AssistantConfiguration
          assistant={metaAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      // Switch to Voice tab
      const voiceTab = screen.getByText('Voice');
      fireEvent.click(voiceTab);

      await waitFor(() => {
        expect(screen.getByText('Voice Configuration')).toBeInTheDocument();
      });

      const voiceSelect = container.querySelectorAll('select')[1] as HTMLSelectElement;
      const options = Array.from(voiceSelect.options);
      
      expect(options.map(o => o.value)).toContain('mms-tts-aka');
      expect(options.map(o => o.value)).toContain('mms-tts-ewe');
      expect(options.map(o => o.value)).toContain('mms-tts-gaa');
      expect(options.map(o => o.value)).toContain('mms-tts-yor');
    });
  });

  describe('Dynamic STT Selection', () => {
    it('should update STT model when provider changes', async () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      // Switch to Transcriber tab
      const transcriberTab = screen.getByText('Transcriber');
      fireEvent.click(transcriberTab);

      await waitFor(() => {
        expect(screen.getByText('Speech Recognition Configuration')).toBeInTheDocument();
      });

      // Find STT provider select - it's the first select in transcriber tab
      const selects = container.querySelectorAll('select');
      const sttProviderSelect = selects[0] as HTMLSelectElement;
      expect(sttProviderSelect).toBeTruthy();
      
      // Change to Deepgram
      fireEvent.change(sttProviderSelect, { target: { value: 'deepgram' } });

      await waitFor(() => {
        expect(mockOnConfigurationChange).toHaveBeenCalledWith({
          stt_provider: 'deepgram'
        });
      });
    });
  });

  describe('Publishing Changes', () => {
    it('should call onPublish when publish button is clicked', () => {
      render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      const publishButton = screen.getByText('Publish Changes');
      fireEvent.click(publishButton);

      expect(mockOnPublish).toHaveBeenCalledTimes(1);
    });

    it('should display last updated time', () => {
      render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  describe('Form Inputs', () => {
    it('should update system prompt', () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      const textareas = container.querySelectorAll('textarea');
      const systemPromptTextarea = textareas[0] as HTMLTextAreaElement;
      expect(systemPromptTextarea).toBeTruthy();
      expect(systemPromptTextarea.value).toBe('You are a helpful assistant');
      
      fireEvent.change(systemPromptTextarea, { target: { value: 'New system prompt' } });

      expect(mockOnConfigurationChange).toHaveBeenCalledWith({
        system_prompt: 'New system prompt'
      });
    });

    it('should update first message', () => {
      const { container } = render(
        <AssistantConfiguration
          assistant={mockAssistant}
          onConfigurationChange={mockOnConfigurationChange}
          onPublish={mockOnPublish}
        />
      );

      const inputs = container.querySelectorAll('input[type="text"]');
      const firstMessageInput = inputs[0] as HTMLInputElement;
      expect(firstMessageInput).toBeTruthy();
      expect(firstMessageInput.value).toBe('Hello, how can I help?');
      
      fireEvent.change(firstMessageInput, { target: { value: 'Welcome!' } });

      expect(mockOnConfigurationChange).toHaveBeenCalledWith({
        first_message: 'Welcome!'
      });
    });
  });
});