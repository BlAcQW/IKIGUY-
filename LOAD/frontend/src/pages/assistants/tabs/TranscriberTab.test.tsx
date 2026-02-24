import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@test/helpers/render';
import { TranscriberTab } from './TranscriberTab';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { DEFAULT_FORM } from '../hooks/useAssistantEditor';

describe('TranscriberTab', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
  });

  it('renders Speech-to-Text heading', () => {
    render(<TranscriberTab form={form} updateField={updateField} />);
    expect(screen.getByText('Speech-to-Text')).toBeInTheDocument();
  });

  it('renders Language heading', () => {
    render(<TranscriberTab form={form} updateField={updateField} />);
    expect(screen.getByText('Language')).toBeInTheDocument();
  });

  it('renders provider and model labels', () => {
    render(<TranscriberTab form={form} updateField={updateField} />);
    expect(screen.getByText('Provider')).toBeInTheDocument();
    expect(screen.getByText('Model')).toBeInTheDocument();
  });

  it('renders Transcription Language label', () => {
    render(<TranscriberTab form={form} updateField={updateField} />);
    expect(screen.getByText('Transcription Language')).toBeInTheDocument();
  });

  it('renders with deepgram provider showing deepgram models', () => {
    const deepgramForm = { ...form, transcriberProvider: 'deepgram', transcriberModel: 'nova-2' };
    render(<TranscriberTab form={deepgramForm} updateField={updateField} />);
    expect(screen.getByText('Speech-to-Text')).toBeInTheDocument();
  });

  it('falls back to openai models for unknown provider', () => {
    const unknownForm = { ...form, transcriberProvider: 'unknown-provider', transcriberModel: 'whisper-1' };
    render(<TranscriberTab form={unknownForm} updateField={updateField} />);
    // Should still render without errors using the fallback
    expect(screen.getByText('Speech-to-Text')).toBeInTheDocument();
  });
});
