import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { OrganizationProvider } from './contexts/OrganizationContext'
import Login from './pages/Login'
import Layout from './components/Layout'
import ReportBug from './components/ReportBug'
import PWAInstallPrompt from './components/PWAInstallPrompt'
import PWAUpdateBanner from './components/PWAUpdateBanner'

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const CRMPage = lazy(() => import('./pages/CRMPage'))
const HRPage = lazy(() => import('./pages/HRPage'))
const FinancePage = lazy(() => import('./pages/FinancePage'))
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'))
const BIPage = lazy(() => import('./pages/BIPage'))
const IntegrationPage = lazy(() => import('./pages/IntegrationPage'))
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'))
const PartnershipsPage = lazy(() => import('./pages/PartnershipsPage'))
const TasksPage = lazy(() => import('./pages/TasksPage'))

// Loading fallback component
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <OrganizationProvider>
          <PWAUpdateBanner />
          <PWAInstallPrompt />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Suspense fallback={<PageLoader />}>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/admin" element={<AdminPage />} />
                        <Route path="/crm" element={<CRMPage />} />
                        <Route path="/tasks" element={<TasksPage />} />
                        <Route path="/hr" element={<HRPage />} />
                        <Route path="/onboarding" element={<OnboardingPage />} />
                        <Route path="/finance" element={<FinancePage />} />
                        <Route path="/projects" element={<ProjectsPage />} />
                        <Route path="/partnerships" element={<PartnershipsPage />} />
                        <Route path="/bi" element={<BIPage />} />
                        <Route path="/integrations" element={<IntegrationPage />} />
                      </Routes>
                    </Suspense>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
          <ReportBug />
        </OrganizationProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
