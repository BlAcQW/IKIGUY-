/**
 * Multi-LLM Fallback Service
 *
 * Implements a robust fallback system across multiple LLM providers:
 * Primary: Anthropic Claude → Secondary: OpenAI GPT-4 → Final: Google Gemini
 *
 * Features:
 * - Automatic failover on errors or timeouts
 * - Provider-specific prompt optimization
 * - Response quality validation
 * - Caching for repeated requests
 * - Usage analytics and cost tracking
 */

interface LLMRequest {
  prompt: string;
  context?: string;
  type: 'campaign-analysis' | 'workflow-generation' | 'optimization' | 'validation';
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
}

interface LLMResponse {
  content: string;
  provider: 'anthropic' | 'openai' | 'gemini';
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  latency: number;
  cost?: number;
  confidence?: number;
}

interface ProviderConfig {
  name: string;
  apiKey: string;
  endpoint: string;
  model: string;
  maxRetries: number;
  timeout: number;
  costPerToken: number;
}

export class LLMFallbackService {
  private static instance: LLMFallbackService;
  private cache: Map<string, LLMResponse> = new Map();
  private analytics: Array<{ provider: string; success: boolean; latency: number; timestamp: string }> = [];

  private readonly providers: Record<string, ProviderConfig> = {
    anthropic: {
      name: 'Anthropic Claude',
      apiKey: process.env.VITE_ANTHROPIC_API_KEY || '',
      endpoint: 'https://api.anthropic.com/v1/messages',
      model: 'claude-3-sonnet-20241022',
      maxRetries: 2,
      timeout: 30000,
      costPerToken: 0.000003 // $3 per 1M tokens
    },
    openai: {
      name: 'OpenAI GPT-4',
      apiKey: process.env.VITE_OPENAI_API_KEY || '',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      model: 'gpt-4',
      maxRetries: 2,
      timeout: 25000,
      costPerToken: 0.00003 // $30 per 1M tokens
    },
    gemini: {
      name: 'Google Gemini',
      apiKey: process.env.VITE_GEMINI_API_KEY || '',
      endpoint: 'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent',
      model: 'gemini-pro',
      maxRetries: 1,
      timeout: 20000,
      costPerToken: 0.000001 // $1 per 1M tokens
    }
  };

  private constructor() {}

  static getInstance(): LLMFallbackService {
    if (!LLMFallbackService.instance) {
      LLMFallbackService.instance = new LLMFallbackService();
    }
    return LLMFallbackService.instance;
  }

  /**
   * Main method to process LLM requests with automatic fallback
   */
  async processRequest(request: LLMRequest): Promise<LLMResponse> {
    const cacheKey = this.generateCacheKey(request);

    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      console.log(`Cache hit for ${request.type} request`);
      return cached;
    }

    const providers = ['anthropic', 'openai', 'gemini'] as const;

    for (const provider of providers) {
      try {
        console.log(`Attempting ${provider} for ${request.type} request`);
        const response = await this.callProvider(provider, request);

        // Validate response quality
        if (this.validateResponse(response, request)) {
          // Cache successful response
          this.cache.set(cacheKey, response);

          // Record analytics
          this.recordAnalytics(provider, true, response.latency);

          return response;
        } else {
          console.warn(`${provider} response failed quality validation`);
          throw new Error('Response quality validation failed');
        }

      } catch (error) {
        console.error(`${provider} failed:`, error);
        this.recordAnalytics(provider, false, 0);

        // If this is the last provider, throw the error
        if (provider === 'gemini') {
          throw new Error(`All LLM providers failed. Last error: ${error.message}`);
        }

        // Continue to next provider
        continue;
      }
    }

    throw new Error('All LLM providers exhausted without success');
  }

  /**
   * Call specific LLM provider
   */
  private async callProvider(provider: keyof typeof this.providers, request: LLMRequest): Promise<LLMResponse> {
    const config = this.providers[provider];
    const startTime = Date.now();

    if (!config.apiKey) {
      throw new Error(`API key not configured for ${provider}`);
    }

    let response: Response;
    let responseData: any;

    switch (provider) {
      case 'anthropic':
        response = await this.callAnthropic(config, request);
        responseData = await response.json();
        break;

      case 'openai':
        response = await this.callOpenAI(config, request);
        responseData = await response.json();
        break;

      case 'gemini':
        response = await this.callGemini(config, request);
        responseData = await response.json();
        break;

      default:
        throw new Error(`Unknown provider: ${provider}`);
    }

    if (!response.ok) {
      throw new Error(`${provider} API error: ${response.status} ${response.statusText}`);
    }

    const latency = Date.now() - startTime;

    return this.parseProviderResponse(provider, responseData, latency, config.costPerToken);
  }

  /**
   * Call Anthropic Claude API
   */
  private async callAnthropic(config: ProviderConfig, request: LLMRequest): Promise<Response> {
    const payload = {
      model: config.model,
      max_tokens: request.maxTokens || 4000,
      temperature: request.temperature || 0.7,
      system: request.systemPrompt || this.getSystemPrompt(request.type),
      messages: [
        {
          role: 'user',
          content: this.optimizePromptForProvider('anthropic', request)
        }
      ]
    };

    return fetch(config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': config.apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(config.timeout)
    });
  }

  /**
   * Call OpenAI GPT-4 API
   */
  private async callOpenAI(config: ProviderConfig, request: LLMRequest): Promise<Response> {
    const payload = {
      model: config.model,
      max_tokens: request.maxTokens || 4000,
      temperature: request.temperature || 0.7,
      messages: [
        {
          role: 'system',
          content: request.systemPrompt || this.getSystemPrompt(request.type)
        },
        {
          role: 'user',
          content: this.optimizePromptForProvider('openai', request)
        }
      ]
    };

    return fetch(config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(config.timeout)
    });
  }

  /**
   * Call Google Gemini API
   */
  private async callGemini(config: ProviderConfig, request: LLMRequest): Promise<Response> {
    const systemPrompt = request.systemPrompt || this.getSystemPrompt(request.type);
    const userPrompt = this.optimizePromptForProvider('gemini', request);

    const payload = {
      contents: [
        {
          parts: [
            { text: `${systemPrompt}\n\n${userPrompt}` }
          ]
        }
      ],
      generationConfig: {
        temperature: request.temperature || 0.7,
        maxOutputTokens: request.maxTokens || 4000,
        topP: 0.8,
        topK: 10
      }
    };

    return fetch(`${config.endpoint}?key=${config.apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(config.timeout)
    });
  }

  /**
   * Parse provider-specific response format
   */
  private parseProviderResponse(
    provider: keyof typeof this.providers,
    data: any,
    latency: number,
    costPerToken: number
  ): LLMResponse {
    let content: string;
    let usage: { promptTokens: number; completionTokens: number; totalTokens: number };

    switch (provider) {
      case 'anthropic':
        content = data.content[0]?.text || '';
        usage = {
          promptTokens: data.usage?.input_tokens || 0,
          completionTokens: data.usage?.output_tokens || 0,
          totalTokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
        };
        break;

      case 'openai':
        content = data.choices[0]?.message?.content || '';
        usage = {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0
        };
        break;

      case 'gemini':
        content = data.candidates[0]?.content?.parts[0]?.text || '';
        // Gemini doesn't provide token usage in response, estimate based on text length
        const estimatedTokens = Math.ceil(content.length / 4);
        usage = {
          promptTokens: estimatedTokens,
          completionTokens: estimatedTokens,
          totalTokens: estimatedTokens * 2
        };
        break;

      default:
        throw new Error(`Unknown provider for response parsing: ${provider}`);
    }

    const cost = usage.totalTokens * costPerToken;
    const confidence = this.calculateConfidence(provider, content, latency);

    return {
      content,
      provider,
      usage,
      latency,
      cost,
      confidence
    };
  }

  /**
   * Get system prompt based on request type
   */
  private getSystemPrompt(type: LLMRequest['type']): string {
    const prompts = {
      'campaign-analysis': `You are an expert voice campaign analyst. Analyze voice campaign configurations and provide optimization suggestions. Focus on:
        - Campaign effectiveness and success probability
        - Audience targeting optimization
        - Integration recommendations
        - Performance improvement suggestions

        Provide specific, actionable recommendations in a structured format.`,

      'workflow-generation': `You are an expert automation engineer specializing in n8n workflows. Generate robust, production-ready workflows for voice campaigns. Focus on:
        - Error handling and retries
        - Rate limiting and throttling
        - Data validation and transformation
        - Integration best practices

        Generate workflows that are scalable, maintainable, and follow n8n best practices.`,

      'optimization': `You are a voice campaign optimization specialist. Analyze campaign performance and suggest improvements. Focus on:
        - Conversion rate optimization
        - Cost efficiency improvements
        - Quality score enhancement
        - Outcome achievement strategies

        Provide data-driven recommendations with clear implementation steps.`,

      'validation': `You are a configuration validation expert. Review voice campaign setups for completeness and potential issues. Focus on:
        - Missing required configurations
        - Integration compatibility
        - Potential failure points
        - Compliance and best practices

        Identify all issues and provide clear resolution steps.`
    };

    return prompts[type] || 'You are a helpful AI assistant specializing in voice campaign optimization.';
  }

  /**
   * Optimize prompt for specific provider
   */
  private optimizePromptForProvider(provider: keyof typeof this.providers, request: LLMRequest): string {
    let prompt = request.prompt;

    // Add context if provided
    if (request.context) {
      prompt = `Context: ${request.context}\n\nRequest: ${prompt}`;
    }

    // Provider-specific optimizations
    switch (provider) {
      case 'anthropic':
        // Claude responds well to structured prompts with clear instructions
        return `Please analyze the following voice campaign configuration and provide detailed recommendations:

${prompt}

Please structure your response with:
1. Key findings and observations
2. Specific optimization recommendations
3. Potential risks or issues
4. Implementation priority order

Be thorough but concise in your analysis.`;

      case 'openai':
        // GPT-4 works well with role-based prompts
        return `As an expert voice campaign consultant, please provide a comprehensive analysis of this configuration:

${prompt}

Your response should include:
- Critical success factors
- Optimization opportunities
- Risk mitigation strategies
- Next steps and recommendations

Format your response in clear, actionable sections.`;

      case 'gemini':
        // Gemini prefers direct, straightforward prompts
        return `Analyze this voice campaign configuration and provide optimization suggestions:

${prompt}

Focus on practical improvements that will increase campaign success rates and provide specific implementation guidance.`;

      default:
        return prompt;
    }
  }

  /**
   * Validate response quality
   */
  private validateResponse(response: LLMResponse, request: LLMRequest): boolean {
    // Basic validation
    if (!response.content || response.content.length < 50) {
      return false;
    }

    // Type-specific validation
    switch (request.type) {
      case 'campaign-analysis':
        return response.content.includes('recommend') || response.content.includes('suggest');

      case 'workflow-generation':
        return response.content.includes('node') || response.content.includes('workflow');

      case 'optimization':
        return response.content.includes('improve') || response.content.includes('optimize');

      case 'validation':
        return response.content.includes('valid') || response.content.includes('issue');

      default:
        return true;
    }
  }

  /**
   * Calculate confidence score based on provider performance
   */
  private calculateConfidence(provider: string, content: string, latency: number): number {
    let confidence = 0.5; // Base confidence

    // Provider-specific confidence adjustments
    switch (provider) {
      case 'anthropic':
        confidence = 0.9; // Highest confidence for primary provider
        break;
      case 'openai':
        confidence = 0.8; // High confidence for fallback
        break;
      case 'gemini':
        confidence = 0.7; // Lower confidence for final fallback
        break;
    }

    // Adjust based on response length (longer = more detailed = higher confidence)
    if (content.length > 1000) confidence += 0.05;
    if (content.length > 2000) confidence += 0.05;

    // Adjust based on latency (faster = better = higher confidence)
    if (latency < 5000) confidence += 0.05;
    if (latency < 2000) confidence += 0.05;

    return Math.min(1.0, confidence);
  }

  /**
   * Generate cache key for request
   */
  private generateCacheKey(request: LLMRequest): string {
    const hashInput = `${request.type}:${request.prompt}:${request.context || ''}:${request.maxTokens || 4000}:${request.temperature || 0.7}`;

    // Simple hash function for cache key
    let hash = 0;
    for (let i = 0; i < hashInput.length; i++) {
      const char = hashInput.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return Math.abs(hash).toString(16);
  }

  /**
   * Record analytics for provider performance
   */
  private recordAnalytics(provider: string, success: boolean, latency: number): void {
    this.analytics.push({
      provider,
      success,
      latency,
      timestamp: new Date().toISOString()
    });

    // Keep only last 1000 entries
    if (this.analytics.length > 1000) {
      this.analytics = this.analytics.slice(-1000);
    }
  }

  /**
   * Get analytics data for monitoring
   */
  getAnalytics(): any {
    const byProvider = this.analytics.reduce((acc, entry) => {
      if (!acc[entry.provider]) {
        acc[entry.provider] = {
          total: 0,
          successful: 0,
          failed: 0,
          avgLatency: 0,
          latencies: []
        };
      }

      acc[entry.provider].total++;
      if (entry.success) {
        acc[entry.provider].successful++;
        acc[entry.provider].latencies.push(entry.latency);
      } else {
        acc[entry.provider].failed++;
      }

      return acc;
    }, {} as any);

    // Calculate averages
    Object.keys(byProvider).forEach(provider => {
      const data = byProvider[provider];
      data.successRate = data.total > 0 ? (data.successful / data.total) * 100 : 0;
      data.avgLatency = data.latencies.length > 0
        ? data.latencies.reduce((sum: number, lat: number) => sum + lat, 0) / data.latencies.length
        : 0;
      delete data.latencies; // Remove raw latency data
    });

    return {
      overall: {
        totalRequests: this.analytics.length,
        cacheSize: this.cache.size
      },
      byProvider
    };
  }

  /**
   * Clear cache (useful for testing or memory management)
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Convenience method for campaign analysis
   */
  async analyzeCampaign(campaignConfig: any): Promise<LLMResponse> {
    return this.processRequest({
      prompt: `Analyze this voice campaign configuration for optimization opportunities:

Campaign Name: ${campaignConfig.name}
Description: ${campaignConfig.description}
Template: ${campaignConfig.templateId || 'Custom'}
Test Audience: ${campaignConfig.testAudienceNumbers?.length || 0} contacts
Main Audience: ${campaignConfig.expectedVolume || 0} contacts
VAPI Assistant: ${campaignConfig.vapiAssistantId}
Integrations: ${campaignConfig.selectedIntegrations?.join(', ') || 'None'}
Desired Outcomes: ${campaignConfig.desiredOutcomes?.join(', ') || 'None'}
Launch Type: ${campaignConfig.launchType || 'test-first'}

Please provide specific optimization recommendations.`,
      type: 'campaign-analysis',
      maxTokens: 2000,
      temperature: 0.7
    });
  }

  /**
   * Convenience method for workflow validation
   */
  async validateWorkflow(workflow: any): Promise<LLMResponse> {
    return this.processRequest({
      prompt: `Validate this n8n workflow configuration for a voice campaign:

Workflow Name: ${workflow.name}
Node Count: ${workflow.nodes?.length || 0}
Has VAPI Integration: ${workflow.nodes?.some((n: any) => n.name.includes('VAPI')) || false}
Has Error Handling: ${workflow.nodes?.some((n: any) => n.name.includes('Error')) || false}
Has Analytics: ${workflow.nodes?.some((n: any) => n.name.includes('Analytics')) || false}

Please identify any missing components, potential issues, or improvement opportunities.`,
      type: 'validation',
      maxTokens: 1500,
      temperature: 0.5
    });
  }
}

// Export singleton instance
export const llmFallbackService = LLMFallbackService.getInstance();
export default llmFallbackService;