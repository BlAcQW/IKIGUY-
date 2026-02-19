import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { CheckCircle, XCircle, Mail, ArrowRight } from 'lucide-react';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const handleEmailVerification = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const type = searchParams.get('type');

      if (!accessToken || type !== 'signup') {
        setIsError(true);
        setErrorMessage('Invalid verification link');
        return;
      }

      setIsLoading(true);

      try {
        // Set the session with the tokens
        const { data, error } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken || ''
        });

        if (error) {
          throw error;
        }

        if (data.session) {
          setIsSuccess(true);
          toast({
            title: "Email verified!",
            description: "Your email has been successfully verified. Welcome to AI Labs Africa!",
          });
        } else {
          throw new Error('Failed to verify email');
        }
      } catch (error: any) {
        console.error('Email verification error:', error);
        setIsError(true);
        setErrorMessage(error.message || 'Failed to verify email. The link may be invalid or expired.');
        toast({
          title: "Verification failed",
          description: error.message || "Failed to verify email. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    handleEmailVerification();
  }, [searchParams, navigate, toast]);

  const handleResendVerification = async () => {
    // This would typically require the user to enter their email again
    // For now, we'll redirect to the auth page
    navigate('/auth');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <LoadingSpinner size="lg" />
            </div>
            <CardTitle className="text-2xl">Verifying your email</CardTitle>
            <CardDescription>
              Please wait while we verify your email address...
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle className="h-16 w-16 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Email verified!</CardTitle>
            <CardDescription>
              Your email has been successfully verified. Welcome to AI Labs Africa!
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertDescription>
                You can now access all features of your account. We recommend completing your profile to get the most out of our services.
              </AlertDescription>
            </Alert>
            <Button 
              className="w-full" 
              onClick={() => navigate('/dashboard')}
            >
              Continue to Dashboard
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <XCircle className="h-16 w-16 text-red-500" />
            </div>
            <CardTitle className="text-2xl">Verification failed</CardTitle>
            <CardDescription>
              {errorMessage}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertDescription>
                The verification link may be invalid or expired. Please try requesting a new verification email.
              </AlertDescription>
            </Alert>
            <div className="flex flex-col gap-2">
              <Button 
                variant="outline"
                onClick={handleResendVerification}
              >
                <Mail className="h-4 w-4 mr-2" />
                Request New Verification
              </Button>
              <Button 
                variant="ghost"
                onClick={() => navigate('/auth')}
              >
                Back to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Mail className="h-16 w-16 text-primary" />
          </div>
          <CardTitle className="text-2xl">Email Verification</CardTitle>
          <CardDescription>
            Please wait while we process your verification...
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
};

export default VerifyEmail;
