import { z } from 'zod';

export const webrtcOfferSchema = z.object({
  assistantId: z.string().uuid(),
  sdpOffer: z.string().min(1).max(65536),
});

export const webrtcIceCandidateSchema = z.object({
  callId: z.string().uuid(),
  candidate: z.object({
    candidate: z.string(),
    sdpMid: z.string().nullable().optional(),
    sdpMLineIndex: z.number().nullable().optional(),
  }),
});

export const webrtcEndCallSchema = z.object({
  callId: z.string().uuid(),
});

export type WebrtcOfferInput = z.infer<typeof webrtcOfferSchema>;
export type WebrtcIceCandidateInput = z.infer<typeof webrtcIceCandidateSchema>;
