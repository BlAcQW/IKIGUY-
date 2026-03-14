/**
 * React Query hook for property chat.
 *
 * Manages chat state, message history, and API interactions.
 */

import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  sendChatMessage,
  ChatMessage,
  ChatResponse,
} from "@/lib/api/chat-api";

export interface UsePropertyChatOptions {
  propertyId: string;
  language?: string;
}

export interface UsePropertyChatReturn {
  messages: ChatMessage[];
  sendMessage: (message: string) => void;
  isLoading: boolean;
  error: Error | null;
  lastResponse: ChatResponse | null;
  clearMessages: () => void;
  retry: () => void;
}

/**
 * Hook for managing property chat interactions.
 *
 * @param options - Chat configuration options
 * @returns Chat state and methods
 */
export function usePropertyChat({
  propertyId,
  language = "en",
}: UsePropertyChatOptions): UsePropertyChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);

  // Mutation for sending messages
  const mutation = useMutation({
    mutationFn: async (message: string) => {
      // Build conversation history from messages (exclude assistant's internal metadata)
      const conversationHistory = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      const response = await sendChatMessage(propertyId, {
        message,
        conversation_history: conversationHistory,
        language,
      });

      return { message, response };
    },
    onSuccess: ({ message, response }) => {
      // Add user message
      const userMessage: ChatMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.reply,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setLastResponse(response);
      setLastFailedMessage(null);
    },
    onError: (_error, message) => {
      // Preserve the user's message so it appears in the chat
      const userMessage: ChatMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setLastFailedMessage(message);
    },
  });

  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim()) return;
      mutation.mutate(message);
    },
    [mutation]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastResponse(null);
    setLastFailedMessage(null);
  }, []);

  const retry = useCallback(() => {
    if (!lastFailedMessage) return;
    // Remove the failed user message before retrying
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "user" && last.content === lastFailedMessage) {
        return prev.slice(0, -1);
      }
      return prev;
    });
    mutation.mutate(lastFailedMessage);
  }, [lastFailedMessage, mutation]);

  return {
    messages,
    sendMessage,
    isLoading: mutation.isPending,
    error: mutation.error,
    lastResponse,
    clearMessages,
    retry,
  };
}
