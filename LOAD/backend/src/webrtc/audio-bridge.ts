/**
 * Bridges WebRTC Opus RTP audio with the voice pipeline's PCM format.
 *
 * Handles Opus encode/decode via @discordjs/opus and resampling between
 * WebRTC's 48kHz and the pipeline's 16kHz (STT) / 24kHz (TTS) rates.
 */

import OpusEncoder from '@discordjs/opus';
import { downsample, upsample } from '../telephony/audio-resample.js';

/** WebRTC Opus audio runs at 48kHz. */
const WEBRTC_SAMPLE_RATE = 48_000;

/** STT / VAD expect 16kHz PCM. */
const STT_SAMPLE_RATE = 16_000;

/** OpenAI TTS outputs 24kHz PCM. */
const TTS_SAMPLE_RATE = 24_000;

/** Opus frame duration in ms (standard for WebRTC). */
const OPUS_FRAME_MS = 20;

/** Number of samples per Opus frame at 48kHz mono (20ms). */
const OPUS_FRAME_SAMPLES = (WEBRTC_SAMPLE_RATE * OPUS_FRAME_MS) / 1000; // 960

export class AudioBridge {
  private readonly decoder: OpusEncoder.OpusEncoder;
  private readonly encoder: OpusEncoder.OpusEncoder;

  constructor() {
    // 48kHz, 1 channel (mono)
    this.decoder = new OpusEncoder.OpusEncoder(WEBRTC_SAMPLE_RATE, 1);
    this.encoder = new OpusEncoder.OpusEncoder(WEBRTC_SAMPLE_RATE, 1);
  }

  /**
   * Decode an incoming Opus RTP payload to raw PCM 16-bit LE at 48kHz.
   */
  decodeOpusToPcm(opusPayload: Buffer): Buffer {
    return this.decoder.decode(opusPayload);
  }

  /**
   * Encode raw PCM 16-bit LE at 48kHz to an Opus frame.
   * The input must be exactly one frame (960 samples = 1920 bytes for mono 48kHz 20ms).
   */
  encodePcmToOpus(pcmFrame: Buffer): Buffer {
    return this.encoder.encode(pcmFrame);
  }

  /**
   * Downsample 48kHz PCM to 16kHz PCM for VAD and STT input.
   */
  downsampleForStt(pcm48k: Buffer): Buffer {
    return downsample(pcm48k, WEBRTC_SAMPLE_RATE, STT_SAMPLE_RATE);
  }

  /**
   * Upsample 24kHz TTS PCM to 48kHz for Opus encoding.
   */
  upsampleFromTts(pcm24k: Buffer): Buffer {
    return upsample(pcm24k, TTS_SAMPLE_RATE, WEBRTC_SAMPLE_RATE);
  }

  /**
   * Split PCM 48kHz buffer into 20ms Opus frames, encode each.
   * Returns an array of Opus-encoded buffers ready for RTP.
   */
  encodeForRtp(pcm48k: Buffer): Buffer[] {
    const frameBytes = OPUS_FRAME_SAMPLES * 2; // 16-bit = 2 bytes per sample
    const frames: Buffer[] = [];

    for (let offset = 0; offset + frameBytes <= pcm48k.length; offset += frameBytes) {
      const frame = pcm48k.subarray(offset, offset + frameBytes);
      frames.push(this.encodePcmToOpus(frame));
    }

    return frames;
  }
}

/**
 * Construct a minimal WAV file from raw PCM 16-bit LE audio data.
 * Whisper STT accepts WAV format for better reliability than raw PCM.
 */
export function wrapPcmAsWav(pcm: Buffer, sampleRate: number): Buffer {
  const headerSize = 44;
  const dataSize = pcm.length;
  const fileSize = headerSize + dataSize;
  const header = Buffer.alloc(headerSize);

  // RIFF header
  header.write('RIFF', 0);
  header.writeUInt32LE(fileSize - 8, 4);
  header.write('WAVE', 8);

  // fmt sub-chunk
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);        // Sub-chunk size
  header.writeUInt16LE(1, 20);         // PCM format
  header.writeUInt16LE(1, 22);         // Mono
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(sampleRate * 2, 28); // Byte rate (sampleRate * channels * bitsPerSample/8)
  header.writeUInt16LE(2, 32);         // Block align (channels * bitsPerSample/8)
  header.writeUInt16LE(16, 34);        // Bits per sample

  // data sub-chunk
  header.write('data', 36);
  header.writeUInt32LE(dataSize, 40);

  return Buffer.concat([header, pcm]);
}

export { WEBRTC_SAMPLE_RATE, STT_SAMPLE_RATE, TTS_SAMPLE_RATE, OPUS_FRAME_MS, OPUS_FRAME_SAMPLES };
