import { describe, it, expect } from 'vitest';
import {
  TOOL_TEMPLATES,
  TOOL_TEMPLATE_CATEGORIES,
  getTemplatesByCategory,
  getTemplateByFunctionName,
  getTemplatesByNames,
  type ToolTemplate,
} from './templates/index.js';

describe('TOOL_TEMPLATES', () => {
  it('contains templates', () => {
    expect(TOOL_TEMPLATES.length).toBeGreaterThan(0);
  });

  it('every template has required fields', () => {
    for (const template of TOOL_TEMPLATES) {
      expect(template.name).toBeTruthy();
      expect(template.description).toBeTruthy();
      expect(template.category).toBeTruthy();
      expect(['FUNCTION', 'TRANSFER_CALL', 'END_CALL']).toContain(template.type);
      expect(template.function).toBeDefined();
      expect(template.function.name).toBeTruthy();
      expect(template.function.description).toBeTruthy();
      expect(template.function.parameters).toBeDefined();
    }
  });

  it('every template has a valid category', () => {
    const validCategories = Object.keys(TOOL_TEMPLATE_CATEGORIES);
    for (const template of TOOL_TEMPLATES) {
      expect(validCategories).toContain(template.category);
    }
  });

  it('every template function has valid JSON Schema parameters', () => {
    for (const template of TOOL_TEMPLATES) {
      const params = template.function.parameters as Record<string, unknown>;
      expect(params.type).toBe('object');
      expect(params.properties).toBeDefined();
      expect(typeof params.properties).toBe('object');
    }
  });

  it('all function names are unique', () => {
    const names = TOOL_TEMPLATES.map((t) => t.function.name);
    const uniqueNames = new Set(names);
    expect(uniqueNames.size).toBe(names.length);
  });

  it('contains scheduling category templates', () => {
    const scheduling = TOOL_TEMPLATES.filter((t) => t.category === 'scheduling');
    expect(scheduling.length).toBeGreaterThan(0);
    expect(scheduling.some((t) => t.function.name === 'check_availability')).toBe(true);
    expect(scheduling.some((t) => t.function.name === 'book_appointment')).toBe(true);
  });

  it('contains sales category templates', () => {
    const sales = TOOL_TEMPLATES.filter((t) => t.category === 'sales');
    expect(sales.length).toBeGreaterThan(0);
    expect(sales.some((t) => t.function.name === 'score_lead_behavior')).toBe(true);
  });

  it('contains finance category templates', () => {
    const finance = TOOL_TEMPLATES.filter((t) => t.category === 'finance');
    expect(finance.length).toBeGreaterThan(0);
    expect(finance.some((t) => t.function.name === 'process_payment')).toBe(true);
  });

  it('contains retention category templates', () => {
    const retention = TOOL_TEMPLATES.filter((t) => t.category === 'retention');
    expect(retention.length).toBeGreaterThan(0);
  });

  it('contains survey category templates', () => {
    const survey = TOOL_TEMPLATES.filter((t) => t.category === 'survey');
    expect(survey.length).toBeGreaterThan(0);
  });

  it('contains marketing category templates', () => {
    const marketing = TOOL_TEMPLATES.filter((t) => t.category === 'marketing');
    expect(marketing.length).toBeGreaterThan(0);
  });

  it('contains insurance category templates', () => {
    const insurance = TOOL_TEMPLATES.filter((t) => t.category === 'insurance');
    expect(insurance.length).toBeGreaterThan(0);
  });

  it('contains healthcare category templates', () => {
    const healthcare = TOOL_TEMPLATES.filter((t) => t.category === 'healthcare');
    expect(healthcare.length).toBeGreaterThan(0);
  });
});

describe('TOOL_TEMPLATE_CATEGORIES', () => {
  it('has display names for all used categories', () => {
    const usedCategories = new Set(TOOL_TEMPLATES.map((t) => t.category));
    for (const category of usedCategories) {
      expect(TOOL_TEMPLATE_CATEGORIES[category]).toBeTruthy();
    }
  });
});

describe('getTemplatesByCategory', () => {
  it('groups templates by category', () => {
    const grouped = getTemplatesByCategory();
    expect(grouped.scheduling.length).toBeGreaterThan(0);
    expect(grouped.sales.length).toBeGreaterThan(0);
    expect(grouped.finance.length).toBeGreaterThan(0);
  });

  it('every template in a group has the correct category', () => {
    const grouped = getTemplatesByCategory();
    for (const [category, templates] of Object.entries(grouped)) {
      for (const template of templates) {
        expect(template.category).toBe(category);
      }
    }
  });
});

describe('getTemplateByFunctionName', () => {
  it('returns the correct template', () => {
    const template = getTemplateByFunctionName('check_availability');
    expect(template).toBeDefined();
    expect(template!.function.name).toBe('check_availability');
    expect(template!.category).toBe('scheduling');
  });

  it('returns undefined for unknown name', () => {
    expect(getTemplateByFunctionName('nonexistent_function')).toBeUndefined();
  });
});

describe('getTemplatesByNames', () => {
  it('returns matching templates', () => {
    const templates = getTemplatesByNames(['check_availability', 'process_payment']);
    expect(templates).toHaveLength(2);
    expect(templates.map((t) => t.function.name).sort()).toEqual(
      ['check_availability', 'process_payment'].sort()
    );
  });

  it('returns empty array for no matches', () => {
    expect(getTemplatesByNames(['nonexistent'])).toHaveLength(0);
  });
});
