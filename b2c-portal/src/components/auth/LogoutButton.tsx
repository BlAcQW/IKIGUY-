/**
 * Logout Button Component
 * Handles user logout with confirmation using MongoDB authentication
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Loader2, LogOut } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';

interface LogoutButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  confirmLogout?: boolean;
  showIcon?: boolean;
  className?: string;
  onLogout?: () => void;
}

export const LogoutButton: React.FC<LogoutButtonProps> = ({
  variant = 'outline',
  size = 'default',
  confirmLogout = false,
  showIcon = true,
  className = '',
  onLogout
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const { signOut } = useMongoAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    if (confirmLogout) {
      const confirmed = window.confirm('Are you sure you want to sign out?');
      if (!confirmed) return;
    }

    setIsLoading(true);

    try {
      await signOut();

      // Call custom onLogout callback if provided
      if (onLogout) {
        onLogout();
      }

      // Redirect to auth page after successful logout
      navigate('/auth');
    } catch (error) {
      toast({
        title: 'Logout Error',
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleLogout}
      disabled={isLoading}
      className={className}
    >
      {isLoading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Signing Out...
        </>
      ) : (
        <>
          {showIcon && <LogOut className="mr-2 h-4 w-4" />}
          Logout
        </>
      )}
    </Button>
  );
};