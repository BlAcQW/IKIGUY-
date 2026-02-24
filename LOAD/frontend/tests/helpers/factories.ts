import type {
  User,
  Organization,
  Assistant,
  ApiKey,
  Call,
  Tool,
  Squad,
  Campaign,
  Webhook,
  WebhookDelivery,
  PhoneNumber,
  AnalyticsSummary,
  TimeSeriesPoint,
} from '../../src/types';

let counter = 0;
function uid(): string {
  counter++;
  return `00000000-0000-0000-0000-${String(counter).padStart(12, '0')}`;
}

const now = new Date().toISOString();

export function buildUser(overrides: Partial<User> = {}): User {
  return {
    id: uid(),
    email: 'test@example.com',
    name: 'Test User',
    role: 'OWNER',
    organizationId: uid(),
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildOrganization(overrides: Partial<Organization> = {}): Organization {
  return {
    id: uid(),
    name: 'Test Org',
    slug: 'test-org',
    plan: 'FREE',
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildAssistant(overrides: Partial<Assistant> = {}): Assistant {
  return {
    id: uid(),
    organizationId: uid(),
    name: 'Test Assistant',
    model: { provider: 'openai', model: 'gpt-4o', temperature: 0.7, maxTokens: 1000, systemPrompt: 'You are helpful.' },
    voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
    transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
    firstMessage: 'Hello!',
    endCallMessage: 'Goodbye!',
    endCallPhrases: ['bye', 'goodbye'],
    metadata: null,
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildApiKey(overrides: Partial<ApiKey> = {}): ApiKey {
  return {
    id: uid(),
    prefix: 'load_abc',
    name: 'Test Key',
    organizationId: uid(),
    createdById: uid(),
    lastUsedAt: null,
    expiresAt: null,
    createdAt: now,
    ...overrides,
  };
}

export function buildCall(overrides: Partial<Call> = {}): Call {
  return {
    id: uid(),
    organizationId: uid(),
    assistantId: uid(),
    type: 'WEB',
    status: 'ENDED',
    phoneNumberId: null,
    customerNumber: null,
    externalCallId: null,
    startedAt: now,
    endedAt: now,
    duration: 120,
    endReason: 'completed',
    transcript: null,
    recordingUrl: null,
    cost: '0.05',
    metadata: null,
    createdAt: now,
    ...overrides,
  };
}

export function buildTool(overrides: Partial<Tool> = {}): Tool {
  return {
    id: uid(),
    organizationId: uid(),
    type: 'FUNCTION',
    name: 'check_availability',
    description: 'Check appointment availability',
    function: { name: 'checkAvailability', parameters: { type: 'object', properties: {} } },
    serverUrl: 'https://example.com/webhook',
    serverSecret: null,
    metadata: null,
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildSquad(overrides: Partial<Squad> = {}): Squad {
  return {
    id: uid(),
    organizationId: uid(),
    name: 'Sales Team',
    members: [{ assistantId: uid() }],
    metadata: null,
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildCampaign(overrides: Partial<Campaign> = {}): Campaign {
  return {
    id: uid(),
    organizationId: uid(),
    name: 'Q1 Outreach',
    assistantId: uid(),
    phoneNumberId: uid(),
    status: 'DRAFT',
    contacts: [{ name: 'John Doe', number: '+15551234567' }],
    schedule: null,
    stats: { total: 1, completed: 0, failed: 0, inProgress: 0 },
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}

export function buildWebhook(overrides: Partial<Webhook> = {}): Webhook {
  return {
    id: uid(),
    organizationId: uid(),
    url: 'https://example.com/webhook',
    events: ['call.started', 'call.ended'],
    secret: 'whsec_test123',
    active: true,
    createdAt: now,
    ...overrides,
  };
}

export function buildWebhookDelivery(overrides: Partial<WebhookDelivery> = {}): WebhookDelivery {
  return {
    id: uid(),
    webhookId: uid(),
    event: 'call.started',
    status: 'success',
    requestBody: { callId: 'abc' },
    responseCode: 200,
    responseBody: '{"ok":true}',
    responseTime: 150,
    error: null,
    attemptNumber: 1,
    createdAt: now,
    ...overrides,
  };
}

export function buildPhoneNumber(overrides: Partial<PhoneNumber> = {}): PhoneNumber {
  return {
    id: uid(),
    organizationId: uid(),
    number: '+15551234567',
    twilioSid: 'PN_test123',
    assistantId: null,
    name: 'Main Line',
    provider: 'twilio',
    sipDomain: null,
    status: 'active',
    createdAt: now,
    ...overrides,
  };
}

export function buildAnalyticsSummary(overrides: Partial<AnalyticsSummary> = {}): AnalyticsSummary {
  return {
    totalCalls: 100,
    completedCalls: 85,
    failedCalls: 15,
    successRate: 85,
    avgDuration: 180,
    totalMinutes: 300,
    byType: [
      { type: 'WEB', count: 50 },
      { type: 'INBOUND', count: 30 },
      { type: 'OUTBOUND', count: 20 },
    ],
    byAssistant: [
      { assistantId: 'a1', assistantName: 'Sales Bot', count: 60 },
      { assistantId: 'a2', assistantName: 'Support Bot', count: 40 },
    ],
    ...overrides,
  };
}

export function buildTimeSeriesPoint(overrides: Partial<TimeSeriesPoint> = {}): TimeSeriesPoint {
  return {
    period: now,
    total: 10,
    completed: 8,
    failed: 2,
    avgDuration: 120,
    ...overrides,
  };
}
