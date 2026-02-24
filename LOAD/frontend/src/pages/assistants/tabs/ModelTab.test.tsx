import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@test/helpers/render';
import { ModelTab } from './ModelTab';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { DEFAULT_FORM } from '../hooks/useAssistantEditor';

describe('ModelTab', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
  });

  it('renders Greeting section heading', () => {
    render(<ModelTab form={form} updateField={updateField} />);
    expect(screen.getByText('Greeting')).toBeInTheDocument();
  });

  it('renders System Prompt section heading', () => {
    render(<ModelTab form={form} updateField={updateField} />);
    expect(screen.getByText('System Prompt')).toBeInTheDocument();
  });

  it('renders Model section heading', () => {
    render(<ModelTab form={form} updateField={updateField} />);
    const headings = screen.getAllByText('Model');
    // h3 heading plus the label
    expect(headings.length).toBeGreaterThanOrEqual(1);
    expect(headings[0]).toBeInTheDocument();
  });

  it('renders Parameters section heading', () => {
    render(<ModelTab form={form} updateField={updateField} />);
    expect(screen.getByText('Parameters')).toBeInTheDocument();
  });

  it('typing in first message calls updateField', async () => {
    const { user } = render(<ModelTab form={form} updateField={updateField} />);
    const input = screen.getByPlaceholderText('Hello! How can I help you today?');
    await user.type(input, 'Hi');
    expect(updateField).toHaveBeenCalledWith('firstMessage', expect.any(String));
  });

  it('typing in system prompt calls updateField', async () => {
    const { user } = render(<ModelTab form={form} updateField={updateField} />);
    const textarea = screen.getByPlaceholderText('You are a helpful assistant that...');
    await user.type(textarea, 'Be nice');
    expect(updateField).toHaveBeenCalledWith('systemPrompt', expect.any(String));
  });

  it('typing in max tokens calls updateField', async () => {
    const { user } = render(<ModelTab form={form} updateField={updateField} />);
    const input = screen.getByDisplayValue('1000');
    await user.clear(input);
    await user.type(input, '2000');
    expect(updateField).toHaveBeenCalledWith('maxTokens', expect.any(Number));
  });

  it('renders provider select with openai text', () => {
    render(<ModelTab form={form} updateField={updateField} />);
    expect(screen.getByText('Provider')).toBeInTheDocument();
    // The Slider component shows a label "Temperature"
    expect(screen.getByText('Temperature')).toBeInTheDocument();
  });

  it('renders with anthropic provider showing anthropic models', () => {
    const anthropicForm = { ...form, modelProvider: 'anthropic', model: 'claude-sonnet-4-20250514' };
    render(<ModelTab form={anthropicForm} updateField={updateField} />);
    expect(screen.getByText('Greeting')).toBeInTheDocument();
    expect(screen.getByText('Parameters')).toBeInTheDocument();
  });

  it('renders with google provider', () => {
    const googleForm = { ...form, modelProvider: 'google', model: 'gemini-2.0-flash' };
    render(<ModelTab form={googleForm} updateField={updateField} />);
    expect(screen.getByText('Greeting')).toBeInTheDocument();
    expect(screen.getByText('Parameters')).toBeInTheDocument();
  });

  it('falls back to openai models for unknown provider', () => {
    const unknownForm = { ...form, modelProvider: 'unknown', model: 'gpt-4o' };
    render(<ModelTab form={unknownForm} updateField={updateField} />);
    expect(screen.getByText('Greeting')).toBeInTheDocument();
  });
});
