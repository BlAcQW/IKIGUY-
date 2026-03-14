import { FastifyInstance, FastifyBaseLogger } from 'fastify';
import { WebSocket } from 'ws';
import { prisma } from '../database/client.js';
import { config } from '../config/index.js';
import { processPipelineTurn, type PipelineConfig } from '../voice-pipeline/pipeline.js';
import { createSession, getSession, endSession, addMessage } from '../voice-pipeline/session.js';
import { AudioBuffer } from '../voice-pipeline/audio-stream.js';
import { createCall, updateCallStatus, endCall, failCall } from '../modules/calls/service.js';
import { buildPipelineFromAssistant } from '../providers/registry.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { resolveTransfer, executeTransfer } from '../voice-pipeline/squad-transfer.js';
import { extractAssistantConfig, loadToolsForPipeline } from '../voice-pipeline/pipeline-helpers.js';
import { getSettingsRaw } from '../modules/settings/service.js';

let logger: FastifyBaseLogger;

/** Inline assistant config for editor test calls (no DB lookup needed). */
interface InlineAssistantConfig {
  name?: string;
  model: { provider?: string; model?: string; temperature?: number; maxTokens?: number; systemPrompt?: string; toolIds?: string[] };
  voice: { provider?: string; voiceId?: string; speed?: number };
  transcriber: { provider?: string; model?: string; language?: string };
  firstMessage?: string;
  endCallPhrases?: string[];
}

interface WebCallState {
  sessionId: string;
  callId: string;
  organizationId: string;
  assistantId: string;
  audioBuffer: AudioBuffer;
  pipeline: PipelineConfig;
  processing: boolean;
  /** Present when the call was started with inline config (editor testing). */
  inlineConfig?: InlineAssistantConfig;
}

const activeConnections = new Map<WebSocket, WebCallState>();

function sendJSON(socket: WebSocket, data: object): void {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(data));
  }
}

/** Track authenticated sockets and their org context. */
const authenticatedSockets = new Map<WebSocket, { userId: string; organizationId: string }>();

export async function websocketRoutes(app: FastifyInstance): Promise<void> {
  logger = app.log;
  app.get('/api/calls/web', { websocket: true }, (socket) => {
    // Set a 10-second auth timeout — client must send an auth message first
    const authTimeout = setTimeout(() => {
      if (!authenticatedSockets.has(socket)) {
        sendJSON(socket, {
          type: 'error',
          code: 'UNAUTHORIZED',
          message: 'Authentication timeout — send an auth message within 10 seconds',
        });
        socket.close(4001, 'Unauthorized');
      }
    }, 10_000);

    socket.on('message', async (message) => {
      // Binary audio data
      if (message instanceof Buffer || message instanceof ArrayBuffer) {
        const state = activeConnections.get(socket);
        if (!state) {
          sendJSON(socket, { type: 'error', message: 'Call not started. Send a start message first.' });
          return;
        }
        if (state.processing) {
          return; // Drop audio while processing
        }

        const chunk = message instanceof ArrayBuffer ? Buffer.from(message) : message;
        state.audioBuffer.append(chunk);
        return;
      }

      // JSON control messages
      let parsed: { type: string; token?: string; assistantId?: string; assistantConfig?: InlineAssistantConfig; [key: string]: unknown };
      try {
        parsed = JSON.parse(message.toString());
      } catch {
        sendJSON(socket, { type: 'error', message: 'Invalid JSON message' });
        return;
      }

      // Handle auth message (must be first message)
      if (parsed.type === 'auth') {
        clearTimeout(authTimeout);

        if (authenticatedSockets.has(socket)) {
          sendJSON(socket, { type: 'error', message: 'Already authenticated' });
          return;
        }

        if (!parsed.token) {
          sendJSON(socket, {
            type: 'error',
            code: 'UNAUTHORIZED',
            message: 'Token is required',
          });
          socket.close(4001, 'Unauthorized');
          return;
        }

        try {
          const decoded = app.jwt.verify<{
            userId: string;
            organizationId: string;
            role: string;
          }>(parsed.token);
          authenticatedSockets.set(socket, {
            userId: decoded.userId,
            organizationId: decoded.organizationId,
          });
          sendJSON(socket, { type: 'status', status: 'ready', message: 'WebSocket connected' });
        } catch {
          sendJSON(socket, {
            type: 'error',
            code: 'UNAUTHORIZED',
            message: 'Invalid or expired token',
          });
          socket.close(4001, 'Unauthorized');
        }
        return;
      }

      // All other messages require authentication
      const auth = authenticatedSockets.get(socket);
      if (!auth) {
        sendJSON(socket, {
          type: 'error',
          code: 'UNAUTHORIZED',
          message: 'Authentication required — send an auth message first',
        });
        return;
      }

      if (parsed.type === 'start') {
        await handleStart(socket, parsed, auth.organizationId);
      } else if (parsed.type === 'end_turn') {
        await handleEndTurn(socket);
      } else if (parsed.type === 'stop') {
        await handleStop(socket);
      } else {
        sendJSON(socket, { type: 'error', message: `Unknown message type: ${parsed.type}` });
      }
    });

    socket.on('close', async () => {
      clearTimeout(authTimeout);
      authenticatedSockets.delete(socket);
      await handleStop(socket);
    });

    socket.on('error', async () => {
      clearTimeout(authTimeout);
      authenticatedSockets.delete(socket);
      const state = activeConnections.get(socket);
      if (state) {
        await failCall(state.callId, 'websocket_error').catch(() => {});
        await endSession(state.sessionId);
        activeConnections.delete(socket);
      }
    });
  });
}

async function handleStart(
  socket: WebSocket,
  parsed: { assistantId?: string; assistantConfig?: InlineAssistantConfig; [key: string]: unknown },
  organizationId?: string
): Promise<void> {
  if (activeConnections.has(socket)) {
    sendJSON(socket, { type: 'error', message: 'Call already in progress' });
    return;
  }

  if (!organizationId) {
    sendJSON(socket, { type: 'error', code: 'UNAUTHORIZED', message: 'Authentication required' });
    socket.close(4001, 'Unauthorized');
    return;
  }

  const isInlineTest = !!parsed.assistantConfig;

  if (!parsed.assistantId && !isInlineTest) {
    sendJSON(socket, { type: 'error', message: 'assistantId or assistantConfig is required' });
    return;
  }

  // Resolve assistant config — either from DB or from inline config
  let assistantId: string;
  let modelConfig: { provider?: string; model?: string; temperature?: number; maxTokens?: number; systemPrompt?: string; toolIds?: string[] };
  let voiceConfig: { provider?: string; voiceId?: string; speed?: number };
  let transcriberConfig: { provider?: string; model?: string; language?: string };
  let firstMessage: string | undefined;
  let endCallPhrases: string[] | undefined;
  let inlineConfig: InlineAssistantConfig | undefined;

  if (isInlineTest) {
    // Editor testing mode — use inline config, skip DB lookup
    const cfg = parsed.assistantConfig!;
    assistantId = 'inline-test';
    modelConfig = cfg.model;
    voiceConfig = cfg.voice;
    transcriberConfig = cfg.transcriber;
    firstMessage = cfg.firstMessage;
    endCallPhrases = cfg.endCallPhrases;
    inlineConfig = cfg;
  } else {
    // Production mode — fetch from DB
    const assistant = await prisma.assistant.findFirst({
      where: { id: parsed.assistantId!, organizationId },
    });
    if (!assistant) {
      sendJSON(socket, { type: 'error', message: 'Assistant not found' });
      return;
    }
    assistantId = assistant.id;
    modelConfig = (assistant.model ?? {}) as typeof modelConfig;
    voiceConfig = (assistant.voice ?? {}) as typeof voiceConfig;
    transcriberConfig = (assistant.transcriber ?? {}) as typeof transcriberConfig;
    firstMessage = assistant.firstMessage ?? undefined;
    endCallPhrases = assistant.endCallPhrases ?? undefined;
  }

  // Fetch org-level settings (provider credentials, pipeline defaults)
  // so the pipeline can use org-specific API keys instead of env vars.
  let orgCredentials: { openaiApiKey?: string; deepgramApiKey?: string; elevenLabsApiKey?: string; cartesiaApiKey?: string } | undefined;
  try {
    const orgSettings = await getSettingsRaw(organizationId);
    orgCredentials = orgSettings.providerCredentials;
  } catch {
    // Non-fatal — fall back to server env vars if org settings fail to load
  }

  // Build pipeline — works with both DB assistant and inline config
  // (buildPipelineFromAssistant only reads .model.provider, .voice.provider, .transcriber.provider)
  let pipeline: PipelineConfig;
  try {
    pipeline = buildPipelineFromAssistant(
      { model: modelConfig, voice: voiceConfig, transcriber: transcriberConfig },
      orgCredentials,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to initialize voice providers';
    logger.error({ err, assistantId }, 'Failed to build pipeline for assistant');
    sendJSON(socket, { type: 'error', message });
    return;
  }

  // Create call record in DB
  const call = await createCall({
    organizationId,
    assistantId: isInlineTest ? undefined : assistantId,
    type: 'WEB',
  });
  await updateCallStatus(call.id, 'IN_PROGRESS');

  // Create session (now async)
  const session = await createSession({
    callId: call.id,
    assistantId,
    organizationId,
    systemPrompt: modelConfig.systemPrompt,
  });

  const state: WebCallState = {
    sessionId: session.id,
    callId: call.id,
    organizationId,
    assistantId,
    audioBuffer: new AudioBuffer(),
    pipeline,
    processing: false,
    inlineConfig,
  };
  activeConnections.set(socket, state);

  sendJSON(socket, {
    type: 'call_started',
    callId: call.id,
    sessionId: session.id,
    assistant: { id: assistantId, name: inlineConfig?.name ?? 'Assistant' },
    config: {
      model: modelConfig.model ?? 'gpt-4',
      voice: voiceConfig.voiceId ?? 'alloy',
      language: transcriberConfig.language ?? 'en',
    },
  });

  // Fire webhook (skip for inline test calls — no real assistant)
  if (!isInlineTest) {
    fireWebhookEvent(organizationId, 'call.started', {
      callId: call.id,
      type: 'WEB',
      assistantId,
    }).catch(() => {});
  }

  // Synthesize and send first message if configured
  if (firstMessage) {
    await addMessage(session.id, { role: 'assistant', content: firstMessage });
    try {
      const audio = await pipeline.tts.synthesize(firstMessage, {
        voiceId: voiceConfig.voiceId,
        speed: voiceConfig.speed,
      });
      sendJSON(socket, { type: 'assistant_message', text: firstMessage, hasAudio: true });
      socket.send(audio);
      sendJSON(socket, { type: 'audio_end' });
    } catch {
      sendJSON(socket, { type: 'assistant_message', text: firstMessage, hasAudio: false });
    }
  }
}

async function handleEndTurn(socket: WebSocket): Promise<void> {
  const state = activeConnections.get(socket);
  if (!state) {
    sendJSON(socket, { type: 'error', message: 'No active call' });
    return;
  }
  if (state.processing) {
    sendJSON(socket, { type: 'error', message: 'Already processing' });
    return;
  }

  const audioData = state.audioBuffer.flush();
  if (audioData.length === 0) {
    sendJSON(socket, { type: 'error', message: 'No audio data received' });
    return;
  }

  state.processing = true;
  sendJSON(socket, { type: 'processing', status: 'started' });

  try {
    // Resolve config from inline config (editor test) or DB (production)
    let modelConfig: { model?: string; temperature?: number; maxTokens?: number; toolIds?: string[] };
    let voiceConfig: { voiceId?: string; speed?: number };
    let transcriberConfig: { model?: string; language?: string };
    let resolvedEndCallPhrases: string[] | undefined;

    if (state.inlineConfig) {
      // Editor test — use stored inline config
      const cfg = state.inlineConfig;
      modelConfig = cfg.model;
      voiceConfig = cfg.voice;
      transcriberConfig = cfg.transcriber;
      resolvedEndCallPhrases = cfg.endCallPhrases;
    } else {
      // Production — fetch from DB
      const assistant = await prisma.assistant.findUnique({ where: { id: state.assistantId } });
      const extracted = extractAssistantConfig({
        model: assistant?.model ?? {},
        voice: assistant?.voice ?? {},
        transcriber: assistant?.transcriber ?? {},
      });
      modelConfig = extracted.modelConfig;
      voiceConfig = extracted.voiceConfig;
      transcriberConfig = extracted.transcriberConfig;
      resolvedEndCallPhrases = assistant?.endCallPhrases ?? undefined;
    }

    const tools = await loadToolsForPipeline(modelConfig.toolIds, state.organizationId);

    const result = await processPipelineTurn(state.sessionId, audioData, state.pipeline, {
      sttModel: transcriberConfig.model,
      sttLanguage: transcriberConfig.language,
      llmModel: modelConfig.model,
      llmTemperature: modelConfig.temperature,
      llmMaxTokens: modelConfig.maxTokens,
      ttsVoiceId: voiceConfig.voiceId,
      ttsSpeed: voiceConfig.speed,
      tools,
    });

    sendJSON(socket, { type: 'user_transcript', text: result.userText });
    sendJSON(socket, { type: 'assistant_message', text: result.assistantText, hasAudio: true });

    // Fire transcript webhook (skip for inline test calls)
    if (!state.inlineConfig) {
      fireWebhookEvent(state.organizationId, 'transcript.update', {
        callId: state.callId,
        userText: result.userText,
        assistantText: result.assistantText,
        toolCalls: result.toolCallsExecuted.map((tc) => ({ name: tc.name, success: tc.result.success })),
      }).catch(() => {});
    }

    // Send audio in chunks
    const CHUNK_SIZE = 16384;
    for (let i = 0; i < result.audioBuffer.length; i += CHUNK_SIZE) {
      const chunk = result.audioBuffer.subarray(i, i + CHUNK_SIZE);
      socket.send(chunk);
    }
    sendJSON(socket, { type: 'audio_end' });

    // Handle transfer request (not supported for inline test calls)
    if (result.transferRequest && !state.inlineConfig) {
      await handleTransfer(socket, state, result.transferRequest.targetAssistantId);
      return;
    }

    // Handle end-call request
    if (result.endCallRequested) {
      sendJSON(socket, { type: 'call_ending', reason: 'end_call_tool' });
      await handleStop(socket);
      return;
    }

    // Check for end-call phrases
    if (resolvedEndCallPhrases && resolvedEndCallPhrases.length > 0) {
      const lower = result.assistantText.toLowerCase();
      const shouldEnd = resolvedEndCallPhrases.some((phrase: string) =>
        lower.includes(phrase.toLowerCase())
      );
      if (shouldEnd) {
        sendJSON(socket, { type: 'call_ending', reason: 'end_phrase_detected' });
        await handleStop(socket);
        return;
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Pipeline processing failed';
    logger.error({ err, sessionId: state.sessionId }, 'Pipeline error during WebSocket processing');
    sendJSON(socket, { type: 'error', message });
  } finally {
    state.processing = false;
    sendJSON(socket, { type: 'processing', status: 'complete' });
  }
}

async function handleTransfer(
  socket: WebSocket,
  state: WebCallState,
  targetAssistantId: string,
): Promise<void> {
  try {
    const validated = await resolveTransfer(
      state.organizationId,
      state.assistantId,
      targetAssistantId,
    );

    if (!validated) {
      sendJSON(socket, { type: 'error', message: 'Transfer failed: assistants not in the same squad' });
      return;
    }

    // Load target assistant
    const targetAssistant = await prisma.assistant.findFirst({
      where: { id: targetAssistantId, organizationId: state.organizationId },
    });
    if (!targetAssistant) {
      sendJSON(socket, { type: 'error', message: 'Transfer target assistant not found' });
      return;
    }

    // Execute the transfer: update session and rebuild pipeline
    // Re-fetch org credentials so the new assistant's providers use org keys
    let transferCreds: { openaiApiKey?: string; deepgramApiKey?: string; elevenLabsApiKey?: string; cartesiaApiKey?: string } | undefined;
    try {
      const orgSettings = await getSettingsRaw(state.organizationId);
      transferCreds = orgSettings.providerCredentials;
    } catch { /* fall back to env vars */ }

    await executeTransfer(state.sessionId, targetAssistant);
    const newPipeline = buildPipelineFromAssistant(targetAssistant, transferCreds);

    // Update state
    state.assistantId = targetAssistant.id;
    state.pipeline = newPipeline;

    sendJSON(socket, {
      type: 'transfer',
      assistant: { id: targetAssistant.id, name: targetAssistant.name },
    });

    // Synthesize first message of new assistant
    if (targetAssistant.firstMessage) {
      const voiceConfig = targetAssistant.voice as { voiceId?: string; speed?: number };
      await addMessage(state.sessionId, { role: 'assistant', content: targetAssistant.firstMessage });

      try {
        const audio = await newPipeline.tts.synthesize(targetAssistant.firstMessage, {
          voiceId: voiceConfig.voiceId,
          speed: voiceConfig.speed,
        });
        sendJSON(socket, { type: 'assistant_message', text: targetAssistant.firstMessage, hasAudio: true });
        socket.send(audio);
        sendJSON(socket, { type: 'audio_end' });
      } catch {
        sendJSON(socket, { type: 'assistant_message', text: targetAssistant.firstMessage, hasAudio: false });
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Transfer failed';
    sendJSON(socket, { type: 'error', message });
  }
}

async function handleStop(socket: WebSocket): Promise<void> {
  const state = activeConnections.get(socket);
  if (!state) return;

  activeConnections.delete(socket);

  const session = await getSession(state.sessionId);
  const transcript = session?.conversationHistory
    .filter((m) => m.role !== 'system')
    .map((m) => ({ role: m.role, content: m.content })) ?? [];

  await endSession(state.sessionId);

  try {
    await endCall(state.callId, transcript, 'completed');
  } catch {
    // Call may already be ended
  }

  // Fire webhook (skip for inline test calls)
  if (!state.inlineConfig) {
    fireWebhookEvent(state.organizationId, 'call.ended', {
      callId: state.callId,
      endReason: 'completed',
      transcript,
    }).catch(() => {});
  }

  sendJSON(socket, { type: 'call_ended', callId: state.callId });
}
