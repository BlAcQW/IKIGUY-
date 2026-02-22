import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/Login';
import { RegisterPage } from './pages/Register';
import { DashboardPage } from './pages/Dashboard';
import { AssistantsPage } from './pages/assistants';
import { CallsPage } from './pages/Calls';
import { PhoneNumbersPage } from './pages/PhoneNumbers';
import { SettingsPage } from './pages/Settings';
import { WebCallPage } from './pages/WebCall';
import { ToolsPage } from './pages/Tools';
import { SquadsPage } from './pages/Squads';
import { CampaignsPage } from './pages/Campaigns';
import { WebhooksPage } from './pages/Webhooks';
import { AnalyticsPage } from './pages/Analytics';
import { useAuth } from './hooks/useAuth';

function LoadingScreen() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background relative overflow-hidden">
      {/* Ambient background */}
      <div className="absolute inset-0 gradient-mesh" />

      {/* Logo + loader */}
      <div className="relative z-10 flex flex-col items-center gap-6">
        <div className="relative">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-primary">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" />
            </svg>
          </div>
          <div className="absolute inset-0 rounded-2xl animate-pulse-glow" />
        </div>
        <div className="flex flex-col items-center gap-2">
          <span className="text-lg font-display font-bold tracking-tight text-foreground">LOAD</span>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <span className="text-xs text-muted-foreground">Loading your workspace</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function ProtectedNoPaddingRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout noPadding>{children}</Layout>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assistants"
        element={
          <ProtectedNoPaddingRoute>
            <AssistantsPage />
          </ProtectedNoPaddingRoute>
        }
      />
      <Route
        path="/assistants/:id"
        element={
          <ProtectedNoPaddingRoute>
            <AssistantsPage />
          </ProtectedNoPaddingRoute>
        }
      />
      <Route
        path="/calls"
        element={
          <ProtectedRoute>
            <CallsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/web-call"
        element={
          <ProtectedRoute>
            <WebCallPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/phone-numbers"
        element={
          <ProtectedRoute>
            <PhoneNumbersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tools"
        element={
          <ProtectedRoute>
            <ToolsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/squads"
        element={
          <ProtectedRoute>
            <SquadsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/campaigns"
        element={
          <ProtectedRoute>
            <CampaignsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/webhooks"
        element={
          <ProtectedRoute>
            <WebhooksPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <AnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
