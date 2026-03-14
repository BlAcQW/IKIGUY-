import { z } from 'zod';

const transferConditionSchema = z.object({
  type: z.enum(['keyword', 'intent', 'tool_result', 'manual']),
  value: z.string().min(1, 'Condition value is required'),
  description: z.string().optional(),
});

const squadMemberSchema = z.object({
  assistantId: z.string().uuid('Invalid assistant ID'),
  transferConditions: z.array(transferConditionSchema).optional().default([]),
});

export const createSquadSchema = z.object({
  name: z.string().min(1, 'Squad name is required').max(100),
  members: z.array(squadMemberSchema).min(1, 'At least one member is required'),
  metadata: z.record(z.unknown()).optional(),
});

export const updateSquadSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  members: z.array(squadMemberSchema).min(1).optional(),
  metadata: z.record(z.unknown()).optional(),
});

export const squadQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export type CreateSquadInput = z.infer<typeof createSquadSchema>;
export type UpdateSquadInput = z.infer<typeof updateSquadSchema>;
export type SquadQueryInput = z.infer<typeof squadQuerySchema>;
export type TransferCondition = z.infer<typeof transferConditionSchema>;
export type SquadMember = z.infer<typeof squadMemberSchema>;
