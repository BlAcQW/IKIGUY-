import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DemoComments from '@/components/DemoComments';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';

// Mock dependencies
vi.mock('@/components/ui/use-toast');
vi.mock('@/contexts/AuthContext');
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    functions: {
      invoke: vi.fn()
    }
  }
}));

const mockToast = vi.fn();
const mockSupabase = {
  functions: {
    invoke: vi.fn()
  }
};

const mockUser = {
  id: 'user-123',
  email: 'test@example.com'
};

const mockComments = [
  {
    comment_id: 'comment-1',
    user_name: 'John Doe',
    user_email: 'john@example.com',
    rating: 5,
    comment_text: 'Great demo! Very helpful.',
    created_at: '2024-01-15T10:00:00Z',
    replies: [
      {
        id: 'reply-1',
        reply_text: 'Thank you for the feedback!',
        is_public: true,
        created_at: '2024-01-15T11:00:00Z',
        user_id: 'user-123'
      }
    ]
  },
  {
    comment_id: 'comment-2',
    user_name: 'Jane Smith',
    rating: 4,
    comment_text: 'Good demo, but could be improved.',
    created_at: '2024-01-15T09:00:00Z',
    replies: []
  }
];

const mockStats = {
  total_comments: 2,
  approved_comments: 2,
  average_rating: 4.5,
  rating_distribution: {
    '1': 0,
    '2': 0,
    '3': 0,
    '4': 1,
    '5': 1
  }
};

describe('DemoComments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    (useToast as any).mockReturnValue({
      toast: mockToast
    });
    
    (useAuth as any).mockReturnValue({
      user: mockUser
    });
    
    // Mock successful API calls
    mockSupabase.functions.invoke.mockResolvedValue({
      data: {
        comments: mockComments,
        stats: mockStats
      },
      error: null
    });
  });

  it('renders component with header and add comment button', () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    expect(screen.getByText('Comments & Feedback')).toBeInTheDocument();
    expect(screen.getByText('Share your thoughts about this Customer Support demo')).toBeInTheDocument();
    expect(screen.getByText('Add Comment')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    expect(screen.getByText('Loading comments...')).toBeInTheDocument();
  });

  it('displays comments after loading', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Great demo! Very helpful.')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Good demo, but could be improved.')).toBeInTheDocument();
    });
  });

  it('displays star ratings correctly', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const stars = screen.getAllByRole('button').filter(button => 
        button.querySelector('svg[class*="fill-yellow-400"]')
      );
      expect(stars).toHaveLength(9); // 5 stars for first comment + 4 stars for second comment
    });
  });

  it('shows empty state when no comments', async () => {
    mockSupabase.functions.invoke.mockResolvedValue({
      data: { comments: [], stats: { ...mockStats, total_comments: 0, approved_comments: 0 } },
      error: null
    });

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No comments yet')).toBeInTheDocument();
      expect(screen.getByText('Be the first to share your thoughts about this demo!')).toBeInTheDocument();
      expect(screen.getByText('Add First Comment')).toBeInTheDocument();
    });
  });

  it('opens comment form dialog when add comment button is clicked', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    expect(screen.getByText('Add Your Comment')).toBeInTheDocument();
    expect(screen.getByText('Share your feedback about the Test Assistant demo')).toBeInTheDocument();
  });

  it('submits comment successfully', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { comments: mockComments, stats: mockStats },
        error: null
      })
      .mockResolvedValueOnce({
        data: { message: 'Comment submitted successfully' },
        error: null
      });

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    // Fill form
    fireEvent.change(screen.getByLabelText('Name *'), {
      target: { value: 'Test User' }
    });
    fireEvent.change(screen.getByLabelText('Comment *'), {
      target: { value: 'This is a test comment' }
    });

    // Submit form
    fireEvent.click(screen.getByText('Submit Comment'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('demo-comments', {
        body: {
          action: 'create_comment',
          demo_id: 'demo-123',
          user_name: 'Test User',
          user_email: undefined,
          rating: undefined,
          comment_text: 'This is a test comment',
          user_agent: navigator.userAgent
        }
      });
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Success',
      description: 'Comment submitted successfully'
    });
  });

  it('validates required fields when submitting comment', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    // Try to submit without filling required fields
    fireEvent.click(screen.getByText('Submit Comment'));

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Validation Error',
      description: 'Name and comment are required',
      variant: 'destructive'
    });
  });

  it('handles comment submission error', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { comments: mockComments, stats: mockStats },
        error: null
      })
      .mockRejectedValueOnce(new Error('API Error'));

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Name *'), {
      target: { value: 'Test User' }
    });
    fireEvent.change(screen.getByLabelText('Comment *'), {
      target: { value: 'This is a test comment' }
    });
    fireEvent.click(screen.getByText('Submit Comment'));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to submit comment',
        variant: 'destructive'
      });
    });
  });

  it('shows reply form when reply button is clicked', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const replyButtons = screen.getAllByText('Reply');
      fireEvent.click(replyButtons[0]);
    });

    expect(screen.getByPlaceholderText('Write your reply...')).toBeInTheDocument();
    expect(screen.getByLabelText('Make reply public')).toBeInTheDocument();
  });

  it('submits reply successfully', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { comments: mockComments, stats: mockStats },
        error: null
      })
      .mockResolvedValueOnce({
        data: { message: 'Reply added successfully' },
        error: null
      });

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const replyButtons = screen.getAllByText('Reply');
      fireEvent.click(replyButtons[0]);
    });

    // Fill reply form
    fireEvent.change(screen.getByPlaceholderText('Write your reply...'), {
      target: { value: 'This is a test reply' }
    });

    // Submit reply
    fireEvent.click(screen.getByText('Reply'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('demo-comments', {
        body: {
          action: 'add_reply',
          comment_id: 'comment-1',
          reply_text: 'This is a test reply',
          is_public: true
        }
      });
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Success',
      description: 'Reply added successfully'
    });
  });

  it('validates reply text when submitting reply', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const replyButtons = screen.getAllByText('Reply');
      fireEvent.click(replyButtons[0]);
    });

    // Try to submit empty reply
    fireEvent.click(screen.getByText('Reply'));

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Validation Error',
      description: 'Reply text is required',
      variant: 'destructive'
    });
  });

  it('shows moderation options for authenticated users', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const moreButtons = screen.getAllByRole('button').filter(button => 
        button.querySelector('svg[class*="MoreHorizontal"]')
      );
      expect(moreButtons.length).toBeGreaterThan(0);
    });
  });

  it('approves comment when approve button is clicked', async () => {
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { comments: mockComments, stats: mockStats },
        error: null
      })
      .mockResolvedValueOnce({
        data: { message: 'Comment approved successfully' },
        error: null
      });

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const moreButtons = screen.getAllByRole('button').filter(button => 
        button.querySelector('svg[class*="MoreHorizontal"]')
      );
      fireEvent.click(moreButtons[0]);
    });

    // Click approve button
    fireEvent.click(screen.getByText('Approve'));

    await waitFor(() => {
      expect(mockSupabase.functions.invoke).toHaveBeenCalledWith('demo-comments', {
        body: {
          action: 'approve_comment',
          comment_id: 'comment-1',
          is_approved: true
        }
      });
    });
  });

  it('shows comment statistics dialog', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Stats (2)'));
    });

    expect(screen.getByText('Comment Statistics')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Total comments
    expect(screen.getByText('2')).toBeInTheDocument(); // Approved comments
    expect(screen.getByText('4.5')).toBeInTheDocument(); // Average rating
  });

  it('displays replies correctly', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Thank you for the feedback!')).toBeInTheDocument();
      expect(screen.getByText('User • about 1 hour ago')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockSupabase.functions.invoke.mockRejectedValue(new Error('API Error'));

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load comments',
        variant: 'destructive'
      });
    });
  });

  it('calls onCommentChange callback when comment is submitted', async () => {
    const mockOnCommentChange = vi.fn();
    
    mockSupabase.functions.invoke
      .mockResolvedValueOnce({
        data: { comments: mockComments, stats: mockStats },
        error: null
      })
      .mockResolvedValueOnce({
        data: { message: 'Comment submitted successfully' },
        error: null
      });

    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
        onCommentChange={mockOnCommentChange}
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    // Fill and submit form
    fireEvent.change(screen.getByLabelText('Name *'), {
      target: { value: 'Test User' }
    });
    fireEvent.change(screen.getByLabelText('Comment *'), {
      target: { value: 'This is a test comment' }
    });
    fireEvent.click(screen.getByText('Submit Comment'));

    await waitFor(() => {
      expect(mockOnCommentChange).toHaveBeenCalled();
    });
  });

  it('handles rating selection in comment form', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('Add Comment'));
    });

    // Click on 4th star
    const stars = screen.getAllByRole('button').filter(button => 
      button.querySelector('svg[class*="text-gray-300"]')
    );
    fireEvent.click(stars[3]); // 4th star

    // Verify the star is now filled
    expect(stars[3].querySelector('svg[class*="fill-yellow-400"]')).toBeInTheDocument();
  });

  it('handles public/private reply toggle', async () => {
    render(
      <DemoComments
        demoId="demo-123"
        assistantName="Test Assistant"
        assistantType="Customer Support"
      />
    );

    await waitFor(() => {
      const replyButtons = screen.getAllByText('Reply');
      fireEvent.click(replyButtons[0]);
    });

    const publicCheckbox = screen.getByLabelText('Make reply public');
    expect(publicCheckbox).toBeChecked();

    fireEvent.click(publicCheckbox);
    expect(publicCheckbox).not.toBeChecked();
  });
});
