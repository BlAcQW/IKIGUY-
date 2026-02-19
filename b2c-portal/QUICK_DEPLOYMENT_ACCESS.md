# QuickAutomationDeployment Component Access Guide

## 🎯 Overview

The `QuickAutomationDeployment.tsx` component provides a streamlined interface for deploying voice automations from company URLs. This guide shows how to access and integrate it into your B2C portal.

## 📁 Component Location

```
/opt/kasaai/apps/b2c-portal/src/components/campaigns/QuickAutomationDeployment.tsx
```

## 🚀 Access Methods

### Method 1: Add to Existing Routes (Recommended)

#### Step 1: Import the Component
Add to your routing file (usually `App.tsx` or a dedicated routes file):

```typescript
import QuickAutomationDeployment from '@/components/campaigns/QuickAutomationDeployment';
```

#### Step 2: Add Route Definition
Add to your route configuration:

```typescript
// React Router v6 example
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      {/* Existing routes */}
      <Route path="/quick-deploy" element={<QuickAutomationDeployment />} />
      <Route path="/automation/quick-deploy" element={<QuickAutomationDeployment />} />
      {/* Other routes */}
    </Routes>
  );
}
```

#### Step 3: Add Navigation Links
Add navigation to your menu/sidebar:

```typescript
// In your navigation component
<NavLink to="/quick-deploy">
  <Zap className="h-4 w-4 mr-2" />
  Quick Deploy
</NavLink>

// Or as a prominent button
<Button asChild>
  <Link to="/quick-deploy">
    <Zap className="h-4 w-4 mr-2" />
    Deploy Automation
  </Link>
</Button>
```

### Method 2: Modal Integration

Add as a modal that can be triggered from anywhere:

```typescript
import { useState } from 'react';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import QuickAutomationDeployment from '@/components/campaigns/QuickAutomationDeployment';

function QuickDeployModal() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Zap className="h-4 w-4 mr-2" />
          Quick Deploy Automation
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <QuickAutomationDeployment />
      </DialogContent>
    </Dialog>
  );
}
```

### Method 3: Dashboard Widget

Add as a widget on your main dashboard:

```typescript
// In your dashboard component
import QuickAutomationDeployment from '@/components/campaigns/QuickAutomationDeployment';

function Dashboard() {
  return (
    <div className="grid gap-6">
      {/* Other dashboard widgets */}

      <Card>
        <CardHeader>
          <CardTitle>Quick Automation Deployment</CardTitle>
          <CardDescription>
            Deploy a voice automation from any company website
          </CardDescription>
        </CardHeader>
        <CardContent>
          <QuickAutomationDeployment />
        </CardContent>
      </Card>
    </div>
  );
}
```

## 📋 Required Dependencies

The component requires these dependencies (should already be available):

```json
{
  "@/components/ui/button": "Button component",
  "@/components/ui/input": "Input component",
  "@/components/ui/card": "Card components",
  "@/components/ui/select": "Select components",
  "@/components/ui/tabs": "Tabs components",
  "@/hooks/use-toast": "Toast notifications",
  "@/services/AutomationOrchestrationService": "Backend service",
  "@/components/shared/SystemPromptGenerator": "AI prompt generation",
  "@/lib/auth-utils": "Authentication utilities",
  "lucide-react": "Icons"
}
```

## 🔧 Configuration

### Environment Variables
Ensure these are set in your `.env`:

```bash
# Backend API
VITE_API_BASE_URL=https://api.ailabsafrica.com

# Authentication (Supabase)
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
```

### Backend Requirements
The component requires these backend endpoints to be active:

- `/enhanced-helpdesk/extract-site-info` - Company information extraction
- `/automation-orchestration/templates` - Template management
- `/automation-orchestration/configurations` - Configuration management
- `/automation-orchestration/configurations/{id}/deploy` - Deployment

## 🎨 Customization Options

### Theme Integration
The component uses your existing design system:

```typescript
// Customize colors, spacing, etc. through your CSS variables
// Component automatically inherits your theme
```

### Feature Flags
You can conditionally show features:

```typescript
// Example: Hide healthcare option for non-HIPAA accounts
const automationTypes = defaultAutomationTypes.filter(type =>
  type.id !== 'healthcare' || user.isHipaaCompliant
);
```

### Custom Instructions
Pre-populate with company-specific instructions:

```typescript
// Pass default values as props
<QuickAutomationDeployment
  defaultIndustry="Technology"
  defaultPersonality="professional"
  defaultInstructions="Focus on enterprise sales"
/>
```

## 🌐 URL Access Examples

Once integrated, users can access via:

- **Direct URL**: `https://your-portal.com/quick-deploy`
- **Dashboard**: `https://your-portal.com/dashboard` (if added as widget)
- **Campaigns**: `https://your-portal.com/campaigns/quick-deploy`
- **Modal**: Triggered from any page with the modal button

## 🔗 Integration with Existing Workflows

### From Campaign Creation
Add a "Quick Deploy" option to your existing campaign creation flow:

```typescript
// In your campaign creation component
<div className="grid grid-cols-2 gap-4">
  <Card>
    <CardHeader>
      <CardTitle>Custom Campaign</CardTitle>
      <CardDescription>Build step by step</CardDescription>
    </CardHeader>
    <CardContent>
      <Button onClick={() => navigate('/campaigns/create')}>
        Create Custom
      </Button>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>Quick Deploy</CardTitle>
      <CardDescription>From company website</CardDescription>
    </CardHeader>
    <CardContent>
      <Button onClick={() => navigate('/quick-deploy')}>
        Quick Deploy
      </Button>
    </CardContent>
  </Card>
</div>
```

### From Company Onboarding
Integrate into new customer onboarding:

```typescript
// Step 3 of onboarding flow
<OnboardingStep title="Deploy Your Automation">
  <QuickAutomationDeployment
    companyUrl={onboardingData.website}
    industry={onboardingData.industry}
  />
</OnboardingStep>
```

## 📊 Analytics Integration

Track usage with your analytics:

```typescript
// Add to component
import { trackEvent } from '@/lib/analytics';

// Track deployments
const handleDeploymentSuccess = (result) => {
  trackEvent('automation_deployed', {
    automation_type: automationType,
    industry: industry,
    company_url: companyUrl,
    deployment_time: Date.now() - startTime
  });
};
```

## 🔐 Permission Requirements

Users need these permissions:
- `automations:create` - Create new automations
- `automations:deploy` - Deploy automations
- `integrations:read` - View available integrations
- `templates:read` - Access automation templates

## 🚀 Quick Start Commands

### 1. Add Route (React Router)
```typescript
// In your main routing file
import QuickAutomationDeployment from '@/components/campaigns/QuickAutomationDeployment';

// Add to routes
<Route path="/quick-deploy" element={<QuickAutomationDeployment />} />
```

### 2. Add Navigation
```typescript
// In your sidebar/menu component
<Link to="/quick-deploy" className="nav-link">
  <Zap className="h-4 w-4" />
  Quick Deploy
</Link>
```

### 3. Test Access
```bash
# Navigate to your portal + the route
https://your-portal.com/quick-deploy
```

## 💡 Best Practices

1. **Prominent Placement**: Add to main navigation for easy discovery
2. **Onboarding Integration**: Include in new user flows
3. **Dashboard Widget**: Show on dashboard for quick access
4. **Mobile Responsive**: Component is mobile-friendly
5. **Error Handling**: Component includes comprehensive error handling
6. **Progress Tracking**: Shows clear progress through deployment steps

## 🔍 Troubleshooting

### Component Not Loading
- Check import path is correct
- Verify all dependencies are installed
- Check browser console for errors

### Deployment Failing
- Verify backend endpoints are accessible
- Check authentication tokens
- Ensure user has required permissions

### Styling Issues
- Component uses your existing design system
- Check CSS imports are correct
- Verify theme variables are set

## 📞 Support

The component includes built-in error handling and user feedback. For issues:

1. Check browser console for errors
2. Verify backend connectivity
3. Test with a simple company URL first
4. Check user permissions and authentication

---

**Quick Access URL**: Once integrated, users can access at `/quick-deploy` or wherever you configure the route.