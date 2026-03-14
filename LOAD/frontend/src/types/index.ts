// Enums matching Prisma schema

export type CallStatus = 'QUEUED' | 'RINGING' | 'IN_PROGRESS' | 'ENDED' | 'FAILED';
export type CampaignStatus = 'DRAFT' | 'RUNNING' | 'PAUSED' | 'COMPLETED';
export type ToolType = 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
export type Role = 'OWNER' | 'ADMIN' | 'MEMBER';
export type Plan = 'FREE' | 'PRO' | 'ENTERPRISE';
export type CallType = 'WEB' | 'INBOUND' | 'OUTBOUND';

// Entity interfaces

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: Plan;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  organizationId: string;
  createdAt: string;
  updatedAt: string;
}

export interface ApiKey {
  id: string;
  prefix: string;
  name: string;
  organizationId: string;
  createdById: string;
  lastUsedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
}

export interface AssistantModel {
  provider: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

export interface AssistantVoice {
  provider: string;
  voiceId: string;
  speed?: number;
}

export interface AssistantTranscriber {
  provider: string;
  model: string;
  language: string;
}

export interface Assistant {
  id: string;
  organizationId: string;
  name: string;
  model: AssistantModel;
  voice: AssistantVoice;
  transcriber: AssistantTranscriber;
  firstMessage: string | null;
  endCallMessage: string | null;
  endCallPhrases: string[];
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface Call {
  id: string;
  organizationId: string;
  assistantId: string;
  type: CallType;
  status: CallStatus;
  phoneNumberId: string | null;
  customerNumber: string | null;
  externalCallId: string | null;
  startedAt: string | null;
  endedAt: string | null;
  duration: number | null;
  endReason: string | null;
  transcript: unknown;
  recordingUrl: string | null;
  cost: string | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface PhoneNumber {
  id: string;
  organizationId: string;
  number: string;
  twilioSid: string | null;
  assistantId: string | null;
  name: string | null;
  provider: string;
  sipDomain: string | null;
  status: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  assistant?: Assistant;
}

export interface ToolFunction {
  name: string;
  description?: string;
  parameters: Record<string, unknown>;
}

export interface Tool {
  id: string;
  organizationId: string;
  type: ToolType;
  name: string;
  description: string | null;
  function: ToolFunction | null;
  serverUrl: string | null;
  serverSecret: string | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface TransferCondition {
  type: 'keyword' | 'intent' | 'tool_result' | 'manual';
  value: string;
}

export interface SquadMember {
  assistantId: string;
  transferConditions?: TransferCondition[];
}

export interface Squad {
  id: string;
  organizationId: string;
  name: string;
  members: SquadMember[];
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface CampaignContact {
  name: string;
  number: string;
  metadata?: Record<string, unknown>;
}

export interface CampaignSchedule {
  startTime?: string;
  endTime?: string;
  timezone?: string;
  maxConcurrent?: number;
  delayBetweenCalls?: number;
  maxRetries?: number;
}

export interface CampaignStats {
  total: number;
  completed: number;
  failed: number;
  inProgress: number;
}

export interface Campaign {
  id: string;
  organizationId: string;
  name: string;
  assistantId: string;
  phoneNumberId: string;
  status: CampaignStatus;
  contacts: CampaignContact[];
  schedule: CampaignSchedule | null;
  stats: CampaignStats | null;
  createdAt: string;
  updatedAt: string;
  assistant?: Assistant;
  phoneNumber?: PhoneNumber;
}

export interface Webhook {
  id: string;
  organizationId: string;
  url: string;
  events: string[];
  secret: string;
  active: boolean;
  createdAt: string;
}

// API request types

export interface CreateAssistantRequest {
  name: string;
  model?: Partial<AssistantModel>;
  voice?: Partial<AssistantVoice>;
  transcriber?: Partial<AssistantTranscriber>;
  firstMessage?: string;
  endCallMessage?: string;
  endCallPhrases?: string[];
  metadata?: Record<string, unknown>;
}

export interface UpdateAssistantRequest {
  name?: string;
  model?: Partial<AssistantModel>;
  voice?: Partial<AssistantVoice>;
  transcriber?: Partial<AssistantTranscriber>;
  firstMessage?: string;
  endCallMessage?: string;
  endCallPhrases?: string[];
  metadata?: Record<string, unknown>;
}

export interface CreateToolRequest {
  name: string;
  type?: ToolType;
  description?: string;
  function?: ToolFunction;
  serverUrl?: string;
  serverSecret?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateToolRequest {
  name?: string;
  type?: ToolType;
  description?: string;
  function?: ToolFunction;
  serverUrl?: string;
  serverSecret?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateSquadRequest {
  name: string;
  members: SquadMember[];
  metadata?: Record<string, unknown>;
}

export interface UpdateSquadRequest {
  name?: string;
  members?: SquadMember[];
  metadata?: Record<string, unknown>;
}

export interface CreateCampaignRequest {
  name: string;
  assistantId: string;
  phoneNumberId: string;
  contacts?: CampaignContact[];
  schedule?: CampaignSchedule;
}

export interface UpdateCampaignRequest {
  name?: string;
  assistantId?: string;
  phoneNumberId?: string;
  contacts?: CampaignContact[];
  schedule?: CampaignSchedule;
}

export interface SearchPhoneNumbersRequest {
  country?: string;
  areaCode?: string;
  contains?: string;
  type?: 'local' | 'tollFree';
  limit?: number;
}

export interface PurchasePhoneNumberRequest {
  phoneNumber: string;
  name?: string;
}

export interface CreateSipNumberRequest {
  number: string;
  name?: string;
  provider: 'SIP_TRUNK';
  sipDomain?: string;
}

export interface CreateGoipNumberRequest {
  number: string;
  name?: string;
  provider: 'GOIP';
  trunkName?: string;
  country?: string;
}

export interface UpdatePhoneNumberRequest {
  assistantId?: string | null;
  name?: string;
}

export interface CreateWebhookRequest {
  url: string;
  events: string[];
  active?: boolean;
}

export interface UpdateWebhookRequest {
  url?: string;
  events?: string[];
  active?: boolean;
}

// Webhook Delivery

export interface WebhookDelivery {
  id: string;
  webhookId: string;
  event: string;
  status: 'success' | 'failed' | 'pending';
  requestBody: Record<string, unknown>;
  responseCode: number | null;
  responseBody: string | null;
  responseTime: number | null;
  error: string | null;
  attemptNumber: number;
  createdAt: string;
}

// Tool Templates

export type ToolTemplateCategory =
  | 'scheduling'
  | 'sales'
  | 'finance'
  | 'retention'
  | 'survey'
  | 'marketing'
  | 'insurance'
  | 'healthcare';

export interface ToolTemplate {
  name: string;
  description: string;
  category: ToolTemplateCategory;
  type: ToolType;
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

export interface ToolTemplatesResponse {
  categories: Record<ToolTemplateCategory, string>;
  templates: Record<ToolTemplateCategory, ToolTemplate[]>;
}

// Organization Settings

export interface ProviderCredentials {
  openaiApiKey?: string;
  deepgramApiKey?: string;
  elevenLabsApiKey?: string;
  cartesiaApiKey?: string;
  googleAiApiKey?: string;
  anthropicApiKey?: string;
  twilioAccountSid?: string;
  twilioAuthToken?: string;
}

export interface PipelineDefaults {
  silenceTimeout: number;
  responseDelay: number;
  interruptionThreshold: number;
  transcriber: { provider: string; model: string; language: string };
  voice: { provider: string; voiceId: string; speed: number };
  llm: { provider: string; model: string; temperature: number; maxTokens: number };
}

export interface CallBehavior {
  maxCallDuration: number;
  sessionIdleTimeout: number;
  recordingEnabled: boolean;
  hipaaCompliant: boolean;
  retrySettings: { maxRetries: number; retryDelay: number };
}

export interface OrgSettings {
  providerCredentials: ProviderCredentials;
  pipelineDefaults: PipelineDefaults;
  callBehavior: CallBehavior;
}

// Analytics

export interface TimeSeriesPoint {
  period: string;
  total: number;
  completed: number;
  failed: number;
  avgDuration: number;
}

export interface AnalyticsSummary {
  totalCalls: number;
  completedCalls: number;
  failedCalls: number;
  successRate: number;
  avgDuration: number;
  totalMinutes: number;
  byType: { type: string; count: number }[];
  byAssistant: { assistantId: string; assistantName: string; count: number }[];
}
