/**
 * Conversation Session Management Service
 *
 * Manages conversation sessions for voice agent interactions including:
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
  audio?: string; // Base64 audio data
  metadata?: {
    confidence?: number;
    processingTime?: number;
    partialTranscript?: boolean;
  };
}

export interface ConversationContext {
  language?: string;
  dialect?: string;
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
    duration: number; // milliseconds
    averageResponseTime?: number;
    status: 'active' | 'paused' | 'ended';
  };
}

class ConversationSessionService {
  private activeSessions: Map<string, ConversationSession> = new Map();
  private storageKey = 'conversation_sessions';

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
    // First check active sessions
    let session = this.activeSessions.get(sessionId);

    // If not in memory, try loading from storage
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

    // Update metadata
    session.metadata.totalMessages++;
    if (type === 'user') {
      session.metadata.userMessages++;
    } else if (type === 'assistant') {
      session.metadata.assistantMessages++;
    }

    // Update duration
    session.metadata.duration = Date.now() - session.startTime.getTime();

    this.persistSession(session);

    console.log(`[Session] Added ${type} message to session ${sessionId}`);
    return message;
  }

  /**
   * Update session context
   */
  updateContext(sessionId: string, context: Partial<ConversationContext>): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      console.error(`[Session] Session not found: ${sessionId}`);
      return false;
    }

    session.context = {
      ...session.context,
      ...context
    };

    this.persistSession(session);
    console.log(`[Session] Updated context for session ${sessionId}`);
    return true;
  }

  /**
   * Get conversation history for context
   */
  getConversationHistory(sessionId: string, limit?: number): ConversationMessage[] {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return [];
    }

    const messages = session.messages.filter(
      m => m.type === 'user' || m.type === 'assistant'
    );

    if (limit) {
      return messages.slice(-limit);
    }

    return messages;
  }

  /**
   * Get conversation context for LLM
   */
  getContextForLLM(sessionId: string, messageLimit: number = 10): string {
    const messages = this.getConversationHistory(sessionId, messageLimit);

    return messages
      .map(m => `${m.type === 'user' ? 'User' : 'Assistant'}: ${m.content}`)
      .join('\n');
  }

  /**
   * Pause a session
   */
  pauseSession(sessionId: string): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return false;
    }

    session.metadata.status = 'paused';
    this.persistSession(session);
    console.log(`[Session] Paused session ${sessionId}`);
    return true;
  }

  /**
   * Resume a paused session
   */
  resumeSession(sessionId: string): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return false;
    }

    session.metadata.status = 'active';
    this.persistSession(session);
    console.log(`[Session] Resumed session ${sessionId}`);
    return true;
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
   * Get all sessions for an assistant
   */
  getAssistantSessions(assistantId: string): ConversationSession[] {
    // Combine active sessions and stored sessions
    const activeSessions = Array.from(this.activeSessions.values());
    const storedSessions = this.loadAllSessions();

    // Merge and deduplicate by ID
    const allSessionsMap = new Map<string, ConversationSession>();

    [...storedSessions, ...activeSessions].forEach(s => {
      allSessionsMap.set(s.id, s);
    });

    return Array.from(allSessionsMap.values()).filter(s => s.assistantId === assistantId);
  }

  /**
   * Get recent sessions
   */
  getRecentSessions(limit: number = 10): ConversationSession[] {
    // Combine active sessions and stored sessions
    const activeSessions = Array.from(this.activeSessions.values());
    const storedSessions = this.loadAllSessions();

    // Merge and deduplicate by ID
    const allSessionsMap = new Map<string, ConversationSession>();

    [...storedSessions, ...activeSessions].forEach(s => {
      allSessionsMap.set(s.id, s);
    });

    return Array.from(allSessionsMap.values())
      .sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime())
      .slice(0, limit);
  }

  /**
   * Clear old sessions
   */
  clearOldSessions(daysOld: number = 7): number {
    const allSessions = this.loadAllSessions();
    const cutoffDate = new Date(Date.now() - daysOld * 24 * 60 * 60 * 1000);

    const sessionsToKeep = allSessions.filter(s => new Date(s.startTime) > cutoffDate);
    const removed = allSessions.length - sessionsToKeep.length;

    this.saveAllSessions(sessionsToKeep);
    console.log(`[Session] Cleared ${removed} old sessions`);
    return removed;
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
   * Calculate average response time
   */
  calculateAverageResponseTime(sessionId: string): number | null {
    const session = this.activeSessions.get(sessionId);
    if (!session || session.messages.length < 2) {
      return null;
    }

    const responseTimes: number[] = [];
    let lastUserMessage: ConversationMessage | null = null;

    for (const message of session.messages) {
      if (message.type === 'user') {
        lastUserMessage = message;
      } else if (message.type === 'assistant' && lastUserMessage) {
        const responseTime = message.timestamp.getTime() - lastUserMessage.timestamp.getTime();
        responseTimes.push(responseTime);
        lastUserMessage = null;
      }
    }

    if (responseTimes.length === 0) {
      return null;
    }

    const avgTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    session.metadata.averageResponseTime = avgTime;

    return avgTime;
  }

  // ============================================================
  // Private Methods
  // ============================================================

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
      // Convert date strings back to Date objects
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

// Export types
export type { ConversationSessionService };
