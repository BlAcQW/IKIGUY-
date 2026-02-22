import { z } from 'zod';

export const searchNumbersSchema = z.object({
  country: z.string().length(2).default('US'),
  areaCode: z.string().regex(/^\d{3}$/, 'Area code must be 3 digits').optional(),
  contains: z.string().max(20).optional(),
  type: z.enum(['local', 'tollFree']).default('local'),
  limit: z.coerce.number().min(1).max(30).default(10),
});

export const purchaseNumberSchema = z.object({
  phoneNumber: z.string().regex(/^\+\d{10,15}$/, 'Phone number must be E.164 format (e.g. +15551234567)'),
  name: z.string().max(100).optional(),
});

export const createSipNumberSchema = z.object({
  number: z.string().regex(/^\+\d{10,15}$/, 'Phone number must be E.164 format (e.g. +15551234567)'),
  name: z.string().max(100).optional(),
  provider: z.literal('SIP_TRUNK'),
  sipDomain: z.string().optional(),
});

export const updatePhoneNumberSchema = z.object({
  assistantId: z.string().uuid().nullable().optional(),
  name: z.string().max(100).optional(),
});

export type SearchNumbersInput = z.infer<typeof searchNumbersSchema>;
export type PurchaseNumberInput = z.infer<typeof purchaseNumberSchema>;
export type CreateSipNumberInput = z.infer<typeof createSipNumberSchema>;
export type UpdatePhoneNumberInput = z.infer<typeof updatePhoneNumberSchema>;
