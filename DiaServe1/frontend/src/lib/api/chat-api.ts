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
