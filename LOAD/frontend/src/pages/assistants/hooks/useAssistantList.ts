import { useEffect, useState, useCallback, useMemo } from 'react';
import { listAssistants, deleteAssistant } from '@/lib/api';
import type { Assistant } from '@/types';
import { toast } from 'sonner';

export function useAssistantList() {
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await listAssistants();
      setAssistants(result.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to load assistants', { description: message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!search.trim()) return assistants;
    const q = search.toLowerCase();
    return assistants.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.model.model.toLowerCase().includes(q)
    );
  }, [assistants, search]);

  const handleDelete = useCallback(
    async (id: string) => {
      setDeleting(true);
      try {
        await deleteAssistant(id);
        toast.success('Assistant deleted');
        await load();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        toast.error('Failed to delete assistant', { description: message });
      } finally {
        setDeleting(false);
      }
    },
    [load]
  );

  return {
    assistants: filtered,
    allAssistants: assistants,
    loading,
    search,
    setSearch,
    deleting,
    handleDelete,
    reload: load,
  };
}
