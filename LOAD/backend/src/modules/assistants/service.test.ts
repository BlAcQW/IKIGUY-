import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../../tests/helpers/prisma-mock.js';
import { buildAssistant, buildTool } from '../../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

vi.mock('../../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import {
  createAssistant,
  listAssistants,
  getAssistant,
  updateAssistant,
  deleteAssistant,
  attachTool,
  detachTool,
  getAssistantTools,
} from './service.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
});

describe('createAssistant', () => {
  it('creates an assistant with all fields', async () => {
    const input = {
      name: 'Sales Bot',
      model: { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
      voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      firstMessage: 'Hello!',
      endCallMessage: 'Goodbye!',
      endCallPhrases: ['bye'],
      metadata: { team: 'sales' },
    };
    const expected = buildAssistant({ name: 'Sales Bot', organizationId: 'org-1' });
    prismaMock.assistant.create.mockResolvedValue(expected);

    const result = await createAssistant(input, 'org-1');

    expect(result.name).toBe('Sales Bot');
    expect(prismaMock.assistant.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          organizationId: 'org-1',
          name: 'Sales Bot',
        }),
      })
    );
  });

  it('associates the assistant with the organization', async () => {
    const input = {
      name: 'Bot',
      model: { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
      voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
      transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
      endCallPhrases: [],
    };
    prismaMock.assistant.create.mockResolvedValue(buildAssistant({ organizationId: 'org-99' }));

    await createAssistant(input, 'org-99');

    expect(prismaMock.assistant.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ organizationId: 'org-99' }),
      })
    );
  });
});

describe('listAssistants', () => {
  it('returns paginated data and meta', async () => {
    const assistants = [buildAssistant(), buildAssistant()];
    prismaMock.assistant.findMany.mockResolvedValue(assistants);
    prismaMock.assistant.count.mockResolvedValue(5);

    const result = await listAssistants({ page: 1, limit: 2 }, 'org-1');

    expect(result.data).toHaveLength(2);
    expect(result.meta).toEqual({ total: 5, page: 1, limit: 2 });
  });

  it('scopes query to the organization', async () => {
    prismaMock.assistant.findMany.mockResolvedValue([]);
    prismaMock.assistant.count.mockResolvedValue(0);

    await listAssistants({ page: 1, limit: 20 }, 'org-1');

    expect(prismaMock.assistant.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { organizationId: 'org-1' },
      })
    );
  });

  it('respects page and limit for pagination', async () => {
    prismaMock.assistant.findMany.mockResolvedValue([]);
    prismaMock.assistant.count.mockResolvedValue(0);

    await listAssistants({ page: 3, limit: 10 }, 'org-1');

    expect(prismaMock.assistant.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        skip: 20,
        take: 10,
      })
    );
  });

  it('orders by createdAt descending', async () => {
    prismaMock.assistant.findMany.mockResolvedValue([]);
    prismaMock.assistant.count.mockResolvedValue(0);

    await listAssistants({ page: 1, limit: 20 }, 'org-1');

    expect(prismaMock.assistant.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        orderBy: { createdAt: 'desc' },
      })
    );
  });
});

describe('getAssistant', () => {
  it('returns the assistant when found', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);

    const result = await getAssistant('ast-1', 'org-1');

    expect(result.id).toBe('ast-1');
  });

  it('throws 404 when assistant is not found', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(getAssistant('bad-id', 'org-1')).rejects.toThrow('Assistant not found');
    await expect(getAssistant('bad-id', 'org-1')).rejects.toMatchObject({ statusCode: 404 });
  });

  it('scopes lookup to organization', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(getAssistant('ast-1', 'org-1')).rejects.toThrow();

    expect(prismaMock.assistant.findFirst).toHaveBeenCalledWith({
      where: { id: 'ast-1', organizationId: 'org-1' },
    });
  });
});

describe('updateAssistant', () => {
  it('updates specified fields', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue({ ...assistant, name: 'Updated' });

    const result = await updateAssistant('ast-1', { name: 'Updated' }, 'org-1');

    expect(result.name).toBe('Updated');
    expect(prismaMock.assistant.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'ast-1' },
        data: expect.objectContaining({ name: 'Updated' }),
      })
    );
  });

  it('verifies ownership before updating', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(updateAssistant('ast-1', { name: 'Updated' }, 'org-1')).rejects.toThrow(
      'Assistant not found'
    );
    expect(prismaMock.assistant.update).not.toHaveBeenCalled();
  });

  it('throws 404 when assistant does not exist', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(updateAssistant('bad-id', { name: 'X' }, 'org-1')).rejects.toMatchObject({
      statusCode: 404,
    });
  });
});

describe('deleteAssistant', () => {
  it('deletes the assistant', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.delete.mockResolvedValue(assistant);

    await deleteAssistant('ast-1', 'org-1');

    expect(prismaMock.assistant.delete).toHaveBeenCalledWith({ where: { id: 'ast-1' } });
  });

  it('verifies ownership before deleting', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(deleteAssistant('ast-1', 'org-1')).rejects.toThrow('Assistant not found');
    expect(prismaMock.assistant.delete).not.toHaveBeenCalled();
  });

  it('throws 404 when assistant does not exist', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(deleteAssistant('bad-id', 'org-1')).rejects.toMatchObject({
      statusCode: 404,
    });
  });
});

describe('attachTool', () => {
  it('adds toolId to model.toolIds', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4', toolIds: [] },
    });
    const tool = buildTool({ id: 'tool-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.tool.findFirst.mockResolvedValue(tool);
    prismaMock.assistant.update.mockResolvedValue({
      ...assistant,
      model: { ...assistant.model as object, toolIds: ['tool-1'] },
    });

    const result = await attachTool('ast-1', 'tool-1', 'org-1');

    expect(prismaMock.assistant.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'ast-1' },
        data: expect.objectContaining({
          model: expect.objectContaining({ toolIds: ['tool-1'] }),
        }),
      }),
    );
  });

  it('does not duplicate existing toolId', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4', toolIds: ['tool-1'] },
    });
    const tool = buildTool({ id: 'tool-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.tool.findFirst.mockResolvedValue(tool);

    await attachTool('ast-1', 'tool-1', 'org-1');

    expect(prismaMock.assistant.update).not.toHaveBeenCalled();
  });

  it('throws 404 when tool not found', async () => {
    const assistant = buildAssistant({ id: 'ast-1', organizationId: 'org-1' });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.tool.findFirst.mockResolvedValue(null);

    await expect(attachTool('ast-1', 'bad-tool', 'org-1')).rejects.toThrow('Tool not found');
  });

  it('throws 404 when assistant not found', async () => {
    prismaMock.assistant.findFirst.mockResolvedValue(null);

    await expect(attachTool('bad-ast', 'tool-1', 'org-1')).rejects.toThrow('Assistant not found');
  });
});

describe('detachTool', () => {
  it('removes toolId from model.toolIds', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4', toolIds: ['tool-1', 'tool-2'] },
    });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue({
      ...assistant,
      model: { ...assistant.model as object, toolIds: ['tool-2'] },
    });

    await detachTool('ast-1', 'tool-1', 'org-1');

    expect(prismaMock.assistant.update).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          model: expect.objectContaining({ toolIds: ['tool-2'] }),
        }),
      }),
    );
  });

  it('handles detaching a non-existent toolId gracefully', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4', toolIds: ['tool-2'] },
    });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.assistant.update.mockResolvedValue(assistant);

    await detachTool('ast-1', 'tool-999', 'org-1');

    expect(prismaMock.assistant.update).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          model: expect.objectContaining({ toolIds: ['tool-2'] }),
        }),
      }),
    );
  });
});

describe('getAssistantTools', () => {
  it('returns tools for the assistant', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4', toolIds: ['tool-1', 'tool-2'] },
    });
    const tools = [buildTool({ id: 'tool-1' }), buildTool({ id: 'tool-2' })];
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);
    prismaMock.tool.findMany.mockResolvedValue(tools);

    const result = await getAssistantTools('ast-1', 'org-1');

    expect(result).toHaveLength(2);
    expect(prismaMock.tool.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: { in: ['tool-1', 'tool-2'] }, organizationId: 'org-1' },
      }),
    );
  });

  it('returns empty array when no toolIds', async () => {
    const assistant = buildAssistant({
      id: 'ast-1',
      organizationId: 'org-1',
      model: { provider: 'openai', model: 'gpt-4' },
    });
    prismaMock.assistant.findFirst.mockResolvedValue(assistant);

    const result = await getAssistantTools('ast-1', 'org-1');

    expect(result).toEqual([]);
    expect(prismaMock.tool.findMany).not.toHaveBeenCalled();
  });
});
