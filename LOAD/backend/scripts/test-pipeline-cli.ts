#!/usr/bin/env tsx
/**
 * Manual pipeline test CLI.
 *
 * Run: npx tsx scripts/test-pipeline-cli.ts [options]
 *
 * Options:
 *   --stt <provider>    STT provider: openai | deepgram (default: deepgram)
 *   --llm <provider>    LLM provider: openai | mock (default: mock)
 *   --tts <provider>    TTS provider: openai | elevenlabs | cartesia | deepgram (default: deepgram)
 *   --input <file>      Input WAV file (default: test fixture)
 *   --output <file>     Save output PCM to file
 *   --mock-llm          Use mock LLM (alias for --llm mock)
 *   --text <text>       Custom text for mock LLM response
 *
 * Examples:
 *   npx tsx scripts/test-pipeline-cli.ts --stt deepgram --tts elevenlabs --mock-llm
 *   npx tsx scripts/test-pipeline-cli.ts --stt openai --llm openai --tts openai
 *   npx tsx scripts/test-pipeline-cli.ts --input my-audio.wav --output response.pcm
 */

import { config as dotenvConfig } from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { readFileSync, writeFileSync, existsSync } from 'fs';

const __dirname_ = typeof __dirname !== 'undefined'
  ? __dirname
  : dirname(fileURLToPath(import.meta.url));

dotenvConfig({ path: resolve(__dirname_, '..', '.env') });

// Dynamic imports to avoid loading all providers at module level
import type { STTProvider } from '@/providers/stt/types.js';
import type { TTSProvider } from '@/providers/tts/types.js';
import type { LLMProvider, Message, LLMChatResult } from '@/providers/llm/types.js';
import type { PipelineConfig } from '@/voice-pipeline/pipeline.js';

// ---------------------------------------------------------------------------
// Mock LLM
// ---------------------------------------------------------------------------

class MockLLMProvider implements LLMProvider {
  readonly name = 'mock-llm';
  private response: string;

  constructor(response: string) {
    this.response = response;
  }

  async chat(_messages: Message[]): Promise<string | LLMChatResult> {
    return this.response;
  }

  async *chatStream(_messages: Message[]): AsyncIterable<string> {
    yield this.response;
  }
}

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

function parseArgs(): {
  sttProvider: string;
  llmProvider: string;
  ttsProvider: string;
  inputFile?: string;
  outputFile?: string;
  mockText: string;
} {
  const args = process.argv.slice(2);
  const opts = {
    sttProvider: 'deepgram',
    llmProvider: 'mock',
    ttsProvider: 'deepgram',
    inputFile: undefined as string | undefined,
    outputFile: undefined as string | undefined,
    mockText: 'I understand your message. How can I help you further?',
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--stt':
        opts.sttProvider = args[++i];
        break;
      case '--llm':
        opts.llmProvider = args[++i];
        break;
      case '--tts':
        opts.ttsProvider = args[++i];
        break;
      case '--input':
        opts.inputFile = args[++i];
        break;
      case '--output':
        opts.outputFile = args[++i];
        break;
      case '--mock-llm':
        opts.llmProvider = 'mock';
        break;
      case '--text':
        opts.mockText = args[++i];
        break;
      case '--help':
      case '-h':
        console.log(`
Usage: npx tsx scripts/test-pipeline-cli.ts [options]

Options:
  --stt <provider>    STT: openai | deepgram (default: deepgram)
  --llm <provider>    LLM: openai | mock (default: mock)
  --tts <provider>    TTS: openai | elevenlabs | cartesia | deepgram (default: deepgram)
  --input <file>      Input WAV file (default: test fixture)
  --output <file>     Save output PCM to file
  --mock-llm          Use mock LLM
  --text <text>       Custom mock LLM response text
`);
        process.exit(0);
    }
  }

  return opts;
}

// ---------------------------------------------------------------------------
// Provider creation
// ---------------------------------------------------------------------------

function requireEnv(name: string): string {
  const val = process.env[name];
  if (!val || val.startsWith('sk-your-')) {
    console.error(`ERROR: ${name} is not set in .env`);
    process.exit(1);
  }
  return val;
}

async function createSTT(name: string): Promise<STTProvider> {
  switch (name) {
    case 'deepgram': {
      const { DeepgramSTTProvider } = await import('@/providers/stt/deepgram.js');
      return new DeepgramSTTProvider(requireEnv('DEEPGRAM_API_KEY'));
    }
    case 'openai': {
      const { OpenAISTTProvider } = await import('@/providers/stt/openai.js');
      return new OpenAISTTProvider(requireEnv('OPENAI_API_KEY'));
    }
    default:
      console.error(`Unknown STT provider: ${name}`);
      process.exit(1);
  }
}

async function createTTS(name: string): Promise<TTSProvider> {
  switch (name) {
    case 'deepgram': {
      const { DeepgramTTSProvider } = await import('@/providers/tts/deepgram.js');
      return new DeepgramTTSProvider(requireEnv('DEEPGRAM_API_KEY'));
    }
    case 'openai': {
      const { OpenAITTSProvider } = await import('@/providers/tts/openai.js');
      return new OpenAITTSProvider(requireEnv('OPENAI_API_KEY'));
    }
    case 'elevenlabs': {
      const { ElevenLabsTTSProvider } = await import('@/providers/tts/elevenlabs.js');
      return new ElevenLabsTTSProvider(requireEnv('ELEVENLABS_API_KEY'));
    }
    case 'cartesia': {
      const { CartesiaTTSProvider } = await import('@/providers/tts/cartesia.js');
      return new CartesiaTTSProvider(requireEnv('CARTESIA_API_KEY'));
    }
    default:
      console.error(`Unknown TTS provider: ${name}`);
      process.exit(1);
  }
}

async function createLLM(name: string, mockText: string): Promise<LLMProvider> {
  switch (name) {
    case 'mock':
      return new MockLLMProvider(mockText);
    case 'openai': {
      const { OpenAILLMProvider } = await import('@/providers/llm/openai.js');
      return new OpenAILLMProvider(requireEnv('OPENAI_API_KEY'));
    }
    default:
      console.error(`Unknown LLM provider: ${name}`);
      process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const opts = parseArgs();

  console.log('\n=== LOAD Pipeline CLI Test ===\n');
  console.log(`  STT: ${opts.sttProvider}`);
  console.log(`  LLM: ${opts.llmProvider}${opts.llmProvider === 'mock' ? ` ("${opts.mockText.substring(0, 40)}...")` : ''}`);
  console.log(`  TTS: ${opts.ttsProvider}`);
  console.log('');

  // Load input audio
  let audioInput: Buffer;
  if (opts.inputFile) {
    if (!existsSync(opts.inputFile)) {
      console.error(`Input file not found: ${opts.inputFile}`);
      process.exit(1);
    }
    audioInput = readFileSync(opts.inputFile);
    console.log(`  Input: ${opts.inputFile} (${audioInput.length} bytes)`);
  } else {
    const fixturePath = resolve(__dirname_, '..', 'tests', 'integration', 'fixtures', 'hello-16k-mono.wav');
    if (!existsSync(fixturePath)) {
      console.error('Test fixture not found. Run: npx tsx tests/integration/fixtures/generate-audio.ts');
      process.exit(1);
    }
    audioInput = readFileSync(fixturePath);
    console.log(`  Input: test fixture (${audioInput.length} bytes, 2s tone)`);
  }

  // Create providers
  console.log('\n  Creating providers...');
  const stt = await createSTT(opts.sttProvider);
  const llm = await createLLM(opts.llmProvider, opts.mockText);
  const tts = await createTTS(opts.ttsProvider);
  console.log('  Providers ready.\n');

  // Create session
  const { createSession, endSession } = await import('@/voice-pipeline/session.js');
  const session = await createSession({
    callId: 'cli-test',
    assistantId: 'cli-test-assistant',
    organizationId: 'cli-test-org',
    systemPrompt: 'You are a helpful assistant. Keep responses to one short sentence.',
  });

  const pipelineConfig: PipelineConfig = { stt, llm, tts };

  try {
    // Run pipeline
    console.log('  Running pipeline...\n');
    const start = Date.now();

    const { processPipelineTurn } = await import('@/voice-pipeline/pipeline.js');
    const result = await processPipelineTurn(session.id, audioInput, pipelineConfig, {
      llmModel: opts.llmProvider === 'openai' ? 'gpt-4o-mini' : undefined,
      llmMaxTokens: 200,
      format: 'wav',
    });

    const elapsed = Date.now() - start;

    // Print results
    console.log('  ┌─────────────────────────────────────────────────┐');
    console.log('  │                 Pipeline Results                 │');
    console.log('  ├─────────────────────────────────────────────────┤');
    console.log(`  │ STT Output:    "${result.userText.substring(0, 40)}"`);
    console.log(`  │ LLM Response:  "${result.assistantText.substring(0, 40)}"`);
    console.log(`  │ TTS Audio:     ${result.audioBuffer.length} bytes`);
    console.log(`  │ Duration:      ${(result.audioBuffer.length / 2 / 16000 * 1000).toFixed(0)}ms @ 16kHz`);
    console.log(`  │ Tool calls:    ${result.toolCallsExecuted.length}`);
    console.log(`  │ Total time:    ${elapsed}ms`);
    console.log('  └─────────────────────────────────────────────────┘');

    // Save output if requested
    if (opts.outputFile) {
      writeFileSync(opts.outputFile, result.audioBuffer);
      console.log(`\n  Output saved: ${opts.outputFile} (${result.audioBuffer.length} bytes)`);
    }

    console.log('\n  Pipeline test PASSED.\n');
  } catch (error) {
    console.error('\n  Pipeline test FAILED:', error);
    process.exit(1);
  } finally {
    await endSession(session.id);
  }
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
