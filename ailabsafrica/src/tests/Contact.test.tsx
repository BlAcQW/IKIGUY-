import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Contact from '@/pages/Contact';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

// Mock Supabase client
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    functions: {
      invoke: vi.fn(),
    },
  },
}));

// Mock useToast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(),
}));

const renderContact = () => {
  return render(
    <BrowserRouter>
      <Contact />
    </BrowserRouter>
  );
};

describe('Contact Page', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
  });

  describe('Header Section', () => {
    it('renders header with title and description', () => {
      renderContact();
      
      expect(screen.getByText('Get in Touch')).toBeInTheDocument();
      expect(screen.getByText(/Ready to transform your business with KasaAI/)).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      renderContact();
      
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Get in Touch');
    });
  });

  describe('Contact Information Section', () => {
    it('renders contact information cards', () => {
      renderContact();
      
      expect(screen.getByText('Contact Information')).toBeInTheDocument();
      expect(screen.getByText('Phone')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Banking')).toBeInTheDocument();
      
      // Check for Company in contact info (not form label)
      const companyElements = screen.getAllByText('Company');
      expect(companyElements.length).toBeGreaterThan(0);
    });

    it('displays company information correctly', () => {
      renderContact();
      
      expect(screen.getByText('AI Labs Africa Ltd')).toBeInTheDocument();
      expect(screen.getByText('124 Pound Street, North Dome')).toBeInTheDocument();
    });

    it('displays phone number correctly', () => {
      renderContact();
      
      expect(screen.getByText('+233 54 569 9663')).toBeInTheDocument();
    });

    it('displays email address correctly', () => {
      renderContact();
      
      expect(screen.getByText('kasaai@ikieguy.com')).toBeInTheDocument();
    });

    it('displays banking information correctly', () => {
      renderContact();
      
      expect(screen.getByText('Stanbic Bank')).toBeInTheDocument();
      expect(screen.getByText('Acc No: 9040010244212')).toBeInTheDocument();
    });

    it('displays quick response guarantee', () => {
      renderContact();
      
      expect(screen.getByText('Quick Response Guarantee')).toBeInTheDocument();
      expect(screen.getByText(/We respond to all inquiries within 24 hours/)).toBeInTheDocument();
    });
  });

  describe('Contact Form', () => {
    it('renders form with all required fields', () => {
      renderContact();
      
      expect(screen.getByText('Send us a Message')).toBeInTheDocument();
      expect(screen.getByLabelText('Full Name *')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
      expect(screen.getByLabelText('Company')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
      expect(screen.getByLabelText('Subject *')).toBeInTheDocument();
      expect(screen.getByLabelText('Message *')).toBeInTheDocument();
    });

    it('renders submit button', () => {
      renderContact();
      
      expect(screen.getByRole('button', { name: /Send Message/i })).toBeInTheDocument();
    });

    it('handles form input changes', () => {
      renderContact();
      
      const nameInput = screen.getByLabelText('Full Name *');
      const emailInput = screen.getByLabelText('Email Address *');
      const subjectInput = screen.getByLabelText('Subject *');
      const messageInput = screen.getByLabelText('Message *');

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(subjectInput, { target: { value: 'Test Subject' } });
      fireEvent.change(messageInput, { target: { value: 'Test message content' } });

      expect(nameInput).toHaveValue('John Doe');
      expect(emailInput).toHaveValue('john@example.com');
      expect(subjectInput).toHaveValue('Test Subject');
      expect(messageInput).toHaveValue('Test message content');
    });

    it('handles optional field input changes', () => {
      renderContact();
      
      const companyInput = screen.getByLabelText('Company');
      const phoneInput = screen.getByLabelText('Phone Number');

      fireEvent.change(companyInput, { target: { value: 'Test Company' } });
      fireEvent.change(phoneInput, { target: { value: '+233 54 123 4567' } });

      expect(companyInput).toHaveValue('Test Company');
      expect(phoneInput).toHaveValue('+233 54 123 4567');
    });
  });

  describe('Form Submission', () => {
    it('submits form successfully', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { success: true },
        error: null,
      } as any);

      renderContact();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Subject *'), { target: { value: 'Test Subject' } });
      fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'Test message' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Send Message/i }));

      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('contact-form', {
          body: {
            name: 'John Doe',
            email: 'john@example.com',
            company: '',
            phone: '',
            subject: 'Test Subject',
            message: 'Test message'
          }
        });
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Message sent successfully!",
          description: "We'll get back to you within 24 hours. Check your email for confirmation.",
        });
      });
    });

    it('handles submission error', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: null,
        error: { message: 'Network error' },
      } as any);

      renderContact();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Subject *'), { target: { value: 'Test Subject' } });
      fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'Test message' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Send Message/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error sending message",
          description: "Network error",
          variant: "destructive"
        });
      });
    });

    it('handles API error response', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { success: false, error: 'Invalid email format' },
        error: null,
      } as any);

      renderContact();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Subject *'), { target: { value: 'Test Subject' } });
      fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'Test message' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Send Message/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Error sending message",
          description: "Invalid email format",
          variant: "destructive"
        });
      });
    });

    it('resets form after successful submission', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { success: true },
        error: null,
      } as any);

      renderContact();
      
      const nameInput = screen.getByLabelText('Full Name *');
      const emailInput = screen.getByLabelText('Email Address *');
      const subjectInput = screen.getByLabelText('Subject *');
      const messageInput = screen.getByLabelText('Message *');

      // Fill form
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(subjectInput, { target: { value: 'Test Subject' } });
      fireEvent.change(messageInput, { target: { value: 'Test message' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Send Message/i }));

      await waitFor(() => {
        expect(nameInput).toHaveValue('');
        expect(emailInput).toHaveValue('');
        expect(subjectInput).toHaveValue('');
        expect(messageInput).toHaveValue('');
      });
    });

    it('shows loading state during submission', async () => {
      mockSupabaseInvoke.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderContact();
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText('Full Name *'), { target: { value: 'John Doe' } });
      fireEvent.change(screen.getByLabelText('Email Address *'), { target: { value: 'john@example.com' } });
      fireEvent.change(screen.getByLabelText('Subject *'), { target: { value: 'Test Subject' } });
      fireEvent.change(screen.getByLabelText('Message *'), { target: { value: 'Test message' } });

      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /Send Message/i }));

      // Check loading state
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sending.../i })).toBeDisabled();
    });
  });

  describe('Form Validation', () => {
    it('requires name field', () => {
      renderContact();
      
      const nameInput = screen.getByLabelText('Full Name *');
      expect(nameInput).toBeRequired();
    });

    it('requires email field', () => {
      renderContact();
      
      const emailInput = screen.getByLabelText('Email Address *');
      expect(emailInput).toBeRequired();
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('requires subject field', () => {
      renderContact();
      
      const subjectInput = screen.getByLabelText('Subject *');
      expect(subjectInput).toBeRequired();
    });

    it('requires message field', () => {
      renderContact();
      
      const messageInput = screen.getByLabelText('Message *');
      expect(messageInput).toBeRequired();
    });

    it('has proper input types', () => {
      renderContact();
      
      expect(screen.getByLabelText('Email Address *')).toHaveAttribute('type', 'email');
      expect(screen.getByLabelText('Phone Number')).toHaveAttribute('type', 'tel');
    });

    it('has proper placeholders', () => {
      renderContact();
      
      expect(screen.getByPlaceholderText('Your full name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('your.email@company.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Your company name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('+233 XX XXX XXXX')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('What would you like to discuss?')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Tell us about your project/)).toBeInTheDocument();
    });
  });

  describe('CTA Section', () => {
    it('renders CTA section with buttons', () => {
      renderContact();
      
      expect(screen.getByText('Ready to Get Started?')).toBeInTheDocument();
      expect(screen.getByText(/Join hundreds of businesses/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Schedule a Demo Call/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /View Pricing Plans/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderContact();
      
      expect(screen.getByLabelText('Full Name *')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument();
      expect(screen.getByLabelText('Company')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
      expect(screen.getByLabelText('Subject *')).toBeInTheDocument();
      expect(screen.getByLabelText('Message *')).toBeInTheDocument();
    });

    it('has proper heading structure', () => {
      renderContact();
      
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
      
      // Check for main heading
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('has proper button roles', () => {
      renderContact();
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      
      // All buttons should be accessible
      buttons.forEach(button => {
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe('Layout and Styling', () => {
    it('renders without crashing', () => {
      expect(() => renderContact()).not.toThrow();
    });

    it('renders all main sections', () => {
      renderContact();
      
      // Check that all main sections are present
      expect(screen.getByText('Get in Touch')).toBeInTheDocument();
      expect(screen.getByText('Contact Information')).toBeInTheDocument();
      expect(screen.getByText('Send us a Message')).toBeInTheDocument();
      expect(screen.getByText('Ready to Get Started?')).toBeInTheDocument();
    });
  });
});
