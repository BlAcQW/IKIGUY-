import { describe, it, expect } from 'vitest';
import {
  mulawToPcm,
  pcmToMulaw,
  decodeTwilioAudio,
  encodeTwilioAudio,
} from './mulaw-codec.js';

describe('mulaw-codec', () => {
  describe('mulawToPcm', () => {
    it('decodes mu-law bytes to PCM 16-bit LE', () => {
      // mu-law 0xFF (complement of 0x00) decodes to 0 (silence)
      const mulaw = Buffer.from([0xFF]);
      const pcm = mulawToPcm(mulaw);
      expect(pcm.length).toBe(2);
      // The decoded value for 0xFF should be 0 (silence)
      const sample = pcm.readInt16LE(0);
      expect(sample).toBe(0);
    });

    it('produces 2 bytes per input byte', () => {
      const mulaw = Buffer.from([0x00, 0x80, 0x40, 0xC0, 0xFF]);
      const pcm = mulawToPcm(mulaw);
      expect(pcm.length).toBe(mulaw.length * 2);
    });

    it('handles empty buffer', () => {
      const pcm = mulawToPcm(Buffer.alloc(0));
      expect(pcm.length).toBe(0);
    });

    it('decodes known mu-law values to expected sign', () => {
      // 0x00 should decode to a large negative value
      const negative = mulawToPcm(Buffer.from([0x00]));
      expect(negative.readInt16LE(0)).toBeLessThan(0);

      // 0x80 should decode to a large positive value
      const positive = mulawToPcm(Buffer.from([0x80]));
      expect(positive.readInt16LE(0)).toBeGreaterThan(0);
    });
  });

  describe('pcmToMulaw', () => {
    it('encodes PCM 16-bit LE to mu-law bytes', () => {
      // Silence (0) should encode to 0xFF
      const pcm = Buffer.alloc(2);
      pcm.writeInt16LE(0, 0);
      const mulaw = pcmToMulaw(pcm);
      expect(mulaw.length).toBe(1);
      expect(mulaw[0]).toBe(0xFF);
    });

    it('produces 1 byte per 2 input bytes', () => {
      const pcm = Buffer.alloc(10); // 5 samples
      const mulaw = pcmToMulaw(pcm);
      expect(mulaw.length).toBe(5);
    });

    it('handles empty buffer', () => {
      const mulaw = pcmToMulaw(Buffer.alloc(0));
      expect(mulaw.length).toBe(0);
    });
  });

  describe('round-trip encode/decode', () => {
    it('preserves signal shape through round-trip', () => {
      // Create a simple waveform
      const sampleCount = 100;
      const pcmOriginal = Buffer.alloc(sampleCount * 2);
      for (let i = 0; i < sampleCount; i++) {
        const value = Math.round(Math.sin(i * 0.1) * 16000);
        pcmOriginal.writeInt16LE(value, i * 2);
      }

      // Encode to mu-law and back
      const encoded = pcmToMulaw(pcmOriginal);
      const decoded = mulawToPcm(encoded);

      expect(decoded.length).toBe(pcmOriginal.length);

      // Mu-law is lossy, but signal should approximate the original
      for (let i = 0; i < sampleCount; i++) {
        const original = pcmOriginal.readInt16LE(i * 2);
        const roundTripped = decoded.readInt16LE(i * 2);
        // Mu-law quantization error should be reasonable (within ~2% of full scale)
        expect(Math.abs(original - roundTripped)).toBeLessThan(2000);
      }
    });

    it('preserves silence through round-trip', () => {
      const silence = Buffer.alloc(20); // 10 samples of silence
      const encoded = pcmToMulaw(silence);
      const decoded = mulawToPcm(encoded);

      for (let i = 0; i < 10; i++) {
        expect(Math.abs(decoded.readInt16LE(i * 2))).toBeLessThan(100);
      }
    });
  });

  describe('decodeTwilioAudio', () => {
    it('converts mu-law 8kHz to PCM 16kHz (4x output length)', () => {
      // 100 mu-law bytes at 8kHz -> 100 PCM samples at 8kHz -> 200 PCM samples at 16kHz -> 400 bytes
      const mulaw = Buffer.alloc(100);
      mulaw.fill(0xFF); // silence
      const pcm = decodeTwilioAudio(mulaw);
      // 100 bytes mulaw -> 200 bytes PCM 8kHz -> upsample 2x -> 400 bytes PCM 16kHz
      expect(pcm.length).toBe(100 * 2 * 2);
    });

    it('handles empty buffer', () => {
      const pcm = decodeTwilioAudio(Buffer.alloc(0));
      expect(pcm.length).toBe(0);
    });
  });

  describe('encodeTwilioAudio', () => {
    it('converts PCM 24kHz to mu-law 8kHz (correct output length)', () => {
      // 600 bytes PCM 24kHz = 300 samples -> downsample 3x -> 100 samples at 8kHz -> 100 bytes mu-law
      const pcm24k = Buffer.alloc(600);
      const mulaw = encodeTwilioAudio(pcm24k);
      expect(mulaw.length).toBe(100);
    });

    it('handles empty buffer', () => {
      const mulaw = encodeTwilioAudio(Buffer.alloc(0));
      expect(mulaw.length).toBe(0);
    });
  });
});
