import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildOrganization, buildOrgSettings } from '../../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { getSettings, getSettingsRaw, updateSettings } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

// ---------------------------------------------------------------------------
// getSettings  — returns settings with masked credentials
// ---------------------------------------------------------------------------

describe('getSettings', () => {
  it('returns default settings when org has no settings stored', async () => {
    const org = buildOrganization();
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: null });

    const result = await getSettings(org.id);

    // Defaults should be applied by Zod
    expect(result.pipelineDefaults.silenceTimeout).toBe(30);
    expect(result.callBehavior.maxCallDuration).toBe(3600);
    expect(result.providerCredentials.openaiApiKey).toBeUndefined();
  });

  it('masks credential values in the response', async () => {
    const org = buildOrganization();
    const settings = buildOrgSettings({
      providerCredentials: {
        openaiApiKey: 'sk-test-1234567890abcdef',
        deepgramApiKey: 'dg_abcdefghijklmnop',
      },
    });
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings });

    const result = await getSettings(org.id);

    // First 4 + last 4 visible, middle replaced with asterisks
    // 'sk-test-1234567890abcdef' = 24 chars → 4 + 16 asterisks + 4
    expect(result.providerCredentials.openaiApiKey).toMatch(/^sk-t\*+cdef$/);
    // 'dg_abcdefghijklmnop' = 19 chars → 4 + 11 asterisks + 4
    expect(result.providerCredentials.deepgramApiKey).toMatch(/^dg_a\*+mnop$/);
  });

  it('throws 404 when organization is not found', async () => {
    prismaMock.organization.findUnique.mockResolvedValue(null);

    await expect(getSettings('non-existent')).rejects.toThrow('Organization not found');
  });
});

// ---------------------------------------------------------------------------
// getSettingsRaw  — returns settings with unmasked credentials
// ---------------------------------------------------------------------------

describe('getSettingsRaw', () => {
  it('returns unmasked credentials for pipeline use', async () => {
    const org = buildOrganization();
    const settings = buildOrgSettings({
      providerCredentials: { openaiApiKey: 'sk-real-key-12345678' },
    });
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings });

    const result = await getSettingsRaw(org.id);

    expect(result.providerCredentials.openaiApiKey).toBe('sk-real-key-12345678');
  });

  it('returns defaults when settings are null', async () => {
    const org = buildOrganization();
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: null });

    const result = await getSettingsRaw(org.id);

    expect(result.pipelineDefaults.silenceTimeout).toBe(30);
    expect(result.callBehavior.recordingEnabled).toBe(false);
  });

  it('throws 404 when organization is not found', async () => {
    prismaMock.organization.findUnique.mockResolvedValue(null);

    await expect(getSettingsRaw('missing')).rejects.toThrow('Organization not found');
  });
});

// ---------------------------------------------------------------------------
// updateSettings  — deep merges patch into existing settings
// ---------------------------------------------------------------------------

describe('updateSettings', () => {
  it('deep-merges a partial update into existing settings', async () => {
    const org = buildOrganization();
    const existing = buildOrgSettings();
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: existing });
    prismaMock.organization.update.mockResolvedValue({ ...org, settings: existing });

    await updateSettings(org.id, {
      pipelineDefaults: { silenceTimeout: 60 },
    });

    // Verify the persisted value was deep-merged
    const persisted = prismaMock.organization.update.mock.calls[0][0].data.settings as Record<string, unknown>;
    const pipeline = persisted.pipelineDefaults as Record<string, unknown>;
    expect(pipeline.silenceTimeout).toBe(60);
    // Other defaults should be preserved
    expect(pipeline.responseDelay).toBe(0.5);
  });

  it('preserves unmodified sections', async () => {
    const org = buildOrganization();
    const existing = buildOrgSettings({
      providerCredentials: { openaiApiKey: 'sk-original-key-value' },
    });
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: existing });
    prismaMock.organization.update.mockResolvedValue({ ...org, settings: existing });

    // Only update callBehavior
    await updateSettings(org.id, {
      callBehavior: { recordingEnabled: true },
    });

    const persisted = prismaMock.organization.update.mock.calls[0][0].data.settings as Record<string, unknown>;
    const creds = persisted.providerCredentials as Record<string, unknown>;
    // Original credential should still be there
    expect(creds.openaiApiKey).toBe('sk-original-key-value');
  });

  it('handles partial nested updates (e.g. only voice.speed)', async () => {
    const org = buildOrganization();
    const existing = buildOrgSettings();
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: existing });
    prismaMock.organization.update.mockResolvedValue({ ...org, settings: existing });

    await updateSettings(org.id, {
      pipelineDefaults: { voice: { speed: 1.5 } },
    });

    const persisted = prismaMock.organization.update.mock.calls[0][0].data.settings as Record<string, unknown>;
    const pipeline = persisted.pipelineDefaults as Record<string, unknown>;
    const voice = pipeline.voice as Record<string, unknown>;
    expect(voice.speed).toBe(1.5);
    // Other voice fields should be preserved from deep merge
    expect(voice.provider).toBe('openai');
    expect(voice.voiceId).toBe('alloy');
  });

  it('returns masked credentials after update', async () => {
    const org = buildOrganization();
    const existing = buildOrgSettings({
      providerCredentials: { openaiApiKey: 'sk-test-1234567890abcdef' },
    });
    prismaMock.organization.findUnique.mockResolvedValue({ ...org, settings: existing });
    prismaMock.organization.update.mockResolvedValue({ ...org, settings: existing });

    const result = await updateSettings(org.id, {
      callBehavior: { recordingEnabled: true },
    });

    expect(result.providerCredentials.openaiApiKey).toMatch(/^sk-t\*+cdef$/);
  });

  it('throws 404 when organization is not found', async () => {
    prismaMock.organization.findUnique.mockResolvedValue(null);

    await expect(
      updateSettings('missing', { callBehavior: { recordingEnabled: true } }),
    ).rejects.toThrow('Organization not found');
  });
});
