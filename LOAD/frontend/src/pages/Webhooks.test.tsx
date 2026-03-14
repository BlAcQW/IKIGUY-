import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, userEvent } from '@test/helpers/render';
import { buildWebhook, buildWebhookDelivery } from '@test/helpers/factories';

vi.mock('@/lib/api', () => ({
  listWebhooks: vi.fn(),
  createWebhook: vi.fn(),
  updateWebhook: vi.fn(),
  deleteWebhook: vi.fn(),
  getWebhookDeliveries: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { WebhooksPage } from './Webhooks';
import { listWebhooks, createWebhook, updateWebhook, deleteWebhook, getWebhookDeliveries } from '@/lib/api';
import { toast } from 'sonner';

const mockedListWebhooks = vi.mocked(listWebhooks);
const mockedCreateWebhook = vi.mocked(createWebhook);
const mockedUpdateWebhook = vi.mocked(updateWebhook);
const mockedDeleteWebhook = vi.mocked(deleteWebhook);
const mockedGetWebhookDeliveries = vi.mocked(getWebhookDeliveries);
const mockedToast = vi.mocked(toast);

describe('WebhooksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title', () => {
    mockedListWebhooks.mockReturnValue(new Promise(() => {}));
    render(<WebhooksPage />);
    expect(screen.getByText('Webhooks')).toBeInTheDocument();
  });

  it('shows empty state when no webhooks', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });
    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });
  });

  it('renders webhooks with URLs', async () => {
    const webhooks = [buildWebhook({ url: 'https://example.com/hook', active: true })];
    mockedListWebhooks.mockResolvedValue({ success: true, data: webhooks });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://example.com/hook')).toBeInTheDocument();
    });
  });

  it('shows active/inactive badge', async () => {
    const webhooks = [
      buildWebhook({ url: 'https://a.com', active: true }),
      buildWebhook({ url: 'https://b.com', active: false }),
    ];
    mockedListWebhooks.mockResolvedValue({ success: true, data: webhooks });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });

  it('shows event badges', async () => {
    const webhooks = [buildWebhook({ events: ['call.started', 'call.ended'] })];
    mockedListWebhooks.mockResolvedValue({ success: true, data: webhooks });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('call.started')).toBeInTheDocument();
      expect(screen.getByText('call.ended')).toBeInTheDocument();
    });
  });

  it('has Create Webhook button', () => {
    mockedListWebhooks.mockReturnValue(new Promise(() => {}));
    render(<WebhooksPage />);
    expect(screen.getByRole('button', { name: /create webhook/i })).toBeInTheDocument();
  });

  it('handles load error gracefully', async () => {
    mockedListWebhooks.mockRejectedValue(new Error('fail'));
    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('Webhooks')).toBeInTheDocument();
    });
  });

  it('opens create dialog on Create Webhook click', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });
    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Add a new webhook endpoint.')).toBeInTheDocument();
    });
  });

  it('renders webhook secret field', async () => {
    const webhooks = [buildWebhook({ secret: 'whsec_testlong123' })];
    mockedListWebhooks.mockResolvedValue({ success: true, data: webhooks });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://example.com/webhook')).toBeInTheDocument();
    });

    // Secret is truncated to first 8 chars + "..."
    expect(screen.getByText('whsec_te...')).toBeInTheDocument();
  });

  it('submits create webhook form with url and events', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });
    mockedCreateWebhook.mockResolvedValue({ success: true, data: buildWebhook() });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    // Open create dialog
    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Add a new webhook endpoint.')).toBeInTheDocument();
    });

    // Fill url
    const urlInput = screen.getByPlaceholderText('https://your-server.com/webhook');
    await userEvent.type(urlInput, 'https://my-webhook.com/hook');

    // Select an event (click the badge to toggle it)
    const callStartedBadge = screen.getByText('call.started');
    await userEvent.click(callStartedBadge);

    // Submit
    const createBtn = screen.getByRole('button', { name: /^create$/i });
    await userEvent.click(createBtn);

    await waitFor(() => {
      expect(mockedCreateWebhook).toHaveBeenCalledWith(expect.objectContaining({
        url: 'https://my-webhook.com/hook',
        events: ['call.started'],
        active: true,
      }));
    });
  });

  it('shows error when submitting webhook with no events selected', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Add a new webhook endpoint.')).toBeInTheDocument();
    });

    const urlInput = screen.getByPlaceholderText('https://your-server.com/webhook');
    await userEvent.type(urlInput, 'https://my-webhook.com/hook');

    // Do NOT select any events
    const createBtn = screen.getByRole('button', { name: /^create$/i });
    await userEvent.click(createBtn);

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Select at least one event');
    });

    // createWebhook should NOT have been called
    expect(mockedCreateWebhook).not.toHaveBeenCalled();
  });

  it('shows error toast when create webhook fails', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });
    mockedCreateWebhook.mockRejectedValue(new Error('Server error'));

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('https://your-server.com/webhook')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('https://your-server.com/webhook'), 'https://test.com');
    await userEvent.click(screen.getByText('call.started'));

    await userEvent.click(screen.getByRole('button', { name: /^create$/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to create webhook', expect.objectContaining({ description: 'Server error' }));
    });
  });

  it('deletes webhook after confirmation', async () => {
    const webhook = buildWebhook({ url: 'https://delete-me.com/hook' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedDeleteWebhook.mockResolvedValue({ success: true });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://delete-me.com/hook')).toBeInTheDocument();
    });

    // Find delete button (has hover:text-destructive)
    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn => btn.className.includes('hover:text-destructive'));
    expect(deleteBtn).toBeTruthy();
    await userEvent.click(deleteBtn!);

    // Confirm in alert dialog
    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /^delete$/i });
    await userEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockedDeleteWebhook).toHaveBeenCalledWith(webhook.id);
    });
  });

  it('shows error toast when delete webhook fails', async () => {
    const webhook = buildWebhook({ url: 'https://fail-delete.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedDeleteWebhook.mockRejectedValue(new Error('Delete failed'));

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://fail-delete.com')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const deleteBtn = allButtons.find(btn => btn.className.includes('hover:text-destructive'));
    await userEvent.click(deleteBtn!);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /^delete$/i }));

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to delete webhook', expect.objectContaining({ description: 'Delete failed' }));
    });
  });

  it('opens edit dialog with populated form when clicking edit button', async () => {
    const webhook = buildWebhook({ url: 'https://edit-me.com/hook', events: ['call.started'], active: true });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://edit-me.com/hook')).toBeInTheDocument();
    });

    // Find the edit (pencil) button - by looking for the pencil SVG
    const allButtons = screen.getAllByRole('button');
    const editBtn = allButtons.find(btn => {
      const svg = btn.querySelector('svg.lucide-pencil');
      return svg !== null;
    });
    expect(editBtn).toBeTruthy();
    await userEvent.click(editBtn!);

    await waitFor(() => {
      expect(screen.getByText('Edit Webhook')).toBeInTheDocument();
      expect(screen.getByText('Update webhook configuration.')).toBeInTheDocument();
    });

    // Verify url is populated
    const urlInput = screen.getByPlaceholderText('https://your-server.com/webhook') as HTMLInputElement;
    expect(urlInput.value).toBe('https://edit-me.com/hook');
  });

  it('submits edit webhook form and calls updateWebhook', async () => {
    const webhook = buildWebhook({ url: 'https://update-me.com', events: ['call.started'] });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedUpdateWebhook.mockResolvedValue({ success: true, data: buildWebhook() });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://update-me.com')).toBeInTheDocument();
    });

    // Find edit button by pencil SVG
    const allButtons = screen.getAllByRole('button');
    const editBtn = allButtons.find(btn => {
      const svg = btn.querySelector('svg.lucide-pencil');
      return svg !== null;
    });
    await userEvent.click(editBtn!);

    await waitFor(() => {
      expect(screen.getByText('Edit Webhook')).toBeInTheDocument();
    });

    // Submit (button says "Update" in edit mode)
    const updateBtn = screen.getByRole('button', { name: /^update$/i });
    await userEvent.click(updateBtn);

    await waitFor(() => {
      expect(mockedUpdateWebhook).toHaveBeenCalledWith(webhook.id, expect.objectContaining({
        url: 'https://update-me.com',
        events: ['call.started'],
      }));
    });
  });

  it('expands webhook to show delivery history', async () => {
    const webhook = buildWebhook({ url: 'https://expand-me.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://expand-me.com')).toBeInTheDocument();
    });

    // Click expand button (the chevron button in the row)
    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    expect(expandBtn).toBeTruthy();
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(mockedGetWebhookDeliveries).toHaveBeenCalledWith(webhook.id);
      expect(screen.getByText('Delivery History')).toBeInTheDocument();
    });
  });

  it('shows delivery history data when expanded with deliveries', async () => {
    const webhook = buildWebhook({ url: 'https://deliveries.com' });
    const delivery = buildWebhookDelivery({ event: 'call.started', status: 'success', responseCode: 200, responseTime: 150 });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [delivery] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://deliveries.com')).toBeInTheDocument();
    });

    // Click expand
    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('Delivery History')).toBeInTheDocument();
      expect(screen.getByText('150ms')).toBeInTheDocument();
    });
  });

  it('shows empty deliveries message', async () => {
    const webhook = buildWebhook({ url: 'https://empty-deliveries.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://empty-deliveries.com')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('No deliveries yet.')).toBeInTheDocument();
    });
  });

  it('toggles secret visibility when clicking eye button', async () => {
    const webhook = buildWebhook({ id: 'vis-wh', secret: 'whsec_fullsecretvalue123' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('whsec_fu...')).toBeInTheDocument();
    });

    // Find the eye toggle button (h-7 w-7 buttons near the secret)
    const allButtons = screen.getAllByRole('button');
    const eyeButtons = allButtons.filter(btn => btn.className.includes('h-7') && btn.className.includes('w-7'));
    // First h-7 button is the eye toggle, second is copy
    expect(eyeButtons.length).toBeGreaterThanOrEqual(2);
    await userEvent.click(eyeButtons[0]);

    // After toggle, full secret should be visible
    await waitFor(() => {
      expect(screen.getByText('whsec_fullsecretvalue123')).toBeInTheDocument();
    });

    // Click again to hide
    await userEvent.click(eyeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('whsec_fu...')).toBeInTheDocument();
    });
  });

  it('renders copy button for secret', async () => {
    const webhook = buildWebhook({ secret: 'whsec_copyme123456' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://example.com/webhook')).toBeInTheDocument();
    });

    // Verify the copy button exists (contains lucide-copy SVG)
    const allButtons = screen.getAllByRole('button');
    const copyBtn = allButtons.find(btn => btn.querySelector('svg.lucide-copy') !== null);
    expect(copyBtn).toBeTruthy();
  });

  it('collapses expanded webhook when clicking expand again', async () => {
    const webhook = buildWebhook({ url: 'https://collapse-test.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://collapse-test.com')).toBeInTheDocument();
    });

    // Click expand
    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('Delivery History')).toBeInTheDocument();
    });

    // Click again to collapse
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.queryByText('Delivery History')).not.toBeInTheDocument();
    });
  });

  it('shows delivery with failed status as destructive badge', async () => {
    const webhook = buildWebhook({ url: 'https://fail-delivery.com' });
    const delivery = buildWebhookDelivery({ event: 'call.failed', status: 'failed', responseCode: 500, responseTime: 2000 });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [delivery] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://fail-delivery.com')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('failed')).toBeInTheDocument();
      expect(screen.getByText('500')).toBeInTheDocument();
      expect(screen.getByText('2000ms')).toBeInTheDocument();
    });
  });

  it('shows -- for null responseCode and responseTime in delivery', async () => {
    const webhook = buildWebhook({ url: 'https://null-delivery.com' });
    const delivery = buildWebhookDelivery({ event: 'call.started', status: 'pending', responseCode: null, responseTime: null });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [delivery] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://null-delivery.com')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('pending')).toBeInTheDocument();
      const dashes = screen.getAllByText('—');
      expect(dashes.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('shows error toast when update webhook fails', async () => {
    const webhook = buildWebhook({ url: 'https://fail-update.com', events: ['call.started'] });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedUpdateWebhook.mockRejectedValue(new Error('Update failed'));

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://fail-update.com')).toBeInTheDocument();
    });

    // Find edit button
    const allButtons = screen.getAllByRole('button');
    const editBtn = allButtons.find(btn => {
      const svg = btn.querySelector('svg.lucide-pencil');
      return svg !== null;
    });
    await userEvent.click(editBtn!);

    await waitFor(() => {
      expect(screen.getByText('Edit Webhook')).toBeInTheDocument();
    });

    const updateBtn = screen.getByRole('button', { name: /^update$/i });
    await userEvent.click(updateBtn);

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to update webhook', expect.objectContaining({ description: 'Update failed' }));
    });
  });

  it('handles deliveries load failure gracefully', async () => {
    const webhook = buildWebhook({ url: 'https://fail-deliveries.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockRejectedValue(new Error('Deliveries error'));

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://fail-deliveries.com')).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    // Should show empty deliveries after error
    await waitFor(() => {
      expect(screen.getByText('No deliveries yet.')).toBeInTheDocument();
    });
  });

  it('shows load error toast on initial load failure', async () => {
    mockedListWebhooks.mockRejectedValue(new Error('Network error'));
    render(<WebhooksPage />);

    await waitFor(() => {
      expect(mockedToast.error).toHaveBeenCalledWith('Failed to load webhooks', expect.objectContaining({ description: 'Network error' }));
    });
  });

  it('toggles event selection in create form', async () => {
    mockedListWebhooks.mockResolvedValue({ success: true, data: [] });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Add a new webhook endpoint.')).toBeInTheDocument();
    });

    // Select then deselect an event
    await userEvent.click(screen.getByText('call.started'));
    await userEvent.click(screen.getByText('call.ended'));

    // Now deselect call.started
    await userEvent.click(screen.getByText('call.started'));

    // Submit - only call.ended should be selected
    const urlInput = screen.getByPlaceholderText('https://your-server.com/webhook');
    await userEvent.type(urlInput, 'https://toggle-test.com');

    mockedCreateWebhook.mockResolvedValue({ success: true, data: buildWebhook() });
    const createBtn = screen.getByRole('button', { name: /^create$/i });
    await userEvent.click(createBtn);

    await waitFor(() => {
      expect(mockedCreateWebhook).toHaveBeenCalledWith(expect.objectContaining({
        events: ['call.ended'],
      }));
    });
  });

  it('renders multiple webhooks', async () => {
    const webhooks = [
      buildWebhook({ url: 'https://first.com/hook', active: true }),
      buildWebhook({ url: 'https://second.com/hook', active: false }),
    ];
    mockedListWebhooks.mockResolvedValue({ success: true, data: webhooks });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://first.com/hook')).toBeInTheDocument();
      expect(screen.getByText('https://second.com/hook')).toBeInTheDocument();
    });
  });

  it('deletes expanded webhook and clears expandedId', async () => {
    const webhook = buildWebhook({ url: 'https://delete-expanded.com' });
    mockedListWebhooks.mockResolvedValue({ success: true, data: [webhook] });
    mockedGetWebhookDeliveries.mockResolvedValue({ success: true, data: [] });
    mockedDeleteWebhook.mockResolvedValue({ success: true });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('https://delete-expanded.com')).toBeInTheDocument();
    });

    // First expand the webhook
    const allButtons = screen.getAllByRole('button');
    const expandBtn = allButtons.find(btn => btn.className.includes('shrink-0') && btn.className.includes('h-8'));
    await userEvent.click(expandBtn!);

    await waitFor(() => {
      expect(screen.getByText('Delivery History')).toBeInTheDocument();
    });

    // Now delete it
    const deleteBtn = screen.getAllByRole('button').find(btn => btn.className.includes('hover:text-destructive'));
    await userEvent.click(deleteBtn!);

    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /^delete$/i }));

    await waitFor(() => {
      expect(mockedDeleteWebhook).toHaveBeenCalledWith(webhook.id);
    });
  });

  it('reloads list after successful create', async () => {
    mockedListWebhooks
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({ success: true, data: [buildWebhook()] });
    mockedCreateWebhook.mockResolvedValue({ success: true, data: buildWebhook() });

    render(<WebhooksPage />);

    await waitFor(() => {
      expect(screen.getByText('No webhooks yet')).toBeInTheDocument();
    });

    const createButtons = screen.getAllByRole('button', { name: /create webhook/i });
    await userEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('https://your-server.com/webhook')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('https://your-server.com/webhook'), 'https://new.com');
    await userEvent.click(screen.getByText('call.ended'));

    await userEvent.click(screen.getByRole('button', { name: /^create$/i }));

    await waitFor(() => {
      expect(mockedListWebhooks).toHaveBeenCalledTimes(2);
    });
  });
});
