import { z } from 'zod';

export const callAnalyticsQuerySchema = z.object({
  from: z.string().datetime().optional(),
  to: z.string().datetime().optional(),
  groupBy: z.enum(['hour', 'day', 'week']).default('day'),
  assistantId: z.string().uuid().optional(),
  type: z.enum(['WEB', 'INBOUND', 'OUTBOUND']).optional(),
});

export const summaryQuerySchema = z.object({
  from: z.string().datetime().optional(),
  to: z.string().datetime().optional(),
  assistantId: z.string().uuid().optional(),
  type: z.enum(['WEB', 'INBOUND', 'OUTBOUND']).optional(),
});

export type CallAnalyticsQuery = z.infer<typeof callAnalyticsQuerySchema>;
export type SummaryQuery = z.infer<typeof summaryQuerySchema>;
