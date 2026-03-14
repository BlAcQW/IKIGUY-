import type { Message } from '../providers/llm/types.js';
import { createSessionStore, type SessionStore } from './session-store.js';

export interface CallSession {
  id: string;
  callId: string;
  assistantId: string;
  organizationId: string;
  conversationHistory: Message[];
  status: 'active' | 'paused' | 'ended';
  startedAt: Date;
  metadata: Record<string, unknown>;
}

let store: SessionStore | null = null;

export function initializeSessionStore(redisUrl?: string): void {
  store = createSessionStore(redisUrl);
}

function getStore(): SessionStore {
  if (!store) {
    store = createSessionStore();
  }
  return store;
}

export async function createSession(params: {
  callId: string;
  assistantId: string;
  organizationId: string;
  systemPrompt?: string;
}): Promise<CallSession> {
  const session: CallSession = {
    id: crypto.randomUUID(),
    callId: params.callId,
    assistantId: params.assistantId,
    organizationId: params.organizationId,
    conversationHistory: params.systemPrompt
      ? [{ role: 'system', content: params.systemPrompt }]
      : [],
    status: 'active',
    startedAt: new Date(),
    metadata: {},
  };
  await getStore().set(session);
  return session;
}

export async function getSession(sessionId: string): Promise<CallSession | undefined> {
  return getStore().get(sessionId);
}

export async function endSession(sessionId: string): Promise<void> {
  const session = await getStore().get(sessionId);
  if (session) {
    await getStore().set({ ...session, status: 'ended' });
  }
}

export async function addMessage(sessionId: string, message: Message): Promise<void> {
  const session = await getStore().get(sessionId);
  if (session) {
    await getStore().set({
      ...session,
      conversationHistory: [...session.conversationHistory, message],
    });
  }
}

export async function updateAssistant(sessionId: string, assistantId: string): Promise<void> {
  const session = await getStore().get(sessionId);
  if (session) {
    await getStore().set({ ...session, assistantId });
  }
}
