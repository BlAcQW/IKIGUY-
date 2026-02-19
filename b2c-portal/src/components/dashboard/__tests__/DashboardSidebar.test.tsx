/**
 * Unit tests for DashboardSidebar component with role-based access control
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { DashboardSidebar } from '../DashboardSidebar';
import * as MongoAuthContext from '@/components/auth/MongoAuthContext';

// Mock the MongoAuthContext
const mockUseMongoAuth = vi.spyOn(MongoAuthContext, 'useMongoAuth');

// Mock user data
const mockRegularUser = {
  id: 'user-1',
  email: 'regular@example.com',
  first_name: 'Regular',
  last_name: 'User',
  display_name: 'Regular User',
  is_active: true,
  is_verified: true,
  is_universal_admin: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockUniversalAdminUser = {
  id: 'user-2',
  email: 'alfred.anyan@gmail.com',
  first_name: 'Alfred',
  last_name: 'Anyan',
  display_name: 'Alfred Anyan',
  is_active: true,
  is_verified: true,
  is_universal_admin: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockAuthContextValue = {
  user: null,
  organization: null,
  isLoading: false,
  isAuthenticated: false,
  signUp: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
  refreshSession: vi.fn(),
  getTenantId: vi.fn(),
  getAccessToken: vi.fn(),
};

describe('DashboardSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Regular User', () => {
    beforeEach(() => {
      mockUseMongoAuth.mockReturnValue({
        ...mockAuthContextValue,
        user: mockRegularUser,
        isAuthenticated: true,
      });
    });

    it('should render sidebar for regular user', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      expect(screen.getByText('KasaAI')).toBeInTheDocument();
    });

    it('should show non-admin menu items for regular user', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      // These should be visible to regular users
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Call Logs')).toBeInTheDocument();
      expect(screen.getByText('Audiences')).toBeInTheDocument();
      expect(screen.getByText('Automations')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
      expect(screen.getByText('Phone Numbers')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Help')).toBeInTheDocument();
    });

    it('should NOT show universal_admin-only menu items for regular user', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      // These should NOT be visible to regular users
      expect(screen.queryByText('Voice Agent')).not.toBeInTheDocument();
      expect(screen.queryByText('Quick Deploy')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Library')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Lab')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Lab Enhanced')).not.toBeInTheDocument();
      expect(screen.queryByText('Billing')).not.toBeInTheDocument();
      expect(screen.queryByText('Integrations')).not.toBeInTheDocument();
    });
  });

  describe('Universal Admin User', () => {
    beforeEach(() => {
      mockUseMongoAuth.mockReturnValue({
        ...mockAuthContextValue,
        user: mockUniversalAdminUser,
        isAuthenticated: true,
      });
    });

    it('should render sidebar for universal admin', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      expect(screen.getByText('KasaAI')).toBeInTheDocument();
    });

    it('should show all menu items for universal admin', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      // All items should be visible to universal admins
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Voice Agent')).toBeInTheDocument();
      expect(screen.getByText('Quick Deploy')).toBeInTheDocument();
      expect(screen.getByText('Call Logs')).toBeInTheDocument();
      expect(screen.getByText('Audiences')).toBeInTheDocument();
      expect(screen.getByText('Automations')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
      expect(screen.getByText('Phone Numbers')).toBeInTheDocument();
      expect(screen.getByText('Voice Library')).toBeInTheDocument();
      expect(screen.getByText('Voice Lab')).toBeInTheDocument();
      expect(screen.getByText('Voice Lab Enhanced')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Billing')).toBeInTheDocument();
      expect(screen.getByText('Integrations')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Help')).toBeInTheDocument();
    });
  });

  describe('Unauthenticated User', () => {
    beforeEach(() => {
      mockUseMongoAuth.mockReturnValue({
        ...mockAuthContextValue,
        user: null,
        isAuthenticated: false,
      });
    });

    it('should render sidebar without user', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      expect(screen.getByText('KasaAI')).toBeInTheDocument();
    });

    it('should NOT show universal_admin-only items when no user', () => {
      render(
        <BrowserRouter>
          <DashboardSidebar />
        </BrowserRouter>
      );

      // These should NOT be visible without authentication
      expect(screen.queryByText('Voice Agent')).not.toBeInTheDocument();
      expect(screen.queryByText('Quick Deploy')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Library')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Lab')).not.toBeInTheDocument();
      expect(screen.queryByText('Voice Lab Enhanced')).not.toBeInTheDocument();
      expect(screen.queryByText('Billing')).not.toBeInTheDocument();
      expect(screen.queryByText('Integrations')).not.toBeInTheDocument();
    });
  });
});
