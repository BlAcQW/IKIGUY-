/**
 * Chat API client for EstateFlow.
 *
 * Provides functions to interact with the property chat endpoints.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import { getAuthTokenSync } from "../auth";

/**
 * Message role in conversation.
 */
export type MessageRole = "user" | "assistant" | "system";

/**
 * Question category detected by AI.
 */
export type QuestionCategory =
  | "location"
  | "financial"
  | "property_features"
  | "pet_policy"
  | "neighborhood_safety"
  | "availability"
  | "general";

/**
 * Chat message in conversation.
 */
export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp: string;
}

/**
 * Source attribution for AI response.
 */
export interface Source {
  type: string;
  field?: string;
  value?: any;
}

/**
 * Chat request payload.
 */
export interface ChatRequest {
  property_id: string;
  message: string;
  conversation_history: ChatMessage[];
  language?: string;
}

/**
 * Chat response from AI.
 */
export interface ChatResponse {
  reply: string;
  sources: Source[];
  confidence: number;
  question_category: QuestionCategory;
  suggested_questions: string[];
  processing_time_ms: number;
  model_used: string;
}

/**
 * Get authentication token from localStorage or session storage.
 * TODO: Replace with actual auth implementation
 */

/**
 * Send a chat message about a property.
 *
 * @param propertyId - Property ID
 * @param request - Chat request
 * @returns Promise<ChatResponse>
 */
export async function sendChatMessage(
  propertyId: string,
  request: Omit<ChatRequest, "property_id">
): Promise<ChatResponse> {
  const url = buildApiUrl(`/api/v1/chat/properties/${propertyId}`);
  const token = getAuthTokenSync();

  const payload: ChatRequest = {
    property_id: propertyId,
    ...request,
  };

  const response = await fetch(url, {
    method: "POST",
    headers: getDefaultHeaders(token || undefined),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to send chat message" }));
    throw new Error(error.detail || "Failed to send chat message");
  }

  return response.json();
}

/**
 * Check chat service health.
 *
 * @returns Promise<{status: string, service: string, llm_service: string}>
 */
export async function checkChatHealth(): Promise<{
  status: string;
  service: string;
  llm_service: string;
}> {
  const url = buildApiUrl("/api/v1/chat/health");

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(),
  });

  if (!response.ok) {
    throw new Error("Chat service health check failed");
  }

  return response.json();
}

// ==================== Conversation Management ====================

export interface Conversation {
  id: string;
  property_id: string;
  title?: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * List conversations.
 *
 * @param params - Query parameters
 * @returns Promise<ConversationListResponse>
 */
export async function listConversations(params?: {
  limit?: number;
  offset?: number;
}): Promise<ConversationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());

  const url = buildApiUrl(`/api/v1/chat/conversations?${searchParams}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to list conversations" }));
    throw new Error(error.detail || "Failed to list conversations");
  }

  return response.json();
}

/**
 * Get a single conversation by ID.
 *
 * @param conversationId - Conversation ID
 * @returns Promise<Conversation>
 */
export async function getConversation(conversationId: string): Promise<Conversation> {
  const url = buildApiUrl(`/api/v1/chat/conversations/${conversationId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get conversation" }));
    throw new Error(error.detail || "Failed to get conversation");
  }

  return response.json();
}

/**
 * Delete a conversation.
 *
 * @param conversationId - Conversation ID
 * @returns Promise<void>
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  const url = buildApiUrl(`/api/v1/chat/conversations/${conversationId}`);
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    method: "DELETE",
    headers: getDefaultHeaders(token || undefined),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to delete conversation" }));
    throw new Error(error.detail || "Failed to delete conversation");
  }
}
