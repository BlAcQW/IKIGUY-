import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Home } from './pages/Home';
import { Events } from './pages/Events';
import { EventDetails } from './pages/EventDetails';
import { EventForm } from './pages/EventForm';
import { Tasks } from './pages/Tasks';
import { Wallet } from './pages/Wallet';
import { Profile } from './pages/Profile';
import VoiceSettings from './pages/VoiceSettings';
import ReportBug from './components/ReportBug';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import PWAUpdateBanner from './components/PWAUpdateBanner';
import { OrganizationProvider } from './contexts/OrganizationContext';

// Admin Pages
import { OrganizationsPage } from './pages/admin/OrganizationsPage';
import { SettingsPage } from './pages/admin/SettingsPage';
import { BillingPage } from './pages/admin/BillingPage';
import { UsersPage } from './pages/admin/UsersPage';

function App() {
  console.log('EventFlow v2.0 - Build:', new Date().toISOString());
  return (
    <OrganizationProvider>
      <BrowserRouter>
      <PWAUpdateBanner />
      <PWAInstallPrompt />
      <ReportBug />
      <Routes>
        {/* All routes are now public and accessible */}

        {/* Default route - redirect to home */}
        <Route path="/" element={<Navigate to="/home" replace />} />

        {/* Public pages (kept for reference) */}
        <Route path="/landing" element={<Landing />} />
        <Route path="/login" element={<Login />} />

        {/* Main application routes - all wrapped in Layout */}
        <Route
          path="/home"
          element={
            <Layout>
              <Home />
            </Layout>
          }
        />
        <Route
          path="/events"
          element={
            <Layout>
              <Events />
            </Layout>
          }
        />
        <Route
          path="/events/new"
          element={
            <Layout>
              <EventForm />
            </Layout>
          }
        />
        <Route
          path="/events/:id/edit"
          element={
            <Layout>
              <EventForm />
            </Layout>
          }
        />
        <Route
          path="/events/:id"
          element={
            <Layout>
              <EventDetails />
            </Layout>
          }
        />
        <Route
          path="/tasks"
          element={
            <Layout>
              <Tasks />
            </Layout>
          }
        />
        <Route
          path="/wallet"
          element={
            <Layout>
              <Wallet />
            </Layout>
          }
        />
        <Route
          path="/profile"
          element={
            <Layout>
              <Profile />
            </Layout>
          }
        />
        <Route
          path="/voice-settings"
          element={
            <Layout>
              <VoiceSettings />
            </Layout>
          }
        />

        {/* Admin Routes */}
        <Route path="/admin/organizations" element={<OrganizationsPage />} />
        <Route path="/admin/settings" element={<SettingsPage />} />
        <Route path="/admin/billing" element={<BillingPage />} />
        <Route path="/admin/users" element={<UsersPage />} />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </BrowserRouter>
    </OrganizationProvider>
  );
}

export default App;
