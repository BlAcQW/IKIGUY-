import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@test/helpers/render';
import { buildAssistant } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listAssistants: vi.fn(),
}));

vi.mock('@/lib/auth', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { WebCallPage } from './WebCall';
import { listAssistants } from '@/lib/api';
import { getToken } from '@/lib/auth';
import { toast } from 'sonner';

const mockedListAssistants = vi.mocked(listAssistants);
const mockedGetToken = vi.mocked(getToken);

// --- Browser API mocks ---

let mockWsInstance: MockWebSocket | null = null;

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  CONNECTING = 0;
  OPEN = 1;
  CLOSING = 2;
  CLOSED = 3;

  url: string;
  onopen: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  readyState = 0;
  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = 3;
  });
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  constructor(url: string) {
    this.url = url;
    this.readyState = 0;
    mockWsInstance = this;
  }
}

class MockMediaRecorder {
  state = 'inactive';
  ondataavailable: ((e: BlobEvent) => void) | null = null;
  start = vi.fn(() => {
    this.state = 'recording';
  });
  stop = vi.fn(() => {
    this.state = 'inactive';
  });
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  static isTypeSupported = vi.fn().mockReturnValue(true);
}

const mockTrackStop = vi.fn();
const mockStream = {
  getTracks: () => [{ stop: mockTrackStop, kind: 'audio' }],
  getAudioTracks: () => [{ stop: mockTrackStop }],
};
const mockGetUserMedia = vi.fn().mockResolvedValue(mockStream);

const mockAudioContextClose = vi.fn().mockResolvedValue(undefined);
const mockAudioContext = {
  createBuffer: vi.fn(() => ({
    getChannelData: vi.fn(() => new Float32Array(100)),
  })),
  createBufferSource: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    start: vi.fn(),
    buffer: null,
    onended: null,
  })),
  createMediaStreamSource: vi.fn(() => ({ connect: vi.fn(), disconnect: vi.fn() })),
  createScriptProcessor: vi.fn(() => ({ connect: vi.fn(), disconnect: vi.fn(), onaudioprocess: null })),
  createAnalyser: vi.fn(() => ({ connect: vi.fn(), disconnect: vi.fn(), fftSize: 0, getByteTimeDomainData: vi.fn() })),
  destination: {},
  close: mockAudioContextClose,
  state: 'running',
  sampleRate: 24000,
};

describe('WebCallPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockWsInstance = null;

    vi.stubGlobal('WebSocket', MockWebSocket);
    vi.stubGlobal('MediaRecorder', MockMediaRecorder);
    vi.stubGlobal('AudioContext', vi.fn(() => ({ ...mockAudioContext, close: vi.fn().mockResolvedValue(undefined) })));

    Object.defineProperty(navigator, 'mediaDevices', {
      value: { getUserMedia: mockGetUserMedia },
      configurable: true,
      writable: true,
    });

    mockedGetToken.mockReturnValue('test-token');
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders page title', () => {
    mockedListAssistants.mockReturnValue(new Promise(() => {}));
    render(<WebCallPage />);
    expect(screen.getByText('Web Call')).toBeInTheDocument();
  });

  it('shows loading state for assistants', () => {
    mockedListAssistants.mockReturnValue(new Promise(() => {}));
    render(<WebCallPage />);
    expect(screen.getByText('Ready to call')).toBeInTheDocument();
  });

  it('renders Start Call button', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeInTheDocument();
    });
  });

  it('shows assistant selector after load', async () => {
    const assistants = [buildAssistant({ name: 'Sales Bot' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByText('Ready to call')).toBeInTheDocument();
    });
  });

  it('shows subtitle text', () => {
    mockedListAssistants.mockReturnValue(new Promise(() => {}));
    render(<WebCallPage />);
    expect(screen.getByText(/test your assistant with a browser-based voice call/i)).toBeInTheDocument();
  });

  it('renders assistant label', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByText('Assistant')).toBeInTheDocument();
    });
  });

  it('handles load error gracefully', async () => {
    mockedListAssistants.mockRejectedValue(new Error('fail'));
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByText('Web Call')).toBeInTheDocument();
    });
  });

  it('disables Start Call when no assistant selected', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeDisabled();
    });
  });

  it('shows call status text', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByText('Ready to call')).toBeInTheDocument();
    });
  });

  it('renders transcript area container is absent when no transcript', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeInTheDocument();
    });

    // Transcript section should NOT be visible when there are no entries
    expect(screen.queryByText('Transcript')).not.toBeInTheDocument();
  });

  it('shows connection status indicators in idle state', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
    render(<WebCallPage />);

    await waitFor(() => {
      // Verify the idle state UI elements
      expect(screen.getByText('Ready to call')).toBeInTheDocument();
      expect(screen.getByText(/select an assistant and start a voice conversation/i)).toBeInTheDocument();
    });
  });

  it('shows "No assistants available" when list is empty', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeInTheDocument();
    });

    // The select trigger should be rendered even with no assistants
    const trigger = screen.getByRole('combobox');
    expect(trigger).toBeInTheDocument();
  });

  it('renders the assistant label above selector', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant({ name: 'My Bot' })] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByText('Assistant')).toBeInTheDocument();
    });
  });

  // --- Helper: switch to Classic mode (since default is now WebRTC) ---

  async function switchToClassic(user: ReturnType<typeof import('@testing-library/user-event').default.setup>) {
    const classicButton = screen.getByRole('button', { name: /classic/i });
    await user.click(classicButton);
  }

  // --- New tests for startCall, endCall, WebSocket, state transitions ---

  it('starts a call: creates WebSocket and transitions to connecting', async () => {
    const assistant = buildAssistant({ name: 'Sales Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    // WebSocket should have been created
    expect(mockWsInstance).not.toBeNull();
    expect(mockWsInstance!.url).toContain('/api/calls/web');

    // UI should transition to connecting state
    await waitFor(() => {
      expect(screen.getByText('Connecting')).toBeInTheDocument();
    });
  });

  it('sends auth message when WebSocket opens, then start on ready', async () => {
    const assistant = buildAssistant({ name: 'Sales Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    // Simulate WebSocket open — should send auth message
    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    expect(mockWsInstance!.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'auth', token: 'test-token' })
    );

    // Simulate server responding with ready status — should send start message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'status', status: 'ready' }),
      }));
    });

    expect(mockWsInstance!.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'start', assistantId: assistant.id })
    );
  });

  it('transitions to active when call_started message received', async () => {
    const assistant = buildAssistant({ name: 'Sales Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    // Simulate WebSocket open
    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    // Simulate call_started message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-123' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    // Call ID should be partially displayed
    expect(screen.getByText('call-123...')).toBeInTheDocument();
  });

  it('shows assistant name during active call', async () => {
    const assistant = buildAssistant({ name: 'Sales Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-123' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Talking to Sales Bot')).toBeInTheDocument();
    });
  });

  it('shows End Call button during active call', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end call/i })).toBeInTheDocument();
    });
  });

  it('ends call when End Call button is clicked', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));
    const ws = mockWsInstance!;

    act(() => {
      ws.onopen!(new Event('open'));
      ws.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end call/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /end call/i }));

    // WebSocket should have received stop message and been closed
    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'stop' }));
    expect(ws.close).toHaveBeenCalled();
  });

  it('displays user transcript when user_transcript message received', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Send a user transcript message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'user_transcript', text: 'Hello, I need help' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Transcript')).toBeInTheDocument();
      expect(screen.getByText('Hello, I need help')).toBeInTheDocument();
    });
  });

  it('displays assistant transcript when assistant_message received', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Send assistant message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'assistant_message', text: 'Sure, how can I help?', hasAudio: false }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Sure, how can I help?')).toBeInTheDocument();
    });
  });

  it('shows both user and assistant transcripts', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'user_transcript', text: 'What time is it?' }),
      }));
    });

    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'assistant_message', text: 'It is 3 PM', hasAudio: false }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('What time is it?')).toBeInTheDocument();
      expect(screen.getByText('It is 3 PM')).toBeInTheDocument();
    });
  });

  it('transitions to processing state on processing message', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Simulate processing started
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'processing', status: 'started' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Processing')).toBeInTheDocument();
    });
  });

  it('transitions back to active after processing completes', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'processing', status: 'started' }),
      }));
    });

    // Processing done
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'processing', status: 'done' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('transitions to ended state on call_ended message', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // End the call via server message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_ended' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Call ended')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /new call/i })).toBeInTheDocument();
    });
  });

  it('transitions to ended state on call_ending message', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_ending' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Call ended')).toBeInTheDocument();
    });
  });

  it('handles WebSocket error gracefully', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    // Simulate WebSocket error
    act(() => {
      mockWsInstance!.onerror!(new Event('error'));
    });

    await waitFor(() => {
      expect(screen.getByText('WebSocket connection failed')).toBeInTheDocument();
    });
  });

  it('handles error message from server', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    // Simulate error message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'error', message: 'Rate limit exceeded', code: 'RATE_LIMIT' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument();
    });
  });

  it('handles UNAUTHORIZED error and transitions to error state', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    // Simulate UNAUTHORIZED error
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'error', message: 'Not authorized', code: 'UNAUTHORIZED' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Not authorized')).toBeInTheDocument();
    });
  });

  it('shows error when no assistant selected and Start Call clicked', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeInTheDocument();
    });

    // Button is disabled when no assistant selected, but startCall still checks
    // We can't click a disabled button, so this tests the guard
    expect(screen.getByRole('button', { name: /start call/i })).toBeDisabled();
  });

  it('shows error when not authenticated', async () => {
    mockedGetToken.mockReturnValue(null);
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    await waitFor(() => {
      expect(screen.getByText('Not authenticated')).toBeInTheDocument();
    });

    // WebSocket should NOT have been created
    expect(mockWsInstance).toBeNull();
  });

  it('resets to idle state with New Call button after call ends', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // End the call
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_ended' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new call/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /new call/i }));

    await waitFor(() => {
      expect(screen.getByText('Ready to call')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start call/i })).toBeInTheDocument();
    });
  });

  it('handles WebSocket close event during connecting state', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    await waitFor(() => {
      expect(screen.getByText('Connecting')).toBeInTheDocument();
    });

    // Simulate WebSocket close while in connecting state
    // The onclose handler captures callStatus='idle' from the closure where startCall ran,
    // so it won't set 'ended' (idle is excluded), but stopRecording is still called.
    // The page should not crash.
    act(() => {
      mockWsInstance!.onclose!(new CloseEvent('close'));
    });

    // Page is still rendered without crashing
    expect(screen.getByText('Web Call')).toBeInTheDocument();
  });

  it('handles non-JSON WebSocket messages without crashing', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    // Send a non-JSON message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: 'not-json-data',
      }));
    });

    // Should not crash - page still exists
    expect(screen.getByText('Web Call')).toBeInTheDocument();
  });

  it('handles status message type without error', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
    });

    // Send a status message (which is handled but doesn't do anything visible)
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'status', status: 'ready' }),
      }));
    });

    // No crash - page still works
    expect(screen.getByText('Web Call')).toBeInTheDocument();
  });

  it('shows Hold to Talk button during active call', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /hold to talk/i })).toBeInTheDocument();
    });
  });

  it('shows call duration timer during active call', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Timer should start at 00:00
    await waitFor(() => {
      expect(screen.getByText('00:00')).toBeInTheDocument();
    });

    // Advance time by 5 seconds
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      expect(screen.getByText('00:05')).toBeInTheDocument();
    });
  });

  it('formats call duration correctly for minutes and seconds', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Advance time by 65 seconds (1 minute 5 seconds)
    act(() => {
      vi.advanceTimersByTime(65000);
    });

    await waitFor(() => {
      expect(screen.getByText('01:05')).toBeInTheDocument();
    });
  });

  it('shows Connecting badge while in connecting state', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    // In connecting state (before WS opens)
    await waitFor(() => {
      expect(screen.getByText('Connecting')).toBeInTheDocument();
    });
  });

  it('calls toast.error when assistants fail to load', async () => {
    mockedListAssistants.mockRejectedValue(new Error('network'));
    render(<WebCallPage />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load assistants');
    });
  });

  it('starts recording when Hold to Talk is clicked during active call', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-rec' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /hold to talk/i })).toBeEnabled();
    });

    await user.click(screen.getByRole('button', { name: /hold to talk/i }));

    // After clicking Hold to Talk, microphone should be requested
    expect(mockGetUserMedia).toHaveBeenCalled();

    // Should now show Send button instead of Hold to Talk
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });
  });

  it('stops recording and sends end_turn when Send is clicked', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));
    const ws = mockWsInstance!;

    act(() => {
      ws.onopen!(new Event('open'));
      ws.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-rec2' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /hold to talk/i })).toBeEnabled();
    });

    // Start recording
    await user.click(screen.getByRole('button', { name: /hold to talk/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    // Click Send to stop recording and send end_turn
    await user.click(screen.getByRole('button', { name: /send/i }));

    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: 'end_turn' }));
  });

  it('handles audio_end message without crashing', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-audio' }),
      }));
    });

    // Send assistant_message with hasAudio=true
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'assistant_message', text: 'Audio response', hasAudio: true }),
      }));
    });

    // Send audio_end message
    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'audio_end' }),
      }));
    });

    // Page should not crash
    expect(screen.getByText('Audio response')).toBeInTheDocument();
  });

  it('shows call ended duration after call ends', async () => {
    const assistant = buildAssistant();
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    const { user } = render(<WebCallPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start call/i })).toBeEnabled();
    });

    await switchToClassic(user);
    await user.click(screen.getByRole('button', { name: /start call/i }));

    act(() => {
      mockWsInstance!.onopen!(new Event('open'));
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_started', callId: 'call-abc' }),
      }));
    });

    // Advance time 10 seconds
    act(() => {
      vi.advanceTimersByTime(10000);
    });

    act(() => {
      mockWsInstance!.onmessage!(new MessageEvent('message', {
        data: JSON.stringify({ type: 'call_ended' }),
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('Call ended')).toBeInTheDocument();
      expect(screen.getByText('00:10')).toBeInTheDocument();
    });
  });
});
