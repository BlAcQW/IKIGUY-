import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('openai', () => {
  const mockCreate = vi.fn();
  return {
    default: class OpenAI {
      chat = { completions: { create: mockCreate } };
    },
    __mockCreate: mockCreate,
  };
});

import { OpenAILLMProvider } from './openai.js';

let provider: OpenAILLMProvider;
let mockCreate: ReturnType<typeof vi.fn>;

beforeEach(async () => {
  const mod = await import('openai');
  mockCreate = (mod as any).__mockCreate;
  mockCreate.mockReset();
  provider = new OpenAILLMProvider('test-key');
});

describe('OpenAILLMProvider', () => {
  describe('chat', () => {
    it('returns the assistant response text', async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: 'Hello there!' } }],
      });

      const result = await provider.chat([
        { role: 'user', content: 'Hi' },
      ]);

      expect(result).toBe('Hello there!');
    });

    it('passes model and options to OpenAI', async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: 'ok' } }],
      });

      await provider.chat(
        [{ role: 'system', content: 'You are helpful' }],
        { model: 'gpt-4-turbo', temperature: 0.5, maxTokens: 500 }
      );

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          model: 'gpt-4-turbo',
          temperature: 0.5,
          max_tokens: 500,
        })
      );
    });

    it('uses default model gpt-4 when not specified', async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: 'ok' } }],
      });

      await provider.chat([{ role: 'user', content: 'test' }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: 'gpt-4' })
      );
    });

    it('returns empty string when no content', async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: null } }],
      });

      const result = await provider.chat([{ role: 'user', content: 'test' }]);
      expect(result).toBe('');
    });

    it('maps message roles correctly', async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: 'ok' } }],
      });

      await provider.chat([
        { role: 'system', content: 'sys' },
        { role: 'user', content: 'usr' },
        { role: 'assistant', content: 'ast' },
      ]);

      const call = mockCreate.mock.calls[0][0];
      expect(call.messages).toEqual([
        { role: 'system', content: 'sys' },
        { role: 'user', content: 'usr' },
        { role: 'assistant', content: 'ast' },
      ]);
    });
  });

  describe('chatStream', () => {
    it('yields content chunks', async () => {
      const chunks = [
        { choices: [{ delta: { content: 'Hello' } }] },
        { choices: [{ delta: { content: ' world' } }] },
        { choices: [{ delta: { content: null } }] },
      ];

      mockCreate.mockResolvedValue({
        [Symbol.asyncIterator]: async function* () {
          for (const chunk of chunks) {
            yield chunk;
          }
        },
      });

      const result: string[] = [];
      for await (const text of provider.chatStream([{ role: 'user', content: 'Hi' }])) {
        result.push(text);
      }

      expect(result).toEqual(['Hello', ' world']);
    });

    it('passes stream: true to OpenAI', async () => {
      mockCreate.mockResolvedValue({
        [Symbol.asyncIterator]: async function* () {},
      });

      // Consume the generator
      for await (const _ of provider.chatStream([{ role: 'user', content: 'test' }])) {
        // noop
      }

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ stream: true })
      );
    });
  });
});
