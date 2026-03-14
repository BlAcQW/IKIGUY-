import { z } from 'zod';

export const createWebCallSchema = z.object({
  assistantId: z.string().uuid('Invalid assistant ID'),
});

export const listCallsSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  status: z.string().optional(),
  assistantId: z.string().optional(),
});

export const createOutboundCallSchema = z.object({
  assistantId: z.string().uuid('Invalid assistant ID'),
  phoneNumberId: z.string().uuid('Invalid phone number ID'),
  customerNumber: z.string().regex(/^\+\d{10,15}$/, 'Customer number must be E.164 format'),
  metadata: z.record(z.unknown()).optional(),
});

export type CreateWebCallInput = z.infer<typeof createWebCallSchema>;
export type ListCallsInput = z.infer<typeof listCallsSchema>;
export type CreateOutboundCallInput = z.infer<typeof createOutboundCallSchema>;
