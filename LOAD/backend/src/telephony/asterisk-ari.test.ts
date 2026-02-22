import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Mock ari-client before importing the module under test
// ---------------------------------------------------------------------------

vi.mock('ari-client', () => ({
  default: {
    connect: vi.fn(),
  },
}));

import { AsteriskAriClient } from './asterisk-ari.js';
import type { AriEventHandlers } from './asterisk-ari.js';
import ariClient from 'ari-client';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createMockAriClient() {
  return {
    start: vi.fn((_app: string, cb: (err: Error | null) => void) => cb(null)),
    on: vi.fn(),
    stop: vi.fn(),
    channels: {
      originate: vi.fn().mockResolvedValue({ id: 'channel-123' }),
      hangup: vi.fn().mockResolvedValue(undefined),
      externalMedia: vi.fn().mockResolvedValue({ id: 'ext-media-456' }),
    },
    bridges: {
      create: vi.fn().mockResolvedValue({ id: 'bridge-789' }),
      addChannel: vi.fn().mockResolvedValue(undefined),
      destroy: vi.fn().mockResolvedValue(undefined),
    },
  };
}

function createDefaultConfig() {
  return {
    url: 'http://localhost:8088',
    username: 'asterisk',
    password: 'secret',
    appName: 'load-test',
  };
}

function createEventHandlers(): AriEventHandlers {
  return {
    onStasisStart: vi.fn(),
    onStasisEnd: vi.fn(),
    onChannelDtmf: vi.fn(),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AsteriskAriClient', () => {
  let client: AsteriskAriClient;
  let mockAri: ReturnType<typeof createMockAriClient>;
  let handlers: AriEventHandlers;

  beforeEach(() => {
    vi.clearAllMocks();

    mockAri = createMockAriClient();
    handlers = createEventHandlers();
    client = new AsteriskAriClient(createDefaultConfig());

    // Set up the ari-client.connect mock to invoke callback with the mock client
    (ariClient.connect as any).mockImplementation(
      (_url: string, _user: string, _pass: string, cb: Function) => {
        cb(null, mockAri);
      },
    );
  });

  it('connects to ARI and starts stasis app', async () => {
    await client.connect(handlers);

    expect(ariClient.connect).toHaveBeenCalledWith(
      'http://localhost:8088',
      'asterisk',
      'secret',
      expect.any(Function),
    );
    expect(mockAri.start).toHaveBeenCalledWith('load-test', expect.any(Function));
    expect(client.connected).toBe(true);
  });

  it('throws when originating without connection', async () => {
    await expect(
      client.originateCall({
        endpoint: 'PJSIP/100',
        callerId: '+15551234567',
      }),
    ).rejects.toThrow('ARI client is not connected');
  });

  it('originates a call and returns channel ID', async () => {
    await client.connect(handlers);

    const channelId = await client.originateCall({
      endpoint: 'PJSIP/100',
      callerId: '+15551234567',
    });

    expect(channelId).toBe('channel-123');
    expect(mockAri.channels.originate).toHaveBeenCalledWith(
      expect.objectContaining({
        endpoint: 'PJSIP/100',
        callerId: '+15551234567',
        app: 'load-test',
      }),
    );
  });

  it('creates external media channel', async () => {
    await client.connect(handlers);

    const extMedia = await client.createExternalMedia({
      app: 'load-test',
      host: '127.0.0.1',
      port: 12000,
    });

    expect(extMedia.channelId).toBe('ext-media-456');
    expect(extMedia.host).toBe('127.0.0.1');
    expect(extMedia.port).toBe(12000);
    expect(mockAri.channels.externalMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        app: 'load-test',
        external_host: '127.0.0.1:12000',
        format: 'slin16',
      }),
    );
  });

  it('creates bridge', async () => {
    await client.connect(handlers);

    const bridgeId = await client.createBridge();

    expect(bridgeId).toBe('bridge-789');
    expect(mockAri.bridges.create).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'mixing' }),
    );
  });

  it('adds channel to bridge', async () => {
    await client.connect(handlers);

    await client.addChannelToBridge('bridge-789', 'channel-123');

    expect(mockAri.bridges.addChannel).toHaveBeenCalledWith({
      bridgeId: 'bridge-789',
      channel: 'channel-123',
    });
  });

  it('handles hangup on already-gone channel gracefully', async () => {
    await client.connect(handlers);

    // Simulate a 404 error (channel already gone)
    mockAri.channels.hangup.mockRejectedValue(
      Object.assign(new Error('Channel not found'), { statusCode: 404 }),
    );

    // Should NOT throw
    await expect(client.hangupChannel('channel-gone')).resolves.toBeUndefined();
  });

  it('handles destroy on already-gone bridge gracefully', async () => {
    await client.connect(handlers);

    // Simulate a 404 error (bridge already gone)
    mockAri.bridges.destroy.mockRejectedValue(
      Object.assign(new Error('Bridge not found'), { statusCode: 404 }),
    );

    // Should NOT throw
    await expect(client.destroyBridge('bridge-gone')).resolves.toBeUndefined();
  });

  it('disconnect clears state', async () => {
    await client.connect(handlers);
    expect(client.connected).toBe(true);

    client.disconnect();

    expect(client.connected).toBe(false);
    expect(mockAri.stop).toHaveBeenCalled();
  });

  it('re-throws non-404 errors from hangupChannel', async () => {
    await client.connect(handlers);

    mockAri.channels.hangup.mockRejectedValue(new Error('Internal server error'));

    await expect(client.hangupChannel('channel-123')).rejects.toThrow(
      'Internal server error',
    );
  });

  it('re-throws non-404 errors from destroyBridge', async () => {
    await client.connect(handlers);

    mockAri.bridges.destroy.mockRejectedValue(new Error('Internal server error'));

    await expect(client.destroyBridge('bridge-789')).rejects.toThrow(
      'Internal server error',
    );
  });

  it('throws when connect callback returns an error', async () => {
    (ariClient.connect as any).mockImplementation(
      (_url: string, _user: string, _pass: string, cb: Function) => {
        cb(new Error('Connection refused'), null);
      },
    );

    await expect(client.connect(handlers)).rejects.toThrow('Connection refused');
    expect(client.connected).toBe(false);
  });
});
