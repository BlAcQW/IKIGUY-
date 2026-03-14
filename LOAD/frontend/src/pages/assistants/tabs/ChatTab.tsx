import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Bot, User, Send, Loader2 } from 'lucide-react';
import { chatWithAssistant } from '@/lib/api';

interface ChatTabProps {
  assistantId?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatTab({ assistantId }: ChatTabProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !assistantId || sending) return;

    const userMessage = input.trim();
    setInput('');
    const updatedMessages: ChatMessage[] = [...messages, { role: 'user', content: userMessage }];
    setMessages(updatedMessages);
    setSending(true);

    try {
      const result = await chatWithAssistant(assistantId, updatedMessages);
      setMessages((prev) => [...prev, { role: 'assistant', content: result.data.message }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!assistantId) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        Save the assistant first to use chat.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[500px] animate-fade-in">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin space-y-3 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            Send a message to start chatting with your assistant.
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                msg.role === 'user'
                  ? 'bg-primary/10 text-primary'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
            </div>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-md'
                  : 'bg-muted text-foreground rounded-bl-md'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex gap-2.5">
            <div className="w-6 h-6 rounded-md flex items-center justify-center shrink-0 bg-muted text-muted-foreground">
              <Bot size={12} />
            </div>
            <div className="bg-muted rounded-xl rounded-bl-md px-3 py-2">
              <Loader2 size={14} className="animate-spin text-muted-foreground" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex gap-2 shrink-0">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 h-10 bg-background"
          disabled={sending}
        />
        <Button type="submit" disabled={!input.trim() || sending} size="sm" className="h-10 px-4">
          <Send size={14} />
        </Button>
      </form>
    </div>
  );
}
