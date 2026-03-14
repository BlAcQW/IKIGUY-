import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildAssistant, buildPhoneNumber } from '../../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

// Mock dependencies
vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

vi.mock('../calls/service.js', () => ({
  createCall: vi.fn(),
  updateCallStatus: vi.fn(),
  endCall: vi.fn(),
  failCall: vi.fn(),
}));

vi.mock('../../voice-pipeline/session.js', () => ({
  createSession: vi.fn(),
}));

vi.mock('../../telephony/twilio.js', () => ({
  makeCall: vi.fn(),
}));

vi.mock('../webhooks/delivery.js', () => ({
  fireWebhookEvent: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../config/index.js', () => ({
  config: {
    API_URL: 'https://api.example.com',
    TWILIO_ACCOUNT_SID: 'AC_test',
    TWILIO_AUTH_TOKEN: 'test_token',
  },
}));

import {
  handleInboundCall,
  handleOutboundConnect,
  handleStatusCallback,
  makeOutboundCallTwilio,
} from './service.js';
import { createCall, updateCallStatus, endCall, failCall } from '../calls/service.js';
import { createSession } from '../../voice-pipeline/session.js';
import { makeCall } from '../../telephony/twilio.js';
import { fireWebhookEvent } from '../webhooks/delivery.js';

describe('telephony/service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    prismaMock = createPrismaMock();
  });

  describe('handleInboundCall', () => {
    const baseInput = {
      CallSid: 'CA_abc123',
      AccountSid: 'AC_test',
      From: '+15551112222',
      To: '+15553334444',
      CallStatus: 'ringing',
    };

    it('routes inbound call to assistant and returns Stream TwiML', async () => {
      const orgId = 'org-1';
      const phone = buildPhoneNumber({
        organizationId: orgId,
        number: '+15553334444',
        assistantId: 'asst-1',
      });
      const assistant = buildAssistant({
        id: 'asst-1',
        organizationId: orgId,
        model: { provider: 'openai', systemPrompt: 'You are helpful' },
      });
      const call = { id: 'call-1', organizationId: orgId, assistantId: 'asst-1' };
      const session = { id: 'session-1' };

      prismaMock.phoneNumber.findFirst.mockResolvedValue(phone);
      prismaMock.assistant.findUnique.mockResolvedValue(assistant);
      (createCall as any).mockResolvedValue(call);
      prismaMock.call.update.mockResolvedValue(call);
      (updateCallStatus as any).mockResolvedValue(call);
      (createSession as any).mockResolvedValue(session);

      const twiml = await handleInboundCall(baseInput);

      expect(twiml).toContain('<Response>');
      expect(twiml).toContain('<Connect>');
      expect(twiml).toContain('<Stream');
      expect(twiml).toContain('wss://api.example.com/api/telephony/media-stream');
      expect(twiml).toContain('callId');
      expect(twiml).toContain('sessionId');
      expect(twiml).toContain('assistantId');
      expect(twiml).toContain('organizationId');

      expect(createCall).toHaveBeenCalledWith(expect.objectContaining({
        organizationId: orgId,
        assistantId: 'asst-1',
        type: 'INBOUND',
        customerNumber: '+15551112222',
      }));
      expect(createSession).toHaveBeenCalledWith(expect.objectContaining({
        callId: 'call-1',
        assistantId: 'asst-1',
        organizationId: orgId,
      }));
      expect(fireWebhookEvent).toHaveBeenCalledWith(orgId, 'call.started', expect.any(Object));
    });

    it('returns "not configured" TwiML when no phone number found', async () => {
      prismaMock.phoneNumber.findFirst.mockResolvedValue(null);

      const twiml = await handleInboundCall(baseInput);

      expect(twiml).toContain('<Say>');
      expect(twiml).toContain('not configured');
      expect(createCall).not.toHaveBeenCalled();
    });

    it('returns "unavailable" TwiML when no assistant assigned', async () => {
      const phone = buildPhoneNumber({
        number: '+15553334444',
        assistantId: null,
      });
      prismaMock.phoneNumber.findFirst.mockResolvedValue(phone);

      const twiml = await handleInboundCall(baseInput);

      expect(twiml).toContain('<Say>');
      expect(twiml).toContain('unavailable');
      expect(createCall).not.toHaveBeenCalled();
    });

    it('returns "unavailable" TwiML when assistant not found', async () => {
      const phone = buildPhoneNumber({
        number: '+15553334444',
        assistantId: 'missing-asst',
      });
      prismaMock.phoneNumber.findFirst.mockResolvedValue(phone);
      prismaMock.assistant.findUnique.mockResolvedValue(null);

      const twiml = await handleInboundCall(baseInput);

      expect(twiml).toContain('<Say>');
      expect(twiml).toContain('unavailable');
    });
  });

  describe('handleOutboundConnect', () => {
    it('finds call by CallSid and generates Stream TwiML', async () => {
      const call = {
        id: 'call-1',
        organizationId: 'org-1',
        assistantId: 'asst-1',
        externalCallId: 'CA_outbound',
        metadata: { sessionId: 'session-1' },
      };

      prismaMock.call.findFirst.mockResolvedValue(call);
      (updateCallStatus as any).mockResolvedValue(call);

      const twiml = await handleOutboundConnect({
        CallSid: 'CA_outbound',
        AccountSid: 'AC_test',
        CallStatus: 'in-progress',
      });

      expect(twiml).toContain('<Stream');
      expect(twiml).toContain('session-1');
      expect(updateCallStatus).toHaveBeenCalledWith('call-1', 'IN_PROGRESS');
    });

    it('returns error TwiML when call not found', async () => {
      prismaMock.call.findFirst.mockResolvedValue(null);

      const twiml = await handleOutboundConnect({
        CallSid: 'CA_unknown',
        AccountSid: 'AC_test',
        CallStatus: 'in-progress',
      });

      expect(twiml).toContain('<Say>');
      expect(twiml).toContain('failed');
    });

    it('returns error TwiML when sessionId missing from metadata', async () => {
      prismaMock.call.findFirst.mockResolvedValue({
        id: 'call-1',
        organizationId: 'org-1',
        assistantId: 'asst-1',
        metadata: {},
      });

      const twiml = await handleOutboundConnect({
        CallSid: 'CA_no_session',
        AccountSid: 'AC_test',
        CallStatus: 'in-progress',
      });

      expect(twiml).toContain('<Say>');
      expect(twiml).toContain('failed');
    });
  });

  describe('handleStatusCallback', () => {
    it('maps "completed" to ENDED and calls endCall', async () => {
      const call = { id: 'call-1', externalCallId: 'CA_done' };
      prismaMock.call.findFirst.mockResolvedValue(call);
      (endCall as any).mockResolvedValue(call);
      prismaMock.call.update.mockResolvedValue(call);

      await handleStatusCallback({
        CallSid: 'CA_done',
        CallStatus: 'completed',
        CallDuration: 120,
      });

      expect(endCall).toHaveBeenCalledWith('call-1', [], 'completed');
      expect(prismaMock.call.update).toHaveBeenCalledWith({
        where: { id: 'call-1' },
        data: { duration: 120 },
      });
    });

    it('maps "failed" status to failCall', async () => {
      const call = { id: 'call-2', externalCallId: 'CA_fail' };
      prismaMock.call.findFirst.mockResolvedValue(call);
      (failCall as any).mockResolvedValue(call);

      await handleStatusCallback({
        CallSid: 'CA_fail',
        CallStatus: 'failed',
      });

      expect(failCall).toHaveBeenCalledWith('call-2', 'failed');
    });

    it('maps "busy" to FAILED', async () => {
      const call = { id: 'call-3', externalCallId: 'CA_busy' };
      prismaMock.call.findFirst.mockResolvedValue(call);
      (failCall as any).mockResolvedValue(call);

      await handleStatusCallback({
        CallSid: 'CA_busy',
        CallStatus: 'busy',
      });

      expect(failCall).toHaveBeenCalledWith('call-3', 'busy');
    });

    it('maps "ringing" to RINGING', async () => {
      const call = { id: 'call-4', externalCallId: 'CA_ring' };
      prismaMock.call.findFirst.mockResolvedValue(call);
      (updateCallStatus as any).mockResolvedValue(call);

      await handleStatusCallback({
        CallSid: 'CA_ring',
        CallStatus: 'ringing',
      });

      expect(updateCallStatus).toHaveBeenCalledWith('call-4', 'RINGING');
    });

    it('ignores unknown CallSid gracefully', async () => {
      prismaMock.call.findFirst.mockResolvedValue(null);

      await handleStatusCallback({
        CallSid: 'CA_unknown',
        CallStatus: 'completed',
      });

      expect(endCall).not.toHaveBeenCalled();
      expect(failCall).not.toHaveBeenCalled();
    });
  });

  describe('makeOutboundCallTwilio', () => {
    it('creates call, session, and initiates Twilio call', async () => {
      const orgId = 'org-1';
      const assistant = buildAssistant({
        id: 'asst-1',
        organizationId: orgId,
        model: { provider: 'openai', systemPrompt: 'Hi' },
      });
      const phone = buildPhoneNumber({
        id: 'phone-1',
        organizationId: orgId,
        number: '+15559998888',
      });
      const call = { id: 'call-out-1', organizationId: orgId, assistantId: 'asst-1' };
      const session = { id: 'session-out-1' };

      prismaMock.assistant.findFirst.mockResolvedValue(assistant);
      prismaMock.phoneNumber.findFirst.mockResolvedValue(phone);
      (createCall as any).mockResolvedValue(call);
      (updateCallStatus as any).mockResolvedValue(call);
      (createSession as any).mockResolvedValue(session);
      prismaMock.call.update.mockResolvedValue(call);
      (makeCall as any).mockResolvedValue('CA_twilio_sid');

      const result = await makeOutboundCallTwilio({
        organizationId: orgId,
        assistantId: 'asst-1',
        customerNumber: '+15551234567',
        phoneNumberId: 'phone-1',
      });

      expect(result.callId).toBe('call-out-1');
      expect(result.externalCallId).toBe('CA_twilio_sid');

      expect(createCall).toHaveBeenCalledWith(expect.objectContaining({
        type: 'OUTBOUND',
        customerNumber: '+15551234567',
      }));
      expect(createSession).toHaveBeenCalled();
      expect(makeCall).toHaveBeenCalledWith(
        '+15551234567',
        '+15559998888',
        'https://api.example.com',
      );
      expect(fireWebhookEvent).toHaveBeenCalledWith(orgId, 'call.started', expect.any(Object));
    });

    it('throws 404 when assistant not found', async () => {
      prismaMock.assistant.findFirst.mockResolvedValue(null);

      await expect(
        makeOutboundCallTwilio({
          organizationId: 'org-1',
          assistantId: 'missing',
          customerNumber: '+15551234567',
          phoneNumberId: 'phone-1',
        }),
      ).rejects.toThrow('Assistant not found');
    });

    it('throws 404 when phone number not found', async () => {
      prismaMock.assistant.findFirst.mockResolvedValue(
        buildAssistant({ organizationId: 'org-1' }),
      );
      prismaMock.phoneNumber.findFirst.mockResolvedValue(null);

      await expect(
        makeOutboundCallTwilio({
          organizationId: 'org-1',
          assistantId: 'asst-1',
          customerNumber: '+15551234567',
          phoneNumberId: 'missing',
        }),
      ).rejects.toThrow('Phone number not found');
    });
  });
});
