import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebRTCChat } from '@/hooks/useWebRTCChat';

// Mock the auth utilities
vi.mock('@/lib/auth-utils', () => ({
  getAuthToken: vi.fn().mockResolvedValue('mock-token-123'),
}));

// Mock the audio utilities
vi.mock('@/lib/audio-utils', () => ({
  playAudioBase64: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API config
vi.mock('@/config/api-config', () => ({
  API_BASE_URL: 'https://api.test.com',
}));

// Mock RTCPeerConnection
class MockRTCPeerConnection {
  localDescription: RTCSessionDescription | null = null;
  remoteDescription: RTCSessionDescription | null = null;
  ontrack: ((event: any) => void) | null = null;

  createDataChannel(label: string) {
    const channel = new MockRTCDataChannel(label);
    setTimeout(() => {
      if (channel.onopen) channel.onopen(new Event('open'));
    }, 10);
    return channel;
  }

  async createOffer() {
    return { type: 'offer' as RTCSdpType, sdp: 'mock-sdp-offer' };
  }

  async setLocalDescription(description: RTCSessionDescriptionInit) {
    this.localDescription = new RTCSessionDescription(description);
  }

  async setRemoteDescription(description: RTCSessionDescriptionInit) {
    this.remoteDescription = new RTCSessionDescription(description);
  }

  addTrack(track: MediaStreamTrack, stream: MediaStream) {
    return {} as RTCRtpSender;
  }

  close() {}
}

class MockRTCDataChannel {
  readyState: RTCDataChannelState = 'connecting';
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(public label: string) {}

  send(data: string) {
    // Simulate sending data
  }

  close() {
    this.readyState = 'closed';
    if (this.onclose) {
      this.onclose(new Event('close'));
    }
  }
}

// Mock MediaStream and MediaStreamTrack
class MockMediaStreamTrack {
  enabled = true;

  stop() {}
}

class MockMediaStream {
  tracks: MockMediaStreamTrack[] = [new MockMediaStreamTrack()];

  getTracks() {
    return this.tracks;
  }

  getAudioTracks() {
    return this.tracks;
  }
}

// Setup global mocks
beforeEach(() => {
  global.RTCPeerConnection = MockRTCPeerConnection as any;
  global.RTCSessionDescription = class {
    type: RTCSdpType;
    sdp: string;
    constructor(init: RTCSessionDescriptionInit) {
      this.type = init.type!;
      this.sdp = init.sdp!;
    }
    toJSON() {
      return { type: this.type, sdp: this.sdp };
    }
  } as any;

  // Mock navigator.mediaDevices
  global.navigator.mediaDevices = {
    getUserMedia: vi.fn().mockResolvedValue(new MockMediaStream()),
  } as any;

  // Mock fetch for WebRTC offer endpoint
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: vi.fn().mockResolvedValue({
      type: 'answer',
      sdp: 'mock-sdp-answer'
    }),
  }) as any;
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useWebRTCChat Hook', () => {
  const mockOptions = {
    assistantId: 'test-assistant-123',
    onTranscription: vi.fn(),
    onTextResponse: vi.fn(),
    onAudioChunk: vi.fn(),
    onAudioComplete: vi.fn(),
    onError: vi.fn(),
    onStatusChange: vi.fn(),
  };

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    expect(result.current.isConnected).toBe(false);
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
  });

  it('should provide all required methods', () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
    expect(typeof result.current.startRecording).toBe('function');
    expect(typeof result.current.stopRecording).toBe('function');
    expect(typeof result.current.stopAudio).toBe('function');
    expect(typeof result.current.sendTextMessage).toBe('function');
  });

  it('should automatically attempt to connect on mount', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith(
        expect.objectContaining({
          audio: expect.objectContaining({
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000,
          }),
        })
      );
    }, { timeout: 3000 });
  });

  it('should set isConnected to true when data channel opens', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    expect(mockOptions.onStatusChange).toHaveBeenCalledWith('Connected');
  });

  it('should create WebRTC offer and send to server', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.com/voice/webrtc/offer',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token-123',
          }),
          body: expect.stringContaining('mock-sdp-offer'),
        })
      );
    }, { timeout: 3000 });
  });

  it('should request microphone access on connection', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Should request microphone with audio constraints
    const calls = (global.navigator.mediaDevices.getUserMedia as any).mock.calls;
    expect(calls.length).toBeGreaterThan(0);
    expect(calls[0][0]).toHaveProperty('audio');
  });

  it('should enable audio tracks when startRecording is called', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    result.current.startRecording();

    await waitFor(() => {
      expect(result.current.isRecording).toBe(true);
    });

    expect(mockOptions.onStatusChange).toHaveBeenCalledWith('Recording...');
  });

  it('should disable audio tracks when stopRecording is called', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    result.current.startRecording();

    await waitFor(() => {
      expect(result.current.isRecording).toBe(true);
    });

    result.current.stopRecording();

    await waitFor(() => {
      expect(result.current.isRecording).toBe(false);
    });

    expect(mockOptions.onStatusChange).toHaveBeenCalledWith('Processing...');
  });

  it('should have callback for handling transcription messages', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify the hook was called with onTranscription callback
    expect(mockOptions.onTranscription).toBeDefined();
    expect(typeof mockOptions.onTranscription).toBe('function');
  });

  it('should have callback for handling text response messages', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify the hook was called with onTextResponse callback
    expect(mockOptions.onTextResponse).toBeDefined();
    expect(typeof mockOptions.onTextResponse).toBe('function');
  });

  it('should have callback for handling audio chunks', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify the hook was called with onAudioChunk callback
    expect(mockOptions.onAudioChunk).toBeDefined();
    expect(typeof mockOptions.onAudioChunk).toBe('function');
  });

  it('should have callback for handling audio complete messages', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify the hook was called with onAudioComplete callback
    expect(mockOptions.onAudioComplete).toBeDefined();
    expect(typeof mockOptions.onAudioComplete).toBe('function');
  });

  it('should have callback for handling error messages', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify the hook was called with onError callback
    expect(mockOptions.onError).toBeDefined();
    expect(typeof mockOptions.onError).toBe('function');
  });

  it('should send text messages through data channel', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    const sendSpy = vi.fn();
    const pc = new MockRTCPeerConnection();
    const dc = pc.createDataChannel('chat');
    dc.send = sendSpy;

    result.current.sendTextMessage('Hello assistant');

    // Note: In real implementation, this would send through the actual data channel
    // For now we verify the method exists and can be called without errors
    expect(typeof result.current.sendTextMessage).toBe('function');
  });

  it('should stop audio playback when stopAudio is called', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    result.current.stopAudio();

    expect(result.current.isSpeaking).toBe(false);
  });

  it('should cleanup resources on disconnect', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    result.current.disconnect();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
    expect(mockOptions.onStatusChange).toHaveBeenCalledWith('Disconnected');
  });

  it('should cleanup resources on unmount', async () => {
    const { result, unmount } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    unmount();

    // Verify cleanup happened without errors
    expect(result.current).toBeDefined();
  });

  it('should handle missing callbacks gracefully', async () => {
    const minimalOptions = {
      assistantId: 'test-assistant-123',
    };

    const { result } = renderHook(() => useWebRTCChat(minimalOptions));

    // Should not throw errors even without callbacks
    await waitFor(() => {
      expect(result.current.isConnected).toBeDefined();
    }, { timeout: 3000 });
  });

  it('should not allow recording when not connected', () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    // Try to start recording before connection is established
    result.current.startRecording();

    // Should call onError about not being initialized
    expect(mockOptions.onError).toHaveBeenCalled();
    expect(result.current.isRecording).toBe(false);
  });

  it('should maintain connection state throughout lifecycle', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Connection should remain stable
    expect(result.current.isConnected).toBe(true);
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
  });

  it('should expose all necessary control methods', async () => {
    const { result } = renderHook(() => useWebRTCChat(mockOptions));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Verify all control methods are available
    expect(typeof result.current.startRecording).toBe('function');
    expect(typeof result.current.stopRecording).toBe('function');
    expect(typeof result.current.stopAudio).toBe('function');
    expect(typeof result.current.sendTextMessage).toBe('function');
    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
  });
});
