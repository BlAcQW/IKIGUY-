import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, userEvent } from '@test/helpers/render';
import { buildApiKey } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listApiKeys: vi.fn(),
  createApiKey: vi.fn(),
  revokeApiKey: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { SettingsPage } from './Settings';
import { listApiKeys, createApiKey, revokeApiKey } from '@/lib/api';

const mockedListApiKeys = vi.mocked(listApiKeys);
const mockedCreateApiKey = vi.mocked(createApiKey);
const mockedRevokeApiKey = vi.mocked(revokeApiKey);

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    render(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('shows loading skeletons initially', () => {
    mockedListApiKeys.mockReturnValue(new Promise(() => {}));
    render(<SettingsPage />);
    // Skeletons are rendered
    expect(screen.queryByText('No API keys yet')).not.toBeInTheDocument();
  });

  it('shows empty state when no keys', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('No API keys yet')).toBeInTheDocument();
    });
  });

  it('lists API keys', async () => {
    const keys = [
      buildApiKey({ name: 'Production', prefix: 'load_abc' }),
      buildApiKey({ name: 'Staging', prefix: 'load_xyz' }),
    ];
    mockedListApiKeys.mockResolvedValue({ success: true, data: keys });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Production')).toBeInTheDocument();
      expect(screen.getByText('Staging')).toBeInTheDocument();
    });
  });

  it('creates a new API key', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    mockedCreateApiKey.mockResolvedValue({
      success: true,
      data: { ...buildApiKey({ name: 'New Key' }), key: 'load_secret_key_value' },
    });

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/key name/i), 'New Key');
    await user.click(screen.getByRole('button', { name: /create key/i }));

    await waitFor(() => {
      expect(mockedCreateApiKey).toHaveBeenCalledWith({ name: 'New Key' });
    });
  });

  it('shows created key with copy button', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    mockedCreateApiKey.mockResolvedValue({
      success: true,
      data: { ...buildApiKey(), key: 'load_full_secret_key_12345678' },
    });

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/key name/i), 'Test');
    await user.click(screen.getByRole('button', { name: /create key/i }));

    await waitFor(() => {
      expect(screen.getByText(/copy it now/i)).toBeInTheDocument();
    });
  });

  it('renders create key input and button', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /create key/i })).toBeInTheDocument();
  });

  it('shows key prefix in list', async () => {
    const keys = [buildApiKey({ prefix: 'load_abc' })];
    mockedListApiKeys.mockResolvedValue({ success: true, data: keys });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('load_abc...')).toBeInTheDocument();
    });
  });

  it('handles API error when loading keys', async () => {
    mockedListApiKeys.mockRejectedValue(new Error('Server error'));
    render(<SettingsPage />);

    // Should still render the page (shows empty state after error)
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  it('renders API Keys section header', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    render(<SettingsPage />);

    expect(screen.getByText('API Keys')).toBeInTheDocument();
  });

  it('revokes API key with confirmation', async () => {
    const key = buildApiKey({ id: 'key-to-revoke', name: 'Staging Key' });
    mockedListApiKeys.mockResolvedValue({ success: true, data: [key] });
    mockedRevokeApiKey.mockResolvedValue({ success: true, data: undefined as unknown as void });

    const { user } = render(<SettingsPage />);

    // Wait for keys to load
    await waitFor(() => {
      expect(screen.getByText('Staging Key')).toBeInTheDocument();
    });

    // Click the revoke (trash) button on the key row
    const revokeButtons = screen.getAllByRole('button');
    const trashButton = revokeButtons.find((btn) =>
      btn.querySelector('svg.lucide-trash-2') || btn.innerHTML.includes('trash')
    );
    // The trash button is the last button in each key row
    const keyRow = screen.getByText('Staging Key').closest('div[class*="flex items-center justify-between"]');
    const rowRevokeButton = keyRow?.querySelector('button:last-child');
    if (rowRevokeButton) {
      await user.click(rowRevokeButton as HTMLElement);
    }

    // The confirmation dialog should appear
    await waitFor(() => {
      expect(screen.getByText('Revoke API Key')).toBeInTheDocument();
    });

    // Click the Revoke confirm button in the dialog
    await user.click(screen.getByRole('button', { name: /^revoke$/i }));

    await waitFor(() => {
      expect(mockedRevokeApiKey).toHaveBeenCalledWith('key-to-revoke');
    });
  });

  it('copies key to clipboard', async () => {
    // Set up clipboard mock before render
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    if (!navigator.clipboard) {
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: writeTextMock },
        writable: true,
        configurable: true,
      });
    } else {
      vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined);
    }

    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    mockedCreateApiKey.mockResolvedValue({
      success: true,
      data: { ...buildApiKey(), key: 'load_full_secret_key_12345678' },
    });

    const { user, container } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    // Create a key first
    await user.type(screen.getByPlaceholderText(/key name/i), 'Clipboard Test');
    await user.click(screen.getByRole('button', { name: /create key/i }));

    // Wait for the created key banner
    await waitFor(() => {
      expect(screen.getByText(/copy it now/i)).toBeInTheDocument();
    });

    // The key display area has a code element and two icon buttons (eye toggle, copy)
    const codeEl = container.querySelector('code');
    expect(codeEl).toBeTruthy();
    const flexRow = codeEl!.parentElement;
    const buttonsInRow = flexRow!.querySelectorAll('button');
    expect(buttonsInRow.length).toBe(2);
    await user.click(buttonsInRow[1] as HTMLElement);

    // Verify clipboard.writeText was called with the key value
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('load_full_secret_key_12345678');
  });

  it('shows error toast when create key fails', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    mockedCreateApiKey.mockRejectedValue(new Error('Create failed'));

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText(/key name/i), 'Fail Key');
    await user.click(screen.getByRole('button', { name: /create key/i }));

    const { toast } = await import('sonner');
    await waitFor(() => {
      expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to create API key', expect.objectContaining({ description: 'Create failed' }));
    });
  });

  it('shows error toast when revoke key fails', async () => {
    const key = buildApiKey({ id: 'fail-revoke', name: 'Fail Revoke Key' });
    mockedListApiKeys.mockResolvedValue({ success: true, data: [key] });
    mockedRevokeApiKey.mockRejectedValue(new Error('Revoke failed'));

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Fail Revoke Key')).toBeInTheDocument();
    });

    const keyRow = screen.getByText('Fail Revoke Key').closest('div[class*="flex items-center justify-between"]');
    const rowRevokeButton = keyRow?.querySelector('button:last-child');
    if (rowRevokeButton) {
      await user.click(rowRevokeButton as HTMLElement);
    }

    await waitFor(() => {
      expect(screen.getByText('Revoke API Key')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /^revoke$/i }));

    const { toast } = await import('sonner');
    await waitFor(() => {
      expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to revoke API key', expect.objectContaining({ description: 'Revoke failed' }));
    });
  });

  it('shows lastUsedAt when present on key', async () => {
    const key = buildApiKey({ name: 'Used Key', lastUsedAt: '2024-01-15T00:00:00Z' });
    mockedListApiKeys.mockResolvedValue({ success: true, data: [key] });

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Used Key')).toBeInTheDocument();
      expect(screen.getByText(/last used/i)).toBeInTheDocument();
    });
  });

  it('shows load error toast with description', async () => {
    mockedListApiKeys.mockRejectedValue(new Error('Connection timeout'));

    render(<SettingsPage />);

    const { toast } = await import('sonner');
    await waitFor(() => {
      expect(vi.mocked(toast).error).toHaveBeenCalledWith('Failed to load API keys', expect.objectContaining({ description: 'Connection timeout' }));
    });
  });

  it('cancels revoke dialog by pressing escape/close', async () => {
    const key = buildApiKey({ id: 'cancel-revoke', name: 'Cancel Key' });
    mockedListApiKeys.mockResolvedValue({ success: true, data: [key] });

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Cancel Key')).toBeInTheDocument();
    });

    // Open revoke dialog
    const keyRow = screen.getByText('Cancel Key').closest('div[class*="flex items-center justify-between"]');
    const rowRevokeButton = keyRow?.querySelector('button:last-child');
    if (rowRevokeButton) {
      await user.click(rowRevokeButton as HTMLElement);
    }

    await waitFor(() => {
      expect(screen.getByText('Revoke API Key')).toBeInTheDocument();
    });

    // Click Cancel button to close dialog
    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelBtn);

    await waitFor(() => {
      expect(screen.queryByText('Revoke API Key')).not.toBeInTheDocument();
    });

    expect(mockedRevokeApiKey).not.toHaveBeenCalled();
  });

  it('toggles key visibility', async () => {
    mockedListApiKeys.mockResolvedValue({ success: true, data: [] });
    mockedCreateApiKey.mockResolvedValue({
      success: true,
      data: { ...buildApiKey(), key: 'load_full_secret_key_12345678' },
    });

    const { user } = render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/key name/i)).toBeInTheDocument();
    });

    // Create a key first
    await user.type(screen.getByPlaceholderText(/key name/i), 'Toggle Test');
    await user.click(screen.getByRole('button', { name: /create key/i }));

    // Wait for the created key banner - after creation, showKey is set to true
    await waitFor(() => {
      expect(screen.getByText(/copy it now/i)).toBeInTheDocument();
    });

    // The full key should be visible initially (showKey starts true after creation)
    const copyItNowText = screen.getByText(/copy it now/i);
    const keyContainer = copyItNowText.closest('.rounded-lg');
    const codeEl = keyContainer?.querySelector('code');
    expect(codeEl?.textContent).toBe('load_full_secret_key_12345678');

    // Click the eye-off button to hide the key (first icon button)
    const iconButtons = keyContainer?.querySelectorAll('button');
    await user.click(iconButtons![0] as HTMLElement);

    // Key should now be partially hidden (truncated with ...)
    await waitFor(() => {
      expect(codeEl?.textContent).toContain('...');
      expect(codeEl?.textContent).not.toBe('load_full_secret_key_12345678');
    });
  });
});
