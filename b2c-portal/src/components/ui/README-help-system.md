# Help System Integration Guide

This guide explains how to integrate tooltips, help icons, and documentation popups throughout the B2C portal.

## 🎯 Overview

The help system provides three main components:
- **HelpIcon**: Interactive help icons with tooltips and modals
- **HelpModal**: Comprehensive help modal with search and navigation
- **useHelp Hook**: React hook for managing help state and content

## 📦 Components

### HelpIcon Component

A versatile help icon that can display tooltips, open modals, or both.

```tsx
import { HelpIcon } from '@/components/ui/help-icon';
import { getHelpContent } from '@/lib/help-content';

const MyComponent = () => {
  const helpContent = getHelpContent('dashboard_overview');
  
  return (
    <div className="flex items-center gap-2">
      <h1>Dashboard</h1>
      <HelpIcon 
        content={helpContent}
        size="sm"
        variant="both"
        position="bottom"
      />
    </div>
  );
};
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `content` | `HelpContent` | Required | Help content object |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Icon size |
| `variant` | `'tooltip' \| 'modal' \| 'both'` | `'both'` | Display mode |
| `position` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'top'` | Tooltip position |
| `className` | `string` | `''` | Additional CSS classes |

### HelpModal Component

A comprehensive help modal with search, navigation, and content display.

```tsx
import { HelpModal } from '@/components/ui/help-modal';
import { useHelp } from '@/hooks/useHelp';

const MyComponent = () => {
  const help = useHelp();
  
  return (
    <>
      <Button onClick={() => help.openHelpModal('dashboard_overview')}>
        Open Help
      </Button>
      
      <HelpModal
        isOpen={help.isHelpModalOpen}
        onClose={help.closeHelpModal}
        initialContent={help.currentHelpContent}
        recentHelp={help.recentHelp}
        onHelpClick={help.openHelpModal}
      />
    </>
  );
};
```

### useHelp Hook

React hook for managing help state and content.

```tsx
import { useHelp } from '@/hooks/useHelp';

const MyComponent = () => {
  const help = useHelp();
  
  const handleHelpClick = () => {
    help.openHelpModal('assistants_overview');
  };
  
  return (
    <div>
      <Button onClick={handleHelpClick}>Get Help</Button>
      <p>Recent help topics: {help.recentHelp.join(', ')}</p>
    </div>
  );
};
```

#### Hook Methods

| Method | Description |
|--------|-------------|
| `getHelp(key)` | Get help content by key |
| `searchHelp(query)` | Search help content |
| `openHelpModal(key)` | Open help modal with content |
| `closeHelpModal()` | Close help modal |
| `addToRecent(key)` | Add help topic to recent list |
| `clearRecent()` | Clear recent help topics |

## 📚 Help Content Structure

Help content is defined in `@/lib/help-content.ts`:

```tsx
interface HelpContent {
  title: string;
  description: string;
  details?: string;
  examples?: string[];
  links?: Array<{
    label: string;
    url: string;
    external?: boolean;
  }>;
  relatedTopics?: string[];
}
```

### Example Help Content

```tsx
export const helpContent = {
  dashboard_overview: {
    title: "Dashboard Overview",
    description: "Your central hub for monitoring performance and accessing key features",
    details: "The dashboard provides real-time insights into your KasaAI usage...",
    examples: [
      "View total calls made in the last 30 days",
      "Monitor assistant success rates"
    ],
    links: [
      { label: "Dashboard Guide", url: "/support#dashboard" },
      { label: "Analytics Documentation", url: "/analytics" }
    ],
    relatedTopics: ["Analytics", "Performance", "Monitoring", "Reports"]
  }
};
```

## 🔧 Integration Examples

### Page Header with Help Icon

```tsx
const DashboardPage = () => {
  const dashboardHelp = getHelpContent('dashboard_overview');
  
  return (
    <div className="flex items-center gap-2">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Monitor your AI campaigns</p>
      </div>
      {dashboardHelp && (
        <HelpIcon 
          content={dashboardHelp} 
          size="sm" 
          variant="both" 
          position="bottom"
        />
      )}
    </div>
  );
};
```

### Card Title with Help Icon

```tsx
const StatsCard = () => {
  const assistantsHelp = getHelpContent('assistants_overview');
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Total Assistants
          {assistantsHelp && (
            <HelpIcon 
              content={assistantsHelp} 
              size="sm" 
              variant="tooltip" 
              position="top"
            />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">12</div>
      </CardContent>
    </Card>
  );
};
```

### Section with Help Modal

```tsx
const IntegrationsSection = () => {
  const help = useHelp();
  const integrationsHelp = getHelpContent('integrations_overview');
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Integrations
          {integrationsHelp && (
            <HelpIcon 
              content={integrationsHelp} 
              size="sm" 
              variant="both" 
              position="right"
            />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={() => help.openHelpModal('integrations_overview')}>
          View Integration Guide
        </Button>
      </CardContent>
    </Card>
  );
};
```

## 🎨 Styling and Customization

### Custom Help Icon Styling

```tsx
<HelpIcon 
  content={helpContent}
  className="text-blue-500 hover:text-blue-600"
  size="lg"
/>
```

### Custom Tooltip Content

The tooltip automatically displays the help content title and description. For custom tooltips, you can create your own component:

```tsx
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const CustomHelpIcon = ({ content }) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost" size="sm">
        <HelpCircle className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      <div className="max-w-xs">
        <h4 className="font-medium">{content.title}</h4>
        <p className="text-sm">{content.description}</p>
      </div>
    </TooltipContent>
  </Tooltip>
);
```

## 📋 Available Help Content Keys

The following help content is available:

### Core Features
- `dashboard_overview` - Dashboard overview and navigation
- `assistants_overview` - AI assistants and automation
- `integrations_overview` - Third-party integrations
- `analytics_overview` - Analytics and reporting
- `settings_overview` - Account and workspace settings

### Industry Modules
- `industries_overview` - Industry-specific modules
- `real_estate_module` - Real estate automation
- `education_module` - Education management

### Integrations
- `email_integrations` - Email service integrations
- `crm_integrations` - CRM system integrations

### Assistants
- `voice_assistants` - Voice AI assistants
- `chat_assistants` - Chat bot assistants

### Settings
- `branding_settings` - Branding and customization
- `telephony_settings` - Voice and telephony setup
- `payment_settings` - Payment and billing configuration

### Support
- `support_overview` - Help and support resources
- `billing_overview` - Billing and usage management
- `api_overview` - API and developer tools

## 🚀 Best Practices

### 1. Consistent Placement
- Place help icons next to titles or labels
- Use consistent sizing (`sm` for most cases)
- Position tooltips to avoid overlapping content

### 2. Appropriate Variants
- Use `tooltip` for quick information
- Use `modal` for detailed explanations
- Use `both` for comprehensive help

### 3. Helpful Content
- Write clear, concise descriptions
- Include practical examples
- Provide relevant links and resources
- Use related topics for navigation

### 4. Performance
- Load help content on demand
- Cache frequently accessed content
- Use the `useHelp` hook for state management

## 🔍 Search and Navigation

The help system includes built-in search functionality:

```tsx
const help = useHelp();
const searchResults = help.searchHelp('assistant');

// Search results include content matching:
// - Title
// - Description  
// - Details
// - Related topics
```

## 📱 Mobile Responsiveness

All help components are mobile-responsive:
- Tooltips adapt to screen size
- Modals are scrollable on mobile
- Touch-friendly interaction areas
- Responsive typography and spacing

## 🧪 Testing

Test help integration with:

```tsx
// Test help icon rendering
expect(screen.getByRole('button')).toBeInTheDocument();

// Test tooltip content
fireEvent.mouseEnter(screen.getByRole('button'));
expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();

// Test modal opening
fireEvent.click(screen.getByRole('button'));
expect(screen.getByText('Help & Documentation')).toBeInTheDocument();
```

## 🔄 Updates and Maintenance

To add new help content:

1. Add content to `@/lib/help-content.ts`
2. Update this documentation
3. Test the new help content
4. Update related components if needed

## 📞 Support

For questions about the help system:
- Check the example components
- Review the help content structure
- Test with the `HelpIntegrationExample` component
- Contact the development team
