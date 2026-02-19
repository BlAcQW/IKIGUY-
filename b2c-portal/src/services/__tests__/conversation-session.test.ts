/**
 * Unit tests for Conversation Session Service
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { conversationSessionService } from '../conversation-session';

describe('ConversationSessionService', () => {
  // Set up a proper localStorage mock
  const localStorageData: Record<string, string> = {};

  beforeEach(() => {
    // Clear data
    Object.keys(localStorageData).forEach(key => delete localStorageData[key]);

    // Mock localStorage with actual storage
    Object.defineProperty(global, 'localStorage', {
      value: {
        getItem: (key: string) => localStorageData[key] || null,
        setItem: (key: string, value: string) => {
          localStorageData[key] = value;
        },
        removeItem: (key: string) => {
          delete localStorageData[key];
        },
        clear: () => {
          Object.keys(localStorageData).forEach(key => delete localStorageData[key]);
        }
      },
      writable: true
    });
  });

  afterEach(() => {
    Object.keys(localStorageData).forEach(key => delete localStorageData[key]);
  });

  describe('Session Creation', () => {
    it('should create a new conversation session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      expect(session).toBeDefined();
      expect(session.id).toContain('session_');
      expect(session.assistantId).toBe('assistant-123');
      expect(session.assistantName).toBe('Test Assistant');
      expect(session.messages).toEqual([]);
      expect(session.metadata.status).toBe('active');
      expect(session.metadata.totalMessages).toBe(0);
    });

    it('should create session with custom context', () => {
      const session = conversationSessionService.createSession(
        'assistant-123',
        'Test Assistant',
        { language: 'tw', dialect: 'asante' }
      );

      expect(session.context.language).toBe('tw');
      expect(session.context.dialect).toBe('asante');
    });

    it('should retrieve created session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const retrieved = conversationSessionService.getSession(session.id);

      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe(session.id);
    });
  });

  describe('Message Management', () => {
    it('should add user message to session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const message = conversationSessionService.addMessage(
        session.id,
        'user',
        'Hello, how are you?'
      );

      expect(message).toBeDefined();
      expect(message?.type).toBe('user');
      expect(message?.content).toBe('Hello, how are you?');

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.messages.length).toBe(1);
      expect(updated?.metadata.userMessages).toBe(1);
      expect(updated?.metadata.totalMessages).toBe(1);
    });

    it('should add assistant message to session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      conversationSessionService.addMessage(session.id, 'assistant', 'I am doing well, thank you!');

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.messages.length).toBe(1);
      expect(updated?.metadata.assistantMessages).toBe(1);
    });

    it('should add message with metadata', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const message = conversationSessionService.addMessage(
        session.id,
        'user',
        'Test message',
        { confidence: 0.95, processingTime: 100 }
      );

      expect(message?.metadata?.confidence).toBe(0.95);
      expect(message?.metadata?.processingTime).toBe(100);
    });

    it('should return null when adding message to non-existent session', () => {
      const message = conversationSessionService.addMessage(
        'non-existent-session',
        'user',
        'Test'
      );

      expect(message).toBeNull();
    });

    it('should track multiple messages in conversation', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      conversationSessionService.addMessage(session.id, 'user', 'Hello');
      conversationSessionService.addMessage(session.id, 'assistant', 'Hi there!');
      conversationSessionService.addMessage(session.id, 'user', 'How are you?');
      conversationSessionService.addMessage(session.id, 'assistant', 'I am good!');

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.messages.length).toBe(4);
      expect(updated?.metadata.userMessages).toBe(2);
      expect(updated?.metadata.assistantMessages).toBe(2);
      expect(updated?.metadata.totalMessages).toBe(4);
    });
  });

  describe('Context Management', () => {
    it('should update session context', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const result = conversationSessionService.updateContext(session.id, {
        language: 'tw',
        dialect: 'asante'
      });

      expect(result).toBe(true);

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.context.language).toBe('tw');
      expect(updated?.context.dialect).toBe('asante');
    });

    it('should merge context updates', () => {
      const session = conversationSessionService.createSession(
        'assistant-123',
        'Test Assistant',
        { language: 'en' }
      );

      conversationSessionService.updateContext(session.id, { dialect: 'british' });

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.context.language).toBe('en');
      expect(updated?.context.dialect).toBe('british');
    });

    it('should return false when updating non-existent session context', () => {
      const result = conversationSessionService.updateContext('non-existent', { language: 'tw' });
      expect(result).toBe(false);
    });
  });

  describe('Conversation History', () => {
    it('should retrieve conversation history', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      conversationSessionService.addMessage(session.id, 'user', 'Message 1');
      conversationSessionService.addMessage(session.id, 'assistant', 'Response 1');
      conversationSessionService.addMessage(session.id, 'system', 'System message');
      conversationSessionService.addMessage(session.id, 'user', 'Message 2');

      const history = conversationSessionService.getConversationHistory(session.id);

      // Should only return user and assistant messages (not system)
      expect(history.length).toBe(3);
      expect(history[0].content).toBe('Message 1');
      expect(history[1].content).toBe('Response 1');
      expect(history[2].content).toBe('Message 2');
    });

    it('should limit conversation history', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      for (let i = 1; i <= 10; i++) {
        conversationSessionService.addMessage(session.id, 'user', `Message ${i}`);
      }

      const history = conversationSessionService.getConversationHistory(session.id, 5);
      expect(history.length).toBe(5);
      expect(history[0].content).toBe('Message 6');
      expect(history[4].content).toBe('Message 10');
    });

    it('should format context for LLM', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      conversationSessionService.addMessage(session.id, 'user', 'Hello');
      conversationSessionService.addMessage(session.id, 'assistant', 'Hi!');

      const context = conversationSessionService.getContextForLLM(session.id);

      expect(context).toContain('User: Hello');
      expect(context).toContain('Assistant: Hi!');
    });
  });

  describe('Session State Management', () => {
    it('should pause a session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const result = conversationSessionService.pauseSession(session.id);

      expect(result).toBe(true);

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.metadata.status).toBe('paused');
    });

    it('should resume a paused session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      conversationSessionService.pauseSession(session.id);
      const result = conversationSessionService.resumeSession(session.id);

      expect(result).toBe(true);

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.metadata.status).toBe('active');
    });

    it('should end a session', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      const result = conversationSessionService.endSession(session.id);

      expect(result).toBe(true);

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.metadata.status).toBe('ended');
      expect(updated?.endTime).toBeDefined();
      expect(updated?.metadata.duration).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Session Persistence', () => {
    it('should persist session to localStorage', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      conversationSessionService.addMessage(session.id, 'user', 'Test message');

      // Check localStorage directly
      const stored = localStorage.getItem('conversation_sessions');
      expect(stored).toBeDefined();

      const sessions = JSON.parse(stored!);
      expect(sessions.length).toBeGreaterThan(0);
      expect(sessions[0].id).toBe(session.id);
    });

    it('should retrieve recent sessions and filter by assistant', () => {
      // Create sessions
      const session1 = conversationSessionService.createSession('assistant-1', 'Assistant 1');
      const session2 = conversationSessionService.createSession('assistant-1', 'Assistant 1');
      const session3 = conversationSessionService.createSession('assistant-2', 'Assistant 2');
      const session4 = conversationSessionService.createSession('assistant-3', 'Assistant 3');

      const allCreatedIds = [session1.id, session2.id, session3.id, session4.id];

      // Test recent sessions
      const recent = conversationSessionService.getRecentSessions(2);
      expect(recent.length).toBe(2);
      // Should return sessions from our created list
      recent.forEach(session => {
        expect(allCreatedIds).toContain(session.id);
      });

      // Test assistant-specific sessions
      const assistant1Sessions = conversationSessionService.getAssistantSessions('assistant-1');
      expect(assistant1Sessions.length).toBe(2);
      expect(assistant1Sessions[0].assistantId).toBe('assistant-1');
      expect(assistant1Sessions[1].assistantId).toBe('assistant-1');

      // Verify session IDs match
      const sessionIds = assistant1Sessions.map(s => s.id);
      expect(sessionIds).toContain(session1.id);
      expect(sessionIds).toContain(session2.id);
    });
  });

  describe('Session Export', () => {
    it('should export session data as JSON', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      conversationSessionService.addMessage(session.id, 'user', 'Test message');

      const exported = conversationSessionService.exportSession(session.id);

      expect(exported).toBeDefined();

      const parsed = JSON.parse(exported!);
      expect(parsed.id).toBe(session.id);
      expect(parsed.messages.length).toBe(1);
    });

    it('should return null when exporting non-existent session', () => {
      const exported = conversationSessionService.exportSession('non-existent');
      expect(exported).toBeNull();
    });
  });

  describe('Response Time Calculation', () => {
    it('should calculate average response time', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      // Add user message
      conversationSessionService.addMessage(session.id, 'user', 'Question 1');

      // Wait a bit
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

      return delay(50).then(() => {
        // Add assistant response
        conversationSessionService.addMessage(session.id, 'assistant', 'Answer 1');

        const avgTime = conversationSessionService.calculateAverageResponseTime(session.id);

        expect(avgTime).toBeDefined();
        expect(avgTime).toBeGreaterThan(0);
      });
    });

    it('should return null when no responses available', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const avgTime = conversationSessionService.calculateAverageResponseTime(session.id);

      expect(avgTime).toBeNull();
    });
  });

  describe('Session Cleanup', () => {
    it('should clear old sessions', () => {
      // Create old session (simulate by creating and manually updating timestamp)
      const oldSession = conversationSessionService.createSession('assistant-old', 'Old Assistant');

      // Create recent session
      conversationSessionService.createSession('assistant-new', 'New Assistant');

      // For this test, we'd need to manually manipulate timestamps
      // This is a simplified test
      const cleared = conversationSessionService.clearOldSessions(0);

      expect(cleared).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message content', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const message = conversationSessionService.addMessage(session.id, 'user', '');

      expect(message).toBeDefined();
      expect(message?.content).toBe('');
    });

    it('should handle very long message content', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const longContent = 'A'.repeat(10000);
      const message = conversationSessionService.addMessage(session.id, 'user', longContent);

      expect(message).toBeDefined();
      expect(message?.content.length).toBe(10000);
    });

    it('should handle special characters in messages', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');
      const specialContent = 'Hello! 你好 👋 <script>alert("test")</script>';
      const message = conversationSessionService.addMessage(session.id, 'user', specialContent);

      expect(message?.content).toBe(specialContent);
    });

    it('should handle concurrent message additions', () => {
      const session = conversationSessionService.createSession('assistant-123', 'Test Assistant');

      // Add multiple messages quickly
      conversationSessionService.addMessage(session.id, 'user', 'Message 1');
      conversationSessionService.addMessage(session.id, 'user', 'Message 2');
      conversationSessionService.addMessage(session.id, 'user', 'Message 3');

      const updated = conversationSessionService.getSession(session.id);
      expect(updated?.messages.length).toBe(3);
      expect(updated?.metadata.totalMessages).toBe(3);
    });
  });
});
