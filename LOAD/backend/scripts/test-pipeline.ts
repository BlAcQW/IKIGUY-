import { readFileSync } from 'fs';
import { resolve } from 'path';

// Load .env manually to avoid shell escaping issues
const envPath = resolve(import.meta.dirname ?? '.', '../.env');
const envContent = readFileSync(envPath, 'utf8');
for (const line of envContent.split('\n')) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  const key = trimmed.slice(0, eqIdx);
  const value = trimmed.slice(eqIdx + 1);
  process.env[key] = value;
}

async function main() {
  const { buildPipelineFromAssistant } = await import('@/providers/registry.js');

  // 1) Build Google pipeline
  const googlePipeline = buildPipelineFromAssistant({
    model: { provider: 'google', model: 'gemini-2.0-flash' },
    voice: { provider: 'openai', voiceId: 'alloy' },
    transcriber: { provider: 'openai', model: 'whisper-1' },
  });
  console.log('Google pipeline: LLM=' + googlePipeline.llm.name + ' STT=' + googlePipeline.stt.name + ' TTS=' + googlePipeline.tts.name);

  // 2) Build OpenAI pipeline
  const openaiPipeline = buildPipelineFromAssistant({
    model: { provider: 'openai', model: 'gpt-4o' },
    voice: { provider: 'openai', voiceId: 'alloy' },
    transcriber: { provider: 'openai', model: 'whisper-1' },
  });
  console.log('OpenAI pipeline: LLM=' + openaiPipeline.llm.name + ' STT=' + openaiPipeline.stt.name + ' TTS=' + openaiPipeline.tts.name);

  // 3) Actually call Gemini
  console.log('\nCalling Gemini...');
  const result = await googlePipeline.llm.chat([
    { role: 'system', content: 'Reply in one short sentence only.' },
    { role: 'user', content: 'Say hello and introduce yourself' },
  ], { model: 'gemini-2.0-flash', temperature: 0.7, maxTokens: 100 });

  const text = typeof result === 'string' ? result : result.content;
  console.log('Gemini says: ' + text);
  console.log('\nSUCCESS - Google provider works! Web Call will work.');
}

main().catch((err) => {
  console.error('FAILED:', err instanceof Error ? err.message : String(err));
  process.exit(1);
});
