export interface ToolTemplate {
  name: string;
  description: string;
  category: ToolTemplateCategory;
  type: 'FUNCTION' | 'TRANSFER_CALL' | 'END_CALL';
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

export type ToolTemplateCategory =
  | 'scheduling'
  | 'sales'
  | 'finance'
  | 'retention'
  | 'survey'
  | 'marketing'
  | 'insurance'
  | 'healthcare';

export const TOOL_TEMPLATE_CATEGORIES: Record<ToolTemplateCategory, string> = {
  scheduling: 'Scheduling',
  sales: 'Sales & Lead Nurturing',
  finance: 'Finance & Payments',
  retention: 'Customer Retention',
  survey: 'Survey & Feedback',
  marketing: 'Marketing & Product Launch',
  insurance: 'Insurance',
  healthcare: 'Healthcare',
};
