import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { buildAssistant } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listAssistants: vi.fn(),
  deleteAssistant: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { useAssistantList } from './useAssistantList';
import { listAssistants, deleteAssistant } from '@/lib/api';

const mockedListAssistants = vi.mocked(listAssistants);
const mockedDeleteAssistant = vi.mocked(deleteAssistant);

describe('useAssistantList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads assistants on mount', async () => {
    const assistants = [buildAssistant({ name: 'Bot A' }), buildAssistant({ name: 'Bot B' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.assistants).toHaveLength(2);
    expect(result.current.assistants[0].name).toBe('Bot A');
  });

  it('filters by search term', async () => {
    const assistants = [
      buildAssistant({ name: 'Sales Bot', model: { provider: 'openai', model: 'gpt-4o' } }),
      buildAssistant({ name: 'Support Bot', model: { provider: 'openai', model: 'gpt-3.5-turbo' } }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.setSearch('Sales');
    });

    expect(result.current.assistants).toHaveLength(1);
    expect(result.current.assistants[0].name).toBe('Sales Bot');
  });

  it('filters by model name', async () => {
    const assistants = [
      buildAssistant({ name: 'Bot A', model: { provider: 'openai', model: 'gpt-4o' } }),
      buildAssistant({ name: 'Bot B', model: { provider: 'openai', model: 'gpt-3.5-turbo' } }),
    ];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.setSearch('3.5');
    });

    expect(result.current.assistants).toHaveLength(1);
    expect(result.current.assistants[0].name).toBe('Bot B');
  });

  it('handleDelete calls API and reloads', async () => {
    const assistants = [buildAssistant({ id: 'a1', name: 'Bot' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });
    mockedDeleteAssistant.mockResolvedValue({ success: true, data: null as unknown as void });

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleDelete('a1');
    });

    expect(mockedDeleteAssistant).toHaveBeenCalledWith('a1');
    // listAssistants called twice: mount + reload
    expect(mockedListAssistants).toHaveBeenCalledTimes(2);
  });

  it('handles load error gracefully', async () => {
    mockedListAssistants.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.assistants).toHaveLength(0);
  });

  it('handles delete error and shows toast', async () => {
    const assistants = [buildAssistant({ id: 'a1', name: 'Bot' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });
    mockedDeleteAssistant.mockRejectedValue(new Error('Delete error'));

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleDelete('a1');
    });

    const { toast } = await import('sonner');
    expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to delete assistant', expect.objectContaining({ description: 'Delete error' }));
  });

  it('handles delete error with non-Error object', async () => {
    const assistants = [buildAssistant({ id: 'a1' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });
    mockedDeleteAssistant.mockRejectedValue('string error');

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.handleDelete('a1');
    });

    const { toast } = await import('sonner');
    expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to delete assistant', expect.objectContaining({ description: 'Unknown error' }));
  });

  it('returns allAssistants unfiltered', async () => {
    const assistants = [buildAssistant({ name: 'A' }), buildAssistant({ name: 'B' })];
    mockedListAssistants.mockResolvedValue({ success: true, data: assistants });

    const { result } = renderHook(() => useAssistantList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.setSearch('A');
    });

    expect(result.current.assistants).toHaveLength(1);
    expect(result.current.allAssistants).toHaveLength(2);
  });
});
