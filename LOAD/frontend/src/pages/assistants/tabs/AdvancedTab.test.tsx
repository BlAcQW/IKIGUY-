import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '@test/helpers/render';
import { AdvancedTab } from './AdvancedTab';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { DEFAULT_FORM } from '../hooks/useAssistantEditor';

describe('AdvancedTab', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
  });

  it('renders Pipeline section heading', () => {
    render(<AdvancedTab form={form} updateField={updateField} />);
    expect(screen.getByText('Pipeline')).toBeInTheDocument();
  });

  it('renders Privacy section heading', () => {
    render(<AdvancedTab form={form} updateField={updateField} />);
    expect(screen.getByText('Privacy')).toBeInTheDocument();
  });

  it('renders Messaging section heading', () => {
    render(<AdvancedTab form={form} updateField={updateField} />);
    expect(screen.getByText('Messaging')).toBeInTheDocument();
  });

  it('renders recording toggle as checked by default', () => {
    render(<AdvancedTab form={form} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    // First switch is Call Recording (recordingEnabled=true by default)
    expect(switches[0]).toHaveAttribute('aria-checked', 'true');
  });

  it('clicking recording toggle calls updateField with false', async () => {
    const { user } = render(<AdvancedTab form={form} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    await user.click(switches[0]);
    expect(updateField).toHaveBeenCalledWith('recordingEnabled', false);
  });

  it('renders HIPAA toggle as unchecked by default', () => {
    render(<AdvancedTab form={form} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    // Second switch is HIPAA Compliant (hipaaCompliant=false by default)
    expect(switches[1]).toHaveAttribute('aria-checked', 'false');
  });

  it('clicking HIPAA toggle calls updateField with true', async () => {
    const { user } = render(<AdvancedTab form={form} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    await user.click(switches[1]);
    expect(updateField).toHaveBeenCalledWith('hipaaCompliant', true);
  });

  it('typing in Server URL input calls updateField', async () => {
    const { user } = render(<AdvancedTab form={form} updateField={updateField} />);
    const input = screen.getByPlaceholderText('https://your-server.com/webhook');
    await user.type(input, 'https://example.com');
    expect(updateField).toHaveBeenCalledWith('serverUrl', expect.any(String));
  });

  it('typing in Idle Message input calls updateField', async () => {
    const { user } = render(<AdvancedTab form={form} updateField={updateField} />);
    const input = screen.getByPlaceholderText('Are you still there?');
    await user.type(input, 'Hello?');
    expect(updateField).toHaveBeenCalledWith('idleMessage', expect.any(String));
  });

  it('typing in idle timeout calls updateField', async () => {
    const { user } = render(<AdvancedTab form={form} updateField={updateField} />);
    const input = screen.getByDisplayValue('120');
    await user.clear(input);
    await user.type(input, '300');
    expect(updateField).toHaveBeenCalledWith('idleTimeout', expect.any(Number));
  });

  it('changing silence timeout slider calls updateField', () => {
    const { container } = render(<AdvancedTab form={form} updateField={updateField} />);
    const rangeInputs = container.querySelectorAll('input[type="range"]');
    expect(rangeInputs.length).toBe(3); // silenceTimeout, responseDelay, interruptionThreshold

    fireEvent.change(rangeInputs[0], { target: { value: '60' } });
    expect(updateField).toHaveBeenCalledWith('silenceTimeout', 60);
  });

  it('changing response delay slider calls updateField', () => {
    const { container } = render(<AdvancedTab form={form} updateField={updateField} />);
    const rangeInputs = container.querySelectorAll('input[type="range"]');

    fireEvent.change(rangeInputs[1], { target: { value: '1.5' } });
    expect(updateField).toHaveBeenCalledWith('responseDelay', 1.5);
  });

  it('changing interruption threshold slider calls updateField', () => {
    const { container } = render(<AdvancedTab form={form} updateField={updateField} />);
    const rangeInputs = container.querySelectorAll('input[type="range"]');

    fireEvent.change(rangeInputs[2], { target: { value: '0.75' } });
    expect(updateField).toHaveBeenCalledWith('interruptionThreshold', 0.75);
  });

  it('renders with recordingEnabled=false showing unchecked switch', () => {
    const offForm = { ...form, recordingEnabled: false };
    render(<AdvancedTab form={offForm} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    expect(switches[0]).toHaveAttribute('aria-checked', 'false');
  });

  it('renders with hipaaCompliant=true showing checked switch', () => {
    const hipaaForm = { ...form, hipaaCompliant: true };
    render(<AdvancedTab form={hipaaForm} updateField={updateField} />);
    const switches = screen.getAllByRole('switch');
    expect(switches[1]).toHaveAttribute('aria-checked', 'true');
  });
});
