import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import websocket from '@fastify/websocket';
import { config } from './config/index.js';
import { connectDatabase, disconnectDatabase } from './database/client.js';
import { errorHandler } from './middleware/error-handler.js';
import { registerRateLimit } from './middleware/rate-limit.js';
import { authRoutes } from './modules/auth/routes.js';
import { assistantRoutes } from './modules/assistants/routes.js';
import { callRoutes } from './modules/calls/routes.js';
import { phoneNumberRoutes } from './modules/phone-numbers/routes.js';
import { toolRoutes } from './modules/tools/routes.js';
import { squadRoutes } from './modules/squads/routes.js';
import { campaignRoutes } from './modules/campaigns/routes.js';
import { webhookRoutes } from './modules/webhooks/routes.js';
import { websocketRoutes } from './websocket/handler.js';
import { createWebhookWorker, closeWebhookQueue } from './modules/webhooks/delivery.js';
import { AsteriskAriClient } from './telephony/asterisk-ari.js';
import { CallBridge } from './telephony/call-bridge.js';
import { createCampaignQueues, setCallBridge, closeCampaignQueues } from './modules/campaigns/engine.js';
import { analyticsRoutes } from './modules/analytics/routes.js';
import { initializeSessionStore } from './voice-pipeline/session.js';
import type { Worker } from 'bullmq';

async function buildApp() {
  const app = Fastify({
    logger: {
      level: config.NODE_ENV === 'production' ? 'info' : 'debug',
    },
  });

  // Plugins
  await app.register(cors, {
    origin: config.FRONTEND_URL,
    credentials: true,
  });

  await app.register(jwt, {
    secret: config.JWT_SECRET,
  });

  await app.register(websocket);

  await app.register(swagger, {
    openapi: {
      info: {
        title: 'LOAD API',
        description: 'AI Call Automation Platform API',
        version: '0.1.0',
      },
      servers: [{ url: config.API_URL }],
      components: {
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'JWT',
          },
          apiKeyAuth: {
            type: 'http',
            scheme: 'bearer',
            description: 'API Key (load_...)',
          },
        },
      },
    },
  });

  await app.register(swaggerUi, {
    routePrefix: '/docs',
  });

  await registerRateLimit(app);

  // Error handler
  app.setErrorHandler(errorHandler);

  // Health check
  app.get('/api/health', async () => ({
    success: true,
    data: { status: 'ok', timestamp: new Date().toISOString() },
  }));

  // Routes
  await app.register(authRoutes);
  await app.register(assistantRoutes);
  await app.register(callRoutes);
  await app.register(phoneNumberRoutes);
  await app.register(toolRoutes);
  await app.register(squadRoutes);
  await app.register(campaignRoutes);
  await app.register(webhookRoutes);
  await app.register(analyticsRoutes);
  await app.register(websocketRoutes);

  return app;
}

async function start() {
  const app = await buildApp();
  let webhookWorker: Worker | null = null;
  let campaignWorkers: { executeWorker: Worker; callWorker: Worker } | null = null;
  let callBridge: CallBridge | null = null;

  try {
    await connectDatabase();
    app.log.info('Database connected');

    // Initialize session store (Redis-backed or in-memory fallback)
    initializeSessionStore(config.REDIS_URL);
    app.log.info('Session store initialized');

    // Initialize webhook delivery worker
    try {
      webhookWorker = createWebhookWorker();
      app.log.info('Webhook delivery worker started');
    } catch (err) {
      app.log.warn(`Failed to start webhook worker (Redis may be unavailable): ${err}`);
    }

    // Initialize Asterisk ARI telephony (conditional)
    if (config.ASTERISK_ARI_URL && config.ASTERISK_ARI_USERNAME && config.ASTERISK_ARI_PASSWORD) {
      try {
        const ariClient = new AsteriskAriClient({
          url: config.ASTERISK_ARI_URL,
          username: config.ASTERISK_ARI_USERNAME,
          password: config.ASTERISK_ARI_PASSWORD,
          appName: config.ASTERISK_ARI_APP,
        });

        callBridge = new CallBridge(ariClient);
        await callBridge.initialize();

        // Decorate Fastify app with bridge reference for route handlers
        (app as any).callBridge = callBridge;

        // Inject into campaign engine
        setCallBridge(callBridge);

        app.log.info('Asterisk ARI telephony initialized');
      } catch (err) {
        app.log.error(`Failed to initialize Asterisk ARI telephony: ${err}`);
      }
    } else {
      app.log.warn('Asterisk ARI not configured — telephony disabled. Set ASTERISK_ARI_URL, ASTERISK_ARI_USERNAME, ASTERISK_ARI_PASSWORD to enable.');
    }

    // Initialize campaign execution engine
    try {
      campaignWorkers = createCampaignQueues();
      app.log.info('Campaign execution engine started');
    } catch (err) {
      app.log.warn(`Failed to start campaign engine (Redis may be unavailable): ${err}`);
    }

    await app.listen({ port: config.PORT, host: '0.0.0.0' });
    app.log.info(`Server listening on port ${config.PORT}`);
    app.log.info(`API docs available at http://localhost:${config.PORT}/docs`);
  } catch (err) {
    app.log.error(err);
    await disconnectDatabase();
    process.exit(1);
  }

  const shutdown = async () => {
    app.log.info('Shutting down...');

    // Close workers first
    if (webhookWorker) {
      await webhookWorker.close().catch(() => {});
    }
    if (campaignWorkers) {
      await campaignWorkers.executeWorker.close().catch(() => {});
      await campaignWorkers.callWorker.close().catch(() => {});
    }

    // Close queues
    await closeWebhookQueue().catch(() => {});
    await closeCampaignQueues().catch(() => {});

    await app.close();
    await disconnectDatabase();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

if (process.env.NODE_ENV !== 'test') {
  start();
}

export { buildApp };
