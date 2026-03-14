import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Fastify from 'fastify';
import websocket from '@fastify/websocket';
import { telephonyRoutes } from './routes.js';

// Mock dependencies
vi.mock('../../config/index.js', () => ({
  config: {
    NODE_ENV: 'test',
    PORT: 3000,
    API_URL: 'https://api.example.com',
    TWILIO_ACCOUNT_SID: '',
    TWILIO_AUTH_TOKEN: '', // Empty = skip signature validation in test
  },
}));

vi.mock('../../telephony/twilio.js', () => ({
  validateTwilioSignature: vi.fn().mockReturnValue(true),
}));

vi.mock('./service.js', () => ({
  handleInboundCall: vi.fn().mockResolvedValue(
    '<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://test/media-stream" /></Connect></Response>',
  ),
  handleOutboundConnect: vi.fn().mockResolvedValue(
    '<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://test/media-stream" /></Connect></Response>',
  ),
  handleStatusCallback: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../telephony/twilio-stream.js', () => ({
  handleTwilioMediaStream: vi.fn(),
}));

import { validateTwilioSignature } from '../../telephony/twilio.js';
import { handleInboundCall, handleOutboundConnect, handleStatusCallback } from './service.js';

describe('telephony/routes', () => {
  let app: ReturnType<typeof Fastify>;

  beforeEach(async () => {
    vi.clearAllMocks();
    app = Fastify();
    await app.register(websocket);
    await app.register(telephonyRoutes);
    await app.ready();
  });

  afterEach(async () => {
    await app.close();
  });

  describe('POST /api/telephony/inbound', () => {
    it('returns TwiML with application/xml content type', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/inbound',
        payload: {
          CallSid: 'CA_test',
          AccountSid: 'AC_test',
          From: '+15551112222',
          To: '+15553334444',
          CallStatus: 'ringing',
        },
      });

      expect(response.statusCode).toBe(200);
      expect(response.headers['content-type']).toContain('application/xml');
      expect(response.body).toContain('<Response>');
      expect(handleInboundCall).toHaveBeenCalledWith(expect.objectContaining({
        CallSid: 'CA_test',
        From: '+15551112222',
        To: '+15553334444',
      }));
    });
  });

  describe('POST /api/telephony/outbound-connect', () => {
    it('returns TwiML with application/xml content type', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/outbound-connect',
        payload: {
          CallSid: 'CA_outbound',
          AccountSid: 'AC_test',
          CallStatus: 'in-progress',
        },
      });

      expect(response.statusCode).toBe(200);
      expect(response.headers['content-type']).toContain('application/xml');
      expect(handleOutboundConnect).toHaveBeenCalledWith(expect.objectContaining({
        CallSid: 'CA_outbound',
      }));
    });
  });

  describe('POST /api/telephony/status', () => {
    it('returns 204 on success', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/status',
        payload: {
          CallSid: 'CA_status',
          CallStatus: 'completed',
          CallDuration: '120',
        },
      });

      expect(response.statusCode).toBe(204);
      expect(handleStatusCallback).toHaveBeenCalledWith(expect.objectContaining({
        CallSid: 'CA_status',
        CallStatus: 'completed',
      }));
    });
  });

  describe('Twilio signature validation', () => {
    it('skips validation in test mode with no auth token', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/inbound',
        payload: {
          CallSid: 'CA_no_sig',
          AccountSid: 'AC_test',
          From: '+15551112222',
          To: '+15553334444',
          CallStatus: 'ringing',
        },
        // No X-Twilio-Signature header
      });

      // Should succeed because test mode skips validation
      expect(response.statusCode).toBe(200);
    });

    it('validates signature when auth token is configured', async () => {
      // Override config to simulate production with Twilio configured
      const configModule = await import('../../config/index.js');
      const originalEnv = configModule.config.NODE_ENV;
      const originalToken = configModule.config.TWILIO_AUTH_TOKEN;

      Object.assign(configModule.config, {
        NODE_ENV: 'production',
        TWILIO_AUTH_TOKEN: 'real_token',
      });

      // Missing signature should return 403
      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/inbound',
        payload: {
          CallSid: 'CA_sig_test',
          AccountSid: 'AC_test',
          From: '+15551112222',
          To: '+15553334444',
          CallStatus: 'ringing',
        },
      });

      expect(response.statusCode).toBe(403);
      expect(JSON.parse(response.body).error.message).toContain('Missing Twilio signature');

      // Restore config
      Object.assign(configModule.config, {
        NODE_ENV: originalEnv,
        TWILIO_AUTH_TOKEN: originalToken,
      });
    });

    it('returns 403 for invalid signature', async () => {
      const configModule = await import('../../config/index.js');
      const originalEnv = configModule.config.NODE_ENV;
      const originalToken = configModule.config.TWILIO_AUTH_TOKEN;

      Object.assign(configModule.config, {
        NODE_ENV: 'production',
        TWILIO_AUTH_TOKEN: 'real_token',
      });

      (validateTwilioSignature as any).mockReturnValue(false);

      const response = await app.inject({
        method: 'POST',
        url: '/api/telephony/inbound',
        headers: {
          'x-twilio-signature': 'invalid_sig',
        },
        payload: {
          CallSid: 'CA_bad_sig',
          AccountSid: 'AC_test',
          From: '+15551112222',
          To: '+15553334444',
          CallStatus: 'ringing',
        },
      });

      expect(response.statusCode).toBe(403);
      expect(JSON.parse(response.body).error.message).toContain('Invalid Twilio signature');

      // Restore
      Object.assign(configModule.config, {
        NODE_ENV: originalEnv,
        TWILIO_AUTH_TOKEN: originalToken,
      });
      (validateTwilioSignature as any).mockReturnValue(true);
    });
  });
});
