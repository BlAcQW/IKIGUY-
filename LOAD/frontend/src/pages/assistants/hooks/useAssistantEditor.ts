import { useEffect, useState, useCallback, useRef } from 'react';
import { getAssistant, updateAssistant, createAssistant } from '@/lib/api';
import type { Assistant } from '@/types';
import { toast } from 'sonner';

export interface AssistantForm {
  name: string;
  // Model
  modelProvider: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  // Voice
  voiceProvider: string;
  voiceId: string;
  speed: number;
  // Transcriber
  transcriberProvider: string;
  transcriberModel: string;
  transcriberLanguage: string;
  // General
  firstMessage: string;
  // Advanced
  endCallMessage: string;
  endCallPhrases: string;
  // Pipeline (stored in metadata)
  silenceTimeout: number;
  responseDelay: number;
  interruptionThreshold: number;
  // Privacy (stored in metadata)
  recordingEnabled: boolean;
  hipaaCompliant: boolean;
  // Messaging (stored in metadata)
  serverUrl: string;
  idleTimeout: number;
  idleMessage: string;
}

export const DEFAULT_FORM: AssistantForm = {
  name: '',
  modelProvider: 'openai',
  model: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 1000,
  systemPrompt: '',
  voiceProvider: 'openai',
  voiceId: 'alloy',
  speed: 1.0,
  transcriberProvider: 'openai',
  transcriberModel: 'whisper-1',
  transcriberLanguage: 'en',
  firstMessage: '',
  endCallMessage: '',
  endCallPhrases: '',
  silenceTimeout: 30,
  responseDelay: 0.5,
  interruptionThreshold: 0.5,
  recordingEnabled: true,
  hipaaCompliant: false,
  serverUrl: '',
  idleTimeout: 120,
  idleMessage: '',
};

export function formFromAssistant(a: Assistant): AssistantForm {
  const meta = (a.metadata ?? {}) as Record<string, unknown>;
  return {
    name: a.name,
    modelProvider: a.model.provider ?? 'openai',
    model: a.model.model,
    temperature: a.model.temperature ?? 0.7,
    maxTokens: a.model.maxTokens ?? 1000,
    systemPrompt: a.model.systemPrompt ?? '',
    voiceProvider: a.voice.provider ?? 'openai',
    voiceId: a.voice.voiceId,
    speed: a.voice.speed ?? 1.0,
    transcriberProvider: a.transcriber?.provider ?? 'openai',
    transcriberModel: a.transcriber?.model ?? 'whisper-1',
    transcriberLanguage: a.transcriber?.language ?? 'en',
    firstMessage: a.firstMessage ?? '',
    endCallMessage: a.endCallMessage ?? '',
    endCallPhrases: (a.endCallPhrases ?? []).join(', '),
    silenceTimeout: (meta.silenceTimeout as number) ?? 30,
    responseDelay: (meta.responseDelay as number) ?? 0.5,
    interruptionThreshold: (meta.interruptionThreshold as number) ?? 0.5,
    recordingEnabled: (meta.recordingEnabled as boolean) ?? true,
    hipaaCompliant: (meta.hipaaCompliant as boolean) ?? false,
    serverUrl: (meta.serverUrl as string) ?? '',
    idleTimeout: (meta.idleTimeout as number) ?? 120,
    idleMessage: (meta.idleMessage as string) ?? '',
  };
}

export function buildPayload(form: AssistantForm) {
  const phrases = form.endCallPhrases
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    name: form.name,
    model: {
      provider: form.modelProvider,
      model: form.model,
      temperature: form.temperature,
      maxTokens: form.maxTokens,
      systemPrompt: form.systemPrompt || undefined,
    },
    voice: {
      provider: form.voiceProvider,
      voiceId: form.voiceId,
      speed: form.speed,
    },
    transcriber: {
      provider: form.transcriberProvider,
      model: form.transcriberModel,
      language: form.transcriberLanguage,
    },
    firstMessage: form.firstMessage || undefined,
    endCallMessage: form.endCallMessage || undefined,
    endCallPhrases: phrases.length > 0 ? phrases : undefined,
    metadata: {
      silenceTimeout: form.silenceTimeout,
      responseDelay: form.responseDelay,
      interruptionThreshold: form.interruptionThreshold,
      recordingEnabled: form.recordingEnabled,
      hipaaCompliant: form.hipaaCompliant,
      serverUrl: form.serverUrl || undefined,
      idleTimeout: form.idleTimeout,
      idleMessage: form.idleMessage || undefined,
    },
  };
}

export function useAssistantEditor(assistantId: string | undefined) {
  const [assistant, setAssistant] = useState<Assistant | null>(null);
  const [form, setForm] = useState<AssistantForm>(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const baselineRef = useRef<string>('');

  const loadAssistant = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const result = await getAssistant(id);
      setAssistant(result.data);
      const formData = formFromAssistant(result.data);
      setForm(formData);
      baselineRef.current = JSON.stringify(formData);
      setDirty(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to load assistant', { description: message });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (assistantId) {
      loadAssistant(assistantId);
    } else {
      setAssistant(null);
      setForm(DEFAULT_FORM);
      baselineRef.current = '';
      setDirty(false);
    }
  }, [assistantId, loadAssistant]);

  const updateField = useCallback(<K extends keyof AssistantForm>(key: K, value: AssistantForm[K]) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value };
      setDirty(JSON.stringify(next) !== baselineRef.current);
      return next;
    });
  }, []);

  const publish = useCallback(async () => {
    if (!assistantId) return null;
    setSaving(true);
    try {
      const data = buildPayload(form);
      const result = await updateAssistant(assistantId, data);
      toast.success('Assistant published');
      const formData = formFromAssistant(result.data);
      setForm(formData);
      baselineRef.current = JSON.stringify(formData);
      setDirty(false);
      setAssistant(result.data);
      return result.data;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to publish assistant', { description: message });
      return null;
    } finally {
      setSaving(false);
    }
  }, [assistantId, form]);

  const create = useCallback(async (name: string) => {
    setSaving(true);
    try {
      const data = buildPayload({ ...DEFAULT_FORM, name });
      const result = await createAssistant(data);
      toast.success('Assistant created');
      return result.data;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error('Failed to create assistant', { description: message });
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

  return {
    assistant,
    form,
    loading,
    saving,
    dirty,
    updateField,
    publish,
    create,
  };
}
