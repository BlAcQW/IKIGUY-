/**
 * Voice Activity Detection (VAD) for browser
 * Detects speech in audio streams using energy-based detection
 *
 * Shared utility for all apps (StudyFlow, InkWave, etc.)
 */

export interface VADOptions {
  energyThreshold?: number;      // Energy threshold for speech detection (default: 0.02)
  silenceTimeout?: number;       // ms of silence before ending speech (default: 1500)
  speechTimeout?: number;        // ms of speech before triggering start (default: 300)
  onSpeechStart?: () => void;
  onSpeechEnd?: (audioBlob: Blob) => void;
  onVolumeChange?: (volume: number) => void;
  onError?: (error: string) => void;
}

export class VoiceActivityDetector {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private mediaStream: MediaStream | null = null;

  // Recording
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  // VAD parameters
  private energyThreshold: number;
  private silenceTimeout: number;
  private speechTimeout: number;

  // State
  private isSpeaking = false;
  private isRecording = false;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private speechTimer: ReturnType<typeof setTimeout> | null = null;
  private isActive = false;

  // Callbacks
  private onSpeechStart?: () => void;
  private onSpeechEnd?: (audioBlob: Blob) => void;
  private onVolumeChange?: (volume: number) => void;
  private onError?: (error: string) => void;

  constructor(options: VADOptions = {}) {
    // Configure thresholds
    this.energyThreshold = options.energyThreshold ?? 0.02;
    this.silenceTimeout = options.silenceTimeout ?? 1500;
    this.speechTimeout = options.speechTimeout ?? 300;

    // Set callbacks
    this.onSpeechStart = options.onSpeechStart;
    this.onSpeechEnd = options.onSpeechEnd;
    this.onVolumeChange = options.onVolumeChange;
    this.onError = options.onError;
  }

  /**
   * Start VAD - requests microphone and begins listening
   */
  async start(): Promise<void> {
    if (this.isActive) {
      console.warn('[VAD] Already active');
      return;
    }

    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });

      // Create audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      });
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.analyser.smoothingTimeConstant = 0.8;

      // Create audio source from stream
      this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create script processor for audio analysis
      this.processor = this.audioContext.createScriptProcessor(2048, 1, 1);

      // Connect nodes
      this.source.connect(this.analyser);
      this.analyser.connect(this.processor);
      this.processor.connect(this.audioContext.destination);

      // Process audio data
      this.processor.onaudioprocess = (e) => {
        if (!this.isActive) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const energy = this.calculateEnergy(inputData);

        // Report volume level (normalized to 0-100)
        if (this.onVolumeChange) {
          this.onVolumeChange(Math.min(100, energy * 500));
        }

        // Detect speech based on energy
        if (energy > this.energyThreshold) {
          this.handleSpeechDetected();
        } else {
          this.handleSilenceDetected();
        }
      };

      // Setup MediaRecorder for capturing audio
      this.setupMediaRecorder();

      this.isActive = true;
      console.log('[VAD] Started - listening for speech');
    } catch (error) {
      console.error('[VAD] Failed to start:', error);
      this.onError?.('Failed to access microphone');
      throw error;
    }
  }

  /**
   * Setup MediaRecorder for capturing speech segments
   */
  private setupMediaRecorder(): void {
    if (!this.mediaStream) return;

    // Try to use webm format with opus codec for better quality
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

    this.mediaRecorder = new MediaRecorder(this.mediaStream, {
      mimeType,
      audioBitsPerSecond: 128000
    });

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.audioChunks.push(e.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      if (this.audioChunks.length > 0) {
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        console.log(`[VAD] Speech captured: ${(audioBlob.size / 1024).toFixed(2)}KB`);
        this.onSpeechEnd?.(audioBlob);
      }
      this.audioChunks = [];
    };

    console.log(`[VAD] MediaRecorder ready with ${mimeType}`);
  }

  /**
   * Stop VAD
   */
  stop(): void {
    if (!this.isActive) return;

    this.isActive = false;

    // Clear timers
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.speechTimer) {
      clearTimeout(this.speechTimer);
      this.speechTimer = null;
    }

    // Stop recording if active
    if (this.mediaRecorder?.state === 'recording') {
      this.mediaRecorder.stop();
    }

    // Disconnect nodes
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    if (this.analyser) {
      this.analyser.disconnect();
      this.analyser = null;
    }

    // Stop media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Close audio context
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.isSpeaking = false;
    this.isRecording = false;

    console.log('[VAD] Stopped');
  }

  /**
   * Calculate energy/volume of audio buffer
   */
  private calculateEnergy(buffer: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) {
      sum += buffer[i] * buffer[i];
    }
    return Math.sqrt(sum / buffer.length);
  }

  /**
   * Handle speech detection
   */
  private handleSpeechDetected(): void {
    // Clear silence timer
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    // Start speech after timeout (debounce)
    if (!this.isSpeaking && !this.speechTimer) {
      this.speechTimer = setTimeout(() => {
        if (!this.isActive) return;

        this.isSpeaking = true;
        this.speechTimer = null;

        // Start recording
        if (this.mediaRecorder && this.mediaRecorder.state !== 'recording') {
          this.audioChunks = [];
          this.mediaRecorder.start(100); // Collect data every 100ms
          this.isRecording = true;
          console.log('[VAD] Speech started - recording');
        }

        this.onSpeechStart?.();
      }, this.speechTimeout);
    }
  }

  /**
   * Handle silence detection
   */
  private handleSilenceDetected(): void {
    // Clear speech timer if not speaking yet
    if (!this.isSpeaking && this.speechTimer) {
      clearTimeout(this.speechTimer);
      this.speechTimer = null;
    }

    // End speech after silence timeout
    if (this.isSpeaking && !this.silenceTimer) {
      this.silenceTimer = setTimeout(() => {
        if (!this.isActive) return;

        this.isSpeaking = false;
        this.silenceTimer = null;

        // Stop recording
        if (this.mediaRecorder?.state === 'recording') {
          this.mediaRecorder.stop();
          this.isRecording = false;
          console.log('[VAD] Speech ended - stopping recording');
        }
      }, this.silenceTimeout);
    }
  }

  /**
   * Update VAD parameters
   */
  updateParams(params: Partial<VADOptions>): void {
    if (params.energyThreshold !== undefined) {
      this.energyThreshold = params.energyThreshold;
    }
    if (params.silenceTimeout !== undefined) {
      this.silenceTimeout = params.silenceTimeout;
    }
    if (params.speechTimeout !== undefined) {
      this.speechTimeout = params.speechTimeout;
    }
  }

  /**
   * Get current speaking state
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * Get current recording state
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Get active state
   */
  getIsActive(): boolean {
    return this.isActive;
  }
}

/**
 * Create and return a VAD instance
 */
export function createVAD(options: VADOptions = {}): VoiceActivityDetector {
  return new VoiceActivityDetector(options);
}
