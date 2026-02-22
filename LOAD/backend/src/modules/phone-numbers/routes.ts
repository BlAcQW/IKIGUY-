import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import {
  searchNumbersSchema,
  purchaseNumberSchema,
  createSipNumberSchema,
  updatePhoneNumberSchema,
} from './schemas.js';
import {
  searchNumbers,
  purchaseNumber,
  createSipTrunkNumber,
  releaseNumber,
  updatePhoneNumber,
  getPhoneNumber,
  listPhoneNumbers,
} from './service.js';

export async function phoneNumberRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  // GET /api/phone-numbers — List all phone numbers for org
  app.get('/api/phone-numbers', async (request) => {
    const data = await listPhoneNumbers(request.organizationId!);
    return { success: true, data };
  });

  // GET /api/phone-numbers/:id — Get single phone number
  app.get('/api/phone-numbers/:id', async (request) => {
    const { id } = request.params as { id: string };
    const data = await getPhoneNumber(id, request.organizationId!);
    return { success: true, data };
  });

  // POST /api/phone-numbers/search — Search available numbers via Twilio
  app.post('/api/phone-numbers/search', async (request) => {
    const params = searchNumbersSchema.parse(request.body);
    const data = await searchNumbers(params);
    return { success: true, data };
  });

  // POST /api/phone-numbers — Purchase or register a phone number
  app.post('/api/phone-numbers', async (request, reply) => {
    const body = request.body as { provider?: string };

    if (body.provider === 'SIP_TRUNK') {
      const input = createSipNumberSchema.parse(body);
      const data = await createSipTrunkNumber(request.organizationId!, input);
      return reply.status(201).send({ success: true, data });
    }

    const input = purchaseNumberSchema.parse(body);
    const data = await purchaseNumber(request.organizationId!, input);
    return reply.status(201).send({ success: true, data });
  });

  // PATCH /api/phone-numbers/:id — Update (assign assistant, rename)
  app.patch('/api/phone-numbers/:id', async (request) => {
    const { id } = request.params as { id: string };
    const body = updatePhoneNumberSchema.parse(request.body);
    const data = await updatePhoneNumber(id, request.organizationId!, body);
    return { success: true, data };
  });

  // DELETE /api/phone-numbers/:id — Release phone number
  app.delete('/api/phone-numbers/:id', async (request) => {
    const { id } = request.params as { id: string };
    const data = await releaseNumber(id, request.organizationId!);
    return { success: true, data };
  });
}
