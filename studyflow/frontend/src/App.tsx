/**
 * Main Application Component
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth-context';
import { OrganizationProvider } from './lib/organization-context';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import MaterialUpload from './pages/MaterialUpload';
import MaterialLibrary from './pages/MaterialLibrary';
import MaterialDetails from './pages/MaterialDetails';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import VoiceSettings from './pages/VoiceSettings';
import Wallet from './pages/Wallet';
import LandingPage from './LandingPage'; // Original landing page
import ReportBug from './components/ReportBug';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import PWAUpdateBanner from './components/PWAUpdateBanner';

// Exercise Pages
import ExercisesList from './pages/ExercisesList';
import TakeExercise from './pages/TakeExercise';
import ExerciseResults from './pages/ExerciseResults';
import ExerciseHistory from './pages/ExerciseHistory';

// Admin Pages
import OrganizationsPage from './pages/admin/OrganizationsPage';
import AdminSettingsPage from './pages/admin/SettingsPage';
import BillingPage from './pages/admin/BillingPage';
import UsersPage from './pages/admin/UsersPage';

function App() {
  return (
    <AuthProvider>
      <OrganizationProvider>
        <Router>
          <PWAUpdateBanner />
          <PWAInstallPrompt />
          <ReportBug />
          <Routes>
          {/* Public Routes */}
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />

          {/* Protected Routes */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />

          {/* Material Management Routes */}
          <Route path="/materials" element={<ProtectedRoute><MaterialLibrary /></ProtectedRoute>} />
          <Route path="/materials/upload" element={<ProtectedRoute><MaterialUpload /></ProtectedRoute>} />
          <Route path="/materials/:id" element={<ProtectedRoute><MaterialDetails /></ProtectedRoute>} />

          {/* Exercise Routes */}
          <Route path="/exercises" element={<ProtectedRoute><ExercisesList /></ProtectedRoute>} />
          <Route path="/exercises/:exerciseId/take" element={<ProtectedRoute><TakeExercise /></ProtectedRoute>} />
          <Route path="/exercises/results/:submissionId" element={<ProtectedRoute><ExerciseResults /></ProtectedRoute>} />
          <Route path="/exercises/history" element={<ProtectedRoute><ExerciseHistory /></ProtectedRoute>} />

          {/* User Pages */}
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/voice-settings" element={<ProtectedRoute><VoiceSettings /></ProtectedRoute>} />
          <Route path="/wallet" element={<ProtectedRoute><Wallet /></ProtectedRoute>} />

          {/* Admin Routes */}
          <Route path="/admin/organizations" element={<ProtectedRoute><OrganizationsPage /></ProtectedRoute>} />
          <Route path="/admin/settings" element={<ProtectedRoute><AdminSettingsPage /></ProtectedRoute>} />
          <Route path="/admin/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute><UsersPage /></ProtectedRoute>} />

          {/* Redirect unknown routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Global footer */}
        <footer className="border-t border-gray-200 bg-white mt-4">
          <div className="max-w-5xl mx-auto px-4 py-3 text-right text-xs text-gray-500">
            Powered by{' '}
            <a
              href="https://ailabsafrica.com"
              target="_blank"
              rel="noreferrer"
              className="text-emerald-600 hover:text-emerald-500 underline underline-offset-2"
            >
              AI Labs
            </a>
          </div>
        </footer>
      </Router>
      </OrganizationProvider>
    </AuthProvider>
  );
}

export default App;
