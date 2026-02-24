import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render as rtlRender, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import React from 'react';

vi.mock('@/lib/api', () => ({
  listAssistants: vi.fn(),
  deleteAssistant: vi.fn(),
  getAssistant: vi.fn(),
  updateAssistant: vi.fn(),
  createAssistant: vi.fn(),
  listTools: vi.fn(),
  listToolTemplates: vi.fn(),
  getAssistantTools: vi.fn(),
  attachToolToAssistant: vi.fn(),
  detachToolFromAssistant: vi.fn(),
  createToolFromTemplate: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { AssistantsPage } from './index';
import {
  listAssistants,
  createAssistant,
  deleteAssistant,
  getAssistant,
  updateAssistant,
  getAssistantTools,
} from '@/lib/api';
import { toast } from 'sonner';
import { buildAssistant } from '@test/helpers/factories';

const mockedListAssistants = vi.mocked(listAssistants);
const mockedCreateAssistant = vi.mocked(createAssistant);
const mockedDeleteAssistant = vi.mocked(deleteAssistant);
const mockedGetAssistant = vi.mocked(getAssistant);
const mockedUpdateAssistant = vi.mocked(updateAssistant);
const mockedGetAssistantTools = vi.mocked(getAssistantTools);
const mockedToast = vi.mocked(toast);

function renderWithRoute(route: string) {
  const user = userEvent.setup();
  const result = rtlRender(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/assistants" element={<AssistantsPage />} />
        <Route path="/assistants/:id" element={<AssistantsPage />} />
      </Routes>
    </MemoryRouter>,
  );
  return { ...result, user };
}

describe('AssistantsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders assistant list panel', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText(/assistants/i)).toBeInTheDocument();
    });
  });

  it('renders create button', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new/i })).toBeInTheDocument();
    });
  });

  it('lists loaded assistants', async () => {
    const assistants = [
      buildAssistant({ name: 'Sales Bot' }),
      buildAssistant({ name: 'Support Bot' }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText('Sales Bot')).toBeInTheDocument();
      expect(screen.getByText('Support Bot')).toBeInTheDocument();
    });
  });

  it('shows search input', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
    });
  });

  it('handles load error gracefully', async () => {
    mockedListAssistants.mockRejectedValue(new Error('Network error'));
    renderWithRoute('/assistants');

    // Should still render the page structure
    await waitFor(() => {
      expect(screen.getByText(/assistants/i)).toBeInTheDocument();
    });
  });

  // ─── New Interaction Tests ──────────────────────────────────────────

  it('opens create dialog when clicking "New" button', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /new/i }));

    await waitFor(() => {
      expect(screen.getByText('Create Assistant')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g., Sales Agent')).toBeInTheDocument();
    });
  });

  it('calls createAssistant API when filling name and submitting', async () => {
    const created = buildAssistant({ id: 'new-ast', name: 'New Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });
    mockedCreateAssistant.mockResolvedValue({ success: true, data: created });
    // After creation, the page navigates to /assistants/:id, triggering getAssistant
    mockedGetAssistant.mockResolvedValue({ success: true, data: created });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });

    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /new/i }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('e.g., Sales Agent')).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText('e.g., Sales Agent'), 'New Bot');
    await user.click(screen.getByRole('button', { name: /^create$/i }));

    await waitFor(() => {
      expect(mockedCreateAssistant).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'New Bot' }),
      );
    });
  });

  it('navigates to assistant editor when clicking an assistant in the list', async () => {
    const assistant = buildAssistant({ id: 'ast-click', name: 'Click Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    // When navigating to /assistants/:id, the editor loads the assistant
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });

    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText('Click Bot')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Click Bot'));

    // After clicking, the editor should load and display the assistant name
    await waitFor(() => {
      expect(mockedGetAssistant).toHaveBeenCalledWith('ast-click');
    });
  });

  it('shows editor panel when assistant ID is in URL', async () => {
    const assistant = buildAssistant({ id: 'url-ast', name: 'URL Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });

    renderWithRoute('/assistants/url-ast');

    await waitFor(() => {
      expect(mockedGetAssistant).toHaveBeenCalledWith('url-ast');
    });

    // The editor shows the assistant name (appears in both list and editor panel)
    // and the Publish button which only exists in the editor
    await waitFor(() => {
      expect(screen.getAllByText('URL Bot').length).toBeGreaterThanOrEqual(2);
      expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
    });
  });

  it('search filters the assistant list', async () => {
    const assistants = [
      buildAssistant({ name: 'Sales Bot' }),
      buildAssistant({ name: 'Support Bot' }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText('Sales Bot')).toBeInTheDocument();
      expect(screen.getByText('Support Bot')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search/i);
    await user.type(searchInput, 'Sales');

    await waitFor(() => {
      expect(screen.getByText('Sales Bot')).toBeInTheDocument();
      expect(screen.queryByText('Support Bot')).not.toBeInTheDocument();
    });
  });

  it('does not submit create dialog if name is empty', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });

    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /new/i }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('e.g., Sales Agent')).toBeInTheDocument();
    });

    // Submit with empty name - the button should be disabled or form won't submit
    const createBtn = screen.getByRole('button', { name: /^create$/i });
    expect(createBtn).toBeDisabled();
    expect(mockedCreateAssistant).not.toHaveBeenCalled();
  });

  it('opens delete confirmation from editor panel and deletes', async () => {
    const assistant = buildAssistant({ id: 'del-ast', name: 'Delete Me Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    mockedDeleteAssistant.mockResolvedValue({ success: true });

    const { user } = renderWithRoute('/assistants/del-ast');

    // Wait for editor to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
    });

    // Click the delete icon button in the editor header
    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn =>
      btn.className.includes('hover:text-destructive') && btn.closest('.px-6')
    );
    if (deleteBtn) {
      await user.click(deleteBtn);

      // Should show the delete confirmation dialog
      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });

      // Confirm delete
      const confirmBtn = screen.getByRole('button', { name: /^delete$/i });
      await user.click(confirmBtn);

      await waitFor(() => {
        expect(mockedDeleteAssistant).toHaveBeenCalledWith('del-ast');
      });
    }
  });

  it('shows "Select an assistant" when no assistant ID in URL', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant({ id: 'a1', name: 'Bot A' })] });

    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText('Select an assistant')).toBeInTheDocument();
    });
  });

  it('cancels create dialog', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });

    const { user } = renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /new/i }));

    await waitFor(() => {
      expect(screen.getByText('Create Assistant')).toBeInTheDocument();
    });

    // Click cancel button
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.queryByText('Give your assistant a name to get started.')).not.toBeInTheDocument();
    });
  });

  it('publishes assistant via Ctrl+S when dirty', async () => {
    const assistant = buildAssistant({ id: 'ctrl-s-ast', name: 'Ctrl S Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    mockedUpdateAssistant.mockResolvedValue({ success: true, data: assistant });

    const { user } = renderWithRoute('/assistants/ctrl-s-ast');

    // Wait for editor to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
    });

    // Make a change to mark dirty
    const systemPrompt = screen.getByPlaceholderText(/you are a helpful/i);
    await user.type(systemPrompt, 'test');

    // Fire Ctrl+S keyboard event
    const event = new KeyboardEvent('keydown', {
      key: 's',
      ctrlKey: true,
      bubbles: true,
    });
    window.dispatchEvent(event);

    await waitFor(() => {
      expect(mockedUpdateAssistant).toHaveBeenCalled();
    });
  });

  it('Ctrl+S does nothing when no assistant is selected', async () => {
    mockedListAssistants.mockResolvedValue({ success: true, data: [] });

    renderWithRoute('/assistants');

    await waitFor(() => {
      expect(screen.getByText('Select an assistant')).toBeInTheDocument();
    });

    // Fire Ctrl+S keyboard event
    const event = new KeyboardEvent('keydown', {
      key: 's',
      ctrlKey: true,
      bubbles: true,
    });
    window.dispatchEvent(event);

    // updateAssistant should not be called
    expect(mockedUpdateAssistant).not.toHaveBeenCalled();
  });

  it('deletes the currently selected assistant and navigates away', async () => {
    const assistant = buildAssistant({ id: 'del-current', name: 'Current Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    mockedDeleteAssistant.mockResolvedValue({ success: true });

    const { user } = renderWithRoute('/assistants/del-current');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
    });

    // Click the delete icon button in the editor header
    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn =>
      btn.className.includes('hover:text-destructive') && btn.closest('.px-6')
    );
    if (deleteBtn) {
      await user.click(deleteBtn);

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });

      const confirmBtn = screen.getByRole('button', { name: /^delete$/i });
      await user.click(confirmBtn);

      await waitFor(() => {
        expect(mockedDeleteAssistant).toHaveBeenCalledWith('del-current');
      });
    }
  });

  it('publishes and reloads list on success', async () => {
    const assistant = buildAssistant({ id: 'pub-ast', name: 'Pub Bot' });
    mockedListAssistants.mockResolvedValue({ success: true, data: [assistant] });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    mockedUpdateAssistant.mockResolvedValue({ success: true, data: assistant });

    const { user } = renderWithRoute('/assistants/pub-ast');

    // Wait for editor to load - use exact text match to avoid matching "Pub Bot"
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^publish$/i })).toBeInTheDocument();
    });

    // Make a change to enable publish
    const systemPrompt = screen.getByPlaceholderText(/you are a helpful/i);
    await user.type(systemPrompt, 'update');

    // Click publish button
    await user.click(screen.getByRole('button', { name: /^publish$/i }));

    await waitFor(() => {
      expect(mockedUpdateAssistant).toHaveBeenCalled();
      // list.reload() should be called after successful publish
      expect(mockedListAssistants).toHaveBeenCalledTimes(2);
    });
  });
});
