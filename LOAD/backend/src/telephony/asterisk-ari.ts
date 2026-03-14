/**
 * Asterisk ARI (Asterisk REST Interface) client wrapper.
 *
 * Provides a clean interface over the `ari-client` npm package for LOAD's
 * telephony system. Handles connection lifecycle, event mapping, and
 * channel/bridge management.
 *
 * Used by `call-bridge.ts` to manage channels and bridges for voice calls.
 */

import ariClient from 'ari-client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AriClientConfig {
  url: string;
  username: string;
  password: string;
  appName: string;
}

export interface AriEventHandlers {
  onStasisStart: (event: StasisStartEvent) => void;
  onStasisEnd: (event: StasisEndEvent) => void;
  onChannelDtmf: (event: ChannelDtmfEvent) => void;
}

export interface StasisStartEvent {
  channelId: string;
  callerNumber: string;
  calledNumber: string;
  args: string[];
}

export interface StasisEndEvent {
  channelId: string;
}

export interface ChannelDtmfEvent {
  channelId: string;
  digit: string;
}

export interface ExternalMediaChannel {
  channelId: string;
  host: string;
  port: number;
}

/** Default audio format for Asterisk ExternalMedia (16 kHz signed linear 16-bit). */
const DEFAULT_EXTERNAL_MEDIA_FORMAT = 'slin16';

/** Maximum number of reconnection attempts before giving up. */
const MAX_RECONNECT_ATTEMPTS = 5;

/** Base delay (ms) between reconnection attempts (doubles each attempt). */
const RECONNECT_BASE_DELAY_MS = 1_000;

// ---------------------------------------------------------------------------
// AsteriskAriClient
// ---------------------------------------------------------------------------

export class AsteriskAriClient {
  private readonly config: AriClientConfig;
  private client: any = null;
  private _connected = false;
  private eventHandlers: AriEventHandlers | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(config: AriClientConfig) {
    this.config = Object.freeze({ ...config });
  }

  // -----------------------------------------------------------------------
  // Connection
  // -----------------------------------------------------------------------

  /**
   * Connect to the Asterisk ARI WebSocket, register the Stasis application,
   * and wire up event handlers.
   */
  async connect(handlers: AriEventHandlers): Promise<void> {
    this.eventHandlers = handlers;

    try {
      this.client = await this.createConnection();
      this._connected = true;
      this.reconnectAttempts = 0;

      this.registerEventHandlers(this.client, handlers);

      // Start the Stasis WebSocket subscription
      await this.startStasisApp(this.client);

      console.log(
        `[AsteriskARI] Connected to ${this.config.url} as app "${this.config.appName}"`
      );
    } catch (error) {
      this._connected = false;
      console.error('[AsteriskARI] Connection failed:', error);
      throw error;
    }
  }

  /**
   * Disconnect from ARI and clean up resources.
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.client) {
      try {
        this.client.stop();
      } catch {
        // Client may already be disconnected -- ignore.
      }
      this.client = null;
    }

    this._connected = false;
    this.eventHandlers = null;
    console.log('[AsteriskARI] Disconnected');
  }

  /** Whether the client is currently connected to ARI. */
  get connected(): boolean {
    return this._connected;
  }

  // -----------------------------------------------------------------------
  // Channel operations
  // -----------------------------------------------------------------------

  /**
   * Originate (place) a new outbound call.
   *
   * @returns The channel ID of the newly created channel.
   */
  async originateCall(params: {
    endpoint: string;
    callerId: string;
    context?: string;
    extension?: string;
    appArgs?: string[];
  }): Promise<string> {
    const client = this.ensureConnected();

    const originateParams: Record<string, unknown> = {
      endpoint: params.endpoint,
      callerId: params.callerId,
      app: this.config.appName,
    };

    if (params.context) {
      originateParams.context = params.context;
    }
    if (params.extension) {
      originateParams.extension = params.extension;
    }
    if (params.appArgs && params.appArgs.length > 0) {
      originateParams.appArgs = params.appArgs.join(',');
    }

    const channel = await client.channels.originate(originateParams);
    const channelId: string = channel.id ?? channel.name;

    console.log(
      `[AsteriskARI] Originated call to ${params.endpoint} -> channel ${channelId}`
    );

    return channelId;
  }

  /**
   * Create an ExternalMedia channel for raw audio I/O over UDP.
   *
   * Asterisk will send/receive audio at the given host:port using the
   * specified format (defaults to `slin16` -- 16 kHz signed linear 16-bit).
   */
  async createExternalMedia(params: {
    app: string;
    host: string;
    port: number;
    format?: string;
  }): Promise<ExternalMediaChannel> {
    const client = this.ensureConnected();

    const externalMediaParams = {
      app: params.app,
      external_host: `${params.host}:${params.port}`,
      format: params.format ?? DEFAULT_EXTERNAL_MEDIA_FORMAT,
    };

    const channel = await client.channels.externalMedia(externalMediaParams);
    const channelId: string = channel.id ?? channel.name;

    console.log(
      `[AsteriskARI] Created ExternalMedia channel ${channelId} -> ${params.host}:${params.port} (${externalMediaParams.format})`
    );

    return {
      channelId,
      host: params.host,
      port: params.port,
    };
  }

  /**
   * Hang up a channel.
   *
   * Handles the case where the channel has already been destroyed (404)
   * gracefully by logging a warning instead of throwing.
   */
  async hangupChannel(channelId: string): Promise<void> {
    const client = this.ensureConnected();

    try {
      await client.channels.hangup({ channelId });
      console.log(`[AsteriskARI] Hung up channel ${channelId}`);
    } catch (error: any) {
      if (this.isNotFoundError(error)) {
        console.warn(
          `[AsteriskARI] Channel ${channelId} already gone when attempting hangup`
        );
      } else {
        throw error;
      }
    }
  }

  // -----------------------------------------------------------------------
  // Bridge operations
  // -----------------------------------------------------------------------

  /**
   * Create a new mixing bridge.
   *
   * @param bridgeType - ARI bridge type (defaults to `"mixing"`).
   * @returns The bridge ID.
   */
  async createBridge(bridgeType?: string): Promise<string> {
    const client = this.ensureConnected();

    const bridge = await client.bridges.create({
      type: bridgeType ?? 'mixing',
    });
    const bridgeId: string = bridge.id;

    console.log(`[AsteriskARI] Created bridge ${bridgeId} (${bridgeType ?? 'mixing'})`);
    return bridgeId;
  }

  /**
   * Add a channel to an existing bridge.
   */
  async addChannelToBridge(bridgeId: string, channelId: string): Promise<void> {
    const client = this.ensureConnected();

    await client.bridges.addChannel({ bridgeId, channel: channelId });
    console.log(
      `[AsteriskARI] Added channel ${channelId} to bridge ${bridgeId}`
    );
  }

  /**
   * Destroy a bridge.
   *
   * Handles the case where the bridge has already been destroyed (404)
   * gracefully by logging a warning instead of throwing.
   */
  async destroyBridge(bridgeId: string): Promise<void> {
    const client = this.ensureConnected();

    try {
      await client.bridges.destroy({ bridgeId });
      console.log(`[AsteriskARI] Destroyed bridge ${bridgeId}`);
    } catch (error: any) {
      if (this.isNotFoundError(error)) {
        console.warn(
          `[AsteriskARI] Bridge ${bridgeId} already gone when attempting destroy`
        );
      } else {
        throw error;
      }
    }
  }

  // -----------------------------------------------------------------------
  // Audio playback
  // -----------------------------------------------------------------------

  /**
   * Play audio to a channel via ARI playback.
   *
   * NOTE: This is a stub. ExternalMedia channels handle audio via UDP, not
   * through ARI playback. This method exists to satisfy the interface contract
   * and will be implemented if direct ARI playback is needed in the future.
   */
  async playAudio(channelId: string, _audioData: Buffer): Promise<void> {
    this.ensureConnected();

    console.warn(
      `[AsteriskARI] playAudio called for channel ${channelId} -- ` +
        'this is a stub. ExternalMedia audio is handled via UDP, not ARI playback.'
    );
  }

  // -----------------------------------------------------------------------
  // Private helpers
  // -----------------------------------------------------------------------

  /**
   * Create a new ari-client connection.
   *
   * The `ari-client` package exposes `connect(url, username, password, cb)`
   * which returns a promise (bluebird) that resolves to a Client instance.
   */
  private createConnection(): Promise<any> {
    return new Promise<any>((resolve, reject) => {
      ariClient.connect(
        this.config.url,
        this.config.username,
        this.config.password,
        (err: Error | null, client: any) => {
          if (err) {
            reject(err);
          } else {
            resolve(client);
          }
        }
      );
    });
  }

  /**
   * Register ARI event listeners on the client instance and map them to
   * the simplified `AriEventHandlers` interface.
   */
  private registerEventHandlers(client: any, handlers: AriEventHandlers): void {
    client.on('StasisStart', (event: any, channel: any) => {
      const mapped: StasisStartEvent = {
        channelId: channel?.id ?? event?.channel?.id ?? '',
        callerNumber: event?.channel?.caller?.number ?? '',
        calledNumber: event?.channel?.dialplan?.exten ?? '',
        args: event?.args ?? [],
      };

      console.log(
        `[AsteriskARI] StasisStart: channel=${mapped.channelId} ` +
          `caller=${mapped.callerNumber} called=${mapped.calledNumber}`
      );

      handlers.onStasisStart(mapped);
    });

    client.on('StasisEnd', (event: any, channel: any) => {
      const mapped: StasisEndEvent = {
        channelId: channel?.id ?? event?.channel?.id ?? '',
      };

      console.log(`[AsteriskARI] StasisEnd: channel=${mapped.channelId}`);
      handlers.onStasisEnd(mapped);
    });

    client.on('ChannelDtmfReceived', (event: any, channel: any) => {
      const mapped: ChannelDtmfEvent = {
        channelId: channel?.id ?? event?.channel?.id ?? '',
        digit: event?.digit ?? '',
      };

      console.log(
        `[AsteriskARI] DTMF: channel=${mapped.channelId} digit=${mapped.digit}`
      );

      handlers.onChannelDtmf(mapped);
    });

    // Handle unexpected WebSocket disconnects with automatic reconnection.
    client.on('WebSocketReconnecting', (err: any) => {
      console.warn('[AsteriskARI] WebSocket reconnecting...', err?.message);
    });

    client.on('WebSocketMaxRetries', (err: any) => {
      console.error(
        '[AsteriskARI] WebSocket max retries reached:',
        err?.message
      );
      this._connected = false;
      this.scheduleReconnect();
    });
  }

  /**
   * Start the Stasis application subscription on the connected client.
   */
  private startStasisApp(client: any): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      client.start(this.config.appName, (err: Error | null) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Schedule a full reconnection attempt (re-create the ARI client).
   *
   * Uses exponential back-off up to `MAX_RECONNECT_ATTEMPTS`.
   */
  private scheduleReconnect(): void {
    if (!this.eventHandlers) {
      return;
    }

    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error(
        `[AsteriskARI] Exhausted ${MAX_RECONNECT_ATTEMPTS} reconnection attempts. Giving up.`
      );
      return;
    }

    const delay =
      RECONNECT_BASE_DELAY_MS * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts += 1;

    console.log(
      `[AsteriskARI] Scheduling reconnect attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay}ms`
    );

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;

      if (!this.eventHandlers) {
        return;
      }

      try {
        // Dispose of the old client if it still exists.
        if (this.client) {
          try {
            this.client.stop();
          } catch {
            // Ignore -- old client may already be dead.
          }
          this.client = null;
        }

        this.client = await this.createConnection();
        this._connected = true;
        this.reconnectAttempts = 0;

        this.registerEventHandlers(this.client, this.eventHandlers);
        await this.startStasisApp(this.client);

        console.log('[AsteriskARI] Reconnected successfully');
      } catch (error) {
        console.error('[AsteriskARI] Reconnect attempt failed:', error);
        this._connected = false;
        this.scheduleReconnect();
      }
    }, delay);
  }

  /**
   * Ensure the ARI client is connected; throw a descriptive error if not.
   */
  private ensureConnected(): any {
    if (!this._connected || !this.client) {
      throw Object.assign(
        new Error(
          'ARI client is not connected. Call connect() first or wait for reconnection.'
        ),
        { statusCode: 503 }
      );
    }
    return this.client;
  }

  /**
   * Detect ARI "not found" (404) responses so callers can handle
   * already-destroyed resources gracefully.
   */
  private isNotFoundError(error: any): boolean {
    if (error?.statusCode === 404) return true;
    if (error?.status === 404) return true;
    const message = String(error?.message ?? '').toLowerCase();
    return message.includes('not found') || message.includes('404');
  }
}
