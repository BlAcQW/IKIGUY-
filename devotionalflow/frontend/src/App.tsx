import { Suspense, lazy } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AdminRoute } from "@/components/auth/AdminRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { PWAUpdateNotification } from "@/components/pwa/PWAUpdateNotification";
import { OfflineIndicator } from "@/components/pwa/OfflineIndicator";
import { UniversalInstallBanner } from "@/components/pwa/UniversalInstallBanner";
import { PWAStatus } from "@/components/pwa/PWAStatus";
import { DevotionalCardSkeleton } from "@/components/loading/DevotionalCardSkeleton";

// Lazy load heavy components for code splitting
const Index = lazy(() => import("./pages/Index"));
const Today = lazy(() => import("./pages/Today"));
const Bookmarks = lazy(() => import("./pages/Bookmarks"));
const Discussions = lazy(() => import("./pages/Discussions"));
const Groups = lazy(() => import("./pages/Groups"));
const GroupDetail = lazy(() => import("./pages/GroupDetail"));
const CreateGroup = lazy(() => import("./pages/CreateGroup"));
const AcceptInvite = lazy(() => import("./pages/AcceptInvite"));
const Auth = lazy(() => import("./pages/Auth"));
const Compose = lazy(() => import("./pages/Compose"));
const Feed = lazy(() => import("./pages/Feed"));
const Devotional = lazy(() => import("./pages/Devotional"));
const Profile = lazy(() => import("./pages/Profile"));
const Achievements = lazy(() => import("./pages/Achievements"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Browse = lazy(() => import("./pages/Browse"));
const About = lazy(() => import("./pages/About"));
const Series = lazy(() => import("./pages/Series"));
const SeriesDetail = lazy(() => import("./pages/SeriesDetail"));
const Subscribe = lazy(() => import("./pages/Subscribe"));
const VerifySubscription = lazy(() => import("./pages/VerifySubscription"));

// Author pages
const SeriesManagement = lazy(() => import("./pages/author/SeriesManagement"));

// Admin pages
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboardEnhanced"));
const UserManagement = lazy(() => import("./pages/admin/UserManagement"));
const CalendarView = lazy(() => import("./pages/admin/CalendarView"));
const CalendarGridView = lazy(() => import("./pages/admin/CalendarGridView"));
const ModerationDashboard = lazy(() => import("./pages/admin/ModerationDashboard"));
const AdminContent = lazy(() => import("./pages/admin/AdminContent"));
const AdminAnalytics = lazy(() => import("./pages/admin/AdminAnalytics"));
const AdminAnalyticsEnhanced = lazy(() => import("./pages/admin/AdminAnalyticsEnhanced"));
const Announcements = lazy(() => import("./pages/admin/Announcements"));
const AdminSettings = lazy(() => import("./pages/admin/AdminSettings"));

// Loading fallback component
const PageSkeleton = () => (
  <div className="min-h-screen bg-background p-4">
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="h-8 bg-muted rounded w-1/3 animate-pulse" />
      <div className="h-4 bg-muted rounded w-2/3 animate-pulse" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <DevotionalCardSkeleton key={i} />
        ))}
      </div>
    </div>
  </div>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          {/* PWA Components */}
          <PWAUpdateNotification />
          <OfflineIndicator />
          <UniversalInstallBanner />
          <PWAStatus />

          {/* Toast Notifications */}
          <Toaster />
          <Sonner />

          <BrowserRouter>
            <Suspense fallback={<PageSkeleton />}>
              <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Index />} />
            <Route path="/about" element={<About />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/series" element={<Series />} />
            <Route path="/series/:id" element={<SeriesDetail />} />
            <Route path="/today" element={<Today />} />
            <Route path="/devotional/:id" element={<Devotional />} />
            <Route path="/subscribe" element={<Subscribe />} />
            <Route path="/subscriptions/verify" element={<VerifySubscription />} />

            {/* Auth Routes */}
            <Route path="/auth" element={<Auth />} />
            <Route path="/login" element={<Auth />} />
            <Route path="/signup" element={<Auth />} />

            {/* Authenticated User Routes */}
            <Route path="/feed" element={<ProtectedRoute><Feed /></ProtectedRoute>} />
            <Route path="/bookmarks" element={<ProtectedRoute><Bookmarks /></ProtectedRoute>} />
            <Route path="/discussions" element={<ProtectedRoute><Discussions /></ProtectedRoute>} />
            <Route path="/discussions/:id" element={<ProtectedRoute><Discussions /></ProtectedRoute>} />
            <Route path="/groups" element={<ProtectedRoute><Groups /></ProtectedRoute>} />
            <Route path="/groups/new" element={<ProtectedRoute><CreateGroup /></ProtectedRoute>} />
            <Route path="/groups/:id" element={<ProtectedRoute><GroupDetail /></ProtectedRoute>} />
            <Route path="/invite/:token" element={<ProtectedRoute><AcceptInvite /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/achievements" element={<ProtectedRoute><Achievements /></ProtectedRoute>} />

            {/* Admin Routes */}
            <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="/dashboard" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="/dashboard/series" element={<AdminRoute><SeriesManagement /></AdminRoute>} />
            <Route path="/admin/compose" element={<AdminRoute><Compose /></AdminRoute>} />
            <Route path="/admin/content" element={<AdminRoute><AdminContent /></AdminRoute>} />
            <Route path="/admin/calendar" element={<AdminRoute><CalendarGridView /></AdminRoute>} />
            <Route path="/admin/calendar/old" element={<AdminRoute><CalendarView /></AdminRoute>} />
            <Route path="/admin/users" element={<AdminRoute><UserManagement /></AdminRoute>} />
            <Route path="/admin/moderation" element={<AdminRoute><ModerationDashboard /></AdminRoute>} />
            <Route path="/admin/analytics" element={<AdminRoute><AdminAnalyticsEnhanced /></AdminRoute>} />
            <Route path="/admin/announcements" element={<AdminRoute><Announcements /></AdminRoute>} />
            <Route path="/admin/settings" element={<AdminRoute><AdminSettings /></AdminRoute>} />

                {/* 404 Catch-All - MUST BE LAST */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
