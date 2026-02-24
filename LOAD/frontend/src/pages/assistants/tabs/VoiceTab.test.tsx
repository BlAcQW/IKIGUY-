import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@test/helpers/render';
import { VoiceTab } from './VoiceTab';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { DEFAULT_FORM } from '../hooks/useAssistantEditor';

describe('VoiceTab', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
  });

  it('renders Text-to-Speech heading', () => {
    render(<VoiceTab form={form} updateField={updateField} />);
    expect(screen.getByText('Text-to-Speech')).toBeInTheDocument();
  });

  it('renders Speech Settings heading', () => {
    render(<VoiceTab form={form} updateField={updateField} />);
    expect(screen.getByText('Speech Settings')).toBeInTheDocument();
  });

  it('renders provider and voice labels', () => {
    render(<VoiceTab form={form} updateField={updateField} />);
    expect(screen.getByText('Provider')).toBeInTheDocument();
    expect(screen.getByText('Voice')).toBeInTheDocument();
  });

  it('renders with elevenlabs provider', () => {
    const elevenlabsForm = { ...form, voiceProvider: 'elevenlabs', voiceId: 'rachel' };
    render(<VoiceTab form={elevenlabsForm} updateField={updateField} />);
    expect(screen.getByText('Text-to-Speech')).toBeInTheDocument();
    expect(screen.getByText('Speech Settings')).toBeInTheDocument();
  });

  it('renders with deepgram provider', () => {
    const deepgramForm = { ...form, voiceProvider: 'deepgram', voiceId: 'aura-asteria-en' };
    render(<VoiceTab form={deepgramForm} updateField={updateField} />);
    expect(screen.getByText('Text-to-Speech')).toBeInTheDocument();
    expect(screen.getByText('Speech Settings')).toBeInTheDocument();
  });

  it('falls back to openai voices for unknown provider', () => {
    const unknownForm = { ...form, voiceProvider: 'unknown', voiceId: 'alloy' };
    render(<VoiceTab form={unknownForm} updateField={updateField} />);
    expect(screen.getByText('Text-to-Speech')).toBeInTheDocument();
  });
});
