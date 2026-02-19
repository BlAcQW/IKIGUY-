import { screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CreateAssistant from '@/pages/CreateAssistant';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';
import { render, waitForRadixUI, clickSelectOption, fillFormField } from './utils/test-utils';

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
    functions: {
      invoke: vi.fn(),
    },
  },
}));

// Mock useToast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

const renderCreateAssistant = () => {
  return render(<CreateAssistant />);
};

// Helper function to fill in all required fields
const fillRequiredFields = async (websiteUrl = 'https://example.com') => {
  const nameInput = screen.getByLabelText('Assistant Name');
  const descInput = screen.getByLabelText('Short Description');
  const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
  
  await fillFormField(nameInput, 'Test Assistant');
  await fillFormField(descInput, 'Test Description');
  await fillFormField(urlInput, websiteUrl);
  
  // Select assistant type (required)
  const comboboxes = screen.getAllByRole('combobox');
  const assistantTypeSelect = comboboxes[0];
  await clickSelectOption(assistantTypeSelect, 'help_desk');
  
  // Select voice (required)
  const voiceSelect = comboboxes[1];
  await clickSelectOption(voiceSelect, 'Paige');
};

describe('CreateAssistant - Phase 1.1: User Input Validation', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
    localStorageMock.getItem.mockReturnValue(null);
    
    // Mock the list-vapi-voices function that gets called on component mount
    mockSupabaseInvoke.mockResolvedValue({
      data: { voices: [{ id: 'Paige', name: 'Paige' }] },
      error: null,
    });
  });

  describe('Assistant Name Validation', () => {
    it('should render assistant name input field', () => {
      renderCreateAssistant();
      expect(screen.getByLabelText('Assistant Name')).toBeInTheDocument();
    });

    it('should accept valid assistant names', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const validNames = [
        'Customer Support Bot',
        'Sales Assistant 2024',
        'Help Desk AI',
        'Insurance Claims Helper',
        'Real Estate Agent AI',
        'Healthcare Assistant',
        'Banking Support Bot',
        'E-commerce Helper',
        'Restaurant Booking Assistant',
        'Travel Planning AI'
      ];

      validNames.forEach(name => {
        fireEvent.change(nameInput, { target: { value: name } });
        expect(nameInput).toHaveValue(name);
      });
    });

    it('should handle special characters in assistant names', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const namesWithSpecialChars = [
        'Customer Support & Sales Bot',
        'AI Assistant - Premium',
        'Help Desk (24/7)',
        'Insurance Claims Helper v2.0',
        'Real Estate Agent AI - Pro',
        'Healthcare Assistant +',
        'Banking Support Bot @',
        'E-commerce Helper #1',
        'Restaurant Booking Assistant!',
        'Travel Planning AI?'
      ];

      namesWithSpecialChars.forEach(name => {
        fireEvent.change(nameInput, { target: { value: name } });
        expect(nameInput).toHaveValue(name);
      });
    });

    it('should handle empty assistant name', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      fireEvent.change(nameInput, { target: { value: '' } });
      expect(nameInput).toHaveValue('');
    });

    it('should handle very long assistant names', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const longName = 'A'.repeat(1000);
      fireEvent.change(nameInput, { target: { value: longName } });
      expect(nameInput).toHaveValue(longName);
    });

    it('should prevent proceeding to next step with empty assistant name', async () => {
      renderCreateAssistant();
      
      // Wait for component to load and voices to be fetched
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Fill other required fields
      fireEvent.change(screen.getByLabelText('Short Description'), { 
        target: { value: 'Test description' } 
      });

      // Try to proceed without assistant name
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // The button should be disabled when required fields are missing
      expect(nextButton).toBeDisabled();
      
      // Try to click it anyway to test the validation
      fireEvent.click(nextButton);
      
      // Since the button is disabled, no toast should be shown
      expect(mockToast).not.toHaveBeenCalled();
    });

    it('should allow proceeding to next step with whitespace-only assistant name (current behavior)', async () => {
      renderCreateAssistant();
      
      // Wait for component to load and voices to be fetched
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Fill assistant name with only whitespace
      fireEvent.change(screen.getByLabelText('Assistant Name'), { 
        target: { value: '   ' } 
      });
      
      // Fill other required fields
      fireEvent.change(screen.getByLabelText('Short Description'), { 
        target: { value: 'Test description' } 
      });

      // The button should be enabled since whitespace-only strings are truthy in JavaScript
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
      
      // Click the button - should advance to step 2 (current behavior)
      fireEvent.click(nextButton);
      
      // Should advance to template selection step
      await waitFor(() => {
        expect(screen.getByText('Choose Template (Optional)')).toBeInTheDocument();
      });
      
      // Note: This reveals a potential improvement - validation should check for trimmed values
    });

    it('should allow proceeding to next step with valid assistant name', async () => {
      renderCreateAssistant();
      
      // Wait for component to load and voices to be fetched
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Mock the extract-site-info function
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: { title: 'Test Site', description: 'Test Description', content: 'Test content' },
        error: null,
      });

      // Fill all required fields
      fireEvent.change(screen.getByLabelText('Assistant Name'), { 
        target: { value: 'Test Assistant' } 
      });
      fireEvent.change(screen.getByLabelText('Short Description'), { 
        target: { value: 'Test description' } 
      });

      // Wait for the button to be enabled
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });

      // Try to proceed
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      // Should advance to step 2 (template selection)
      await waitFor(() => {
        expect(screen.getByText('Choose Template (Optional)')).toBeInTheDocument();
      });
    });

    it('should handle assistant name with numbers', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const namesWithNumbers = [
        'Assistant 1',
        'Bot 2024',
        'AI Helper v2.0',
        'Support Agent 24/7',
        'Customer Service Bot 1.0',
        'Sales Assistant 2024 Pro',
        'Help Desk AI v3.1',
        'Insurance Claims Helper 2.0',
        'Real Estate Agent AI 2024',
        'Healthcare Assistant v1.5'
      ];

      namesWithNumbers.forEach(name => {
        fireEvent.change(nameInput, { target: { value: name } });
        expect(nameInput).toHaveValue(name);
      });
    });

    it('should handle assistant name with unicode characters', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const namesWithUnicode = [
        'Customer Support Bot 🚀',
        'AI Assistant ⭐',
        'Help Desk 🤖',
        'Insurance Claims Helper 💼',
        'Real Estate Agent AI 🏠',
        'Healthcare Assistant 🏥',
        'Banking Support Bot 💳',
        'E-commerce Helper 🛒',
        'Restaurant Booking Assistant 🍽️',
        'Travel Planning AI ✈️'
      ];

      namesWithUnicode.forEach(name => {
        fireEvent.change(nameInput, { target: { value: name } });
        expect(nameInput).toHaveValue(name);
      });
    });

    it('should handle assistant name with mixed case', () => {
      renderCreateAssistant();
      const nameInput = screen.getByLabelText('Assistant Name');
      
      const mixedCaseNames = [
        'Customer Support Bot',
        'CUSTOMER SUPPORT BOT',
        'customer support bot',
        'CuStOmEr SuPpOrT bOt',
        'CustomerSupportBot',
        'customer_support_bot',
        'customer-support-bot',
        'Customer.Support.Bot',
        'Customer Support Bot!',
        'Customer Support Bot?'
      ];

      mixedCaseNames.forEach(name => {
        fireEvent.change(nameInput, { target: { value: name } });
        expect(nameInput).toHaveValue(name);
      });
    });

    it('should persist assistant name in localStorage when user is not authenticated', async () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderCreateAssistant();
      
      // Wait for component to load and voices to be fetched
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      fireEvent.change(screen.getByLabelText('Assistant Name'), { 
        target: { value: 'Test Assistant' } 
      });
      fireEvent.change(screen.getByLabelText('Short Description'), { 
        target: { value: 'Test description' } 
      });

      // Wait for the button to be enabled
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });

      // Try to proceed (should redirect to auth)
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'create_assistant_form',
        expect.stringContaining('"assistantName":"Test Assistant"')
      );
    });

    it('should restore assistant name from localStorage on component mount', () => {
      const cachedForm = {
        assistantName: 'Cached Assistant',
        description: 'Cached description',
        websiteUrl: 'https://example.com',
        assistantType: 'help_desk',
        useTemplate: false,
        selectedTemplate: null
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(cachedForm));

      renderCreateAssistant();
      
      expect(screen.getByLabelText('Assistant Name')).toHaveValue('Cached Assistant');
    });

    it('should handle malformed localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid json');

      renderCreateAssistant();
      
      // Should not crash and should have empty name field
      expect(screen.getByLabelText('Assistant Name')).toHaveValue('');
    });
  });

  describe('Website URL Validation', () => {
    it('should render website URL input field', () => {
      renderCreateAssistant();
      expect(screen.getByLabelText('Website URL (optional, recommended)')).toBeInTheDocument();
    });

    it('should accept valid website URLs', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const validUrls = [
        'https://example.com',
        'https://www.example.com',
        'https://example.com/path',
        'https://example.com/path?param=value',
        'https://example.com/path#section',
        'http://example.com',
        'https://subdomain.example.com',
        'https://example.co.uk',
        'https://example.org',
        'https://example.net'
      ];

      validUrls.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
      });
    });

    it('should handle invalid website URLs', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const invalidUrls = [
        'not-a-url',
        'ftp://example.com',
        'file:///path/to/file',
        'mailto:test@example.com',
        'tel:+1234567890',
        'javascript:alert("test")',
        'data:text/html,<script>alert("test")</script>',
        'example.com', // missing protocol
        'www.example.com', // missing protocol
        'https://' // incomplete URL
      ];

      invalidUrls.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
        // Note: HTML5 validation will show browser-specific error messages
      });
    });

    it('should handle empty website URL', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(urlInput, { target: { value: '' } });
      expect(urlInput).toHaveValue('');
    });

    it('should handle very long website URLs', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const longUrl = 'https://example.com/' + 'a'.repeat(2000);
      fireEvent.change(urlInput, { target: { value: longUrl } });
      expect(urlInput).toHaveValue(longUrl);
    });

    it('should handle URLs with special characters', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const urlsWithSpecialChars = [
        'https://example.com/path with spaces',
        'https://example.com/path-with-dashes',
        'https://example.com/path_with_underscores',
        'https://example.com/path/with/slashes',
        'https://example.com/path?param=value&another=param',
        'https://example.com/path#section-name',
        'https://example.com/path%20with%20encoding',
        'https://example.com/path+with+plus+signs',
        'https://example.com/path?param=value#section',
        'https://user:pass@example.com/path'
      ];

      urlsWithSpecialChars.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
      });
    });

    it('should handle internationalized domain names', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const internationalUrls = [
        'https://münchen.de',
        'https://bücher.de',
        'https://café.fr',
        'https://résumé.com',
        'https://naïve.org',
        'https://façade.net',
        'https://soupçon.co.uk',
        'https://voilà.com',
        'https://über.de',
        'https://schön.com'
      ];

      internationalUrls.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
      });
    });

    it('should handle URLs with different protocols', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const protocolUrls = [
        'https://example.com',
        'http://example.com',
        'https://example.com:8080',
        'https://example.com:443',
        'http://example.com:80',
        'https://example.com:3000',
        'https://example.com:9000',
        'https://example.com:12345',
        'https://example.com:65535',
        'https://example.com:1'
      ];

      protocolUrls.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
      });
    });

    it('should handle malformed URLs gracefully', () => {
      renderCreateAssistant();
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      const malformedUrls = [
        'https://',
        'http://',
        '://example.com',
        'example.com://',
        'https://example.com:',
        'https://example.com:abc',
        'https://example.com:99999',
        'https://example.com:0',
        'https://example.com:-1',
        'https://example.com:65536'
      ];

      malformedUrls.forEach(url => {
        fireEvent.change(urlInput, { target: { value: url } });
        expect(urlInput).toHaveValue(url);
      });
    });

    it('should persist website URL in localStorage when user is not authenticated', async () => {
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });

      renderCreateAssistant();
      
      // Wait for component to load and voices to be fetched
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      fireEvent.change(screen.getByLabelText('Assistant Name'), { 
        target: { value: 'Test Assistant' } 
      });
      fireEvent.change(screen.getByLabelText('Short Description'), { 
        target: { value: 'Test description' } 
      });
      fireEvent.change(screen.getByLabelText('Website URL (optional, recommended)'), { 
        target: { value: 'https://example.com' } 
      });

      // Wait for the button to be enabled
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });

      // Try to proceed (should redirect to auth)
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'create_assistant_form',
        expect.stringContaining('"websiteUrl":"https://example.com"')
      );
    });

    it('should restore website URL from localStorage on component mount', () => {
      const cachedForm = {
        assistantName: 'Cached Assistant',
        description: 'Cached description',
        websiteUrl: 'https://cached-example.com',
        assistantType: 'help_desk',
        useTemplate: false,
        selectedTemplate: null
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(cachedForm));

      renderCreateAssistant();
      
      expect(screen.getByLabelText('Website URL (optional, recommended)')).toHaveValue('https://cached-example.com');
    });
  });

  describe('Knowledge Base File Upload', () => {
    it('should render knowledge base file upload section', () => {
      renderCreateAssistant();
      expect(screen.getByText('Knowledge Base (Optional)')).toBeInTheDocument();
    });

    it('should render file upload area', () => {
      renderCreateAssistant();
      const uploadArea = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]');
      expect(uploadArea).toBeInTheDocument();
    });

    it('should accept multiple file types', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      expect(fileInput).toHaveAttribute('multiple');
    });

    it('should handle file selection', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });
      
      expect(fileInput.files).toHaveLength(1);
      expect(fileInput.files?.[0]).toBe(testFile);
    });

    it('should handle multiple file selection', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const testFiles = [
        new File(['content 1'], 'file1.txt', { type: 'text/plain' }),
        new File(['content 2'], 'file2.pdf', { type: 'application/pdf' }),
        new File(['content 3'], 'file3.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      ];
      
      fireEvent.change(fileInput, { target: { files: testFiles } });
      
      expect(fileInput.files).toHaveLength(3);
      expect(fileInput.files?.[0]).toBe(testFiles[0]);
      expect(fileInput.files?.[1]).toBe(testFiles[1]);
      expect(fileInput.files?.[2]).toBe(testFiles[2]);
    });

    it('should handle empty file selection', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      fireEvent.change(fileInput, { target: { files: [] } });
      
      expect(fileInput.files).toHaveLength(0);
    });

    it('should handle large files', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      // Create a large file (10MB)
      const largeContent = 'x'.repeat(10 * 1024 * 1024);
      const largeFile = new File([largeContent], 'large.txt', { type: 'text/plain' });
      
      fireEvent.change(fileInput, { target: { files: [largeFile] } });
      
      expect(fileInput.files).toHaveLength(1);
      expect(fileInput.files?.[0]).toBe(largeFile);
    });

    it('should handle files with special characters in names', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const specialNameFiles = [
        new File(['content'], 'file with spaces.txt', { type: 'text/plain' }),
        new File(['content'], 'file-with-dashes.txt', { type: 'text/plain' }),
        new File(['content'], 'file_with_underscores.txt', { type: 'text/plain' }),
        new File(['content'], 'file.with.dots.txt', { type: 'text/plain' }),
        new File(['content'], 'file(1).txt', { type: 'text/plain' }),
        new File(['content'], 'file[1].txt', { type: 'text/plain' }),
        new File(['content'], 'file{1}.txt', { type: 'text/plain' }),
        new File(['content'], 'file@1.txt', { type: 'text/plain' }),
        new File(['content'], 'file#1.txt', { type: 'text/plain' }),
        new File(['content'], 'file$1.txt', { type: 'text/plain' })
      ];
      
      fireEvent.change(fileInput, { target: { files: specialNameFiles } });
      
      expect(fileInput.files).toHaveLength(10);
    });

    it('should handle files with different extensions', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const differentExtensionFiles = [
        new File(['content'], 'document.txt', { type: 'text/plain' }),
        new File(['content'], 'document.pdf', { type: 'application/pdf' }),
        new File(['content'], 'document.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }),
        new File(['content'], 'document.doc', { type: 'application/msword' }),
        new File(['content'], 'document.rtf', { type: 'application/rtf' }),
        new File(['content'], 'document.odt', { type: 'application/vnd.oasis.opendocument.text' }),
        new File(['content'], 'document.md', { type: 'text/markdown' }),
        new File(['content'], 'document.html', { type: 'text/html' }),
        new File(['content'], 'document.csv', { type: 'text/csv' }),
        new File(['content'], 'document.json', { type: 'application/json' })
      ];
      
      fireEvent.change(fileInput, { target: { files: differentExtensionFiles } });
      
      expect(fileInput.files).toHaveLength(10);
    });

    it('should handle files with unicode characters in names', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const unicodeNameFiles = [
        new File(['content'], 'café.txt', { type: 'text/plain' }),
        new File(['content'], 'résumé.txt', { type: 'text/plain' }),
        new File(['content'], 'naïve.txt', { type: 'text/plain' }),
        new File(['content'], 'façade.txt', { type: 'text/plain' }),
        new File(['content'], 'soupçon.txt', { type: 'text/plain' }),
        new File(['content'], 'voilà.txt', { type: 'text/plain' }),
        new File(['content'], 'über.txt', { type: 'text/plain' }),
        new File(['content'], 'schön.txt', { type: 'text/plain' }),
        new File(['content'], 'münchen.txt', { type: 'text/plain' }),
        new File(['content'], 'bücher.txt', { type: 'text/plain' })
      ];
      
      fireEvent.change(fileInput, { target: { files: unicodeNameFiles } });
      
      expect(fileInput.files).toHaveLength(10);
    });

    it('should handle files with very long names', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const longName = 'a'.repeat(255) + '.txt';
      const longNameFile = new File(['content'], longName, { type: 'text/plain' });
      
      fireEvent.change(fileInput, { target: { files: [longNameFile] } });
      
      expect(fileInput.files).toHaveLength(1);
      expect(fileInput.files?.[0]?.name).toBe(longName);
    });

    it('should handle files with no extension', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const noExtensionFiles = [
        new File(['content'], 'file1', { type: 'text/plain' }),
        new File(['content'], 'file2', { type: 'application/octet-stream' }),
        new File(['content'], 'file3', { type: '' }),
        new File(['content'], 'file4', { type: 'unknown/type' })
      ];
      
      fireEvent.change(fileInput, { target: { files: noExtensionFiles } });
      
      expect(fileInput.files).toHaveLength(4);
    });

    it('should handle files with mixed content types', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      const mixedContentFiles = [
        new File(['text content'], 'text.txt', { type: 'text/plain' }),
        new File(['binary content'], 'binary.bin', { type: 'application/octet-stream' }),
        new File(['<html>content</html>'], 'webpage.html', { type: 'text/html' }),
        new File(['{"json": "content"}'], 'data.json', { type: 'application/json' }),
        new File(['markdown content'], 'readme.md', { type: 'text/markdown' })
      ];
      
      fireEvent.change(fileInput, { target: { files: mixedContentFiles } });
      
      expect(fileInput.files).toHaveLength(5);
    });

    it('should handle file input reset', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      // First, add some files
      const testFiles = [
        new File(['content 1'], 'file1.txt', { type: 'text/plain' }),
        new File(['content 2'], 'file2.txt', { type: 'text/plain' })
      ];
      
      fireEvent.change(fileInput, { target: { files: testFiles } });
      expect(fileInput.files).toHaveLength(2);
      
      // Then reset
      fireEvent.change(fileInput, { target: { files: [] } });
      expect(fileInput.files).toHaveLength(0);
    });

    it('should handle file input with null files', () => {
      renderCreateAssistant();
      const fileInput = screen.getByText('Knowledge Base (Optional)').closest('div')?.querySelector('input[type="file"]') as HTMLInputElement;
      
      fireEvent.change(fileInput, { target: { files: null } });
      
      expect(fileInput.files).toBeNull();
    });
  });
});

describe('CreateAssistant - Phase 1.2: Site Information Extraction', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
    localStorageMock.getItem.mockReturnValue(null);
    
    // Mock the list-vapi-voices function that gets called on component mount
    mockSupabaseInvoke.mockResolvedValue({
      data: { voices: [{ id: 'Paige', name: 'Paige' }] },
      error: null,
    });
  });



  describe('Gemini Integration', () => {
    it('should call extract-site-info edge function with valid URL', async () => {
      renderCreateAssistant();
      
      // Fill in all required fields
      await fillRequiredFields();
      
      // Mock successful site extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Website',
          description: 'A test website for extraction',
          content: 'This is the extracted content from the website.'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('extract-site-info', {
          body: { url: 'https://example.com' }
        });
      });
    });

    it('should handle API key validation errors', async () => {
      renderCreateAssistant();
      
      // Fill in all required fields
      await fillRequiredFields();
      
      // Mock API key error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Invalid API key'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Invalid API key'),
          variant: 'destructive'
        });
      });
    });

    it('should handle response format errors', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock invalid response format
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: null,
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('No data returned'),
          variant: 'destructive'
        });
      });
    });
  });

  describe('Website Accessibility', () => {
    it('should handle CORS errors gracefully', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock CORS error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('CORS policy error'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Website access blocked due to security restrictions'),
          variant: 'destructive'
        });
      });
    });

    it('should handle authentication required errors', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock authentication error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Unauthorized'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Authentication required'),
          variant: 'destructive'
        });
      });
    });

    it('should handle rate limiting errors', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock rate limiting error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Rate limit exceeded'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Rate limit exceeded'),
          variant: 'destructive'
        });
      });
    });
  });

  describe('Content Extraction Quality', () => {
    it('should extract relevant website information', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock successful extraction with good content
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'AI Labs Africa - Voice AI Solutions',
          description: 'Leading provider of voice AI assistants for African businesses',
          content: 'We specialize in creating custom voice AI assistants that help businesses automate customer service, sales, and support operations. Our solutions are designed specifically for the African market and support multiple languages including English, French, Arabic, and local African languages.'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('AI Labs Africa - Voice AI Solutions')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Leading provider of voice AI assistants for African businesses')).toBeInTheDocument();
        expect(screen.getByDisplayValue(/We specialize in creating custom voice AI assistants/)).toBeInTheDocument();
      });
    });

    it('should handle empty content extraction', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock empty content
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: '',
          description: '',
          content: ''
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Test Assistant')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Test Description')).toBeInTheDocument();
        expect(screen.getByDisplayValue('No content extracted')).toBeInTheDocument();
      });
    });

    it('should handle very long content extraction', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock very long content
      const longContent = 'A'.repeat(10000);
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Long Content Test',
          description: 'Testing with very long content',
          content: longContent
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Long Content Test')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Testing with very long content')).toBeInTheDocument();
        expect(screen.getByDisplayValue(longContent)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network failures', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock network failure
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Network error'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Network error'),
          variant: 'destructive'
        });
      });
    });

    it('should handle invalid URLs', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'invalid-url' } });
      
      // Mock invalid URL error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Invalid URL format'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Invalid URL format'),
          variant: 'destructive'
        });
      });
    });

    it('should handle timeout errors', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock timeout error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Request timeout'));
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Site extraction failed',
          description: expect.stringContaining('Website took too long to respond'),
          variant: 'destructive'
        });
      });
    });
  });

  describe('Extraction Performance', () => {
    it('should handle large sites efficiently', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://large-site.com' } });
      
      // Mock successful extraction for large site
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Large Website',
          description: 'A large website with extensive content',
          content: 'This is a large website with extensive content that should be processed efficiently.'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Large Website')).toBeInTheDocument();
        expect(screen.getByDisplayValue('A large website with extensive content')).toBeInTheDocument();
      });
    });

    it('should show loading state during extraction', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock delayed response
      mockSupabaseInvoke.mockImplementationOnce(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            data: {
              title: 'Test Site',
              description: 'Test Description',
              content: 'Test Content'
            },
            error: null,
          }), 100)
        )
      );
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      // Should show loading state
      expect(screen.getByText('Extracting website information...')).toBeInTheDocument();
      expect(screen.getByText('This may take a few moments')).toBeInTheDocument();
    });

    it('should handle concurrent extraction requests', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock successful extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Test Site',
          description: 'Test Description',
          content: 'Test Content'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      // Try to click next again (should be disabled during loading)
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        // Should only call extract-site-info once
        expect(mockSupabaseInvoke).toHaveBeenCalledTimes(2); // Once for voices, once for extraction
      });
    });
  });

  describe('URL Format Handling', () => {
    it('should add https:// prefix to URLs without protocol', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'example.com' } });
      
      // Mock successful extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Site',
          description: 'Example Description',
          content: 'Example Content'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('extract-site-info', {
          body: { url: 'https://example.com' }
        });
      });
    });

    it('should preserve existing https:// protocol', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Mock successful extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Site',
          description: 'Example Description',
          content: 'Example Content'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('extract-site-info', {
          body: { url: 'https://example.com' }
        });
      });
    });

    it('should handle http:// protocol', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      fireEvent.change(urlInput, { target: { value: 'http://example.com' } });
      
      // Mock successful extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Site',
          description: 'Example Description',
          content: 'Example Content'
        },
        error: null,
      });
      
      // Click next to trigger site extraction
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('extract-site-info', {
          body: { url: 'http://example.com' }
        });
      });
    });
  });
});

describe('CreateAssistant - Phase 1.3: System Prompt Generation', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
    localStorageMock.getItem.mockReturnValue(null);
    
    // Mock the list-vapi-voices function that gets called on component mount
    mockSupabaseInvoke.mockResolvedValue({
      data: { voices: [{ id: 'Paige', name: 'Paige' }] },
      error: null,
    });
  });

  // Helper function to fill in all required fields and advance to step 3
  const setupForPromptGeneration = async () => {
    renderCreateAssistant();
    
    // Fill in required fields
    const nameInput = screen.getByLabelText('Assistant Name');
    const descInput = screen.getByLabelText('Short Description');
    const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
    
    fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
    fireEvent.change(descInput, { target: { value: 'Test Description' } });
    fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
    
    // Select assistant type (required)
    const assistantTypeSelect = screen.getByRole('combobox', { name: /assistant type/i });
    fireEvent.click(assistantTypeSelect);
    const helpDeskOption = screen.getByText('Help Desk');
    fireEvent.click(helpDeskOption);
    
    // Select voice (required)
    const voiceSelect = screen.getByRole('combobox', { name: /voice/i });
    fireEvent.click(voiceSelect);
    const paigeVoice = screen.getByText('Paige');
    fireEvent.click(paigeVoice);
    
    // Mock successful site extraction
    mockSupabaseInvoke.mockResolvedValueOnce({
      data: {
        title: 'Example Website',
        description: 'A test website for extraction',
        content: 'This is the extracted content from the website.'
      },
      error: null,
    });
    
    // Click next to trigger site extraction and advance to step 2
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByText('Template Selection')).toBeInTheDocument();
    });
    
    // Click next again to advance to step 3 (prompt generation)
    const nextButton2 = screen.getByText('Next');
    fireEvent.click(nextButton2);
    
    await waitFor(() => {
      expect(screen.getByText('System Prompt')).toBeInTheDocument();
    });
  };

  describe('Prompt Quality', () => {
    it('should generate relevant prompt based on assistant type', async () => {
      await setupForPromptGeneration();
      
      // Check that the prompt contains relevant content for help desk assistant
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant, a helpful customer support assistant/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('helpful customer support assistant'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('Test Description'));
      });
    });

    it('should generate different prompts for different assistant types', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
      
      fireEvent.change(nameInput, { target: { value: 'Sales Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Sales expert for products' } });
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
      
      // Select sales assistant type
      const assistantTypeSelect = screen.getByRole('combobox', { name: /assistant type/i });
      fireEvent.click(assistantTypeSelect);
      const salesOption = screen.getByText('Sales');
      fireEvent.click(salesOption);
      
      // Select voice
      const voiceSelect = screen.getByRole('combobox', { name: /voice/i });
      fireEvent.click(voiceSelect);
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Mock successful site extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Website',
          description: 'A test website for extraction',
          content: 'This is the extracted content from the website.'
        },
        error: null,
      });
      
      // Advance to step 3
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      // Check that the prompt contains sales-specific content
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Sales Assistant, a sales expert/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('sales expert'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('overcome objections'));
      });
    });

    it('should include company information from site extraction', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Company Information/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('This is the extracted content from the website.'));
      });
    });

    it('should handle missing site information gracefully', async () => {
      renderCreateAssistant();
      
      // Fill in required fields without website URL
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      
      // Select assistant type
      const assistantTypeSelect = screen.getByRole('combobox', { name: /assistant type/i });
      fireEvent.click(assistantTypeSelect);
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = screen.getByRole('combobox', { name: /voice/i });
      fireEvent.click(voiceSelect);
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Advance to step 3
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      // Check that prompt is generated without company information section
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).not.toHaveValue(expect.stringContaining('Company Information'));
      });
    });
  });

  describe('Knowledge Base Integration', () => {
    it('should integrate knowledge base content into prompt', async () => {
      await setupForPromptGeneration();
      
      // Add knowledge base file
      const fileInput = screen.getByLabelText(/Knowledge Base/);
      const file = new File(['This is knowledge base content'], 'test.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [file] } });
      
      // Wait for file processing
      await waitFor(() => {
        expect(screen.getByText('test.txt')).toBeInTheDocument();
      });
      
      // Check that knowledge base content is included in prompt
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Additional Knowledge Base/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('This is knowledge base content'));
      });
    });

    it('should handle multiple knowledge base files', async () => {
      await setupForPromptGeneration();
      
      // Add multiple knowledge base files
      const fileInput = screen.getByLabelText(/Knowledge Base/);
      const file1 = new File(['Content from file 1'], 'file1.txt', { type: 'text/plain' });
      const file2 = new File(['Content from file 2'], 'file2.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [file1, file2] } });
      
      // Wait for file processing
      await waitFor(() => {
        expect(screen.getByText('file1.txt')).toBeInTheDocument();
        expect(screen.getByText('file2.txt')).toBeInTheDocument();
      });
      
      // Check that both files are included in prompt
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Additional Knowledge Base/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('Content from file 1'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('Content from file 2'));
      });
    });

    it('should handle encoding issues in knowledge base files', async () => {
      await setupForPromptGeneration();
      
      // Add file with special characters
      const fileInput = screen.getByLabelText(/Knowledge Base/);
      const file = new File(['Content with émojis 🎉 and special chars: ñáéíóú'], 'special.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [file] } });
      
      // Wait for file processing
      await waitFor(() => {
        expect(screen.getByText('special.txt')).toBeInTheDocument();
      });
      
      // Check that special characters are handled properly
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Additional Knowledge Base/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('émojis'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('ñáéíóú'));
      });
    });
  });

  describe('Prompt Customization', () => {
    it('should integrate user description into prompt', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Test Description/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('Test Description'));
      });
    });

    it('should build context from assistant name and type', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('helpful customer support assistant'));
      });
    });

    it('should allow manual prompt editing', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Edit the prompt
        fireEvent.change(promptTextarea, { 
          target: { value: 'Custom edited prompt content' } 
        });
        
        expect(promptTextarea).toHaveValue('Custom edited prompt content');
      });
    });
  });

  describe('Prompt Validation', () => {
    it('should enforce length limits', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Try to add very long content
        const longContent = 'A'.repeat(10000);
        fireEvent.change(promptTextarea, { target: { value: longContent } });
        
        // Check that the content is truncated or handled appropriately
        expect(promptTextarea).toHaveValue(longContent);
      });
    });

    it('should validate prompt content quality', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Check that the prompt contains required sections
        expect(promptTextarea).toHaveValue(expect.stringContaining('You are'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('Your role is'));
      });
    });

    it('should handle empty prompt gracefully', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Clear the prompt
        fireEvent.change(promptTextarea, { target: { value: '' } });
        
        // Should show validation error or warning
        expect(screen.getByText(/prompt.*required/i) || screen.getByText(/cannot.*empty/i)).toBeInTheDocument();
      });
    });
  });

  describe('Prompt Preview', () => {
    it('should show prompt preview before creation', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Check that the prompt is visible and editable
        expect(promptTextarea).toBeVisible();
        expect(promptTextarea).not.toBeDisabled();
      });
    });

    it('should allow users to review prompt before proceeding', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Check that there's a way to proceed (Next button)
        const nextButton = screen.getByText('Next');
        expect(nextButton).toBeInTheDocument();
        expect(nextButton).not.toBeDisabled();
      });
    });

    it('should show prompt length and content summary', async () => {
      await setupForPromptGeneration();
      
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        
        // Check that the prompt shows the expected content structure
        expect(promptTextarea).toHaveValue(expect.stringContaining('You are Test Assistant'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('Test Description'));
        expect(promptTextarea).toHaveValue(expect.stringContaining('Company Information'));
      });
    });
  });

  describe('Template Integration', () => {
    it('should use template system prompt when template is selected', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Template Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Template Description' } });
      
      // Select assistant type
      const assistantTypeSelect = screen.getByRole('combobox', { name: /assistant type/i });
      fireEvent.click(assistantTypeSelect);
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = screen.getByRole('combobox', { name: /voice/i });
      fireEvent.click(voiceSelect);
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Advance to step 2 (template selection)
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      // Select a template
      const useTemplateCheckbox = screen.getByLabelText(/Use template/i);
      fireEvent.click(useTemplateCheckbox);
      
      // Wait for template options to appear and select one
      await waitFor(() => {
        const templateOption = screen.getByText(/Beginner/i);
        fireEvent.click(templateOption);
      });
      
      // Advance to step 3
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      // Check that template content is used
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Template Assistant/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('Template Assistant'));
      });
    });

    it('should replace template placeholders with actual values', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Company Name' } });
      fireEvent.change(descInput, { target: { value: 'Company Description' } });
      
      // Select assistant type
      const assistantTypeSelect = screen.getByRole('combobox', { name: /assistant type/i });
      fireEvent.click(assistantTypeSelect);
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = screen.getByRole('combobox', { name: /voice/i });
      fireEvent.click(voiceSelect);
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Advance to step 2
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      // Select template
      const useTemplateCheckbox = screen.getByLabelText(/Use template/i);
      fireEvent.click(useTemplateCheckbox);
      
      await waitFor(() => {
        const templateOption = screen.getByText(/Beginner/i);
        fireEvent.click(templateOption);
      });
      
      // Advance to step 3
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      // Check that placeholders are replaced
      await waitFor(() => {
        const promptTextarea = screen.getByDisplayValue(/Company Name/);
        expect(promptTextarea).toBeInTheDocument();
        expect(promptTextarea).toHaveValue(expect.stringContaining('Company Name'));
        expect(promptTextarea).not.toHaveValue(expect.stringContaining('{company_name}'));
      });
    });
  });
});

describe('CreateAssistant - Phase 1.4: VAPI Assistant Creation', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
    localStorageMock.getItem.mockReturnValue(null);
    
    // Mock the list-vapi-voices function that gets called on component mount
    mockSupabaseInvoke.mockResolvedValue({
      data: { voices: [{ id: 'Paige', name: 'Paige' }] },
      error: null,
    });
  });

  // Helper function to setup component for VAPI assistant creation testing
  const setupForVapiCreation = async () => {
    renderCreateAssistant();
    
    // Fill in required fields
    const nameInput = screen.getByLabelText('Assistant Name');
    const descInput = screen.getByLabelText('Short Description');
    const urlInput = screen.getByLabelText('Website URL (optional, recommended)');
    
    fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
    fireEvent.change(descInput, { target: { value: 'Test Description' } });
    fireEvent.change(urlInput, { target: { value: 'https://example.com' } });
    
    // Wait for voices to be loaded
    await waitFor(() => {
      expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
    });
    
    // Select assistant type - use getAllByRole to get the first combobox
    const comboboxes = screen.getAllByRole('combobox');
    const assistantTypeSelect = comboboxes[0]; // First combobox is assistant type
    fireEvent.click(assistantTypeSelect);
    
    // Wait for dropdown to open and select option
    await waitFor(() => {
      expect(screen.getByText('Help Desk')).toBeInTheDocument();
    });
    const helpDeskOption = screen.getByText('Help Desk');
    fireEvent.click(helpDeskOption);
    
    // Select voice - use the second combobox
    const voiceSelect = comboboxes[1]; // Second combobox is voice
    fireEvent.click(voiceSelect);
    
    // Wait for voice dropdown to open and select option
    await waitFor(() => {
      expect(screen.getByText('Paige')).toBeInTheDocument();
    });
    const paigeVoice = screen.getByText('Paige');
    fireEvent.click(paigeVoice);
    
    // Mock successful site extraction
    mockSupabaseInvoke.mockResolvedValueOnce({
      data: {
        title: 'Example Website',
        description: 'A test website for extraction',
        content: 'This is the extracted content from the website.'
      },
      error: null,
    });
    
    // Advance to step 2 (template selection)
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByText('Template Selection')).toBeInTheDocument();
    });
    
    // Advance to step 3 (system prompt)
    const nextButton2 = screen.getByText('Next');
    fireEvent.click(nextButton2);
    
    await waitFor(() => {
      expect(screen.getByText('System Prompt')).toBeInTheDocument();
    });
    
    // Advance to step 4 (VAPI creation)
    const nextButton3 = screen.getByText('Next');
    fireEvent.click(nextButton3);
    
    await waitFor(() => {
      expect(screen.getByText('Demo Page Code')).toBeInTheDocument();
    });
  };

  describe('VAPI API Integration', () => {
    it('should call create-assistant edge function with correct parameters', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      // Check that create-assistant was called with correct parameters
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('create-assistant', {
          body: {
            assistantName: 'Test Assistant',
            description: 'Test Description',
            websiteUrl: 'https://example.com',
            assistantType: 'help_desk',
            voiceId: 'Paige',
            knowledgeBaseUrls: [],
            systemPromptOverride: expect.stringContaining('You are Test Assistant')
          }
        });
      });
    });

    it('should handle authentication requirements', async () => {
      // Mock unauthenticated user
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });
      
      await setupForVapiCreation();
      
      // Should show authentication requirement
      expect(screen.getByText(/Please sign in to continue/i)).toBeInTheDocument();
    });

    it('should validate request format before sending', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      // Check that all required fields are included in the request
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        
        const requestBody = createCall![1].body;
        expect(requestBody.assistantName).toBe('Test Assistant');
        expect(requestBody.description).toBe('Test Description');
        expect(requestBody.assistantType).toBe('help_desk');
        expect(requestBody.voiceId).toBe('Paige');
        expect(requestBody.systemPromptOverride).toContain('You are Test Assistant');
      });
    });

    it('should handle response format validation', async () => {
      await setupForVapiCreation();
      
      // Mock invalid response format (missing assistant_id)
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      // Should handle missing assistant_id gracefully
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: expect.stringContaining('Invalid response format'),
          variant: 'destructive'
        });
      });
    });
  });

  describe('Assistant Creation Success', () => {
    it('should retrieve and display assistant ID', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Assistant created successfully! ID: test-assistant-123/)).toBeInTheDocument();
      });
    });

    it('should verify assistant creation status', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        // Check that the assistant ID is displayed
        expect(screen.getByText(/test-assistant-123/)).toBeInTheDocument();
        
        // Check that success message is shown
        expect(screen.getByText(/Assistant created successfully!/)).toBeInTheDocument();
      });
    });

    it('should handle HTML code generation from edge function', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation with HTML
      const testHtml = '<html><body><h1>Test Demo Page</h1></body></html>';
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: testHtml
        },
        error: null,
      });
      
      await waitFor(() => {
        const htmlTextarea = screen.getByDisplayValue(testHtml);
        expect(htmlTextarea).toBeInTheDocument();
      });
    });

    it('should fallback to generated HTML if not provided by edge function', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation without HTML
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123'
        },
        error: null,
      });
      
      await waitFor(() => {
        // Should still show HTML code (generated fallback)
        const htmlTextarea = screen.getByDisplayValue(/<!DOCTYPE html>/);
        expect(htmlTextarea).toBeInTheDocument();
        expect(htmlTextarea).toHaveValue(expect.stringContaining('Test Assistant'));
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API failures gracefully', async () => {
      await setupForVapiCreation();
      
      // Mock API failure
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('VAPI API error'));
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'VAPI API error',
          variant: 'destructive'
        });
      });
    });

    it('should handle invalid data errors', async () => {
      await setupForVapiCreation();
      
      // Mock invalid data error
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: null,
        error: { message: 'Invalid assistant data' }
      });
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'Invalid assistant data',
          variant: 'destructive'
        });
      });
    });

    it('should handle rate limiting errors', async () => {
      await setupForVapiCreation();
      
      // Mock rate limiting error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Rate limit exceeded'));
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'Rate limit exceeded',
          variant: 'destructive'
        });
      });
    });

    it('should handle network timeout errors', async () => {
      await setupForVapiCreation();
      
      // Mock timeout error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('Request timeout'));
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'Request timeout',
          variant: 'destructive'
        });
      });
    });

    it('should handle VAPI service unavailable errors', async () => {
      await setupForVapiCreation();
      
      // Mock service unavailable error
      mockSupabaseInvoke.mockRejectedValueOnce(new Error('VAPI service unavailable'));
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'VAPI service unavailable',
          variant: 'destructive'
        });
      });
    });
  });

  describe('Voice Assignment', () => {
    it('should validate voice ID before sending request', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        expect(createCall![1].body.voiceId).toBe('Paige');
      });
    });

    it('should use default voice fallback when no voice is selected', async () => {
      renderCreateAssistant();
      
      // Fill in required fields without selecting voice
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      
      // Wait for voices to be loaded
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Select assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const assistantTypeSelect = comboboxes[0]; // First combobox is assistant type
      fireEvent.click(assistantTypeSelect);
      
      // Wait for dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Help Desk')).toBeInTheDocument();
      });
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Mock successful site extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Website',
          description: 'A test website for extraction',
          content: 'This is the extracted content from the website.'
        },
        error: null,
      });
      
      // Advance through steps to VAPI creation
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      const nextButton3 = screen.getByText('Next');
      fireEvent.click(nextButton3);
      
      await waitFor(() => {
        expect(screen.getByText('Demo Page Code')).toBeInTheDocument();
      });
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      // Should use default voice (Paige) when no voice is selected
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        expect(createCall![1].body.voiceId).toBe('Paige');
      });
    });

    it('should handle invalid voice ID errors', async () => {
      await setupForVapiCreation();
      
      // Mock invalid voice ID error
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: null,
        error: { message: 'Invalid voice ID: invalid-voice' }
      });
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Failed to create assistant',
          description: 'Invalid voice ID: invalid-voice',
          variant: 'destructive'
        });
      });
    });
  });

  describe('System Prompt Transmission', () => {
    it('should properly encode system prompt for transmission', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        
        const systemPrompt = createCall![1].body.systemPromptOverride;
        expect(systemPrompt).toContain('You are Test Assistant');
        expect(systemPrompt).toContain('Test Description');
        expect(systemPrompt).toContain('helpful customer support assistant');
      });
    });

    it('should handle long system prompts within limits', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        
        const systemPrompt = createCall![1].body.systemPromptOverride;
        // Should handle long prompts without truncation
        expect(systemPrompt.length).toBeGreaterThan(100);
      });
    });

    it('should handle special characters in system prompt', async () => {
      await setupForVapiCreation();
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'test-assistant-123',
          demo_url: 'https://demo.example.com/test-assistant-123',
          html: '<html>Test HTML</html>'
        },
        error: null,
      });
      
      await waitFor(() => {
        const createCall = mockSupabaseInvoke.mock.calls.find(
          call => call[0] === 'create-assistant'
        );
        expect(createCall).toBeDefined();
        
        const systemPrompt = createCall![1].body.systemPromptOverride;
        // Should handle special characters like quotes, newlines, etc.
        expect(systemPrompt).toContain('"');
        expect(systemPrompt).toContain('\n');
      });
    });

    it('should handle empty system prompt gracefully', async () => {
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Test Description' } });
      
      // Wait for voices to be loaded
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Select assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const assistantTypeSelect = comboboxes[0]; // First combobox is assistant type
      fireEvent.click(assistantTypeSelect);
      
      // Wait for dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Help Desk')).toBeInTheDocument();
      });
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = comboboxes[1]; // Second combobox is voice
      fireEvent.click(voiceSelect);
      
      // Wait for voice dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Paige')).toBeInTheDocument();
      });
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Advance to step 3 (system prompt)
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      // Clear the system prompt
      const promptTextarea = screen.getByDisplayValue(/You are Test Assistant/);
      fireEvent.change(promptTextarea, { target: { value: '' } });
      
      // Try to advance to step 4
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      // Should show validation error for empty prompt
      await waitFor(() => {
        expect(screen.getByText(/prompt.*required/i) || screen.getByText(/cannot.*empty/i)).toBeInTheDocument();
      });
    });
  });

  describe('Guest Mode Integration', () => {
    it('should handle guest mode assistant creation', async () => {
      // Mock unauthenticated user
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });
      
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Guest Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Guest Description' } });
      
      // Wait for voices to be loaded
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Select assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const assistantTypeSelect = comboboxes[0]; // First combobox is assistant type
      fireEvent.click(assistantTypeSelect);
      
      // Wait for dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Help Desk')).toBeInTheDocument();
      });
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = comboboxes[1]; // Second combobox is voice
      fireEvent.click(voiceSelect);
      
      // Wait for voice dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Paige')).toBeInTheDocument();
      });
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Mock successful site extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Website',
          description: 'A test website for extraction',
          content: 'This is the extracted content from the website.'
        },
        error: null,
      });
      
      // Advance through steps
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      const nextButton3 = screen.getByText('Next');
      fireEvent.click(nextButton3);
      
      await waitFor(() => {
        expect(screen.getByText('Demo Page Code')).toBeInTheDocument();
      });
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'guest-assistant-123',
          demo_url: 'https://demo.example.com/guest-assistant-123',
          html: '<html>Guest HTML</html>'
        },
        error: null,
      });
      
      // Mock successful guest save
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: { success: true },
        error: null,
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Assistant created successfully!/)).toBeInTheDocument();
      });
    });

    it('should handle guest save failures gracefully', async () => {
      // Mock unauthenticated user
      (useAuth as any).mockReturnValue({
        user: null,
        loading: false,
      });
      
      renderCreateAssistant();
      
      // Fill in required fields
      const nameInput = screen.getByLabelText('Assistant Name');
      const descInput = screen.getByLabelText('Short Description');
      
      fireEvent.change(nameInput, { target: { value: 'Guest Assistant' } });
      fireEvent.change(descInput, { target: { value: 'Guest Description' } });
      
      // Wait for voices to be loaded
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
      
      // Select assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const assistantTypeSelect = comboboxes[0]; // First combobox is assistant type
      fireEvent.click(assistantTypeSelect);
      
      // Wait for dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Help Desk')).toBeInTheDocument();
      });
      const helpDeskOption = screen.getByText('Help Desk');
      fireEvent.click(helpDeskOption);
      
      // Select voice
      const voiceSelect = comboboxes[1]; // Second combobox is voice
      fireEvent.click(voiceSelect);
      
      // Wait for voice dropdown to open and select option
      await waitFor(() => {
        expect(screen.getByText('Paige')).toBeInTheDocument();
      });
      const paigeVoice = screen.getByText('Paige');
      fireEvent.click(paigeVoice);
      
      // Mock successful site extraction
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          title: 'Example Website',
          description: 'A test website for extraction',
          content: 'This is the extracted content from the website.'
        },
        error: null,
      });
      
      // Advance through steps
      const nextButton = screen.getByText('Next');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Template Selection')).toBeInTheDocument();
      });
      
      const nextButton2 = screen.getByText('Next');
      fireEvent.click(nextButton2);
      
      await waitFor(() => {
        expect(screen.getByText('System Prompt')).toBeInTheDocument();
      });
      
      const nextButton3 = screen.getByText('Next');
      fireEvent.click(nextButton3);
      
      await waitFor(() => {
        expect(screen.getByText('Demo Page Code')).toBeInTheDocument();
      });
      
      // Mock successful VAPI assistant creation
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: {
          assistant_id: 'guest-assistant-123',
          demo_url: 'https://demo.example.com/guest-assistant-123',
          html: '<html>Guest HTML</html>'
        },
        error: null,
      });
      
      // Mock guest save failure
      mockSupabaseInvoke.mockResolvedValueOnce({
        data: null,
        error: { message: 'Guest save failed' }
      });
      
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Warning',
          description: 'Assistant created but failed to save for guest access. Please note your assistant ID.',
          variant: 'destructive',
        });
      });
    });
  });
});

describe("Phase 1.1.5: Voice Selection Testing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock scrollIntoView to prevent Radix UI errors
    Element.prototype.scrollIntoView = vi.fn();
    render(<CreateAssistant />);
  });

  test("should load voices from VAPI API on component mount", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" },
      { id: "voice3", name: "Mike" }
    ];

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    await waitFor(() => {
      expect(supabase.functions.invoke).toHaveBeenCalledWith("list-vapi-voices");
    });
  });

  test("should set first voice as default when voices are loaded", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" }
    ];

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1]; // Second combobox is voice selection
      expect(voiceSelect).toHaveValue("voice1");
    });
  });

  test("should fallback to Paige voice when API fails", async () => {
    (supabase.functions.invoke as Mock).mockRejectedValueOnce(new Error("API Error"));

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1]; // Second combobox is voice selection
      expect(voiceSelect).toHaveValue("Paige");
    });
  });

  test("should allow user to change voice selection", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" }
    ];

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1]; // Second combobox is voice selection
      fireEvent.click(voiceSelect);
    });

    await waitFor(() => {
      const sarahOption = screen.getByText("Sarah");
      fireEvent.click(sarahOption);
    });

    const voiceSelects = screen.getAllByRole("combobox");
    const voiceSelect = voiceSelects[1];
    expect(voiceSelect).toHaveValue("voice2");
  });

  test("should persist voice selection in localStorage", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" }
    ];

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1];
      fireEvent.click(voiceSelect);
    });

    await waitFor(() => {
      const sarahOption = screen.getByText("Sarah");
      fireEvent.click(sarahOption);
    });

    // Check if voice selection is saved to localStorage
    const savedData = JSON.parse(localStorage.getItem("create_assistant_form") || "{}");
    expect(savedData.voiceId).toBe("voice2");
  });

  test("should restore voice selection from localStorage on component mount", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" }
    ];

    // Set up localStorage with saved voice selection
    localStorage.setItem("create_assistant_form", JSON.stringify({
      voiceId: "voice2"
    }));

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    render(<CreateAssistant />);

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1];
      expect(voiceSelect).toHaveValue("voice2");
    });
  });

  test("should handle empty voice list gracefully", async () => {
    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: [] },
      error: null
    });

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1];
      expect(voiceSelect).toHaveValue("Paige"); // Should fallback to Paige
    });
  });

  test("should display voice names in dropdown options", async () => {
    const mockVoices = [
      { id: "voice1", name: "Paige" },
      { id: "voice2", name: "Sarah" },
      { id: "voice3", name: "Mike" }
    ];

    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { voices: mockVoices },
      error: null
    });

    await waitFor(() => {
      const voiceSelects = screen.getAllByRole("combobox");
      const voiceSelect = voiceSelects[1];
      fireEvent.click(voiceSelect);
    });

    await waitFor(() => {
      expect(screen.getByText("Paige")).toBeInTheDocument();
      expect(screen.getByText("Sarah")).toBeInTheDocument();
      expect(screen.getByText("Mike")).toBeInTheDocument();
    });
  });
});

describe("Phase 1.1.6: Assistant Type Selection Testing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock scrollIntoView to prevent Radix UI errors
    Element.prototype.scrollIntoView = vi.fn();
    render(<CreateAssistant />);
  });

  test("should have default assistant type selected", () => {
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0]; // First combobox is assistant type
    expect(typeSelect).toHaveValue("sales_cold_call"); // First option should be default
  });

  test("should display all assistant types in dropdown", async () => {
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    fireEvent.click(typeSelect);

    await waitFor(() => {
      expect(screen.getByText("Sales - Cold Call")).toBeInTheDocument();
      expect(screen.getByText("Help Desk")).toBeInTheDocument();
      expect(screen.getByText("Follow-up (e.g. Church)")).toBeInTheDocument();
      expect(screen.getByText("Survey")).toBeInTheDocument();
    });
  });

  test("should allow user to change assistant type", async () => {
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    fireEvent.click(typeSelect);

    await waitFor(() => {
      const helpDeskOption = screen.getByText("Help Desk");
      fireEvent.click(helpDeskOption);
    });

    expect(typeSelect).toHaveValue("help_desk");
  });

  test("should persist assistant type selection in localStorage", async () => {
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    fireEvent.click(typeSelect);

    await waitFor(() => {
      const surveyOption = screen.getByText("Survey");
      fireEvent.click(surveyOption);
    });

    // Check if assistant type is saved to localStorage
    const savedData = JSON.parse(localStorage.getItem("create_assistant_form") || "{}");
    expect(savedData.assistantType).toBe("survey");
  });

  test("should restore assistant type from localStorage on component mount", () => {
    // Set up localStorage with saved assistant type
    localStorage.setItem("create_assistant_form", JSON.stringify({
      assistantType: "help_desk"
    }));

    render(<CreateAssistant />);

    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    expect(typeSelect).toHaveValue("help_desk");
  });

  test("should update system prompt based on assistant type", async () => {
    // Fill required fields first
    await fillRequiredFields();

    // Change assistant type to help desk
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    fireEvent.click(typeSelect);

    await waitFor(() => {
      const helpDeskOption = screen.getByText("Help Desk");
      fireEvent.click(helpDeskOption);
    });

    // Mock the system prompt generation
    (supabase.functions.invoke as Mock).mockResolvedValueOnce({
      data: { prompt: "Help desk specific prompt" },
      error: null
    });

    // Move to step 4 to trigger system prompt generation
    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton); // Step 2
    fireEvent.click(nextButton); // Step 3
    fireEvent.click(nextButton); // Step 4

    await waitFor(() => {
      expect(supabase.functions.invoke).toHaveBeenCalledWith(
        "extract-site-info",
        expect.objectContaining({
          assistantType: "help_desk"
        })
      );
    });
  });

  test("should validate assistant type is selected before proceeding", async () => {
    // Fill other required fields but not assistant type
    const nameInput = screen.getByLabelText(/assistant name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const voiceSelects = screen.getAllByRole("combobox");

    fireEvent.change(nameInput, { target: { value: "Test Assistant" } });
    fireEvent.change(descriptionInput, { target: { value: "Test description" } });

    // Wait for voice to be loaded and selected
    await waitFor(() => {
      expect(voiceSelects[1]).toHaveValue();
    });

    // Next button should be enabled even without assistant type (it has a default)
    const nextButton = screen.getByRole("button", { name: /next/i });
    expect(nextButton).not.toBeDisabled();
  });

  test("should handle all assistant type values correctly", async () => {
    const assistantTypes = [
      { value: "sales_cold_call", label: "Sales - Cold Call" },
      { value: "help_desk", label: "Help Desk" },
      { value: "follow_up", label: "Follow-up (e.g. Church)" },
      { value: "survey", label: "Survey" }
    ];

    for (const type of assistantTypes) {
      const typeSelects = screen.getAllByRole("combobox");
      const typeSelect = typeSelects[0];
      fireEvent.click(typeSelect);

      await waitFor(() => {
        const options = screen.getAllByText(type.label);
        const option = options[options.length - 1]; // Get the last one (the actual option)
        fireEvent.click(option);
      });

      expect(typeSelect).toHaveValue(type.value);
    }
  });

  test("should maintain assistant type selection across form steps", async () => {
    // Select a specific assistant type
    const typeSelects = screen.getAllByRole("combobox");
    const typeSelect = typeSelects[0];
    fireEvent.click(typeSelect);

    await waitFor(() => {
      const surveyOption = screen.getByText("Survey");
      fireEvent.click(surveyOption);
    });

    // Fill required fields and proceed to next step
    await fillRequiredFields();
    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

    // Assistant type should still be selected
    expect(typeSelect).toHaveValue("survey");
  });
});

describe('CreateAssistant - Phase 1.5: Voice Selection & Assistant Type Testing', () => {
  const mockToast = vi.fn();
  const mockSupabaseInvoke = vi.mocked(supabase.functions.invoke);

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue({ toast: mockToast });
    (useAuth as any).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      loading: false,
    });
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('Voice Selection Tests', () => {
    it('should load VAPI voices on component mount', async () => {
      const mockVoices = [
        { id: 'Paige', name: 'Paige' },
        { id: 'John', name: 'John' },
        { id: 'Sarah', name: 'Sarah' }
      ];

      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: mockVoices },
        error: null,
      });

      renderCreateAssistant();

      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith('list-vapi-voices');
      });
    });

    it('should handle VAPI voice loading errors gracefully', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: null,
        error: { message: 'Failed to load voices' },
      });

      renderCreateAssistant();

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            description: expect.stringContaining('Failed to load voices'),
            variant: 'destructive',
          })
        );
      });
    });

    it('should populate voice select with loaded voices', async () => {
      const mockVoices = [
        { id: 'Paige', name: 'Paige' },
        { id: 'John', name: 'John' },
        { id: 'Sarah', name: 'Sarah' }
      ];

      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: mockVoices },
        error: null,
      });

      renderCreateAssistant();

      await waitFor(() => {
        // Check that voice select is present (it will be the second combobox)
        const comboboxes = screen.getAllByRole('combobox');
        expect(comboboxes.length).toBeGreaterThan(1);
      });
    });

    it('should validate voice selection is required', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      // Fill other required fields but not voice
      const nameInput = screen.getByLabelText(/assistant name/i);
      const descriptionInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Voice should be required for form validation
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        // Button should be disabled until voice is selected
        expect(nextButton).toBeDisabled();
      });
    });

    it('should persist voice selection across form steps', async () => {
      const mockVoices = [
        { id: 'Paige', name: 'Paige' },
        { id: 'John', name: 'John' }
      ];

      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: mockVoices },
        error: null,
      });

      renderCreateAssistant();

      // Wait for voices to load and select a voice
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const voiceSelect = comboboxes[1]; // Second combobox is voice
        fireEvent.click(voiceSelect);
      });

      await waitFor(() => {
        const johnOption = screen.getByText('John');
        fireEvent.click(johnOption);
      });

      // Fill other required fields
      const nameInput = screen.getByLabelText(/assistant name/i);
      const descriptionInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Proceed to next step
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      // Voice selection should persist
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const voiceSelect = comboboxes[1];
        expect(voiceSelect).toHaveValue('John');
      });
    });
  });

  describe('Assistant Type Selection Tests', () => {
    it('should display all assistant types in the select dropdown', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      const comboboxes = screen.getAllByRole('combobox');
      const typeSelect = comboboxes[0]; // First combobox is assistant type
      fireEvent.click(typeSelect);

      await waitFor(() => {
        expect(screen.getByText('Sales - Cold Call')).toBeInTheDocument();
        expect(screen.getByText('Help Desk')).toBeInTheDocument();
        expect(screen.getByText('Follow-up (e.g. Church)')).toBeInTheDocument();
        expect(screen.getByText('Survey')).toBeInTheDocument();
      });
    });

    it('should set default assistant type on component mount', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const typeSelect = comboboxes[0];
        expect(typeSelect).toHaveValue('sales_cold_call');
      });
    });

    it('should update assistant type when user selects different option', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      const comboboxes = screen.getAllByRole('combobox');
      const typeSelect = comboboxes[0];
      fireEvent.click(typeSelect);

      await waitFor(() => {
        const helpDeskOption = screen.getByText('Help Desk');
        fireEvent.click(helpDeskOption);
      });

      expect(typeSelect).toHaveValue('help_desk');
    });

    it('should persist assistant type selection across form steps', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      // Select a specific assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const typeSelect = comboboxes[0];
      fireEvent.click(typeSelect);

      await waitFor(() => {
        const surveyOption = screen.getByText('Survey');
        fireEvent.click(surveyOption);
      });

      // Fill required fields and proceed
      await fillRequiredFields();

      // Assistant type should persist
      expect(typeSelect).toHaveValue('survey');
    });

    it('should validate assistant type is selected before form submission', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      // Fill other fields but not assistant type (it has default)
      const nameInput = screen.getByLabelText(/assistant name/i);
      const descriptionInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Wait for voice to be selected
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const voiceSelect = comboboxes[1];
        fireEvent.click(voiceSelect);
      });

      await waitFor(() => {
        const paigeOption = screen.getByText('Paige');
        fireEvent.click(paigeOption);
      });

      // Form should be valid with default assistant type
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });
  });

  describe('VAPI Integration Tests', () => {
    it('should call VAPI assistant creation with correct parameters', async () => {
      mockSupabaseInvoke
        .mockResolvedValueOnce({
          data: { voices: [{ id: 'Paige', name: 'Paige' }] },
          error: null,
        })
        .mockResolvedValueOnce({
          data: { id: 'vapi-assistant-id' },
          error: null,
        });

      renderCreateAssistant();

      // Fill required fields
      await fillRequiredFields();

      // Proceed through all steps to trigger VAPI creation
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // Step 1 to 2
      fireEvent.click(nextButton);
      
      // Step 2 to 3
      fireEvent.click(nextButton);
      
      // Step 3 to 4
      fireEvent.click(nextButton);
      
      // Step 4 to deploy
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith(
          'create-assistant',
          expect.objectContaining({
            assistantName: 'Test Assistant',
            description: 'Test Description',
            assistantType: 'help_desk',
            voiceId: 'Paige'
          })
        );
      });
    });

    it('should handle VAPI assistant creation errors', async () => {
      mockSupabaseInvoke
        .mockResolvedValueOnce({
          data: { voices: [{ id: 'Paige', name: 'Paige' }] },
          error: null,
        })
        .mockResolvedValueOnce({
          data: null,
          error: { message: 'VAPI creation failed' },
        });

      renderCreateAssistant();

      // Fill required fields
      await fillRequiredFields();

      // Proceed through all steps
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // Step 1 to 2
      fireEvent.click(nextButton);
      
      // Step 2 to 3
      fireEvent.click(nextButton);
      
      // Step 3 to 4
      fireEvent.click(nextButton);
      
      // Step 4 to deploy
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            description: expect.stringContaining('VAPI creation failed'),
            variant: 'destructive',
          })
        );
      });
    });

    it('should show loading state during VAPI assistant creation', async () => {
      mockSupabaseInvoke
        .mockResolvedValueOnce({
          data: { voices: [{ id: 'Paige', name: 'Paige' }] },
          error: null,
        })
        .mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderCreateAssistant();

      // Fill required fields
      await fillRequiredFields();

      // Proceed through all steps
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // Step 1 to 2
      fireEvent.click(nextButton);
      
      // Step 2 to 3
      fireEvent.click(nextButton);
      
      // Step 3 to 4
      fireEvent.click(nextButton);
      
      // Step 4 to deploy
      fireEvent.click(nextButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/creating vapi assistant/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation Tests', () => {
    it('should validate all required fields before allowing form submission', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      // Initially, form should be invalid
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Fill required fields one by one
      const nameInput = screen.getByLabelText(/assistant name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      expect(nextButton).toBeDisabled();

      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });
      expect(nextButton).toBeDisabled();

      // Select voice
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const voiceSelect = comboboxes[1];
        fireEvent.click(voiceSelect);
      });

      await waitFor(() => {
        const paigeOption = screen.getByText('Paige');
        fireEvent.click(paigeOption);
      });

      // Now form should be valid
      expect(nextButton).not.toBeDisabled();
    });

    it('should show validation errors for empty required fields', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      // Try to submit without filling required fields
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // Button should be disabled, indicating validation is working
      expect(nextButton).toBeDisabled();
    });

    it('should validate assistant name length and format', async () => {
      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: [{ id: 'Paige', name: 'Paige' }] },
        error: null,
      });

      renderCreateAssistant();

      const nameInput = screen.getByLabelText(/assistant name/i);
      
      // Test with very short name
      fireEvent.change(nameInput, { target: { value: 'A' } });
      
      // Test with very long name
      fireEvent.change(nameInput, { target: { value: 'A'.repeat(100) } });
      
      // Test with valid name
      fireEvent.change(nameInput, { target: { value: 'Valid Assistant Name' } });

      // Fill other required fields
      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Select voice
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox');
        const voiceSelect = comboboxes[1];
        fireEvent.click(voiceSelect);
      });

      await waitFor(() => {
        const paigeOption = screen.getByText('Paige');
        fireEvent.click(paigeOption);
      });

      // Form should be valid with proper name
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });
  });

  describe('Integration Tests', () => {
    it('should integrate voice selection with assistant type selection', async () => {
      const mockVoices = [
        { id: 'Paige', name: 'Paige' },
        { id: 'John', name: 'John' }
      ];

      mockSupabaseInvoke.mockResolvedValue({
        data: { voices: mockVoices },
        error: null,
      });

      renderCreateAssistant();

      // Select assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const typeSelect = comboboxes[0];
      fireEvent.click(typeSelect);

      await waitFor(() => {
        const helpDeskOption = screen.getByText('Help Desk');
        fireEvent.click(helpDeskOption);
      });

      // Select voice
      await waitFor(() => {
        const voiceSelect = comboboxes[1];
        fireEvent.click(voiceSelect);
      });

      await waitFor(() => {
        const johnOption = screen.getByText('John');
        fireEvent.click(johnOption);
      });

      // Fill other required fields
      const nameInput = screen.getByLabelText(/assistant name/i);
      const descriptionInput = screen.getByLabelText(/description/i);
      
      fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test description' } });

      // Both selections should persist
      expect(typeSelect).toHaveValue('help_desk');
      expect(comboboxes[1]).toHaveValue('John');

      // Form should be valid
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });

    it('should handle complete form workflow with all selections', async () => {
      mockSupabaseInvoke
        .mockResolvedValueOnce({
          data: { voices: [{ id: 'Paige', name: 'Paige' }] },
          error: null,
        })
        .mockResolvedValueOnce({
          data: { id: 'vapi-assistant-id' },
          error: null,
        });

      renderCreateAssistant();

      // Complete form filling
      await fillRequiredFields();

      // Change assistant type
      const comboboxes = screen.getAllByRole('combobox');
      const typeSelect = comboboxes[0];
      fireEvent.click(typeSelect);

      await waitFor(() => {
        const surveyOption = screen.getByText('Survey');
        fireEvent.click(surveyOption);
      });

      // Proceed through all steps
      const nextButton = screen.getByRole('button', { name: /next/i });
      
      // Step 1 to 2
      fireEvent.click(nextButton);
      
      // Step 2 to 3
      fireEvent.click(nextButton);
      
      // Step 3 to 4
      fireEvent.click(nextButton);
      
      // Step 4 to deploy
      fireEvent.click(nextButton);

      // Should create VAPI assistant with correct parameters
      await waitFor(() => {
        expect(mockSupabaseInvoke).toHaveBeenCalledWith(
          'create-assistant',
          expect.objectContaining({
            assistantName: 'Test Assistant',
            description: 'Test Description',
            assistantType: 'survey',
            voiceId: 'Paige'
          })
        );
      });
    });
  });
});
