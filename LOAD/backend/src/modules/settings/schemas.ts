import { z } from 'zod';

// --- Provider Credentials ---
// Third-party API keys that the organization provides so the voice pipeline
// can authenticate with STT / LLM / TTS / telephony services without relying
// on server-level environment variables.

export const providerCredentialsSchema = z.object({
  openaiApiKey: z.string().optional(),
  googleAiApiKey: z.string().optional(),
  anthropicApiKey: z.string().optional(),
  deepgramApiKey: z.string().optional(),
  elevenLabsApiKey: z.string().optional(),
  cartesiaApiKey: z.string().optional(),
  twilioAccountSid: z.string().optional(),
  twilioAuthToken: z.string().optional(),
});

export type ProviderCredentials = z.infer<typeof providerCredentialsSchema>;

// --- Pipeline Defaults ---
// Default voice-pipeline settings inherited by every assistant in the org
// unless the assistant overrides them.

export const pipelineDefaultsSchema = z.object({
  // How many seconds of silence before the pipeline considers the turn over
  silenceTimeout: z.number().min(5).max(120).default(30),
  // Artificial delay (seconds) before the assistant starts responding
  responseDelay: z.number().min(0).max(2).default(0.5),
  // Confidence threshold (0-1) for detecting user interruptions
  interruptionThreshold: z.number().min(0).max(1).default(0.5),

  // Default transcriber (STT) configuration
  transcriber: z.object({
    provider: z.string().default('openai'),
    model: z.string().default('whisper-1'),
    language: z.string().default('en'),
  }).default({}),

  // Default voice (TTS) configuration
  voice: z.object({
    provider: z.string().default('openai'),
    voiceId: z.string().default('alloy'),
    speed: z.number().min(0.5).max(2).default(1.0),
  }).default({}),

  // Default LLM configuration
  llm: z.object({
    provider: z.string().default('openai'),
    model: z.string().default('gpt-4'),
    temperature: z.number().min(0).max(2).default(0.7),
    maxTokens: z.number().min(1).max(128000).default(1000),
  }).default({}),
});

export type PipelineDefaults = z.infer<typeof pipelineDefaultsSchema>;

// --- Call Behavior ---
// Organization-wide defaults for call lifecycle, recording, and retry logic.

export const callBehaviorSchema = z.object({
  // Maximum allowed call duration in seconds (1 min – 4 hours)
  maxCallDuration: z.number().min(60).max(14400).default(3600),
  // Seconds of inactivity before the session is automatically ended
  sessionIdleTimeout: z.number().min(30).max(600).default(120),
  // Whether calls should be recorded
  recordingEnabled: z.boolean().default(false),
  // Whether HIPAA-compliant mode is enabled (disables logging of PHI)
  hipaaCompliant: z.boolean().default(false),

  // Retry behaviour for failed outbound calls
  retrySettings: z.object({
    maxRetries: z.number().min(0).max(10).default(0),
    retryDelay: z.number().min(1).max(300).default(30),
  }).default({}),
});

export type CallBehavior = z.infer<typeof callBehaviorSchema>;

// --- Top-level Org Settings ---
// Combines all three sections into one JSONB blob stored on Organization.settings.

export const orgSettingsSchema = z.object({
  providerCredentials: providerCredentialsSchema.default({}),
  pipelineDefaults: pipelineDefaultsSchema.default({}),
  callBehavior: callBehaviorSchema.default({}),
});

export type OrgSettings = z.infer<typeof orgSettingsSchema>;

// --- Update schema (partial) ---
// Used for PUT /api/settings — every field is optional so the client can
// send only the sections it wants to change.

export const updateOrgSettingsSchema = z.object({
  providerCredentials: providerCredentialsSchema.partial().optional(),
  pipelineDefaults: pipelineDefaultsSchema.deepPartial().optional(),
  callBehavior: callBehaviorSchema.deepPartial().optional(),
});

export type UpdateOrgSettings = z.infer<typeof updateOrgSettingsSchema>;
