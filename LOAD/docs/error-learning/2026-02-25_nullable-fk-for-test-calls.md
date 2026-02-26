# Error Learning Record

## Date
2026-02-25

## Error Category
[x] Architectural  [ ] Security-Relevant  [ ] Integration Contract Violation

## What Went Wrong
Added inline assistant config support to the WebSocket handler (`handleStart`) for editor testing. The code passed `undefined` as `assistantId` to `createCall()`, but the Prisma `Call` model had `assistantId String` (non-nullable) with a foreign key to `Assistant`. This caused Prisma to throw at runtime when attempting to create a call record without an assistantId.

Additionally, making `assistantId` nullable in the schema rippled type errors into `analytics/service.ts` (groupBy query results now include `string | null`) and `telephony/service.ts` (accessing `call.assistantId` became `string | null`).

## Root Cause
Wrong assumption: that all calls would always be associated with a persisted assistant. The inline test flow creates calls from ephemeral config objects that don't exist in the `Assistant` table, so there's no valid FK target.

## Corrected Implementation
1. Made `assistantId String?` (nullable) in the Prisma schema
2. Updated `CreateCallInput.assistantId` to `string | undefined`
3. Fixed downstream type errors in analytics (filter null IDs) and telephony (non-null assert for telephony-specific paths where assistantId is always present)

```typescript
// Call model
assistantId String?
assistant   Assistant? @relation(...)

// CreateCallInput
assistantId?: string;

// createCall
assistantId: input.assistantId ?? null,
```

## Reasoning Behind the Correction
Making the FK nullable is the correct approach because:
- Test calls are legitimate call records (they use real pipeline resources and should be tracked)
- A synthetic/placeholder assistantId would create orphan references
- Nullable FK cleanly represents "this call had no persisted assistant"

## Extracted Rule
When adding a new execution path that creates a database record, check every non-nullable FK on that model — if the new path doesn't have a valid FK target, the FK must be made nullable (and all downstream type references updated) before the feature ships.

## Recurrence Risk
[x] First occurrence
[ ] Has appeared before — ESCALATE TO ARCHITECTURAL REVIEW
