import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';

// Mock the API module so we can control what getOrgSettings returns
vi.mock('@/lib/api', () => ({
  getOrgSettings: vi.fn(),
  updateOrgSettings: vi.fn(),
}));

import { getOrgSettings } from '@/lib/api';
import { SettingsPage } from './settings';

const mockSettings = {
  providerCredentials: {},
  pipelineDefaults: {
    silenceTimeout: 30,
    responseDelay: 0.5,
    interruptionThreshold: 0.5,
    transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
    voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
    llm: { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
  },
  callBehavior: {
    maxCallDuration: 3600,
    sessionIdleTimeout: 120,
    recordingEnabled: false,
    hipaaCompliant: false,
    retrySettings: { maxRetries: 0, retryDelay: 30 },
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  (getOrgSettings as ReturnType<typeof vi.fn>).mockResolvedValue({
    success: true,
    data: mockSettings,
  });
});

describe('SettingsPage', () => {
  it('renders page title and loading state', () => {
    render(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Loading settings...')).toBeInTheDocument();
  });

  it('renders API Keys card with link to /api-keys after loading', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument();
    });
    expect(screen.getByRole('link', { name: /manage/i })).toHaveAttribute('href', '/api-keys');
  });

  it('renders Provider Credentials card after loading', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('Provider Credentials')).toBeInTheDocument();
    });
  });

  it('renders Pipeline Defaults card after loading', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('Pipeline Defaults')).toBeInTheDocument();
    });
  });

  it('renders Call Behavior card after loading', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('Call Behavior')).toBeInTheDocument();
    });
  });
});
