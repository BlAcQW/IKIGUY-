import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string(),
  REDIS_URL: z.string().default('redis://localhost:6379'),
  JWT_SECRET: z.string().min(16),
  JWT_EXPIRES_IN: z.string().default('15m'),
  JWT_REFRESH_EXPIRES_IN: z.string().default('7d'),
  OPENAI_API_KEY: z.string().optional(),
  TWILIO_ACCOUNT_SID: z.string().optional(),
  TWILIO_AUTH_TOKEN: z.string().optional(),
  TWILIO_PHONE_NUMBER: z.string().optional(),
  ASTERISK_ARI_URL: z.string().optional(),
  ASTERISK_ARI_USERNAME: z.string().optional(),
  ASTERISK_ARI_PASSWORD: z.string().optional(),
  ASTERISK_ARI_APP: z.string().default('load'),
  DEEPGRAM_API_KEY: z.string().optional(),
  ELEVENLABS_API_KEY: z.string().optional(),
  CARTESIA_API_KEY: z.string().optional(),
  FRONTEND_URL: z.string().default('http://localhost:5173'),
  API_URL: z.string().default('http://localhost:3000'),
  WEBHOOK_SECRET: z.string().min(16),
  STUN_SERVERS: z.string().default('stun:stun.l.google.com:19302'),
  TURN_URL: z.string().optional(),
  TURN_USERNAME: z.string().optional(),
  TURN_CREDENTIAL: z.string().optional(),
});

export type Env = z.infer<typeof envSchema>;

function loadConfig(): Env {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    const formatted = result.error.format();
    const missing = Object.entries(formatted)
      .filter(([key, val]) => key !== '_errors' && val && typeof val === 'object' && '_errors' in val && (val as { _errors: string[] })._errors.length > 0)
      .map(([key]) => key);
    throw new Error(`Missing or invalid environment variables: ${missing.join(', ')}`);
  }
  return result.data;
}

export const config = loadConfig();
