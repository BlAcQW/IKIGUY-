import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoEmbedding from '@/components/DemoEmbedding';
import { useToast } from '@/components/ui/use-toast';

// Mock dependencies
vi.mock('@/components/ui/use-toast');

const mockToast = vi.fn();

describe('DemoEmbedding', () => {
  const mockProps = {
    demoId: 'demo-1',
    assistantName: 'Test Assistant',
    assistantType: 'sales_cold_call',
    assistantId: 'assistant-1',
    description: 'A test assistant for sales calls',
    onEmbed: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    
    // Mock navigator.clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined)
      },
      writable: true
    });
    
    // Mock URL.createObjectURL and document.createElement for download
    Object.defineProperty(global, 'URL', {
      value: {
        createObjectURL: vi.fn(() => 'blob:mock-url'),
        revokeObjectURL: vi.fn()
      }
    });

    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: vi.fn()
      }))
    });

    Object.defineProperty(document.body, 'appendChild', {
      value: vi.fn()
    });

    Object.defineProperty(document.body, 'removeChild', {
      value: vi.fn()
    });
  });

  it('renders embed button', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    expect(screen.getByText('Embed Demo')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /embed demo/i })).toBeInTheDocument();
  });

  it('opens embed dialog when button is clicked', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    expect(screen.getByText('Embed Demo')).toBeInTheDocument();
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
  });

  it('displays demo info in dialog', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
    expect(screen.getByText('A test assistant for sales calls')).toBeInTheDocument();
  });

  it('shows configuration tab by default', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('Theme')).toBeInTheDocument();
    expect(screen.getByText('Position')).toBeInTheDocument();
    expect(screen.getByText('Size')).toBeInTheDocument();
    expect(screen.getByText('Mode')).toBeInTheDocument();
  });

  it('allows theme selection', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const themeSelect = screen.getByDisplayValue('Dark');
    fireEvent.click(themeSelect);
    
    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Dark')).toBeInTheDocument();
  });

  it('allows position selection', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const positionSelect = screen.getByDisplayValue('Bottom Right');
    fireEvent.click(positionSelect);
    
    expect(screen.getByText('Bottom Right')).toBeInTheDocument();
    expect(screen.getByText('Bottom Left')).toBeInTheDocument();
    expect(screen.getByText('Top Right')).toBeInTheDocument();
    expect(screen.getByText('Top Left')).toBeInTheDocument();
    expect(screen.getByText('Center')).toBeInTheDocument();
  });

  it('allows size selection', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const sizeSelect = screen.getByDisplayValue('Large');
    fireEvent.click(sizeSelect);
    
    expect(screen.getByText('Small')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
    expect(screen.getByText('Full')).toBeInTheDocument();
  });

  it('allows mode selection', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const modeSelect = screen.getByDisplayValue('Voice Only');
    fireEvent.click(modeSelect);
    
    expect(screen.getByText('Voice Only')).toBeInTheDocument();
    expect(screen.getByText('Chat Only')).toBeInTheDocument();
    expect(screen.getByText('Voice & Chat')).toBeInTheDocument();
  });

  it('allows custom title input', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const titleInput = screen.getByDisplayValue('Talk to Test Assistant');
    fireEvent.change(titleInput, { target: { value: 'Custom Title' } });
    
    expect(titleInput).toHaveValue('Custom Title');
  });

  it('allows custom message input', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const messageInput = screen.getByDisplayValue('Hello! How can I help you today?');
    fireEvent.change(messageInput, { target: { value: 'Custom message' } });
    
    expect(messageInput).toHaveValue('Custom message');
  });

  it('allows toggling show transcript', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const transcriptSwitch = screen.getByRole('checkbox', { name: /show transcript/i });
    expect(transcriptSwitch).toBeChecked();
    
    fireEvent.click(transcriptSwitch);
    expect(transcriptSwitch).not.toBeChecked();
  });

  it('allows toggling consent required', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const consentSwitch = screen.getByRole('checkbox', { name: /require consent/i });
    expect(consentSwitch).toBeChecked();
    
    fireEvent.click(consentSwitch);
    expect(consentSwitch).not.toBeChecked();
  });

  it('switches to preview tab', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const previewButton = screen.getByText('Preview');
    fireEvent.click(previewButton);
    
    expect(screen.getByText('Widget Preview')).toBeInTheDocument();
    expect(screen.getByText('Desktop Preview')).toBeInTheDocument();
    expect(screen.getByText('Mobile Preview')).toBeInTheDocument();
  });

  it('switches to code tab', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    expect(screen.getByText('Embed Code')).toBeInTheDocument();
    expect(screen.getByText('Copy Widget')).toBeInTheDocument();
    expect(screen.getByText('Download Full Page')).toBeInTheDocument();
  });

  it('copies widget code to clipboard', async () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const copyButton = screen.getByText('Copy Widget');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalled();
      expect(mockProps.onEmbed).toHaveBeenCalledWith('widget', expect.any(String));
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Code copied!',
        description: 'Embed code copied to clipboard'
      });
    });
  });

  it('downloads full page code', async () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const downloadButton = screen.getByText('Download Full Page');
    fireEvent.click(downloadButton);
    
    await waitFor(() => {
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockProps.onEmbed).toHaveBeenCalledWith('download', expect.any(String));
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Downloaded!',
        description: 'test-assistant-demo.html downloaded successfully'
      });
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
    
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const copyButton = screen.getByText('Copy Widget');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Failed to copy',
        description: 'Could not copy code to clipboard',
        variant: 'destructive'
      });
    });
  });

  it('displays widget code in textarea', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const widgetCodeTextarea = screen.getByDisplayValue(/<!-- Test Assistant - AI Voice Assistant Widget -->/);
    expect(widgetCodeTextarea).toBeInTheDocument();
    expect(widgetCodeTextarea).toHaveValue(expect.stringContaining('vapi-widget'));
  });

  it('displays full page code in textarea', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const fullPageTextarea = screen.getByDisplayValue(/<!DOCTYPE html>/);
    expect(fullPageTextarea).toBeInTheDocument();
    expect(fullPageTextarea).toHaveValue(expect.stringContaining('<html lang="en">'));
  });

  it('shows instructions in code tab', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    expect(screen.getByText('📋 Instructions')).toBeInTheDocument();
    expect(screen.getByText(/Widget Code:/)).toBeInTheDocument();
    expect(screen.getByText(/Full Page Code:/)).toBeInTheDocument();
  });

  it('closes dialog when close button is clicked', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    expect(screen.getByText('Embed Demo')).toBeInTheDocument();
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(screen.queryByText('Embed Demo')).not.toBeInTheDocument();
  });

  it('works without onEmbed callback', () => {
    const propsWithoutCallback = { ...mockProps };
    delete propsWithoutCallback.onEmbed;
    
    render(<DemoEmbedding {...propsWithoutCallback} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const copyButton = screen.getByText('Copy Widget');
    fireEvent.click(copyButton);
    
    // Should not throw error
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('handles assistant name with special characters in filename', () => {
    const propsWithSpecialChars = {
      ...mockProps,
      assistantName: 'Test & Assistant (Special)'
    };
    
    render(<DemoEmbedding {...propsWithSpecialChars} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const downloadButton = screen.getByText('Download Full Page');
    fireEvent.click(downloadButton);
    
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Downloaded!',
      description: 'test-assistant-special-demo.html downloaded successfully'
    });
  });

  it('updates preview when configuration changes', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    // Change custom title
    const titleInput = screen.getByDisplayValue('Talk to Test Assistant');
    fireEvent.change(titleInput, { target: { value: 'New Title' } });
    
    // Switch to preview tab
    const previewButton = screen.getByText('Preview');
    fireEvent.click(previewButton);
    
    expect(screen.getByText('New Title')).toBeInTheDocument();
  });

  it('generates different code for different configurations', () => {
    render(<DemoEmbedding {...mockProps} />);
    
    const embedButton = screen.getByRole('button', { name: /embed demo/i });
    fireEvent.click(embedButton);
    
    // Get initial code
    const codeButton = screen.getByText('Code');
    fireEvent.click(codeButton);
    
    const initialCode = screen.getByDisplayValue(/<!-- Test Assistant - AI Voice Assistant Widget -->/).value;
    
    // Change theme
    const configButton = screen.getByText('Configuration');
    fireEvent.click(configButton);
    
    const themeSelect = screen.getByDisplayValue('Dark');
    fireEvent.click(themeSelect);
    fireEvent.click(screen.getByText('Light'));
    
    // Get new code
    fireEvent.click(codeButton);
    
    const newCode = screen.getByDisplayValue(/<!-- Test Assistant - AI Voice Assistant Widget -->/).value;
    
    expect(initialCode).not.toBe(newCode);
  });
});
