import { test } from 'node:test';
import assert from 'node:assert/strict';
import { VoiceClient } from './client.ts';

class MockRTCPeerConnection extends EventTarget {
  connectionState: RTCPeerConnectionState = 'new';
  iceConnectionState: RTCIceConnectionState = 'new';
  addTrackCalled = false;
  offerCreated = false;
  addTrack() {
    this.addTrackCalled = true;
  }
  createOffer() {
    this.offerCreated = true;
    return Promise.resolve({} as RTCSessionDescriptionInit);
  }
  setLocalDescription() {
    return Promise.resolve();
  }
  close() {}
  changeConnectionState(state: RTCPeerConnectionState) {
    this.connectionState = state;
    this.dispatchEvent(new Event('connectionstatechange'));
  }
}

const mockStream: MediaStream = {
  getAudioTracks: () => [{} as MediaStreamTrack],
} as any;

test('adds microphone track before creating offer', async () => {
  const pc = new MockRTCPeerConnection();
  const client = new VoiceClient({
    createPeerConnection: () => pc,
    getUserMedia: async () => mockStream,
  });
  await client.connect();
  assert.ok(pc.addTrackCalled);
  assert.ok(pc.offerCreated);
});

test('retries on dropped connection and emits status events', async () => {
  let pcCount = 0;
  const pcs: MockRTCPeerConnection[] = [];
  const client = new VoiceClient({
    createPeerConnection: () => {
      const pc = new MockRTCPeerConnection();
      pcs.push(pc);
      pcCount++;
      return pc;
    },
    getUserMedia: async () => mockStream,
    maxRetries: 1,
  });

  const events: any[] = [];
  client.addEventListener('status', (e: any) => events.push(e.detail));

  await client.connect();
  pcs[0].changeConnectionState('failed');
  await new Promise((r) => setTimeout(r, 0));

  assert.equal(pcCount, 2);
  assert.ok(events.some((e) => e.type === 'connection' && e.state === 'failed'));
  assert.ok(events.some((e) => e.type === 'retry'));
});

test('emits error after exceeding max retries', async () => {
  const pc = new MockRTCPeerConnection();
  const client = new VoiceClient({
    createPeerConnection: () => pc,
    getUserMedia: async () => mockStream,
    maxRetries: 0,
  });

  let errorEvent = false;
  client.addEventListener('status', (e: any) => {
    if (e.detail.type === 'error') {
      errorEvent = true;
    }
  });

  await client.connect();
  pc.changeConnectionState('failed');
  await new Promise((r) => setTimeout(r, 0));

  assert.ok(errorEvent);
});
