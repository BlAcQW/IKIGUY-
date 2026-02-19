/**
 * MongoDB Authentication Page
 * Provides login and signup functionality using MongoDB backend
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { MongoLoginForm } from '@/components/auth/MongoLoginForm';
import { MongoSignupForm } from '@/components/auth/MongoSignupForm';
import { getReferralCode } from '@/lib/referral-tracking';

const MongoAuth = () => {
  const { isAuthenticated, isLoading } = useMongoAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // IMPORTANT: Check for referral code FIRST, before any other logic
    // This must happen synchronously to prevent race conditions
    const searchParams = new URLSearchParams(location.search);
    const refParam = searchParams.get('ref');
    const hasReferralInUrl = !!refParam;
    const hasReferralInStorage = !!getReferralCode();

    // If there's a referral code (in URL or storage), ALWAYS redirect to affiliate page
    // This takes priority over any other redirect logic
    if (hasReferralInUrl || hasReferralInStorage) {
      console.log('[MongoAuth] Referral code detected, redirecting to affiliate page');
      navigate('/affiliates/join', { replace: true });
      return; // Exit early - don't execute any other redirect logic
    }

    // Only redirect to /voice-agent if:
    // 1. Auth check is complete (not loading)
    // 2. User is authenticated
    // 3. NO referral code was found (checked above)
    if (!isLoading && isAuthenticated) {
      console.log('[MongoAuth] No referral code, redirecting authenticated user to /voice-agent');
      navigate('/voice-agent', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, location.search]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/10 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  // Don't render auth forms if user is already authenticated
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-secondary/10 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 mb-8">
          <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-foreground transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>
        </div>

        <Card className="border-border/50 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Welcome to KasaAI
            </CardTitle>
            <CardDescription>
              Sign in to your account or create a new one to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="signin" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="signin">Sign In</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>

              <TabsContent value="signin" className="space-y-4">
                <MongoLoginForm />
              </TabsContent>

              <TabsContent value="signup" className="space-y-4">
                <MongoSignupForm />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MongoAuth;