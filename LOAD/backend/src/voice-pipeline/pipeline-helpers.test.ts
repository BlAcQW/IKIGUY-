import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPrismaMock, type PrismaMock } from '../../tests/helpers/prisma-mock.js';
import { buildTool } from '../../tests/helpers/factories.js';

let prismaMock: PrismaMock;

vi.mock('../database/client.js', () => ({
  get prisma() {
    return prismaMock;
  },
}));

import { extractAssistantConfig, loadToolsForPipeline } from './pipeline-helpers.js';

beforeEach(() => {
  prismaMock = createPrismaMock();
  vi.clearAllMocks();
});

describe('extractAssistantConfig', () => {
  it('extracts model, voice, and transcriber configs', () => {
    const result = extractAssistantConfig({
      model: { model: 'gpt-4', temperature: 0.5, maxTokens: 500 },
      voice: { voiceId: 'alloy', speed: 1.2 },
      transcriber: { model: 'whisper-1', language: 'en' },
    });

    expect(result.modelConfig.model).toBe('gpt-4');
    expect(result.modelConfig.temperature).toBe(0.5);
    expect(result.voiceConfig.voiceId).toBe('alloy');
    expect(result.transcriberConfig.language).toBe('en');
  });

  it('handles null/undefined fields gracefully', () => {
    const result = extractAssistantConfig({
      model: null,
      voice: undefined,
      transcriber: null,
    });

    expect(result.modelConfig).toEqual({});
    expect(result.voiceConfig).toEqual({});
    expect(result.transcriberConfig).toEqual({});
  });
});

describe('loadToolsForPipeline', () => {
  it('returns undefined for empty toolIds', async () => {
    const result = await loadToolsForPipeline([], 'org-1');
    expect(result).toBeUndefined();
    expect(prismaMock.tool.findMany).not.toHaveBeenCalled();
  });

  it('returns undefined for undefined toolIds', async () => {
    const result = await loadToolsForPipeline(undefined, 'org-1');
    expect(result).toBeUndefined();
  });

  it('returns tools mapped to PipelineTool shape', async () => {
    const tool = buildTool({ id: 't-1', organizationId: 'org-1' });
    prismaMock.tool.findMany.mockResolvedValue([tool]);

    const result = await loadToolsForPipeline(['t-1'], 'org-1');

    expect(result).toHaveLength(1);
    expect(result![0].id).toBe('t-1');
    expect(result![0].name).toBe(tool.name);
  });

  it('returns undefined when no tools found in DB', async () => {
    prismaMock.tool.findMany.mockResolvedValue([]);

    const result = await loadToolsForPipeline(['nonexistent'], 'org-1');
    expect(result).toBeUndefined();
  });
});
