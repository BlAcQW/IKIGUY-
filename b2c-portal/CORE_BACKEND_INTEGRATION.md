# B2C Portal Core Backend Integration

## Overview

This document summarizes the integration of the B2C Portal with the Core Backend's internal APIs. The B2C Portal is the main SaaS frontend for self-serve customers and connects to the Core Backend (private control plane) for all business logic and data operations.

## Architecture

```
B2C Portal (React Frontend) → Core Backend (Internal APIs) → Shared Libraries
```

### Key Points:

- **B2C Portal**: React/TypeScript frontend application
- **Core Backend**: Private control plane with internal APIs (`/internal/*`)
- **No Separate Backend**: B2C Portal does not have its own backend - it uses Core Backend directly
- **Authentication**: Uses service tokens for Core Backend API calls
- **Shared Libraries**: Core Backend integrates with shared libraries for telephony, config, usage, license, etc.

## Implementation

### 1. Core API Service Layer (`src/lib/core-api.ts`)

Created a comprehensive service layer that provides TypeScript interfaces and API methods for all Core Backend endpoints:

#### API Categories:

- **Assistant Management**: Create, get, list assistants
- **Campaign Management**: Create, get, list campaigns
- **Knowledge Base**: Ingest content, search knowledge base
- **License Management**: Get status, verify, activate licenses
- **Usage Analytics**: Get usage data, dashboard data
- **Payment Management**: Payment methods, deposits, mobile money, wallet
- **MCP Integrations**: CRM leads, contacts, helpdesk tickets, payments
- **Health Check**: Core Backend health status

#### Key Features:

- TypeScript interfaces for all API responses
- Authenticated requests with service tokens
- Error handling and timeout management
- Mock implementations for endpoints not yet available in Core Backend

### 2. React Hooks (`src/hooks/useCoreApi.ts`)

Created React hooks using TanStack Query for state management and caching:

#### Available Hooks:

- `useAssistants(tenantId)` - Assistant management
- `useCampaigns(tenantId)` - Campaign management
- `useLicense(tenantId)` - License management
- `useUsage(tenantId)` - Usage analytics
- `usePayments(tenantId)` - Payment management
- `useKnowledgeBase(tenantId)` - Knowledge base operations
- `useMCP(tenantId)` - MCP integrations
- `useHealth()` - Health monitoring

#### Features:

- Automatic caching and background refetching
- Loading and error states
- Optimistic updates
- Toast notifications for success/error
- Mutation handling with proper error handling

## Core Backend API Endpoints Used

### Assistant Management

- `POST /internal/assistants` - Create assistant
- `GET /internal/assistants/{id}` - Get assistant
- `GET /internal/assistants` - List assistants (mock)

### Campaign Management

- `POST /internal/campaigns` - Create campaign
- `GET /internal/campaigns/{id}` - Get campaign
- `GET /internal/campaigns` - List campaigns (mock)

### Knowledge Base

- `POST /internal/kb` - Ingest content
- `POST /internal/kb/search` - Search knowledge base

### License Management

- `GET /internal/licenses/status/{tenant_id}` - Get license status
- `POST /internal/licenses/verify` - Verify license
- `POST /internal/licenses/activate` - Activate license

### Usage Analytics

- `GET /internal/usage` - Get usage data
- Usage dashboard (mock implementation)

### Payment Management

- `GET /internal/payments/methods` - Get payment methods
- `POST /internal/payments/deposit` - Create deposit
- `POST /internal/payments/mobile-money` - Process mobile money
- `GET /internal/payments/wallet/{tenant_id}` - Get wallet balance

### MCP Integrations

- `POST /internal/mcp/crm/leads` - Create CRM lead
- `PUT /internal/mcp/crm/contacts/{id}` - Update CRM contact
- `POST /internal/mcp/helpdesk/tickets` - Create helpdesk ticket
- `POST /internal/mcp/payments/process` - Process payment

### Health Check

- `GET /health` - Core Backend health status

## Authentication Flow

1. **User Authentication**: B2C Portal uses Supabase Auth for user authentication
2. **Service Token**: User's access token is used as service token for Core Backend calls
3. **API Calls**: All Core Backend API calls include `X-Service-Token` header
4. **Authorization**: Core Backend validates service tokens and enforces tenant isolation

## Environment Configuration

```typescript
// Core Backend API URL (defaults to localhost:8000)
const CORE_API_BASE_URL =
  import.meta.env.VITE_CORE_API_URL || 'http://localhost:8000';
```

## Usage Examples

### Creating an Assistant

```typescript
import { useAssistants } from '@/hooks/useCoreApi';

function AssistantBuilder() {
  const { createAssistant, isCreatingAssistant } = useAssistants(tenantId);

  const handleCreate = async (assistantData) => {
    await createAssistant({
      name: 'Sales Assistant',
      template: 'sales',
      channel: 'voice',
      language: 'en',
      voice: 'sarah',
      prompt: 'You are a professional sales assistant...',
      tenant_id: tenantId,
    });
  };
}
```

### Getting Usage Analytics

```typescript
import { useUsage } from '@/hooks/useCoreApi';

function AnalyticsDashboard() {
  const { usageData, usageDashboard, isLoadingUsage } = useUsage(tenantId);

  if (isLoadingUsage) return <div>Loading...</div>;

  return (
    <div>
      <h2>Usage Analytics</h2>
      <p>Total Minutes: {usageData?.minutes}</p>
      <p>Total Messages: {usageData?.messages}</p>
    </div>
  );
}
```

### License Verification

```typescript
import { useLicense } from '@/hooks/useCoreApi';

function FeatureGate() {
  const { verifyLicense, licenseInfo } = useLicense(tenantId);

  const checkFeatureAccess = async () => {
    const result = await verifyLicense({ agents: 1, channels: 1 });
    if (result.allowed) {
      // Enable feature
    }
  };
}
```

## Benefits

1. **Centralized Business Logic**: All business logic resides in Core Backend
2. **Shared Libraries**: Leverages shared telephony, config, usage, license libraries
3. **Consistent APIs**: Standardized API responses and error handling
4. **Type Safety**: Full TypeScript support with proper interfaces
5. **Caching**: Efficient data caching with TanStack Query
6. **Error Handling**: Comprehensive error handling with user feedback
7. **Scalability**: Frontend can scale independently of backend

## Next Steps

1. **Update Components**: Replace mock data in existing components with Core Backend API calls
2. **Add Missing Endpoints**: Implement missing endpoints in Core Backend (e.g., list assistants, list campaigns)
3. **Token Exchange**: Implement proper JWT to service token exchange
4. **Error Boundaries**: Add React error boundaries for API failures
5. **Testing**: Add unit tests for API hooks and service layer
6. **Performance**: Optimize API calls and implement proper loading states

## Files Created/Modified

### New Files:

- `src/lib/core-api.ts` - Core Backend API service layer
- `src/hooks/useCoreApi.ts` - React hooks for Core Backend APIs
- `CORE_BACKEND_INTEGRATION.md` - This documentation

### Modified Files:

- `TASKS.md` - Updated to reflect Core Backend integration progress

## Conclusion

The B2C Portal now has a complete integration layer with the Core Backend, providing access to all shared library functionality through a clean, type-safe API. This follows the correct architecture where the B2C Portal is a pure frontend that connects to the Core Backend's internal APIs, eliminating the need for a separate backend service.
