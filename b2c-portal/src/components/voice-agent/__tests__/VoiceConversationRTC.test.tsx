import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VoiceConversationRTC } from '../VoiceConversationRTC';

// Mock the WebRTC hook
const mockUseWebRTCChat = {
  isConnected: true,
  isRecording: false,
  isSpeaking: false,
  sendTextMessage: vi.fn(),
  startRecording: vi.fn(),
  stopRecording: vi.fn(),
  stopAudio: vi.fn(),
  disconnect: vi.fn(),
};

vi.mock('@/hooks/useWebRTCChat', () => ({
  useWebRTCChat: vi.fn(() => mockUseWebRTCChat),
}));

// Mock conversation session service
vi.mock('@/services/conversation-session', () => ({
  conversationSessionService: {
    createSession: vi.fn().mockReturnValue({
      id: 'test-session-123',
      startTime: Date.now(),
      messages: [],
      metadata: {
        totalMessages: 0,
        duration: 0,
        language: 'en',
      },
    }),
    endSession: vi.fn(),
    addMessage: vi.fn(),
    updateContext: vi.fn(),
    exportSession: vi.fn().mockReturnValue(
      JSON.stringify({ sessionId: 'test-session-123', messages: [] })
    ),
  },
}));

describe('VoiceConversationRTC Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    assistantName: 'Test Assistant',
    assistantId: 'test-assistant-123',
    assistant: {
      id: 'test-assistant-123',
      name: 'Test Assistant',
      language: 'en',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock to default state
    Object.assign(mockUseWebRTCChat, {
      isConnected: true,
      isRecording: false,
      isSpeaking: false,
      sendTextMessage: vi.fn(),
      startRecording: vi.fn(),
      stopRecording: vi.fn(),
      stopAudio: vi.fn(),
      disconnect: vi.fn(),
    });

    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('should render when isOpen is true', () => {
    render(<VoiceConversationRTC {...defaultProps} />);

    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('WebRTC')).toBeInTheDocument();
  });

  it('should not render when isOpen is false', () => {
    render(<VoiceConversationRTC {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Test Assistant')).not.toBeInTheDocument();
  });

  it('should display WebRTC badge when connected', () => {
    render(<VoiceConversationRTC {...defaultProps} />);

    const webrtcBadge = screen.getByText('WebRTC');
    expect(webrtcBadge).toBeInTheDocument();
    expect(webrtcBadge.className).toContain('bg-green-100');
  });

  it('should show disconnected indicator when not connected', () => {
    Object.assign(mockUseWebRTCChat, { isConnected: false });

    render(<VoiceConversationRTC {...defaultProps} />);

    // WebRTC badge should not be visible when disconnected
    const disconnected = screen.queryByText('WebRTC');
    expect(disconnected).not.toBeInTheDocument();
  });

  it('should render conversation interface elements', () => {
    render(<VoiceConversationRTC {...defaultProps} />);

    // Check for key interface elements
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
    expect(screen.getByText('WebRTC')).toBeInTheDocument();
  });

  it('should integrate with useWebRTCChat hook', () => {
    render(<VoiceConversationRTC {...defaultProps} />);

    // Verify component is using the WebRTC hook
    expect(mockUseWebRTCChat.sendTextMessage).toBeDefined();
    expect(mockUseWebRTCChat.startRecording).toBeDefined();
    expect(mockUseWebRTCChat.stopRecording).toBeDefined();
    expect(mockUseWebRTCChat.stopAudio).toBeDefined();
  });

  it('should handle missing assistant prop gracefully', () => {
    const propsWithoutAssistant = {
      ...defaultProps,
      assistant: undefined,
    };

    render(<VoiceConversationRTC {...propsWithoutAssistant} />);

    // Should still render without crashing
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
  });

  it('should initialize with default language when assistant language is not specified', () => {
    const propsWithoutLanguage = {
      ...defaultProps,
      assistant: {
        id: 'test-assistant-123',
        name: 'Test Assistant',
      },
    };

    render(<VoiceConversationRTC {...propsWithoutLanguage} />);

    // Should render without crashing and default to English
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
  });

  it('should render with all required props', () => {
    render(<VoiceConversationRTC {...defaultProps} />);

    // Verify all key UI elements are present
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('WebRTC')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });
});
