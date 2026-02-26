import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildSquad, buildAssistant } from '../../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { createSquad, listSquads, getSquad, updateSquad, deleteSquad } from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('createSquad', () => {
  const orgId = 'org-1';

  it('creates a squad with valid members', async () => {
    const input = {
      name: 'Support Team',
      members: [
        { assistantId: 'ast-1', transferConditions: [] },
        { assistantId: 'ast-2', transferConditions: [] },
      ],
    };
    const expected = buildSquad({ name: 'Support Team', organizationId: orgId });
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-1' }, { id: 'ast-2' }]);
    prismaMock.squad.create.mockResolvedValue(expected);

    const result = await createSquad(input, orgId);

    expect(result.name).toBe('Support Team');
    expect(prismaMock.squad.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: orgId,
          name: 'Support Team',
          members: input.members,
        }),
      })
    );
  });

  it('associates the squad with the organization', async () => {
    const input = {
      name: 'Sales Squad',
      members: [{ assistantId: 'ast-1', transferConditions: [] }],
    };
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-1' }]);
    prismaMock.squad.create.mockResolvedValue(buildSquad({ organizationId: 'org-99' }));

    await createSquad(input, 'org-99');

    expect(prismaMock.squad.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ organizationId: 'org-99' }),
      })
    );
  });

  it('passes metadata to prisma when provided', async () => {
    const input = {
      name: 'Meta Squad',
      members: [{ assistantId: 'ast-1', transferConditions: [] }],
      metadata: { department: 'engineering' },
    };
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-1' }]);
    prismaMock.squad.create.mockResolvedValue(
      buildSquad({ name: 'Meta Squad', metadata: { department: 'engineering' } })
    );

    await createSquad(input, orgId);

    expect(prismaMock.squad.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          metadata: { department: 'engineering' },
        }),
      })
    );
  });

  it('throws 400 when duplicate assistant IDs are provided', async () => {
    const input = {
      name: 'Bad Squad',
      members: [
        { assistantId: 'ast-1', transferConditions: [] },
        { assistantId: 'ast-1', transferConditions: [] },
      ],
    };

    await expect(createSquad(input, orgId)).rejects.toThrow('Duplicate assistant IDs in members');
    await expect(createSquad(input, orgId)).rejects.toMatchObject({ statusCode: 400 });
    expect(prismaMock.assistant.findMany).not.toHaveBeenCalled();
    expect(prismaMock.squad.create).not.toHaveBeenCalled();
  });

  it('throws 400 when an assistant ID does not belong to the organization', async () => {
    const input = {
      name: 'Missing Member Squad',
      members: [
        { assistantId: 'ast-1', transferConditions: [] },
        { assistantId: 'ast-missing', transferConditions: [] },
      ],
    };
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-1' }]);

    await expect(createSquad(input, orgId)).rejects.toThrow('Assistants not found: ast-missing');
    await expect(createSquad(input, orgId)).rejects.toMatchObject({ statusCode: 400 });
    expect(prismaMock.squad.create).not.toHaveBeenCalled();
  });

  it('lists all missing assistant IDs in error message', async () => {
    const input = {
      name: 'Multi-missing Squad',
      members: [
        { assistantId: 'ast-bad-1', transferConditions: [] },
        { assistantId: 'ast-bad-2', transferConditions: [] },
      ],
    };
    prismaMock.assistant.findMany.mockResolvedValue([]);

    await expect(createSquad(input, orgId)).rejects.toThrow(
      'Assistants not found: ast-bad-1, ast-bad-2'
    );
  });

  it('validates assistant IDs scoped to the organization', async () => {
    const input = {
      name: 'Scoped Squad',
      members: [{ assistantId: 'ast-1', transferConditions: [] }],
    };
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-1' }]);
    prismaMock.squad.create.mockResolvedValue(buildSquad());

    await createSquad(input, orgId);

    expect(prismaMock.assistant.findMany).toHaveBeenCalledWith({
      where: { id: { in: ['ast-1'] }, organizationId: orgId },
      select: { id: true },
    });
  });
});

describe('listSquads', () => {
  const orgId = 'org-1';

  it('returns squads with pagination metadata', async () => {
    const squads = [buildSquad(), buildSquad()];
    prismaMock.squad.findMany.mockResolvedValue(squads);
    prismaMock.squad.count.mockResolvedValue(5);

    const result = await listSquads(orgId, 1, 2);

    expect(result.squads).toHaveLength(2);
    expect(result.total).toBe(5);
    expect(result.page).toBe(1);
    expect(result.limit).toBe(2);
  });

  it('scopes query to the organization', async () => {
    prismaMock.squad.findMany.mockResolvedValue([]);
    prismaMock.squad.count.mockResolvedValue(0);

    await listSquads(orgId, 1, 20);

    expect(prismaMock.squad.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { organizationId: orgId },
      })
    );
    expect(prismaMock.squad.count).toHaveBeenCalledWith({
      where: { organizationId: orgId },
    });
  });

  it('respects page and limit for pagination offset', async () => {
    prismaMock.squad.findMany.mockResolvedValue([]);
    prismaMock.squad.count.mockResolvedValue(0);

    await listSquads(orgId, 3, 10);

    expect(prismaMock.squad.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        skip: 20,
        take: 10,
      })
    );
  });

  it('orders by createdAt descending', async () => {
    prismaMock.squad.findMany.mockResolvedValue([]);
    prismaMock.squad.count.mockResolvedValue(0);

    await listSquads(orgId, 1, 20);

    expect(prismaMock.squad.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        orderBy: { createdAt: 'desc' },
      })
    );
  });

  it('returns empty list when no squads exist', async () => {
    prismaMock.squad.findMany.mockResolvedValue([]);
    prismaMock.squad.count.mockResolvedValue(0);

    const result = await listSquads(orgId, 1, 20);

    expect(result.squads).toEqual([]);
    expect(result.total).toBe(0);
  });
});

describe('getSquad', () => {
  const orgId = 'org-1';

  it('returns the squad when found', async () => {
    const squad = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(squad);

    const result = await getSquad('sqd-1', orgId);

    expect(result.id).toBe('sqd-1');
  });

  it('throws 404 when squad is not found', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(getSquad('bad-id', orgId)).rejects.toThrow('Squad not found');
    await expect(getSquad('bad-id', orgId)).rejects.toMatchObject({ statusCode: 404 });
  });

  it('scopes lookup to organization', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(getSquad('sqd-1', orgId)).rejects.toThrow();

    expect(prismaMock.squad.findFirst).toHaveBeenCalledWith({
      where: { id: 'sqd-1', organizationId: orgId },
    });
  });
});

describe('updateSquad', () => {
  const orgId = 'org-1';

  it('updates the squad name without validating members', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(existing);
    prismaMock.squad.update.mockResolvedValue({ ...existing, name: 'Renamed Squad' });

    const result = await updateSquad('sqd-1', { name: 'Renamed Squad' }, orgId);

    expect(result.name).toBe('Renamed Squad');
    expect(prismaMock.assistant.findMany).not.toHaveBeenCalled();
    expect(prismaMock.squad.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'sqd-1' },
        data: expect.objectContaining({ name: 'Renamed Squad' }),
      })
    );
  });

  it('validates assistant IDs when members are updated', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    const newMembers = [{ assistantId: 'ast-3', transferConditions: [] as never[] }];
    prismaMock.squad.findFirst.mockResolvedValue(existing);
    prismaMock.assistant.findMany.mockResolvedValue([{ id: 'ast-3' }]);
    prismaMock.squad.update.mockResolvedValue({ ...existing, members: newMembers });

    await updateSquad('sqd-1', { members: newMembers }, orgId);

    expect(prismaMock.assistant.findMany).toHaveBeenCalledWith({
      where: { id: { in: ['ast-3'] }, organizationId: orgId },
      select: { id: true },
    });
  });

  it('throws 404 when squad does not exist', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(updateSquad('bad-id', { name: 'X' }, orgId)).rejects.toThrow('Squad not found');
    await expect(updateSquad('bad-id', { name: 'X' }, orgId)).rejects.toMatchObject({
      statusCode: 404,
    });
    expect(prismaMock.squad.update).not.toHaveBeenCalled();
  });

  it('throws 400 when updated members contain duplicate assistant IDs', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(existing);

    const dupeMembers = [
      { assistantId: 'ast-1', transferConditions: [] as never[] },
      { assistantId: 'ast-1', transferConditions: [] as never[] },
    ];

    await expect(updateSquad('sqd-1', { members: dupeMembers }, orgId)).rejects.toThrow(
      'Duplicate assistant IDs in members'
    );
    await expect(updateSquad('sqd-1', { members: dupeMembers }, orgId)).rejects.toMatchObject({
      statusCode: 400,
    });
    expect(prismaMock.squad.update).not.toHaveBeenCalled();
  });

  it('throws 400 when updated members reference non-existent assistants', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(existing);
    prismaMock.assistant.findMany.mockResolvedValue([]);

    const members = [{ assistantId: 'ast-gone', transferConditions: [] as never[] }];

    await expect(updateSquad('sqd-1', { members }, orgId)).rejects.toThrow(
      'Assistants not found: ast-gone'
    );
    await expect(updateSquad('sqd-1', { members }, orgId)).rejects.toMatchObject({
      statusCode: 400,
    });
  });

  it('updates metadata when provided', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(existing);
    prismaMock.squad.update.mockResolvedValue({
      ...existing,
      metadata: { priority: 'high' },
    });

    await updateSquad('sqd-1', { metadata: { priority: 'high' } }, orgId);

    expect(prismaMock.squad.update).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ metadata: { priority: 'high' } }),
      })
    );
  });
});

describe('deleteSquad', () => {
  const orgId = 'org-1';

  it('deletes the squad when it exists', async () => {
    const existing = buildSquad({ id: 'sqd-1', organizationId: orgId });
    prismaMock.squad.findFirst.mockResolvedValue(existing);
    prismaMock.squad.delete.mockResolvedValue(existing);

    await deleteSquad('sqd-1', orgId);

    expect(prismaMock.squad.delete).toHaveBeenCalledWith({ where: { id: 'sqd-1' } });
  });

  it('verifies ownership before deleting', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(deleteSquad('sqd-1', orgId)).rejects.toThrow('Squad not found');
    expect(prismaMock.squad.delete).not.toHaveBeenCalled();
  });

  it('throws 404 when squad does not exist', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(deleteSquad('bad-id', orgId)).rejects.toMatchObject({ statusCode: 404 });
  });

  it('scopes ownership check to organization', async () => {
    prismaMock.squad.findFirst.mockResolvedValue(null);

    await expect(deleteSquad('sqd-1', orgId)).rejects.toThrow();

    expect(prismaMock.squad.findFirst).toHaveBeenCalledWith({
      where: { id: 'sqd-1', organizationId: orgId },
    });
  });
});
