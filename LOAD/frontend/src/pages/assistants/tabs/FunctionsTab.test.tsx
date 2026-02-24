import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';
import type { AssistantForm } from '../hooks/useAssistantEditor';
import { DEFAULT_FORM } from '../hooks/useAssistantEditor';
import { buildTool } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  getAssistantTools: vi.fn(),
  attachToolToAssistant: vi.fn(),
  detachToolFromAssistant: vi.fn(),
  listTools: vi.fn(),
  listToolTemplates: vi.fn(),
  createToolFromTemplate: vi.fn(),
}));

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

import { FunctionsTab } from './FunctionsTab';
import {
  getAssistantTools,
  attachToolToAssistant,
  detachToolFromAssistant,
  listTools,
  listToolTemplates,
  createToolFromTemplate,
} from '@/lib/api';
import { toast } from 'sonner';

const mockedGetAssistantTools = vi.mocked(getAssistantTools);
const mockedAttachToolToAssistant = vi.mocked(attachToolToAssistant);
const mockedDetachToolFromAssistant = vi.mocked(detachToolFromAssistant);
const mockedListTools = vi.mocked(listTools);
const mockedListToolTemplates = vi.mocked(listToolTemplates);
const mockedCreateToolFromTemplate = vi.mocked(createToolFromTemplate);
const mockedToast = vi.mocked(toast);

describe('FunctionsTab', () => {
  let form: AssistantForm;
  let updateField: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    form = { ...DEFAULT_FORM };
    updateField = vi.fn();
    vi.clearAllMocks();
  });

  it('renders End Call section heading', () => {
    render(<FunctionsTab form={form} updateField={updateField} />);
    expect(screen.getByText('End Call')).toBeInTheDocument();
  });

  it('renders endCallMessage input', () => {
    render(<FunctionsTab form={form} updateField={updateField} />);
    expect(screen.getByPlaceholderText('Thank you for calling. Goodbye!')).toBeInTheDocument();
  });

  it('renders endCallPhrases input', () => {
    render(<FunctionsTab form={form} updateField={updateField} />);
    expect(screen.getByPlaceholderText('goodbye, bye, end call, hang up')).toBeInTheDocument();
  });

  it('shows "Save assistant first" when no assistantId', () => {
    render(<FunctionsTab form={form} updateField={updateField} />);
    expect(screen.getByText('Save assistant first')).toBeInTheDocument();
  });

  it('shows "No tools attached" with assistantId and empty tools', async () => {
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    render(<FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />);

    await waitFor(() => {
      expect(screen.getByText('No tools attached')).toBeInTheDocument();
    });
  });

  it('renders attached tools list', async () => {
    const tools = [
      buildTool({ name: 'check_availability', type: 'FUNCTION' }),
      buildTool({ name: 'end_call_tool', type: 'END_CALL' }),
    ];
    mockedGetAssistantTools.mockResolvedValue({ data: tools });
    render(<FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />);

    await waitFor(() => {
      expect(screen.getByText('check_availability')).toBeInTheDocument();
      expect(screen.getByText('end_call_tool')).toBeInTheDocument();
    });
  });

  it('shows Add Tool button when assistantId provided', async () => {
    mockedGetAssistantTools.mockResolvedValue({ data: [] });
    render(<FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add tool/i })).toBeInTheDocument();
    });
  });

  it('typing in endCallMessage calls updateField', async () => {
    const { user } = render(<FunctionsTab form={form} updateField={updateField} />);
    const input = screen.getByPlaceholderText('Thank you for calling. Goodbye!');
    await user.type(input, 'See you!');
    expect(updateField).toHaveBeenCalledWith('endCallMessage', expect.any(String));
  });

  it('typing in endCallPhrases calls updateField', async () => {
    const { user } = render(<FunctionsTab form={form} updateField={updateField} />);
    const input = screen.getByPlaceholderText('goodbye, bye, end call, hang up');
    await user.type(input, 'ciao');
    expect(updateField).toHaveBeenCalledWith('endCallPhrases', expect.any(String));
  });

  // ─── ToolPickerDialog Tests ──────────────────────────────────────────

  describe('ToolPickerDialog', () => {
    beforeEach(() => {
      mockedGetAssistantTools.mockResolvedValue({ data: [] });
    });

    /** Helper: waits for load to finish, then clicks the first "Add Tool" button. */
    async function openToolPicker(user: ReturnType<typeof import('@testing-library/user-event').default.setup>) {
      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /add tool/i }).length).toBeGreaterThan(0);
      });
      // Click the first "Add Tool" button (header button)
      await user.click(screen.getAllByRole('button', { name: /add tool/i })[0]);
      await waitFor(() => {
        expect(screen.getByText('Existing Tool')).toBeInTheDocument();
      });
    }

    it('opens tool picker and shows choose view', async () => {
      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);

      expect(screen.getByText('Existing Tool')).toBeInTheDocument();
      expect(screen.getByText('From Template')).toBeInTheDocument();
    });

    it('shows existing tools list when clicking Existing Tool', async () => {
      const tool = buildTool({ id: 'tool-1', name: 'My Tool' });
      mockedListTools.mockResolvedValue({ success: true, data: [tool] });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('My Tool')).toBeInTheDocument();
      });
    });

    it('calls attachToolToAssistant when clicking an existing tool', async () => {
      const tool = buildTool({ id: 'tool-1', name: 'My Tool' });
      mockedListTools.mockResolvedValue({ success: true, data: [tool] });
      mockedAttachToolToAssistant.mockResolvedValue({ success: true, data: {} as never });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('My Tool')).toBeInTheDocument();
      });

      await user.click(screen.getByText('My Tool'));

      await waitFor(() => {
        expect(mockedAttachToolToAssistant).toHaveBeenCalledWith('ast-1', 'tool-1');
      });
    });

    it('shows template view when clicking From Template', async () => {
      mockedListToolTemplates.mockResolvedValue({
        data: {
          categories: { scheduling: 'Scheduling', crm: 'CRM' } as never,
          templates: {
            scheduling: [
              {
                name: 'Check Availability',
                description: 'Check calendar',
                type: 'FUNCTION' as const,
                category: 'scheduling' as const,
                function: {
                  name: 'check_availability',
                  description: 'Check availability',
                  parameters: { type: 'object', properties: { date: { type: 'string' } } },
                },
              },
            ],
            crm: [],
          } as never,
        },
      });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('From Template'));

      await waitFor(() => {
        expect(screen.getByText('Create from Template')).toBeInTheDocument();
      });
    });

    it('detaches tool when clicking trash button on attached tool', async () => {
      const tool = buildTool({ id: 'tool-detach', name: 'Detachable Tool' });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });
      mockedDetachToolFromAssistant.mockResolvedValue({ success: true, data: {} as never });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('Detachable Tool')).toBeInTheDocument();
      });

      // The trash button is an icon-only button in the tool row
      const buttons = screen.getAllByRole('button');
      // Find the icon-only button (trash) - it has no text content
      const trashButton = buttons.find((b) => b.textContent === '');
      expect(trashButton).toBeDefined();
      await user.click(trashButton!);

      await waitFor(() => {
        expect(mockedDetachToolFromAssistant).toHaveBeenCalledWith('ast-1', 'tool-detach');
      });
    });

    it('shows "No available tools" when existing tools list is empty', async () => {
      mockedListTools.mockResolvedValue({ success: true, data: [] });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('No available tools')).toBeInTheDocument();
      });
    });

    it('handles getAssistantTools rejection without crashing', async () => {
      mockedGetAssistantTools.mockRejectedValue(new Error('Network error'));

      render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      // Should not crash; after the error, it should fall into the empty tools state
      await waitFor(() => {
        expect(screen.getByText('No tools attached')).toBeInTheDocument();
      });
    });

    it('shows error toast when detach fails', async () => {
      const tool = buildTool({ id: 'tool-fail-detach', name: 'Fail Detach' });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });
      mockedDetachToolFromAssistant.mockRejectedValue(new Error('Detach error'));

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('Fail Detach')).toBeInTheDocument();
      });

      const buttons = screen.getAllByRole('button');
      const trashButton = buttons.find((b) => b.textContent === '');
      await user.click(trashButton!);

      await waitFor(() => {
        expect(mockedToast.error).toHaveBeenCalledWith('Failed to remove tool', expect.objectContaining({ description: 'Detach error' }));
      });
    });

    it('shows error toast when attach existing tool fails', async () => {
      const tool = buildTool({ id: 'tool-fail-attach', name: 'Fail Attach Tool' });
      mockedListTools.mockResolvedValue({ success: true, data: [tool] });
      mockedAttachToolToAssistant.mockRejectedValue(new Error('Attach error'));

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('Fail Attach Tool')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Fail Attach Tool'));

      await waitFor(() => {
        expect(mockedToast.error).toHaveBeenCalledWith('Failed to attach tool', expect.objectContaining({ description: 'Attach error' }));
      });
    });

    it('renders attached tool with TRANSFER_CALL type badge', async () => {
      const tool = buildTool({ id: 'tool-transfer', name: 'Transfer Tool', type: 'TRANSFER_CALL' });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });

      render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('Transfer Tool')).toBeInTheDocument();
        expect(screen.getByText('Transfer')).toBeInTheDocument();
      });
    });

    it('renders attached tool with END_CALL type badge', async () => {
      const tool = buildTool({ id: 'tool-end', name: 'End Tool', type: 'END_CALL', description: null });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });

      render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('End Tool')).toBeInTheDocument();
        // 'End Call' badge text
        expect(screen.getAllByText('End Call').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('shows error toast when loading tools for picker fails', async () => {
      mockedListTools.mockRejectedValue(new Error('Load error'));

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(mockedToast.error).toHaveBeenCalledWith('Failed to load tools');
      });
    });

    it('shows error toast when loading templates fails', async () => {
      mockedListToolTemplates.mockRejectedValue(new Error('Templates error'));

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('From Template'));

      await waitFor(() => {
        expect(mockedToast.error).toHaveBeenCalledWith('Failed to load templates');
      });
    });

    it('renders tool with description in attached list', async () => {
      const tool = buildTool({ id: 'tool-desc', name: 'Desc Tool', description: 'A great tool' });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });

      render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('Desc Tool')).toBeInTheDocument();
        expect(screen.getByText('A great tool')).toBeInTheDocument();
      });
    });

    it('renders tool without function property', async () => {
      const tool = buildTool({ id: 'tool-nofn', name: 'No Fn Tool', type: 'END_CALL', function: null as any, description: null });
      mockedGetAssistantTools.mockResolvedValue({ data: [tool] });

      render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('No Fn Tool')).toBeInTheDocument();
      });
    });

    it('clicks Back button in existing tools view to return to choose view', async () => {
      mockedListTools.mockResolvedValue({ success: true, data: [] });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('No available tools')).toBeInTheDocument();
      });

      // Click Back button to return to choose view
      const backBtn = screen.getByRole('button', { name: /back/i });
      await user.click(backBtn);

      await waitFor(() => {
        expect(screen.getByText('Existing Tool')).toBeInTheDocument();
        expect(screen.getByText('From Template')).toBeInTheDocument();
      });
    });

    it('clicks Back button in templates view to return to choose view', async () => {
      mockedListToolTemplates.mockResolvedValue({
        data: {
          categories: { scheduling: 'Scheduling' } as never,
          templates: { scheduling: [] } as never,
        },
      });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('From Template'));

      await waitFor(() => {
        expect(screen.getByText('Create from Template')).toBeInTheDocument();
      });

      // Click Back button to return to choose view
      const backBtn = screen.getByRole('button', { name: /back/i });
      await user.click(backBtn);

      await waitFor(() => {
        expect(screen.getByText('Existing Tool')).toBeInTheDocument();
        expect(screen.getByText('From Template')).toBeInTheDocument();
      });
    });

    it('shows tool description in existing tools picker', async () => {
      const tool = buildTool({ id: 'tool-desc-2', name: 'Described Tool', description: 'A described tool' });
      mockedListTools.mockResolvedValue({ success: true, data: [tool] });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await openToolPicker(user);
      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        expect(screen.getByText('A described tool')).toBeInTheDocument();
      });
    });

    it('filters out already-attached tools from existing tools picker', async () => {
      const attachedTool = buildTool({ id: 'attached-1', name: 'Attached' });
      const availableTool = buildTool({ id: 'available-1', name: 'Available' });
      mockedGetAssistantTools.mockResolvedValue({ data: [attachedTool] });
      mockedListTools.mockResolvedValue({ success: true, data: [attachedTool, availableTool] });

      const { user } = render(
        <FunctionsTab form={form} updateField={updateField} assistantId="ast-1" />,
      );

      await waitFor(() => {
        expect(screen.getByText('Attached')).toBeInTheDocument();
      });

      // Open the tool picker from header Add Tool button
      const addButtons = screen.getAllByRole('button', { name: /add tool/i });
      await user.click(addButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Existing Tool')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Existing Tool'));

      await waitFor(() => {
        // Only Available should be shown, not Attached
        expect(screen.getByText('Available')).toBeInTheDocument();
      });
    });
  });
});
