import { prisma } from '../../database/client.js';
import { orgSettingsSchema, type OrgSettings, type UpdateOrgSettings } from './schemas.js';

// ---------------------------------------------------------------------------
// Credential masking
// ---------------------------------------------------------------------------
// Shows the first 4 and last 4 characters of a secret, replacing everything
// in between with asterisks.  Short strings (≤8 chars) are fully masked.

function maskCredential(value: string): string {
  if (value.length <= 8) return '*'.repeat(value.length);
  return `${value.slice(0, 4)}${'*'.repeat(value.length - 8)}${value.slice(-4)}`;
}

/** Returns a new ProviderCredentials object with every non-empty key masked. */
function maskCredentials(creds: Record<string, string | undefined>): Record<string, string | undefined> {
  const masked: Record<string, string | undefined> = {};
  for (const [key, val] of Object.entries(creds)) {
    masked[key] = val ? maskCredential(val) : undefined;
  }
  return masked;
}

// ---------------------------------------------------------------------------
// Deep merge helper  (immutable — returns a new object)
// ---------------------------------------------------------------------------
// Recursively merges `patch` into `base`. Only plain objects are merged;
// arrays and primitives in `patch` overwrite the corresponding key in `base`.

function deepMerge<T extends Record<string, unknown>>(base: T, patch: Record<string, unknown>): T {
  const result = { ...base };
  for (const [key, patchVal] of Object.entries(patch)) {
    if (patchVal === undefined) continue; // skip undefined — means "not provided"

    const baseVal = (result as Record<string, unknown>)[key];
    if (
      baseVal !== null &&
      patchVal !== null &&
      typeof baseVal === 'object' &&
      typeof patchVal === 'object' &&
      !Array.isArray(baseVal) &&
      !Array.isArray(patchVal)
    ) {
      (result as Record<string, unknown>)[key] = deepMerge(
        baseVal as Record<string, unknown>,
        patchVal as Record<string, unknown>,
      );
    } else {
      (result as Record<string, unknown>)[key] = patchVal;
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Retrieve org settings with **masked** credentials.
 * Safe for returning to the frontend — secrets are never exposed in full.
 */
export async function getSettings(organizationId: string): Promise<OrgSettings> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    select: { settings: true },
  });

  if (!org) {
    throw Object.assign(new Error('Organization not found'), { statusCode: 404 });
  }

  // Parse stored JSON through Zod (applies defaults for missing keys)
  const settings = orgSettingsSchema.parse(org.settings ?? {});

  // Return a copy with credentials masked
  return {
    ...settings,
    providerCredentials: maskCredentials(settings.providerCredentials) as OrgSettings['providerCredentials'],
  };
}

/**
 * Retrieve org settings with **raw** (unmasked) credentials.
 * Internal use only — called by the voice pipeline to resolve API keys.
 */
export async function getSettingsRaw(organizationId: string): Promise<OrgSettings> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    select: { settings: true },
  });

  if (!org) {
    throw Object.assign(new Error('Organization not found'), { statusCode: 404 });
  }

  return orgSettingsSchema.parse(org.settings ?? {});
}

/**
 * Update org settings by deep-merging the provided `input` into the existing
 * settings blob.  Only the keys the client sends are changed; everything
 * else is preserved.
 *
 * Returns the updated settings with credentials masked (same as GET).
 */
export async function updateSettings(
  organizationId: string,
  input: UpdateOrgSettings,
): Promise<OrgSettings> {
  // 1. Load existing settings (raw — we need unmasked values for the merge)
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    select: { settings: true },
  });

  if (!org) {
    throw Object.assign(new Error('Organization not found'), { statusCode: 404 });
  }

  const existing = orgSettingsSchema.parse(org.settings ?? {});

  // 2. Deep-merge patch into existing settings (immutable)
  const merged = deepMerge(existing, input as Record<string, unknown>);

  // 3. Validate the merged result against the full schema
  const validated = orgSettingsSchema.parse(merged);

  // 4. Persist — cast to `any` for Prisma's Json field typing
  await prisma.organization.update({
    where: { id: organizationId },
    data: { settings: JSON.parse(JSON.stringify(validated)) },
  });

  // 5. Return masked copy
  return {
    ...validated,
    providerCredentials: maskCredentials(validated.providerCredentials) as OrgSettings['providerCredentials'],
  };
}
