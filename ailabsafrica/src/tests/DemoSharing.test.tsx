import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoSharing from '@/components/DemoSharing';
import { useToast } from '@/components/ui/use-toast';

// Mock dependencies
vi.mock('@/components/ui/use-toast');

const mockToast = vi.fn();

describe('DemoSharing', () => {
  const mockProps = {
    demoId: 'demo-1',
    assistantName: 'Test Assistant',
    assistantType: 'sales_cold_call',
    demoUrl: 'https://example.com/demo',
    description: 'A test assistant for sales calls',
    onShare: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    
    // Mock window.open
    Object.defineProperty(window, 'open', {
      value: vi.fn(),
      writable: true
    });
    
    // Mock navigator.clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined)
      },
      writable: true
    });
    
    // Mock navigator.userAgent
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      writable: true
    });
  });

  it('renders share button', () => {
    render(<DemoSharing {...mockProps} />);
    
    expect(screen.getByText('Share Demo')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /share demo/i })).toBeInTheDocument();
  });

  it('opens share dialog when button is clicked', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    expect(screen.getByText('Share Demo')).toBeInTheDocument();
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
  });

  it('displays demo preview in dialog', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
    expect(screen.getByText('A test assistant for sales calls')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/demo')).toBeInTheDocument();
  });

  it('shows custom message textarea', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const textarea = screen.getByLabelText('Custom Message (Optional)');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue('');
  });

  it('displays default message in textarea placeholder', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const textarea = screen.getByLabelText('Custom Message (Optional)');
    expect(textarea).toHaveAttribute('placeholder', 'Check out Test Assistant, an AI voice assistant for sales cold call! 🎤✨');
  });

  it('allows custom message input', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const textarea = screen.getByLabelText('Custom Message (Optional)');
    fireEvent.change(textarea, { target: { value: 'Custom share message' } });
    
    expect(textarea).toHaveValue('Custom share message');
  });

  it('displays all social media platforms', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    expect(screen.getByText('Twitter')).toBeInTheDocument();
    expect(screen.getByText('Facebook')).toBeInTheDocument();
    expect(screen.getByText('LinkedIn')).toBeInTheDocument();
    expect(screen.getByText('WhatsApp')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('handles Twitter sharing', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const twitterButton = screen.getByText('Twitter').closest('button');
    fireEvent.click(twitterButton!);
    
    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('twitter.com/intent/tweet'),
      '_blank',
      expect.any(String)
    );
    expect(mockProps.onShare).toHaveBeenCalledWith('twitter', expect.any(String));
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Shared!',
      description: 'Shared on Twitter'
    });
  });

  it('handles Facebook sharing', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const facebookButton = screen.getByText('Facebook').closest('button');
    fireEvent.click(facebookButton!);
    
    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('facebook.com/sharer'),
      '_blank',
      expect.any(String)
    );
    expect(mockProps.onShare).toHaveBeenCalledWith('facebook', expect.any(String));
  });

  it('handles LinkedIn sharing', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const linkedinButton = screen.getByText('LinkedIn').closest('button');
    fireEvent.click(linkedinButton!);
    
    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('linkedin.com/sharing'),
      '_blank',
      expect.any(String)
    );
    expect(mockProps.onShare).toHaveBeenCalledWith('linkedin', expect.any(String));
  });

  it('handles WhatsApp sharing on desktop', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const whatsappButton = screen.getByText('WhatsApp').closest('button');
    fireEvent.click(whatsappButton!);
    
    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('wa.me'),
      '_blank',
      expect.any(String)
    );
    expect(mockProps.onShare).toHaveBeenCalledWith('whatsapp', expect.any(String));
  });

  it('handles WhatsApp sharing on mobile', () => {
    // Mock mobile user agent
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
      writable: true
    });
    
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const whatsappButton = screen.getByText('WhatsApp').closest('button');
    fireEvent.click(whatsappButton!);
    
    expect(window.location.href).toBe(expect.stringContaining('whatsapp://send'));
  });

  it('handles email sharing', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const emailButton = screen.getByText('Email').closest('button');
    fireEvent.click(emailButton!);
    
    expect(window.open).toHaveBeenCalledWith(
      expect.stringContaining('mailto:'),
      '_blank',
      expect.any(String)
    );
    expect(mockProps.onShare).toHaveBeenCalledWith('email', expect.any(String));
  });

  it('copies share link to clipboard', async () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const copyLinkButton = screen.getByText('Copy Link');
    fireEvent.click(copyLinkButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com/demo');
      expect(mockProps.onShare).toHaveBeenCalledWith('copy_link', 'https://example.com/demo');
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Link copied!',
        description: 'Demo link copied to clipboard'
      });
    });
  });

  it('copies share text to clipboard', async () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const copyTextButton = screen.getByText('Copy Text');
    fireEvent.click(copyTextButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('Check out Test Assistant')
      );
      expect(mockProps.onShare).toHaveBeenCalledWith('copy_text', expect.any(String));
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Text copied!',
        description: 'Share text copied to clipboard'
      });
    });
  });

  it('copies custom message when provided', async () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const textarea = screen.getByLabelText('Custom Message (Optional)');
    fireEvent.change(textarea, { target: { value: 'Custom message' } });
    
    const copyTextButton = screen.getByText('Copy Text');
    fireEvent.click(copyTextButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('Custom message')
      );
    });
  });

  it('handles clipboard copy error', async () => {
    // Mock clipboard error
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockRejectedValue(new Error('Clipboard error'))
      },
      writable: true
    });
    
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const copyLinkButton = screen.getByText('Copy Link');
    fireEvent.click(copyLinkButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to copy',
        description: 'Could not copy link to clipboard',
        variant: 'destructive'
      });
    });
  });

  it('closes dialog when close button is clicked', () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    expect(screen.getByText('Share Demo')).toBeInTheDocument();
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(screen.queryByText('Share Demo')).not.toBeInTheDocument();
  });

  it('handles popup blocked scenario', () => {
    // Mock popup blocked
    (window.open as any).mockReturnValue(null);
    
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const twitterButton = screen.getByText('Twitter').closest('button');
    fireEvent.click(twitterButton!);
    
    // Should fallback to direct navigation
    expect(window.open).toHaveBeenCalledTimes(2);
  });

  it('works without onShare callback', () => {
    const propsWithoutCallback = { ...mockProps };
    delete propsWithoutCallback.onShare;
    
    render(<DemoSharing {...propsWithoutCallback} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const twitterButton = screen.getByText('Twitter').closest('button');
    fireEvent.click(twitterButton!);
    
    // Should not throw error
    expect(window.open).toHaveBeenCalled();
  });

  it('handles assistant type with underscores', () => {
    const propsWithUnderscores = {
      ...mockProps,
      assistantType: 'customer_support_agent'
    };
    
    render(<DemoSharing {...propsWithUnderscores} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    expect(screen.getByText('customer support agent')).toBeInTheDocument();
    
    const textarea = screen.getByLabelText('Custom Message (Optional)');
    expect(textarea).toHaveAttribute('placeholder', 'Check out Test Assistant, an AI voice assistant for customer support agent! 🎤✨');
  });

  it('displays copy button states correctly', async () => {
    render(<DemoSharing {...mockProps} />);
    
    const shareButton = screen.getByRole('button', { name: /share demo/i });
    fireEvent.click(shareButton);
    
    const copyLinkButton = screen.getByText('Copy Link');
    expect(copyLinkButton).toBeInTheDocument();
    
    fireEvent.click(copyLinkButton);
    
    await waitFor(() => {
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });
});
