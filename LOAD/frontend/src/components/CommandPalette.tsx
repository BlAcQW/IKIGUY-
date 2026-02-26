import { useEffect, useState, useCallback } from 'react';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import { navSections } from '@/lib/navigation';
import { listAssistants } from '@/lib/api';
import type { Assistant } from '@/types';
import { Bot, Plus, Settings, Search } from 'lucide-react';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!open) return;
    setSearch('');
    listAssistants(1, 50)
      .then((res) => setAssistants(res.data))
      .catch(() => {});
  }, [open]);

  const runAction = useCallback(
    (action: () => void) => {
      onOpenChange(false);
      action();
    },
    [onOpenChange],
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="absolute left-1/2 top-[20%] -translate-x-1/2 w-full max-w-[540px]">
        <Command
          className="bg-popover border border-border rounded-xl shadow-2xl overflow-hidden"
          loop
        >
          <div className="flex items-center gap-3 px-4 border-b border-border">
            <Search size={16} className="text-muted-foreground shrink-0" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Type a command or search..."
              className="flex-1 h-12 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono text-muted-foreground border border-border">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-[320px] overflow-y-auto scrollbar-thin p-2">
            <Command.Empty className="py-8 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            {/* Navigation */}
            <Command.Group heading="Navigation" className="mb-1">
              {navSections.flatMap((section) =>
                section.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Command.Item
                      key={item.path}
                      value={`${item.label} ${section.label}`}
                      onSelect={() => runAction(() => navigate(item.path))}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
                    >
                      <Icon size={16} className="text-muted-foreground shrink-0" />
                      <span className="flex-1">{item.label}</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                        {section.label}
                      </span>
                    </Command.Item>
                  );
                }),
              )}
            </Command.Group>

            {/* Assistants */}
            {assistants.length > 0 && (
              <Command.Group heading="Assistants" className="mb-1">
                {assistants.map((a) => (
                  <Command.Item
                    key={a.id}
                    value={`assistant ${a.name}`}
                    onSelect={() => runAction(() => navigate(`/assistants/${a.id}`))}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
                  >
                    <Bot size={16} className="text-muted-foreground shrink-0" />
                    <span className="flex-1">{a.name}</span>
                    <span className="text-[10px] text-muted-foreground">Edit</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Actions */}
            <Command.Group heading="Actions" className="mb-1">
              <Command.Item
                value="create new assistant"
                onSelect={() => runAction(() => navigate('/assistants?create=true'))}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
              >
                <Plus size={16} className="text-muted-foreground shrink-0" />
                <span className="flex-1">Create Assistant</span>
              </Command.Item>
              <Command.Item
                value="open settings preferences"
                onSelect={() => runAction(() => navigate('/settings'))}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-foreground data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
              >
                <Settings size={16} className="text-muted-foreground shrink-0" />
                <span className="flex-1">Open Settings</span>
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
