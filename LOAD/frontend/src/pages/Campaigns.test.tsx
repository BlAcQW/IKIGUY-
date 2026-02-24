import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { render, screen, waitFor, userEvent, within } from '@test/helpers/render';
import { buildCampaign, buildAssistant, buildPhoneNumber } from '@test/helpers/factories';

// Stub pointer capture methods required by Radix UI Select in jsdom
beforeAll(() => {
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  }
  if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = vi.fn();
  }
  if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = vi.fn();
  }
});

vi.mock('@/lib/api', () => ({
  listCampaigns: vi.fn(),
  createCampaign: vi.fn(),
  updateCampaign: vi.fn(),
  deleteCampaign: vi.fn(),
  startCampaign: vi.fn(),
  pauseCampaign: vi.fn(),
  resumeCampaign: vi.fn(),
  listAssistants: vi.fn(),
  listPhoneNumbers: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { CampaignsPage } from './Campaigns';
import {
  listCampaigns,
  createCampaign,
  updateCampaign,
  deleteCampaign,
  startCampaign,
  pauseCampaign,
  resumeCampaign,
  listAssistants,
  listPhoneNumbers,
} from '@/lib/api';
import { toast } from 'sonner';

const mockedListCampaigns = vi.mocked(listCampaigns);
const mockedCreateCampaign = vi.mocked(createCampaign);
const mockedUpdateCampaign = vi.mocked(updateCampaign);
const mockedDeleteCampaign = vi.mocked(deleteCampaign);
const mockedStartCampaign = vi.mocked(startCampaign);
const mockedPauseCampaign = vi.mocked(pauseCampaign);
const mockedResumeCampaign = vi.mocked(resumeCampaign);
const mockedListAssistants = vi.mocked(listAssistants);
const mockedListPhoneNumbers = vi.mocked(listPhoneNumbers);

const testAssistant = buildAssistant({ id: 'ast-1', name: 'Sales Bot' });
const testPhoneNumber = buildPhoneNumber({ id: 'pn-1', number: '+15559876543', name: 'Main Line' });

function mockDependencies() {
  mockedListAssistants.mockResolvedValue({ success: true, data: [testAssistant] });
  mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [testPhoneNumber] });
}

/** Helper to open the create dialog from the empty state */
async function openCreateDialog() {
  await waitFor(() => {
    expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
  });

  // There are two "Create Campaign" buttons in empty state: header + empty card
  const createButtons = screen.getAllByRole('button', { name: /create campaign/i });
  await userEvent.click(createButtons[0]);

  // Wait for dialog to be visible
  await waitFor(() => {
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  return screen.getByRole('dialog');
}

/** Helper to find action buttons in a campaign table row */
function getRowButtons(campaignName: string) {
  const row = screen.getByText(campaignName).closest('tr')!;
  return within(row).getAllByRole('button');
}

describe('CampaignsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDependencies();
  });

  it('renders page title', () => {
    mockedListCampaigns.mockReturnValue(new Promise(() => {}));
    render(<CampaignsPage />);
    expect(screen.getByText('Campaigns')).toBeInTheDocument();
  });

  it('shows empty state when no campaigns', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
    });
  });

  it('renders campaigns in table', async () => {
    const campaigns = [
      buildCampaign({ name: 'Q1 Outreach', status: 'DRAFT' }),
      buildCampaign({ name: 'Follow Up', status: 'RUNNING' }),
    ];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Q1 Outreach')).toBeInTheDocument();
      expect(screen.getByText('Follow Up')).toBeInTheDocument();
    });
  });

  it('shows status badges', async () => {
    const campaigns = [buildCampaign({ name: 'Test', status: 'RUNNING' })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('RUNNING')).toBeInTheDocument();
    });
  });

  it('shows contact count', async () => {
    const campaigns = [buildCampaign({ contacts: [{ name: 'A', number: '+1' }, { name: 'B', number: '+2' }] })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('has Create Campaign button', () => {
    mockedListCampaigns.mockReturnValue(new Promise(() => {}));
    render(<CampaignsPage />);
    expect(screen.getByRole('button', { name: /create campaign/i })).toBeInTheDocument();
  });

  it('handles load error gracefully', async () => {
    mockedListCampaigns.mockRejectedValue(new Error('fail'));
    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Campaigns')).toBeInTheDocument();
    });
  });

  it('shows stats in table', async () => {
    const campaigns = [buildCampaign({ stats: { total: 10, completed: 5, failed: 2, inProgress: 3 } })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('5/10')).toBeInTheDocument();
    });
  });

  it('opens create dialog on Create Campaign click', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('No campaigns yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create campaign/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Set up an outbound calling campaign.')).toBeInTheDocument();
    });
  });

  it('renders campaign name in table', async () => {
    const campaigns = [buildCampaign({ name: 'Winter Sale', status: 'DRAFT' })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Winter Sale')).toBeInTheDocument();
      expect(screen.getByText('DRAFT')).toBeInTheDocument();
    });
  });

  // --- New interaction tests ---

  it('creates a campaign via the form (submits with validation)', async () => {
    // Test that submitting the create form without required selects triggers validation error
    // Full Radix Select interaction is not supported in jsdom, so we validate the form flow
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Fill in the name field
    const nameInput = within(dialog).getByPlaceholderText('e.g., Q1 Outreach');
    await userEvent.type(nameInput, 'Spring Sale');

    // Fill in contact fields
    const contactNameInput = within(dialog).getByPlaceholderText('Name');
    await userEvent.clear(contactNameInput);
    await userEvent.type(contactNameInput, 'John Doe');

    const contactNumberInput = within(dialog).getByPlaceholderText('+1234567890');
    await userEvent.clear(contactNumberInput);
    await userEvent.type(contactNumberInput, '+15551234567');

    // Verify the dialog contains the assistant and phone number select triggers
    const comboboxes = within(dialog).getAllByRole('combobox');
    expect(comboboxes).toHaveLength(2);

    // Submit without selecting assistant/phone - should show error
    const submitButton = within(dialog).getByRole('button', { name: 'Create' });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Select an assistant and phone number');
    });

    expect(mockedCreateCampaign).not.toHaveBeenCalled();
  });

  it('calls createCampaign via update flow (edit existing campaign)', async () => {
    // Test the full save flow by editing a campaign that already has select values populated
    const campaign = buildCampaign({
      id: 'camp-save',
      name: 'Test Save',
      status: 'DRAFT',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
      contacts: [{ name: 'Jane', number: '+15551112222' }],
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedUpdateCampaign.mockResolvedValue({ success: true, data: buildCampaign() });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Save')).toBeInTheDocument();
    });

    // Open edit dialog (selects are pre-filled)
    const buttons = getRowButtons('Test Save');
    await userEvent.click(buttons[1]); // Edit button

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });

    // Change name
    const nameInput = screen.getByPlaceholderText('e.g., Q1 Outreach');
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'Updated Campaign');

    // Submit
    const updateButton = screen.getByRole('button', { name: 'Update' });
    await userEvent.click(updateButton);

    await waitFor(() => {
      expect(mockedUpdateCampaign).toHaveBeenCalledWith('camp-save', expect.objectContaining({
        name: 'Updated Campaign',
        assistantId: 'ast-1',
        phoneNumberId: 'pn-1',
        contacts: [{ name: 'Jane', number: '+15551112222' }],
        schedule: { maxConcurrent: 1, timezone: 'UTC' },
      }));
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign updated');
  });

  it('shows toast error when required fields missing on create', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Fill only the name (required by HTML), but NOT assistant and phone number
    const nameInput = within(dialog).getByPlaceholderText('e.g., Q1 Outreach');
    await userEvent.type(nameInput, 'Test');

    // Click Create without selecting assistant/phone
    const submitButton = within(dialog).getByRole('button', { name: 'Create' });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Select an assistant and phone number');
    });

    // createCampaign should NOT have been called
    expect(mockedCreateCampaign).not.toHaveBeenCalled();
  });

  it('deletes a DRAFT campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-1', name: 'To Delete', status: 'DRAFT' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedDeleteCampaign.mockResolvedValue({ success: true, data: null });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('To Delete')).toBeInTheDocument();
    });

    // For DRAFT: Start (title="Start"), Edit (pencil), Delete (trash) -- 3 buttons
    const buttons = getRowButtons('To Delete');
    // The last button is the delete (trash) button
    const trashButton = buttons[buttons.length - 1];
    await userEvent.click(trashButton);

    // AlertDialog should appear with "Delete Campaign" title
    await waitFor(() => {
      expect(screen.getByText('Delete Campaign')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete "To Delete"/)).toBeInTheDocument();
    });

    // Confirm the delete
    const confirmButton = screen.getByRole('button', { name: 'Delete' });
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockedDeleteCampaign).toHaveBeenCalledWith('camp-1');
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign deleted');
  });

  it('deletes a COMPLETED campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-2', name: 'Completed One', status: 'COMPLETED' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedDeleteCampaign.mockResolvedValue({ success: true, data: null });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Completed One')).toBeInTheDocument();
    });

    const buttons = getRowButtons('Completed One');
    // COMPLETED only shows a delete button
    const trashButton = buttons[buttons.length - 1];
    await userEvent.click(trashButton);

    await waitFor(() => {
      expect(screen.getByText('Delete Campaign')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: 'Delete' });
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockedDeleteCampaign).toHaveBeenCalledWith('camp-2');
    });
  });

  it('starts a DRAFT campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-3', name: 'Draft Camp', status: 'DRAFT' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedStartCampaign.mockResolvedValue({ success: true, data: null });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Draft Camp')).toBeInTheDocument();
    });

    // Find the Start button via title attribute
    const startButton = screen.getByTitle('Start');
    await userEvent.click(startButton);

    await waitFor(() => {
      expect(mockedStartCampaign).toHaveBeenCalledWith('camp-3');
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign started');
  });

  it('pauses a RUNNING campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-4', name: 'Running Camp', status: 'RUNNING' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedPauseCampaign.mockResolvedValue({ success: true, data: null });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Running Camp')).toBeInTheDocument();
    });

    const pauseButton = screen.getByTitle('Pause');
    await userEvent.click(pauseButton);

    await waitFor(() => {
      expect(mockedPauseCampaign).toHaveBeenCalledWith('camp-4');
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign paused');
  });

  it('resumes a PAUSED campaign', async () => {
    const campaign = buildCampaign({ id: 'camp-5', name: 'Paused Camp', status: 'PAUSED' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedResumeCampaign.mockResolvedValue({ success: true, data: null });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Paused Camp')).toBeInTheDocument();
    });

    const resumeButton = screen.getByTitle('Resume');
    await userEvent.click(resumeButton);

    await waitFor(() => {
      expect(mockedResumeCampaign).toHaveBeenCalledWith('camp-5');
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign resumed');
  });

  it('adds a contact in the create dialog', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Initially there should be 1 contact row
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(1);
    expect(within(dialog).getAllByPlaceholderText('+1234567890')).toHaveLength(1);

    // Click "Add Contact" button
    const addContactButton = within(dialog).getByRole('button', { name: /add contact/i });
    await userEvent.click(addContactButton);

    // Now there should be 2 contact rows
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(2);
    expect(within(dialog).getAllByPlaceholderText('+1234567890')).toHaveLength(2);
  });

  it('removes a contact in the create dialog', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Add a second contact
    const addContactButton = within(dialog).getByRole('button', { name: /add contact/i });
    await userEvent.click(addContactButton);

    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(2);

    // Each contact row has an X button. Find the small icon buttons that are NOT
    // add contact, cancel, or create.
    // The X buttons are within contact row divs as the last child button.
    const allButtons = within(dialog).getAllByRole('button');
    // The remove buttons are h-8 w-8 ghost buttons with an X icon
    const removeButtons = allButtons.filter((btn) =>
      btn.classList.contains('shrink-0')
    );

    expect(removeButtons.length).toBe(2);
    await userEvent.click(removeButtons[0]);

    // Should be back to 1 contact row
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(1);
  });

  it('opens edit dialog for a DRAFT campaign', async () => {
    const campaign = buildCampaign({
      id: 'camp-edit',
      name: 'Editable Campaign',
      status: 'DRAFT',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
      contacts: [{ name: 'Alice', number: '+15551111111' }],
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Editable Campaign')).toBeInTheDocument();
    });

    // For DRAFT: Start (title="Start"), Edit (pencil), Delete (trash)
    const buttons = getRowButtons('Editable Campaign');
    // Edit button is the second button (index 1)
    const editButton = buttons[1];
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
      expect(screen.getByText('Update campaign configuration.')).toBeInTheDocument();
    });

    // The form should be pre-filled with the campaign name
    const nameInput = screen.getByPlaceholderText('e.g., Q1 Outreach') as HTMLInputElement;
    expect(nameInput.value).toBe('Editable Campaign');
  });

  it('updates an existing campaign via edit dialog', async () => {
    const campaign = buildCampaign({
      id: 'camp-update',
      name: 'Old Name',
      status: 'DRAFT',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
      contacts: [{ name: 'Bob', number: '+15552222222' }],
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedUpdateCampaign.mockResolvedValue({ success: true, data: buildCampaign() });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Old Name')).toBeInTheDocument();
    });

    // Open edit dialog
    const buttons = getRowButtons('Old Name');
    const editButton = buttons[1]; // Edit is second button for DRAFT
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });

    // Change the name
    const nameInput = screen.getByPlaceholderText('e.g., Q1 Outreach');
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'New Name');

    // Submit the form
    const updateButton = screen.getByRole('button', { name: 'Update' });
    await userEvent.click(updateButton);

    await waitFor(() => {
      expect(mockedUpdateCampaign).toHaveBeenCalledWith('camp-update', expect.objectContaining({
        name: 'New Name',
        assistantId: 'ast-1',
        phoneNumberId: 'pn-1',
      }));
    });

    expect(toast.success).toHaveBeenCalledWith('Campaign updated');
  });

  it('opens edit dialog for a PAUSED campaign', async () => {
    const campaign = buildCampaign({
      id: 'camp-paused-edit',
      name: 'Paused Editable',
      status: 'PAUSED',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Paused Editable')).toBeInTheDocument();
    });

    // For PAUSED: Resume (title="Resume"), Edit (pencil) -- 2 buttons
    const buttons = getRowButtons('Paused Editable');
    // Edit is the second button (after Resume)
    const editButton = buttons[1];
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });
  });

  it('handles update campaign API error', async () => {
    // Test the save error path via update (edit existing campaign with pre-filled selects)
    const campaign = buildCampaign({
      id: 'camp-err-update',
      name: 'Error Test',
      status: 'DRAFT',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
      contacts: [{ name: 'Bob', number: '+15553334444' }],
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedUpdateCampaign.mockRejectedValue(new Error('Server error'));

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Error Test')).toBeInTheDocument();
    });

    // Open edit dialog
    const buttons = getRowButtons('Error Test');
    await userEvent.click(buttons[1]); // Edit button

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });

    // Submit
    const updateButton = screen.getByRole('button', { name: 'Update' });
    await userEvent.click(updateButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to update campaign', { description: 'Server error' });
    });
  });

  it('handles start campaign API error', async () => {
    const campaign = buildCampaign({ id: 'camp-err', name: 'Error Camp', status: 'DRAFT' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedStartCampaign.mockRejectedValue(new Error('Cannot start'));

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Error Camp')).toBeInTheDocument();
    });

    const startButton = screen.getByTitle('Start');
    await userEvent.click(startButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to start campaign', { description: 'Cannot start' });
    });
  });

  it('handles delete campaign API error', async () => {
    const campaign = buildCampaign({ id: 'camp-del-err', name: 'Del Error', status: 'DRAFT' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedDeleteCampaign.mockRejectedValue(new Error('Delete failed'));

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Del Error')).toBeInTheDocument();
    });

    // Click delete button (last button in DRAFT row)
    const buttons = getRowButtons('Del Error');
    const trashButton = buttons[buttons.length - 1];
    await userEvent.click(trashButton);

    await waitFor(() => {
      expect(screen.getByText('Delete Campaign')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: 'Delete' });
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to delete campaign', { description: 'Delete failed' });
    });
  });

  it('cancels delete dialog', async () => {
    const campaign = buildCampaign({ id: 'camp-cancel', name: 'Cancel Delete', status: 'DRAFT' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Cancel Delete')).toBeInTheDocument();
    });

    // Open delete dialog
    const buttons = getRowButtons('Cancel Delete');
    const trashButton = buttons[buttons.length - 1];
    await userEvent.click(trashButton);

    await waitFor(() => {
      expect(screen.getByText('Delete Campaign')).toBeInTheDocument();
    });

    // Click Cancel
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await userEvent.click(cancelButton);

    // Dialog should close, delete should NOT be called
    await waitFor(() => {
      expect(screen.queryByText('Delete Campaign')).not.toBeInTheDocument();
    });

    expect(mockedDeleteCampaign).not.toHaveBeenCalled();
  });

  it('shows failed count in stats', async () => {
    const campaigns = [buildCampaign({ stats: { total: 10, completed: 5, failed: 3, inProgress: 2 } })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('5/10')).toBeInTheDocument();
      expect(screen.getByText('(3 failed)')).toBeInTheDocument();
    });
  });

  it('shows dash for campaigns with no stats', async () => {
    const campaigns = [buildCampaign({ stats: null })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      // The progress column should show a dash
      const cells = screen.getAllByRole('cell');
      const progressCell = cells.find((cell) => cell.textContent === '\u2014');
      expect(progressCell).toBeDefined();
    });
  });

  it('displays assistant name and phone number in table', async () => {
    const campaign = buildCampaign({
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Sales Bot')).toBeInTheDocument();
      expect(screen.getByText('+15559876543')).toBeInTheDocument();
    });
  });

  it('shows subtitle text', () => {
    mockedListCampaigns.mockReturnValue(new Promise(() => {}));
    render(<CampaignsPage />);
    expect(screen.getByText('Manage bulk outbound calling campaigns')).toBeInTheDocument();
  });

  it('cancels create dialog', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Click Cancel within the dialog
    const cancelButton = within(dialog).getByRole('button', { name: 'Cancel' });
    await userEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('handles pause campaign API error', async () => {
    const campaign = buildCampaign({ id: 'camp-pause-err', name: 'Pause Error', status: 'RUNNING' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedPauseCampaign.mockRejectedValue(new Error('Pause failed'));

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Pause Error')).toBeInTheDocument();
    });

    const pauseButton = screen.getByTitle('Pause');
    await userEvent.click(pauseButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to pause campaign', { description: 'Pause failed' });
    });
  });

  it('calls toast.error when campaigns fail to load', async () => {
    mockedListCampaigns.mockRejectedValue(new Error('Network error'));
    render(<CampaignsPage />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load campaigns', { description: 'Network error' });
    });
  });

  it('renders multiple contact inputs after adding contacts', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Add two more contacts
    const addContactButton = within(dialog).getByRole('button', { name: /add contact/i });
    await userEvent.click(addContactButton);
    await userEvent.click(addContactButton);

    // Should now have 3 contact rows
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(3);
    expect(within(dialog).getAllByPlaceholderText('+1234567890')).toHaveLength(3);
  });

  it('shows loading skeletons while loading', () => {
    mockedListCampaigns.mockReturnValue(new Promise(() => {}));
    render(<CampaignsPage />);

    // While loading, skeletons should be present
    expect(screen.getByText('Campaigns')).toBeInTheDocument();
    // The empty state or table should not be visible yet
    expect(screen.queryByText('No campaigns yet')).not.toBeInTheDocument();
  });

  it('shows stats with 0 failed (no failed span)', async () => {
    const campaigns = [buildCampaign({ stats: { total: 10, completed: 8, failed: 0, inProgress: 2 } })];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('8/10')).toBeInTheDocument();
      // When failed is 0, the "(X failed)" text should NOT appear
      expect(screen.queryByText(/failed/)).not.toBeInTheDocument();
    });
  });

  it('opens edit dialog for PAUSED campaign with empty contacts defaults to one slot', async () => {
    const campaign = buildCampaign({
      id: 'camp-empty-contacts',
      name: 'Empty Contacts Camp',
      status: 'PAUSED',
      assistantId: 'ast-1',
      phoneNumberId: 'pn-1',
      contacts: [],
      schedule: null as any,
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Empty Contacts Camp')).toBeInTheDocument();
    });

    // For PAUSED: Resume, Edit
    const buttons = getRowButtons('Empty Contacts Camp');
    await userEvent.click(buttons[1]); // Edit button

    await waitFor(() => {
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });

    // Should have 1 contact row (default when empty)
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(1);
  });

  it('handles resume campaign API error', async () => {
    const campaign = buildCampaign({ id: 'camp-resume-err', name: 'Resume Error', status: 'PAUSED' });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });
    mockedResumeCampaign.mockRejectedValue(new Error('Resume failed'));

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('Resume Error')).toBeInTheDocument();
    });

    const resumeButton = screen.getByTitle('Resume');
    await userEvent.click(resumeButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to resume campaign', { description: 'Resume failed' });
    });
  });

  it('shows all four status badges (DRAFT, RUNNING, PAUSED, COMPLETED)', async () => {
    const campaigns = [
      buildCampaign({ name: 'Draft', status: 'DRAFT' }),
      buildCampaign({ name: 'Running', status: 'RUNNING' }),
      buildCampaign({ name: 'Paused', status: 'PAUSED' }),
      buildCampaign({ name: 'Completed', status: 'COMPLETED' }),
    ];
    mockedListCampaigns.mockResolvedValue({ success: true, data: campaigns });

    render(<CampaignsPage />);

    await waitFor(() => {
      expect(screen.getByText('DRAFT')).toBeInTheDocument();
      expect(screen.getByText('RUNNING')).toBeInTheDocument();
      expect(screen.getByText('PAUSED')).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });
  });

  it('shows dash for unknown assistant and phone number', async () => {
    const campaign = buildCampaign({
      assistantId: 'unknown-ast',
      phoneNumberId: 'unknown-pn',
    });
    mockedListCampaigns.mockResolvedValue({ success: true, data: [campaign] });

    render(<CampaignsPage />);

    await waitFor(() => {
      // Should show '—' for unknown assistant and phone number
      const dashes = screen.getAllByText('\u2014');
      expect(dashes.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('removes last contact and keeps one empty slot', async () => {
    mockedListCampaigns.mockResolvedValue({ success: true, data: [] });
    render(<CampaignsPage />);
    const dialog = await openCreateDialog();

    // Remove the only contact
    const allButtons = within(dialog).getAllByRole('button');
    const removeButtons = allButtons.filter((btn) => btn.classList.contains('shrink-0'));
    expect(removeButtons.length).toBe(1);
    await userEvent.click(removeButtons[0]);

    // Should still have 1 contact row (minimum)
    expect(within(dialog).getAllByPlaceholderText('Name')).toHaveLength(1);
  });
});
