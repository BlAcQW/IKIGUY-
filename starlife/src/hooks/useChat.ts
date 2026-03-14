import { useState, useCallback, useRef } from 'react';
import { sendMessage as callVapiChat } from '@/lib/vapi-chat';
import { CHAT_CONFIG } from '@/data/chat';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: CHAT_CONFIG.welcomeMessage,
      },
    ],
    isLoading: false,
    error: null,
  });

  const previousChatIdRef = useRef<string | undefined>(undefined);

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMsg],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await callVapiChat(trimmed, previousChatIdRef.current);
      previousChatIdRef.current = response.id;

      const assistantContent =
        response.output.find((o) => o.role === 'assistant')?.content ??
        response.output[0]?.content ??
        'Sorry, I could not generate a response.';

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMsg],
        isLoading: false,
      }));
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === 'AbortError'
          ? CHAT_CONFIG.timeoutMessage
          : CHAT_CONFIG.errorMessage;

      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
    }
  }, []);

  const clearChat = useCallback(() => {
    previousChatIdRef.current = undefined;
    setState({
      messages: [
        {
          id: 'welcome',
          role: 'assistant',
          content: CHAT_CONFIG.welcomeMessage,
        },
      ],
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage,
    clearChat,
  };
}
