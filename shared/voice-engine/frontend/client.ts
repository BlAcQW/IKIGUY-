export interface VoiceClientOptions {
  maxRetries?: number;
  createPeerConnection?: () => RTCPeerConnection;
  getUserMedia?: (constraints: MediaStreamConstraints) => Promise<MediaStream>;
}

export interface StatusDetail {
  type: 'connection' | 'ice' | 'retry' | 'error';
  state: string;
}

export class VoiceClient extends EventTarget {
  private pc: RTCPeerConnection | null = null;
  private retries = 0;
  private readonly maxRetries: number;
  private readonly createPeerConnection: () => RTCPeerConnection;
  private readonly getUserMedia: (constraints: MediaStreamConstraints) => Promise<MediaStream>;

  constructor(opts: VoiceClientOptions = {}) {
    super();
    this.maxRetries = opts.maxRetries ?? 3;
    this.createPeerConnection = opts.createPeerConnection ?? (() => new RTCPeerConnection());
    this.getUserMedia = opts.getUserMedia ?? ((c) => navigator.mediaDevices.getUserMedia(c));
  }

  async connect(): Promise<void> {
    this.pc = this.createPeerConnection();

    this.pc.addEventListener('connectionstatechange', () => {
      const state = this.pc!.connectionState;
      this.dispatchEvent(new CustomEvent<StatusDetail>('status', { detail: { type: 'connection', state } }));
      if (state === 'failed' || state === 'disconnected') {
        this.retry();
      }
    });

    this.pc.addEventListener('iceconnectionstatechange', () => {
      const state = this.pc!.iceConnectionState;
      this.dispatchEvent(new CustomEvent<StatusDetail>('status', { detail: { type: 'ice', state } }));
    });

    const stream = await this.getUserMedia({ audio: true });
    const [track] = stream.getAudioTracks();
    if (track) {
      this.pc.addTrack(track, stream);
    }

    const offer = await this.pc.createOffer();
    await this.pc.setLocalDescription(offer);
  }

  private async retry(): Promise<void> {
    if (this.retries >= this.maxRetries) {
      this.dispatchEvent(new CustomEvent<StatusDetail>('status', { detail: { type: 'error', state: 'max-retries' } }));
      return;
    }
    this.retries += 1;
    this.dispatchEvent(new CustomEvent<StatusDetail>('status', { detail: { type: 'retry', state: String(this.retries) } }));
    this.pc?.close();
    await this.connect();
  }
}
