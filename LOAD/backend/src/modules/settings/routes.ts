import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { updateOrgSettingsSchema } from './schemas.js';
import { getSettings, updateSettings } from './service.js';

// ---------------------------------------------------------------------------
// Settings routes — organisation-scoped configuration
// ---------------------------------------------------------------------------
//
// These routes manage the `settings` JSONB column on the Organization model.
// The settings object has three sections:
//
//   1. providerCredentials — API keys for STT/LLM/TTS/telephony providers
//   2. pipelineDefaults    — default voice pipeline config (timeouts, models)
//   3. callBehavior        — call duration limits, recording, HIPAA, retries
//
// Data flow:
//   Frontend Settings page → PUT /api/settings → deep-merge → Organization.settings
//   Voice pipeline (WS/WebRTC) → getSettingsRaw() → resolve API keys → providers
//
// Security:
//   - GET always returns credentials masked (e.g. "sk-t****cdef")
//   - PUT restricted to OWNER / ADMIN roles
//   - Raw (unmasked) credentials are only used server-side in the pipeline
// ---------------------------------------------------------------------------

export async function settingsRoutes(app: FastifyInstance): Promise<void> {
  // ── GET /api/settings ──────────────────────────────────────────────────
  // Returns the org settings with credentials masked.
  // Any authenticated user in the org can read settings.

  app.get('/api/settings', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    const settings = await getSettings(request.organizationId!);
    return reply.send({ success: true, data: settings });
  });

  // ── PUT /api/settings ──────────────────────────────────────────────────
  // Deep-merges the provided payload into existing settings.
  // Restricted to OWNER and ADMIN roles — MEMBERs cannot change org config.

  app.put('/api/settings', {
    preHandler: [authMiddleware],
  }, async (request, reply) => {
    // RBAC: only OWNER and ADMIN may update settings
    const role = request.userRole;
    if (role !== 'OWNER' && role !== 'ADMIN') {
      return reply.status(403).send({
        success: false,
        error: {
          code: 'FORBIDDEN',
          message: 'Only OWNER or ADMIN roles can update settings',
          statusCode: 403,
        },
      });
    }

    // Validate request body
    const parsed = updateOrgSettingsSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.status(400).send({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: parsed.error.issues.map((i) => i.message).join(', '),
          statusCode: 400,
        },
      });
    }

    const settings = await updateSettings(request.organizationId!, parsed.data);
    return reply.send({ success: true, data: settings });
  });
}
