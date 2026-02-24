/**
 * Bridge between Asterisk ARI and the LOAD voice pipeline.
 *
 * Manages the lifecycle of telephony calls: inbound call routing,
 * outbound call origination, voice activity detection, pipeline
 * invocation, and session/channel cleanup.
 *
 * Audio processing via ExternalMedia UDP is not yet fully implemented.
 * The core flow (channel management, session lifecycle, webhook events)
 * is the priority for this phase.
 */

import { prisma } from '../database/client.js';
import {
  createCall,
  updateCallStatus,
  endCall,
  failCall,
} from '../modules/calls/service.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { buildPipelineFromAssistant } from '../providers/registry.js';
import { processPipelineTurn } from '../voice-pipeline/pipeline.js';
import {
  createSession,
  getSession,
  endSession,
  addMessage,
} from '../voice-pipeline/session.js';
import { resolveTransfer, executeTransfer } from '../voice-pipeline/squad-transfer.js';
import { extractAssistantConfig, loadToolsForPipeline } from '../voice-pipeline/pipeline-helpers.js';
import { downsample } from './audio-resample.js';
import type {
  AsteriskAriClient,
  StasisStartEvent,
  StasisEndEvent,
} from './asterisk-ari.js';
import { SimpleVAD } from './vad.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Sample rate of TTS output (OpenAI TTS default). */
const TTS_SAMPLE_RATE = 24_000;

/** Sample rate expected by Asterisk ExternalMedia (slin16). */
const ASTERISK_SAMPLE_RATE = 16_000;

/** Default SIP trunk endpoint template for outbound calls. */
const DEFAULT_OUTBOUND_ENDPOINT = 'PJSIP/{number}@ant-cellular';

/** GoIP trunk endpoint template. */
const GOIP_OUTBOUND_ENDPOINT = 'PJSIP/{number}@{trunk}';

/**
 * Resolve the PJSIP endpoint for an outbound call based on the phone number's provider.
 */
function resolveEndpoint(
  customerNumber: string,
  provider: string,
  metadata?: Record<string, unknown> | null,
): string {
  if (provider === 'GOIP') {
    const trunkName = (metadata?.trunkName as string) ?? 'goip-trunk';
    return GOIP_OUTBOUND_ENDPOINT
      .replace('{number}', customerNumber)
      .replace('{trunk}', trunkName);
  }
  return DEFAULT_OUTBOUND_ENDPOINT.replace('{number}', customerNumber);
}

// ---------------------------------------------------------------------------
// CallBridge
// ---------------------------------------------------------------------------

export class CallBridge {
  private readonly ariClient: AsteriskAriClient;

  /** channelId -> sessionId */
  private readonly channelToSession: Map<string, string>;

  /** sessionId -> channelId */
  private readonly sessionToChannel: Map<string, string>;

  /** sessionId -> VAD instance */
  private readonly sessionVAD: Map<string, SimpleVAD>;

  /** sessionId -> accumulated audio chunks for current utterance */
  private readonly sessionAudio: Map<string, Buffer[]>;

  /** sessionId -> bridgeId */
  private readonly sessionBridge: Map<string, string>;

  /** sessionId -> current assistantId (for transfers) */
  private readonly sessionAssistant: Map<string, string>;

  constructor(ariClient: AsteriskAriClient) {
    this.ariClient = ariClient;
    this.channelToSession = new Map();
    this.sessionToChannel = new Map();
    this.sessionVAD = new Map();
    this.sessionAudio = new Map();
    this.sessionBridge = new Map();
    this.sessionAssistant = new Map();
  }

  // -----------------------------------------------------------------------
  // Initialization
  // -----------------------------------------------------------------------

  async initialize(): Promise<void> {
    console.log('[CallBridge] Initializing ARI connection...');

    await this.ariClient.connect({
      onStasisStart: (event: StasisStartEvent) => {
        const isOutbound = event.args.includes('outbound');
        if (isOutbound) {
          this.onOutboundAnswer(event).catch((error) => {
            console.error('[CallBridge] Error handling outbound answer:', error);
          });
        } else {
          this.onInbound(event).catch((error) => {
            console.error('[CallBridge] Error handling inbound call:', error);
          });
        }
      },
      onStasisEnd: (event: StasisEndEvent) => {
        this.onChannelEnd(event).catch((error) => {
          console.error('[CallBridge] Error handling channel end:', error);
        });
      },
      onChannelDtmf: (event) => {
        console.log(
          `[CallBridge] DTMF received on channel ${event.channelId}: digit=${event.digit} (no-op)`
        );
      },
    });

    console.log('[CallBridge] Initialized and listening for calls');
  }

  // -----------------------------------------------------------------------
  // Outbound origination
  // -----------------------------------------------------------------------

  async initiateOutbound(params: {
    organizationId: string;
    assistantId: string;
    customerNumber: string;
    phoneNumberId: string;
    metadata?: Record<string, unknown>;
  }): Promise<{ callId: string; channelId: string }> {
    console.log(
      `[CallBridge] Initiating outbound call to ${params.customerNumber} ` +
        `(assistant=${params.assistantId})`
    );

    const assistant = await prisma.assistant.findUnique({
      where: { id: params.assistantId },
    });
    if (!assistant) {
      throw Object.assign(new Error('Assistant not found'), {
        statusCode: 404,
      });
    }

    const phoneNumber = await prisma.phoneNumber.findUnique({
      where: { id: params.phoneNumberId },
    });
    if (!phoneNumber) {
      throw Object.assign(new Error('Phone number not found'), {
        statusCode: 404,
      });
    }

    const call = await createCall({
      organizationId: params.organizationId,
      assistantId: assistant.id,
      type: 'OUTBOUND',
      customerNumber: params.customerNumber,
      phoneNumberId: phoneNumber.id,
    });

    await updateCallStatus(call.id, 'RINGING');

    const modelConfig = assistant.model as { systemPrompt?: string };
    const session = await createSession({
      callId: call.id,
      assistantId: assistant.id,
      organizationId: params.organizationId,
      systemPrompt: modelConfig.systemPrompt,
    });

    const vad = new SimpleVAD();

    const endpoint = resolveEndpoint(
      params.customerNumber,
      phoneNumber.provider,
      phoneNumber.metadata as Record<string, unknown> | null,
    );
    const channelId = await this.ariClient.originateCall({
      endpoint,
      callerId: phoneNumber.number,
      appArgs: ['outbound'],
    });

    this.channelToSession.set(channelId, session.id);
    this.sessionToChannel.set(session.id, channelId);
    this.sessionVAD.set(session.id, vad);
    this.sessionAudio.set(session.id, []);
    this.sessionAssistant.set(session.id, assistant.id);

    await fireWebhookEvent(params.organizationId, 'call.started', {
      callId: call.id,
      type: 'OUTBOUND',
      assistantId: assistant.id,
      customerNumber: params.customerNumber,
      phoneNumberId: phoneNumber.id,
      metadata: params.metadata ?? {},
    }).catch((error) => {
      console.warn('[CallBridge] Failed to fire call.started webhook:', error);
    });

    console.log(
      `[CallBridge] Outbound call originated: callId=${call.id} channelId=${channelId}`
    );

    return { callId: call.id, channelId };
  }

  // -----------------------------------------------------------------------
  // Inbound call handling
  // -----------------------------------------------------------------------

  private async onInbound(event: StasisStartEvent): Promise<void> {
    console.log(
      `[CallBridge] Inbound call: channel=${event.channelId} ` +
        `from=${event.callerNumber} to=${event.calledNumber}`
    );

    const phoneNumber = await prisma.phoneNumber.findFirst({
      where: {
        number: { endsWith: event.calledNumber },
        status: 'ACTIVE',
      },
    });

    if (!phoneNumber || !phoneNumber.assistantId) {
      console.error(
        `[CallBridge] No active phone number or assistant found for ${event.calledNumber}`
      );
      try {
        await this.ariClient.hangupChannel(event.channelId);
      } catch (hangupError) {
        console.error('[CallBridge] Failed to hangup unroutable channel:', hangupError);
      }
      return;
    }

    const assistant = await prisma.assistant.findUnique({
      where: { id: phoneNumber.assistantId },
    });

    if (!assistant) {
      console.error(
        `[CallBridge] Assistant ${phoneNumber.assistantId} not found for phone number ${phoneNumber.id}`
      );
      try {
        await this.ariClient.hangupChannel(event.channelId);
      } catch (hangupError) {
        console.error('[CallBridge] Failed to hangup channel:', hangupError);
      }
      return;
    }

    let call;
    try {
      call = await createCall({
        organizationId: phoneNumber.organizationId,
        assistantId: assistant.id,
        type: 'INBOUND',
        customerNumber: event.callerNumber,
        phoneNumberId: phoneNumber.id,
      });
    } catch (error) {
      console.error('[CallBridge] Failed to create call record:', error);
      try {
        await this.ariClient.hangupChannel(event.channelId);
      } catch (hangupError) {
        console.error('[CallBridge] Failed to hangup channel after call creation failure:', hangupError);
      }
      return;
    }

    await updateCallStatus(call.id, 'IN_PROGRESS');

    const modelConfig = assistant.model as { systemPrompt?: string };
    const session = await createSession({
      callId: call.id,
      assistantId: assistant.id,
      organizationId: phoneNumber.organizationId,
      systemPrompt: modelConfig.systemPrompt,
    });

    this.channelToSession.set(event.channelId, session.id);
    this.sessionToChannel.set(session.id, event.channelId);
    this.sessionAudio.set(session.id, []);
    this.sessionAssistant.set(session.id, assistant.id);

    const vad = new SimpleVAD();
    this.sessionVAD.set(session.id, vad);

    await fireWebhookEvent(phoneNumber.organizationId, 'call.started', {
      callId: call.id,
      type: 'INBOUND',
      assistantId: assistant.id,
      customerNumber: event.callerNumber,
      phoneNumberId: phoneNumber.id,
    }).catch((error) => {
      console.warn('[CallBridge] Failed to fire call.started webhook:', error);
    });

    if (assistant.firstMessage) {
      try {
        await addMessage(session.id, {
          role: 'assistant',
          content: assistant.firstMessage,
        });

        const pipeline = buildPipelineFromAssistant(assistant);
        const voiceConfig = assistant.voice as {
          voiceId?: string;
          speed?: number;
        };

        const ttsAudio = await pipeline.tts.synthesize(
          assistant.firstMessage,
          {
            voiceId: voiceConfig.voiceId,
            speed: voiceConfig.speed,
          }
        );

        const asteriskAudio = downsample(
          ttsAudio,
          TTS_SAMPLE_RATE,
          ASTERISK_SAMPLE_RATE
        );

        console.log(
          `[CallBridge] First message audio ready (${asteriskAudio.length} bytes) ` +
            'but ExternalMedia UDP send is not yet implemented'
        );
      } catch (error) {
        console.error(
          '[CallBridge] Failed to synthesize first message:',
          error
        );
      }
    }

    console.log(
      `[CallBridge] Inbound call set up: callId=${call.id} ` +
        `sessionId=${session.id} channelId=${event.channelId}`
    );
  }

  // -----------------------------------------------------------------------
  // Outbound answer handling
  // -----------------------------------------------------------------------

  private async onOutboundAnswer(event: StasisStartEvent): Promise<void> {
    console.log(
      `[CallBridge] Outbound call answered: channel=${event.channelId}`
    );

    const sessionId = this.channelToSession.get(event.channelId);

    if (!sessionId) {
      console.warn(
        `[CallBridge] No session found for outbound channel ${event.channelId}. ` +
          'This may indicate a channel ID mismatch.'
      );
      return;
    }

    const session = await getSession(sessionId);
    if (!session) {
      console.warn(
        `[CallBridge] Session ${sessionId} not found for outbound channel ${event.channelId}`
      );
      return;
    }

    try {
      await updateCallStatus(session.callId, 'IN_PROGRESS');
    } catch (error) {
      console.error(
        `[CallBridge] Failed to update call status to IN_PROGRESS for call ${session.callId}:`,
        error
      );
    }

    console.log(
      `[CallBridge] Outbound call in progress: callId=${session.callId} ` +
        `sessionId=${sessionId} channelId=${event.channelId}`
    );
  }

  // -----------------------------------------------------------------------
  // Channel end handling
  // -----------------------------------------------------------------------

  private async onChannelEnd(event: StasisEndEvent): Promise<void> {
    console.log(`[CallBridge] Channel ended: ${event.channelId}`);

    const sessionId = this.channelToSession.get(event.channelId);
    if (!sessionId) {
      console.log(
        `[CallBridge] No session found for ended channel ${event.channelId} (already cleaned up?)`
      );
      return;
    }

    const session = await getSession(sessionId);
    if (!session) {
      console.warn(
        `[CallBridge] Session ${sessionId} not found during channel end`
      );
      await this.cleanup(sessionId);
      return;
    }

    const transcript = session.conversationHistory
      .filter((m) => m.role !== 'system')
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      await endCall(session.callId, transcript, 'hangup');
    } catch (error) {
      console.error(
        `[CallBridge] Failed to end call ${session.callId}:`,
        error
      );
    }

    await fireWebhookEvent(session.organizationId, 'call.ended', {
      callId: session.callId,
      assistantId: session.assistantId,
      duration: session.startedAt
        ? Math.round((Date.now() - session.startedAt.getTime()) / 1000)
        : 0,
      transcript,
      endReason: 'hangup',
    }).catch((error) => {
      console.warn('[CallBridge] Failed to fire call.ended webhook:', error);
    });

    await this.cleanup(sessionId);

    console.log(
      `[CallBridge] Call ended and cleaned up: callId=${session.callId} ` +
        `sessionId=${sessionId}`
    );
  }

  // -----------------------------------------------------------------------
  // Audio processing
  // -----------------------------------------------------------------------

  async processAudioChunk(sessionId: string, chunk: Buffer): Promise<void> {
    const vad = this.sessionVAD.get(sessionId);
    if (!vad) {
      console.warn(
        `[CallBridge] No VAD found for session ${sessionId}, ignoring audio chunk`
      );
      return;
    }

    const audioChunks = this.sessionAudio.get(sessionId);
    if (!audioChunks) {
      console.warn(
        `[CallBridge] No audio buffer found for session ${sessionId}, ignoring audio chunk`
      );
      return;
    }

    const { isSpeech, speechComplete } = vad.processChunk(chunk);

    if (isSpeech || speechComplete) {
      this.sessionAudio.set(sessionId, [...audioChunks, chunk]);
    }

    if (speechComplete) {
      await this.runPipelineTurn(sessionId);
    }
  }

  // -----------------------------------------------------------------------
  // Pipeline execution
  // -----------------------------------------------------------------------

  private async runPipelineTurn(sessionId: string): Promise<void> {
    const session = await getSession(sessionId);
    if (!session) {
      console.error(
        `[CallBridge] Cannot run pipeline turn: session ${sessionId} not found`
      );
      return;
    }

    const audioChunks = this.sessionAudio.get(sessionId) ?? [];
    this.sessionAudio.set(sessionId, []);

    const vad = this.sessionVAD.get(sessionId);
    if (vad) {
      vad.reset();
    }

    if (audioChunks.length === 0) {
      console.log(
        `[CallBridge] No audio accumulated for session ${sessionId}, skipping pipeline turn`
      );
      return;
    }

    const combinedAudio = Buffer.concat(audioChunks);

    console.log(
      `[CallBridge] Running pipeline turn for session ${sessionId} ` +
        `(${combinedAudio.length} bytes of audio)`
    );

    try {
      const currentAssistantId = this.sessionAssistant.get(sessionId) ?? session.assistantId;
      const assistant = await prisma.assistant.findUnique({
        where: { id: currentAssistantId },
      });

      if (!assistant) {
        console.error(
          `[CallBridge] Assistant ${currentAssistantId} not found during pipeline turn`
        );
        return;
      }

      const pipeline = buildPipelineFromAssistant(assistant);

      const { modelConfig, voiceConfig, transcriberConfig } = extractAssistantConfig(assistant);
      const tools = await loadToolsForPipeline(modelConfig.toolIds, session.organizationId);

      const result = await processPipelineTurn(
        sessionId,
        combinedAudio,
        pipeline,
        {
          sttModel: transcriberConfig.model,
          sttLanguage: transcriberConfig.language,
          llmModel: modelConfig.model,
          llmTemperature: modelConfig.temperature,
          llmMaxTokens: modelConfig.maxTokens,
          ttsVoiceId: voiceConfig.voiceId,
          ttsSpeed: voiceConfig.speed,
          tools,
        }
      );

      const asteriskAudio = downsample(
        result.audioBuffer,
        TTS_SAMPLE_RATE,
        ASTERISK_SAMPLE_RATE
      );

      console.log(
        `[CallBridge] Pipeline turn complete for session ${sessionId}: ` +
          `user="${result.userText}" assistant="${result.assistantText}" ` +
          `audioOut=${asteriskAudio.length} bytes ` +
          '(ExternalMedia UDP send not yet implemented)'
      );

      // Handle transfer
      if (result.transferRequest) {
        await this.handleTransfer(sessionId, session.organizationId, result.transferRequest.targetAssistantId);
        return;
      }

      // Handle end-call tool
      if (result.endCallRequested) {
        console.log(`[CallBridge] End-call tool triggered in session ${sessionId}, hanging up`);
        const channelId = this.sessionToChannel.get(sessionId);
        if (channelId) {
          try {
            await this.ariClient.hangupChannel(channelId);
          } catch (error) {
            console.error(`[CallBridge] Failed to hangup channel ${channelId}:`, error);
          }
        }
        return;
      }

      // Check for end-call phrases (legacy)
      if (
        assistant.endCallPhrases &&
        assistant.endCallPhrases.length > 0
      ) {
        const lowerResponse = result.assistantText.toLowerCase();
        const shouldEnd = assistant.endCallPhrases.some((phrase) =>
          lowerResponse.includes(phrase.toLowerCase())
        );

        if (shouldEnd) {
          console.log(
            `[CallBridge] End-call phrase detected in session ${sessionId}, hanging up`
          );
          const channelId = this.sessionToChannel.get(sessionId);
          if (channelId) {
            try {
              await this.ariClient.hangupChannel(channelId);
            } catch (error) {
              console.error(
                `[CallBridge] Failed to hangup channel ${channelId} after end-call phrase:`,
                error
              );
            }
          }
        }
      }
    } catch (error) {
      console.error(
        `[CallBridge] Pipeline turn failed for session ${sessionId}:`,
        error
      );

      try {
        const reason =
          error instanceof Error ? error.message : 'Pipeline processing failed';
        await failCall(session.callId, reason);
        await fireWebhookEvent(session.organizationId, 'call.failed', {
          callId: session.callId,
          assistantId: session.assistantId,
          error: reason,
        });
      } catch (failError) {
        console.error(
          `[CallBridge] Failed to record call failure for ${session.callId}:`,
          failError
        );
      }
    }
  }

  // -----------------------------------------------------------------------
  // Transfer handling
  // -----------------------------------------------------------------------

  private async handleTransfer(
    sessionId: string,
    organizationId: string,
    targetAssistantId: string,
  ): Promise<void> {
    const currentAssistantId = this.sessionAssistant.get(sessionId);
    if (!currentAssistantId) return;

    const validated = await resolveTransfer(organizationId, currentAssistantId, targetAssistantId);
    if (!validated) {
      console.warn(`[CallBridge] Transfer failed: assistants not in same squad`);
      return;
    }

    const targetAssistant = await prisma.assistant.findFirst({
      where: { id: targetAssistantId, organizationId },
    });
    if (!targetAssistant) {
      console.warn(`[CallBridge] Transfer target assistant ${targetAssistantId} not found`);
      return;
    }

    await executeTransfer(sessionId, targetAssistant);
    this.sessionAssistant.set(sessionId, targetAssistantId);

    console.log(`[CallBridge] Transferred session ${sessionId} to assistant ${targetAssistantId}`);
  }

  // -----------------------------------------------------------------------
  // Cleanup
  // -----------------------------------------------------------------------

  private async cleanup(sessionId: string): Promise<void> {
    console.log(`[CallBridge] Cleaning up session ${sessionId}`);

    await endSession(sessionId);

    const channelId = this.sessionToChannel.get(sessionId);
    if (channelId) {
      this.channelToSession.delete(channelId);
    }

    this.sessionToChannel.delete(sessionId);
    this.sessionVAD.delete(sessionId);
    this.sessionAudio.delete(sessionId);
    this.sessionAssistant.delete(sessionId);

    const bridgeId = this.sessionBridge.get(sessionId);
    if (bridgeId) {
      this.sessionBridge.delete(sessionId);
      try {
        await this.ariClient.destroyBridge(bridgeId);
      } catch (error) {
        console.warn(
          `[CallBridge] Failed to destroy bridge ${bridgeId} during cleanup:`,
          error
        );
      }
    }

    console.log(`[CallBridge] Session ${sessionId} cleaned up`);
  }
}
