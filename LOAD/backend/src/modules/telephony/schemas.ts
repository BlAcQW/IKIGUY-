/**
 * Zod schemas for Twilio webhook payloads.
 *
 * Twilio sends POST requests with form-encoded bodies. These schemas
 * validate the relevant fields while using `.passthrough()` to allow
 * additional Twilio-specific fields we don't need to inspect.
 */

import { z } from 'zod';

/**
 * Twilio inbound call webhook (voiceUrl).
 * Sent when a call arrives on a Twilio phone number.
 */
export const inboundWebhookSchema = z.object({
  CallSid: z.string(),
  AccountSid: z.string(),
  From: z.string(),
  To: z.string(),
  CallStatus: z.string(),
}).passthrough();

export type InboundWebhookInput = z.infer<typeof inboundWebhookSchema>;

/**
 * Twilio outbound connect webhook.
 * Sent when an outbound call is answered and Twilio requests TwiML instructions.
 */
export const outboundConnectSchema = z.object({
  CallSid: z.string(),
  AccountSid: z.string(),
  CallStatus: z.string(),
}).passthrough();

export type OutboundConnectInput = z.infer<typeof outboundConnectSchema>;

/**
 * Twilio status callback webhook.
 * Sent for call status transitions (queued, ringing, in-progress, etc.).
 */
export const statusCallbackSchema = z.object({
  CallSid: z.string(),
  CallStatus: z.enum([
    'queued',
    'initiated',
    'ringing',
    'in-progress',
    'completed',
    'busy',
    'no-answer',
    'canceled',
    'failed',
  ]),
  CallDuration: z.coerce.number().optional(),
}).passthrough();

export type StatusCallbackInput = z.infer<typeof statusCallbackSchema>;
