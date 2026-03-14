import { useEffect, useState, useCallback, useRef } from 'react';
import { getAssistant, updateAssistant, createAssistant } from '@/lib/api';
import type { Assistant } from '@/types';
import { toast } from 'sonner';

export interface FallbackVoice {
  provider: string;
  voiceId: string;
}

export interface AssistantForm {
  name: string;
  // Model
  modelProvider: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  firstMessageMode: 'assistant-speaks-first' | 'wait-for-user' | 'off';
  // Voice
  voiceProvider: string;
  voiceId: string;
  speed: number;
  fallbackVoices: FallbackVoice[];
  // Transcriber
  transcriberProvider: string;
  transcriberModel: string;
  transcriberLanguage: string;
  transcriberKeywords: string;
  endOfTurnConfidenceThreshold: number;
  transcriberCustomUrl: string;
  // General
  firstMessage: string;
  // Advanced
  endCallMessage: string;
  endCallPhrases: string;
  // Pipeline (stored in metadata)
  silenceTimeout: number;
  responseDelay: number;
  interruptionThreshold: number;
  // Start Speaking Plan (stored in metadata)
  startSpeakingWaitTime: number;
  smartEndpointing: boolean;
  // Stop Speaking Plan (stored in metadata)
  stopSpeakingNumWords: number;
  backoffTime: number;
  // Voicemail Detection (stored in metadata)
  voicemailDetectionEnabled: boolean;
  voicemailMessage: string;
  voicemailTimeout: number;
  // Recording (stored in metadata)
  recordingEnabled: boolean;
  audioRecordingFormat: 'wav' | 'mp3';
  videoRecordingEnabled: boolean;
  // Privacy (stored in metadata)
  hipaaCompliant: boolean;
  // Messaging (stored in metadata)
  serverUrl: string;
  idleTimeout: number;
  idleMessage: string;
  // Analysis (stored in metadata)
  successEvaluationPrompt: string;
  summaryPrompt: string;
  structuredDataSchema: string;
  // Compliance (stored in metadata)
  pciDssCompliant: boolean;
  recordingConsent: 'none' | 'single-party' | 'all-party';
  dataRetentionDays: number;
}

export const DEFAULT_FORM: AssistantForm = {
  name: '',
  modelProvider: 'openai',
  model: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 1000,
  systemPrompt: '',
  firstMessageMode: 'assistant-speaks-first',
  voiceProvider: 'openai',
  voiceId: 'alloy',
  speed: 1.0,
  fallbackVoices: [],
  transcriberProvider: 'openai',
  transcriberModel: 'whisper-1',
  transcriberLanguage: 'en',
  transcriberKeywords: '',
  endOfTurnConfidenceThreshold: 0.5,
  transcriberCustomUrl: '',
  firstMessage: '',
  endCallMessage: '',
  endCallPhrases: '',
  silenceTimeout: 30,
  responseDelay: 0.5,
  interruptionThreshold: 0.5,
  startSpeakingWaitTime: 0.4,
  smartEndpointing: false,
  stopSpeakingNumWords: 0,
  backoffTime: 1.0,
  voicemailDetectionEnabled: false,
  voicemailMessage: '',
  voicemailTimeout: 30,
  recordingEnabled: true,
  audioRecordingFormat: 'wav',
  videoRecordingEnabled: false,
  hipaaCompliant: false,
  serverUrl: '',
  idleTimeout: 120,
  idleMessage: '',
  successEvaluationPrompt: '',
  summaryPrompt: '',
  structuredDataSchema: '',
  pciDssCompliant: false,
  recordingConsent: 'none',
  dataRetentionDays: 90,
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
    firstMessageMode: (meta.firstMessageMode as AssistantForm['firstMessageMode']) ?? 'assistant-speaks-first',
    voiceProvider: a.voice.provider ?? 'openai',
    voiceId: a.voice.voiceId,
    speed: a.voice.speed ?? 1.0,
    fallbackVoices: (meta.fallbackVoices as FallbackVoice[]) ?? [],
    transcriberProvider: a.transcriber?.provider ?? 'openai',
    transcriberModel: a.transcriber?.model ?? 'whisper-1',
    transcriberLanguage: a.transcriber?.language ?? 'en',
    transcriberKeywords: (meta.transcriberKeywords as string) ?? '',
    endOfTurnConfidenceThreshold: (meta.endOfTurnConfidenceThreshold as number) ?? 0.5,
    transcriberCustomUrl: (meta.transcriberCustomUrl as string) ?? '',
    firstMessage: a.firstMessage ?? '',
    endCallMessage: a.endCallMessage ?? '',
    endCallPhrases: (a.endCallPhrases ?? []).join(', '),
    silenceTimeout: (meta.silenceTimeout as number) ?? 30,
    responseDelay: (meta.responseDelay as number) ?? 0.5,
    interruptionThreshold: (meta.interruptionThreshold as number) ?? 0.5,
    startSpeakingWaitTime: (meta.startSpeakingWaitTime as number) ?? 0.4,
    smartEndpointing: (meta.smartEndpointing as boolean) ?? false,
    stopSpeakingNumWords: (meta.stopSpeakingNumWords as number) ?? 0,
    backoffTime: (meta.backoffTime as number) ?? 1.0,
    voicemailDetectionEnabled: (meta.voicemailDetectionEnabled as boolean) ?? false,
    voicemailMessage: (meta.voicemailMessage as string) ?? '',
    voicemailTimeout: (meta.voicemailTimeout as number) ?? 30,
    recordingEnabled: (meta.recordingEnabled as boolean) ?? true,
    audioRecordingFormat: (meta.audioRecordingFormat as 'wav' | 'mp3') ?? 'wav',
    videoRecordingEnabled: (meta.videoRecordingEnabled as boolean) ?? false,
    hipaaCompliant: (meta.hipaaCompliant as boolean) ?? false,
    serverUrl: (meta.serverUrl as string) ?? '',
    idleTimeout: (meta.idleTimeout as number) ?? 120,
    idleMessage: (meta.idleMessage as string) ?? '',
    successEvaluationPrompt: (meta.successEvaluationPrompt as string) ?? '',
    summaryPrompt: (meta.summaryPrompt as string) ?? '',
    structuredDataSchema: (meta.structuredDataSchema as string) ?? '',
    pciDssCompliant: (meta.pciDssCompliant as boolean) ?? false,
    recordingConsent: (meta.recordingConsent as AssistantForm['recordingConsent']) ?? 'none',
    dataRetentionDays: (meta.dataRetentionDays as number) ?? 90,
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
      // Pipeline
      silenceTimeout: form.silenceTimeout,
      responseDelay: form.responseDelay,
      interruptionThreshold: form.interruptionThreshold,
      // Start Speaking Plan
      startSpeakingWaitTime: form.startSpeakingWaitTime,
      smartEndpointing: form.smartEndpointing,
      // Stop Speaking Plan
      stopSpeakingNumWords: form.stopSpeakingNumWords,
      backoffTime: form.backoffTime,
      // Voicemail Detection
      voicemailDetectionEnabled: form.voicemailDetectionEnabled,
      voicemailMessage: form.voicemailMessage || undefined,
      voicemailTimeout: form.voicemailTimeout,
      // Recording
      recordingEnabled: form.recordingEnabled,
      audioRecordingFormat: form.audioRecordingFormat,
      videoRecordingEnabled: form.videoRecordingEnabled,
      // Privacy
      hipaaCompliant: form.hipaaCompliant,
      // Voice
      fallbackVoices: form.fallbackVoices.length > 0 ? form.fallbackVoices : undefined,
      // Transcriber extras
      transcriberKeywords: form.transcriberKeywords || undefined,
      endOfTurnConfidenceThreshold: form.endOfTurnConfidenceThreshold,
      transcriberCustomUrl: form.transcriberCustomUrl || undefined,
      // Messaging
      serverUrl: form.serverUrl || undefined,
      idleTimeout: form.idleTimeout,
      idleMessage: form.idleMessage || undefined,
      firstMessageMode: form.firstMessageMode,
      // Analysis
      successEvaluationPrompt: form.successEvaluationPrompt || undefined,
      summaryPrompt: form.summaryPrompt || undefined,
      structuredDataSchema: form.structuredDataSchema || undefined,
      // Compliance
      pciDssCompliant: form.pciDssCompliant,
      recordingConsent: form.recordingConsent,
      dataRetentionDays: form.dataRetentionDays,
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
