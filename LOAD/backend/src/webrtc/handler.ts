/**
 * WebRTCCallHandler — manages one WebRTC voice call session.
 *
 * Pattern mirrors CallBridge from telephony/call-bridge.ts but for
 * browser-based WebRTC peer connections instead of Asterisk channels.
 *
 * Audio flow:
 *   Browser mic (Opus 48kHz) → RTP → decode → downsample → VAD → pipeline
 *   Pipeline TTS (24kHz PCM) → upsample → encode Opus → RTP → browser speakers
 */

import {
  RTCPeerConnection,
  RTCSessionDescription,
  RTCIceCandidate,
  MediaStreamTrack,
  RtpPacket,
} from 'werift';
import { prisma } from '../database/client.js';
import { AudioBridge, wrapPcmAsWav, OPUS_FRAME_MS, OPUS_FRAME_SAMPLES } from './audio-bridge.js';
import { SimpleVAD } from '../telephony/vad.js';
import { processPipelineTurn, type PipelineConfig } from '../voice-pipeline/pipeline.js';
import {
  getSession,
  endSession,
  addMessage,
} from '../voice-pipeline/session.js';
import { extractAssistantConfig, loadToolsForPipeline } from '../voice-pipeline/pipeline-helpers.js';
import { buildPipelineFromAssistant } from '../providers/registry.js';
import { endCall, failCall } from '../modules/calls/service.js';
import { fireWebhookEvent } from '../modules/webhooks/delivery.js';
import { resolveTransfer, executeTransfer } from '../voice-pipeline/squad-transfer.js';
import { config } from '../config/index.js';

/** STT/VAD sample rate. */
const STT_SAMPLE_RATE = 16_000;

interface WebRTCHandlerParams {
  organizationId: string;
  assistantId: string;
  callId: string;
  sessionId: string;
  pipeline: PipelineConfig;
  assistant: {
    id: string;
    name: string;
    model: unknown;
    voice: unknown;
    transcriber: unknown;
    firstMessage: string | null;
    endCallPhrases: string[];
    metadata: unknown;
  };
}

interface DataChannelMessage {
  type: string;
  [key: string]: unknown;
}

export class WebRTCCallHandler {
  private pc: RTCPeerConnection;
  private audioBridge: AudioBridge;
  private vad: SimpleVAD;
  private audioChunks: Buffer[] = [];
  private processing = false;
  private closed = false;

  private sender: any = null;
  private dataChannel: ReturnType<RTCPeerConnection['createDataChannel']> | null = null;

  // RTP state for outgoing audio
  private rtpSeqNum = 0;
  private rtpTimestamp = 0;
  private rtpSsrc = Math.floor(Math.random() * 0xffffffff);

  readonly callId: string;
  readonly sessionId: string;
  readonly organizationId: string;
  readonly createdAt: number = Date.now();
  private assistantId: string;
  private pipeline: PipelineConfig;
  private readonly assistant: WebRTCHandlerParams['assistant'];
  private onCloseCallback: (() => void) | null = null;

  constructor(params: WebRTCHandlerParams) {
    this.callId = params.callId;
    this.sessionId = params.sessionId;
    this.organizationId = params.organizationId;
    this.assistantId = params.assistantId;
    this.pipeline = params.pipeline;
    this.assistant = params.assistant;

    this.audioBridge = new AudioBridge();
    this.vad = new SimpleVAD({ sampleRate: STT_SAMPLE_RATE });

    this.pc = new RTCPeerConnection({
      iceServers: this.buildIceServers().map((url) => ({ urls: url })),
    });
  }

  /**
   * Register a callback to be invoked when this handler closes itself
   * (e.g., due to peer connection failure or end-call phrase).
   */
  onClose(callback: () => void): void {
    this.onCloseCallback = callback;
  }

  /**
   * Handle an SDP offer from the browser client.
   * Sets up transceiver, DataChannel, and RTP listener.
   * Returns the SDP answer string.
   */
  async handleOffer(sdpOffer: string): Promise<string> {
    // Create a DataChannel for JSON control messages
    this.dataChannel = this.pc.createDataChannel('control');

    // Add a sendrecv audio transceiver
    const transceiver = this.pc.addTransceiver('audio', {
      direction: 'sendrecv',
    });

    // Store the sender for outgoing RTP
    this.sender = transceiver.sender;

    // Listen for incoming audio via the transceiver's onTrack event
    // When the remote track arrives, subscribe to its RTP packets
    transceiver.onTrack.subscribe((track: MediaStreamTrack) => {
      track.onReceiveRtp.subscribe((rtp: RtpPacket) => {
        if (this.closed) return;
        this.onAudioRtpPacket(rtp);
      });
    });

    // Set remote description (browser's offer)
    await this.pc.setRemoteDescription(
      new RTCSessionDescription(sdpOffer, 'offer')
    );

    // Create and set local description (our answer)
    const answer = await this.pc.createAnswer();
    await this.pc.setLocalDescription(answer);

    // Monitor connection state — auto-close on failure/disconnect
    this.pc.connectionStateChange.subscribe((state: string) => {
      if (state === 'failed' || state === 'disconnected' || state === 'closed') {
        if (!this.closed) {
          console.warn(`[WebRTC] Peer connection ${state} for call ${this.callId}, auto-closing`);
          this.close().catch(() => {});
        }
      }
    });

    // Send call_started message once DataChannel opens
    this.dataChannel.onopen = () => {
      this.sendDataChannelMessage({
        type: 'call_started',
        callId: this.callId,
        sessionId: this.sessionId,
        assistant: { id: this.assistant.id, name: this.assistant.name },
      });

      // Handle first message
      if (this.assistant.firstMessage) {
        this.handleFirstMessage().catch((err) => {
          console.error('[WebRTC] Failed to send first message:', err);
        });
      }
    };

    return this.pc.localDescription?.sdp ?? '';
  }

  /**
   * Add a trickle ICE candidate from the browser.
   */
  async addIceCandidate(candidate: {
    candidate: string;
    sdpMid?: string | null;
    sdpMLineIndex?: number | null;
  }): Promise<void> {
    await this.pc.addIceCandidate(
      new RTCIceCandidate({
        candidate: candidate.candidate,
        sdpMid: candidate.sdpMid ?? undefined,
        sdpMLineIndex: candidate.sdpMLineIndex ?? undefined,
      })
    );
  }

  /**
   * Close the peer connection and clean up.
   */
  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;

    // Get transcript before ending session
    const session = await getSession(this.sessionId);
    const transcript = session?.conversationHistory
      .filter((m) => m.role !== 'system')
      .map((m) => ({ role: m.role, content: m.content })) ?? [];

    this.sendDataChannelMessage({ type: 'call_ended', callId: this.callId });

    await endSession(this.sessionId);

    try {
      await endCall(this.callId, transcript, 'completed');
    } catch {
      // Call may already be ended
    }

    fireWebhookEvent(this.organizationId, 'call.ended', {
      callId: this.callId,
      endReason: 'completed',
      transcript,
    }).catch(() => {});

    try {
      await this.pc.close();
    } catch {
      // Peer connection may already be closed
    }

    // Notify the route layer to remove this handler from the map
    if (this.onCloseCallback) {
      this.onCloseCallback();
      this.onCloseCallback = null;
    }
  }

  /**
   * Process an incoming audio RTP packet.
   */
  private onAudioRtpPacket(rtp: RtpPacket): void {
    if (this.processing) return;

    try {
      // Decode Opus to 48kHz PCM
      const pcm48k = this.audioBridge.decodeOpusToPcm(rtp.payload);

      // Downsample to 16kHz for VAD + STT
      const pcm16k = this.audioBridge.downsampleForStt(pcm48k);

      // Feed to VAD
      const { isSpeech, speechComplete } = this.vad.processChunk(pcm16k);

      if (isSpeech || speechComplete) {
        this.audioChunks = [...this.audioChunks, pcm16k];
      }

      if (speechComplete) {
        this.runPipelineTurn().catch((err) => {
          console.error('[WebRTC] Pipeline turn failed:', err);
        });
      }
    } catch (err) {
      // Malformed packet — skip silently
      console.warn('[WebRTC] Failed to process RTP packet:', err);
    }
  }

  /**
   * Concatenate accumulated audio, run the voice pipeline, and play back TTS.
   */
  private async runPipelineTurn(): Promise<void> {
    if (this.processing || this.closed) return;
    this.processing = true;

    const chunks = this.audioChunks;
    this.audioChunks = [];
    this.vad.reset();

    if (chunks.length === 0) {
      this.processing = false;
      return;
    }

    this.sendDataChannelMessage({ type: 'processing', status: 'started' });

    try {
      const combinedPcm = Buffer.concat(chunks);
      const wavBuffer = wrapPcmAsWav(combinedPcm, STT_SAMPLE_RATE);

      // Fetch current assistant for tools
      const assistant = await prisma.assistant.findUnique({
        where: { id: this.assistantId },
      });

      const { modelConfig, voiceConfig, transcriberConfig } = extractAssistantConfig({
        model: assistant?.model ?? this.assistant.model,
        voice: assistant?.voice ?? this.assistant.voice,
        transcriber: assistant?.transcriber ?? this.assistant.transcriber,
      });

      const tools = await loadToolsForPipeline(modelConfig.toolIds, this.organizationId);

      const result = await processPipelineTurn(this.sessionId, wavBuffer, this.pipeline, {
        sttModel: transcriberConfig.model,
        sttLanguage: transcriberConfig.language,
        llmModel: modelConfig.model,
        llmTemperature: modelConfig.temperature,
        llmMaxTokens: modelConfig.maxTokens,
        ttsVoiceId: voiceConfig.voiceId,
        ttsSpeed: voiceConfig.speed,
        format: 'wav',
        tools,
      });

      // Send transcript via DataChannel
      this.sendDataChannelMessage({ type: 'user_transcript', text: result.userText });
      this.sendDataChannelMessage({ type: 'assistant_message', text: result.assistantText });

      // Fire transcript webhook
      fireWebhookEvent(this.organizationId, 'transcript.update', {
        callId: this.callId,
        userText: result.userText,
        assistantText: result.assistantText,
        toolCalls: result.toolCallsExecuted.map((tc) => ({
          name: tc.name,
          success: tc.result.success,
        })),
      }).catch(() => {});

      // Play TTS audio via RTP
      await this.playTtsAudio(result.audioBuffer);

      // Handle transfer
      if (result.transferRequest) {
        await this.handleTransfer(result.transferRequest.targetAssistantId);
        return;
      }

      // Handle end-call tool
      if (result.endCallRequested) {
        this.sendDataChannelMessage({ type: 'call_ending', reason: 'end_call_tool' });
        await this.close();
        return;
      }

      // Check for end-call phrases
      const endCallPhrases = assistant?.endCallPhrases ?? this.assistant.endCallPhrases;
      if (endCallPhrases.length > 0) {
        const lower = result.assistantText.toLowerCase();
        const shouldEnd = endCallPhrases.some((phrase: string) =>
          lower.includes(phrase.toLowerCase())
        );
        if (shouldEnd) {
          this.sendDataChannelMessage({ type: 'call_ending', reason: 'end_phrase_detected' });
          await this.close();
          return;
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Pipeline processing failed';
      console.error(`[WebRTC] Pipeline error for session ${this.sessionId}:`, err);
      this.sendDataChannelMessage({ type: 'error', message });

      try {
        await failCall(this.callId, message);
        await fireWebhookEvent(this.organizationId, 'call.failed', {
          callId: this.callId,
          assistantId: this.assistantId,
          error: message,
        });
      } catch {
        // Ignore failure reporting errors
      }
    } finally {
      this.processing = false;
      this.sendDataChannelMessage({ type: 'processing', status: 'complete' });
    }
  }

  /**
   * Upsample TTS PCM from 24kHz to 48kHz, encode to Opus, and send via RTP
   * paced at 20ms intervals to match real-time playback.
   */
  private async playTtsAudio(pcm24k: Buffer): Promise<void> {
    if (this.closed || !this.sender) return;

    // Upsample 24kHz → 48kHz
    const pcm48k = this.audioBridge.upsampleFromTts(pcm24k);

    // Encode into 20ms Opus frames
    const opusFrames = this.audioBridge.encodeForRtp(pcm48k);

    // Send each frame paced at 20ms
    for (const opusFrame of opusFrames) {
      if (this.closed) break;

      this.rtpSeqNum = (this.rtpSeqNum + 1) & 0xffff;
      this.rtpTimestamp = (this.rtpTimestamp + OPUS_FRAME_SAMPLES) >>> 0;

      try {
        // Use sender.sendRtp() — the werift API for pushing RTP packets
        this.sender.sendRtp(opusFrame, {
          sequenceNumber: this.rtpSeqNum,
          timestamp: this.rtpTimestamp,
        });
      } catch {
        // Sender may be closed
        break;
      }

      // Pace at 20ms per frame for real-time playback
      await sleep(OPUS_FRAME_MS);
    }
  }

  /**
   * Handle assistant transfer within a squad.
   */
  private async handleTransfer(targetAssistantId: string): Promise<void> {
    const validated = await resolveTransfer(
      this.organizationId,
      this.assistantId,
      targetAssistantId,
    );

    if (!validated) {
      this.sendDataChannelMessage({
        type: 'error',
        message: 'Transfer failed: assistants not in the same squad',
      });
      return;
    }

    const targetAssistant = await prisma.assistant.findFirst({
      where: { id: targetAssistantId, organizationId: this.organizationId },
    });
    if (!targetAssistant) {
      this.sendDataChannelMessage({
        type: 'error',
        message: 'Transfer target assistant not found',
      });
      return;
    }

    await executeTransfer(this.sessionId, targetAssistant);
    const newPipeline = buildPipelineFromAssistant(targetAssistant);

    this.assistantId = targetAssistant.id;
    this.pipeline = newPipeline;

    this.sendDataChannelMessage({
      type: 'transfer',
      assistant: { id: targetAssistant.id, name: targetAssistant.name },
    });

    // Play first message of new assistant
    if (targetAssistant.firstMessage) {
      const voiceConfig = targetAssistant.voice as { voiceId?: string; speed?: number };
      await addMessage(this.sessionId, { role: 'assistant', content: targetAssistant.firstMessage });

      try {
        const audio = await newPipeline.tts.synthesize(targetAssistant.firstMessage, {
          voiceId: voiceConfig.voiceId,
          speed: voiceConfig.speed,
        });
        this.sendDataChannelMessage({
          type: 'assistant_message',
          text: targetAssistant.firstMessage,
        });
        await this.playTtsAudio(audio);
      } catch {
        this.sendDataChannelMessage({
          type: 'assistant_message',
          text: targetAssistant.firstMessage,
        });
      }
    }
  }

  /**
   * Synthesize and play the assistant's first message.
   */
  private async handleFirstMessage(): Promise<void> {
    const voiceConfig = this.assistant.voice as { voiceId?: string; speed?: number };

    await addMessage(this.sessionId, {
      role: 'assistant',
      content: this.assistant.firstMessage!,
    });

    try {
      const audio = await this.pipeline.tts.synthesize(this.assistant.firstMessage!, {
        voiceId: voiceConfig.voiceId,
        speed: voiceConfig.speed,
      });
      this.sendDataChannelMessage({
        type: 'assistant_message',
        text: this.assistant.firstMessage!,
      });
      await this.playTtsAudio(audio);
    } catch {
      this.sendDataChannelMessage({
        type: 'assistant_message',
        text: this.assistant.firstMessage!,
      });
    }
  }

  /**
   * Send a JSON message over the DataChannel.
   */
  private sendDataChannelMessage(data: DataChannelMessage): void {
    try {
      if (this.dataChannel?.readyState === 'open') {
        this.dataChannel.send(JSON.stringify(data));
      }
    } catch {
      // DataChannel may be closing
    }
  }

  /**
   * Build ICE server list from environment.
   */
  private buildIceServers(): string[] {
    const servers: string[] = [];
    const stunServers = config.STUN_SERVERS ?? 'stun:stun.l.google.com:19302';
    servers.push(...stunServers.split(',').map((s) => s.trim()));
    return servers;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
