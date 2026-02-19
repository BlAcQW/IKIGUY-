import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Suspense, lazy } from "react";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AccessibilityProvider } from "./components/AccessibilityProvider";
import Navigation from "./components/Navigation";
import ErrorBoundary from "./components/ErrorBoundary";
import SessionTimeout from "./components/SessionTimeout";
import ProtectedRoute from "./components/ProtectedRoute";
import ServiceWorkerRegistration from "./components/ServiceWorkerRegistration";
import PerformanceMonitor from "./components/PerformanceMonitor";
import { UserRole } from "./lib/roles";
// import { I18nProvider } from "./contexts/I18nContext";
import { SeoProvider } from "./components/SEO/SeoProvider";
import { HelpProvider } from "./contexts/HelpContext";
import { useToast } from "@/components/ui/use-toast";

// Import i18n configuration - temporarily disabled for debugging
// import './lib/i18n';

// Lazy load all pages for code splitting
const Home = lazy(() => import("./pages/Home"));
const Demos = lazy(() => import("./pages/Demos"));
const Contact = lazy(() => import("./pages/Contact"));
const Recruitment = lazy(() => import("./pages/Recruitment"));
const Auth = lazy(() => import("./pages/Auth"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const PaymentSuccess = lazy(() => import("./pages/PaymentSuccess"));
const NotFound = lazy(() => import("./pages/NotFound"));
const BankingSupportBot = lazy(() => import("./pages/demos/BankingSupportBot"));
const BankLoansSalesExpert = lazy(() => import("./pages/demos/BankLoansSalesExpert"));
const InsuranceClaimsAssistant = lazy(() => import("./pages/demos/InsuranceClaimsAssistant"));
const InsuranceSalesExpert = lazy(() => import("./pages/demos/InsuranceSalesExpert"));
const RealEstateLeadQualifier = lazy(() => import("./pages/demos/RealEstateLeadQualifier"));
const RetailProductAdvisor = lazy(() => import("./pages/demos/RetailProductAdvisor"));
const HealthcareAppointmentBot = lazy(() => import("./pages/demos/HealthcareAppointmentBot"));
const ServiceBookingAssistant = lazy(() => import("./pages/demos/ServiceBookingAssistant"));
const PaymentReminderSystem = lazy(() => import("./pages/demos/PaymentReminderSystem"));
const LoanApplicationAssistant = lazy(() => import("./pages/demos/LoanApplicationAssistant"));
const GermanTherapist = lazy(() => import("./pages/demos/GermanTherapist"));
const GreenBook = lazy(() => import("./pages/demos/GreenBook"));
const KojoBonsuCampaign = lazy(() => import("./pages/demos/KojoBonsuCampaign"));
const ScheduleDemo = lazy(() => import("./pages/ScheduleDemo"));
const CreateAssistant = lazy(() => import("./pages/CreateAssistant"));
const VoiceAgents = lazy(() => import("./pages/VoiceAgents"));
const CustomDemos = lazy(() => import("./pages/CustomDemos"));
const DemoPreview = lazy(() => import("./pages/DemoPreview"));
// CDNDashboard removed - CDN functionality disabled
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const VerifyEmail = lazy(() => import("./pages/VerifyEmail"));
const Wallet = lazy(() => import("./pages/Wallet"));
const GuestDashboard = lazy(() => import("./pages/GuestDashboard"));
const Debug = lazy(() => import("./pages/Debug"));
const FAQ = lazy(() => import("./pages/FAQ"));
const SubscriptionManagement = lazy(() => import("./components/SubscriptionManagement"));
const TeamManagement = lazy(() => import("./components/TeamManagement"));
const MarketingFeatures = lazy(() => import("./components/MarketingFeatures"));
const Help = lazy(() => import("./pages/Help"));
const VoiceAgentDetails = lazy(() => import("./pages/VoiceAgentDetails"));
const IntegrationTest = lazy(() => import("./components/IntegrationTest"));
const WebhookTest = lazy(() => import("./components/WebhookTest"));

// Loading component for Suspense fallback
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
  </div>
);

const queryClient = new QueryClient();

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <HelmetProvider>
        <ThemeProvider>
          <AuthProvider>
            <AccessibilityProvider>
              <TooltipProvider>
                <Toaster />
                <Sonner />
                <ServiceWorkerRegistration>
                  <PerformanceMonitor enabled={import.meta.env.DEV}>
                    <BrowserRouter>
                      <SessionTimeout>
                      {/* <I18nProvider> */}
                        <SeoProvider>
                          <HelpProvider>
                          <Navigation />
                          <Suspense fallback={<LoadingSpinner />}>
                            <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/auth" element={<Auth />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="/reset-password" element={<ResetPassword />} />
                    <Route path="/verify-email" element={<VerifyEmail />} />
                    <Route path="/dashboard" element={
                      <ProtectedRoute>
                        <Dashboard />
                      </ProtectedRoute>
                    } />
                    <Route path="/payment-success" element={<PaymentSuccess />} />
                    <Route path="/demos" element={<Demos />} />
                    <Route path="/demos/banking-support-bot" element={<BankingSupportBot />} />
                    <Route path="/demos/bank-loans-sales-expert" element={<BankLoansSalesExpert />} />
                    <Route path="/demos/insurance-claims-assistant" element={<InsuranceClaimsAssistant />} />
                    <Route path="/demos/insurance-sales-expert" element={<InsuranceSalesExpert />} />
                    <Route path="/demos/real-estate-lead-qualifier" element={<RealEstateLeadQualifier />} />
                    <Route path="/demos/retail-product-advisor" element={<RetailProductAdvisor />} />
                    <Route path="/demos/healthcare-appointment-bot" element={<HealthcareAppointmentBot />} />
                    <Route path="/demos/service-booking-assistant" element={<ServiceBookingAssistant />} />
                    <Route path="/demos/payment-reminder-system" element={<PaymentReminderSystem />} />
                    <Route path="/demos/loan-application-assistant" element={<LoanApplicationAssistant />} />
                    <Route path="/demos/german-therapist" element={<GermanTherapist />} />
                    <Route path="/demos/green-book" element={<GreenBook />} />
                    <Route path="/demos/kojo-bonsu-campaign" element={<KojoBonsuCampaign />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/recruitment" element={<Recruitment />} />
                    <Route path="/careers" element={<Recruitment />} />
                    <Route path="/faq" element={<FAQ />} />
                    <Route path="/schedule-demo" element={<ScheduleDemo />} />
                    <Route path="/create-assistant" element={<CreateAssistant />} />
                    <Route path="/guest-dashboard" element={<GuestDashboard />} />
                    <Route path="/guest-access" element={<GuestDashboard />} />
                    <Route path="/debug" element={<Debug />} />
                    <Route path="/voice-agents" element={
                      <ProtectedRoute requiredPermission={{ resource: 'assistants', action: 'read' }}>
                        <VoiceAgents />
                      </ProtectedRoute>
                    } />
                    <Route path="/custom-demos" element={
                      <ProtectedRoute requiredPermission={{ resource: 'demos', action: 'read' }}>
                        <CustomDemos />
                      </ProtectedRoute>
                    } />
                                         <Route path="/demo-preview" element={<DemoPreview />} />
                    <Route path="/wallet" element={
                      <ProtectedRoute>
                        <Wallet />
                      </ProtectedRoute>
                    } />
                                         <Route path="/subscription" element={
                       <ProtectedRoute>
                         <SubscriptionManagement />
                       </ProtectedRoute>
                     } />
                     <Route path="/teams" element={
                       <ProtectedRoute>
                         <TeamManagement />
                       </ProtectedRoute>
                     } />
                     <Route path="/marketing" element={
                       <ProtectedRoute>
                         <MarketingFeatures />
                       </ProtectedRoute>
                     } />
                     <Route path="/help" element={<Help />} />
                     <Route path="/voice-agents/:id" element={<VoiceAgentDetails />} />
                     <Route path="/integration-test" element={<IntegrationTest />} />
                     <Route path="/webhook-test" element={<WebhookTest />} />
                    {/* CDN Dashboard removed - CDN functionality disabled */}
                                                            </Routes>
                                                    </Suspense>
                        </HelpProvider>
                      </SeoProvider>
                      {/* </I18nProvider> */}
                    </SessionTimeout>
                </BrowserRouter>
              </PerformanceMonitor>
            </ServiceWorkerRegistration>
          </TooltipProvider>
        </AccessibilityProvider>
      </AuthProvider>
    </ThemeProvider>
        </HelmetProvider>
  </QueryClientProvider>
</ErrorBoundary>
);

export default App;
