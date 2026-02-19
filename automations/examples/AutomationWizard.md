I'll analyze the EnhancedHelpdeskWizard.tsx to understand the
  automation wizard steps and implementation details.

● Based on my analysis of the EnhancedHelpdeskWizard.tsx, here's the
  complete breakdown:

  Wizard Steps and Implementation

  8-Step Automation Wizard Process:

  1. Company Info (Globe icon)
  2. Extract Data (Database icon)
  3. Voice Agent (Bot icon)
  4. N8N Workflow (Workflow icon)
  5. Integrations (Settings icon)
  6. Demo Setup (ExternalLink icon)
  7. Analytics (BarChart3 icon)
  8. Review (CheckCircle icon)

● Services & Functions per Step:

  Step 1: Company Information

  - Functions: updateConfig() for form state management
  - Fields: Company name, website URL, description
  - Services: None (pure form input)

  Step 2: Extract Data

  - Main Function: extractCompanyInfo() (lines 348-409)
  - API Endpoint: ${apiBaseUrl}/extract-site-info
  - Services: Site extraction service for company information
  - Enhancement Function: generateEnhancedSystemPrompt() (lines 411-433)

  Step 3: Voice Agent (VAPI)

  - Main Function: createVAPIAgent() (lines 510-568)
  - API Endpoint: ${apiBaseUrl}/vapi/create-assistant
  - Services: VAPI voice assistant creation
  - Configuration: Voice settings, AI model, system prompts, tools

  Step 4: N8N Workflow

  - Main Function: createN8NWorkflow() (lines 435-508)
  - Services: N8N automation workflow creation
  - Integration: Webhook triggers, calendar, ticketing, Supabase logging

  Step 5: Integrations

  - Services Configured:
    - Calendly: Appointment booking (calendly.enabled, calendly.apiKey)
    - Supabase: Database/logging (supabase.projectId)
    - Tavily: Web search (tavily.apiKey)
    - Resend: Email notifications (resend.apiKey)
    - Vonage: SMS messaging (vonage.apiKey)

  Step 6: Demo Setup

  - Main Function: deployDemo() (lines 570-605)
  - Helper Function: generateDemoHTML() (lines 607-681)
  - API Endpoint: ${apiBaseUrl}/deploy-demo
  - Services: Demo page deployment with VAPI integration

  Step 7: Analytics

  - Configuration: Analytics tracking settings
  - Features: Call analytics, performance metrics, email reporting
  - Fields: Report email, webhook URL, tracking enablement

  Step 8: Review

  - Main Function: handleSubmit() (lines 683-729)
  - Orchestration: Calls all creation functions in sequence
  - Services: Campaign creation via onCreateCampaign(config)

● Core Configuration Interface:

  interface EnhancedHelpdeskConfig {
    companyInfo: CompanyInfo;
    vapiAgent: VAPIAgent;
    n8nWorkflow: N8NWorkflow;
    integrations: {
      calendly, supabase, tavily, resend, vonage
    };
    demoSettings: DemoSettings;
    analytics: AnalyticsConfig;
  }

  Template Adaptation System:

  The wizard includes sophisticated template adaptation via:
  - adaptConfigForTemplate() (lines 206-237)
  - generateTemplateSpecificPrompt() (lines 240-259)
  - adaptToolsForTemplate() (lines 262-281)
  - adaptEndpointsForTemplate() (lines 284-335)

  Template Categories: sales, retention, support, scheduling

  Key External Dependencies:

  1. API Services: Site extraction, VAPI assistant creation, demo
  deployment
  2. Integration APIs: Calendly, Supabase, Tavily, Resend, Vonage
  3. N8N Workflow Engine: For automation orchestration
  4. Toast Notifications: User feedback system

● The wizard implements a comprehensive 8-step automation setup process
  with robust template adaptation, external service integrations, and a
  sophisticated configuration management system. Each step has dedicated
   functions and API endpoints for creating a complete helpdesk
  automation solution.


  Based on my review of the Premier Health automation system, here are
  the deployment stages, functions, and services:

  Deployment Stages:

  Stage 1: Data Import & Database Setup

  - Function: import_data.py - Data migration from Excel to PostgreSQL
  - Database: PostgreSQL with pgvector extension for semantic search
  - Data: 103 healthcare providers with complete contact information
  - Schema: Optimized indexes for provider name, area, and specialty
  searches

  Stage 2: Voice Agent Tools Development

  - Core Class: HealthcareVoiceTools
  (/opt/kasaai/apps/automations/premier-health/voice_agent_tools.py:12)
  - Query Engine: VoiceAgentQueries for natural language processing
  - Area Mapping: AreaMapper for location normalization

  Stage 3: API Integration

  - Backend Routes:
  /opt/kasaai/apps/core_backend/backend/routes/premier_health.py
  - API Prefix: /premier-health
  - Authentication: Bearer token via get_current_user_bearer

  Stage 4: N8N Workflow Deployment

  - Workflow Files:
    - n8n_premier_health_workflow.json
    - n8n_premier_health_workflow_enhanced.json
    - n8n_premier_health_workflow_with_freshdesk.json

  Stage 5: VAPI Voice Assistant Configuration

  - Config File: claims/vapi_assistant_config.json
  - Voice Provider: 11labs with "rachel" voice
  - Model: GPT-4 with temperature 0.7

● Core Functions & Services:

  Healthcare Search Functions:

  1. search_healthcare_providers() (/opt/kasaai/apps/automations/premier
  -health/voice_agent_tools.py:17-95)
    - Natural language query processing
    - Multi-filter search (location, specialty, provider_type)
    - Confidence scoring and voice response formatting
  2. get_provider_details() (/opt/kasaai/apps/automations/premier-health
  /voice_agent_tools.py:97-148)
    - Individual provider information retrieval
    - Voice-optimized response formatting
  3. get_emergency_providers() - Emergency healthcare prioritization
  4. get_providers_by_area() (/opt/kasaai/apps/automations/premier-healt
  h/voice_agent_tools.py:149-200)
  5. get_providers_by_specialty()

  API Endpoints:

  - /search (/opt/kasaai/apps/core_backend/backend/routes/premier_health
  .py:77-118) - Main search endpoint
  - /emergency-providers (/opt/kasaai/apps/core_backend/backend/routes/p
  remier_health.py:120-148)
  - /vapi-webhook (/opt/kasaai/apps/core_backend/backend/routes/premier_
  health.py:281-387) - VAPI integration
  - /send-email (/opt/kasaai/apps/core_backend/backend/routes/premier_he
  alth.py:448-478) - Provider info delivery
  - /send-sms (/opt/kasaai/apps/core_backend/backend/routes/premier_heal
  th.py:480-509)
  - /escalate-to-support (/opt/kasaai/apps/core_backend/backend/routes/p
  remier_health.py:552-598) - Freshdesk integration

  Integration Services:

  1. PostgreSQL Database - Provider data storage with semantic search
  2. VAPI Voice Platform - Voice assistant integration
  3. N8N Automation - Workflow orchestration
  4. Freshdesk - Support ticket escalation
  5. Email/SMS Services - Information delivery
  6. Background Analytics - Call summary logging

  Voice Assistant Functions:

  - checkClaimStatus - Insurance claim status checking
  - fileNewClaim - New claim filing
  - scheduleCallback - Support scheduling
  - getRequiredDocuments - Documentation guidance
  - updateClaimInformation - Claim updates

  The Premier Health system implements a complete voice-enabled
  healthcare provider location service with intelligent search,
  multi-channel communication, and comprehensive analytics tracking.





  is there a way merge the functionality and get the best
  of both which will be used as a generic automation deployment wizard
  that can be preconfigured with all settings to for quick demo deployment
  but also allows users to configure the various stages as with the
  @apps/b2c-portal/src/components/campaigns/EnhancedHelpdeskWizard.tsx? it
  should also use standard functions for each stage - ex.




  The TemplateManagementService uses a different interface structure than
  AutomationTemplatesService. Let me update the AutomationDeploymentWizard to use the database-driven AutomationTemplatesService: