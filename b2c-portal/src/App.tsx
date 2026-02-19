import React, { Suspense, lazy, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { MongoAuthProvider } from "./components/auth/MongoAuthContext";
import { OrganizationProvider } from "./contexts/OrganizationContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import ReportBug from "./components/ReportBug";
import { trackReferralClick } from "./lib/referral-tracking";
import { ReferralJoinPrompt, useReferralJoinPrompt } from "./components/affiliates/ReferralJoinPrompt";

// Core pages - loaded immediately
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import MongoAuth from "./pages/MongoAuth";
import Dashboard from "./pages/Dashboard";
import AcceptInvitation from "./pages/AcceptInvitation";

// Lazy-loaded pages (loaded on demand)
const Settings = lazy(() => import("./pages/Settings"));
const Pricing = lazy(() => import("./pages/Pricing"));
const About = lazy(() => import("./pages/About"));
const Features = lazy(() => import("./pages/Features"));
const VoiceAgent = lazy(() => import("./pages/VoiceAgent"));
const PhoneNumbers = lazy(() => import("./pages/PhoneNumbers"));
const VoiceStudio = lazy(() => import("./pages/VoiceStudio"));
const VoiceLab = lazy(() => import("./pages/VoiceLab"));
const VoiceLabEnhanced = lazy(() => import("./pages/VoiceLabEnhanced"));
const TwiConversation = lazy(() => import("./pages/TwiConversation"));
const TTSLab = lazy(() => import("./pages/TTSLab"));
const AudioHistory = lazy(() => import("./pages/AudioHistory"));
const APIKeys = lazy(() => import("./pages/APIKeys"));
const ASRLab = lazy(() => import("./pages/ASRLab"));
const VapiManagement = lazy(() => import("./pages/VapiManagement"));
const VapiAssistants = lazy(() => import("./pages/VapiAssistants"));
const LLMLab = lazy(() => import("./pages/LLMLab"));
const SelectTemplate = lazy(() => import("./pages/SelectTemplate"));
const TemplateSelector = lazy(() => import("./pages/TemplateSelector"));
const TemplateSelectionPage = lazy(() => import("./pages/TemplateSelection"));
const AutomationDeployPage = lazy(() => import("./pages/AutomationDeploy"));
const Audiences = lazy(() => import("./pages/Audiences"));
const SMSCampaigns = lazy(() => import("./pages/SMSCampaigns"));
const WhatsAppCampaigns = lazy(() => import("./pages/WhatsAppCampaigns"));
const WhatsAppCampaignForm = lazy(() => import("./pages/WhatsAppCampaignForm"));
const Automations = lazy(() => import("./pages/Automations"));
const AutomationTemplates = lazy(() => import("./pages/AutomationTemplates"));
const AutomationConfiguration = lazy(() => import("./pages/AutomationConfiguration"));
const AutomationSuccess = lazy(() => import("./pages/AutomationSuccess"));
const Integrations = lazy(() => import("./pages/Integrations"));
const Insurance = lazy(() => import("./pages/Insurance"));
const QuickDeploy = lazy(() => import("./pages/QuickDeploy"));
const AdminLayout = lazy(() => import("./pages/admin/AdminLayout"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const AdminSystemHealth = lazy(() => import("./pages/admin/SystemHealth"));
const AdminUsers = lazy(() => import("./pages/admin/Users"));
const AdminRoles = lazy(() => import("./pages/admin/Roles"));
const AdminSettings = lazy(() => import("./pages/admin/AdminSettings"));
const AdminDatabase = lazy(() => import("./pages/admin/Database"));
const AdminLogs = lazy(() => import("./pages/admin/Logs"));
const AdminApiKeys = lazy(() => import("./pages/admin/ApiKeys"));
const AdminGpuMonitoring = lazy(() => import("./pages/admin/GpuMonitoring"));
const AdminOrganizations = lazy(() => import("./pages/admin/Organizations"));
const AdminCostAnalytics = lazy(() => import("./pages/admin/CostAnalytics"));
const AdminBillingManagement = lazy(() => import("./pages/admin/BillingManagement"));
const AdminFraudDetection = lazy(() => import("./pages/admin/FraudDetection"));
const AdminWalletAutoReload = lazy(() => import("./pages/admin/WalletAutoReload"));
const AdminVoiceLibrary = lazy(() => import("./pages/admin/VoiceLibraryAdmin"));
const AdminVoiceSettings = lazy(() => import("./pages/admin/VoiceSettingsAdmin"));
const CallLogs = lazy(() => import("./pages/CallLogs"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Billing = lazy(() => import("./pages/Billing"));
const KnowledgeBase = lazy(() => import("./pages/KnowledgeBase"));
const CustomTools = lazy(() => import("./pages/CustomTools"));
const RegisterTool = lazy(() => import("./pages/RegisterTool"));
const CustomToolDetail = lazy(() => import("./pages/CustomToolDetail"));
const CronManagement = lazy(() => import("./pages/CronManagement"));
const Help = lazy(() => import("./pages/Help"));
const Utilities = lazy(() => import("./pages/Utilities"));
const SpeechToSpeech = lazy(() => import("./pages/SpeechToSpeech"));
const Telephony = lazy(() => import("./pages/Telephony"));
const AffiliatesDashboard = lazy(() => import("./pages/affiliates/AffiliatesDashboard"));
const AffiliatesJoin = lazy(() => import("./pages/affiliates/AffiliatesJoin"));

// Loading spinner component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
  </div>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache configuration for performance
      staleTime: 5 * 60 * 1000, // 5 minutes - data stays fresh
      cacheTime: 10 * 60 * 1000, // 10 minutes - keep in cache
      refetchOnMount: false, // Don't refetch if data is fresh
      refetchOnWindowFocus: false, // Don't refetch on window focus
      refetchOnReconnect: false, // Don't refetch on reconnect

      // Retry logic with exponential backoff
      retry: (failureCount, error: any) => {
        // Don't retry on auth errors (401, 403)
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          return false;
        }
        // Don't retry on 4xx client errors (except 429 rate limit, 408 timeout, 503 service unavailable)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          if (error?.response?.status === 429 || error?.response?.status === 408) {
            return failureCount < 3; // Retry rate limits and timeouts
          }
          return false;
        }
        // Retry 5xx errors up to 3 times
        return failureCount < 3;
      },

      // Exponential backoff delay
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: false, // Don't retry mutations by default
    },
  },
});

/**
 * Referral Tracking Component
 * Runs on every route change to check for referral parameters
 * Redirects to affiliate join page if referral link is clicked
 */
const ReferralTracker = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // CRITICAL: Check for referral code SYNCHRONOUSLY and redirect IMMEDIATELY
    // This must happen before any other component's useEffect runs
    const searchParams = new URLSearchParams(location.search);
    const refParam = searchParams.get('ref');
    
    // If there's a referral code, redirect IMMEDIATELY with highest priority
    if (refParam) {
      const currentPath = location.pathname;
      const isOnAffiliatePage = currentPath.includes('/affiliates/');
      
      // Only redirect if not already on an affiliate page
      if (!isOnAffiliatePage) {
        console.log('[ReferralTracker] Referral code detected, redirecting to /affiliates/join');
        // Use replace: true and immediate execution to prevent other redirects
        navigate('/affiliates/join', { replace: true });
        
        // Then do the async tracking in the background (non-blocking)
        trackReferralClick().catch(error => {
          console.error('[Referral Tracking] Error tracking referral:', error);
        });
        
        // Return early to prevent any other logic
        return;
      } else {
        // Already on affiliate page, just track it
        trackReferralClick().catch(error => {
          console.error('[Referral Tracking] Error tracking referral:', error);
        });
      }
    }
  }, [location.search, location.pathname, navigate]);

  return null;
};

/**
 * Referral Join Prompt Component
 * Shows prompt to logged-in users when they click a referral link
 */
const ReferralJoinPromptWrapper = () => {
  const { showPrompt, referralCode, setShowPrompt } = useReferralJoinPrompt();

  if (!referralCode) return null;

  return (
    <ReferralJoinPrompt
      open={showPrompt}
      onOpenChange={setShowPrompt}
      referralCode={referralCode}
    />
  );
};

const AppContent = () => {
  return (
    <>
      <ReferralTracker />
      <ReferralJoinPromptWrapper />
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/features" element={<Features />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/auth" element={<MongoAuth />} />
            <Route path="/accept-invitation" element={<AcceptInvitation />} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/voice-agent" element={<ProtectedRoute><VoiceAgent /></ProtectedRoute>} />
            <Route path="/call-logs" element={<ProtectedRoute><CallLogs /></ProtectedRoute>} />
            <Route path="/audiences" element={<ProtectedRoute><Audiences /></ProtectedRoute>} />
            <Route path="/sms-campaigns" element={<ProtectedRoute><SMSCampaigns /></ProtectedRoute>} />
            <Route path="/whatsapp-campaigns" element={<ProtectedRoute><WhatsAppCampaigns /></ProtectedRoute>} />
            <Route path="/whatsapp-campaigns/create" element={<ProtectedRoute><WhatsAppCampaignForm /></ProtectedRoute>} />
            <Route path="/automations" element={<ProtectedRoute><Automations /></ProtectedRoute>} />
            <Route path="/automations/select-template" element={<ProtectedRoute><TemplateSelector mode="automation" /></ProtectedRoute>} />
            <Route path="/automations/templates" element={<ProtectedRoute><AutomationTemplates /></ProtectedRoute>} />
            <Route path="/automations/templates/:industry" element={<ProtectedRoute><AutomationTemplates /></ProtectedRoute>} />
            <Route path="/automations/templates/:templateId/audience-selection" element={<ProtectedRoute><Audiences /></ProtectedRoute>} />
            <Route path="/automations/templates/:templateId/configure" element={<ProtectedRoute><AutomationConfiguration /></ProtectedRoute>} />
            <Route path="/automations/deploy" element={<ProtectedRoute><AutomationDeployPage /></ProtectedRoute>} />
            <Route path="/automations/industry/:industryId" element={<ProtectedRoute><TemplateSelector mode="automation" /></ProtectedRoute>} />
            <Route path="/automations/configure/:templateId" element={<ProtectedRoute><AutomationConfiguration /></ProtectedRoute>} />
            <Route path="/automations/success" element={<ProtectedRoute><AutomationSuccess /></ProtectedRoute>} />
            <Route path="/automations/custom" element={<ProtectedRoute><AutomationConfiguration /></ProtectedRoute>} />
            <Route path="/automations/quick-deploy" element={<ProtectedRoute><QuickDeploy /></ProtectedRoute>} />
            <Route path="/quick-deploy" element={<ProtectedRoute><QuickDeploy /></ProtectedRoute>} />
            <Route path="/integrations" element={<ProtectedRoute><Integrations /></ProtectedRoute>} />
            <Route path="/insurance" element={<ProtectedRoute><Insurance /></ProtectedRoute>} />
            <Route path="/phone-numbers" element={<ProtectedRoute><PhoneNumbers /></ProtectedRoute>} />
            <Route path="/voice-library" element={<ProtectedRoute><VoiceStudio /></ProtectedRoute>} />
            <Route path="/voice-lab" element={<ProtectedRoute><VoiceLab /></ProtectedRoute>} />
            <Route path="/voice-lab-enhanced" element={<ProtectedRoute><VoiceLabEnhanced /></ProtectedRoute>} />
            <Route path="/tts-lab" element={<ProtectedRoute><TTSLab /></ProtectedRoute>} />
            <Route path="/audio-history" element={<ProtectedRoute><AudioHistory /></ProtectedRoute>} />
            <Route path="/api-keys" element={<ProtectedRoute><APIKeys /></ProtectedRoute>} />
            <Route path="/asr-lab" element={<ProtectedRoute><ASRLab /></ProtectedRoute>} />
            <Route path="/vapi-management" element={<ProtectedRoute><VapiManagement /></ProtectedRoute>} />
            <Route path="/vapi-assistants" element={<ProtectedRoute><VapiAssistants /></ProtectedRoute>} />
            <Route path="/llm-lab" element={<ProtectedRoute><LLMLab /></ProtectedRoute>} />
            <Route path="/twi-conversation" element={<ProtectedRoute><TwiConversation /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
              <Route index element={<AdminDashboard />} />
              <Route path="organizations" element={<AdminOrganizations />} />
              <Route path="billing" element={<AdminBillingManagement />} />
              <Route path="fraud" element={<AdminFraudDetection />} />
              <Route path="auto-reload" element={<AdminWalletAutoReload />} />
              <Route path="system-health" element={<AdminSystemHealth />} />
              <Route path="gpu" element={<AdminGpuMonitoring />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="roles" element={<AdminRoles />} />
              <Route path="settings" element={<AdminSettings />} />
              <Route path="database" element={<AdminDatabase />} />
              <Route path="logs" element={<AdminLogs />} />
              <Route path="api-keys" element={<AdminApiKeys />} />
              <Route path="cost-analytics" element={<AdminCostAnalytics />} />
              <Route path="cron" element={<CronManagement />} />
              <Route path="voice-library" element={<AdminVoiceLibrary />} />
              <Route path="voice-settings" element={<AdminVoiceSettings />} />
            </Route>
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/billing" element={<ProtectedRoute><Billing /></ProtectedRoute>} />
            <Route path="/knowledge-base" element={<ProtectedRoute><KnowledgeBase /></ProtectedRoute>} />
            <Route path="/custom-tools" element={<ProtectedRoute><CustomTools /></ProtectedRoute>} />
            <Route path="/custom-tools/register" element={<ProtectedRoute><RegisterTool /></ProtectedRoute>} />
            <Route path="/custom-tools/:toolId" element={<ProtectedRoute><CustomToolDetail /></ProtectedRoute>} />
            <Route path="/utilities" element={<ProtectedRoute><Utilities /></ProtectedRoute>} />
            <Route path="/speech-to-speech" element={<ProtectedRoute><SpeechToSpeech /></ProtectedRoute>} />
            <Route path="/telephony" element={<ProtectedRoute><Telephony /></ProtectedRoute>} />
            <Route path="/help" element={<ProtectedRoute><Help /></ProtectedRoute>} />
            <Route path="/affiliates/dashboard" element={<ProtectedRoute><AffiliatesDashboard /></ProtectedRoute>} />
            <Route path="/affiliates/join" element={<AffiliatesJoin />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <MongoAuthProvider>
      <OrganizationProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <ReportBug />
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </TooltipProvider>
      </OrganizationProvider>
    </MongoAuthProvider>
  </QueryClientProvider>
);

export default App;
