/**
 * Integration test: OpenAI GPT LLM
 *
 * Sends real prompts to OpenAI Chat API and verifies responses.
 * Requires OPENAI_API_KEY in .env.
 */
import { describe, it, expect } from 'vitest';
import { describeIfKey, requireKey } from '../helpers/skip-if-missing.js';
import { OpenAILLMProvider } from '@/providers/llm/openai.js';
import type { Message, LLMChatResult } from '@/providers/llm/types.js';

describeIfKey('OPENAI_API_KEY', 'OpenAI LLM Provider', () => {
  let provider: OpenAILLMProvider;

  beforeAll(() => {
    provider = new OpenAILLMProvider(requireKey('OPENAI_API_KEY'));
  });

  it('should return a chat response', async () => {
    const messages: Message[] = [
      { role: 'system', content: 'You are a helpful assistant. Reply in one sentence.' },
      { role: 'user', content: 'What is 2 + 2?' },
    ];

    const result = await provider.chat(messages, {
      model: 'gpt-4o-mini',
      maxTokens: 100,
    });

    // Without tools, returns a string
    expect(typeof result).toBe('string');
    const text = result as string;
    expect(text.length).toBeGreaterThan(0);
    // Should mention "4" somewhere
    expect(text).toMatch(/4/);
  });

  it('should handle tool calling', async () => {
    const messages: Message[] = [
      { role: 'system', content: 'You are a helpful assistant. Use the provided tools when appropriate.' },
      { role: 'user', content: 'What is the weather in London?' },
    ];

    const result = await provider.chat(messages, {
      model: 'gpt-4o-mini',
      maxTokens: 200,
      tools: [
        {
          type: 'function',
          function: {
            name: 'get_weather',
            description: 'Get current weather for a location',
            parameters: {
              type: 'object',
              properties: {
                location: { type: 'string', description: 'City name' },
              },
              required: ['location'],
            },
          },
        },
      ],
    });

    // With tools provided, should return LLMChatResult
    expect(typeof result).toBe('object');
    const chatResult = result as LLMChatResult;

    // The model should attempt to call the weather tool
    expect(chatResult.toolCalls.length).toBeGreaterThan(0);
    expect(chatResult.toolCalls[0].name).toBe('get_weather');

    // Arguments should include "London"
    const args = JSON.parse(chatResult.toolCalls[0].arguments);
    expect(args.location.toLowerCase()).toContain('london');
  });

  it('should support streaming', async () => {
    const messages: Message[] = [
      { role: 'user', content: 'Say "hello world" and nothing else.' },
    ];

    const chunks: string[] = [];
    for await (const chunk of provider.chatStream(messages, {
      model: 'gpt-4o-mini',
      maxTokens: 50,
    })) {
      chunks.push(chunk);
    }

    expect(chunks.length).toBeGreaterThan(0);
    const fullResponse = chunks.join('');
    expect(fullResponse.toLowerCase()).toContain('hello');
  });

  it('should throw an error with an invalid API key', async () => {
    const badProvider = new OpenAILLMProvider('sk-invalid-key-12345');

    await expect(
      badProvider.chat([{ role: 'user', content: 'Hi' }])
    ).rejects.toThrow();
  });
});
