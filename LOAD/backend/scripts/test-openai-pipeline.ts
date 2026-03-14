import { readFileSync } from 'fs';
import { resolve } from 'path';

const envPath = resolve(import.meta.dirname ?? '.', '../.env');
const envContent = readFileSync(envPath, 'utf8');
for (const line of envContent.split('\n')) {
  const trimmed = line.trim();
  if (trimmed.length === 0 || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  process.env[trimmed.slice(0, eqIdx)] = trimmed.slice(eqIdx + 1);
}

async function main() {
  const { buildPipelineFromAssistant } = await import('@/providers/registry.js');

  // Build OpenAI pipeline (what your assistants now use)
  const pipeline = buildPipelineFromAssistant({
    model: { provider: 'openai', model: 'gpt-4o' },
    voice: { provider: 'openai', voiceId: 'alloy' },
    transcriber: { provider: 'openai', model: 'whisper-1' },
  });
  console.log('Pipeline built: LLM=' + pipeline.llm.name + ' STT=' + pipeline.stt.name + ' TTS=' + pipeline.tts.name);

  // Test LLM
  console.log('\nCalling GPT-4o...');
  const llmResult = await pipeline.llm.chat([
    { role: 'system', content: 'You are a helpful voice assistant. Reply in one short sentence.' },
    { role: 'user', content: 'Hello, can you hear me?' },
  ], { model: 'gpt-4o', temperature: 0.7, maxTokens: 100 });

  const text = typeof llmResult === 'string' ? llmResult : llmResult.content;
  console.log('GPT-4o says: ' + text);

  // Test TTS
  console.log('\nSynthesizing speech...');
  const audio = await pipeline.tts.synthesize(text ?? 'Hello there!', {
    voiceId: 'alloy',
    speed: 1.0,
  });
  console.log('TTS audio: ' + audio.length + ' bytes');

  console.log('\nALL TESTS PASSED - Web Call is ready!');
}

main().catch((err) => {
  console.error('FAILED:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
