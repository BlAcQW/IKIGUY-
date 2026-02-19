import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Mock Supabase at the top level
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: vi.fn(() => ({
      upsert: vi.fn(() => Promise.resolve({ error: null })),
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          single: vi.fn(() => Promise.resolve({ data: null, error: null }))
        }))
      })),
      delete: vi.fn(() => ({
        eq: vi.fn(() => Promise.resolve({ error: null }))
      }))
    }))
  }
}));

import CreateAssistant from '@/pages/CreateAssistant';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('Save Progress Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    localStorageMock.setItem.mockImplementation(() => {});
    localStorageMock.removeItem.mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should save progress to localStorage when save button is clicked', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <CreateAssistant />
        </AuthProvider>
      </BrowserRouter>
    );

    // Fill in some form data
    const nameInput = screen.getByLabelText(/assistant name/i);
    fireEvent.change(nameInput, { target: { value: 'Test Assistant' } });

    // Find and click save progress button
    const saveButton = screen.getByText(/save progress/i);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'create_assistant_progress',
        expect.stringContaining('Test Assistant')
      );
    });
  });

  it('should load progress from localStorage when load button is clicked', async () => {
    const mockProgressData = {
      step: 2,
      timestamp: new Date().toISOString(),
      data: {
        assistantName: 'Saved Assistant',
        description: 'Test description',
        websiteUrl: 'https://example.com',
        assistantType: 'sales_cold_call',
        useTemplate: false,
        selectedTemplate: null,
        voiceId: '',
        knowledgeBaseCount: 0,
        siteInfo: null,
        systemPrompt: '',
        htmlCode: '',
        assistantId: ''
      }
    };

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockProgressData));

    render(
      <BrowserRouter>
        <AuthProvider>
          <CreateAssistant />
        </AuthProvider>
      </BrowserRouter>
    );

    // Find and click load progress button
    const loadButton = screen.getByText(/load progress/i);
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Saved Assistant')).toBeInTheDocument();
    });
  });

  it('should clear progress when clear button is clicked', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <CreateAssistant />
        </AuthProvider>
      </BrowserRouter>
    );

    // Find and click clear progress button
    const clearButton = screen.getByText(/clear progress/i);
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('create_assistant_progress');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('create_assistant_form');
    });
  });

  it('should show save progress button when there is no saved progress', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <CreateAssistant />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/save progress/i)).toBeInTheDocument();
  });

  it('should show load progress button when there is saved progress', () => {
    localStorageMock.getItem.mockReturnValue('{"step": 1, "data": {}}');

    render(
      <BrowserRouter>
        <AuthProvider>
          <CreateAssistant />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/load progress/i)).toBeInTheDocument();
  });
});
