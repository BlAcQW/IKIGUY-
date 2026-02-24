import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { formFromAssistant, buildPayload, DEFAULT_FORM, useAssistantEditor } from './useAssistantEditor';
import { buildAssistant } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  getAssistant: vi.fn(),
  updateAssistant: vi.fn(),
  createAssistant: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { getAssistant, updateAssistant, createAssistant } from '@/lib/api';

const mockedGetAssistant = vi.mocked(getAssistant);
const mockedUpdateAssistant = vi.mocked(updateAssistant);
const mockedCreateAssistant = vi.mocked(createAssistant);

describe('formFromAssistant', () => {
  it('extracts all fields from an Assistant', () => {
    const assistant = buildAssistant({
      name: 'Bot',
      model: { provider: 'openai', model: 'gpt-4o', temperature: 0.5, maxTokens: 2000, systemPrompt: 'Be helpful' },
      voice: { provider: 'openai', voiceId: 'nova', speed: 1.2 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'es' },
      firstMessage: 'Hi!',
      endCallMessage: 'Bye!',
      endCallPhrases: ['goodbye', 'bye'],
      metadata: {
        silenceTimeout: 60,
        responseDelay: 1.0,
        interruptionThreshold: 0.8,
        recordingEnabled: false,
        hipaaCompliant: true,
        serverUrl: 'https://example.com',
        idleTimeout: 300,
        idleMessage: 'Are you there?',
      },
    });

    const form = formFromAssistant(assistant);

    expect(form.name).toBe('Bot');
    expect(form.model).toBe('gpt-4o');
    expect(form.temperature).toBe(0.5);
    expect(form.maxTokens).toBe(2000);
    expect(form.systemPrompt).toBe('Be helpful');
    expect(form.voiceId).toBe('nova');
    expect(form.speed).toBe(1.2);
    expect(form.transcriberLanguage).toBe('es');
    expect(form.firstMessage).toBe('Hi!');
    expect(form.endCallMessage).toBe('Bye!');
    expect(form.endCallPhrases).toBe('goodbye, bye');
    expect(form.silenceTimeout).toBe(60);
    expect(form.responseDelay).toBe(1.0);
    expect(form.interruptionThreshold).toBe(0.8);
    expect(form.recordingEnabled).toBe(false);
    expect(form.hipaaCompliant).toBe(true);
    expect(form.serverUrl).toBe('https://example.com');
    expect(form.idleTimeout).toBe(300);
    expect(form.idleMessage).toBe('Are you there?');
  });

  it('handles null metadata with defaults', () => {
    const assistant = buildAssistant({ metadata: null });
    const form = formFromAssistant(assistant);

    expect(form.silenceTimeout).toBe(30);
    expect(form.responseDelay).toBe(0.5);
    expect(form.recordingEnabled).toBe(true);
    expect(form.hipaaCompliant).toBe(false);
  });

  it('handles null firstMessage and endCallMessage', () => {
    const assistant = buildAssistant({ firstMessage: null, endCallMessage: null, endCallPhrases: [] });
    const form = formFromAssistant(assistant);

    expect(form.firstMessage).toBe('');
    expect(form.endCallMessage).toBe('');
    expect(form.endCallPhrases).toBe('');
  });
});

describe('buildPayload', () => {
  it('converts form to API payload', () => {
    const payload = buildPayload({
      ...DEFAULT_FORM,
      name: 'MyBot',
      model: 'gpt-4o',
      temperature: 0.8,
      systemPrompt: 'Be nice',
      firstMessage: 'Hello',
      endCallPhrases: 'bye, goodbye, see ya',
    });

    expect(payload.name).toBe('MyBot');
    expect(payload.model.model).toBe('gpt-4o');
    expect(payload.model.temperature).toBe(0.8);
    expect(payload.model.systemPrompt).toBe('Be nice');
    expect(payload.firstMessage).toBe('Hello');
    expect(payload.endCallPhrases).toEqual(['bye', 'goodbye', 'see ya']);
  });

  it('splits endCallPhrases by comma and trims', () => {
    const payload = buildPayload({ ...DEFAULT_FORM, endCallPhrases: ' a , b ,  c  ' });
    expect(payload.endCallPhrases).toEqual(['a', 'b', 'c']);
  });

  it('omits empty endCallPhrases', () => {
    const payload = buildPayload({ ...DEFAULT_FORM, endCallPhrases: '' });
    expect(payload.endCallPhrases).toBeUndefined();
  });

  it('omits empty systemPrompt', () => {
    const payload = buildPayload({ ...DEFAULT_FORM, systemPrompt: '' });
    expect(payload.model.systemPrompt).toBeUndefined();
  });

  it('includes metadata fields', () => {
    const payload = buildPayload({ ...DEFAULT_FORM, silenceTimeout: 45, recordingEnabled: false });
    expect(payload.metadata.silenceTimeout).toBe(45);
    expect(payload.metadata.recordingEnabled).toBe(false);
  });
});

describe('useAssistantEditor hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads assistant when ID is provided', async () => {
    const assistant = buildAssistant({ id: 'a1' });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });

    const { result } = renderHook(() => useAssistantEditor('a1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockedGetAssistant).toHaveBeenCalledWith('a1');
    expect(result.current.assistant).toEqual(assistant);
    expect(result.current.form.name).toBe(assistant.name);
    expect(result.current.dirty).toBe(false);
  });

  it('resets when ID becomes undefined', async () => {
    const assistant = buildAssistant({ id: 'a1' });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });

    const { result, rerender } = renderHook(
      ({ id }) => useAssistantEditor(id),
      { initialProps: { id: 'a1' as string | undefined } },
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    rerender({ id: undefined });

    expect(result.current.assistant).toBeNull();
    expect(result.current.form).toEqual(DEFAULT_FORM);
    expect(result.current.dirty).toBe(false);
  });

  it('sets dirty when field changes', async () => {
    const assistant = buildAssistant({ id: 'a1' });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });

    const { result } = renderHook(() => useAssistantEditor('a1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.updateField('name', 'Changed Name');
    });

    expect(result.current.dirty).toBe(true);
    expect(result.current.form.name).toBe('Changed Name');
  });

  it('publish calls updateAssistant and resets dirty', async () => {
    const assistant = buildAssistant({ id: 'a1' });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedUpdateAssistant.mockResolvedValue({ success: true, data: assistant });

    const { result } = renderHook(() => useAssistantEditor('a1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.updateField('name', 'Updated');
    });

    await act(async () => {
      await result.current.publish();
    });

    expect(mockedUpdateAssistant).toHaveBeenCalledWith('a1', expect.any(Object));
    expect(result.current.dirty).toBe(false);
  });

  it('create calls createAssistant with name', async () => {
    const assistant = buildAssistant();
    mockedCreateAssistant.mockResolvedValue({ success: true, data: assistant });

    const { result } = renderHook(() => useAssistantEditor(undefined));

    let created: unknown;
    await act(async () => {
      created = await result.current.create('New Bot');
    });

    expect(mockedCreateAssistant).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'New Bot' }),
    );
    expect(created).toEqual(assistant);
  });

  it('handles load error gracefully', async () => {
    mockedGetAssistant.mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useAssistantEditor('bad-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.assistant).toBeNull();
  });

  it('handles publish error and shows toast', async () => {
    const assistant = buildAssistant({ id: 'pub-err' });
    mockedGetAssistant.mockResolvedValue({ success: true, data: assistant });
    mockedUpdateAssistant.mockRejectedValue(new Error('Publish failed'));

    const { result } = renderHook(() => useAssistantEditor('pub-err'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    let publishResult: unknown;
    await act(async () => {
      publishResult = await result.current.publish();
    });

    expect(publishResult).toBeNull();
    expect(result.current.saving).toBe(false);
    const { toast } = await import('sonner');
    expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to publish assistant', expect.objectContaining({ description: 'Publish failed' }));
  });

  it('handles create error and shows toast', async () => {
    mockedCreateAssistant.mockRejectedValue(new Error('Create failed'));

    const { result } = renderHook(() => useAssistantEditor(undefined));

    let created: unknown;
    await act(async () => {
      created = await result.current.create('Fail Bot');
    });

    expect(created).toBeNull();
    expect(result.current.saving).toBe(false);
    const { toast } = await import('sonner');
    expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to create assistant', expect.objectContaining({ description: 'Create failed' }));
  });

  it('publish returns null when no assistantId', async () => {
    const { result } = renderHook(() => useAssistantEditor(undefined));

    let publishResult: unknown;
    await act(async () => {
      publishResult = await result.current.publish();
    });

    expect(publishResult).toBeNull();
    expect(mockedUpdateAssistant).not.toHaveBeenCalled();
  });

  it('handles load error with non-Error object', async () => {
    mockedGetAssistant.mockRejectedValue('string error');

    const { result } = renderHook(() => useAssistantEditor('err-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.assistant).toBeNull();
    const { toast } = await import('sonner');
    expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to load assistant', expect.objectContaining({ description: 'Unknown error' }));
  });
});
