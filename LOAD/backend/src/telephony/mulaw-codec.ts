/**
 * G.711 mu-law codec for Twilio Media Streams audio conversion.
 *
 * Twilio Media Streams send/receive audio as base64-encoded mu-law (G.711)
 * at 8kHz mono. The voice pipeline works with PCM 16-bit LE at 16kHz.
 * These functions handle the conversion in both directions.
 *
 * Lookup tables are built at module load time per ITU G.711 specification.
 */

import { upsample, downsample } from './audio-resample.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MULAW_BIAS = 0x84; // 132
const MULAW_CLIP = 32635;
const MULAW_MAX = 0xFF;

/** Twilio Media Streams sample rate (mu-law). */
const TWILIO_SAMPLE_RATE = 8000;

/** Voice pipeline STT input sample rate. */
const PIPELINE_SAMPLE_RATE = 16000;

/** TTS output sample rate (OpenAI TTS default). */
const TTS_SAMPLE_RATE = 24000;

// ---------------------------------------------------------------------------
// Mu-law decode table (256 entries: mulaw byte -> PCM 16-bit signed)
// ---------------------------------------------------------------------------

const MULAW_DECODE_TABLE: Int16Array = buildDecodeTable();

function buildDecodeTable(): Int16Array {
  const table = new Int16Array(256);
  for (let i = 0; i < 256; i++) {
    // Complement and extract sign/exponent/mantissa
    const mu = ~i & 0xFF;
    const sign = mu & 0x80;
    const exponent = (mu >> 4) & 0x07;
    const mantissa = mu & 0x0F;

    // Reconstruct linear value
    let sample = ((mantissa << 3) + MULAW_BIAS) << exponent;
    sample -= MULAW_BIAS;

    table[i] = sign !== 0 ? -sample : sample;
  }
  return table;
}

// ---------------------------------------------------------------------------
// Mu-law encode table (65536 entries: PCM 16-bit unsigned index -> mulaw byte)
// ---------------------------------------------------------------------------
// For fast encoding, we precompute a lookup from each possible 16-bit sample.

const MULAW_ENCODE_TABLE: Uint8Array = buildEncodeTable();

function buildEncodeTable(): Uint8Array {
  const table = new Uint8Array(65536);
  for (let i = 0; i < 65536; i++) {
    // Convert unsigned table index to signed 16-bit
    const sample = i >= 32768 ? i - 65536 : i;
    table[i] = encodeSample(sample);
  }
  return table;
}

/** Encode a single PCM 16-bit signed sample to mu-law byte. */
function encodeSample(sample: number): number {
  const sign = sample < 0 ? 0x80 : 0x00;
  let magnitude = sample < 0 ? -sample : sample;

  if (magnitude > MULAW_CLIP) magnitude = MULAW_CLIP;
  magnitude += MULAW_BIAS;

  let exponent = 7;
  const exponentMask = 0x4000;
  for (let i = 0; i < 7; i++) {
    if (magnitude & (exponentMask >> i)) break;
    exponent--;
  }

  const mantissa = (magnitude >> (exponent + 3)) & 0x0F;
  const mulawByte = ~(sign | (exponent << 4) | mantissa) & MULAW_MAX;
  return mulawByte;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Decode a mu-law encoded buffer to PCM 16-bit LE.
 * Each input byte produces one 16-bit sample (2 bytes output).
 */
export function mulawToPcm(mulaw: Buffer): Buffer {
  const pcm = Buffer.alloc(mulaw.length * 2);
  for (let i = 0; i < mulaw.length; i++) {
    pcm.writeInt16LE(MULAW_DECODE_TABLE[mulaw[i]], i * 2);
  }
  return pcm;
}

/**
 * Encode PCM 16-bit LE buffer to mu-law.
 * Each 16-bit sample (2 bytes) produces one mu-law byte.
 */
export function pcmToMulaw(pcm: Buffer): Buffer {
  const sampleCount = Math.floor(pcm.length / 2);
  const mulaw = Buffer.alloc(sampleCount);
  for (let i = 0; i < sampleCount; i++) {
    const sample = pcm.readInt16LE(i * 2);
    // Convert signed to unsigned index for the lookup table
    const index = sample < 0 ? sample + 65536 : sample;
    mulaw[i] = MULAW_ENCODE_TABLE[index];
  }
  return mulaw;
}

/**
 * Decode Twilio Media Streams audio for the voice pipeline.
 * mu-law 8kHz -> PCM 16-bit LE 16kHz
 */
export function decodeTwilioAudio(mulaw: Buffer): Buffer {
  const pcm8k = mulawToPcm(mulaw);
  return upsample(pcm8k, TWILIO_SAMPLE_RATE, PIPELINE_SAMPLE_RATE);
}

/**
 * Encode voice pipeline TTS output for Twilio Media Streams.
 * PCM 16-bit LE 24kHz -> mu-law 8kHz
 */
export function encodeTwilioAudio(pcm24k: Buffer): Buffer {
  const pcm8k = downsample(pcm24k, TTS_SAMPLE_RATE, TWILIO_SAMPLE_RATE);
  return pcmToMulaw(pcm8k);
}
