import { FastifyInstance } from 'fastify';
import { authMiddleware } from '../../middleware/auth.js';
import { callAnalyticsQuerySchema, summaryQuerySchema } from './schemas.js';
import { getCallTimeSeries, getAnalyticsSummary } from './service.js';

export async function analyticsRoutes(app: FastifyInstance): Promise<void> {
  app.addHook('preHandler', authMiddleware);

  app.get('/api/analytics/calls', async (request) => {
    const query = callAnalyticsQuerySchema.parse(request.query);
    const data = await getCallTimeSeries(request.organizationId!, query);
    return { success: true, data };
  });

  app.get('/api/analytics/summary', async (request) => {
    const query = summaryQuerySchema.parse(request.query);
    const data = await getAnalyticsSummary(request.organizationId!, query);
    return { success: true, data };
  });
}
