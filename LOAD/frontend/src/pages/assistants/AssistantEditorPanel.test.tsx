import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';
import { AssistantEditorPanel } from './AssistantEditorPanel';
import type { AssistantForm } from './hooks/useAssistantEditor';
import { DEFAULT_FORM } from './hooks/useAssistantEditor';

vi.mock('@/lib/api', () => ({
  getAssistantTools: vi.fn().mockResolvedValue({ data: [] }),
  attachToolToAssistant: vi.fn(),
  detachToolFromAssistant: vi.fn(),
  listTools: vi.fn(),
  listToolTemplates: vi.fn(),
  createToolFromTemplate: vi.fn(),
}));

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

describe('AssistantEditorPanel', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;
  let onPublish: ReturnType<typeof vi.fn>;
  let onDelete: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
    onPublish = vi.fn();
    onDelete = vi.fn();
    vi.clearAllMocks();
  });

  const defaultProps = () => ({
    form,
    updateField,
    loading: false,
    saving: false,
    dirty: false,
    onPublish,
    onDelete,
    hasAssistant: true,
    assistantId: 'ast-1',
  });

  it('shows empty state "Select an assistant" when hasAssistant=false', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} hasAssistant={false} />,
    );
    expect(screen.getByText('Select an assistant')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading=true', () => {
    const { container } = render(
      <AssistantEditorPanel {...defaultProps()} loading={true} />,
    );
    // Skeleton elements are rendered as div with specific classes
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders assistant name when loaded', () => {
    const namedForm = { ...form, name: 'Sales Bot' };
    render(
      <AssistantEditorPanel {...defaultProps()} form={namedForm} />,
    );
    expect(screen.getByText('Sales Bot')).toBeInTheDocument();
  });

  it('shows "Untitled Assistant" when name is empty', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} />,
    );
    expect(screen.getByText('Untitled Assistant')).toBeInTheDocument();
  });

  it('shows "Unsaved changes" badge when dirty=true', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} dirty={true} />,
    );
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });

  it('renders Publish button disabled when not dirty', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} dirty={false} />,
    );
    const publishBtn = screen.getByRole('button', { name: /publish/i });
    expect(publishBtn).toBeDisabled();
  });

  it('renders all 5 tab triggers', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} />,
    );
    expect(screen.getByRole('tab', { name: /model/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /transcriber/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /voice/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /functions/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /advanced/i })).toBeInTheDocument();
  });

  it('calls onPublish when Publish clicked and dirty', async () => {
    const { user } = render(
      <AssistantEditorPanel {...defaultProps()} dirty={true} />,
    );
    const publishBtn = screen.getByRole('button', { name: /publish/i });
    await user.click(publishBtn);
    expect(onPublish).toHaveBeenCalledTimes(1);
  });

  it('calls onDelete when delete button clicked', async () => {
    const { user, container } = render(
      <AssistantEditorPanel {...defaultProps()} />,
    );
    // The delete button is the icon-only ghost button in the header area
    // It has class text-muted-foreground hover:text-destructive and is an icon button
    const allButtons = container.querySelectorAll('button');
    // The delete button is the icon button before Publish — it has no text content
    const deleteBtn = Array.from(allButtons).find(
      (btn) => btn.classList.contains('hover:text-destructive') ||
               (btn.querySelector('svg') && btn.textContent?.trim() === '' && !btn.disabled),
    );
    expect(deleteBtn).toBeDefined();
    await user.click(deleteBtn!);
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('enables name editing when clicked and saves on Enter key', async () => {
    const namedForm = { ...form, name: 'My Bot' };
    const { user } = render(
      <AssistantEditorPanel {...defaultProps()} form={namedForm} />,
    );

    // Click on the name button to start editing
    const nameBtn = screen.getByText('My Bot');
    await user.click(nameBtn);

    // Should now show an input
    const input = screen.getByDisplayValue('My Bot');
    expect(input).toBeInTheDocument();

    // Press Enter to save
    await user.keyboard('{Enter}');

    // Should go back to button mode
    expect(screen.getByText('My Bot')).toBeInTheDocument();
  });

  it('cancels name editing on Escape key', async () => {
    const namedForm = { ...form, name: 'My Bot' };
    const { user } = render(
      <AssistantEditorPanel {...defaultProps()} form={namedForm} />,
    );

    // Click to start editing
    await user.click(screen.getByText('My Bot'));

    // Should show input
    const input = screen.getByDisplayValue('My Bot');
    expect(input).toBeInTheDocument();

    // Press Escape to cancel
    await user.keyboard('{Escape}');

    // Should go back to button mode
    expect(screen.getByText('My Bot')).toBeInTheDocument();
  });

  it('stops editing name on blur', async () => {
    const namedForm = { ...form, name: 'My Bot' };
    const { user } = render(
      <AssistantEditorPanel {...defaultProps()} form={namedForm} />,
    );

    // Click to start editing
    await user.click(screen.getByText('My Bot'));

    const input = screen.getByDisplayValue('My Bot');
    expect(input).toBeInTheDocument();

    // Click somewhere else to blur
    await user.click(document.body);

    // Should go back to display mode
    await waitFor(() => {
      expect(screen.getByText('My Bot')).toBeInTheDocument();
    });
  });

  it('shows "Publishing..." text when saving', () => {
    render(
      <AssistantEditorPanel {...defaultProps()} saving={true} dirty={true} />,
    );
    expect(screen.getByText('Publishing...')).toBeInTheDocument();
  });

  it('updates name field when editing', async () => {
    const namedForm = { ...form, name: 'My Bot' };
    const { user } = render(
      <AssistantEditorPanel {...defaultProps()} form={namedForm} />,
    );

    // Click to start editing
    await user.click(screen.getByText('My Bot'));

    const input = screen.getByDisplayValue('My Bot');
    await user.type(input, ' v2');

    expect(updateField).toHaveBeenCalledWith('name', expect.any(String));
  });
});
