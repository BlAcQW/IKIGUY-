import { describe, it, expect } from 'vitest';
import { createSession, getSession, endSession, addMessage } from './session.js';

describe('session management', () => {
  describe('createSession', () => {
    it('creates a session with a unique ID', async () => {
      const session = await createSession({
        callId: 'call-1',
        assistantId: 'ast-1',
        organizationId: 'org-1',
      });

      expect(session.id).toBeDefined();
      expect(session.callId).toBe('call-1');
      expect(session.status).toBe('active');
    });

    it('initializes with system prompt when provided', async () => {
      const session = await createSession({
        callId: 'call-1',
        assistantId: 'ast-1',
        organizationId: 'org-1',
        systemPrompt: 'You are a helpful assistant',
      });

      expect(session.conversationHistory).toHaveLength(1);
      expect(session.conversationHistory[0]).toEqual({
        role: 'system',
        content: 'You are a helpful assistant',
      });
    });

    it('initializes empty history when no system prompt', async () => {
      const session = await createSession({
        callId: 'call-1',
        assistantId: 'ast-1',
        organizationId: 'org-1',
      });

      expect(session.conversationHistory).toHaveLength(0);
    });
  });

  describe('getSession', () => {
    it('returns the session by ID', async () => {
      const created = await createSession({
        callId: 'call-2',
        assistantId: 'ast-1',
        organizationId: 'org-1',
      });

      const found = await getSession(created.id);
      expect(found?.id).toBe(created.id);
    });

    it('returns undefined for unknown ID', async () => {
      const found = await getSession('nonexistent-id');
      expect(found).toBeUndefined();
    });
  });

  describe('endSession', () => {
    it('marks session as ended', async () => {
      const session = await createSession({
        callId: 'call-3',
        assistantId: 'ast-1',
        organizationId: 'org-1',
      });

      await endSession(session.id);

      const updated = await getSession(session.id);
      expect(updated?.status).toBe('ended');
    });

    it('does nothing for unknown session', async () => {
      // Should not throw
      await endSession('nonexistent');
    });
  });

  describe('addMessage', () => {
    it('appends message to conversation history', async () => {
      const session = await createSession({
        callId: 'call-4',
        assistantId: 'ast-1',
        organizationId: 'org-1',
      });

      await addMessage(session.id, { role: 'user', content: 'Hello' });

      const updated = await getSession(session.id);
      expect(updated?.conversationHistory).toHaveLength(1);
      expect(updated?.conversationHistory[0]).toEqual({
        role: 'user',
        content: 'Hello',
      });
    });

    it('preserves existing messages', async () => {
      const session = await createSession({
        callId: 'call-5',
        assistantId: 'ast-1',
        organizationId: 'org-1',
        systemPrompt: 'Be helpful',
      });

      await addMessage(session.id, { role: 'user', content: 'Hi' });
      await addMessage(session.id, { role: 'assistant', content: 'Hello!' });

      const updated = await getSession(session.id);
      expect(updated?.conversationHistory).toHaveLength(3);
    });

    it('does nothing for unknown session', async () => {
      await addMessage('nonexistent', { role: 'user', content: 'test' });
      // Should not throw
    });
  });
});
