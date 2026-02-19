import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import TeamManagement from '../components/TeamManagement';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: vi.fn(() => Promise.resolve({
      data: {
        session: {
          access_token: 'mock-token'
        }
      }
    }))
  }
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

// Mock fetch
global.fetch = vi.fn();

describe('TeamManagement', () => {
  const mockTeams = [
    {
      id: 'team-1',
      name: 'Test Team',
      description: 'A test team',
      slug: 'test-team',
      owner_id: 'user-1',
      max_members: 10,
      is_active: true,
      created_at: '2025-01-21T10:00:00Z',
      updated_at: '2025-01-21T10:00:00Z'
    }
  ];

  const mockTeamMembers = [
    {
      user_id: 'user-1',
      email: 'user1@example.com',
      full_name: 'User One',
      role_name: 'owner',
      role_display_name: 'Owner',
      status: 'active',
      joined_at: '2025-01-21T10:00:00Z',
      last_active_at: '2025-01-21T10:00:00Z'
    },
    {
      user_id: 'user-2',
      email: 'user2@example.com',
      full_name: 'User Two',
      role_name: 'member',
      role_display_name: 'Member',
      status: 'active',
      joined_at: '2025-01-21T11:00:00Z',
      last_active_at: '2025-01-21T11:00:00Z'
    }
  ];

  const mockInvitations = [
    {
      id: 'inv-1',
      team_id: 'team-1',
      email: 'invite@example.com',
      role_id: 'role-1',
      invited_by: 'user-1',
      token: 'token-1',
      expires_at: '2025-01-28T10:00:00Z',
      status: 'pending',
      created_at: '2025-01-21T10:00:00Z',
      team_roles: {
        name: 'member',
        display_name: 'Member'
      }
    }
  ];

  const mockResources = [
    {
      id: 'resource-1',
      team_id: 'team-1',
      resource_type: 'assistant',
      resource_id: 'assistant-1',
      resource_name: 'Test Assistant',
      shared_by: 'user-1',
      permissions: { read: true, write: false, delete: false },
      is_public: false,
      created_at: '2025-01-21T10:00:00Z'
    }
  ];

  const mockActivity = [
    {
      id: 'activity-1',
      team_id: 'team-1',
      user_id: 'user-1',
      action: 'team_created',
      resource_type: null,
      resource_id: null,
      details: { team_name: 'Test Team' },
      created_at: '2025-01-21T10:00:00Z'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      json: () => Promise.resolve({ data: mockTeams })
    });
  });

  describe('Initial Rendering', () => {
    it('renders the component with title and description', async () => {
      render(<TeamManagement />);
      
      expect(screen.getByText('Team Management')).toBeInTheDocument();
      expect(screen.getByText('Manage your teams, members, and resources')).toBeInTheDocument();
    });

    it('shows loading state initially', () => {
      render(<TeamManagement />);
      
      expect(screen.getByText('Loading teams...')).toBeInTheDocument();
    });

    it('shows empty state when no teams exist', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ data: [] })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('No Teams Yet')).toBeInTheDocument();
        expect(screen.getByText('Create your first team to start collaborating with others')).toBeInTheDocument();
      });
    });
  });

  describe('Team Creation', () => {
    it('opens create team dialog when button is clicked', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Team')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Team'));

      expect(screen.getByText('Create New Team')).toBeInTheDocument();
      expect(screen.getByText('Create a new team to collaborate with others')).toBeInTheDocument();
    });

    it('handles team creation successfully', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ data: { id: 'new-team' } })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Team')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Team'));

      // Fill form
      fireEvent.change(screen.getByLabelText('Team Name'), {
        target: { value: 'New Team' }
      });
      fireEvent.change(screen.getByLabelText('Team Slug'), {
        target: { value: 'new-team' }
      });
      fireEvent.change(screen.getByLabelText('Description'), {
        target: { value: 'A new team' }
      });

      fireEvent.click(screen.getByText('Create Team'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Success',
          description: 'Team created successfully'
        });
      });
    });

    it('handles team creation error', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ error: 'Team creation failed' })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Create Team')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Team'));

      // Fill form
      fireEvent.change(screen.getByLabelText('Team Name'), {
        target: { value: 'New Team' }
      });
      fireEvent.change(screen.getByLabelText('Team Slug'), {
        target: { value: 'new-team' }
      });

      fireEvent.click(screen.getByText('Create Team'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error',
          description: 'Team creation failed',
          variant: 'destructive'
        });
      });
    });
  });

  describe('Team Selection and Display', () => {
    beforeEach(async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeams })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeamMembers })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockInvitations })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockResources })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockActivity })
        });
    });

    it('displays team list when teams exist', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Your Teams')).toBeInTheDocument();
        expect(screen.getByText('Test Team')).toBeInTheDocument();
        expect(screen.getByText('test-team')).toBeInTheDocument();
      });
    });

    it('selects first team by default and shows team details', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Test Team')).toBeInTheDocument();
        expect(screen.getByText('A test team')).toBeInTheDocument();
      });
    });

    it('shows team overview with statistics', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Total Members')).toBeInTheDocument();
        expect(screen.getByText('Pending Invitations')).toBeInTheDocument();
        expect(screen.getByText('Shared Resources')).toBeInTheDocument();
        expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      });
    });
  });

  describe('Team Members Management', () => {
    beforeEach(async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeams })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeamMembers })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockInvitations })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockResources })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockActivity })
        });
    });

    it('displays team members in members tab', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Members')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Members'));

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
        expect(screen.getByText('User Two')).toBeInTheDocument();
        expect(screen.getByText('user1@example.com')).toBeInTheDocument();
        expect(screen.getByText('user2@example.com')).toBeInTheDocument();
      });
    });

    it('shows role badges for team members', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Members'));
      });

      await waitFor(() => {
        expect(screen.getByText('Owner')).toBeInTheDocument();
        expect(screen.getByText('Member')).toBeInTheDocument();
      });
    });

    it('handles member removal', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ message: 'Member removed successfully' })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Members'));
      });

      await waitFor(() => {
        const removeButtons = screen.getAllByRole('button');
        const removeButton = removeButtons.find(button => 
          button.querySelector('svg')?.classList.contains('h-4')
        );
        if (removeButton) {
          fireEvent.click(removeButton);
        }
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Success',
          description: 'Member removed successfully'
        });
      });
    });
  });

  describe('Member Invitations', () => {
    beforeEach(async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeams })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeamMembers })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockInvitations })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockResources })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockActivity })
        });
    });

    it('opens invite member dialog when button is clicked', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Invite Member')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Invite Member'));

      expect(screen.getByText('Invite Team Member')).toBeInTheDocument();
      expect(screen.getByText('Send an invitation to join your team')).toBeInTheDocument();
    });

    it('handles member invitation successfully', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ data: { id: 'invitation-1' } })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Invite Member')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Invite Member'));

      // Fill form
      fireEvent.change(screen.getByLabelText('Email Address'), {
        target: { value: 'newmember@example.com' }
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Success',
          description: 'Invitation sent successfully'
        });
      });
    });

    it('displays invitations in invitations tab', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Invitations')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Invitations'));

      await waitFor(() => {
        expect(screen.getByText('invite@example.com')).toBeInTheDocument();
        expect(screen.getByText('Member')).toBeInTheDocument();
        expect(screen.getByText('pending')).toBeInTheDocument();
      });
    });

    it('handles invitation cancellation', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ message: 'Invitation cancelled' })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Invitations'));
      });

      await waitFor(() => {
        const cancelButtons = screen.getAllByRole('button');
        const cancelButton = cancelButtons.find(button => 
          button.querySelector('svg')?.classList.contains('h-4')
        );
        if (cancelButton) {
          fireEvent.click(cancelButton);
        }
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Success',
          description: 'Invitation cancelled successfully'
        });
      });
    });
  });

  describe('Resource Sharing', () => {
    beforeEach(async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeams })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeamMembers })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockInvitations })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockResources })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockActivity })
        });
    });

    it('opens share resource dialog when button is clicked', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Share Resource')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Share Resource'));

      expect(screen.getByText('Share Resource')).toBeInTheDocument();
      expect(screen.getByText('Share a resource with your team')).toBeInTheDocument();
    });

    it('handles resource sharing successfully', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ data: { id: 'resource-1' } })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Share Resource')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Share Resource'));

      // Fill form
      fireEvent.change(screen.getByLabelText('Resource ID'), {
        target: { value: 'assistant-123' }
      });
      fireEvent.change(screen.getByLabelText('Resource Name'), {
        target: { value: 'My Assistant' }
      });

      fireEvent.click(screen.getByText('Share Resource'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Success',
          description: 'Resource shared successfully'
        });
      });
    });

    it('displays shared resources in resources tab', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Resources')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Resources'));

      await waitFor(() => {
        expect(screen.getByText('Test Assistant')).toBeInTheDocument();
        expect(screen.getByText('assistant')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(<TeamManagement />);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error',
          description: 'Failed to load teams',
          variant: 'destructive'
        });
      });
    });

    it('handles API errors gracefully', async () => {
      (global.fetch as any).mockResolvedValue({
        json: () => Promise.resolve({ error: 'API error' })
      });

      render(<TeamManagement />);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error',
          description: 'Failed to load teams',
          variant: 'destructive'
        });
      });
    });
  });

  describe('Role and Status Icons', () => {
    it('displays correct role icons', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Members'));
      });

      // Check that role icons are rendered (they should be present as SVG elements)
      await waitFor(() => {
        const svgElements = document.querySelectorAll('svg');
        expect(svgElements.length).toBeGreaterThan(0);
      });
    });

    it('displays correct status icons', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Members'));
      });

      // Check that status indicators are present
      await waitFor(() => {
        expect(screen.getByText('active')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    beforeEach(async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeams })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockTeamMembers })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockInvitations })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockResources })
        })
        .mockResolvedValueOnce({
          json: () => Promise.resolve({ data: mockActivity })
        });
    });

    it('switches between tabs correctly', async () => {
      render(<TeamManagement />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Members')).toBeInTheDocument();
        expect(screen.getByText('Invitations')).toBeInTheDocument();
        expect(screen.getByText('Resources')).toBeInTheDocument();
      });

      // Click on Members tab
      fireEvent.click(screen.getByText('Members'));
      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument();
      });

      // Click on Invitations tab
      fireEvent.click(screen.getByText('Invitations'));
      await waitFor(() => {
        expect(screen.getByText('invite@example.com')).toBeInTheDocument();
      });

      // Click on Resources tab
      fireEvent.click(screen.getByText('Resources'));
      await waitFor(() => {
        expect(screen.getByText('Test Assistant')).toBeInTheDocument();
      });

      // Click back to Overview tab
      fireEvent.click(screen.getByText('Overview'));
      await waitFor(() => {
        expect(screen.getByText('Total Members')).toBeInTheDocument();
      });
    });
  });
});
