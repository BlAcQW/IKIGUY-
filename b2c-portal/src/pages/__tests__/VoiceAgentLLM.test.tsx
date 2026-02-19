import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import VoiceAgent from '../VoiceAgent';
import { setupVoiceAgentMocks, cleanupVoiceAgentMocks } from '../../test/mocks/voice-agent-mocks';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('VoiceAgent LLM Model Tab', () => {
  beforeEach(() => {
    setupVoiceAgentMocks();
  });

  afterEach(() => {
    cleanupVoiceAgentMocks();
    vi.clearAllMocks();
  });

  it('displays LLM providers and models in the model tab', async () => {
    render(
      <BrowserRouter>
        <VoiceAgent />
      </BrowserRouter>
    );

    // Wait for the data to be loaded and check if the component renders
    await waitFor(() => {
      expect(screen.getByText('Kasa AI')).toBeInTheDocument();
    });

    // Look for the model tab and click it
    const modelTab = screen.getByText('Model');
    expect(modelTab).toBeInTheDocument();
    modelTab.click();

    // Check that the provider dropdown shows the correct options
    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('Google AI')).toBeInTheDocument();
    });

    // Check that the model dropdown shows the correct options for the selected provider
    await waitFor(() => {
      expect(screen.getByText('GPT-4o')).toBeInTheDocument();
      expect(screen.getByText('GPT-4o Mini')).toBeInTheDocument();
    });
  });

  it('updates model options when provider changes', async () => {
    render(
      <BrowserRouter>
        <VoiceAgent />
      </BrowserRouter>
    );

    // Wait for the data to be loaded and check if the component renders
    await waitFor(() => {
      expect(screen.getByText('Kasa AI')).toBeInTheDocument();
    });

    // Look for the model tab and click it
    const modelTab = screen.getByText('Model');
    expect(modelTab).toBeInTheDocument();
    modelTab.click();

    // Select a different provider
    const providerSelect = screen.getByDisplayValue('openai');
    providerSelect.value = 'anthropic';
    providerSelect.dispatchEvent(new Event('change'));

    // Check that the model options update
    await waitFor(() => {
      expect(screen.getByText('Claude 3.5 Sonnet')).toBeInTheDocument();
    });
  });

  it('shows debug information correctly', async () => {
    render(
      <BrowserRouter>
        <VoiceAgent />
      </BrowserRouter>
    );

    // Wait for the data to be loaded and check if the component renders
    await waitFor(() => {
      expect(screen.getByText('Kasa AI')).toBeInTheDocument();
    });

    // Look for the model tab and click it
    const modelTab = screen.getByText('Model');
    expect(modelTab).toBeInTheDocument();
    modelTab.click();

    // Check that debug information is shown
    await waitFor(() => {
      expect(screen.getByText(/Debug: \d+ providers available/)).toBeInTheDocument();
      expect(screen.getByText(/Debug: \d+ models available/)).toBeInTheDocument();
    });
  });
});
