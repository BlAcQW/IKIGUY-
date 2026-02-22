import IORedis from 'ioredis';
import type { CallSession } from './session.js';

const SESSION_TTL = 7200; // 2 hours

export interface SessionStore {
  get(sessionId: string): Promise<CallSession | undefined>;
  set(session: CallSession): Promise<void>;
  delete(sessionId: string): Promise<void>;
}

export class InMemorySessionStore implements SessionStore {
  private readonly sessions = new Map<string, CallSession>();

  async get(sessionId: string): Promise<CallSession | undefined> {
    return this.sessions.get(sessionId);
  }

  async set(session: CallSession): Promise<void> {
    this.sessions.set(session.id, session);
  }

  async delete(sessionId: string): Promise<void> {
    this.sessions.delete(sessionId);
  }
}

export class RedisSessionStore implements SessionStore {
  private readonly client: IORedis;

  constructor(redisUrl: string) {
    this.client = new IORedis(redisUrl, { maxRetriesPerRequest: null });
  }

  private key(sessionId: string): string {
    return `session:${sessionId}`;
  }

  async get(sessionId: string): Promise<CallSession | undefined> {
    const raw = await this.client.get(this.key(sessionId));
    if (!raw) return undefined;
    const parsed = JSON.parse(raw);
    return {
      ...parsed,
      startedAt: new Date(parsed.startedAt),
    };
  }

  async set(session: CallSession): Promise<void> {
    await this.client.set(
      this.key(session.id),
      JSON.stringify(session),
      'EX',
      SESSION_TTL,
    );
  }

  async delete(sessionId: string): Promise<void> {
    await this.client.del(this.key(sessionId));
  }

  async close(): Promise<void> {
    await this.client.quit();
  }
}

export function createSessionStore(redisUrl?: string): SessionStore {
  if (redisUrl) {
    try {
      return new RedisSessionStore(redisUrl);
    } catch {
      console.warn('[session-store] Failed to connect to Redis, falling back to in-memory store');
      return new InMemorySessionStore();
    }
  }
  return new InMemorySessionStore();
}
