/**
 * Accept Invite Page
 * Page for accepting group invitations via invite link
 */

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader2, Users, BookOpen } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { MainNavigation } from '@/components/navigation/MainNavigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

export default function AcceptInvite() {
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();
  const { user } = useAuth();
  const { toast } = useToast();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  // Fetch invite details
  const { data: invite, isLoading } = useQuery({
    queryKey: ['invite', token],
    queryFn: async () => {
      if (!token) throw new Error('No token provided');
      return await apiClient.getInviteByToken(token);
    },
    enabled: !!token,
    retry: false,
  });

  // Accept invite mutation
  const acceptMutation = useMutation({
    mutationFn: async () => {
      if (!token) throw new Error('No token provided');
      return await apiClient.acceptInvite(token);
    },
    onSuccess: (data) => {
      setStatus('success');
      toast({
        title: "Invite accepted!",
        description: "You've joined the group",
      });
      setTimeout(() => {
        navigate(`/groups/${data.group_id}`);
      }, 2000);
    },
    onError: (error: any) => {
      setStatus('error');
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to accept invite";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  useEffect(() => {
    if (invite && user && status === 'loading') {
      // Auto-accept if user is logged in
      acceptMutation.mutate();
    } else if (invite && !user) {
      // Redirect to login if not authenticated
      navigate(`/login?redirect=/invite/${token}`);
    }
  }, [invite, user, token]);

  if (isLoading || status === 'loading') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-secondary" />
          <p className="text-muted-foreground">Loading invite...</p>
        </div>
      </div>
    );
  }

  if (status === 'error' || !invite) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <MainNavigation />
        <div className="text-center max-w-md px-4">
          <XCircle className="w-16 h-16 mx-auto mb-4 text-destructive" />
          <h2 className="font-serif text-2xl font-bold mb-2">Invite Not Found</h2>
          <p className="text-muted-foreground mb-6">
            This invite may have expired or been revoked
          </p>
          <Button onClick={() => navigate('/groups')}>
            Browse Groups
          </Button>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center pb-20">
        <MainNavigation />
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md px-4"
        >
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-secondary" />
          <h2 className="font-serif text-2xl font-bold mb-2">Invite Accepted!</h2>
          <p className="text-muted-foreground mb-6">
            You've successfully joined the group. Redirecting...
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <MainNavigation />
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card rounded-2xl border border-border p-8"
          >
            <Users className="w-16 h-16 mx-auto mb-4 text-secondary" />
            <h1 className="font-serif text-2xl font-bold text-foreground mb-2">
              Group Invitation
            </h1>
            <p className="text-muted-foreground mb-6">
              You've been invited to join a Bible study group
            </p>
            {invite && (
              <div className="text-left bg-muted/30 rounded-lg p-4 mb-6">
                <p className="text-sm text-muted-foreground mb-1">Invited by</p>
                <p className="font-medium text-foreground">{invite.inviter_name}</p>
              </div>
            )}
            {!user && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Please sign in to accept this invitation
                </p>
                <div className="flex gap-3">
                  <Button
                    onClick={() => navigate(`/login?redirect=/invite/${token}`)}
                    className="flex-1"
                  >
                    Sign In
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/signup?redirect=/invite/${token}`)}
                    className="flex-1"
                  >
                    Sign Up
                  </Button>
                </div>
              </div>
            )}
            {user && (
              <Button
                onClick={() => acceptMutation.mutate()}
                disabled={acceptMutation.isPending}
                className="w-full gap-2"
              >
                {acceptMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Accepting...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Accept Invitation
                  </>
                )}
              </Button>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

