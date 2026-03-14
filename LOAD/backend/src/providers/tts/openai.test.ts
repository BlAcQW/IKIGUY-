import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockCreate = vi.fn();

vi.mock('openai', () => ({
  default: class OpenAI {
    audio = { speech: { create: mockCreate } };
  },
}));

import { OpenAITTSProvider } from './openai.js';

let provider: OpenAITTSProvider;

beforeEach(() => {
  mockCreate.mockReset();
  provider = new OpenAITTSProvider('test-key');
});

describe('OpenAITTSProvider', () => {
  it('returns audio buffer', async () => {
    const fakeAudio = new ArrayBuffer(100);
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(fakeAudio),
    });

    const result = await provider.synthesize('Hello');

    expect(Buffer.isBuffer(result)).toBe(true);
    expect(result.length).toBe(100);
  });

  it('passes text as input', async () => {
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });

    await provider.synthesize('Test speech');

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ input: 'Test speech' })
    );
  });

  it('passes voice and speed options', async () => {
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });

    await provider.synthesize('Hello', { voiceId: 'nova', speed: 1.5 });

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        voice: 'nova',
        speed: 1.5,
      })
    );
  });

  it('uses default voice alloy', async () => {
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });

    await provider.synthesize('Hello');

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ voice: 'alloy' })
    );
  });

  it('uses PCM response format', async () => {
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });

    await provider.synthesize('Hello');

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ response_format: 'pcm' })
    );
  });

  it('uses default model tts-1', async () => {
    mockCreate.mockResolvedValue({
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    });

    await provider.synthesize('Hello');

    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({ model: 'tts-1' })
    );
  });
});
