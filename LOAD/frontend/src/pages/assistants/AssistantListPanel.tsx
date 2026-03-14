import { Bot, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import type { Assistant } from '@/types';

interface AssistantListPanelProps {
  assistants: Assistant[];
  loading: boolean;
  search: string;
  onSearchChange: (value: string) => void;
  selectedId: string | undefined;
  onSelect: (id: string) => void;
  onCreate: () => void;
}

function getProviderTag(assistant: Assistant): string {
  const transcriber = assistant.transcriber?.provider ?? 'openai';
  const model = assistant.model?.provider ?? 'openai';
  const voice = assistant.voice?.provider ?? 'openai';
  const parts = [transcriber, model, voice].map((p) => {
    const map: Record<string, string> = {
      openai: 'openai',
      anthropic: 'anthropic',
      google: 'google',
      elevenlabs: 'elevenlabs',
      deepgram: 'deepgram',
    };
    return map[p] ?? p;
  });
  return parts.join(' . ');
}

export function AssistantListPanel({
  assistants,
  loading,
  search,
  onSearchChange,
  selectedId,
  onSelect,
  onCreate,
}: AssistantListPanelProps) {
  return (
    <div className="w-[300px] shrink-0 border-r border-panel-border bg-panel flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-5 pb-3 border-b border-panel-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-display font-semibold text-foreground">Assistants</h2>
          <Button
            size="sm"
            onClick={onCreate}
            className="h-7 px-2.5 text-xs font-semibold"
          >
            <Plus size={14} className="mr-1" />
            New
          </Button>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search assistants..."
            className="h-8 pl-8 text-xs bg-background"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-2">
        {loading ? (
          <div className="space-y-2 p-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 rounded-lg">
                <Skeleton className="h-4 w-28 mb-2" />
                <Skeleton className="h-3 w-20" />
              </div>
            ))}
          </div>
        ) : assistants.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center mb-3">
              <Bot size={18} className="text-muted-foreground/40" />
            </div>
            <p className="text-xs text-muted-foreground text-center">
              {search ? 'No assistants match your search.' : 'No assistants yet. Create one to get started.'}
            </p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {assistants.map((a) => (
              <button
                key={a.id}
                onClick={() => onSelect(a.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150 group ${
                  selectedId === a.id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'hover:bg-white/[0.03] border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                      selectedId === a.id
                        ? 'bg-primary/15 text-primary'
                        : 'bg-muted/50 text-muted-foreground'
                    }`}
                  >
                    <Bot size={14} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p
                        className={`text-[13px] font-medium truncate ${
                          selectedId === a.id ? 'text-primary' : 'text-foreground'
                        }`}
                      >
                        {a.name}
                      </p>
                      <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                        true ? 'bg-emerald-500' : 'bg-muted-foreground/30'
                      }`} title="Published" />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5 truncate">
                      {getProviderTag(a)}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
