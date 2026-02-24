export type { ToolTemplate, ToolTemplateCategory } from './types.js';
export { TOOL_TEMPLATE_CATEGORIES } from './types.js';

import type { ToolTemplate, ToolTemplateCategory } from './types.js';
import { schedulingTemplates } from './scheduling.js';
import { salesTemplates } from './sales.js';
import { financeTemplates } from './finance.js';
import { retentionTemplates } from './retention.js';
import { surveyTemplates } from './survey.js';
import { marketingTemplates } from './marketing.js';
import { insuranceTemplates } from './insurance.js';
import { healthcareTemplates } from './healthcare.js';
import { commonTemplates } from './common.js';

export const TOOL_TEMPLATES: readonly ToolTemplate[] = Object.freeze([
  ...schedulingTemplates,
  ...salesTemplates,
  ...financeTemplates,
  ...retentionTemplates,
  ...surveyTemplates,
  ...marketingTemplates,
  ...insuranceTemplates,
  ...healthcareTemplates,
  ...commonTemplates,
]);

export function getTemplatesByCategory(): Record<ToolTemplateCategory, ToolTemplate[]> {
  const grouped: Record<string, ToolTemplate[]> = {};
  for (const template of TOOL_TEMPLATES) {
    if (!grouped[template.category]) {
      grouped[template.category] = [];
    }
    grouped[template.category].push(template);
  }
  return grouped as Record<ToolTemplateCategory, ToolTemplate[]>;
}

export function getTemplateByFunctionName(functionName: string): ToolTemplate | undefined {
  return TOOL_TEMPLATES.find((t) => t.function.name === functionName);
}

export function getTemplatesByNames(names: string[]): ToolTemplate[] {
  return TOOL_TEMPLATES.filter((t) => names.includes(t.function.name));
}
