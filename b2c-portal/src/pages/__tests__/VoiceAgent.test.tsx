import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import VoiceAgent from '../VoiceAgent';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Mock the environment variable
const mockEnv = {
  VITE_CORE_API_URL: CORE_API_URL
};

// Mock fetch
global.fetch = vi.fn();

// Mock AudioContext
global.AudioContext = vi.fn().mockImplementation(() => ({
  createMediaStreamSource: vi.fn(),
  createScriptProcessor: vi.fn(),
  destination: {},
  sampleRate: 44100,
  createBuffer: vi.fn(),
  createBufferSource: vi.fn(),
}));

// Mock navigator.mediaDevices
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    })
  },
  writable: true
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('VoiceAgent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      json: () => Promise.resolve({
        stt: { openai: ['gpt-4o-transcribe'], google: ['google-stt'] },
        tts: { coqui: ['xtts'], elevenlabs: ['eleven_multilingual_v1'] },
        llm: ['gpt-4o-mini', 'llama-3-8b'],
        languages: ['English', 'Twi'],
        countries: ['Ghana', 'Kenya']
      })
    });
  });

  it('renders the Kasa AI interface', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for main interface elements - use getAllByText to handle multiple instances
    expect(screen.getAllByText('Kasa AI')).toHaveLength(2); // One in sidebar, one in header
    expect(screen.getAllByText('Assistants')).toHaveLength(2); // One in sidebar, one in panel header
    expect(screen.getAllByText('New Assistant')).toHaveLength(2); // One in header, one in list
    expect(screen.getByText('+ Create Assistant')).toBeInTheDocument();
  });

  it('displays configuration tabs', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for configuration tabs - use getAllByText for elements that might appear multiple times
    expect(screen.getByText('Model')).toBeInTheDocument();
    expect(screen.getAllByText('Voice')).toHaveLength(2); // Tab and label
    expect(screen.getByText('Transcriber')).toBeInTheDocument();
    expect(screen.getAllByText('Tools')).toHaveLength(2); // Tab and sidebar item
    expect(screen.getByText('Analysis')).toBeInTheDocument();
    expect(screen.getByText('Advanced')).toBeInTheDocument();
    expect(screen.getByText('Widget')).toBeInTheDocument();
  });

  it('shows cost and latency metrics', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for metrics
    expect(screen.getByText('~$0.14 /min')).toBeInTheDocument();
    expect(screen.getByText('~1200 ms')).toBeInTheDocument();
  });

  it('displays assistant list', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for some assistant names
    expect(screen.getByText('Prime Twi')).toBeInTheDocument();
    expect(screen.getByText('Voice Engine')).toBeInTheDocument();
    expect(screen.getByText('Kofi Logistics')).toBeInTheDocument();
  });

  it('shows navigation sections', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for navigation sections
    expect(screen.getByText('BUILD')).toBeInTheDocument();
    expect(screen.getByText('OBSERVE')).toBeInTheDocument();
  });

  it('displays credits section', () => {
    renderWithRouter(<VoiceAgent />);
    
    // Check for credits
    expect(screen.getByText('PAYG')).toBeInTheDocument();
    expect(screen.getByText('29.52 Credits')).toBeInTheDocument();
    expect(screen.getByText('↑ Buy Credits')).toBeInTheDocument();
  });
});
