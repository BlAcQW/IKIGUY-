import { describe, it, expect } from 'vitest';
import { InMemorySessionStore } from './session-store.js';
import type { CallSession } from './session.js';

function buildSession(overrides: Partial<CallSession> = {}): CallSession {
  return {
    id: 'session-1',
    callId: 'call-1',
    assistantId: 'assistant-1',
    organizationId: 'org-1',
    conversationHistory: [],
    status: 'active',
    startedAt: new Date('2026-01-01T00:00:00Z'),
    metadata: {},
    ...overrides,
  };
}

describe('InMemorySessionStore', () => {
  it('should store and retrieve a session', async () => {
    const store = new InMemorySessionStore();
    const session = buildSession();

    await store.set(session);
    const retrieved = await store.get('session-1');

    expect(retrieved).toEqual(session);
  });

  it('should return undefined for non-existent session', async () => {
    const store = new InMemorySessionStore();
    const retrieved = await store.get('non-existent');

    expect(retrieved).toBeUndefined();
  });

  it('should delete a session', async () => {
    const store = new InMemorySessionStore();
    const session = buildSession();

    await store.set(session);
    await store.delete('session-1');
    const retrieved = await store.get('session-1');

    expect(retrieved).toBeUndefined();
  });

  it('should overwrite existing session', async () => {
    const store = new InMemorySessionStore();
    const session = buildSession();

    await store.set(session);
    const updated = { ...session, status: 'ended' as const };
    await store.set(updated);

    const retrieved = await store.get('session-1');
    expect(retrieved?.status).toBe('ended');
  });

  it('should handle multiple sessions independently', async () => {
    const store = new InMemorySessionStore();

    await store.set(buildSession({ id: 'a' }));
    await store.set(buildSession({ id: 'b' }));

    await store.delete('a');

    expect(await store.get('a')).toBeUndefined();
    expect(await store.get('b')).toBeDefined();
  });
});
