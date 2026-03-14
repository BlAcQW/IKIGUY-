/**
 * UDP Audio Bridge for Asterisk ExternalMedia.
 *
 * Manages a pool of UDP sockets that bridge audio between Asterisk
 * ExternalMedia channels and the Node.js voice pipeline. Each active call
 * gets a dedicated UDP port from the pool.
 *
 * Audio flow:
 *   Asterisk ExternalMedia → UDP socket → onAudioReceived callback → pipeline
 *   Pipeline TTS output → sendAudio() → UDP socket → Asterisk ExternalMedia
 *
 * Key features:
 *   - Port pool with configurable range (default 20000–20100)
 *   - Remote address learning (first packet from Asterisk teaches reply address)
 *   - Paced audio sends at real-time rate (640 bytes / 20ms for 16kHz slin16)
 */

import dgram from 'node:dgram';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UdpBridgeOptions {
  /** IP address that Asterisk can reach for UDP audio. */
  host: string;
  /** First port in the pool range (inclusive). */
  portStart: number;
  /** Last port in the pool range (inclusive). */
  portEnd: number;
}

export interface UdpAudioSession {
  sessionId: string;
  localPort: number;
  socket: dgram.Socket;
  remoteAddress: string | null;
  remotePort: number | null;
  /** Timer handle for paced audio sending. */
  sendTimer: ReturnType<typeof setTimeout> | null;
}

export type AudioReceivedCallback = (sessionId: string, chunk: Buffer) => void;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Bytes per packet for 16kHz slin16 at 20ms intervals (16000 * 2 bytes * 0.020s). */
const PACKET_SIZE = 640;

/** Interval between paced audio sends in ms. */
const SEND_INTERVAL_MS = 20;

// ---------------------------------------------------------------------------
// UdpAudioBridge
// ---------------------------------------------------------------------------

export class UdpAudioBridge {
  private readonly options: UdpBridgeOptions;
  private readonly availablePorts: number[];
  private readonly sessions: Map<string, UdpAudioSession>;
  private onAudioReceived: AudioReceivedCallback | null;

  constructor(options: UdpBridgeOptions) {
    this.options = Object.freeze({ ...options });
    this.sessions = new Map();
    this.onAudioReceived = null;

    // Initialize port pool
    this.availablePorts = [];
    for (let port = options.portStart; port <= options.portEnd; port++) {
      this.availablePorts.push(port);
    }

    console.log(
      `[UdpAudioBridge] Initialized with ${this.availablePorts.length} ports ` +
        `(${options.portStart}–${options.portEnd}) on host ${options.host}`
    );
  }

  /**
   * Register the callback invoked when audio is received from Asterisk.
   */
  setAudioCallback(callback: AudioReceivedCallback): void {
    this.onAudioReceived = callback;
  }

  /**
   * The host address Asterisk should send audio to.
   */
  get host(): string {
    return this.options.host;
  }

  /**
   * Create a new UDP audio session for a call.
   *
   * Allocates a port from the pool, binds a UDP socket, and starts
   * listening for incoming audio from Asterisk.
   *
   * @returns The local port number the socket is bound to.
   * @throws If no ports are available in the pool.
   */
  async createSession(sessionId: string): Promise<number> {
    if (this.sessions.has(sessionId)) {
      const existing = this.sessions.get(sessionId)!;
      console.warn(
        `[UdpAudioBridge] Session ${sessionId} already exists on port ${existing.localPort}`
      );
      return existing.localPort;
    }

    const port = this.availablePorts.shift();
    if (port === undefined) {
      throw new Error(
        '[UdpAudioBridge] No available UDP ports in pool. ' +
          `All ${this.options.portEnd - this.options.portStart + 1} ports are in use.`
      );
    }

    const socket = dgram.createSocket('udp4');

    const session: UdpAudioSession = {
      sessionId,
      localPort: port,
      socket,
      remoteAddress: null,
      remotePort: null,
      sendTimer: null,
    };

    // Register session immediately (before async bind) to prevent
    // concurrent createSession calls from double-allocating this port
    this.sessions.set(sessionId, session);

    // Listen for incoming audio from Asterisk
    socket.on('message', (msg: Buffer, rinfo: dgram.RemoteInfo) => {
      // Learn remote address from first packet (handles Docker networking/NAT)
      if (session.remoteAddress === null) {
        session.remoteAddress = rinfo.address;
        session.remotePort = rinfo.port;
        console.log(
          `[UdpAudioBridge] Session ${sessionId}: learned remote ` +
            `${rinfo.address}:${rinfo.port}`
        );
      }

      if (this.onAudioReceived) {
        this.onAudioReceived(sessionId, msg);
      }
    });

    // Bind socket to the allocated port
    try {
      await new Promise<void>((resolve, reject) => {
        socket.once('error', reject);
        socket.bind(port, '0.0.0.0', () => {
          resolve();
        });
      });
    } catch (bindError) {
      // Bind failed — return port to pool and remove session
      this.sessions.delete(sessionId);
      this.availablePorts.push(port);
      try { socket.close(); } catch { /* ignore */ }
      throw new Error(
        `[UdpAudioBridge] Failed to bind port ${port} for session ${sessionId}: ${bindError}`
      );
    }

    // Register permanent error handler after successful bind
    socket.on('error', (err) => {
      console.error(
        `[UdpAudioBridge] Socket error on session ${sessionId} (port ${port}):`,
        err
      );
    });

    console.log(
      `[UdpAudioBridge] Created session ${sessionId} on port ${port} ` +
        `(${this.availablePorts.length} ports remaining)`
    );

    return port;
  }

  /**
   * Send TTS audio to Asterisk at real-time pace.
   *
   * Breaks the audio buffer into 640-byte packets (20ms of 16kHz slin16)
   * and sends them at 20ms intervals so Asterisk doesn't drop packets
   * from receiving too fast.
   */
  async sendAudio(sessionId: string, audioBuffer: Buffer): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      console.warn(
        `[UdpAudioBridge] Cannot send audio: session ${sessionId} not found`
      );
      return;
    }

    if (!session.remoteAddress || !session.remotePort) {
      console.warn(
        `[UdpAudioBridge] Cannot send audio for session ${sessionId}: ` +
          'remote address not yet learned (no packet received from Asterisk)'
      );
      return;
    }

    // Cancel any in-progress send
    if (session.sendTimer) {
      clearTimeout(session.sendTimer);
      session.sendTimer = null;
    }

    const totalPackets = Math.ceil(audioBuffer.length / PACKET_SIZE);
    const { remoteAddress, remotePort } = session;

    console.log(
      `[UdpAudioBridge] Sending ${audioBuffer.length} bytes (${totalPackets} packets) ` +
        `to ${remoteAddress}:${remotePort} for session ${sessionId}`
    );

    let packetIndex = 0;

    const sendNext = (): void => {
      // Check session still exists (may have been cleaned up during send)
      if (!this.sessions.has(sessionId)) {
        return;
      }

      if (packetIndex >= totalPackets) {
        session.sendTimer = null;
        return;
      }

      const offset = packetIndex * PACKET_SIZE;
      const end = Math.min(offset + PACKET_SIZE, audioBuffer.length);
      const packet = audioBuffer.subarray(offset, end);

      session.socket.send(packet, remotePort, remoteAddress, (err) => {
        if (err) {
          console.error(
            `[UdpAudioBridge] Send error for session ${sessionId}:`,
            err
          );
        }
      });

      packetIndex++;
      session.sendTimer = setTimeout(sendNext, SEND_INTERVAL_MS);
    };

    sendNext();
  }

  /**
   * Close a UDP audio session and return the port to the pool.
   */
  closeSession(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return;
    }

    // Cancel any in-progress paced send
    if (session.sendTimer) {
      clearTimeout(session.sendTimer);
      session.sendTimer = null;
    }

    try {
      session.socket.close();
    } catch {
      // Socket may already be closed
    }

    // Return port to pool
    this.availablePorts.push(session.localPort);
    this.sessions.delete(sessionId);

    console.log(
      `[UdpAudioBridge] Closed session ${sessionId} (port ${session.localPort} returned, ` +
        `${this.availablePorts.length} ports available)`
    );
  }

  /**
   * Close all sessions and release all resources.
   */
  closeAll(): void {
    for (const [sessionId] of this.sessions) {
      this.closeSession(sessionId);
    }
    console.log('[UdpAudioBridge] All sessions closed');
  }
}
