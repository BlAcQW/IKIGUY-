import { z } from 'zod';

const modelConfigSchema = z.object({
  provider: z.string().default('openai'),
  model: z.string().default('gpt-4'),
  temperature: z.number().min(0).max(2).default(0.7),
  maxTokens: z.number().min(1).max(16000).default(1000),
  systemPrompt: z.string().optional(),
});

const voiceConfigSchema = z.object({
  provider: z.string().default('openai'),
  voiceId: z.string().default('alloy'),
  speed: z.number().min(0.25).max(4).default(1.0),
});

const transcriberConfigSchema = z.object({
  provider: z.string().default('openai'),
  model: z.string().default('whisper-1'),
  language: z.string().default('en'),
});

export const createAssistantSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  model: modelConfigSchema.default({}),
  voice: voiceConfigSchema.default({}),
  transcriber: transcriberConfigSchema.default({}),
  firstMessage: z.string().optional(),
  endCallMessage: z.string().optional(),
  endCallPhrases: z.array(z.string()).default([]),
  metadata: z.record(z.unknown()).optional(),
});

export const updateAssistantSchema = createAssistantSchema.partial();

export const listAssistantsSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
});

export type CreateAssistantInput = z.infer<typeof createAssistantSchema>;
export type UpdateAssistantInput = z.infer<typeof updateAssistantSchema>;
export type ListAssistantsInput = z.infer<typeof listAssistantsSchema>;
