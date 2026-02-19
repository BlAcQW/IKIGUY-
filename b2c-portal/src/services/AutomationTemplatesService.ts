/**
 * Automation Templates API Service
 * Provides methods to interact with the automation templates API
 */

const API_BASE_URL = 'https://api.ailabsafrica.com';

export interface AutomationTemplate {
  id: string;
  name: string;
  description: string;
  industry: string;
  category?: string;
  complexity: string;
  estimatedTime: string;
  rating: number;
  usageCount: number;
  popular: boolean;
  integrationCategories: string[];
  defaultIntegrations: string[];
  workflow: WorkflowStep[];
  vapiConfig: VAPIConfig | null;
  features: string[];
  supportedLanguages: string[];
  knowledgeBase: KnowledgeBaseEntry[];
  tags: string[];
  isActive: boolean;
  isPublic: boolean;
  createdBy: string | null;
  createdAt: string;
  updatedAt: string;
  version: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  description: string;
}

export interface VAPIConfig {
  voiceAgentEnabled: boolean;
  agentPersonality: {
    role: string;
    tone: string;
    background: string;
    expertise: string[];
  };
  voiceSettings: {
    voiceId: string;
    speed: number;
    pitch: number;
    volume: number;
  };
  systemPrompt: string;
  callScenarios: {
    scenarios: string[];
    averageCallDuration: string;
  };
  customFunctions: any[];
  webhookUrl: string | null;
}

export interface KnowledgeBaseEntry {
  title: string;
  content: string;
  extractedContent: string;
}

export interface AutomationTemplatesListResponse {
  templates: AutomationTemplate[];
  total: number;
}

export interface AutomationTemplatesFilters {
  industry?: string;
  complexity?: string;
  popular?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}

class AutomationTemplatesService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/automation-templates`;
  }

  /**
   * Get all automation templates with optional filtering
   */
  async listTemplates(filters: AutomationTemplatesFilters = {}): Promise<AutomationTemplatesListResponse> {
    try {
      const params = new URLSearchParams();

      if (filters.industry) params.append('industry', filters.industry);
      if (filters.complexity) params.append('complexity', filters.complexity);
      if (filters.popular !== undefined) params.append('popular', filters.popular.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.per_page) params.append('per_page', filters.per_page.toString());

      const url = `${this.baseUrl}/public/list${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching automation templates:', error);
      throw error;
    }
  }

  /**
   * Get a specific automation template by ID
   */
  async getTemplate(templateId: string): Promise<AutomationTemplate> {
    try {
      const response = await fetch(`${this.baseUrl}/public/list`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const template = data.templates.find((t: AutomationTemplate) => t.id === templateId);

      if (!template) {
        throw new Error(`Template with ID ${templateId} not found`);
      }

      return template;
    } catch (error) {
      console.error('Error fetching automation template:', error);
      throw error;
    }
  }

  /**
   * Get templates filtered by industry
   */
  async getTemplatesByIndustry(industry: string): Promise<AutomationTemplate[]> {
    const response = await this.listTemplates({ industry });
    return response.templates;
  }


  /**
   * Get popular templates
   */
  async getPopularTemplates(): Promise<AutomationTemplate[]> {
    const response = await this.listTemplates({ popular: true });
    return response.templates;
  }

  /**
   * Search templates by name or description
   */
  async searchTemplates(query: string): Promise<AutomationTemplate[]> {
    const response = await this.listTemplates({ search: query });
    return response.templates;
  }


  /**
   * Get template industries
   */
  async getIndustries(): Promise<string[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/automation-templates/public/industries`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.industries.map((industry: { name: string }) => industry.name);
    } catch (error) {
      console.error('Error fetching industries:', error);
      throw error;
    }
  }

  /**
   * Get industries with template counts
   */
  async getIndustriesWithCounts(): Promise<Array<{ name: string; count: number }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/automation-templates/public/industries`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.industries;
    } catch (error) {
      console.error('Error fetching industries with counts:', error);
      throw error;
    }
  }


  /**
   * Get template statistics
   */
  async getTemplateStats(): Promise<{
    total: number;
    byIndustry: Record<string, number>;
    byComplexity: Record<string, number>;
  }> {
    try {
      const response = await this.listTemplates();
      const templates = response.templates;

      const stats = {
        total: templates.length,
        byIndustry: {} as Record<string, number>,
        byComplexity: {} as Record<string, number>,
      };

      templates.forEach(template => {
        // Count by industry
        stats.byIndustry[template.industry] = (stats.byIndustry[template.industry] || 0) + 1;

        // Count by complexity
        stats.byComplexity[template.complexity] = (stats.byComplexity[template.complexity] || 0) + 1;
      });

      return stats;
    } catch (error) {
      console.error('Error fetching template stats:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const automationTemplatesService = new AutomationTemplatesService();
export default AutomationTemplatesService;