/**
 * WebSocket handler for Twilio's bidirectional Media Streams protocol.
 *
 * Twilio opens a WebSocket after receiving TwiML with <Connect><Stream>.
 * Audio flows as JSON messages with base64-encoded mu-law at 8kHz.
 *
 * This handler:
 * 1. Parses Twilio media stream events (connected, start, media, stop, mark)
 * 2. Decodes mu-law audio, feeds it through VAD, accumulates speech
 * 3. On speechComplete, runs the voice pipeline
 * 4. Encodes TTS output back to mu-law and sends to Twilio
 */

import { WebSocket } from 'ws';
import { prisma } from '../database/client.js';
import { decodeTwilioAudio, encodeTwilioAudio } from './mulaw-codec.js';
import { SimpleVAD } from './vad.js';
import { processPipelineTurn, type PipelineConfig } from '../voice-pipeline/pipeline.js';
import { getSession, endSession, addMessage } from '../voice-pipeline/session.js';
import { endCall, failCall } from '../modules/calls/service.js';
import { buildPipelineFromAssistant } from '../providers/registry.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { resolveTransfer, executeTransfer } from '../voice-pipeline/squad-transfer.js';
import { extractAssistantConfig, loadToolsForPipeline } from '../voice-pipeline/pipeline-helpers.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Internal state tracked per Twilio Media Stream connection. */
export interface TwilioStreamState {
  streamSid: string;
  callId: string;
  sessionId: string;
  assistantId: string;
  organizationId: string;
  pipeline: PipelineConfig;
  vad: SimpleVAD;
  audioChunks: Buffer[];
  processing: boolean;
}

/** Twilio Media Streams message envelope. */
interface TwilioStreamMessage {
  event: string;
  sequenceNumber?: string;
  streamSid?: string;
  start?: {
    streamSid: string;
    accountSid: string;
    callSid: string;
    customParameters?: Record<string, string>;
    mediaFormat?: {
      encoding: string;
      sampleRate: number;
      channels: number;
    };
  };
  media?: {
    track: string;
    chunk: string;
    timestamp: string;
    payload: string; // base64-encoded mu-law audio
  };
  stop?: {
    accountSid: string;
    callSid: string;
  };
  mark?: {
    name: string;
  };
}

// ---------------------------------------------------------------------------
// Connection state
// ---------------------------------------------------------------------------

const activeStreams = new Map<WebSocket, TwilioStreamState>();

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

/**
 * Handle a Twilio Media Streams WebSocket connection.
 * Called from the telephony route handler.
 */
export function handleTwilioMediaStream(socket: WebSocket): void {
  socket.on('message', async (data) => {
    let msg: TwilioStreamMessage;
    try {
      msg = JSON.parse(data.toString());
    } catch {
      console.warn('[twilio-stream] Failed to parse WebSocket message');
      return;
    }

    try {
      switch (msg.event) {
        case 'connected':
          onConnected(socket, msg);
          break;
        case 'start':
          await onStart(socket, msg);
          break;
        case 'media':
          await onMedia(socket, msg);
          break;
        case 'stop':
          await onStop(socket);
          break;
        case 'mark':
          onMark(socket, msg);
          break;
        default:
          // Ignore unknown events (Twilio may add new ones)
          break;
      }
    } catch (err) {
      console.error(`[twilio-stream] Error handling ${msg.event} event:`, err);
    }
  });

  socket.on('close', async () => {
    await onStop(socket);
  });

  socket.on('error', async (err) => {
    console.error('[twilio-stream] WebSocket error:', err);
    const state = activeStreams.get(socket);
    if (state) {
      await failCall(state.callId, 'websocket_error').catch(() => {});
      await endSession(state.sessionId).catch(() => {});
      activeStreams.delete(socket);
    }
  });
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------

function onConnected(_socket: WebSocket, msg: TwilioStreamMessage): void {
  console.log('[twilio-stream] Twilio Media Stream connected', msg.streamSid ?? '');
}

async function onStart(socket: WebSocket, msg: TwilioStreamMessage): Promise<void> {
  if (activeStreams.has(socket)) {
    console.warn('[twilio-stream] Duplicate start event, ignoring');
    return;
  }

  const params = msg.start?.customParameters;
  if (!params?.callId || !params?.sessionId || !params?.assistantId || !params?.organizationId) {
    console.error('[twilio-stream] Missing required custom parameters in start event');
    socket.close(1008, 'Missing required parameters');
    return;
  }

  const { callId, sessionId, assistantId, organizationId } = params;
  const streamSid = msg.start?.streamSid ?? '';

  // Load assistant and build pipeline
  const assistant = await prisma.assistant.findFirst({
    where: { id: assistantId, organizationId },
  });

  if (!assistant) {
    console.error(`[twilio-stream] Assistant ${assistantId} not found`);
    socket.close(1008, 'Assistant not found');
    return;
  }

  let pipeline: PipelineConfig;
  try {
    pipeline = buildPipelineFromAssistant(assistant);
  } catch (err) {
    console.error('[twilio-stream] Failed to build pipeline:', err);
    socket.close(1011, 'Pipeline initialization failed');
    return;
  }

  const vad = new SimpleVAD({
    sampleRate: 16000, // After upsampling from 8kHz
  });

  const state: TwilioStreamState = {
    streamSid,
    callId,
    sessionId,
    assistantId,
    organizationId,
    pipeline,
    vad,
    audioChunks: [],
    processing: false,
  };

  activeStreams.set(socket, state);

  console.log(
    `[twilio-stream] Stream started: streamSid=${streamSid} ` +
      `callId=${callId} sessionId=${sessionId} assistant=${assistantId}`,
  );

  // Send first message if configured
  if (assistant.firstMessage) {
    try {
      await addMessage(sessionId, { role: 'assistant', content: assistant.firstMessage });

      const voiceConfig = assistant.voice as { voiceId?: string; speed?: number };
      const ttsAudio = await pipeline.tts.synthesize(assistant.firstMessage, {
        voiceId: voiceConfig.voiceId,
        speed: voiceConfig.speed,
      });

      const mulawAudio = encodeTwilioAudio(ttsAudio);
      sendClearAndAudio(socket, streamSid, mulawAudio);

      console.log(
        `[twilio-stream] First message sent (${mulawAudio.length} bytes mulaw) ` +
          `for session ${sessionId}`,
      );
    } catch (err) {
      console.error('[twilio-stream] Failed to synthesize first message:', err);
    }
  }
}

async function onMedia(socket: WebSocket, msg: TwilioStreamMessage): Promise<void> {
  const state = activeStreams.get(socket);
  if (!state) return;

  // Skip if we're already processing a pipeline turn
  if (state.processing) return;

  if (!msg.media?.payload) return;

  // Decode base64 mu-law -> PCM 16kHz
  const mulawBuffer = Buffer.from(msg.media.payload, 'base64');
  const pcmChunk = decodeTwilioAudio(mulawBuffer);

  // Feed through VAD
  const { isSpeech, speechComplete } = state.vad.processChunk(pcmChunk);

  if (isSpeech || speechComplete) {
    state.audioChunks = [...state.audioChunks, pcmChunk];
  }

  if (speechComplete) {
    await runPipelineTurn(socket, state);
  }
}

async function onStop(socket: WebSocket): Promise<void> {
  const state = activeStreams.get(socket);
  if (!state) return;

  activeStreams.delete(socket);

  // Extract transcript from session
  const session = await getSession(state.sessionId);
  const transcript = session?.conversationHistory
    .filter((m) => m.role !== 'system')
    .map((m) => ({ role: m.role, content: m.content })) ?? [];

  await endSession(state.sessionId);

  try {
    await endCall(state.callId, transcript, 'hangup');
  } catch (err) {
    console.error(`[twilio-stream] Failed to end call ${state.callId}:`, err);
  }

  fireWebhookEvent(state.organizationId, 'call.ended', {
    callId: state.callId,
    assistantId: state.assistantId,
    duration: session?.startedAt
      ? Math.round((Date.now() - session.startedAt.getTime()) / 1000)
      : 0,
    transcript,
    endReason: 'hangup',
  }).catch((err) => {
    console.warn('[twilio-stream] Failed to fire call.ended webhook:', err);
  });

  console.log(
    `[twilio-stream] Stream stopped: callId=${state.callId} sessionId=${state.sessionId}`,
  );
}

function onMark(_socket: WebSocket, msg: TwilioStreamMessage): void {
  // Marks are used to track when audio playback completes on Twilio's side
  console.log(`[twilio-stream] Mark received: ${msg.mark?.name ?? 'unknown'}`);
}

// ---------------------------------------------------------------------------
// Pipeline execution
// ---------------------------------------------------------------------------

async function runPipelineTurn(
  socket: WebSocket,
  state: TwilioStreamState,
): Promise<void> {
  state.processing = true;

  try {
    const audioChunks = state.audioChunks;
    state.audioChunks = [];
    state.vad.reset();

    if (audioChunks.length === 0) {
      return;
    }

    const combinedAudio = Buffer.concat(audioChunks);

    // Load current assistant for config
    const assistant = await prisma.assistant.findUnique({
      where: { id: state.assistantId },
    });
    if (!assistant) {
      console.error(`[twilio-stream] Assistant ${state.assistantId} not found during pipeline turn`);
      return;
    }

    const { modelConfig, voiceConfig, transcriberConfig } = extractAssistantConfig(assistant);
    const tools = await loadToolsForPipeline(modelConfig.toolIds, state.organizationId);

    const result = await processPipelineTurn(
      state.sessionId,
      combinedAudio,
      state.pipeline,
      {
        sttModel: transcriberConfig.model,
        sttLanguage: transcriberConfig.language,
        llmModel: modelConfig.model,
        llmTemperature: modelConfig.temperature,
        llmMaxTokens: modelConfig.maxTokens,
        ttsVoiceId: voiceConfig.voiceId,
        ttsSpeed: voiceConfig.speed,
        tools,
        format: 'wav', // PCM raw audio from mulaw decode
      },
    );

    // Encode TTS output for Twilio
    const mulawAudio = encodeTwilioAudio(result.audioBuffer);
    sendClearAndAudio(socket, state.streamSid, mulawAudio);

    console.log(
      `[twilio-stream] Pipeline turn complete for session ${state.sessionId}: ` +
        `user="${result.userText}" assistant="${result.assistantText}" ` +
        `audioOut=${mulawAudio.length} bytes`,
    );

    // Handle transfer
    if (result.transferRequest) {
      await handleTransfer(socket, state, result.transferRequest.targetAssistantId);
      return;
    }

    // Handle end-call tool
    if (result.endCallRequested) {
      console.log(`[twilio-stream] End-call tool triggered in session ${state.sessionId}`);
      socket.close(1000, 'Call ended by assistant');
      return;
    }

    // Check for end-call phrases (legacy)
    if (assistant.endCallPhrases && assistant.endCallPhrases.length > 0) {
      const lowerResponse = result.assistantText.toLowerCase();
      const shouldEnd = assistant.endCallPhrases.some((phrase) =>
        lowerResponse.includes(phrase.toLowerCase()),
      );
      if (shouldEnd) {
        console.log(`[twilio-stream] End-call phrase detected in session ${state.sessionId}`);
        socket.close(1000, 'Call ended by phrase match');
      }
    }
  } catch (err) {
    console.error(`[twilio-stream] Pipeline turn failed for session ${state.sessionId}:`, err);

    const reason = err instanceof Error ? err.message : 'Pipeline processing failed';
    await failCall(state.callId, reason).catch(() => {});
    fireWebhookEvent(state.organizationId, 'call.failed', {
      callId: state.callId,
      assistantId: state.assistantId,
      error: reason,
    }).catch(() => {});
  } finally {
    state.processing = false;
  }
}

// ---------------------------------------------------------------------------
// Transfer handling
// ---------------------------------------------------------------------------

async function handleTransfer(
  socket: WebSocket,
  state: TwilioStreamState,
  targetAssistantId: string,
): Promise<void> {
  const validated = await resolveTransfer(
    state.organizationId,
    state.assistantId,
    targetAssistantId,
  );

  if (!validated) {
    console.warn('[twilio-stream] Transfer failed: assistants not in same squad');
    return;
  }

  const targetAssistant = await prisma.assistant.findFirst({
    where: { id: targetAssistantId, organizationId: state.organizationId },
  });
  if (!targetAssistant) {
    console.warn(`[twilio-stream] Transfer target assistant ${targetAssistantId} not found`);
    return;
  }

  await executeTransfer(state.sessionId, targetAssistant);
  const newPipeline = buildPipelineFromAssistant(targetAssistant);

  // Update state
  state.assistantId = targetAssistantId;
  state.pipeline = newPipeline;

  console.log(`[twilio-stream] Transferred session ${state.sessionId} to assistant ${targetAssistantId}`);

  // Synthesize first message of new assistant
  if (targetAssistant.firstMessage) {
    try {
      const voiceConfig = targetAssistant.voice as { voiceId?: string; speed?: number };
      await addMessage(state.sessionId, { role: 'assistant', content: targetAssistant.firstMessage });

      const ttsAudio = await newPipeline.tts.synthesize(targetAssistant.firstMessage, {
        voiceId: voiceConfig.voiceId,
        speed: voiceConfig.speed,
      });

      const mulawAudio = encodeTwilioAudio(ttsAudio);
      sendClearAndAudio(socket, state.streamSid, mulawAudio);
    } catch (err) {
      console.error('[twilio-stream] Failed to synthesize transfer first message:', err);
    }
  }
}

// ---------------------------------------------------------------------------
// Twilio Media Streams send helpers
// ---------------------------------------------------------------------------

/** Maximum payload size per media message (Twilio recommends ≤ 32KB). */
const MAX_MEDIA_CHUNK_BYTES = 16000; // ~2 seconds of mu-law at 8kHz

/**
 * Clear any queued audio on Twilio's side, then send new audio.
 * The "clear" event tells Twilio to stop playing any previously sent audio,
 * which prevents overlapping with the new response.
 */
function sendClearAndAudio(
  socket: WebSocket,
  streamSid: string,
  mulawAudio: Buffer,
): void {
  if (socket.readyState !== WebSocket.OPEN) return;

  // Send clear event to interrupt any queued audio
  socket.send(JSON.stringify({
    event: 'clear',
    streamSid,
  }));

  // Send audio in chunks
  for (let offset = 0; offset < mulawAudio.length; offset += MAX_MEDIA_CHUNK_BYTES) {
    const chunk = mulawAudio.subarray(offset, offset + MAX_MEDIA_CHUNK_BYTES);
    socket.send(JSON.stringify({
      event: 'media',
      streamSid,
      media: {
        payload: chunk.toString('base64'),
      },
    }));
  }

  // Send mark to track when playback completes
  socket.send(JSON.stringify({
    event: 'mark',
    streamSid,
    mark: { name: `response-${Date.now()}` },
  }));
}

/**
 * Expose activeStreams for testing purposes.
 * @internal
 */
export { activeStreams };
