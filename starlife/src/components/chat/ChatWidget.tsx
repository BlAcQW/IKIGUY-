import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import { MessageCircle, X, Send, RotateCcw, Phone, PhoneOff } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useChat, type ChatMessage } from '@/hooks/useChat';
import { useVapiCall, type CallStatus } from '@/hooks/useVapiCall';
import { CallOverlay } from '@/components/chat/CallOverlay';
import { CHAT_CONFIG } from '@/data/chat';

const supportsWebRTC =
  typeof window !== 'undefined' &&
  typeof navigator?.mediaDevices?.getUserMedia === 'function';

/* ─── Chat Button (FAB) ─── */

function ChatButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label="Open chat"
      className="fixed bottom-6 right-6 z-[60] flex h-14 w-14 items-center justify-center rounded-full bg-navy shadow-lg transition-transform hover:scale-105 active:scale-95"
    >
      <MessageCircle className="h-6 w-6 text-gold" />
    </button>
  );
}

/* ─── Chat Header ─── */

function ChatHeader({
  onClose,
  onClear,
  callStatus,
  onCallToggle,
}: {
  onClose: () => void;
  onClear: () => void;
  callStatus: CallStatus;
  onCallToggle: () => void;
}) {
  const isCallActive = callStatus === 'connecting' || callStatus === 'active';

  return (
    <div className="flex items-center justify-between rounded-t-2xl bg-navy px-4 py-3 max-sm:rounded-none">
      <div>
        <h3 className="text-sm font-semibold text-white">{CHAT_CONFIG.title}</h3>
        <p className="text-xs text-white/70">{CHAT_CONFIG.subtitle}</p>
      </div>
      <div className="flex items-center gap-1">
        {supportsWebRTC && (
          <button
            onClick={onCallToggle}
            aria-label={isCallActive ? 'End voice call' : CHAT_CONFIG.call.callTooltip}
            title={isCallActive ? 'End voice call' : CHAT_CONFIG.call.callTooltip}
            className={`rounded-lg p-1.5 transition-colors ${
              isCallActive
                ? 'text-red-400 hover:bg-white/10 hover:text-red-300'
                : 'text-white/70 hover:bg-white/10 hover:text-white'
            }`}
          >
            {isCallActive ? (
              <PhoneOff className="h-4 w-4" />
            ) : (
              <Phone className="h-4 w-4" />
            )}
          </button>
        )}
        <button
          onClick={onClear}
          aria-label="Clear chat"
          className="rounded-lg p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        <button
          onClick={onClose}
          aria-label="Close chat"
          className="rounded-lg p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

/* ─── Chat Bubble ─── */

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'rounded-br-md bg-navy text-white'
            : 'rounded-bl-md border border-gray-200 bg-white text-gray-800 shadow-sm prose prose-sm prose-gray max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0'
        }`}
      >
        {isUser ? message.content : <ReactMarkdown>{message.content}</ReactMarkdown>}
      </div>
    </div>
  );
}

/* ─── Typing Indicator ─── */

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-gray-200 bg-white px-4 py-3 shadow-sm">
        <span className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400" />
        <span className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400 [animation-delay:150ms]" />
        <span className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400 [animation-delay:300ms]" />
      </div>
    </div>
  );
}

/* ─── Chat Messages ─── */

function ChatMessages({
  messages,
  isLoading,
  error,
}: {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <TypingIndicator />}
      {error && (
        <div className="text-center text-xs text-red-500">{error}</div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

/* ─── Chat Input ─── */

function ChatInput({
  onSend,
  isLoading,
}: {
  onSend: (text: string) => void;
  isLoading: boolean;
}) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSend(value);
      setValue('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSend(value);
        setValue('');
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-gray-200 px-4 py-3"
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={CHAT_CONFIG.placeholder}
        rows={1}
        className="flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-navy"
      />
      <button
        type="submit"
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gold text-navy-dark transition-colors hover:bg-gold-light disabled:opacity-40 disabled:hover:bg-gold"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}

/* ─── Chat Panel ─── */

function ChatPanel({ onClose }: { onClose: () => void }) {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const call = useVapiCall();

  const showOverlay = call.status !== 'idle';

  const handleCallToggle = () => {
    if (call.status === 'connecting' || call.status === 'active') {
      call.endCall();
    } else {
      call.startCall();
    }
  };

  // Combine text chat error with call error
  const displayError = call.error ?? error;

  return (
    <div className="fixed bottom-24 right-6 z-[60] flex h-[520px] w-[380px] animate-chat-open flex-col overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 shadow-2xl max-sm:inset-0 max-sm:bottom-0 max-sm:right-0 max-sm:h-full max-sm:w-full max-sm:rounded-none">
      <ChatHeader
        onClose={onClose}
        onClear={clearChat}
        callStatus={call.status}
        onCallToggle={handleCallToggle}
      />
      <div className="relative flex flex-1 flex-col overflow-hidden">
        <ChatMessages messages={messages} isLoading={isLoading} error={displayError} />
        {showOverlay && (
          <CallOverlay
            status={call.status}
            isMuted={call.isMuted}
            duration={call.duration}
            onToggleMute={call.toggleMute}
            onEndCall={call.endCall}
          />
        )}
      </div>
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

/* ─── Chat Widget (Root) ─── */

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {isOpen ? (
        <ChatPanel onClose={() => setIsOpen(false)} />
      ) : (
        <ChatButton onClick={() => setIsOpen(true)} />
      )}
    </>
  );
}
