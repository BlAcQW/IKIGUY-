/** LOAD API entity types — mirrors the backend Zod schemas and Prisma models. */

export type Role = 'OWNER' | 'ADMIN' | 'MEMBER';
export type Plan = 'FREE' | 'PRO' | 'ENTERPRISE';
export type CallType = 'WEB' | 'INBOUND' | 'OUTBOUND';
export type CallStatus = 'QUEUED' | 'RINGING' | 'IN_PROGRESS' | 'ENDED' | 'FAILED';
export type CampaignStatus = 'DRAFT' | 'RUNNING' | 'PAUSED' | 'COMPLETED';
export type ToolType = 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';

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
}

export interface Assistant {
  id: string;
  organizationId: string;
  name: string;
  model: { provider: string; model: string; temperature?: number; maxTokens?: number; systemPrompt?: string };
  voice: { provider: string; voiceId: string; speed?: number };
  transcriber: { provider: string; model: string; language: string };
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
  status: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface SquadMember {
  assistantId: string;
  transferConditions?: Array<{ type: string; value: string; description?: string }>;
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

export interface Tool {
  id: string;
  organizationId: string;
  type: ToolType;
  name: string;
  description: string | null;
  function: Record<string, unknown> | null;
  serverUrl: string | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface Campaign {
  id: string;
  organizationId: string;
  name: string;
  assistantId: string;
  phoneNumberId: string;
  status: CampaignStatus;
  contacts: Array<{ name: string; number: string; metadata?: Record<string, unknown> }>;
  schedule: Record<string, unknown> | null;
  stats: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
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

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: { total: number; page: number; limit: number };
  error?: { code: string; message: string; statusCode: number };
}
