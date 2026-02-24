import crypto from 'node:crypto';

interface UserOverrides {
  id?: string;
  email?: string;
  passwordHash?: string;
  name?: string;
  role?: string;
  organizationId?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildUser(overrides: UserOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    email: overrides.email ?? 'test@example.com',
    passwordHash: overrides.passwordHash ?? '$2b$12$hashedpassword',
    name: overrides.name ?? 'Test User',
    role: overrides.role ?? 'OWNER',
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

interface OrganizationOverrides {
  id?: string;
  name?: string;
  slug?: string;
  plan?: string;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildOrganization(overrides: OrganizationOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    name: overrides.name ?? 'Test Org',
    slug: overrides.slug ?? 'test-org-abc123',
    plan: overrides.plan ?? 'FREE',
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

interface AssistantOverrides {
  id?: string;
  organizationId?: string;
  name?: string;
  model?: object;
  voice?: object;
  transcriber?: object;
  firstMessage?: string | null;
  endCallMessage?: string | null;
  endCallPhrases?: string[];
  metadata?: object | null;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildAssistant(overrides: AssistantOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    name: overrides.name ?? 'Test Assistant',
    model: overrides.model ?? { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
    voice: overrides.voice ?? { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
    transcriber: overrides.transcriber ?? { provider: 'openai', model: 'whisper-1', language: 'en' },
    firstMessage: overrides.firstMessage ?? 'Hello, how can I help?',
    endCallMessage: overrides.endCallMessage ?? 'Goodbye!',
    endCallPhrases: overrides.endCallPhrases ?? [],
    metadata: overrides.metadata ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

interface ToolOverrides {
  id?: string;
  organizationId?: string;
  type?: string;
  name?: string;
  description?: string | null;
  function?: object | null;
  serverUrl?: string | null;
  serverSecret?: string | null;
  metadata?: object | null;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildTool(overrides: ToolOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    type: overrides.type ?? 'FUNCTION',
    name: overrides.name ?? 'Test Tool',
    description: overrides.description ?? 'A test tool',
    function: overrides.function ?? { name: 'test_function', description: 'Test', parameters: { type: 'object', properties: {} } },
    serverUrl: overrides.serverUrl ?? 'https://example.com/webhook',
    serverSecret: overrides.serverSecret ?? null,
    metadata: overrides.metadata ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

interface ApiKeyOverrides {
  id?: string;
  keyHash?: string;
  prefix?: string;
  name?: string;
  organizationId?: string;
  createdById?: string;
  lastUsedAt?: Date | null;
  expiresAt?: Date | null;
  createdAt?: Date;
}

export function buildApiKey(overrides: ApiKeyOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    keyHash: overrides.keyHash ?? '$2b$12$hashedapikey',
    prefix: overrides.prefix ?? 'load_abcd1234',
    name: overrides.name ?? 'Test API Key',
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    createdById: overrides.createdById ?? crypto.randomUUID(),
    lastUsedAt: overrides.lastUsedAt ?? null,
    expiresAt: overrides.expiresAt ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
  };
}
