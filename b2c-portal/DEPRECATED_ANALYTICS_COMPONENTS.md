# Deprecated Analytics Components

The following analytics components have been deprecated as part of the analytics consolidation effort. They have been marked with `@deprecated` comments and will be removed in a future release.

## Deprecated Components

### 1. AutomationAnalyticsDashboard.tsx
- **Reason**: Consolidated into `UnifiedAutomationDashboard`
- **Replacement**: Use `UnifiedAutomationDashboard` instead
- **Status**: Marked as deprecated

### 2. AutomationMonitoringDashboard.tsx
- **Reason**: Consolidated into `UnifiedAutomationDashboard`
- **Replacement**: Use `UnifiedAutomationDashboard` instead
- **Status**: Marked as deprecated

### 3. EnhancedAnalytics.tsx
- **Reason**: Features absorbed into other components
- **Replacement**: Use `UnifiedAutomationDashboard`, `DeploymentAnalyticsDashboard`, or `RealTimeHealthMonitor`
- **Status**: Marked as deprecated

### 4. AutomationHealthCard.tsx
- **Reason**: Functionality moved to `RealTimeHealthMonitor`
- **Replacement**: Use `RealTimeHealthMonitor` or health subcomponents
- **Status**: Marked as deprecated

## Migration Guide

### From AutomationAnalyticsDashboard or AutomationMonitoringDashboard
```tsx
// Old
import AutomationAnalyticsDashboard from '@/components/analytics/AutomationAnalyticsDashboard';
import AutomationMonitoringDashboard from '@/components/analytics/AutomationMonitoringDashboard';

// New
import UnifiedAutomationDashboard from '@/components/analytics/UnifiedAutomationDashboard';

// Usage
<UnifiedAutomationDashboard
  configId="your-config-id"
  timeRange="7d"
/>
```

### From AutomationHealthCard
```tsx
// Old
import AutomationHealthCard from '@/components/analytics/AutomationHealthCard';

// New
import RealTimeHealthMonitor from '@/components/analytics/RealTimeHealthMonitor';
// Or use the individual health components
import HealthStatusCard from '@/components/analytics/health/HealthStatusCard';

// Usage
<RealTimeHealthMonitor
  automationId="your-automation-id"
  showActivityLog={true}
  refreshInterval={30000}
/>
```

## New Analytics Structure

After consolidation, the analytics system now consists of:

1. **UnifiedAutomationDashboard** - Main automation analytics
2. **DeploymentAnalyticsDashboard** - Deployment-specific metrics
3. **RealTimeHealthMonitor** - Health monitoring
4. **VapiAnalyticsDashboard** - Voice/VAPI analytics
5. **Analytics Page** - Unified page with sidebar navigation

## Removal Timeline

These deprecated components will be removed in the next major release after all references have been updated.

## Related Files Updated

- `src/pages/AutomationConfiguration.tsx` - Updated import
- `src/components/campaigns/AutomationDeploymentWizard.tsx` - Updated import
- `src/tests/category-fix.test.tsx` - Mock updated
- `src/components/campaigns/__tests__/AutomationDeploymentWizard.simple.test.tsx` - Mock updated