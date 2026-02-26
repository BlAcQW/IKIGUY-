import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render as rtlRender, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/auth', () => ({
  logout: vi.fn(),
  isAuthenticated: vi.fn(),
  getCurrentUser: vi.fn(),
}));

// Mock all page components to avoid deep dependency chains
vi.mock('@/pages/Login', () => ({ LoginPage: () => <div>Login Page</div> }));
vi.mock('@/pages/Register', () => ({ RegisterPage: () => <div>Register Page</div> }));
vi.mock('@/pages/Dashboard', () => ({ DashboardPage: () => <div>Dashboard Page</div> }));
vi.mock('@/pages/assistants', () => ({ AssistantsPage: () => <div>Assistants Page</div> }));
vi.mock('@/pages/Calls', () => ({ CallsPage: () => <div>Calls Page</div> }));
vi.mock('@/pages/PhoneNumbers', () => ({ PhoneNumbersPage: () => <div>Phone Numbers Page</div> }));
vi.mock('@/pages/Settings', () => ({ SettingsPage: () => <div>Settings Page</div> }));
vi.mock('@/pages/WebCall', () => ({ WebCallPage: () => <div>WebCall Page</div> }));
vi.mock('@/pages/Tools', () => ({ ToolsPage: () => <div>Tools Page</div> }));
vi.mock('@/pages/Squads', () => ({ SquadsPage: () => <div>Squads Page</div> }));
vi.mock('@/pages/Campaigns', () => ({ CampaignsPage: () => <div>Campaigns Page</div> }));
vi.mock('@/pages/Webhooks', () => ({ WebhooksPage: () => <div>Webhooks Page</div> }));
vi.mock('@/pages/Analytics', () => ({ AnalyticsPage: () => <div>Analytics Page</div> }));

import { App } from './App';
import { useAuth } from '@/hooks/useAuth';

const mockedUseAuth = vi.mocked(useAuth);

function renderApp(route: string) {
  return rtlRender(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>,
  );
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login page at /login', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: false, refresh: vi.fn() });
    renderApp('/login');
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders register page at /register', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: false, refresh: vi.fn() });
    renderApp('/register');
    expect(screen.getByText('Register Page')).toBeInTheDocument();
  });

  it('redirects to login when not authenticated on protected route', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: false, refresh: vi.fn() });
    renderApp('/');
    // Should redirect to login
    expect(screen.queryByText('Dashboard Page')).not.toBeInTheDocument();
  });

  it('shows loading screen while checking auth', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: true, refresh: vi.fn() });
    renderApp('/');
    expect(screen.getByText(/loading your workspace/i)).toBeInTheDocument();
  });

  it('renders dashboard when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/');
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
  });

  it('redirects to login when visiting /assistants unauthenticated', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: false, refresh: vi.fn() });
    renderApp('/assistants');
    expect(screen.queryByText('Assistants Page')).not.toBeInTheDocument();
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('shows loading screen for ProtectedNoPaddingRoute while checking auth', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: true, refresh: vi.fn() });
    renderApp('/assistants');
    expect(screen.getByText(/loading your workspace/i)).toBeInTheDocument();
  });

  it('renders assistants page when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/assistants');
    expect(screen.getByText('Assistants Page')).toBeInTheDocument();
  });

  it('renders calls page when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/calls');
    expect(screen.getByText('Calls Page')).toBeInTheDocument();
  });

  it('redirects unknown routes to / (then to login when unauthenticated)', () => {
    mockedUseAuth.mockReturnValue({ user: null, loading: false, refresh: vi.fn() });
    renderApp('/nonexistent');
    // Wildcard route navigates to /, which triggers ProtectedRoute -> redirect to login
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders tools page when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/tools');
    expect(screen.getByText('Tools Page')).toBeInTheDocument();
  });

  it('renders squads page when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/squads');
    expect(screen.getByText('Squads Page')).toBeInTheDocument();
  });

  it('renders settings page when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { userId: 'u1', organizationId: 'o1', role: 'OWNER', name: 'Test', email: 'test@test.com', organizationName: 'Org' },
      loading: false,
      refresh: vi.fn(),
    });
    renderApp('/settings');
    expect(screen.getByText('Account settings and configuration')).toBeInTheDocument();
  });
});
