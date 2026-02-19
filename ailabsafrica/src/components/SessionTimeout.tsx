import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { Clock, RefreshCw } from 'lucide-react';

interface SessionTimeoutProps {
  children: React.ReactNode;
}

const SessionTimeout: React.FC<SessionTimeoutProps> = ({ children }) => {
  const { session, isSessionExpired, refreshSession, signOut } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showTimeoutDialog, setShowTimeoutDialog] = useState(false);
  const [timeUntilExpiry, setTimeUntilExpiry] = useState<number>(0);

  // Check session expiry every minute
  useEffect(() => {
    if (!session) return;

    const checkSessionExpiry = () => {
      if (!session.expires_at) return;

      const now = Math.floor(Date.now() / 1000);
      const timeLeft = session.expires_at - now;
      
      // Show warning 5 minutes before expiry
      if (timeLeft <= 300 && timeLeft > 0) {
        setTimeUntilExpiry(timeLeft);
        setShowTimeoutDialog(true);
      }
      
      // Auto logout when session expires
      if (timeLeft <= 0) {
        handleSessionExpired();
      }
    };

    // Check immediately
    checkSessionExpiry();

    // Check every minute
    const interval = setInterval(checkSessionExpiry, 60000);

    return () => clearInterval(interval);
  }, [session]);

  // Handle session expiration
  useEffect(() => {
    if (isSessionExpired) {
      handleSessionExpired();
    }
  }, [isSessionExpired]);

  const handleSessionExpired = () => {
    toast({
      title: "Session Expired",
      description: "Your session has expired. Please sign in again.",
      variant: "destructive",
    });
    
    signOut();
    navigate('/auth');
  };

  const handleRefreshSession = async () => {
    try {
      await refreshSession();
      setShowTimeoutDialog(false);
      toast({
        title: "Session Refreshed",
        description: "Your session has been refreshed successfully.",
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh session. Please sign in again.",
        variant: "destructive",
      });
      handleSessionExpired();
    }
  };

  const handleSignOut = () => {
    setShowTimeoutDialog(false);
    handleSessionExpired();
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <>
      {children}
      
      <Dialog open={showTimeoutDialog} onOpenChange={setShowTimeoutDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-orange-500" />
              Session Expiring Soon
            </DialogTitle>
            <DialogDescription>
              Your session will expire in {formatTime(timeUntilExpiry)}. 
              Would you like to refresh your session to stay logged in?
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex flex-col gap-3">
            <Button 
              onClick={handleRefreshSession}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh Session
            </Button>
            
            <Button 
              variant="outline" 
              onClick={handleSignOut}
            >
              Sign Out
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default SessionTimeout;
