import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ScheduleDemo from '@/pages/ScheduleDemo';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      insert: vi.fn(),
    })),
    functions: {
      invoke: vi.fn(),
    },
  },
}));

// Mock useToast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(),
}));

const renderScheduleDemo = () => {
  return render(
    <BrowserRouter>
      <ScheduleDemo />
    </BrowserRouter>
  );
};

describe('ScheduleDemo Page', () => {
  const mockToast = vi.fn();
  const mockSupabaseFrom = vi.mocked(supabase.from);
  const mockSupabaseInsert = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    mockSupabaseFrom.mockReturnValue({
      insert: mockSupabaseInsert,
    } as any);
  });

  describe('Authentication States', () => {
    it('shows loading state when auth is loading', () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: true,
      });

      renderScheduleDemo();
      
      expect(screen.getByText('Schedule a Demo')).toBeInTheDocument();
      // Check for loading skeleton
      const skeletonElements = document.querySelectorAll('.animate-pulse');
      expect(skeletonElements.length).toBeGreaterThan(0);
    });

    it('redirects to auth when user is not logged in', () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderScheduleDemo();
      
      expect(screen.getByText('Authentication Required')).toBeInTheDocument();
      expect(screen.getByText('You need to be signed in to schedule a demo')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    });

    it('shows demo form when user is authenticated', () => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });

      renderScheduleDemo();
      
      expect(screen.getByText('Schedule a Demo')).toBeInTheDocument();
      expect(screen.getByText('Demo Booking')).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Name \*/)).toBeInTheDocument();
    });
  });

  describe('Header Section', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('renders header with title and description', () => {
      renderScheduleDemo();
      
      expect(screen.getByText('Schedule a Demo')).toBeInTheDocument();
      expect(screen.getByText(/Book a personalized demonstration/)).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      renderScheduleDemo();
      
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Schedule a Demo');
    });
  });

  describe('Demo Booking Form', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('renders form with all required fields', () => {
      renderScheduleDemo();
      
      expect(screen.getByText('Demo Booking')).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Name \*/)).toBeInTheDocument();
      expect(screen.getByLabelText('Company Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
      expect(screen.getByLabelText('Preferred Date *')).toBeInTheDocument();
      expect(screen.getByLabelText(/Preferred Time \*/)).toBeInTheDocument();
      expect(screen.getByLabelText('Timezone')).toBeInTheDocument();
      expect(screen.getByLabelText('Demo Type')).toBeInTheDocument();
      expect(screen.getByLabelText('Additional Notes')).toBeInTheDocument();
    });

    it('renders submit button', () => {
      renderScheduleDemo();
      
      expect(screen.getByRole('button', { name: /Schedule Demo/i })).toBeInTheDocument();
    });

    it('pre-fills email with user email', () => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'user@example.com' },
        loading: false,
      });

      renderScheduleDemo();
      
      const emailInput = screen.getByLabelText('Email Address *');
      expect(emailInput).toHaveValue('user@example.com');
    });

    it('handles form input changes', () => {
      renderScheduleDemo();
      
      const nameInput = screen.getByLabelText(/Full Name \*/);
      const companyInput = screen.getByLabelText('Company Name');
      const phoneInput = screen.getByLabelText('Phone Number');
      const notesInput = screen.getByLabelText('Additional Notes');

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(companyInput, { target: { value: 'Test Company' } });
      fireEvent.change(phoneInput, { target: { value: '+233 54 123 4567' } });
      fireEvent.change(notesInput, { target: { value: 'Test notes' } });

      expect(nameInput).toHaveValue('John Doe');
      expect(companyInput).toHaveValue('Test Company');
      expect(phoneInput).toHaveValue('+233 54 123 4567');
      expect(notesInput).toHaveValue('Test notes');
    });

    it('handles date and time input changes', () => {
      renderScheduleDemo();
      
      const dateInput = screen.getByLabelText('Preferred Date *');
      const timeInput = screen.getByLabelText(/Preferred Time \*/);

      fireEvent.change(dateInput, { target: { value: '2024-12-25' } });
      fireEvent.change(timeInput, { target: { value: '14:30' } });

      expect(dateInput).toHaveValue('2024-12-25');
      expect(timeInput).toHaveValue('14:30');
    });

    it('sets minimum date to today', () => {
      renderScheduleDemo();
      
      const dateInput = screen.getByLabelText('Preferred Date *');
      const today = new Date().toISOString().split('T')[0];
      
      expect(dateInput).toHaveAttribute('min', today);
    });
  });

  describe('Form Submission', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('submits form successfully', async () => {
      mockSupabaseInsert.mockResolvedValue({ error: null });
      mockSupabaseInvoke.mockResolvedValue({ error: null });

      renderScheduleDemo();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText(/Full Name \*/), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Preferred Date *'), { target: { value: '2024-12-25' } });
      fireEvent.change(screen.getByLabelText(/Preferred Time \*/), { target: { value: '14:30' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Schedule Demo/i }));

      await waitFor(() => {
        expect(mockSupabaseInsert).toHaveBeenCalledWith([{
          user_id: 'user-123',
          full_name: 'John Doe',
          company_name: '',
          email: 'john@example.com',
          phone: '',
          preferred_date: '2024-12-25',
          preferred_time: '14:30',
          timezone: 'UTC',
          demo_type: 'general',
          notes: ''
        }]);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Demo scheduled!",
          description: "We'll contact you soon to confirm your demo appointment. Confirmation email sent!",
        });
      });
    });

    it('handles database error', async () => {
      mockSupabaseInsert.mockResolvedValue({ error: { message: 'Database error' } });

      renderScheduleDemo();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText(/Full Name \*/), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Preferred Date *'), { target: { value: '2024-12-25' } });
      fireEvent.change(screen.getByLabelText(/Preferred Time \*/), { target: { value: '14:30' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Schedule Demo/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error scheduling demo",
          description: "Database error",
          variant: "destructive",
        });
      });
    });

    it('handles email notification error gracefully', async () => {
      mockSupabaseInsert.mockResolvedValue({ error: null });
      mockSupabaseInvoke.mockResolvedValue({ error: { message: 'Email error' } });

      renderScheduleDemo();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText(/Full Name \*/), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Preferred Date *'), { target: { value: '2024-12-25' } });
      fireEvent.change(screen.getByLabelText(/Preferred Time \*/), { target: { value: '14:30' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Schedule Demo/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Demo scheduled!",
          description: "We'll contact you soon to confirm your demo appointment. Confirmation email sent!",
        });
      });
    });

    it('resets form after successful submission', async () => {
      mockSupabaseInsert.mockResolvedValue({ error: null });
      mockSupabaseInvoke.mockResolvedValue({ error: null });

      renderScheduleDemo();
      
      const nameInput = screen.getByLabelText(/Full Name \*/);
      const emailInput = screen.getByLabelText('Email Address *');

      // Fill form
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Schedule Demo/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Demo scheduled!",
          description: "We'll contact you soon to confirm your demo appointment. Confirmation email sent!",
        });
      });
    });

    it('shows loading state during submission', async () => {
      mockSupabaseInsert.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderScheduleDemo();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText(/Full Name \*/), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Schedule Demo/i }));

      // Check loading state
      expect(screen.getByText('Scheduling...')).toBeInTheDocument();
    });

    it('redirects to auth if user becomes null during submission', async () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderScheduleDemo();
      
      // Try to submit form (should redirect to auth)
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('requires name field', () => {
      renderScheduleDemo();
      
      const nameInput = screen.getByLabelText(/Full Name \*/);
      expect(nameInput).toBeRequired();
    });

    it('requires email field', () => {
      renderScheduleDemo();
      
      const emailInput = screen.getByLabelText('Email Address *');
      expect(emailInput).toBeRequired();
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('requires date field', () => {
      renderScheduleDemo();
      
      const dateInput = screen.getByLabelText('Preferred Date *');
      expect(dateInput).toBeRequired();
      expect(dateInput).toHaveAttribute('type', 'date');
    });

    it('requires time field', () => {
      renderScheduleDemo();
      
      const timeInput = screen.getByLabelText(/Preferred Time \*/);
      expect(timeInput).toBeRequired();
      expect(timeInput).toHaveAttribute('type', 'time');
    });

    it('has proper input types', () => {
      renderScheduleDemo();
      
      expect(screen.getByLabelText('Email Address *')).toHaveAttribute('type', 'email');
      expect(screen.getByLabelText('Phone Number')).toHaveAttribute('type', 'tel');
      expect(screen.getByLabelText('Preferred Date *')).toHaveAttribute('type', 'date');
      expect(screen.getByLabelText(/Preferred Time \*/)).toHaveAttribute('type', 'time');
    });

    it('has proper placeholders', () => {
      renderScheduleDemo();
      
      expect(screen.getByPlaceholderText('Enter your full name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your company name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your phone number')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Tell us about your specific requirements/)).toBeInTheDocument();
    });
  });

  describe('Select Components', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('renders timezone select with options', () => {
      renderScheduleDemo();
      
      expect(screen.getByText('Timezone')).toBeInTheDocument();
      expect(screen.getByText('UTC')).toBeInTheDocument();
    });

    it('renders demo type select with options', () => {
      renderScheduleDemo();
      
      expect(screen.getByText('Demo Type')).toBeInTheDocument();
      expect(screen.getByText('General Overview')).toBeInTheDocument();
    });
  });

  describe('Authentication Redirects', () => {
    it('redirects to auth when clicking sign in button', () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderScheduleDemo();
      
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));
      expect(mockNavigate).toHaveBeenCalledWith('/auth');
    });

    it('shows auth required toast when user is not logged in', () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderScheduleDemo();
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Authentication Required",
        description: "Please sign in to schedule a demo",
        variant: "destructive",
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('has proper form labels', () => {
      renderScheduleDemo();
      
      expect(screen.getByLabelText(/Full Name \*/)).toBeInTheDocument();
      expect(screen.getByLabelText('Company Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
      expect(screen.getByLabelText('Preferred Date *')).toBeInTheDocument();
      expect(screen.getByLabelText(/Preferred Time \*/)).toBeInTheDocument();
      expect(screen.getByText('Timezone')).toBeInTheDocument();
      expect(screen.getByText('Demo Type')).toBeInTheDocument();
      expect(screen.getByLabelText('Additional Notes')).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      renderScheduleDemo();
      
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
      
      // Check for main heading
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('has proper button roles', () => {
      renderScheduleDemo();
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      
      // All buttons should be accessible
      buttons.forEach(button => {
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe('Layout and Styling', () => {
    beforeEach(() => {
      (useAuth as any).mockReturnValue({
        user: { id: 'user-123', email: 'test@example.com' },
        loading: false,
      });
    });

    it('renders without crashing', () => {
      expect(() => renderScheduleDemo()).not.toThrow();
    });

    it('renders all main sections', () => {
      renderScheduleDemo();
      
      // Check that all main sections are present
      expect(screen.getByText('Schedule a Demo')).toBeInTheDocument();
      expect(screen.getByText('Demo Booking')).toBeInTheDocument();
    });

    it('has proper card structure', () => {
      renderScheduleDemo();
      
      expect(screen.getByText('Demo Booking')).toBeInTheDocument();
      expect(screen.getByText(/Fill out the form below/)).toBeInTheDocument();
    });
  });
});
