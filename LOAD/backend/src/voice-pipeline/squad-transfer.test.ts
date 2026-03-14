import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../tests/helpers/prisma-mock.js';

let prismaMock: PrismaMock;

vi.mock('../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { resolveTransfer } from './squad-transfer.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('resolveTransfer', () => {
  it('should return true when both assistants are in the same squad', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue({
      id: 'target-assistant',
      organizationId: 'org-1',
    });
    prismaMock.squad.findMany.mockResolvedValue([
      {
        id: 'squad-1',
        organizationId: 'org-1',
        members: [
          { assistantId: 'current-assistant' },
          { assistantId: 'target-assistant' },
        ],
      },
    ]);

    const result = await resolveTransfer('org-1', 'current-assistant', 'target-assistant');
    expect(result).toBe(true);
  });

  it('should return false when assistants are in different squads', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue({
      id: 'target-assistant',
      organizationId: 'org-1',
    });
    prismaMock.squad.findMany.mockResolvedValue([
      {
        id: 'squad-1',
        organizationId: 'org-1',
        members: [{ assistantId: 'current-assistant' }],
      },
      {
        id: 'squad-2',
        organizationId: 'org-1',
        members: [{ assistantId: 'target-assistant' }],
      },
    ]);

    const result = await resolveTransfer('org-1', 'current-assistant', 'target-assistant');
    expect(result).toBe(false);
  });

  it('should return false when target assistant does not exist', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    const result = await resolveTransfer('org-1', 'current-assistant', 'non-existent');
    expect(result).toBe(false);
  });

  it('should return false when transferring to same assistant', async () => {
    const result = await resolveTransfer('org-1', 'same-id', 'same-id');
    expect(result).toBe(false);
  });

  it('should return false when no squads exist', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue({
      id: 'target-assistant',
      organizationId: 'org-1',
    });
    prismaMock.squad.findMany.mockResolvedValue([]);

    const result = await resolveTransfer('org-1', 'current-assistant', 'target-assistant');
    expect(result).toBe(false);
  });
});
