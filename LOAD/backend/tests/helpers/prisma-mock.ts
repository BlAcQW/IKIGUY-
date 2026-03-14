import { vi } from 'vitest';

function createModelMock() {
  return {
    findUnique: vi.fn(),
    findFirst: vi.fn(),
    findMany: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateMany: vi.fn(),
    delete: vi.fn(),
    deleteMany: vi.fn(),
    count: vi.fn(),
    aggregate: vi.fn(),
    groupBy: vi.fn(),
  };
}

export function createPrismaMock() {
  return {
    user: createModelMock(),
    organization: createModelMock(),
    apiKey: createModelMock(),
    refreshToken: createModelMock(),
    assistant: createModelMock(),
    call: createModelMock(),
    phoneNumber: createModelMock(),
    tool: createModelMock(),
    squad: createModelMock(),
    campaign: createModelMock(),
    webhook: createModelMock(),
    webhookDelivery: createModelMock(),
    $connect: vi.fn(),
    $disconnect: vi.fn(),
    $queryRaw: vi.fn(),
    $transaction: vi.fn().mockImplementation((args: unknown) =>
      Array.isArray(args) ? Promise.all(args) : (args as (tx: unknown) => Promise<unknown>)(this),
    ),
  };
}

export type PrismaMock = ReturnType<typeof createPrismaMock>;
