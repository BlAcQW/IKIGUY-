declare module 'ari-client' {
  interface AriClient {
    start(appName: string): void;
    on(event: string, handler: (...args: any[]) => void): void;
    removeAllListeners(): void;
    Channel(): any;
    Bridge(): any;
    channels: {
      originate(params: Record<string, unknown>, callback: (err: Error | null, channel: any) => void): void;
      hangup(params: { channelId: string }, callback: (err: Error | null) => void): void;
      externalMedia(params: Record<string, unknown>, callback: (err: Error | null, channel: any) => void): void;
    };
    bridges: {
      create(params: Record<string, unknown>, callback: (err: Error | null, bridge: any) => void): void;
      addChannel(params: { bridgeId: string; channel: string }, callback: (err: Error | null) => void): void;
      destroy(params: { bridgeId: string }, callback: (err: Error | null) => void): void;
    };
  }

  export function connect(
    url: string,
    username: string,
    password: string,
    callback: (err: Error | null, client: AriClient) => void
  ): void;
}
