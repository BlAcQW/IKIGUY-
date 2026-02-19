import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoVersioning from '@/components/DemoVersioning';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';

// Mock dependencies
vi.mock('@/components/ui/use-toast');
vi.mock('@/integrations/supabase/client');

const mockToast = vi.fn();
const mockSupabase = {
  functions: {
    invoke: vi.fn()
  }
};

describe('DemoVersioning', () => {
  const mockProps = {
    demoId: 'demo-1',
    assistantName: 'Test Assistant',
    assistantType: 'sales_cold_call',
    currentVersion: 2,
    onVersionChange: vi.fn()
  };

  const mockVersions = [
    {
      version_number: 2,
      assistant_name: 'Test Assistant v2',
      assistant_type: 'sales_cold_call',
      description: 'Updated version with new features',
      version_notes: 'Added new sales scripts and improved responses',
      created_at: '2024-01-15T10:30:00Z',
      is_current: true
    },
    {
      version_number: 1,
      assistant_name: 'Test Assistant',
      assistant_type: 'sales_cold_call',
      description: 'Initial version',
      version_notes: 'Initial version with basic functionality',
      created_at: '2024-01-10T09:00:00Z',
      is_current: false
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (supabase as any).mockReturnValue(mockSupabase);
  });

  it('renders version management buttons', () => {
    render(<DemoVersioning {...mockProps} />);
    
    expect(screen.getByText('New Version')).toBeInTheDocument();
    expect(screen.getByText('Version History')).toBeInTheDocument();
  });

  it('shows version count badge when versions exist', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Version count badge
    });
  });

  it('opens create version dialog when New Version button is clicked', () => {
    render(<DemoVersioning {...mockProps} />);
    
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    expect(screen.getByText('Create New Version')).toBeInTheDocument();
    expect(screen.getByText('Test Assistant')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument(); // Current version badge
  });

  it('requires version notes to create a new version', async () => {
    render(<DemoVersioning {...mockProps} />);
    
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    const createButton = screen.getByText('Create Version');
    expect(createButton).toBeDisabled();
    
    const notesTextarea = screen.getByPlaceholderText('Describe what changes you\'re making in this version...');
    fireEvent.change(notesTextarea, { target: { value: 'Test version notes' } });
    
    expect(createButton).not.toBeDisabled();
  });

  it('creates a new version successfully', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions }
      })
      .mockResolvedValueOnce({
        data: { success: true, version_number: 3 }
      })
      .mockResolvedValueOnce({
        data: { success: true, versions: [...mockVersions, { ...mockVersions[0], version_number: 3, is_current: true }] }
      });

    render(<DemoVersioning {...mockProps} />);
    
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    const notesTextarea = screen.getByPlaceholderText('Describe what changes you\'re making in this version...');
    fireEvent.change(notesTextarea, { target: { value: 'New version with improvements' } });
    
    const createButton = screen.getByText('Create Version');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('demo-versioning', {
        body: { 
          demo_id: 'demo-1',
          version_notes: 'New version with improvements'
        },
        query: { action: 'create_version' }
      });
    });
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Version created!',
        description: 'Version 3 created successfully'
      });
    });
    
    expect(mockProps.onVersionChange).toHaveBeenCalledWith(3);
  });

  it('handles version creation error', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions }
      })
      .mockRejectedValueOnce(new Error('Failed to create version'));

    render(<DemoVersioning {...mockProps} />);
    
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    const notesTextarea = screen.getByPlaceholderText('Describe what changes you\'re making in this version...');
    fireEvent.change(notesTextarea, { target: { value: 'Test notes' } });
    
    const createButton = screen.getByText('Create Version');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to create version',
        variant: 'destructive'
      });
    });
  });

  it('opens version history dialog when Version History button is clicked', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Version History')).toBeInTheDocument();
      expect(screen.getByText('Track all versions of your demo and rollback to previous versions if needed')).toBeInTheDocument();
    });
  });

  it('displays version history correctly', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('v2')).toBeInTheDocument();
      expect(screen.getByText('v1')).toBeInTheDocument();
      expect(screen.getByText('Test Assistant v2')).toBeInTheDocument();
      expect(screen.getByText('Test Assistant')).toBeInTheDocument();
      expect(screen.getByText('Current')).toBeInTheDocument();
      expect(screen.getByText('Added new sales scripts and improved responses')).toBeInTheDocument();
      expect(screen.getByText('Initial version with basic functionality')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching version history', () => {
    mockSupabase.functions.invoke.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    expect(screen.getByText('Loading version history...')).toBeInTheDocument();
  });

  it('shows empty state when no versions exist', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: [] }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('No versions yet')).toBeInTheDocument();
      expect(screen.getByText('Create your first version to start tracking changes')).toBeInTheDocument();
      expect(screen.getByText('Create First Version')).toBeInTheDocument();
    });
  });

  it('handles version history fetch error', async () => {
    mockSupabase.functions.invoke.mockRejectedValue(new Error('Failed to fetch'));

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to fetch version history',
        variant: 'destructive'
      });
    });
  });

  it('shows rollback button for non-current versions', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      const rollbackButtons = screen.getAllByText('Rollback');
      expect(rollbackButtons).toHaveLength(1); // Only for v1, not v2 (current)
    });
  });

  it('opens rollback confirmation dialog when rollback button is clicked', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      const rollbackButton = screen.getByText('Rollback');
      fireEvent.click(rollbackButton);
    });
    
    expect(screen.getByText('Confirm Rollback')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText(/Rolling back to version 1 will replace your current demo configuration/)).toBeInTheDocument();
  });

  it('performs rollback successfully', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions }
      })
      .mockResolvedValueOnce({
        data: { success: true }
      })
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions.map(v => ({ ...v, is_current: v.version_number === 1 })) }
      });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      const rollbackButton = screen.getByText('Rollback');
      fireEvent.click(rollbackButton);
    });
    
    const confirmRollbackButton = screen.getByText('Rollback to v1');
    fireEvent.click(confirmRollbackButton);
    
    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('demo-versioning', {
        body: { 
          demo_id: 'demo-1',
          version_number: 1
        },
        query: { action: 'rollback_version' }
      });
    });
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Rollback successful!',
        description: 'Rolled back to version 1'
      });
    });
    
    expect(mockProps.onVersionChange).toHaveBeenCalledWith(1);
  });

  it('handles rollback error', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions }
      })
      .mockRejectedValueOnce(new Error('Failed to rollback'));

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      const rollbackButton = screen.getByText('Rollback');
      fireEvent.click(rollbackButton);
    });
    
    const confirmRollbackButton = screen.getByText('Rollback to v1');
    fireEvent.click(confirmRollbackButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to rollback version',
        variant: 'destructive'
      });
    });
  });

  it('formats dates correctly', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      // Check that dates are formatted (the exact format depends on locale)
      expect(screen.getByText(/Jan 15/)).toBeInTheDocument();
      expect(screen.getByText(/Jan 10/)).toBeInTheDocument();
    });
  });

  it('closes dialogs when cancel buttons are clicked', () => {
    render(<DemoVersioning {...mockProps} />);
    
    // Test create version dialog
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    expect(screen.getByText('Create New Version')).toBeInTheDocument();
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(screen.queryByText('Create New Version')).not.toBeInTheDocument();
  });

  it('works without onVersionChange callback', async () => {
    const propsWithoutCallback = { ...mockProps };
    delete propsWithoutCallback.onVersionChange;
    
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { success: true, versions: mockVersions }
      })
      .mockResolvedValueOnce({
        data: { success: true, version_number: 3 }
      });

    render(<DemoVersioning {...propsWithoutCallback} />);
    
    const newVersionButton = screen.getByText('New Version');
    fireEvent.click(newVersionButton);
    
    const notesTextarea = screen.getByPlaceholderText('Describe what changes you\'re making in this version...');
    fireEvent.change(notesTextarea, { target: { value: 'Test notes' } });
    
    const createButton = screen.getByText('Create Version');
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Version created!',
        description: 'Version 3 created successfully'
      });
    });
    
    // Should not throw error when onVersionChange is not provided
  });

  it('displays assistant type correctly', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getAllByText('sales cold call')).toHaveLength(2);
    });
  });

  it('shows version notes in history', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: mockVersions }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Version Notes')).toBeInTheDocument();
      expect(screen.getByText('Added new sales scripts and improved responses')).toBeInTheDocument();
      expect(screen.getByText('Initial version with basic functionality')).toBeInTheDocument();
    });
  });

  it('handles empty version notes gracefully', async () => {
    const versionsWithEmptyNotes = mockVersions.map(v => ({ ...v, version_notes: '' }));
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { success: true, versions: versionsWithEmptyNotes }
    });

    render(<DemoVersioning {...mockProps} />);
    
    const historyButton = screen.getByText('Version History');
    fireEvent.click(historyButton);
    
    await waitFor(() => {
      // Should not show "Version Notes" label when notes are empty
      expect(screen.queryByText('Version Notes')).not.toBeInTheDocument();
    });
  });
});
