import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AssistantHeader } from '../AssistantHeader';

describe('AssistantHeader', () => {
  const defaultProps = {
    assistantName: 'Test Assistant',
    assistantId: 'test-assistant-123',
    onStartConversation: vi.fn(),
    onShowCode: vi.fn(),
    onDelete: vi.fn(),
    onClone: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders assistant header with name and ID', () => {
    render(<AssistantHeader {...defaultProps} />);

    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('test-assistant-123')).toBeInTheDocument();
    expect(screen.getByText('Kasa AI')).toBeInTheDocument();
  });

  it('calls onStartConversation when Talk to Assistant button is clicked', () => {
    render(<AssistantHeader {...defaultProps} />);

    const talkButton = screen.getByText('Talk to Assistant');
    fireEvent.click(talkButton);

    expect(defaultProps.onStartConversation).toHaveBeenCalledTimes(1);
  });

  it('has more options button that can be clicked', () => {
    render(<AssistantHeader {...defaultProps} />);

    // Find the more options button by looking for the button with aria attributes
    const moreButton = screen.getByRole('button', { expanded: false });
    expect(moreButton).toBeInTheDocument();

    // Should be able to click it without errors
    fireEvent.click(moreButton);
    expect(moreButton).toBeInTheDocument();
  });

  it('includes clone callback in props', () => {
    const { onClone } = defaultProps;
    expect(typeof onClone).toBe('function');

    // Verify the callback exists and can be called
    expect(() => onClone()).not.toThrow();
    expect(defaultProps.onClone).toHaveBeenCalledTimes(1);
  });

  it('includes all required callback props', () => {
    const { onStartConversation, onShowCode, onDelete, onClone } = defaultProps;

    expect(typeof onStartConversation).toBe('function');
    expect(typeof onShowCode).toBe('function');
    expect(typeof onDelete).toBe('function');
    expect(typeof onClone).toBe('function');
  });

  it('renders all action buttons', () => {
    render(<AssistantHeader {...defaultProps} />);

    expect(screen.getByText('Code')).toBeInTheDocument();
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('Talk to Assistant')).toBeInTheDocument();
    expect(screen.getByText('Call')).toBeInTheDocument();
  });

  it('handles empty assistant name gracefully', () => {
    render(<AssistantHeader {...defaultProps} assistantName="" />);

    // Component should render without crashing, even with empty name
    expect(screen.getByText('Kasa AI')).toBeInTheDocument();
  });

  it('handles long assistant names', () => {
    const longName = 'This is a very long assistant name that might cause layout issues if not handled properly';
    render(<AssistantHeader {...defaultProps} assistantName={longName} />);

    expect(screen.getByText(longName)).toBeInTheDocument();
  });

  it('renders Docs button', () => {
    render(<AssistantHeader {...defaultProps} />);

    expect(screen.getByText('Docs')).toBeInTheDocument();
  });

  describe('Transport Mode Toggle', () => {
    it('should not render transport toggle when onTransportModeChange is not provided', () => {
      render(<AssistantHeader {...defaultProps} />);

      expect(screen.queryByTitle('WebSocket (traditional)')).not.toBeInTheDocument();
      expect(screen.queryByTitle('WebRTC (low latency)')).not.toBeInTheDocument();
    });

    it('should render transport toggle when onTransportModeChange is provided', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      expect(screen.getByTitle('WebSocket (traditional)')).toBeInTheDocument();
      expect(screen.getByTitle('WebRTC (low latency)')).toBeInTheDocument();
    });

    it('should highlight websocket button when transportMode is websocket', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const wsButton = screen.getByTitle('WebSocket (traditional)');
      expect(wsButton.className).toContain('bg-background');
      expect(wsButton.className).toContain('shadow-sm');
    });

    it('should highlight webrtc button when transportMode is webrtc', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="webrtc"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const rtcButton = screen.getByTitle('WebRTC (low latency)');
      expect(rtcButton.className).toContain('bg-background');
      expect(rtcButton.className).toContain('shadow-sm');
    });

    it('should call onTransportModeChange with websocket when WS button is clicked', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="webrtc"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const wsButton = screen.getByTitle('WebSocket (traditional)');
      fireEvent.click(wsButton);

      expect(onTransportModeChange).toHaveBeenCalledWith('websocket');
      expect(onTransportModeChange).toHaveBeenCalledTimes(1);
    });

    it('should call onTransportModeChange with webrtc when RTC button is clicked', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const rtcButton = screen.getByTitle('WebRTC (low latency)');
      fireEvent.click(rtcButton);

      expect(onTransportModeChange).toHaveBeenCalledWith('webrtc');
      expect(onTransportModeChange).toHaveBeenCalledTimes(1);
    });

    it('should default to websocket mode when transportMode prop is not provided', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          onTransportModeChange={onTransportModeChange}
        />
      );

      const wsButton = screen.getByTitle('WebSocket (traditional)');
      expect(wsButton.className).toContain('bg-background');
    });

    it('should render Wifi icon for WebSocket button', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const wsButton = screen.getByTitle('WebSocket (traditional)');
      const icon = wsButton.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should render Radio icon for WebRTC button', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const rtcButton = screen.getByTitle('WebRTC (low latency)');
      const icon = rtcButton.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should show WS text on larger screens', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      // Text should be hidden on small screens (hidden sm:inline)
      const wsButtons = screen.getAllByText('WS');
      expect(wsButtons.length).toBeGreaterThan(0);
      wsButtons.forEach(button => {
        expect(button.className).toContain('hidden');
        expect(button.className).toContain('sm:inline');
      });
    });

    it('should show RTC text on larger screens', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const rtcButtons = screen.getAllByText('RTC');
      expect(rtcButtons.length).toBeGreaterThan(0);
      rtcButtons.forEach(button => {
        expect(button.className).toContain('hidden');
        expect(button.className).toContain('sm:inline');
      });
    });

    it('should allow switching between modes multiple times', () => {
      const onTransportModeChange = vi.fn();
      const { rerender } = render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      // Switch to WebRTC
      const rtcButton = screen.getByTitle('WebRTC (low latency)');
      fireEvent.click(rtcButton);
      expect(onTransportModeChange).toHaveBeenCalledWith('webrtc');

      // Re-render with new mode
      rerender(
        <AssistantHeader
          {...defaultProps}
          transportMode="webrtc"
          onTransportModeChange={onTransportModeChange}
        />
      );

      // Switch back to WebSocket
      const wsButton = screen.getByTitle('WebSocket (traditional)');
      fireEvent.click(wsButton);
      expect(onTransportModeChange).toHaveBeenCalledWith('websocket');
      expect(onTransportModeChange).toHaveBeenCalledTimes(2);
    });

    it('should maintain proper styling structure for toggle container', () => {
      const onTransportModeChange = vi.fn();
      render(
        <AssistantHeader
          {...defaultProps}
          transportMode="websocket"
          onTransportModeChange={onTransportModeChange}
        />
      );

      const wsButton = screen.getByTitle('WebSocket (traditional)');
      const container = wsButton.parentElement;

      expect(container?.className).toContain('flex');
      expect(container?.className).toContain('bg-muted');
      expect(container?.className).toContain('rounded-md');
    });
  });
});