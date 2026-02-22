import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockCreate = vi.fn();

vi.mock('openai', () => ({
  default: class OpenAI {
    audio = { transcriptions: { create: mockCreate } };
  },
  toFile: vi.fn().mockImplementation((buf, name, opts) =>
    Promise.resolve({ name, type: opts?.type })
  ),
}));

import { OpenAISTTProvider } from './openai.js';

let provider: OpenAISTTProvider;

beforeEach(() => {
  mockCreate.mockReset();
  provider = new OpenAISTTProvider('test-key');
});

describe('OpenAISTTProvider', () => {
  it('returns transcribed text', async () => {
    mockCreate.mockResolvedValue({ text: 'Hello world' });

    const result = await provider.transcribe(Buffer.from('audio-data'));

    expect(result).toBe('Hello world');
  });

  it('passes model and language options', async () => {
    mockCreate.mockResolvedValue({ text: 'test' });

    await provider.transcribe(Buffer.from('audio'), {
      model: 'whisper-1',
      language: 'fr',
    });

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        model: 'whisper-1',
        language: 'fr',
      })
    );
  });

  it('uses default model whisper-1', async () => {
    mockCreate.mockResolvedValue({ text: 'test' });

    await provider.transcribe(Buffer.from('audio'));

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ model: 'whisper-1' })
    );
  });

  it('uses default language en', async () => {
    mockCreate.mockResolvedValue({ text: 'test' });

    await provider.transcribe(Buffer.from('audio'));

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ language: 'en' })
    );
  });
});
