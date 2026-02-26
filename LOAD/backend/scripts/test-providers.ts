#!/usr/bin/env tsx
/**
 * Provider smoke test — quickly tests every configured provider.
 *
 * Run: npx tsx scripts/test-providers.ts
 *
 * Checks each provider API key, attempts a minimal API call,
 * and prints a PASS/FAIL summary table.
 */

import { config as dotenvConfig } from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { readFileSync } from 'fs';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

dotenvConfig({ path: resolve(__dirname_, '..', '.env') });

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ProviderTest {
  name: string;
  type: 'STT' | 'TTS' | 'LLM';
  envVar: string;
  test: (apiKey: string) => Promise<string>;
}

interface TestResult {
  name: string;
  type: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  detail: string;
  durationMs: number;
}

// ---------------------------------------------------------------------------
// Placeholder detection
// ---------------------------------------------------------------------------

const PLACEHOLDER_PATTERNS = [
  /^sk-your-/,
  /^your[-_]/i,
  /^xxx/i,
  /^placeholder/i,
  /^CHANGE[-_]ME/i,
  /^TODO/i,
];

function isPlaceholder(value: string): boolean {
  return PLACEHOLDER_PATTERNS.some((p) => p.test(value));
}

// ---------------------------------------------------------------------------
// Audio fixtures
// ---------------------------------------------------------------------------

function loadTestAudio(): Buffer {
  const wavPath = resolve(__dirname_, '..', 'tests', 'integration', 'fixtures', 'hello-16k-mono.wav');
  try {
    return readFileSync(wavPath);
  } catch {
    // Generate a minimal WAV in-memory if fixture doesn't exist
    console.log('  (generating test audio in-memory)');
    const sampleRate = 16_000;
    const duration = 1;
    const samples = sampleRate * duration;
    const pcm = Buffer.alloc(samples * 2);
    for (let i = 0; i < samples; i++) {
      pcm.writeInt16LE(Math.round(8000 * Math.sin(2 * Math.PI * 440 * (i / sampleRate))), i * 2);
    }
    // WAV header
    const header = Buffer.alloc(44);
    header.write('RIFF', 0);
    header.writeUInt32LE(36 + pcm.length, 4);
    header.write('WAVE', 8);
    header.write('fmt ', 12);
    header.writeUInt32LE(16, 16);
    header.writeUInt16LE(1, 20);
    header.writeUInt16LE(1, 22);
    header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(sampleRate * 2, 28);
    header.writeUInt16LE(2, 32);
    header.writeUInt16LE(16, 34);
    header.write('data', 36);
    header.writeUInt32LE(pcm.length, 40);
    return Buffer.concat([header, pcm]);
  }
}

// ---------------------------------------------------------------------------
// Provider test definitions
// ---------------------------------------------------------------------------

const testAudio = loadTestAudio();

const providers: ProviderTest[] = [
  {
    name: 'Deepgram Nova',
    type: 'STT',
    envVar: 'DEEPGRAM_API_KEY',
    test: async (apiKey) => {
      const res = await fetch('https://api.deepgram.com/v1/listen?model=nova-2&language=en', {
        method: 'POST',
        headers: { Authorization: `Token ${apiKey}`, 'Content-Type': 'audio/wav' },
        body: testAudio.buffer.slice(testAudio.byteOffset, testAudio.byteOffset + testAudio.byteLength) as BodyInit,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json() as { results?: { channels?: Array<{ alternatives?: Array<{ transcript?: string }> }> } };
      const transcript = data.results?.channels?.[0]?.alternatives?.[0]?.transcript ?? '';
      return `Transcript: "${transcript.substring(0, 60)}"`;
    },
  },
  {
    name: 'OpenAI Whisper',
    type: 'STT',
    envVar: 'OPENAI_API_KEY',
    test: async (apiKey) => {
      const { default: OpenAI, toFile } = await import('openai');
      const client = new OpenAI({ apiKey });
      const file = await toFile(testAudio, 'audio.wav', { type: 'audio/wav' });
      const result = await client.audio.transcriptions.create({ model: 'whisper-1', file, language: 'en' });
      return `Transcript: "${result.text.substring(0, 60)}"`;
    },
  },
  {
    name: 'OpenAI GPT',
    type: 'LLM',
    envVar: 'OPENAI_API_KEY',
    test: async (apiKey) => {
      const { default: OpenAI } = await import('openai');
      const client = new OpenAI({ apiKey });
      const result = await client.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: 'Say "hello" and nothing else.' }],
        max_tokens: 10,
      });
      const text = result.choices[0]?.message?.content ?? '';
      return `Response: "${text.substring(0, 60)}"`;
    },
  },
  {
    name: 'ElevenLabs',
    type: 'TTS',
    envVar: 'ELEVENLABS_API_KEY',
    test: async (apiKey) => {
      const res = await fetch('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM?output_format=pcm_16000', {
        method: 'POST',
        headers: { 'xi-api-key': apiKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'Hello.', model_id: 'eleven_turbo_v2_5' }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const buf = await res.arrayBuffer();
      return `Audio: ${buf.byteLength} bytes (${((buf.byteLength / 2) / 16000 * 1000).toFixed(0)}ms @ 16kHz)`;
    },
  },
  {
    name: 'Cartesia Sonic',
    type: 'TTS',
    envVar: 'CARTESIA_API_KEY',
    test: async (apiKey) => {
      const res = await fetch('https://api.cartesia.ai/tts/bytes', {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Cartesia-Version': '2024-06-10',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: 'sonic-2',
          transcript: 'Hello.',
          voice: { mode: 'id', id: 'a0e99841-438c-4a64-b679-ae501e7d6091' },
          output_format: { container: 'raw', encoding: 'pcm_s16le', sample_rate: 16000 },
          language: 'en',
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const buf = await res.arrayBuffer();
      return `Audio: ${buf.byteLength} bytes (${((buf.byteLength / 2) / 16000 * 1000).toFixed(0)}ms @ 16kHz)`;
    },
  },
  {
    name: 'Deepgram Aura',
    type: 'TTS',
    envVar: 'DEEPGRAM_API_KEY',
    test: async (apiKey) => {
      const res = await fetch('https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=linear16&sample_rate=16000', {
        method: 'POST',
        headers: { Authorization: `Token ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'Hello.' }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const buf = await res.arrayBuffer();
      return `Audio: ${buf.byteLength} bytes (${((buf.byteLength / 2) / 16000 * 1000).toFixed(0)}ms @ 16kHz)`;
    },
  },
  {
    name: 'OpenAI TTS',
    type: 'TTS',
    envVar: 'OPENAI_API_KEY',
    test: async (apiKey) => {
      const { default: OpenAI } = await import('openai');
      const client = new OpenAI({ apiKey });
      const res = await client.audio.speech.create({
        model: 'tts-1',
        voice: 'alloy',
        input: 'Hello.',
        response_format: 'pcm',
      });
      const buf = await res.arrayBuffer();
      return `Audio: ${buf.byteLength} bytes (${((buf.byteLength / 2) / 24000 * 1000).toFixed(0)}ms @ 24kHz)`;
    },
  },
];

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  console.log('\n=== LOAD Provider Smoke Test ===\n');

  const results: TestResult[] = [];

  for (const provider of providers) {
    const keyValue = process.env[provider.envVar];
    const hasKey = keyValue && keyValue.trim() !== '' && !isPlaceholder(keyValue);

    if (!hasKey) {
      results.push({
        name: provider.name,
        type: provider.type,
        status: 'SKIP',
        detail: `${provider.envVar} not configured`,
        durationMs: 0,
      });
      continue;
    }

    const start = Date.now();
    try {
      const detail = await provider.test(keyValue);
      results.push({
        name: provider.name,
        type: provider.type,
        status: 'PASS',
        detail,
        durationMs: Date.now() - start,
      });
    } catch (error) {
      results.push({
        name: provider.name,
        type: provider.type,
        status: 'FAIL',
        detail: error instanceof Error ? error.message.substring(0, 80) : String(error),
        durationMs: Date.now() - start,
      });
    }
  }

  // Print summary table
  console.log('');
  console.log('┌────────────────────┬──────┬────────┬─────────┬──────────────────────────────────────────────────┐');
  console.log('│ Provider           │ Type │ Status │ Time    │ Detail                                           │');
  console.log('├────────────────────┼──────┼────────┼─────────┼──────────────────────────────────────────────────┤');

  for (const r of results) {
    const icon = r.status === 'PASS' ? '\x1b[32mPASS\x1b[0m' : r.status === 'FAIL' ? '\x1b[31mFAIL\x1b[0m' : '\x1b[33mSKIP\x1b[0m';
    const name = r.name.padEnd(18);
    const type = r.type.padEnd(4);
    const time = r.durationMs > 0 ? `${r.durationMs}ms`.padEnd(7) : '—'.padEnd(7);
    const detail = r.detail.substring(0, 48).padEnd(48);
    console.log(`│ ${name} │ ${type} │ ${icon}   │ ${time} │ ${detail} │`);
  }

  console.log('└────────────────────┴──────┴────────┴─────────┴──────────────────────────────────────────────────┘');

  const passed = results.filter((r) => r.status === 'PASS').length;
  const failed = results.filter((r) => r.status === 'FAIL').length;
  const skipped = results.filter((r) => r.status === 'SKIP').length;

  console.log(`\n  ${passed} passed, ${failed} failed, ${skipped} skipped (${results.length} total)\n`);

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
