import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CloneVoiceAgentModal } from '../CloneVoiceAgentModal';
import { Assistant } from '../AssistantList';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock fetch
global.fetch = vi.fn();

const mockSourceAgent: Assistant = {
  id: 'test-agent-1',
  name: 'Test Voice Agent',
  description: 'A test voice agent for cloning',
  user_id: 'user-123',
  template_id: 'custom',
  status: 'published',
  llm_provider: 'openai',
  llm_model: 'gpt-4o-mini',
  first_message_mode: 'assistant_first',
  first_message: 'Hello! How can I help you?',
  system_prompt: 'You are a helpful assistant.',
  tts_provider: 'openai',
  tts_voice: 'alloy',
  language: 'en',
  country: 'US',
  stt_provider: 'openai',
  stt_model: 'whisper-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  metadata: {}
};

describe('CloneVoiceAgentModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onAgentCloned: vi.fn(),
    sourceAgent: mockSourceAgent,
    apiBaseUrl: 'https://api.test.com'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
  });

  it('renders clone modal when open with source agent', () => {
    render(<CloneVoiceAgentModal {...defaultProps} />);

    expect(screen.getAllByText('Clone Voice Agent')).toHaveLength(2); // Title and button
    expect(screen.getByText('Test Voice Agent')).toBeInTheDocument();
    expect(screen.getByText('A test voice agent for cloning')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Voice Agent (Copy)')).toBeInTheDocument();
  });

  it('does not render when not open', () => {
    render(<CloneVoiceAgentModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Clone Voice Agent')).not.toBeInTheDocument();
  });

  it('does not render when no source agent provided', () => {
    render(<CloneVoiceAgentModal {...defaultProps} sourceAgent={null} />);

    expect(screen.queryByText('Clone Voice Agent')).not.toBeInTheDocument();
  });

  it('allows user to modify clone form fields', () => {
    render(<CloneVoiceAgentModal {...defaultProps} />);

    const nameInput = screen.getByDisplayValue('Test Voice Agent (Copy)') as HTMLInputElement;
    const descriptionInput = screen.getByDisplayValue('A test voice agent for cloning') as HTMLTextAreaElement;
    const systemPromptInput = screen.getByDisplayValue('You are a helpful assistant.') as HTMLTextAreaElement;
    const firstMessageInput = screen.getByDisplayValue('Hello! How can I help you?') as HTMLInputElement;
    const urlInput = screen.getByPlaceholderText('https://example.com/webhook') as HTMLInputElement;

    // Update form fields
    fireEvent.change(nameInput, { target: { value: 'My Cloned Agent' } });
    fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });
    fireEvent.change(systemPromptInput, { target: { value: 'Updated system prompt' } });
    fireEvent.change(firstMessageInput, { target: { value: 'Updated greeting' } });
    fireEvent.change(urlInput, { target: { value: 'https://custom.webhook.com' } });

    expect(nameInput.value).toBe('My Cloned Agent');
    expect(descriptionInput.value).toBe('Updated description');
    expect(systemPromptInput.value).toBe('Updated system prompt');
    expect(firstMessageInput.value).toBe('Updated greeting');
    expect(urlInput.value).toBe('https://custom.webhook.com');
  });

  it('shows error toast when name is empty and user tries to clone', async () => {
    render(<CloneVoiceAgentModal {...defaultProps} />);

    const nameInput = screen.getByDisplayValue('Test Voice Agent (Copy)');
    const cloneButton = screen.getByRole('button', { name: /Clone Voice Agent/i });

    // Clear the name field
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(cloneButton);

    expect(mockToast).toHaveBeenCalledWith({
      title: "Name required",
      description: "Please enter a name for the cloned agent",
      variant: "destructive"
    });
  });

  it('successfully clones voice agent with API call', async () => {
    const mockClonedAgent = { ...mockSourceAgent, id: 'cloned-agent-id', name: 'Test Voice Agent (Copy)' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockClonedAgent
    });

    render(<CloneVoiceAgentModal {...defaultProps} />);

    const cloneButton = screen.getByRole('button', { name: /Clone Voice Agent/i });
    fireEvent.click(cloneButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/voice/assistants/',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"name":"Test Voice Agent (Copy)"')
        })
      );
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Voice agent cloned",
        description: "Test Voice Agent (Copy) has been created successfully from Test Voice Agent.",
      });
    });

    expect(defaultProps.onAgentCloned).toHaveBeenCalled();
  });

  it('handles API error during cloning', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error'
    });

    render(<CloneVoiceAgentModal {...defaultProps} />);

    const cloneButton = screen.getByRole('button', { name: /Clone Voice Agent/i });
    fireEvent.click(cloneButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: "Failed to clone voice agent",
        description: "Internal Server Error",
        variant: "destructive"
      });
    });
  });

  it('includes custom URL in cloned agent metadata when provided', async () => {
    const mockClonedAgent = { ...mockSourceAgent, id: 'cloned-agent-id' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockClonedAgent
    });

    render(<CloneVoiceAgentModal {...defaultProps} />);

    const urlInput = screen.getByPlaceholderText('https://example.com/webhook');
    const cloneButton = screen.getByRole('button', { name: /Clone Voice Agent/i });

    fireEvent.change(urlInput, { target: { value: 'https://my-webhook.com/clone' } });
    fireEvent.click(cloneButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/voice/assistants/',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"custom_url":"https://my-webhook.com/clone"')
        })
      );
    });
  });

  it('closes modal when cancel button is clicked', () => {
    render(<CloneVoiceAgentModal {...defaultProps} />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('closes modal when X button is clicked', () => {
    render(<CloneVoiceAgentModal {...defaultProps} />);

    const closeButton = screen.getByRole('button', { name: '' }); // X button doesn't have text
    fireEvent.click(closeButton);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('shows cloning state when cloning is in progress', async () => {
    // Mock a delayed response
    (global.fetch as any).mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ ...mockSourceAgent, id: 'cloned' })
      }), 1000))
    );

    render(<CloneVoiceAgentModal {...defaultProps} />);

    const cloneButton = screen.getByRole('button', { name: /Clone Voice Agent/i });
    fireEvent.click(cloneButton);

    // Should show loading state
    expect(screen.getByText('Cloning...')).toBeInTheDocument();
  });

  it('displays source agent information correctly', () => {
    const publishedAgent = { ...mockSourceAgent, status: 'published' as const };
    render(<CloneVoiceAgentModal {...defaultProps} sourceAgent={publishedAgent} />);

    expect(screen.getByText('Cloning from:')).toBeInTheDocument();
    expect(screen.getByText('Test Voice Agent')).toBeInTheDocument();
    expect(screen.getByText('published')).toBeInTheDocument();
    expect(screen.getByText('en')).toBeInTheDocument();
  });

  it('shows draft status correctly for draft agents', () => {
    const draftAgent = { ...mockSourceAgent, status: 'draft' as const };
    render(<CloneVoiceAgentModal {...defaultProps} sourceAgent={draftAgent} />);

    expect(screen.getByText('draft')).toBeInTheDocument();
  });
});