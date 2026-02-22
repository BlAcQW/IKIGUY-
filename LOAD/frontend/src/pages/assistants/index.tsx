import { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { AlertDialog } from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AssistantListPanel } from './AssistantListPanel';
import { AssistantEditorPanel } from './AssistantEditorPanel';
import { useAssistantList } from './hooks/useAssistantList';
import { useAssistantEditor } from './hooks/useAssistantEditor';

export function AssistantsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const list = useAssistantList();
  const editor = useAssistantEditor(id);

  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  // Ctrl/Cmd+S to publish
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (id && editor.dirty && !editor.saving) {
          editor.publish();
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [id, editor]);

  const handleSelect = useCallback(
    (assistantId: string) => {
      navigate(`/assistants/${assistantId}`);
    },
    [navigate]
  );

  const handleCreate = useCallback(async () => {
    if (!createName.trim()) return;
    const created = await editor.create(createName.trim());
    if (created) {
      setCreateOpen(false);
      setCreateName('');
      await list.reload();
      navigate(`/assistants/${created.id}`);
    }
  }, [createName, editor, list, navigate]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    await list.handleDelete(deleteTarget.id);
    setDeleteTarget(null);
    if (id === deleteTarget.id) {
      navigate('/assistants');
    }
  }, [deleteTarget, list, id, navigate]);

  const handleEditorDelete = useCallback(() => {
    if (editor.assistant) {
      setDeleteTarget({ id: editor.assistant.id, name: editor.assistant.name });
    }
  }, [editor.assistant]);

  const handlePublish = useCallback(async () => {
    const updated = await editor.publish();
    if (updated) {
      await list.reload();
    }
  }, [editor, list]);

  return (
    <div className="flex h-full">
      {/* Left: Assistant List */}
      <AssistantListPanel
        assistants={list.assistants}
        loading={list.loading}
        search={list.search}
        onSearchChange={list.setSearch}
        selectedId={id}
        onSelect={handleSelect}
        onCreate={() => setCreateOpen(true)}
      />

      {/* Right: Editor */}
      <AssistantEditorPanel
        form={editor.form}
        updateField={editor.updateField}
        loading={editor.loading}
        saving={editor.saving}
        dirty={editor.dirty}
        onPublish={handlePublish}
        onDelete={handleEditorDelete}
        hasAssistant={!!id && !!editor.assistant}
      />

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-display">Create Assistant</DialogTitle>
            <DialogDescription>
              Give your assistant a name to get started.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleCreate();
            }}
          >
            <div className="space-y-2 py-2">
              <Label className="text-xs font-medium">Name</Label>
              <Input
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="e.g., Sales Agent"
                className="h-10"
                autoFocus
                required
              />
            </div>
            <DialogFooter className="pt-4">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={editor.saving || !createName.trim()} className="font-semibold">
                {editor.saving ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Assistant"
        description={`Are you sure you want to delete "${deleteTarget?.name ?? ''}"? This will also remove all associated calls, phone number assignments, and campaigns. This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        loading={list.deleting}
        onConfirm={handleDelete}
      />
    </div>
  );
}
