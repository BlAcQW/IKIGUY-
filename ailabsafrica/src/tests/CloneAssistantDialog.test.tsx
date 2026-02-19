import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CloneAssistantDialog from '@/components/CloneAssistantDialog';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');

const mockToast = vi.fn();
const mockSupabase = {
  functions: {
    invoke: vi.fn()
  },
  auth: {
    getUser: vi.fn()
  }
};

describe('CloneAssistantDialog', () => {
  const mockAssistant = {
    id: 'demo-1',
    assistant_name: 'Test Assistant',
    assistant_type: 'sales_cold_call',
    assistant_id: 'assistant-1'
  };

  const mockProps = {
    open: true,
    onOpenChange: vi.fn(),
    assistant: mockAssistant,
    onSuccess: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (supabase as any) = mockSupabase;
    (mockSupabase.auth.getUser as any).mockResolvedValue({
      data: { user: { id: 'user-1' } }
    });
  });

  it('renders dialog with assistant information', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    expect(screen.getByText('Clone Assistant')).toBeInTheDocument();
    expect(screen.getByText('Cloning: Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('sales cold call')).toBeInTheDocument();
    expect(screen.getByLabelText('New Assistant Name')).toBeInTheDocument();
  });

  it('generates suggested clone name', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    const placeholder = input.getAttribute('placeholder');
    
    expect(placeholder).toContain('Test Assistant (Copy -');
    expect(placeholder).toMatch(/Test Assistant \(Copy - [A-Za-z]{3} \d{1,2}\)/);
  });

  it('disables clone button when name is empty', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    expect(cloneButton).toBeDisabled();
  });

  it('enables clone button when name is entered', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'New Test Assistant' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    expect(cloneButton).not.toBeDisabled();
  });

  it('shows error when trying to clone with empty name', async () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Error',
      description: 'Please enter a name for the cloned assistant',
      variant: 'destructive'
    });
  });

  it('successfully clones assistant', async () => {
    (mockSupabase.functions.invoke as any).mockResolvedValue({ error: null });
    
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'New Test Assistant' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('clone-assistant', {
        body: {
          source_assistant_id: 'assistant-1',
          new_name: 'New Test Assistant',
          user_id: 'user-1'
        }
      });
    });
    
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Success',
      description: 'Assistant cloned successfully'
    });
    
    expect(mockProps.onOpenChange).toHaveBeenCalledWith(false);
    expect(mockProps.onSuccess).toHaveBeenCalled();
  });

  it('handles name already exists error', async () => {
    (mockSupabase.functions.invoke as any).mockResolvedValue({
      error: { message: 'An assistant with this name already exists' }
    });
    
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'Existing Name' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Name already exists',
        description: 'Please choose a different name for the cloned assistant',
        variant: 'destructive'
      });
    });
  });

  it('handles general clone error', async () => {
    const errorMessage = 'Failed to clone assistant';
    (mockSupabase.functions.invoke as any).mockRejectedValue(new Error(errorMessage));
    
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'New Test Assistant' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Clone failed',
        description: errorMessage,
        variant: 'destructive'
      });
    });
  });

  it('shows loading state during cloning', async () => {
    (mockSupabase.functions.invoke as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ error: null }), 100))
    );
    
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'New Test Assistant' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    expect(screen.getByText('Cloning...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cloning.../i })).toBeDisabled();
    
    await waitFor(() => {
      expect(screen.getByText('Clone Assistant')).toBeInTheDocument();
    });
  });

  it('clears input when dialog is closed', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: 'Test Name' } });
    
    expect(input).toHaveValue('Test Name');
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    
    expect(mockProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it('handles dialog close without cloning', () => {
    render(<CloneAssistantDialog {...mockProps} />);
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    
    expect(mockProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it('renders correctly when assistant is null', () => {
    render(<CloneAssistantDialog {...mockProps} assistant={null} />);
    
    expect(screen.getByText('Clone Assistant')).toBeInTheDocument();
    expect(screen.queryByText('Cloning:')).not.toBeInTheDocument();
  });

  it('trims whitespace from assistant name', async () => {
    (mockSupabase.functions.invoke as any).mockResolvedValue({ error: null });
    
    render(<CloneAssistantDialog {...mockProps} />);
    
    const input = screen.getByLabelText('New Assistant Name');
    fireEvent.change(input, { target: { value: '  Test Name  ' } });
    
    const cloneButton = screen.getByRole('button', { name: /clone assistant/i });
    fireEvent.click(cloneButton);
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('clone-assistant', {
        body: {
          source_assistant_id: 'assistant-1',
          new_name: 'Test Name',
          user_id: 'user-1'
        }
      });
    });
  });
});
