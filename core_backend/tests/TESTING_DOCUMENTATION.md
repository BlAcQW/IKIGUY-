# Automation Testing System Documentation

## Overview
This document outlines the comprehensive testing system for the automation orchestration platform, including the AutomationDeploymentWizard, automation orchestration services, and template-specific tests.

## Testing Architecture

### 1. Frontend Component Tests (AutomationDeploymentWizard)
**Location**: `/opt/kasaai/apps/b2c-portal/src/components/campaigns/AutomationDeploymentWizard.tsx`

#### Current Test Coverage
- **Configuration Save/Load Tests**: Validation of automation configuration persistence
- **Deployment Flow Tests**: End-to-end deployment workflow testing
- **Health Check Integration**: Frontend health monitoring functionality
- **Form Validation**: Input validation and error handling

#### Test Requirements
```typescript
// Component Test Structure
describe('AutomationDeploymentWizard', () => {
  describe('Configuration Management', () => {
    test('saves configuration with all fields');
    test('loads existing configuration');
    test('validates required fields');
    test('handles configuration errors');
  });

  describe('Deployment Process', () => {
    test('deploys automation successfully');
    test('handles deployment failures');
    test('performs health checks after deployment');
    test('updates UI with deployment status');
  });

  describe('Health Monitoring', () => {
    test('displays health status indicators');
    test('refreshes health status');
    test('handles unhealthy components');
  });
});
```

### 2. Backend Service Tests

#### 2.1 VAPI Service Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/test_vapi_service.py` ✅ **IMPLEMENTED**

**Test Coverage**:
- ✅ Agent creation (success/failure scenarios)
- ✅ Agent listing and retrieval
- ✅ Assistant management operations
- ✅ Call initiation and management
- ✅ Phone number retrieval
- ✅ Tenant-specific agent creation
- ✅ Connection testing and health checks
- ✅ Error handling and logging
- ✅ Session management and cleanup

**Key Test Methods**:
```python
class TestVAPIService:
    def test_create_agent_success()
    def test_create_agent_api_error()
    def test_list_agents_success()
    def test_get_assistant_success()
    def test_get_assistant_not_found()
    def test_initiate_call_success()
    def test_health_check_comprehensive()
    def test_error_handling_and_logging()
```

#### 2.2 N8N Service Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/test_n8n_service.py` ✅ **IMPLEMENTED**

**Test Coverage**:
- ✅ Workflow creation (success/failure scenarios)
- ✅ Workflow activation and deactivation
- ✅ Workflow triggering via webhooks
- ✅ Template search and retrieval
- ✅ Workflow customization for campaigns
- ✅ Health check operations
- ✅ MCP tools integration fallback
- ✅ Webhook URL extraction
- ✅ Error handling and configuration

**Key Test Methods**:
```python
class TestN8NService:
    def test_create_workflow_success()
    def test_create_workflow_api_error()
    def test_stop_workflow_success()
    def test_activate_workflow_success()
    def test_trigger_workflow_success()
    def test_search_workflow_template_success()
    def test_workflow_health_check_comprehensive()
    def test_webhook_connectivity()
```

#### 2.3 Automation Orchestration Service Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/test_automation_monitoring.py` ✅ **IMPLEMENTED**

**Test Coverage**:
- ✅ Full deployment orchestration
- ✅ Health monitoring and status checks
- ✅ VAPI and N8N integration
- ✅ Configuration validation
- ✅ Error handling and recovery
- ✅ Monitoring functionality
- ✅ Real-time health checks

**Key Test Methods**:
```python
class TestAutomationMonitoring:
    def test_deploy_automation_full_workflow()
    def test_health_monitoring_real_time()
    def test_automation_status_monitoring()
    def test_integration_error_handling()
    def test_configuration_validation()
```

### 3. Template-Specific Tests

#### 3.1 Health Locator Template Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/templates/test_health_locator_template.py` ⚠️ **NEEDS IMPLEMENTATION**

**Test Requirements**:
```python
class TestHealthLocatorTemplate:
    """Comprehensive tests for Health Locator automation template."""

    def test_template_deployment()
    def test_vapi_agent_with_healthcare_tools()
    def test_n8n_workflow_nodes()
    def test_premier_health_integration()
    def test_healthcare_provider_search()
    def test_emergency_provider_lookup()
    def test_provider_details_retrieval()
    def test_area_and_specialty_filtering()
    def test_vapi_webhook_handling()
    def test_email_and_sms_notifications()
    def test_support_escalation()
    def test_end_to_end_call_flow()
```

#### 3.2 Premier Health Custom Tools Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/templates/test_premier_health_tools.py` ⚠️ **NEEDS IMPLEMENTATION**

**Custom Tools Coverage** (from `/opt/kasaai/apps/core_backend/backend/routes/premier_health.py`):
- 🔧 `search_healthcare_providers`: Main search functionality
- 🔧 `get_emergency_providers`: Emergency provider lookup
- 🔧 `get_provider_details`: Detailed provider information
- 🔧 `get_available_areas`: Location coverage
- 🔧 `get_available_specialties`: Medical specialties
- 🔧 `get_providers_by_area`: Area-specific search
- 🔧 `get_providers_by_specialty`: Specialty-specific search
- 🔧 `vapi_webhook`: Webhook handling for voice interactions
- 🔧 `send_provider_info_email`: Email notifications
- 🔧 `send_provider_info_sms`: SMS notifications
- 🔧 `escalate_to_support`: Support ticket creation

### 4. Integration Tests

#### 4.1 End-to-End Automation Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/integration/test_e2e_automation.py` ⚠️ **NEEDS IMPLEMENTATION**

**Test Scenarios**:
- Complete automation deployment workflow
- Frontend-to-backend integration
- VAPI and N8N service coordination
- Health monitoring across all components
- Error recovery and fallback scenarios

#### 4.2 Template Integration Tests
**Location**: `/opt/kasaai/apps/core_backend/tests/integration/test_template_integration.py` ⚠️ **NEEDS IMPLEMENTATION**

**Test Coverage**:
- Template-specific deployment workflows
- Custom tool integration with VAPI agents
- N8N workflow execution with custom endpoints
- Real-world scenario simulation

## Test Organization Structure

```
/opt/kasaai/apps/core_backend/tests/
├── TESTING_DOCUMENTATION.md (this file)
├── test_vapi_service.py ✅
├── test_n8n_service.py ✅
├── test_automation_monitoring.py ✅
├── templates/
│   ├── __init__.py
│   ├── test_health_locator_template.py ⚠️
│   ├── test_premier_health_tools.py ⚠️
│   └── conftest.py (shared fixtures)
├── integration/
│   ├── __init__.py
│   ├── test_e2e_automation.py ⚠️
│   └── test_template_integration.py ⚠️
└── fixtures/
    ├── automation_configs.py
    ├── vapi_responses.py
    └── n8n_workflows.py
```

## Test Data and Fixtures

### Automation Configuration Fixtures
```python
# /opt/kasaai/apps/core_backend/tests/fixtures/automation_configs.py
HEALTH_LOCATOR_CONFIG = {
    "name": "Premier Health Provider Locator",
    "description": "Healthcare provider search automation",
    "category": "healthcare",
    "template_id": "health_locator",
    "company_info": {
        "name": "Premier Health Insurance",
        "description": "Healthcare provider location service"
    },
    "vapi_agent": {
        "name": "Premier Health Assistant",
        "system_prompt": "You are a helpful healthcare assistant...",
        "voice": "alloy",
        "tools": [...] # Custom healthcare tools
    },
    "n8n_workflow": {
        "workflow_name": "Premier Health Automation",
        "nodes": [...], # Workflow nodes
        "connections": {...} # Node connections
    }
}
```

## Testing Guidelines

### 1. Test Naming Convention
- **Unit Tests**: `test_[component]_[method]_[scenario]`
- **Integration Tests**: `test_[feature]_integration_[scenario]`
- **Template Tests**: `test_[template_name]_[functionality]`

### 2. Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interaction and data flow
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization

### 3. Mock vs Real Integration
- **Development**: Use mocks for external services
- **CI/CD**: Use real services for integration tests
- **Production**: Monitor real deployments with health checks

### 4. Test Data Management
- Use fixtures for consistent test data
- Clean up after each test
- Isolate test environments
- Use test-specific configurations

## Running Tests

### Individual Test Suites
```bash
# VAPI Service Tests
pytest tests/test_vapi_service.py -v

# N8N Service Tests
pytest tests/test_n8n_service.py -v

# Automation Monitoring Tests
pytest tests/test_automation_monitoring.py -v

# Template-specific Tests
pytest tests/templates/ -v

# Integration Tests
pytest tests/integration/ -v
```

### Complete Test Suite
```bash
# Run all automation tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test markers
pytest tests/ -m "healthcare" -v
pytest tests/ -m "integration" -v
```

## Health Check and Monitoring

### Deployment Health Checks
- ✅ VAPI agent creation and availability
- ✅ N8N workflow activation and webhook accessibility
- ✅ Custom tool endpoint responsiveness
- ✅ Database connectivity
- ✅ Real-time status monitoring

### Continuous Monitoring
- Service health indicators
- Error rate monitoring
- Performance metrics
- User interaction analytics
- Escalation tracking

## Next Steps

### Priority Implementation
1. **Health Locator Template Tests** - Comprehensive template testing
2. **Premier Health Tools Tests** - Custom tool validation
3. **E2E Integration Tests** - Complete workflow testing
4. **Frontend Component Tests** - AutomationDeploymentWizard testing

### Future Enhancements
- Performance benchmarking
- Load testing for voice interactions
- Security penetration testing
- A/B testing for template variations
- Analytics and reporting integration

---

**Legend**:
- ✅ **IMPLEMENTED**: Test suite is complete and functional
- ⚠️ **NEEDS IMPLEMENTATION**: Test suite needs to be created
- 🔧 **CUSTOM TOOL**: Premier Health specific functionality

Last Updated: 2025-09-19


  Summary of Changes

  1. Updated Existing Tests to Verify Actual Tool Functionality

  - Enhanced the VAPI chat method in
  test_real_vapi_chat_general_tools.py to capture and print tool results
   for verification
  - Removed duplicate healthcare tests from the general tools test file
  to avoid bloat
  - Focused each test file on its specific purpose:
    - test_real_vapi_chat_healthcare_tools.py: Healthcare-specific tools
    - test_real_vapi_chat_general_tools.py: Communication, calendar,
  support, and search tools

  2. Made Tests Run Automatically When App Starts

  - Created a comprehensive test runner
  (backend/services/vapi_test_runner.py) that runs:
    - Unit tests: Fast tests without external dependencies
    - Integration tests: Tests with external dependencies
    - VAPI tools tests: Quick validation of VAPI functionality
  - Integrated the test runner into app startup in main.py
  - Added environment variable control (STARTUP_TESTS_ENABLED) to
  enable/disable tests