import { describe, it, expect } from 'vitest';
import { createAssistantSchema, updateAssistantSchema, listAssistantsSchema } from './schemas.js';

describe('createAssistantSchema', () => {
  it('validates a full valid input', () => {
    const input = {
      name: 'Sales Bot',
      model: { provider: 'openai', model: 'gpt-4', temperature: 0.5, maxTokens: 500 },
      voice: { provider: 'openai', voiceId: 'nova', speed: 1.2 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      firstMessage: 'Hello!',
      endCallMessage: 'Goodbye!',
      endCallPhrases: ['bye', 'goodbye'],
      metadata: { team: 'sales' },
    };
    const result = createAssistantSchema.parse(input);
    expect(result.name).toBe('Sales Bot');
    expect(result.model.temperature).toBe(0.5);
    expect(result.voice.voiceId).toBe('nova');
  });

  it('applies defaults for model, voice, and transcriber', () => {
    const result = createAssistantSchema.parse({ name: 'Minimal Bot' });
    expect(result.model).toEqual({
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 1000,
    });
    expect(result.voice).toEqual({
      provider: 'openai',
      voiceId: 'alloy',
      speed: 1.0,
    });
    expect(result.transcriber).toEqual({
      provider: 'openai',
      model: 'whisper-1',
      language: 'en',
    });
  });

  it('rejects a missing name', () => {
    expect(() => createAssistantSchema.parse({})).toThrow();
  });

  it('rejects an empty name', () => {
    expect(() => createAssistantSchema.parse({ name: '' })).toThrow('Name is required');
  });

  it('defaults endCallPhrases to empty array', () => {
    const result = createAssistantSchema.parse({ name: 'Bot' });
    expect(result.endCallPhrases).toEqual([]);
  });
});

describe('updateAssistantSchema', () => {
  it('accepts partial updates', () => {
    const result = updateAssistantSchema.parse({ name: 'Updated' });
    expect(result.name).toBe('Updated');
    expect(result.model).toBeUndefined();
  });

  it('accepts an empty object', () => {
    const result = updateAssistantSchema.parse({});
    expect(result).toEqual({});
  });
});

describe('listAssistantsSchema', () => {
  it('coerces string page and limit to numbers', () => {
    const result = listAssistantsSchema.parse({ page: '3', limit: '50' });
    expect(result.page).toBe(3);
    expect(result.limit).toBe(50);
  });

  it('applies default values', () => {
    const result = listAssistantsSchema.parse({});
    expect(result.page).toBe(1);
    expect(result.limit).toBe(20);
  });

  it('rejects limit above 100', () => {
    expect(() => listAssistantsSchema.parse({ limit: 101 })).toThrow();
  });
});
