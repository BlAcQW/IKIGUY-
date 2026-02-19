import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { blobToBase64, playAudioBase64 as playAudioBase64Util } from '@/lib/audio-utils';
import type {
  TranscriptionOptions,
  TranscriptionResult,
  SynthesisOptions,
  SynthesisResult,
  ChatOptions,
  ChatResult,
} from '@/types/voice-lab';


// Using API_BASE_URL from api-config;

/**
 * Voice API Service
 *
 * Centralized service layer for all Voice Lab API calls.
 * Handles authentication, request formatting, and response parsing.
 */

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get authenticated request headers
 */
async function getRequestHeaders(): Promise<Record<string, string>> {
  const authHeaders = await getAuthHeaders();
  return {
    ...authHeaders,
    'Content-Type': 'application/json',
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Transcribe audio to text (Speech-to-Text)
 *
 * @param audioBlob - Audio blob to transcribe
 * @param options - Transcription options
 * @returns Transcription result
 *
 * @example
 * const result = await transcribeAudio(audioBlob, {
 *   language: 'tw',
 *   dialect: 'asante',
 *   model: 'akan-whisper'
 * });
 */
export async function transcribeAudio(
  audioBlob: Blob,
  options: TranscriptionOptions = {}
): Promise<TranscriptionResult> {
  console.log('[VoiceAPI] 🎤 Transcribing audio...');
  console.log('[VoiceAPI] 📦 Audio blob size:', audioBlob.size, 'bytes');
  console.log('[VoiceAPI] ⚙️  Options:', options);

  try {
    const headers = await getRequestHeaders();
    const base64Audio = await blobToBase64(audioBlob);

    console.log('[VoiceAPI] 📤 Sending transcription request...');
    const startTime = Date.now();

    const response = await fetch(`${API_BASE_URL}/api/voice-lab/transcribe`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        audio_base64: base64Audio,
        language: options.language || 'tw',
        dialect: options.dialect || 'asante',
        model: options.model || 'akan-whisper',
        enhance_text: options.enhanceText !== false,
        return_timestamps: options.returnTimestamps || false,
        enable_vad: options.enableVAD || false,
        enable_streaming: options.enableStreaming || false,
      }),
    });

    const requestTime = Date.now() - startTime;
    console.log(`[VoiceAPI] ⏱️  Request completed in ${requestTime}ms`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[VoiceAPI] ❌ API error:', response.status, errorText);
      throw new Error(`Transcription failed: ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('[VoiceAPI] ✅ Transcription successful');
    console.log('[VoiceAPI] 📝 Text:', data.text);
    console.log('[VoiceAPI] 🎯 Confidence:', (data.confidence * 100).toFixed(1) + '%');

    return {
      text: data.text,
      enhancedText: data.enhanced_text,
      confidence: data.confidence,
      language: data.language,
      dialect: data.dialect,
      duration: data.duration,
      processingTime: data.processing_time,
      timestamps: data.timestamps,
    };
  } catch (error) {
    console.error('[VoiceAPI] ❌ Transcription failed:', error);
    throw error;
  }
}

/**
 * Synthesize text to speech (Text-to-Speech)
 *
 * @param text - Text to synthesize
 * @param options - Synthesis options
 * @returns Synthesis result with base64 audio
 *
 * @example
 * const result = await synthesizeSpeech('Akwaaba', {
 *   model: 'akan-mms',
 *   language: 'tw',
 *   speed: 1.0
 * });
 */
export async function synthesizeSpeech(
  text: string,
  options: SynthesisOptions = {}
): Promise<SynthesisResult> {
  console.log('[VoiceAPI] 🔊 Synthesizing speech...');
  console.log('[VoiceAPI] 📝 Text:', text);
  console.log('[VoiceAPI] ⚙️  Options:', options);

  if (!text || text.trim().length === 0) {
    throw new Error('Text cannot be empty');
  }

  try {
    const headers = await getRequestHeaders();

    console.log('[VoiceAPI] 📤 Sending synthesis request...');
    const startTime = Date.now();

    const response = await fetch(`${API_BASE_URL}/api/voice-lab/synthesize`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        text: text.trim(),
        model: options.model || 'akan-mms',
        voice_id: options.voiceId || 'default',
        language: options.language || 'tw',
        speed: options.speed || 1.0,
        pitch: options.pitch || 0.0,
        dialect: options.dialect || 'asante',
        enhance_text: options.enhanceText !== false,
        output_format: options.outputFormat || 'wav',
      }),
    });

    const requestTime = Date.now() - startTime;
    console.log(`[VoiceAPI] ⏱️  Request completed in ${requestTime}ms`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[VoiceAPI] ❌ API error:', response.status, errorText);
      throw new Error(`Synthesis failed: ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('[VoiceAPI] ✅ Synthesis successful');
    console.log('[VoiceAPI] 🎵 Audio size:', data.audio_base64?.length || 0, 'base64 chars');
    console.log('[VoiceAPI] ⏱️  Processing time:', data.processing_time?.toFixed(2) || 'N/A', 's');

    return {
      audioBase64: data.audio_base64,
      text: data.text,
      voiceId: data.voice_id,
      duration: data.duration,
      processingTime: data.processing_time,
      sampleRate: data.sample_rate,
      model: data.model,
    };
  } catch (error) {
    console.error('[VoiceAPI] ❌ Synthesis failed:', error);
    throw error;
  }
}

/**
 * Send a chat message to the LLM
 *
 * @param options - Chat options including message, model, and history
 * @returns Chat response from LLM
 *
 * @example
 * const result = await sendChatMessage({
 *   message: 'Hello',
 *   model: 'gemini-2.5-flash',
 *   mode: 'general',
 *   history: []
 * });
 */
export async function sendChatMessage(options: ChatOptions): Promise<ChatResult> {
  console.log('[VoiceAPI] 💬 Sending chat message...');
  console.log('[VoiceAPI] 📝 Message:', options.message);
  console.log('[VoiceAPI] 🤖 Model:', options.model);

  try {
    const headers = await getRequestHeaders();

    console.log('[VoiceAPI] 📤 Sending chat request...');
    const startTime = Date.now();

    const response = await fetch(`${API_BASE_URL}/api/voice-lab/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        message: options.message,
        model: options.model || 'gemini-2.5-flash',
        mode: options.mode || 'general',
        history: options.history || [],
        language: options.language || 'tw',
        dialect: options.dialect || 'asante',
      }),
    });

    const requestTime = Date.now() - startTime;
    console.log(`[VoiceAPI] ⏱️  Request completed in ${requestTime}ms`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[VoiceAPI] ❌ API error:', response.status, errorText);
      throw new Error(`Chat failed: ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('[VoiceAPI] ✅ Chat successful');
    console.log('[VoiceAPI] 💬 Response:', data.response.substring(0, 100) + '...');

    return {
      response: data.response,
      model: data.model,
      processingTime: data.processing_time,
    };
  } catch (error) {
    console.error('[VoiceAPI] ❌ Chat failed:', error);
    throw error;
  }
}

/**
 * Play audio from base64 string
 *
 * @param audioBase64 - Base64 encoded audio data
 * @returns Promise that resolves when audio finishes playing
 *
 * @example
 * await playAudioBase64(result.audioBase64);
 */
export async function playAudioBase64(audioBase64: string): Promise<void> {
  console.log('[VoiceAPI] ▶️  Playing audio...');

  if (!audioBase64) {
    console.warn('[VoiceAPI] ⚠️  No audio data to play');
    return;
  }

  return new Promise<void>((resolve, reject) => {
    try {
      // Convert base64 to Uint8Array
      const byteCharacters = atob(audioBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);

      console.log('[VoiceAPI] 📊 Audio data size:', byteArray.length, 'bytes');
      console.log('[VoiceAPI] 🔍 First bytes:',
        Array.from(byteArray.slice(0, 8))
          .map(b => '0x' + b.toString(16).padStart(2, '0'))
          .join(' ')
      );

      // Detect audio format from file signature (magic bytes)
      let mimeType = 'audio/wav'; // Default fallback

      // Check for OGG Opus (used by OpenAI TTS)
      if (byteArray[0] === 0x4f && byteArray[1] === 0x67 && byteArray[2] === 0x67 && byteArray[3] === 0x53) {
        // OGG container - likely Opus codec
        mimeType = 'audio/ogg; codecs=opus';
        console.log('[VoiceAPI] 🎵 Detected OGG Opus format');
      }
      // Check for WebM (1A 45 DF A3)
      else if (byteArray[0] === 0x1a && byteArray[1] === 0x45 && byteArray[2] === 0xdf && byteArray[3] === 0xa3) {
        mimeType = 'audio/webm; codecs=opus';
        console.log('[VoiceAPI] 🎵 Detected WebM Opus format');
      }
      // Check for MP3 (FF Fx or ID3)
      else if ((byteArray[0] === 0xff && (byteArray[1] & 0xe0) === 0xe0) ||
               (byteArray[0] === 0x49 && byteArray[1] === 0x44 && byteArray[2] === 0x33)) {
        mimeType = 'audio/mpeg';
        console.log('[VoiceAPI] 🎵 Detected MP3 format');
      }
      // Check for WAV (RIFF....WAVE)
      else if (byteArray[0] === 0x52 && byteArray[1] === 0x49 && byteArray[2] === 0x46 && byteArray[3] === 0x46) {
        mimeType = 'audio/wav';
        console.log('[VoiceAPI] 🎵 Detected WAV format');
      }
      // Check for MP4/M4A (ftyp)
      else if (byteArray[4] === 0x66 && byteArray[5] === 0x74 && byteArray[6] === 0x79 && byteArray[7] === 0x70) {
        mimeType = 'audio/mp4';
        console.log('[VoiceAPI] 🎵 Detected MP4/M4A format');
      }
      else {
        console.warn('[VoiceAPI] ⚠️  Unknown format, trying WAV fallback');
      }

      // Create blob with detected mime type
      const blob = new Blob([byteArray], { type: mimeType });
      const url = URL.createObjectURL(blob);

      console.log('[VoiceAPI] 🔗 Blob URL created:', url);
      console.log('[VoiceAPI] 📦 Blob type:', mimeType);
      console.log('[VoiceAPI] 📏 Blob size:', blob.size, 'bytes');

      // Create and configure audio element
      const audio = new Audio();
      audio.volume = 1.0;
      audio.preload = 'auto';

      // Set up error handling before setting src
      audio.onerror = (event) => {
        console.error('[VoiceAPI] ❌ Audio playback error:');
        console.error('[VoiceAPI] 📊 Error event:', event);
        console.error('[VoiceAPI] 📊 Audio error code:', audio.error?.code);
        console.error('[VoiceAPI] 📊 Audio error message:', audio.error?.message);
        console.error('[VoiceAPI] 📊 Network state:', audio.networkState);
        console.error('[VoiceAPI] 📊 Ready state:', audio.readyState);
        console.error('[VoiceAPI] 📊 MIME type:', mimeType);

        URL.revokeObjectURL(url);
        reject(new Error(`Audio playback failed: ${audio.error?.message || 'Unknown error'} (code: ${audio.error?.code})`));
      };

      // Set up success handlers
      audio.onended = () => {
        console.log('[VoiceAPI] ✅ Playback completed');
        URL.revokeObjectURL(url);
        resolve();
      };

      audio.onloadedmetadata = () => {
        console.log('[VoiceAPI] 📊 Audio metadata loaded');
        console.log('[VoiceAPI] ⏱️  Duration:', audio.duration, 'seconds');
        console.log('[VoiceAPI] 📊 Ready state:', audio.readyState);
      };

      // Set source and play
      audio.src = url;
      console.log('[VoiceAPI] 🎶 Starting playback...');

      audio.play()
        .then(() => {
          console.log('[VoiceAPI] ▶️  Playback started successfully');
        })
        .catch((playError) => {
          console.error('[VoiceAPI] ❌ Play() promise rejected:', playError);
          URL.revokeObjectURL(url);
          reject(new Error(`Failed to start playback: ${playError.message}`));
        });

    } catch (error) {
      console.error('[VoiceAPI] ❌ Play setup failed:', error);
      reject(error instanceof Error ? error : new Error('Audio playback setup failed'));
    }
  });
}