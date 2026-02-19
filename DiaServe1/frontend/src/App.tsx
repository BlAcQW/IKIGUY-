import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { AuthProvider } from "@/contexts/AuthContext";
import { OrganizationProvider } from "@/contexts/OrganizationContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { PWAUpdateBanner } from "@/components/PWAUpdateBanner";
import { PWAInstallPrompt } from "@/components/PWAInstallPrompt";
import { OfflineIndicator } from "@/components/OfflineIndicator";
import ErrorBoundary from "@/components/ErrorBoundary";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import InviteAccept from "./pages/InviteAccept";
import Dashboard from "./pages/Dashboard";
import Properties from "./pages/Properties";
import PropertyDetail from "./pages/PropertyDetail";
import Map from "./pages/Map";
import Saved from "./pages/Saved";
import MyProperties from "./pages/MyProperties";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Contacts from "./pages/Contacts";
import Bookings from "./pages/Bookings";
import Campaigns from "./pages/Campaigns";
import Documents from "./pages/Documents";
import Invoices from "./pages/Invoices";
import Payments from "./pages/Payments";
import NewPayment from "./pages/NewPayment";
import AIChat from "./pages/AIChat";
import VoiceAgent from "./pages/VoiceAgent";
import AIAssistant from "./pages/AIAssistant";
import Settings from "./pages/Settings";
import Help from "./pages/Help";
import Admin from "./pages/Admin";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <AuthProvider>
          <OrganizationProvider>
            <TooltipProvider>
              <Toaster />
              <Sonner />
              <PWAUpdateBanner />
              <PWAInstallPrompt />
              <OfflineIndicator />
              <BrowserRouter>
                <Routes>
                  {/* Public routes with PublicLayout */}
                  <Route element={<PublicLayout />}>
                    <Route path="/" element={<Landing />} />
                    <Route path="/properties" element={<Properties />} />
                    <Route path="/properties/:id" element={<PropertyDetail />} />
                    <Route path="/map" element={<Map />} />
                    <Route path="/saved" element={<Saved />} />
                    <Route path="/my-properties" element={<MyProperties />} />
                    <Route path="/about" element={<About />} />
                    <Route path="/contact" element={<Contact />} />
                  </Route>

                  {/* Auth routes (no layout) */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/invite/:token" element={<InviteAccept />} />

                  {/* Protected routes with DashboardLayout */}
                  <Route element={<ProtectedRoute />}>
                    <Route element={<DashboardLayout />}>
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/contacts" element={<Contacts />} />
                      <Route path="/bookings" element={<Bookings />} />
                      <Route path="/campaigns" element={<Campaigns />} />
                      <Route path="/documents" element={<Documents />} />
                      <Route path="/invoices" element={<Invoices />} />
                      <Route path="/payments" element={<Payments />} />
                      <Route path="/payments/new" element={<NewPayment />} />
                      <Route path="/ai-chat" element={<AIChat />} />
                      <Route path="/voice-agent" element={<VoiceAgent />} />
                      <Route path="/ai-assistant" element={<AIAssistant />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="/admin" element={<Admin />} />
                      <Route path="/help" element={<Help />} />
                    </Route>
                  </Route>

                  {/* 404 route */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </BrowserRouter>
            </TooltipProvider>
          </OrganizationProvider>
        </AuthProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
};

export default App;
