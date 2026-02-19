# Shared Admin Components

Comprehensive, reusable admin interface components for all KasaAI applications.

## 📦 Components

### 1. AdminLayout
Main layout component with sidebar navigation, organization selector, and user menu.

**Features:**
- Responsive sidebar navigation
- Organization switcher dropdown
- User profile menu
- Search functionality
- Notification bell
- Customizable navigation items

### 2. OrganizationManagement
Complete organization management interface.

**Features:**
- List all user's organizations
- Create new organizations
- View organization details
- Manage organization members
- Send member invitations
- View invitation status
- Role-based access control (owner, admin, user)

### 3. OrganizationSettings
Organization configuration and preferences.

**Features:**
- **General Settings**: Name, description, contact info, address
- **Branding**: Logo upload, color customization, brand preview
- **Integrations**: API keys, webhooks, notifications
- **Security**: 2FA, session timeout, danger zone (delete org)

### 4. OrganizationBilling
Billing, invoicing, and usage tracking.

**Features:**
- Wallet balance display
- Add funds functionality
- Transaction history
- Invoice management
- Usage analytics by service
- Export transactions to CSV
- Current billing period overview

### 5. UserManagement
Manage users within an organization.

**Features:**
- List all organization members
- Search and filter users
- Edit user roles (admin/user)
- Remove users from organization
- View user statistics (total, active, by role)
- User status indicators

## 🚀 Installation & Usage

### Step 1: Copy Components

```bash
# The components are already in:
/opt/kasaai/apps/shared/frontend/admin-components/
```

### Step 2: Import in Your App

```typescript
// Example: StudyFlow Admin Dashboard
import {
  AdminLayout,
  OrganizationManagement,
  OrganizationSettings,
  OrganizationBilling,
  UserManagement
} from '../../../shared/frontend/admin-components';

// Example usage in a page component
export default function AdminDashboard() {
  return (
    <AdminLayout
      currentPage="/admin"
      user={{
        name: "John Doe",
        email: "john@example.com"
      }}
      organizations={[
        {
          id: "org-1",
          name: "my-org",
          display_name: "My Organization",
          role: "admin"
        }
      ]}
      currentOrganization={currentOrg}
      onOrganizationChange={(orgId) => setCurrentOrgId(orgId)}
      appName="StudyFlow"
    >
      {/* Your page content */}
      <h1>Welcome to Admin</h1>
    </AdminLayout>
  );
}
```

### Step 3: Create Admin Routes

```typescript
// App.tsx or Router configuration
import { OrganizationManagement } from '../../../shared/frontend/admin-components';

function App() {
  return (
    <Routes>
      <Route path="/admin/organizations" element={
        <AdminLayout currentPage="/admin/organizations" {...props}>
          <OrganizationManagement
            apiBaseUrl="https://api.example.com"
            onError={(msg) => showError(msg)}
          />
        </AdminLayout>
      } />

      <Route path="/admin/settings" element={
        <AdminLayout currentPage="/admin/settings" {...props}>
          <OrganizationSettings
            organizationId={currentOrgId}
            apiBaseUrl="https://api.example.com"
            onError={(msg) => showError(msg)}
            onSuccess={(msg) => showSuccess(msg)}
          />
        </AdminLayout>
      } />

      <Route path="/admin/billing" element={
        <AdminLayout currentPage="/admin/billing" {...props}>
          <OrganizationBilling
            organizationId={currentOrgId}
            apiBaseUrl="https://api.example.com"
            onError={(msg) => showError(msg)}
          />
        </AdminLayout>
      } />

      <Route path="/admin/users" element={
        <AdminLayout currentPage="/admin/users" {...props}>
          <UserManagement
            organizationId={currentOrgId}
            apiBaseUrl="https://api.example.com"
            onError={(msg) => showError(msg)}
            onSuccess={(msg) => showSuccess(msg)}
          />
        </AdminLayout>
      } />
    </Routes>
  );
}
```

## 🎨 Customization

### Add Custom Navigation Items

```typescript
<AdminLayout
  customNavItems={[
    {
      icon: BookIcon,
      label: 'Books',
      path: '/admin/books'
    },
    {
      icon: VideoIcon,
      label: 'Videos',
      path: '/admin/videos'
    }
  ]}
  {...otherProps}
>
  {children}
</AdminLayout>
```

### Customize App Name

```typescript
<AdminLayout
  appName="StudyFlow" // or "InkWave", "ChurchFlow", "EventFlow"
  {...otherProps}
>
  {children}
</AdminLayout>
```

## 🔌 API Integration

All components expect your backend to have the following endpoints:

### Organizations
- `GET /api/v1/organizations` - List user's organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations/:id` - Get organization details
- `PATCH /api/v1/organizations/:id` - Update organization
- `DELETE /api/v1/organizations/:id` - Delete organization
- `GET /api/v1/organizations/:id/members` - List members
- `POST /api/v1/organizations/:id/invitations` - Send invitation
- `GET /api/v1/organizations/:id/invitations` - List invitations

### Billing
- `GET /api/v1/organizations/:id/wallet` - Get wallet balance
- `POST /api/v1/organizations/:id/wallet/add-funds` - Add funds
- `GET /api/v1/organizations/:id/transactions` - List transactions
- `GET /api/v1/organizations/:id/usage` - Get usage stats

### Users
- `GET /api/v1/organizations/:id/members` - List members
- `PATCH /api/v1/organizations/:id/members/:userId` - Update member role
- `DELETE /api/v1/organizations/:id/members/:userId` - Remove member

**Note:** These endpoints are already implemented in the backend organization routes we created earlier!

## 📱 Responsive Design

All components are fully responsive and work on:
- ✅ Desktop (1920px+)
- ✅ Laptop (1024px - 1920px)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

## 🎨 Theming

Components use Tailwind CSS classes. To customize colors:

1. **Primary Color**: Blue-600 → Change to your brand color
2. **Success**: Green-600
3. **Warning**: Yellow-600
4. **Error**: Red-600

Find and replace color classes in the component files.

## 📖 Component Props

### AdminLayout Props
```typescript
interface AdminLayoutProps {
  children: React.ReactNode;
  currentPage: string;                    // Current active page path
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  organizations?: Organization[];
  currentOrganization?: Organization;
  onOrganizationChange?: (orgId: string) => void;
  appName?: string;                       // Default: "KasaAI"
  customNavItems?: Array<{
    icon: any;                            // Lucide icon component
    label: string;
    path: string;
  }>;
}
```

### OrganizationManagement Props
```typescript
interface OrganizationManagementProps {
  apiBaseUrl: string;                     // e.g., "https://api.example.com"
  onError?: (error: string) => void;
}
```

### OrganizationSettings Props
```typescript
interface OrganizationSettingsProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
  onSuccess?: (message: string) => void;
}
```

### OrganizationBilling Props
```typescript
interface OrganizationBillingProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
}
```

### UserManagement Props
```typescript
interface UserManagementProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
  onSuccess?: (message: string) => void;
}
```

## 🔐 Authentication

Components expect a JWT token in localStorage:

```typescript
localStorage.getItem('access_token')
```

The token is automatically sent with all API requests in the `Authorization` header:

```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'X-Organization-ID': organizationId  // For organization-scoped requests
}
```

## ✅ Features Included

- ✅ Organization CRUD operations
- ✅ Member management with role-based access
- ✅ Invitation system
- ✅ Wallet & billing tracking
- ✅ Transaction history
- ✅ Usage analytics
- ✅ User management
- ✅ Settings & preferences
- ✅ Branding customization
- ✅ Security settings
- ✅ Responsive design
- ✅ Search & filtering
- ✅ Loading states
- ✅ Error handling
- ✅ Success notifications

## 📚 Examples

### Example 1: StudyFlow Admin Page

```typescript
// /opt/kasaai/apps/studyflow/frontend/src/pages/AdminOrganizations.tsx
import { AdminLayout, OrganizationManagement } from '../../../../shared/frontend/admin-components';

export default function AdminOrganizations() {
  return (
    <AdminLayout
      currentPage="/admin/organizations"
      appName="StudyFlow"
      user={currentUser}
      organizations={userOrganizations}
      currentOrganization={selectedOrg}
      onOrganizationChange={handleOrgChange}
    >
      <OrganizationManagement
        apiBaseUrl={process.env.REACT_APP_API_URL}
        onError={(msg) => toast.error(msg)}
      />
    </AdminLayout>
  );
}
```

### Example 2: InkWave Admin Settings

```typescript
// /opt/kasaai/apps/inkwave/frontend/src/pages/AdminSettingsPage.tsx
import { AdminLayout, OrganizationSettings } from '../../../../shared/frontend/admin-components';

export default function AdminSettingsPage() {
  return (
    <AdminLayout currentPage="/admin/settings" appName="InkWave" {...props}>
      <OrganizationSettings
        organizationId={currentOrgId}
        apiBaseUrl={import.meta.env.VITE_API_URL}
        onError={(msg) => showToast(msg, 'error')}
        onSuccess={(msg) => showToast(msg, 'success')}
      />
    </AdminLayout>
  );
}
```

## 🛠 Development

### Adding New Features

1. Edit the component file in `/opt/kasaai/apps/shared/frontend/admin-components/`
2. The changes will be available to all apps immediately (shared folder)
3. Test in one app, deploy to all apps

### Styling Guidelines

- Use Tailwind CSS utility classes
- Follow existing color scheme (blue primary, gradient accents)
- Maintain responsive breakpoints: `md:`, `lg:` prefixes
- Use Lucide React icons for consistency

## 🚨 Troubleshooting

### Components Not Found
```bash
# Verify the shared folder exists:
ls -la /opt/kasaai/apps/shared/frontend/admin-components/

# Check import path (adjust based on your app structure):
import { AdminLayout } from '../../../shared/frontend/admin-components';
```

### TypeScript Errors
```bash
# Ensure lucide-react is installed:
npm install lucide-react

# Ensure React types are installed:
npm install --save-dev @types/react @types/react-dom
```

### API Errors
- Verify `apiBaseUrl` prop is correct
- Check network tab for failed requests
- Ensure backend endpoints are implemented
- Verify JWT token is in localStorage
- Check CORS configuration on backend

## 📄 License

These components are part of the KasaAI platform and are shared across all KasaAI applications.

---

**Built with ❤️ for the KasaAI Platform**

For support or questions, contact the development team.
