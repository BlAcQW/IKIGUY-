import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AudioBridge, wrapPcmAsWav, WEBRTC_SAMPLE_RATE, STT_SAMPLE_RATE, TTS_SAMPLE_RATE, OPUS_FRAME_SAMPLES } from './audio-bridge.js';

// Mock @discordjs/opus
vi.mock('@discordjs/opus', () => {
  class MockOpusEncoder {
    constructor(_rate: number, _channels: number) {}
    decode(input: Buffer): Buffer {
      // Return a buffer simulating 960 samples of PCM (20ms @ 48kHz mono)
      return Buffer.alloc(OPUS_FRAME_SAMPLES * 2);
    }
    encode(input: Buffer): Buffer {
      // Return a smaller buffer simulating compressed opus
      return Buffer.alloc(80);
    }
  }
  return { default: { OpusEncoder: MockOpusEncoder }, OpusEncoder: MockOpusEncoder };
});

// Mock audio-resample
vi.mock('../telephony/audio-resample.js', () => ({
  downsample: vi.fn((input: Buffer, _from: number, _to: number) => {
    // Simulate downsample by returning a smaller buffer
    const ratio = 48000 / 16000;
    return Buffer.alloc(Math.floor(input.length / ratio));
  }),
  upsample: vi.fn((input: Buffer, _from: number, _to: number) => {
    // Simulate upsample by returning a larger buffer
    const ratio = 48000 / 24000;
    return Buffer.alloc(Math.floor(input.length * ratio));
  }),
}));

describe('AudioBridge', () => {
  let bridge: AudioBridge;

  beforeEach(() => {
    bridge = new AudioBridge();
  });

  describe('decodeOpusToPcm', () => {
    it('should decode opus payload to PCM buffer', () => {
      const opusPayload = Buffer.alloc(80);
      const pcm = bridge.decodeOpusToPcm(opusPayload);
      expect(pcm).toBeInstanceOf(Buffer);
      expect(pcm.length).toBe(OPUS_FRAME_SAMPLES * 2); // 960 samples * 2 bytes
    });
  });

  describe('encodePcmToOpus', () => {
    it('should encode PCM frame to opus buffer', () => {
      const pcmFrame = Buffer.alloc(OPUS_FRAME_SAMPLES * 2);
      const opus = bridge.encodePcmToOpus(pcmFrame);
      expect(opus).toBeInstanceOf(Buffer);
      expect(opus.length).toBe(80); // Mock returns 80 bytes
    });
  });

  describe('downsampleForStt', () => {
    it('should downsample 48kHz to 16kHz', () => {
      const pcm48k = Buffer.alloc(9600); // 100ms at 48kHz mono (4800 samples * 2)
      const pcm16k = bridge.downsampleForStt(pcm48k);
      expect(pcm16k).toBeInstanceOf(Buffer);
      // Should be roughly 1/3 the size
      expect(pcm16k.length).toBeLessThan(pcm48k.length);
    });
  });

  describe('upsampleFromTts', () => {
    it('should upsample 24kHz to 48kHz', () => {
      const pcm24k = Buffer.alloc(4800); // 100ms at 24kHz mono (2400 samples * 2)
      const pcm48k = bridge.upsampleFromTts(pcm24k);
      expect(pcm48k).toBeInstanceOf(Buffer);
      // Should be roughly 2x the size
      expect(pcm48k.length).toBeGreaterThan(pcm24k.length);
    });
  });

  describe('encodeForRtp', () => {
    it('should split PCM into 20ms frames and encode each', () => {
      // 100ms of 48kHz mono = 4800 samples = 9600 bytes = 5 frames of 960 samples
      const pcm48k = Buffer.alloc(OPUS_FRAME_SAMPLES * 2 * 5);
      const frames = bridge.encodeForRtp(pcm48k);
      expect(frames).toHaveLength(5);
      frames.forEach((frame) => {
        expect(frame).toBeInstanceOf(Buffer);
        expect(frame.length).toBe(80); // Mock opus output
      });
    });

    it('should handle partial frames (discard trailing)', () => {
      // 2.5 frames worth — should produce 2 frames
      const pcm48k = Buffer.alloc(OPUS_FRAME_SAMPLES * 2 * 2 + 100);
      const frames = bridge.encodeForRtp(pcm48k);
      expect(frames).toHaveLength(2);
    });

    it('should return empty array for empty input', () => {
      const frames = bridge.encodeForRtp(Buffer.alloc(0));
      expect(frames).toHaveLength(0);
    });
  });
});

describe('wrapPcmAsWav', () => {
  it('should create a valid WAV file with correct header', () => {
    const pcm = Buffer.alloc(1000);
    const wav = wrapPcmAsWav(pcm, 16000);

    // WAV header is 44 bytes
    expect(wav.length).toBe(44 + 1000);

    // Check RIFF header
    expect(wav.toString('ascii', 0, 4)).toBe('RIFF');
    expect(wav.readUInt32LE(4)).toBe(wav.length - 8);
    expect(wav.toString('ascii', 8, 12)).toBe('WAVE');

    // Check fmt sub-chunk
    expect(wav.toString('ascii', 12, 16)).toBe('fmt ');
    expect(wav.readUInt32LE(16)).toBe(16); // Sub-chunk size
    expect(wav.readUInt16LE(20)).toBe(1);  // PCM format
    expect(wav.readUInt16LE(22)).toBe(1);  // Mono
    expect(wav.readUInt32LE(24)).toBe(16000); // Sample rate
    expect(wav.readUInt32LE(28)).toBe(32000); // Byte rate
    expect(wav.readUInt16LE(32)).toBe(2);  // Block align
    expect(wav.readUInt16LE(34)).toBe(16); // Bits per sample

    // Check data sub-chunk
    expect(wav.toString('ascii', 36, 40)).toBe('data');
    expect(wav.readUInt32LE(40)).toBe(1000);
  });

  it('should handle different sample rates', () => {
    const pcm = Buffer.alloc(500);
    const wav = wrapPcmAsWav(pcm, 48000);
    expect(wav.readUInt32LE(24)).toBe(48000);
    expect(wav.readUInt32LE(28)).toBe(96000);
  });

  it('should handle empty PCM input', () => {
    const wav = wrapPcmAsWav(Buffer.alloc(0), 16000);
    expect(wav.length).toBe(44);
    expect(wav.readUInt32LE(40)).toBe(0);
  });
});
