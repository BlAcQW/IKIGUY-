#!/usr/bin/env tsx
/**
 * Generate WAV test fixtures for integration tests.
 *
 * Produces:
 *   - hello-16k-mono.wav  — 2s 440Hz sine tone (simulates speech-like audio)
 *   - silence-16k-mono.wav — 2s silence
 *
 * WAV format: 16-bit PCM, 16kHz, mono.
 * Uses only Node.js built-ins (no external dependencies).
 *
 * Run: npx tsx tests/integration/fixtures/generate-audio.ts
 */

import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

const SAMPLE_RATE = 16_000;
const BITS_PER_SAMPLE = 16;
const NUM_CHANNELS = 1;
const DURATION_SECONDS = 2;
const TOTAL_SAMPLES = SAMPLE_RATE * DURATION_SECONDS;

/**
 * Write a WAV file header for 16-bit PCM mono audio.
 */
function createWavBuffer(pcmData: Buffer): Buffer {
  const header = Buffer.alloc(44);
  const dataSize = pcmData.length;
  const fileSize = 36 + dataSize;

  // RIFF header
  header.write('RIFF', 0);
  header.writeUInt32LE(fileSize, 4);
  header.write('WAVE', 8);

  // fmt sub-chunk
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);             // Sub-chunk size (16 for PCM)
  header.writeUInt16LE(1, 20);              // Audio format (1 = PCM)
  header.writeUInt16LE(NUM_CHANNELS, 22);   // Number of channels
  header.writeUInt32LE(SAMPLE_RATE, 24);    // Sample rate
  header.writeUInt32LE(SAMPLE_RATE * NUM_CHANNELS * (BITS_PER_SAMPLE / 8), 28); // Byte rate
  header.writeUInt16LE(NUM_CHANNELS * (BITS_PER_SAMPLE / 8), 32); // Block align
  header.writeUInt16LE(BITS_PER_SAMPLE, 34); // Bits per sample

  // data sub-chunk
  header.write('data', 36);
  header.writeUInt32LE(dataSize, 40);

  return Buffer.concat([header, pcmData]);
}

/**
 * Generate a 440Hz sine wave tone (2 seconds).
 */
function generateTone(): Buffer {
  const pcm = Buffer.alloc(TOTAL_SAMPLES * 2); // 2 bytes per sample
  const frequency = 440;
  const amplitude = 16_000; // ~50% of max int16

  for (let i = 0; i < TOTAL_SAMPLES; i++) {
    const t = i / SAMPLE_RATE;
    const sample = Math.round(amplitude * Math.sin(2 * Math.PI * frequency * t));
    pcm.writeInt16LE(sample, i * 2);
  }

  return createWavBuffer(pcm);
}

/**
 * Generate 2 seconds of silence.
 */
function generateSilence(): Buffer {
  const pcm = Buffer.alloc(TOTAL_SAMPLES * 2); // All zeros = silence
  return createWavBuffer(pcm);
}

// --- Main ---

const helloPath = join(__dirname_, 'hello-16k-mono.wav');
const silencePath = join(__dirname_, 'silence-16k-mono.wav');

writeFileSync(helloPath, generateTone());
console.log(`Generated: ${helloPath} (${DURATION_SECONDS}s, 440Hz tone, 16kHz mono)`);

writeFileSync(silencePath, generateSilence());
console.log(`Generated: ${silencePath} (${DURATION_SECONDS}s, silence, 16kHz mono)`);

// Also export the generators for programmatic use in tests
export { generateTone, generateSilence, createWavBuffer, SAMPLE_RATE, TOTAL_SAMPLES };
