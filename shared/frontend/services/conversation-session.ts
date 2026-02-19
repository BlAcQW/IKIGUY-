/**
 * Shared Conversation Session Management Service
 *
 * Manages conversation sessions for voice interactions including:
 * - Session creation and metadata tracking
 * - Conversation history management
 * - Session persistence and restoration
 * - Context management across conversation turns
 */

export interface ConversationMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  audio?: string;
  metadata?: {
    confidence?: number;
    processingTime?: number;
    partialTranscript?: boolean;
  };
}

export interface ConversationContext {
  language?: string;
  dialect?: string;
  transport?: 'websocket' | 'webrtc';
  userPreferences?: Record<string, any>;
  customData?: Record<string, any>;
}

export interface ConversationSession {
  id: string;
  assistantId: string;
  assistantName: string;
  startTime: Date;
  endTime?: Date;
  messages: ConversationMessage[];
  context: ConversationContext;
  metadata: {
    totalMessages: number;
    userMessages: number;
    assistantMessages: number;
    duration: number;
    averageResponseTime?: number;
    status: 'active' | 'paused' | 'ended';
  };
}

class ConversationSessionService {
  private activeSessions: Map<string, ConversationSession> = new Map();
  private storageKey = 'shared_conversation_sessions';

  /**
   * Create a new conversation session
   */
  createSession(assistantId: string, assistantName: string, context?: ConversationContext): ConversationSession {
    const session: ConversationSession = {
      id: this.generateSessionId(),
      assistantId,
      assistantName,
      startTime: new Date(),
      messages: [],
      context: context || {},
      metadata: {
        totalMessages: 0,
        userMessages: 0,
        assistantMessages: 0,
        duration: 0,
        status: 'active'
      }
    };

    this.activeSessions.set(session.id, session);
    this.persistSession(session);

    console.log(`[Session] Created new session: ${session.id}`);
    return session;
  }

  /**
   * Get an active session
   */
  getSession(sessionId: string): ConversationSession | null {
    let session = this.activeSessions.get(sessionId);

    if (!session) {
      session = this.loadSession(sessionId);
      if (session) {
        this.activeSessions.set(sessionId, session);
      }
    }

    return session || null;
  }

  /**
   * Add a message to the session
   */
  addMessage(
    sessionId: string,
    type: 'user' | 'assistant' | 'system',
    content: string,
    metadata?: ConversationMessage['metadata'],
    audio?: string
  ): ConversationMessage | null {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      console.error(`[Session] Session not found: ${sessionId}`);
      return null;
    }

    const message: ConversationMessage = {
      id: this.generateMessageId(),
      type,
      content,
      timestamp: new Date(),
      audio,
      metadata
    };

    session.messages.push(message);
    session.metadata.totalMessages++;
    if (type === 'user') {
      session.metadata.userMessages++;
    } else if (type === 'assistant') {
      session.metadata.assistantMessages++;
    }

    session.metadata.duration = Date.now() - session.startTime.getTime();
    this.persistSession(session);

    return message;
  }

  /**
   * Update session context
   */
  updateContext(sessionId: string, context: Partial<ConversationContext>): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return false;
    }

    session.context = { ...session.context, ...context };
    this.persistSession(session);
    return true;
  }

  /**
   * Get conversation history
   */
  getConversationHistory(sessionId: string, limit?: number): ConversationMessage[] {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return [];
    }

    const messages = session.messages.filter(m => m.type === 'user' || m.type === 'assistant');
    return limit ? messages.slice(-limit) : messages;
  }

  /**
   * End a session
   */
  endSession(sessionId: string): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return false;
    }

    session.endTime = new Date();
    session.metadata.status = 'ended';
    session.metadata.duration = session.endTime.getTime() - session.startTime.getTime();

    this.persistSession(session);
    console.log(`[Session] Ended session ${sessionId}, duration: ${session.metadata.duration}ms`);
    return true;
  }

  /**
   * Export session data
   */
  exportSession(sessionId: string): string | null {
    const session = this.activeSessions.get(sessionId) || this.loadSession(sessionId);
    if (!session) {
      return null;
    }
    return JSON.stringify(session, null, 2);
  }

  /**
   * Get recent sessions
   */
  getRecentSessions(limit: number = 10): ConversationSession[] {
    const activeSessions = Array.from(this.activeSessions.values());
    const storedSessions = this.loadAllSessions();

    const allSessionsMap = new Map<string, ConversationSession>();
    [...storedSessions, ...activeSessions].forEach(s => {
      allSessionsMap.set(s.id, s);
    });

    return Array.from(allSessionsMap.values())
      .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime())
      .slice(0, limit);
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private persistSession(session: ConversationSession): void {
    try {
      const allSessions = this.loadAllSessions();
      const existingIndex = allSessions.findIndex(s => s.id === session.id);

      if (existingIndex >= 0) {
        allSessions[existingIndex] = session;
      } else {
        allSessions.push(session);
      }

      this.saveAllSessions(allSessions);
    } catch (error) {
      console.error('[Session] Failed to persist session:', error);
    }
  }

  private loadSession(sessionId: string): ConversationSession | null {
    const allSessions = this.loadAllSessions();
    return allSessions.find(s => s.id === sessionId) || null;
  }

  private loadAllSessions(): ConversationSession[] {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) {
        return [];
      }

      const sessions = JSON.parse(stored);
      return sessions.map((s: any) => ({
        ...s,
        startTime: new Date(s.startTime),
        endTime: s.endTime ? new Date(s.endTime) : undefined,
        messages: s.messages.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        }))
      }));
    } catch (error) {
      console.error('[Session] Failed to load sessions:', error);
      return [];
    }
  }

  private saveAllSessions(sessions: ConversationSession[]): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(sessions));
    } catch (error) {
      console.error('[Session] Failed to save sessions:', error);
    }
  }
}

// Export singleton instance
export const conversationSessionService = new ConversationSessionService();
export type { ConversationSessionService };
