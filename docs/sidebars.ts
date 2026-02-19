import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * KasaAI Developer Documentation Sidebars
 *
 * Five main sidebar sections:
 * 1. Getting Started - Quick onboarding
 * 2. Guides - In-depth tutorials
 * 3. API Reference - Complete API docs
 * 4. Use Cases - Real-world examples
 * 5. Internal - Internal documentation (requires authentication)
 */
const sidebars: SidebarsConfig = {
  // ============================================================================
  // GETTING STARTED
  // ============================================================================
  gettingStartedSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/introduction',
        'getting-started/quickstart',
        'getting-started/authentication',
        'getting-started/first-api-call',
        'getting-started/core-concepts',
      ],
    },
  ],

  // ============================================================================
  // GUIDES
  // ============================================================================
  guidesSidebar: [
    {
      type: 'category',
      label: 'Voice Assistants',
      collapsed: false,
      items: [
        'guides/voice-assistants/creating-assistants',
        'guides/voice-assistants/configuring-voice',
        'guides/voice-assistants/adding-tools',
        'guides/voice-assistants/testing-assistants',
      ],
    },
    {
      type: 'category',
      label: 'Phone Calls',
      items: [
        'guides/phone-calls/making-calls',
        'guides/phone-calls/receiving-calls',
        'guides/phone-calls/call-transfer',
        'guides/phone-calls/recording-calls',
      ],
    },
    {
      type: 'category',
      label: 'Workflows',
      items: [
        'guides/workflows/creating-workflows',
        'guides/workflows/n8n-integration',
        'guides/workflows/webhook-handlers',
        'guides/workflows/error-handling',
      ],
    },
    {
      type: 'category',
      label: 'Best Practices',
      items: [
        'guides/best-practices/error-handling',
        'guides/best-practices/rate-limiting',
        'guides/best-practices/security',
        'guides/best-practices/production-checklist',
      ],
    },
  ],

  // ============================================================================
  // API REFERENCE
  // ============================================================================
  apiReferenceSidebar: [
    'api-reference/overview',
    {
      type: 'category',
      label: 'Assistants',
      items: [
        'api-reference/assistants/create-assistant',
        'api-reference/assistants/get-assistant',
        'api-reference/assistants/update-assistant',
        'api-reference/assistants/delete-assistant',
        'api-reference/assistants/list-assistants',
      ],
    },
    {
      type: 'category',
      label: 'Calls',
      items: [
        'api-reference/calls/create-call',
        'api-reference/calls/get-call',
        'api-reference/calls/list-calls',
        'api-reference/calls/end-call',
      ],
    },
    {
      type: 'category',
      label: 'Workflows',
      items: [
        'api-reference/workflows/create-workflow',
        'api-reference/workflows/get-workflow',
        'api-reference/workflows/update-workflow',
        'api-reference/workflows/delete-workflow',
        'api-reference/workflows/list-workflows',
        'api-reference/workflows/trigger-workflow',
      ],
    },
    {
      type: 'category',
      label: 'Executions',
      items: [
        'api-reference/executions/get-execution',
        'api-reference/executions/list-executions',
      ],
    },
    {
      type: 'category',
      label: 'Usage & Analytics',
      items: [
        'api-reference/usage/get-quota',
        'api-reference/usage/get-rate-limit',
        'api-reference/usage/get-stats',
        'api-reference/usage/get-summary',
      ],
    },
    'api-reference/errors',
  ],

  // ============================================================================
  // USE CASES
  // ============================================================================
  useCasesSidebar: [
    {
      type: 'category',
      label: 'Use Cases',
      collapsed: false,
      items: [
        'use-cases/customer-support-bot',
        'use-cases/appointment-reminders',
        'use-cases/lead-qualification',
        'use-cases/survey-automation',
        'use-cases/delivery-notifications',
        'use-cases/payment-reminders',
        'use-cases/feedback-collection',
        'use-cases/emergency-alerts',
      ],
    },
  ],

  // ============================================================================
  // INTERNAL DOCUMENTATION (Requires Authentication)
  // ============================================================================
  internalSidebar: [
    {
      type: 'category',
      label: 'Internal Documentation',
      collapsed: false,
      items: [
        'internal/introduction',
        'internal/onboarding',
        'internal/architecture',
        'internal/deployment',
        'internal/maintenance',
        'internal/ai-development-guide',
      ],
    },
  ],
};

export default sidebars;
