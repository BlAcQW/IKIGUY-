import React, { Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { BackendAuthProvider } from "@/contexts/BackendAuthContext";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { ErrorProvider } from "@/contexts/ErrorContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Loader2 } from "lucide-react";
import OfflineNotification from "./components/OfflineNotification";
import "./lib/performance"; // Initialize performance monitoring

// Lazy load pages for better performance
const Index = React.lazy(() => import("./pages/Index"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const Languages = React.lazy(() => import("./pages/Languages"));
const LanguageDetail = React.lazy(() => import("./pages/LanguageDetail"));
const LanguageFamilyDetail = React.lazy(() => import("./pages/LanguageFamilyDetail"));
const Submit = React.lazy(() => import("./pages/Submit"));
const Validate = React.lazy(() => import("./pages/Validate"));
const Community = React.lazy(() => import("./pages/Community"));
const Moderation = React.lazy(() => import("./pages/Moderation"));
const Datasets = React.lazy(() => import("./pages/Datasets"));
const MLOps = React.lazy(() => import("./pages/MLOps"));
const Search = React.lazy(() => import("./pages/Search"));
const Profile = React.lazy(() => import("./pages/Profile"));
const Notebooks = React.lazy(() => import("./pages/Notebooks"));
const NotebookUpload = React.lazy(() => import("./pages/NotebookUpload"));
const NotebookDetail = React.lazy(() => import("./pages/NotebookDetail"));
const ModelDetail = React.lazy(() => import("./pages/ModelDetail"));
const PipelineDetail = React.lazy(() => import("./pages/PipelineDetail"));
const Proposals = React.lazy(() => import("./pages/Proposals"));
const ProposalDetail = React.lazy(() => import("./pages/ProposalDetail"));
const NotFound = React.lazy(() => import("./pages/NotFound"));

// Loading component for suspense fallbacks
const PageLoader = () => (
  <div className="min-h-screen bg-background flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm text-muted-foreground">Loading page...</p>
    </div>
  </div>
);

// Optimized QueryClient configuration for better performance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes by default
      staleTime: 5 * 60 * 1000,
      // Keep unused data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests 2 times with exponential backoff
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Disable automatic refetching on window focus for better performance
      refetchOnWindowFocus: false,
      // Only refetch on reconnect if data is stale
      refetchOnReconnect: 'always',
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
    },
  },
});

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <ErrorProvider>
        <NotificationProvider>
          <BackendAuthProvider>
            <WebSocketProvider>
              <TooltipProvider>
                <Toaster />
                <Sonner />
                <OfflineNotification />
                <BrowserRouter>
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route path="/" element={<Index />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/languages" element={<Languages />} />
                      <Route path="/languages/families/:familyId" element={<LanguageFamilyDetail />} />
                      <Route path="/languages/:languageCode" element={<LanguageDetail />} />
                      <Route path="/submit" element={<Submit />} />
                      <Route path="/validate" element={<Validate />} />
                      <Route path="/community" element={<Community />} />
                      <Route path="/moderation" element={<Moderation />} />
                      <Route path="/datasets" element={<Datasets />} />
                      <Route path="/mlops" element={<MLOps />} />
                      <Route path="/search" element={<Search />} />
                      <Route path="/profile" element={<Profile />} />
                      <Route path="/profile/:userId" element={<Profile />} />
                      <Route path="/notebooks" element={<Notebooks />} />
                      <Route path="/notebooks/upload" element={<NotebookUpload />} />
                      <Route path="/notebooks/:notebookId" element={<NotebookDetail />} />
                      <Route path="/models/:modelId" element={<ModelDetail />} />
                      <Route path="/pipelines/:pipelineId" element={<PipelineDetail />} />
                      <Route path="/proposals" element={<Proposals />} />
                      <Route path="/proposals/:id" element={<ProposalDetail />} />
                      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Suspense>
                </BrowserRouter>
              </TooltipProvider>
            </WebSocketProvider>
          </BackendAuthProvider>
        </NotificationProvider>
      </ErrorProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
