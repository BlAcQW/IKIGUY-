/**
 * Voice Activity Detection (VAD) for browser
 * Detects speech in audio streams using energy-based detection
 */

export class VoiceActivityDetector {
  private audioContext: AudioContext;
  private analyser: AnalyserNode;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  
  // VAD parameters
  private energyThreshold: number;
  private silenceTimeout: number;
  private speechTimeout: number;
  
  // State
  private isSpeaking = false;
  private silenceTimer: NodeJS.Timeout | null = null;
  private speechTimer: NodeJS.Timeout | null = null;
  private isActive = false;
  
  // Callbacks
  private onSpeechStart?: () => void;
  private onSpeechEnd?: () => void;
  private onVolumeChange?: (volume: number) => void;
  
  constructor(options: {
    energyThreshold?: number;
    silenceTimeout?: number;
    speechTimeout?: number;
    onSpeechStart?: () => void;
    onSpeechEnd?: () => void;
    onVolumeChange?: (volume: number) => void;
  } = {}) {
    this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    this.analyser.smoothingTimeConstant = 0.8;
    
    // Configure thresholds
    this.energyThreshold = options.energyThreshold || 0.02; // Energy threshold for speech
    this.silenceTimeout = options.silenceTimeout || 1500; // ms of silence before ending speech
    this.speechTimeout = options.speechTimeout || 500; // ms of speech before starting
    
    // Set callbacks
    this.onSpeechStart = options.onSpeechStart;
    this.onSpeechEnd = options.onSpeechEnd;
    this.onVolumeChange = options.onVolumeChange;
  }
  
  /**
   * Start VAD on a media stream
   */
  async start(stream: MediaStream): Promise<void> {
    if (this.isActive) {
      console.warn('VAD already active');
      return;
    }
    
    try {
      // Create audio source from stream
      this.source = this.audioContext.createMediaStreamSource(stream);
      
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
        
        // Report volume level
        if (this.onVolumeChange) {
          this.onVolumeChange(energy);
        }
        
        // Detect speech based on energy
        if (energy > this.energyThreshold) {
          this.handleSpeechDetected();
        } else {
          this.handleSilenceDetected();
        }
      };
      
      this.isActive = true;
      console.log('VAD started');
    } catch (error) {
      console.error('Failed to start VAD:', error);
      throw error;
    }
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
    
    // Disconnect nodes
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    
    // End speech if active
    if (this.isSpeaking) {
      this.isSpeaking = false;
      if (this.onSpeechEnd) {
        this.onSpeechEnd();
      }
    }
    
    console.log('VAD stopped');
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
    
    // Start speech after timeout
    if (!this.isSpeaking && !this.speechTimer) {
      this.speechTimer = setTimeout(() => {
        if (!this.isActive) return;
        
        this.isSpeaking = true;
        this.speechTimer = null;
        console.log('Speech started');
        
        if (this.onSpeechStart) {
          this.onSpeechStart();
        }
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
        console.log('Speech ended');
        
        if (this.onSpeechEnd) {
          this.onSpeechEnd();
        }
      }, this.silenceTimeout);
    }
  }
  
  /**
   * Update VAD parameters
   */
  updateParams(params: {
    energyThreshold?: number;
    silenceTimeout?: number;
    speechTimeout?: number;
  }): void {
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
   * Cleanup resources
   */
  destroy(): void {
    this.stop();
    if (this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
  }
}