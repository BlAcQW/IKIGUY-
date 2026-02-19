import { renderHook, waitFor } from '@testing-library/react';
import { useAssistants } from '../useCoreApi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { coreApi } from '@/lib/core-api';

const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: mockToast }) }));

vi.mock('@/lib/core-api', () => ({
  coreApi: { assistant: { list: vi.fn() } }
}));

describe('useAssistants hook', () => {
  const wrapper = ({ children }: any) => (
    <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    mockToast.mockReset();
    (coreApi.assistant.list as any).mockReset();
  });

  it('returns assistants on success', async () => {
    (coreApi.assistant.list as any).mockResolvedValue([{ id: 'a1' }]);
    const { result } = renderHook(() => useAssistants('tenant1'), { wrapper });
    await waitFor(() => expect(result.current.assistants).toHaveLength(1));
  });

  it('does not fetch when tenantId missing', async () => {
    const { result } = renderHook(() => useAssistants(''), { wrapper });
    expect(result.current.assistants).toEqual([]);
  });

  it('handles errors', async () => {
    (coreApi.assistant.list as any).mockRejectedValue(new Error('fail'));
    const { result } = renderHook(() => useAssistants('tenant1'), { wrapper });
    await waitFor(() => expect(result.current.assistantsError).toBeDefined());
  });
});
