import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, userEvent } from '@test/helpers/render';
import { buildPhoneNumber, buildAssistant } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listPhoneNumbers: vi.fn(),
  searchPhoneNumbers: vi.fn(),
  purchasePhoneNumber: vi.fn(),
  createSipNumber: vi.fn(),
  createGoipNumber: vi.fn(),
  updatePhoneNumber: vi.fn(),
  deletePhoneNumber: vi.fn(),
  listAssistants: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

import { PhoneNumbersPage } from './PhoneNumbers';
import { listPhoneNumbers, searchPhoneNumbers, purchasePhoneNumber, createSipNumber, createGoipNumber, updatePhoneNumber, deletePhoneNumber, listAssistants } from '@/lib/api';
import { toast } from 'sonner';

const mockedListPhoneNumbers = vi.mocked(listPhoneNumbers);
const mockedSearchPhoneNumbers = vi.mocked(searchPhoneNumbers);
const mockedPurchasePhoneNumber = vi.mocked(purchasePhoneNumber);
const mockedCreateSipNumber = vi.mocked(createSipNumber);
const mockedCreateGoipNumber = vi.mocked(createGoipNumber);
const mockedUpdatePhoneNumber = vi.mocked(updatePhoneNumber);
const mockedDeletePhoneNumber = vi.mocked(deletePhoneNumber);
const mockedListAssistants = vi.mocked(listAssistants);
const mockedToast = vi.mocked(toast);

describe('PhoneNumbersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedListAssistants.mockResolvedValue({ success: true, data: [buildAssistant()] });
  });

  it('renders page title', () => {
    mockedListPhoneNumbers.mockReturnValue(new Promise(() => {}));
    render(<PhoneNumbersPage />);
    expect(screen.getByText('Phone Numbers')).toBeInTheDocument();
  });

  it('shows empty state when no numbers', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });
  });

  it('renders phone numbers in table', async () => {
    const numbers = [buildPhoneNumber({ number: '+15551234567', name: 'Main Line', provider: 'twilio' })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15551234567')).toBeInTheDocument();
      expect(screen.getByText('Main Line')).toBeInTheDocument();
    });
  });

  it('has Add Number button', () => {
    mockedListPhoneNumbers.mockReturnValue(new Promise(() => {}));
    render(<PhoneNumbersPage />);
    expect(screen.getByRole('button', { name: /add number/i })).toBeInTheDocument();
  });

  it('shows provider badge', async () => {
    const numbers = [buildPhoneNumber({ provider: 'twilio' })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('twilio')).toBeInTheDocument();
    });
  });

  it('handles load error gracefully', async () => {
    mockedListPhoneNumbers.mockRejectedValue(new Error('fail'));
    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('Phone Numbers')).toBeInTheDocument();
    });
  });

  it('opens add number dialog on Add Number click', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);
    await waitFor(() => {
      expect(screen.getByText('Add Phone Number')).toBeInTheDocument();
    });
  });

  it('shows assigned assistant name', async () => {
    const numbers = [buildPhoneNumber({ assistantId: 'a1' })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15551234567')).toBeInTheDocument();
    });
  });

  it('opens add number dialog with search tab showing search form', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Add Phone Number')).toBeInTheDocument();
      expect(screen.getByText('Search & Purchase')).toBeInTheDocument();
      expect(screen.getByText('SIP Trunk')).toBeInTheDocument();
    });

    // Verify search form fields exist
    expect(screen.getByPlaceholderText('US')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('415')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
  });

  it('searches for phone numbers and displays results', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockResolvedValue({
      success: true,
      data: [
        { number: '+14155551234', locality: 'San Francisco', region: 'CA' },
        { number: '+14155555678', locality: 'San Francisco', region: 'CA' },
      ],
    });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    // Click search
    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(mockedSearchPhoneNumbers).toHaveBeenCalledWith(expect.objectContaining({
        country: 'US',
        type: 'local',
        limit: 10,
      }));
      expect(screen.getByText('+14155551234')).toBeInTheDocument();
      expect(screen.getByText('+14155555678')).toBeInTheDocument();
    });
  });

  it('shows error toast when search fails', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockRejectedValue(new Error('Search failed'));

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to search numbers', expect.objectContaining({ description: 'Search failed' }));
    });
  });

  it('opens SIP trunk tab and submits SIP form', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedCreateSipNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ provider: 'SIP_TRUNK' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('SIP Trunk')).toBeInTheDocument();
    });

    // Click the SIP Trunk tab
    await userEvent.click(screen.getByText('SIP Trunk'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+14155551234')).toBeInTheDocument();
    });

    // Fill the SIP form
    await userEvent.type(screen.getByPlaceholderText('+14155551234'), '+12125551234');
    await userEvent.type(screen.getByPlaceholderText('Office Main Line'), 'My SIP Line');
    await userEvent.type(screen.getByPlaceholderText('sip.example.com'), 'sip.mycompany.com');

    // Submit
    const addSipBtn = screen.getByRole('button', { name: /add sip number/i });
    await userEvent.click(addSipBtn);

    await waitFor(() => {
      expect(mockedCreateSipNumber).toHaveBeenCalledWith(expect.objectContaining({
        number: '+12125551234',
        name: 'My SIP Line',
        provider: 'SIP_TRUNK',
        sipDomain: 'sip.mycompany.com',
      }));
    });
  });

  it('shows error toast when SIP creation fails', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedCreateSipNumber.mockRejectedValue(new Error('SIP error'));

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('SIP Trunk')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('SIP Trunk'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+14155551234')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('+14155551234'), '+12125551234');

    await userEvent.click(screen.getByRole('button', { name: /add sip number/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to add SIP number', expect.objectContaining({ description: 'SIP error' }));
    });
  });

  it('deletes phone number after confirmation', async () => {
    const phoneNum = buildPhoneNumber({ number: '+15559876543', name: 'Delete Line' });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [phoneNum] });
    mockedDeletePhoneNumber.mockResolvedValue({ success: true });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15559876543')).toBeInTheDocument();
    });

    // Find the delete button (has hover:text-destructive)
    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn => btn.className.includes('hover:text-destructive'));
    expect(deleteBtn).toBeTruthy();
    await userEvent.click(deleteBtn!);

    // Confirm in alert dialog
    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /^release$/i });
    await userEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockedDeletePhoneNumber).toHaveBeenCalledWith(phoneNum.id);
    });
  });

  it('shows error toast when delete phone number fails', async () => {
    const phoneNum = buildPhoneNumber({ number: '+15559999999' });
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [phoneNum] });
    mockedDeletePhoneNumber.mockRejectedValue(new Error('Release failed'));

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15559999999')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn => btn.className.includes('hover:text-destructive'));
    await userEvent.click(deleteBtn!);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /^release$/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to release number', expect.objectContaining({ description: 'Release failed' }));
    });
  });

  it('displays multiple phone numbers in table', async () => {
    const numbers = [
      buildPhoneNumber({ number: '+15551111111', name: 'Line 1', provider: 'twilio' }),
      buildPhoneNumber({ number: '+15552222222', name: 'Line 2', provider: 'SIP_TRUNK' }),
    ];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15551111111')).toBeInTheDocument();
      expect(screen.getByText('+15552222222')).toBeInTheDocument();
      expect(screen.getByText('Line 1')).toBeInTheDocument();
      expect(screen.getByText('Line 2')).toBeInTheDocument();
    });
  });

  it('shows status badge for phone numbers', async () => {
    const numbers = [buildPhoneNumber({ status: 'active' })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('active')).toBeInTheDocument();
    });
  });

  it('reloads list after successful delete', async () => {
    const phoneNum = buildPhoneNumber({ number: '+15553333333' });
    mockedListPhoneNumbers
      .mockResolvedValueOnce({ success: true, data: [phoneNum] })
      .mockResolvedValueOnce({ success: true, data: [] });
    mockedDeletePhoneNumber.mockResolvedValue({ success: true });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('+15553333333')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn => btn.className.includes('hover:text-destructive'));
    await userEvent.click(deleteBtn!);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /^release$/i }));

    await waitFor(() => {
      expect(mockedListPhoneNumbers).toHaveBeenCalledTimes(2);
    });
  });

  it('shows phone number with no name as --', async () => {
    const numbers = [buildPhoneNumber({ name: null })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('--')).toBeInTheDocument();
    });
  });

  it('shows toast.info when search returns empty results', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockResolvedValue({ success: true, data: [] });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(mockedToast.info).toHaveBeenCalledWith('No numbers found matching your criteria');
    });
  });

  it('shows error toast when purchase fails', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockResolvedValue({
      success: true,
      data: [{ number: '+14155551234', locality: 'San Francisco', region: 'CA' }],
    });
    mockedPurchasePhoneNumber.mockRejectedValue(new Error('Purchase failed'));

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(screen.getByText('+14155551234')).toBeInTheDocument();
    });

    const purchaseBtn = screen.getByRole('button', { name: /^purchase$/i });
    await userEvent.click(purchaseBtn);

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to purchase number', expect.objectContaining({ description: 'Purchase failed' }));
    });
  });

  it('shows error toast on initial load failure with description', async () => {
    mockedListPhoneNumbers.mockRejectedValue(new Error('Connection timeout'));
    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to load phone numbers', expect.objectContaining({ description: 'Connection timeout' }));
    });
  });

  it('shows TWILIO vs SIP_TRUNK badges with correct variants', async () => {
    const numbers = [
      buildPhoneNumber({ number: '+1555twilio', provider: 'TWILIO', status: 'ACTIVE' }),
      buildPhoneNumber({ number: '+1555sip00', provider: 'SIP_TRUNK', status: 'INACTIVE' as any }),
    ];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('TWILIO')).toBeInTheDocument();
      expect(screen.getByText('SIP_TRUNK')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('shows search results with locality and region', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockResolvedValue({
      success: true,
      data: [
        { number: '+14155551234', locality: 'San Francisco', region: 'CA' },
      ],
    });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    });
  });

  it('reloads list after successful SIP creation', async () => {
    mockedListPhoneNumbers
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({ success: true, data: [buildPhoneNumber({ provider: 'SIP_TRUNK' })] });
    mockedCreateSipNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ provider: 'SIP_TRUNK' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('SIP Trunk')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('SIP Trunk'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+14155551234')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('+14155551234'), '+12125559999');
    await userEvent.click(screen.getByRole('button', { name: /add sip number/i }));

    await waitFor(() => {
      expect(mockedListPhoneNumbers).toHaveBeenCalledTimes(2);
    });
  });

  it('purchases a phone number from search results', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedSearchPhoneNumbers.mockResolvedValue({
      success: true,
      data: [{ number: '+14155551234', locality: 'San Francisco', region: 'CA' }],
    });
    mockedPurchasePhoneNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ number: '+14155551234' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    // Open dialog and search
    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(screen.getByText('+14155551234')).toBeInTheDocument();
    });

    // Click Purchase button
    const purchaseBtn = screen.getByRole('button', { name: /^purchase$/i });
    await userEvent.click(purchaseBtn);

    await waitFor(() => {
      expect(mockedPurchasePhoneNumber).toHaveBeenCalledWith({ phoneNumber: '+14155551234' });
    });
  });

  it('opens GoIP tab and submits GoIP form', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedCreateGoipNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ provider: 'GOIP' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('GoIP')).toBeInTheDocument();
    });

    // Click the GoIP tab
    await userEvent.click(screen.getByText('GoIP'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+233241234567')).toBeInTheDocument();
    });

    // Fill the GoIP form
    await userEvent.type(screen.getByPlaceholderText('+233241234567'), '+233201234567');
    await userEvent.type(screen.getByPlaceholderText('Ghana MTN Line 1'), 'My GoIP');
    await userEvent.type(screen.getByPlaceholderText('goip-trunk'), 'trunk-1');

    // Submit
    const addGoipBtn = screen.getByRole('button', { name: /add goip number/i });
    await userEvent.click(addGoipBtn);

    await waitFor(() => {
      expect(mockedCreateGoipNumber).toHaveBeenCalledWith(expect.objectContaining({
        number: '+233201234567',
        name: 'My GoIP',
        provider: 'GOIP',
        trunkName: 'trunk-1',
        country: 'GH',
      }));
    });
  });

  it('shows error toast when GoIP creation fails', async () => {
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: [] });
    mockedCreateGoipNumber.mockRejectedValue(new Error('GoIP error'));

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('GoIP')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('GoIP'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+233241234567')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('+233241234567'), '+233201234567');

    await userEvent.click(screen.getByRole('button', { name: /add goip number/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to add GoIP number', expect.objectContaining({ description: 'GoIP error' }));
    });
  });

  it('shows GOIP provider badge with emerald styling', async () => {
    const numbers = [buildPhoneNumber({ number: '+233201234567', provider: 'GOIP', status: 'ACTIVE' })];
    mockedListPhoneNumbers.mockResolvedValue({ success: true, data: numbers });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('GOIP')).toBeInTheDocument();
    });

    // Verify GOIP badge is displayed
    const goipBadge = screen.getByText('GOIP');
    expect(goipBadge).toBeInTheDocument();
  });

  it('reloads list after successful purchase', async () => {
    mockedListPhoneNumbers
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({ success: true, data: [buildPhoneNumber({ number: '+14155551234' })] });
    mockedSearchPhoneNumbers.mockResolvedValue({
      success: true,
      data: [{ number: '+14155551234', locality: 'San Francisco', region: 'CA' }],
    });
    mockedPurchasePhoneNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ number: '+14155551234' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /search available numbers/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /search available numbers/i }));

    await waitFor(() => {
      expect(screen.getByText('+14155551234')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /^purchase$/i }));

    await waitFor(() => {
      // Initial load + reload after purchase
      expect(mockedListPhoneNumbers).toHaveBeenCalledTimes(2);
    });
  });

  it('reloads list after successful GoIP creation', async () => {
    mockedListPhoneNumbers
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({ success: true, data: [buildPhoneNumber({ provider: 'GOIP' })] });
    mockedCreateGoipNumber.mockResolvedValue({ success: true, data: buildPhoneNumber({ provider: 'GOIP' }) });

    render(<PhoneNumbersPage />);

    await waitFor(() => {
      expect(screen.getByText('No phone numbers')).toBeInTheDocument();
    });

    const addButtons = screen.getAllByRole('button', { name: /add number/i });
    await userEvent.click(addButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('GoIP')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('GoIP'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('+233241234567')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('+233241234567'), '+233201234567');
    await userEvent.click(screen.getByRole('button', { name: /add goip number/i }));

    await waitFor(() => {
      expect(mockedListPhoneNumbers).toHaveBeenCalledTimes(2);
    });
  });
});
