import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import VoiceAgentManagement from '@/components/dashboard/VoiceAgentManagement';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/contexts/AuthContext');
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');

const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
};

const mockAgents = [
  {
    id: 'agent-1',
    name: 'Customer Support Bot',
    description: 'Handles customer inquiries and support',
    status: 'active',
    model: 'gpt-4',
    voice_id: 'voice-1',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    total_calls: 150,
    total_duration: 3600,
    last_call_at: '2024-01-20T14:30:00Z',
  },
  {
    id: 'agent-2',
    name: 'Sales Assistant',
    description: 'Generates leads and qualifies prospects',
    status: 'paused',
    model: 'gpt-4',
    voice_id: 'voice-2',
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-18T16:45:00Z',
    total_calls: 75,
    total_duration: 1800,
    last_call_at: '2024-01-18T16:45:00Z',
  },
  {
    id: 'agent-3',
    name: 'Appointment Scheduler',
    description: 'Schedules appointments and manages calendar',
    status: 'active',
    model: 'gpt-4',
    voice_id: 'voice-3',
    created_at: '2024-01-05T11:30:00Z',
    updated_at: '2024-01-05T11:30:00Z',
    total_calls: 200,
    total_duration: 4800,
    last_call_at: '2024-01-21T10:15:00Z',
  },
];

describe('VoiceAgentManagement', () => {
  const mockToast = vi.fn();
  const mockSupabase = {
    from: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    neq: vi.fn().mockReturnThis(),
    order: vi.fn().mockReturnThis(),
    functions: {
      invoke: vi.fn(),
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    (useAuth as any).mockReturnValue({
      user: mockUser,
    });
    
    (useToast as any).mockReturnValue({
      toast: mockToast,
    });
    
    (supabase as any) = mockSupabase;
  });

  it('renders loading state initially', () => {
    mockSupabase.order.mockResolvedValue({ data: null, error: null });
    
    render(<VoiceAgentManagement />);
    
    expect(screen.getByText('Loading voice agents...')).toBeInTheDocument();
  });

  it('renders agents when loaded successfully', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Customer Support Bot')).toBeInTheDocument();
      expect(screen.getByText('Sales Assistant')).toBeInTheDocument();
      expect(screen.getByText('Appointment Scheduler')).toBeInTheDocument();
    });
  });

  it('displays agent status badges correctly', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const activeBadges = screen.getAllByText('Active');
      expect(activeBadges.length).toBeGreaterThan(0);
      expect(screen.getByText('Paused')).toBeInTheDocument();
    });
  });

  it('handles individual agent pause action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent paused successfully' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const pauseButtons = screen.getAllByTitle('Pause Agent');
      fireEvent.click(pauseButtons[0]);
    });
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('manage-assistant', {
        body: {
          action: 'pause',
          assistant_id: 'agent-1',
          user_id: 'test-user-id'
        }
      });
    });
  });

  it('handles individual agent resume action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent resumed successfully' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const resumeButtons = screen.getAllByTitle('Resume Agent');
      fireEvent.click(resumeButtons[0]);
    });
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('manage-assistant', {
        body: {
          action: 'resume',
          assistant_id: 'agent-2',
          user_id: 'test-user-id'
        }
      });
    });
  });

  it('handles individual agent delete action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent deleted successfully' }, 
      error: null 
    });
    
    // Mock confirm dialog
    const mockConfirm = vi.fn().mockReturnValue(true);
    global.confirm = mockConfirm;
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle('Delete Agent');
      fireEvent.click(deleteButtons[0]);
    });
    
    expect(mockConfirm).toHaveBeenCalledWith(
      'Are you sure you want to delete "Customer Support Bot"? This action cannot be undone.'
    );
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('manage-assistant', {
        body: {
          action: 'delete',
          assistant_id: 'agent-1',
          user_id: 'test-user-id'
        }
      });
    });
  });

  it('shows bulk operations header when agents exist', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Select agents for bulk operations')).toBeInTheDocument();
    });
  });

  it('handles select all functionality', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      // Click the first checkbox (select all)
      fireEvent.click(checkboxes[0]);
    });
    
    await waitFor(() => {
      expect(screen.getByText('3 of 3 agents selected')).toBeInTheDocument();
    });
  });

  it('handles individual agent selection', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(1);
      // Click the second checkbox (first individual agent)
      fireEvent.click(checkboxes[1]);
    });
    
    await waitFor(() => {
      expect(screen.getByText('1 of 3 agents selected')).toBeInTheDocument();
    });
  });

  it('shows bulk action buttons when agents are selected', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      expect(screen.getByText('Pause 3 Agents')).toBeInTheDocument();
      expect(screen.getByText('Resume 3 Agents')).toBeInTheDocument();
      expect(screen.getByText('Delete 3 Agents')).toBeInTheDocument();
    });
  });

  it('handles bulk pause action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent paused successfully' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      const bulkPauseButton = screen.getByText('Pause 3 Agents');
      fireEvent.click(bulkPauseButton);
    });
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledTimes(3);
    });
  });

  it('handles bulk resume action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent resumed successfully' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      const bulkResumeButton = screen.getByText('Resume 3 Agents');
      fireEvent.click(bulkResumeButton);
    });
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledTimes(3);
    });
  });

  it('handles bulk delete action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent deleted successfully' }, 
      error: null 
    });
    
    // Mock confirm dialog
    const mockConfirm = vi.fn().mockReturnValue(true);
    global.confirm = mockConfirm;
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      const bulkDeleteButton = screen.getByText('Delete 3 Agents');
      fireEvent.click(bulkDeleteButton);
    });
    
    expect(mockConfirm).toHaveBeenCalled();
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledTimes(3);
    });
  });

  it('clears selection after bulk action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: true, message: 'Agent paused successfully' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      const bulkPauseButton = screen.getByText('Pause 3 Agents');
      fireEvent.click(bulkPauseButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Select agents for bulk operations')).toBeInTheDocument();
    });
  });

  it('disables checkboxes during bulk action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: { success: true } }), 100))
    );
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click select all
    });
    
    await waitFor(() => {
      const bulkPauseButton = screen.getByText('Pause 3 Agents');
      fireEvent.click(bulkPauseButton);
    });
    
    // Checkboxes should be disabled during bulk action
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeDisabled();
    });
  });

  it('shows empty state when no agents exist', async () => {
    mockSupabase.order.mockResolvedValue({ data: [], error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('No voice agents found')).toBeInTheDocument();
      expect(screen.getByText('Create your first voice agent to get started.')).toBeInTheDocument();
      expect(screen.getByText('Create Voice Agent')).toBeInTheDocument();
    });
  });

  it('handles copy to clipboard functionality', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    // Mock clipboard API
    const mockClipboard = {
      writeText: vi.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const copyButtons = screen.getAllByTitle('Copy Agent ID');
      fireEvent.click(copyButtons[0]);
    });
    
    expect(mockClipboard.writeText).toHaveBeenCalledWith('agent-1');
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Copied!',
      description: 'Agent ID copied to clipboard',
    });
  });

  it('handles refresh functionality', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      // Find refresh button by its icon and accessibility
      const buttons = screen.getAllByRole('button');
      const refreshButton = buttons.find(button => 
        button.querySelector('svg[class*="refresh-cw"]')
      );
      expect(refreshButton).toBeDefined();
      fireEvent.click(refreshButton!);
    });
    
    expect(mockSupabase.from).toHaveBeenCalledWith('voice_agents');
  });

  it('handles error when loading agents', async () => {
    const mockError = new Error('Database error');
    mockSupabase.order.mockResolvedValue({ data: null, error: mockError });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error loading agents',
        description: 'Database error',
        variant: 'destructive',
      });
    });
  });

  it('handles error during individual action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockResolvedValue({ 
      data: { success: false, error: 'Action failed' }, 
      error: null 
    });
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const pauseButtons = screen.getAllByTitle('Pause Agent');
      fireEvent.click(pauseButtons[0]);
    });
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Action failed',
        variant: 'destructive',
      });
    });
  });

  it('handles error during bulk action', async () => {
    mockSupabase.order.mockResolvedValue({ data: mockAgents, error: null });
    mockSupabase.functions.invoke.mockRejectedValue(new Error('Bulk action failed'));
    
    render(<VoiceAgentManagement />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
      fireEvent.click(checkboxes[0]); // Click the first checkbox (select all)
    });
    
    await waitFor(() => {
      const bulkPauseButton = screen.getByText('Pause 3 Agents');
      fireEvent.click(bulkPauseButton);
    });
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Bulk action partially completed',
        description: 'Successfully pauseed 0 agent(s), 3 failed',
        variant: 'destructive',
      });
    });
  });
});
