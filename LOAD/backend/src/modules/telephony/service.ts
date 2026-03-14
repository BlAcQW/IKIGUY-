/**
 * Business logic for Twilio telephony webhooks and outbound call initiation.
 *
 * Handles inbound call routing (phone number -> assistant -> TwiML with Stream),
 * outbound call connection, status callbacks, and direct Twilio outbound calls.
 */

import { prisma } from '../../database/client.js';
import { config } from '../../config/index.js';
import {
  createCall,
  updateCallStatus,
  endCall,
  failCall,
} from '../calls/service.js';
import { createSession } from '../../voice-pipeline/session.js';
import { makeCall } from '../../telephony/twilio.js';
import { fireWebhookEvent } from '../webhooks/delivery.js';
import type {
  InboundWebhookInput,
  OutboundConnectInput,
  StatusCallbackInput,
} from './schemas.js';

// ---------------------------------------------------------------------------
// TwiML helpers
// ---------------------------------------------------------------------------

/**
 * Convert an HTTP(S) URL to a WebSocket URL.
 * Used to generate the Stream URL for Twilio Media Streams.
 */
function toWebSocketUrl(httpUrl: string): string {
  return httpUrl
    .replace(/^https:\/\//, 'wss://')
    .replace(/^http:\/\//, 'ws://');
}

/**
 * Build TwiML XML containing a <Connect><Stream> directive.
 * Custom parameters are passed to the WebSocket handler via <Parameter> tags.
 */
function buildStreamTwiml(
  params: {
    callId: string;
    sessionId: string;
    assistantId: string;
    organizationId: string;
  },
): string {
  const wsBase = toWebSocketUrl(config.API_URL);
  const streamUrl = `${wsBase}/api/telephony/media-stream`;

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<Response>',
    '  <Connect>',
    `    <Stream url="${streamUrl}">`,
    `      <Parameter name="callId" value="${params.callId}" />`,
    `      <Parameter name="sessionId" value="${params.sessionId}" />`,
    `      <Parameter name="assistantId" value="${params.assistantId}" />`,
    `      <Parameter name="organizationId" value="${params.organizationId}" />`,
    '    </Stream>',
    '  </Connect>',
    '</Response>',
  ].join('\n');
}

/** Build a simple TwiML <Say> response for error cases. */
function buildSayTwiml(message: string): string {
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<Response>',
    `  <Say>${message}</Say>`,
    '</Response>',
  ].join('\n');
}

// ---------------------------------------------------------------------------
// Inbound call handler
// ---------------------------------------------------------------------------

export async function handleInboundCall(
  input: InboundWebhookInput,
): Promise<string> {
  const { CallSid, From, To } = input;

  // Look up the phone number by the "To" number
  const phoneNumber = await prisma.phoneNumber.findFirst({
    where: {
      number: To,
      status: 'ACTIVE',
    },
  });

  if (!phoneNumber) {
    console.warn(`[telephony] No phone number configured for ${To}`);
    return buildSayTwiml('This number is not configured. Goodbye.');
  }

  if (!phoneNumber.assistantId) {
    console.warn(`[telephony] Phone number ${To} has no assistant assigned`);
    return buildSayTwiml('This service is currently unavailable. Goodbye.');
  }

  // Load assistant
  const assistant = await prisma.assistant.findUnique({
    where: { id: phoneNumber.assistantId },
  });

  if (!assistant) {
    console.warn(`[telephony] Assistant ${phoneNumber.assistantId} not found`);
    return buildSayTwiml('This service is currently unavailable. Goodbye.');
  }

  // Create call record
  const call = await createCall({
    organizationId: phoneNumber.organizationId,
    assistantId: assistant.id,
    type: 'INBOUND',
    customerNumber: From,
    phoneNumberId: phoneNumber.id,
  });

  // Store Twilio CallSid as externalCallId
  await prisma.call.update({
    where: { id: call.id },
    data: { externalCallId: CallSid },
  });

  await updateCallStatus(call.id, 'IN_PROGRESS');

  // Create voice pipeline session
  const modelConfig = assistant.model as { systemPrompt?: string };
  const session = await createSession({
    callId: call.id,
    assistantId: assistant.id,
    organizationId: phoneNumber.organizationId,
    systemPrompt: modelConfig.systemPrompt,
  });

  // Fire webhook
  fireWebhookEvent(phoneNumber.organizationId, 'call.started', {
    callId: call.id,
    type: 'INBOUND',
    assistantId: assistant.id,
    customerNumber: From,
    phoneNumberId: phoneNumber.id,
  }).catch((err) => {
    console.warn('[telephony] Failed to fire call.started webhook:', err);
  });

  console.log(
    `[telephony] Inbound call routed: CallSid=${CallSid} callId=${call.id} ` +
      `sessionId=${session.id} assistant=${assistant.id}`,
  );

  return buildStreamTwiml({
    callId: call.id,
    sessionId: session.id,
    assistantId: assistant.id,
    organizationId: phoneNumber.organizationId,
  });
}

// ---------------------------------------------------------------------------
// Outbound connect handler
// ---------------------------------------------------------------------------

export async function handleOutboundConnect(
  input: OutboundConnectInput,
): Promise<string> {
  const { CallSid } = input;

  // Find the call record by Twilio CallSid
  const call = await prisma.call.findFirst({
    where: { externalCallId: CallSid },
  });

  if (!call) {
    console.warn(`[telephony] No call found for outbound CallSid=${CallSid}`);
    return buildSayTwiml('Call setup failed. Goodbye.');
  }

  // Read sessionId from call metadata (stored during makeOutboundCallTwilio)
  const metadata = call.metadata as { sessionId?: string } | null;
  const sessionId = metadata?.sessionId;

  if (!sessionId) {
    console.warn(`[telephony] No sessionId in metadata for call ${call.id}`);
    return buildSayTwiml('Call setup failed. Goodbye.');
  }

  await updateCallStatus(call.id, 'IN_PROGRESS');

  console.log(
    `[telephony] Outbound call connected: CallSid=${CallSid} callId=${call.id} ` +
      `sessionId=${sessionId}`,
  );

  return buildStreamTwiml({
    callId: call.id,
    sessionId,
    assistantId: call.assistantId!,
    organizationId: call.organizationId,
  });
}

// ---------------------------------------------------------------------------
// Status callback handler
// ---------------------------------------------------------------------------

/** Map Twilio call status to LOAD CallStatus. */
function mapTwilioStatus(
  twilioStatus: string,
): 'QUEUED' | 'RINGING' | 'IN_PROGRESS' | 'ENDED' | 'FAILED' | null {
  switch (twilioStatus) {
    case 'queued':
    case 'initiated':
      return 'QUEUED';
    case 'ringing':
      return 'RINGING';
    case 'in-progress':
      return 'IN_PROGRESS';
    case 'completed':
      return 'ENDED';
    case 'busy':
    case 'no-answer':
    case 'canceled':
    case 'failed':
      return 'FAILED';
    default:
      return null;
  }
}

export async function handleStatusCallback(
  input: StatusCallbackInput,
): Promise<void> {
  const { CallSid, CallStatus, CallDuration } = input;

  const call = await prisma.call.findFirst({
    where: { externalCallId: CallSid },
  });

  if (!call) {
    console.warn(`[telephony] Status callback for unknown CallSid=${CallSid}`);
    return;
  }

  const loadStatus = mapTwilioStatus(CallStatus);
  if (!loadStatus) {
    console.warn(`[telephony] Unknown Twilio status: ${CallStatus}`);
    return;
  }

  if (loadStatus === 'ENDED') {
    await endCall(call.id, [], CallStatus);
    if (CallDuration !== undefined) {
      await prisma.call.update({
        where: { id: call.id },
        data: { duration: CallDuration },
      });
    }
  } else if (loadStatus === 'FAILED') {
    await failCall(call.id, CallStatus);
  } else {
    await updateCallStatus(call.id, loadStatus);
  }

  console.log(
    `[telephony] Status update: CallSid=${CallSid} status=${CallStatus} -> ${loadStatus}`,
  );
}

// ---------------------------------------------------------------------------
// Outbound call initiation (Twilio Direct)
// ---------------------------------------------------------------------------

export async function makeOutboundCallTwilio(params: {
  organizationId: string;
  assistantId: string;
  customerNumber: string;
  phoneNumberId: string;
  metadata?: Record<string, unknown>;
}): Promise<{ callId: string; externalCallId: string }> {
  const assistant = await prisma.assistant.findFirst({
    where: { id: params.assistantId, organizationId: params.organizationId },
  });
  if (!assistant) {
    throw Object.assign(new Error('Assistant not found'), { statusCode: 404 });
  }

  const phoneNumber = await prisma.phoneNumber.findFirst({
    where: { id: params.phoneNumberId, organizationId: params.organizationId },
  });
  if (!phoneNumber) {
    throw Object.assign(new Error('Phone number not found'), { statusCode: 404 });
  }

  // Create call record
  const call = await createCall({
    organizationId: params.organizationId,
    assistantId: assistant.id,
    type: 'OUTBOUND',
    customerNumber: params.customerNumber,
    phoneNumberId: phoneNumber.id,
  });

  await updateCallStatus(call.id, 'RINGING');

  // Create session and store ID in call metadata
  const modelConfig = assistant.model as { systemPrompt?: string };
  const session = await createSession({
    callId: call.id,
    assistantId: assistant.id,
    organizationId: params.organizationId,
    systemPrompt: modelConfig.systemPrompt,
  });

  await prisma.call.update({
    where: { id: call.id },
    data: {
      metadata: {
        ...((params.metadata ?? {}) as object),
        sessionId: session.id,
      },
    },
  });

  // Initiate call via Twilio REST API
  const callSid = await makeCall(
    params.customerNumber,
    phoneNumber.number,
    config.API_URL,
  );

  // Store the Twilio CallSid
  await prisma.call.update({
    where: { id: call.id },
    data: { externalCallId: callSid },
  });

  // Fire webhook
  fireWebhookEvent(params.organizationId, 'call.started', {
    callId: call.id,
    type: 'OUTBOUND',
    assistantId: assistant.id,
    customerNumber: params.customerNumber,
    phoneNumberId: phoneNumber.id,
    metadata: params.metadata ?? {},
  }).catch((err) => {
    console.warn('[telephony] Failed to fire call.started webhook:', err);
  });

  console.log(
    `[telephony] Outbound call initiated: callId=${call.id} ` +
      `CallSid=${callSid} to=${params.customerNumber}`,
  );

  return { callId: call.id, externalCallId: callSid };
}
