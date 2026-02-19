import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DashboardOverview from './pages/DashboardOverview'
import Landing from './pages/Landing'
import ConferencesList from './pages/ConferencesList'
import ConferenceRegistration from './pages/ConferenceRegistration'
import ConferenceInfo from './pages/ConferenceInfo'
import BusManagement from './pages/BusManagement'
import BusBooking from './pages/BusBooking'
import ConferenceManagement from './pages/ConferenceManagement'
import ConferenceDetail from './pages/ConferenceDetail'
import QRScanner from './pages/QRScanner'
import SelfCheckIn from './pages/SelfCheckIn'
import Members from './pages/Members'
import RegisteredMembers from './pages/RegisteredMembers'
import RegistrationDetail from './pages/RegistrationDetail'
import SessionDetail from './pages/SessionDetail'
import BusCheckIn from './pages/BusCheckIn'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/DashboardLayout'
import BottomNav from './components/BottomNav'
import OfflineIndicator from './components/OfflineIndicator'
import PWAUpdateBanner from './components/PWAUpdateBanner'
import PWAInstallPrompt from './components/PWAInstallPrompt'
import WelcomeNotification from './components/WelcomeNotification'
import VoiceLibrary from './pages/VoiceLibrary'
import TalkToPapa from './pages/TalkToPapa'
import SMSCampaigns from './pages/SMSCampaigns'
// import WhatsAppCampaigns from './pages/WhatsAppCampaigns' // Temporarily disabled - missing dependencies
// import WhatsAppCampaignForm from './pages/WhatsAppCampaignForm' // Temporarily disabled - missing dependencies
import ConferenceAnalytics from './pages/ConferenceAnalytics'
import { OrganizationProvider } from './contexts/OrganizationContext'

// Admin Pages
import OrganizationsPage from './pages/admin/OrganizationsPage'
import AdminSettingsPage from './pages/admin/SettingsPage'
import BillingPage from './pages/admin/BillingPage'
import UsersPage from './pages/admin/UsersPage'
import MembersDashboardPage from './pages/admin/MembersDashboardPage'
import PlatformAdminPage from './pages/admin/PlatformAdminPage'
import AnalyticsPage from './pages/admin/AnalyticsPage'
import IntegrationsPage from './pages/admin/IntegrationsPage'
import AutomationPage from './pages/admin/AutomationPage'
import GroupManagement from './pages/admin/GroupManagement'
import SubgroupManagement from './pages/admin/SubgroupManagement'
import FirstTimerDashboard from './pages/admin/FirstTimerDashboard'
import AnnouncementManagement from './pages/admin/AnnouncementManagement'
import MemberProfileView from './pages/admin/MemberProfileView'

// Giving Pages
import GivingPage from './pages/GivingPage'

// Member Portal Pages
import MemberPortalPage from './pages/MemberPortalPage'

// Service Management Pages
import ServiceManagement from './pages/ServiceManagement'
import ServiceDetail from './pages/ServiceDetail'
import ServiceCheckIn from './pages/ServiceCheckIn'
import AttendanceAnalytics from './pages/AttendanceAnalytics'

// Onboarding Pages
import SignupPage from './pages/SignupPage'

// Visitor Tracking Pages
import VisitorList from './pages/VisitorList'
import VisitorCapture from './pages/VisitorCapture'
import VisitorDetail from './pages/VisitorDetail'
import VisitorAnalytics from './pages/VisitorAnalytics'
import CellGroupManager from './pages/CellGroupManager'

// Page transition variants
const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
}

const pageTransition = {
  type: 'tween',
  ease: 'easeInOut',
  duration: 0.2,
}

// Animated page wrapper
function AnimatedPage({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial="initial"
      animate="animate"
      exit="exit"
      variants={pageVariants}
      transition={pageTransition}
      className="pb-20 md:pb-0"
    >
      {children}
    </motion.div>
  )
}

// Animated routes wrapper
function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public Routes - Only landing, login, register, impact, signup, self-checkin, and giving are public */}
        <Route path="/" element={<AnimatedPage><Landing /></AnimatedPage>} />
        <Route path="/landing" element={<AnimatedPage><Landing /></AnimatedPage>} />
        <Route path="/impact" element={<AnimatedPage><Landing /></AnimatedPage>} />
        <Route path="/login" element={<AnimatedPage><Login /></AnimatedPage>} />
        <Route path="/signup" element={<AnimatedPage><SignupPage /></AnimatedPage>} />
        <Route path="/register" element={<AnimatedPage><ConferenceRegistration /></AnimatedPage>} />
        <Route path="/register/:conferenceId" element={<AnimatedPage><ConferenceRegistration /></AnimatedPage>} />
        <Route path="/self-checkin" element={<AnimatedPage><SelfCheckIn /></AnimatedPage>} />
        <Route path="/giving" element={<AnimatedPage><DashboardLayout><GivingPage /></DashboardLayout></AnimatedPage>} />

        {/* Public-Facing Routes */}
        <Route path="/members" element={<AnimatedPage><Members /></AnimatedPage>} />
        <Route path="/events" element={<ProtectedRoute><AnimatedPage><ConferencesList /></AnimatedPage></ProtectedRoute>} />
        {/* Legacy public conference info route (kept for compatibility) */}
        <Route path="/conference/:conferenceId" element={<ProtectedRoute><AnimatedPage><ConferenceInfo /></AnimatedPage></ProtectedRoute>} />
        <Route path="/bus-booking" element={<AnimatedPage><BusBooking /></AnimatedPage>} />
        <Route path="/talk-to-papa" element={<ProtectedRoute><AnimatedPage><TalkToPapa /></AnimatedPage></ProtectedRoute>} />

        {/* Protected Routes with Dashboard Layout */}
        <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout><DashboardOverview /></DashboardLayout></ProtectedRoute>} />
        <Route path="/conferences" element={<ProtectedRoute><DashboardLayout><ConferenceManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/conferences/:conferenceId" element={<ProtectedRoute><DashboardLayout><ConferenceDetail /></DashboardLayout></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><DashboardLayout><ConferenceAnalytics /></DashboardLayout></ProtectedRoute>} />
        <Route path="/buses" element={<ProtectedRoute><DashboardLayout><BusManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/bus-checkin" element={<ProtectedRoute><DashboardLayout><BusCheckIn /></DashboardLayout></ProtectedRoute>} />
        <Route path="/check-in" element={<ProtectedRoute><DashboardLayout><QRScanner /></DashboardLayout></ProtectedRoute>} />
        <Route path="/sms-campaigns" element={<ProtectedRoute><DashboardLayout><SMSCampaigns /></DashboardLayout></ProtectedRoute>} />
        {/* <Route path="/whatsapp-campaigns" element={<ProtectedRoute><DashboardLayout><WhatsAppCampaigns /></DashboardLayout></ProtectedRoute>} /> */}
        {/* <Route path="/whatsapp-campaigns/create" element={<ProtectedRoute><DashboardLayout><WhatsAppCampaignForm /></DashboardLayout></ProtectedRoute>} /> */}
        <Route path="/registered-users" element={<ProtectedRoute><DashboardLayout><RegisteredMembers /></DashboardLayout></ProtectedRoute>} />
        <Route path="/registered-users/:registrationId" element={<ProtectedRoute><RegistrationDetail /></ProtectedRoute>} />
        <Route path="/sessions/:sessionId" element={<ProtectedRoute><SessionDetail /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><DashboardLayout><div className="bg-white rounded-xl shadow-sm border p-6"><h3 className="text-lg font-semibold mb-4">Send Notifications</h3><p className="text-gray-500">Notification interface coming soon...</p></div></DashboardLayout></ProtectedRoute>} />

        {/* Visitor Tracking Routes */}
        <Route path="/visitors" element={<ProtectedRoute><DashboardLayout><VisitorList /></DashboardLayout></ProtectedRoute>} />
        <Route path="/visitors/capture" element={<ProtectedRoute><DashboardLayout><VisitorCapture /></DashboardLayout></ProtectedRoute>} />
        <Route path="/visitors/analytics" element={<ProtectedRoute><DashboardLayout><VisitorAnalytics /></DashboardLayout></ProtectedRoute>} />
        <Route path="/visitors/:id" element={<ProtectedRoute><DashboardLayout><VisitorDetail /></DashboardLayout></ProtectedRoute>} />
        <Route path="/cell-groups" element={<ProtectedRoute><DashboardLayout><CellGroupManager /></DashboardLayout></ProtectedRoute>} />

        {/* Admin Routes with Dashboard Layout */}
        <Route path="/admin/conferences" element={<ProtectedRoute><DashboardLayout><ConferenceManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/services" element={<ProtectedRoute><DashboardLayout><ServiceManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/services/:serviceId" element={<ProtectedRoute><DashboardLayout><ServiceDetail /></DashboardLayout></ProtectedRoute>} />
        <Route path="/services/check-in" element={<ProtectedRoute><DashboardLayout><ServiceCheckIn /></DashboardLayout></ProtectedRoute>} />
        <Route path="/services/analytics" element={<ProtectedRoute><DashboardLayout><AttendanceAnalytics /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/analytics" element={<ProtectedRoute><DashboardLayout><AnalyticsPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/integrations" element={<ProtectedRoute><DashboardLayout><IntegrationsPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/automation" element={<ProtectedRoute><DashboardLayout><AutomationPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/portal" element={<ProtectedRoute><DashboardLayout><MemberPortalPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/organizations" element={<ProtectedRoute><DashboardLayout><OrganizationsPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/settings" element={<ProtectedRoute><DashboardLayout><AdminSettingsPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/billing" element={<ProtectedRoute><DashboardLayout><BillingPage /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute><DashboardLayout><UsersPage /></DashboardLayout></ProtectedRoute>} />
        {/* Members dashboard moved to Member Portal Admin tab - route removed to avoid duplication */}
        <Route path="/admin/voice-library" element={<ProtectedRoute><DashboardLayout><VoiceLibrary /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/sms-campaigns" element={<ProtectedRoute><DashboardLayout><SMSCampaigns /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/groups" element={<ProtectedRoute><DashboardLayout><GroupManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/groups/:groupId/subgroups" element={<ProtectedRoute><DashboardLayout><SubgroupManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/first-timers" element={<ProtectedRoute><DashboardLayout><FirstTimerDashboard /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/announcements" element={<ProtectedRoute><DashboardLayout><AnnouncementManagement /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/members/:memberId" element={<ProtectedRoute><DashboardLayout><MemberProfileView /></DashboardLayout></ProtectedRoute>} />
        <Route path="/admin/platform" element={<ProtectedRoute><PlatformAdminPage /></ProtectedRoute>} />
        {/* <Route path="/admin/whatsapp-campaigns" element={<ProtectedRoute><DashboardLayout><WhatsAppCampaigns /></DashboardLayout></ProtectedRoute>} /> */}

        {/* Redirect all unknown routes to landing page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  )
}

function App() {
  return (
    <OrganizationProvider>
      <BrowserRouter>
        <OfflineIndicator />
        <PWAUpdateBanner />
        <PWAInstallPrompt />
        <WelcomeNotification />
        <BottomNav />
        <AnimatedRoutes />

        {/* Global footer (desktop) */}
        <footer className="hidden md:block border-t border-gray-800 bg-gray-950/90">
          <div className="max-w-6xl mx-auto px-4 py-3 text-right text-xs text-gray-500">
            Powered by{' '}
            <a
              href="https://ailabsafrica.com"
              target="_blank"
              rel="noreferrer"
              className="text-purple-400 hover:text-purple-300 underline underline-offset-2"
            >
              AI Labs
            </a>
          </div>
        </footer>
      </BrowserRouter>
    </OrganizationProvider>
  )
}

export default App
