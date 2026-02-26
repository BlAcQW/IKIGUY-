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
  settings?: object | null;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildOrganization(overrides: OrganizationOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    name: overrides.name ?? 'Test Org',
    slug: overrides.slug ?? 'test-org-abc123',
    plan: overrides.plan ?? 'FREE',
    settings: overrides.settings ?? null,
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

// --- Org Settings factory ---

interface OrgSettingsOverrides {
  providerCredentials?: Record<string, string | undefined>;
  pipelineDefaults?: Record<string, unknown>;
  callBehavior?: Record<string, unknown>;
}

export function buildOrgSettings(overrides: OrgSettingsOverrides = {}) {
  return {
    providerCredentials: {
      openaiApiKey: 'sk-test-1234567890abcdef',
      deepgramApiKey: undefined,
      elevenLabsApiKey: undefined,
      cartesiaApiKey: undefined,
      twilioAccountSid: undefined,
      twilioAuthToken: undefined,
      ...overrides.providerCredentials,
    },
    pipelineDefaults: {
      silenceTimeout: 30,
      responseDelay: 0.5,
      interruptionThreshold: 0.5,
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
      llm: { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
      ...overrides.pipelineDefaults,
    },
    callBehavior: {
      maxCallDuration: 3600,
      sessionIdleTimeout: 120,
      recordingEnabled: false,
      hipaaCompliant: false,
      retrySettings: { maxRetries: 0, retryDelay: 30 },
      ...overrides.callBehavior,
    },
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

// --- Squad factory ---

interface SquadOverrides {
  id?: string;
  organizationId?: string;
  name?: string;
  members?: object[];
  metadata?: object | null;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildSquad(overrides: SquadOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    name: overrides.name ?? 'Test Squad',
    members: overrides.members ?? [
      { assistantId: crypto.randomUUID(), transferConditions: [] },
      { assistantId: crypto.randomUUID(), transferConditions: [] },
    ],
    metadata: overrides.metadata ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

// --- Phone Number factory ---

interface PhoneNumberOverrides {
  id?: string;
  organizationId?: string;
  number?: string;
  twilioSid?: string | null;
  assistantId?: string | null;
  name?: string | null;
  provider?: string;
  sipDomain?: string | null;
  status?: string;
  metadata?: object | null;
  createdAt?: Date;
}

export function buildPhoneNumber(overrides: PhoneNumberOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    number: overrides.number ?? '+15551234567',
    twilioSid: overrides.twilioSid ?? null,
    assistantId: overrides.assistantId ?? null,
    name: overrides.name ?? 'Test Number',
    provider: overrides.provider ?? 'TWILIO',
    sipDomain: overrides.sipDomain ?? null,
    status: overrides.status ?? 'ACTIVE',
    metadata: overrides.metadata ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
  };
}

// --- Campaign factory ---

interface CampaignOverrides {
  id?: string;
  organizationId?: string;
  name?: string;
  assistantId?: string;
  phoneNumberId?: string;
  status?: string;
  contacts?: object[];
  schedule?: object | null;
  stats?: object | null;
  createdAt?: Date;
  updatedAt?: Date;
}

export function buildCampaign(overrides: CampaignOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    name: overrides.name ?? 'Test Campaign',
    assistantId: overrides.assistantId ?? crypto.randomUUID(),
    phoneNumberId: overrides.phoneNumberId ?? crypto.randomUUID(),
    status: overrides.status ?? 'DRAFT',
    contacts: overrides.contacts ?? [{ name: 'John', number: '+15551234567' }],
    schedule: overrides.schedule ?? null,
    stats: overrides.stats ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
    updatedAt: overrides.updatedAt ?? new Date('2024-01-01'),
  };
}

// --- Webhook factory ---

interface WebhookOverrides {
  id?: string;
  organizationId?: string;
  url?: string;
  events?: string[];
  secret?: string;
  active?: boolean;
  createdAt?: Date;
}

export function buildWebhook(overrides: WebhookOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    url: overrides.url ?? 'https://example.com/webhook',
    events: overrides.events ?? ['call.started', 'call.ended'],
    secret: overrides.secret ?? 'whsec_test_secret_123',
    active: overrides.active ?? true,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
  };
}

// --- Refresh Token factory ---

interface RefreshTokenOverrides {
  id?: string;
  tokenHash?: string;
  userId?: string;
  organizationId?: string;
  expiresAt?: Date;
  revokedAt?: Date | null;
  createdAt?: Date;
}

export function buildRefreshToken(overrides: RefreshTokenOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    tokenHash: overrides.tokenHash ?? '$2b$12$hashedrefreshtoken',
    userId: overrides.userId ?? crypto.randomUUID(),
    organizationId: overrides.organizationId ?? crypto.randomUUID(),
    expiresAt: overrides.expiresAt ?? new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    revokedAt: overrides.revokedAt ?? null,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
  };
}

// --- Webhook Delivery factory ---

interface WebhookDeliveryOverrides {
  id?: string;
  webhookId?: string;
  event?: string;
  status?: string;
  requestBody?: object;
  responseCode?: number | null;
  responseBody?: string | null;
  responseTime?: number | null;
  error?: string | null;
  attemptNumber?: number;
  createdAt?: Date;
}

export function buildWebhookDelivery(overrides: WebhookDeliveryOverrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    webhookId: overrides.webhookId ?? crypto.randomUUID(),
    event: overrides.event ?? 'call.started',
    status: overrides.status ?? 'success',
    requestBody: overrides.requestBody ?? { callId: crypto.randomUUID() },
    responseCode: overrides.responseCode ?? 200,
    responseBody: overrides.responseBody ?? '{"ok": true}',
    responseTime: overrides.responseTime ?? 150,
    error: overrides.error ?? null,
    attemptNumber: overrides.attemptNumber ?? 1,
    createdAt: overrides.createdAt ?? new Date('2024-01-01'),
  };
}
