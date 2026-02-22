import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { executeTool } from './tool-executor.js';

describe('executeTool', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('FUNCTION tool', () => {
    const functionTool = {
      id: 'tool-1',
      type: 'FUNCTION' as const,
      name: 'check_availability',
      serverUrl: 'https://example.com/webhook',
      serverSecret: 'my-secret',
    };

    it('should call serverUrl with HMAC-signed body', async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ result: 'available' })),
      });

      const result = await executeTool(functionTool, '{"date":"2026-01-01"}', 'session-1');

      expect(result.success).toBe(true);
      expect(result.output).toBe('available');
      expect(fetchSpy).toHaveBeenCalledOnce();

      const [url, options] = fetchSpy.mock.calls[0];
      expect(url).toBe('https://example.com/webhook');
      expect(options.method).toBe('POST');
      expect(options.headers['X-Load-Signature']).toMatch(/^sha256=/);
    });

    it('should return error when serverUrl is not configured', async () => {
      const noUrlTool = { ...functionTool, serverUrl: null };
      const result = await executeTool(noUrlTool, '{}', 'session-1');

      expect(result.success).toBe(false);
      expect(result.output).toContain('no server URL');
    });

    it('should handle non-ok HTTP response', async () => {
      fetchSpy.mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve(JSON.stringify({ error: 'Internal error' })),
      });

      const result = await executeTool(functionTool, '{}', 'session-1');

      expect(result.success).toBe(false);
      expect(result.output).toContain('Internal error');
    });

    it('should handle fetch failure', async () => {
      fetchSpy.mockRejectedValue(new Error('Network error'));

      const result = await executeTool(functionTool, '{}', 'session-1');

      expect(result.success).toBe(false);
      expect(result.output).toContain('Network error');
    });

    it('should handle non-JSON response body', async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        text: () => Promise.resolve('plain text response'),
      });

      const result = await executeTool(functionTool, '{}', 'session-1');

      expect(result.success).toBe(true);
      expect(result.output).toEqual({ raw: 'plain text response' });
    });
  });

  describe('TRANSFER_CALL tool', () => {
    const transferTool = {
      id: 'tool-2',
      type: 'TRANSFER_CALL' as const,
      name: 'transfer_to_sales',
      metadata: { targetAssistantId: 'assistant-sales' },
    };

    it('should return transfer signal with target assistant ID', async () => {
      const result = await executeTool(transferTool, '{"reason":"needs sales"}', 'session-1');

      expect(result.success).toBe(true);
      expect(result.signal).toBe('transfer_call');
      expect(result.targetAssistantId).toBe('assistant-sales');
    });

    it('should fail when no targetAssistantId in metadata', async () => {
      const noTargetTool = { ...transferTool, metadata: null };
      const result = await executeTool(noTargetTool, '{}', 'session-1');

      expect(result.success).toBe(false);
      expect(result.output).toContain('targetAssistantId');
    });
  });

  describe('END_CALL tool', () => {
    const endCallTool = {
      id: 'tool-3',
      type: 'END_CALL' as const,
      name: 'end_call',
    };

    it('should return end_call signal', async () => {
      const result = await executeTool(endCallTool, '{"reason":"customer satisfied"}', 'session-1');

      expect(result.success).toBe(true);
      expect(result.signal).toBe('end_call');
      expect(result.output).toContain('customer satisfied');
    });
  });
});
