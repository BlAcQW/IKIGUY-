import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Mail,
  User,
  Lock,
  CheckCircle,
  XCircle,
  Loader2,
  Calendar,
  Shield,
  Gift
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { API_ENDPOINTS } from '@/config/api';
import { format } from 'date-fns';

interface InvitationDetails {
  email: string;
  invited_by: string;
  role: string;
  message: string | null;
  created_at: string;
  expires_at: string;
  status: string;
  is_expired: boolean;
  is_valid: boolean;
}

export default function AcceptInvitation() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    password: '',
    confirm_password: '',
  });

  // Fetch invitation details
  useEffect(() => {
    if (!token) {
      setError('Invalid invitation link. No token provided.');
      setLoading(false);
      return;
    }

    fetchInvitationDetails();
  }, [token]);

  const fetchInvitationDetails = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.invitationDetails(token!));

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch invitation details');
      }

      const data = await response.json();
      setInvitation(data.invitation);
    } catch (error: any) {
      setError(error.message || 'Failed to load invitation');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.first_name || !formData.last_name) {
      toast({
        title: 'Error',
        description: 'Please enter your first and last name',
        variant: 'destructive',
      });
      return;
    }

    if (formData.password.length < 8) {
      toast({
        title: 'Error',
        description: 'Password must be at least 8 characters',
        variant: 'destructive',
      });
      return;
    }

    if (formData.password !== formData.confirm_password) {
      toast({
        title: 'Error',
        description: 'Passwords do not match',
        variant: 'destructive',
      });
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(API_ENDPOINTS.invitationAccept(token!), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          first_name: formData.first_name,
          last_name: formData.last_name,
          password: formData.password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to accept invitation');
      }

      const data = await response.json();

      // Save tokens
      localStorage.setItem('mongo_access_token', data.tokens.access_token);
      localStorage.setItem('mongo_refresh_token', data.tokens.refresh_token);

      toast({
        title: 'Success',
        description: 'Account created successfully! Redirecting...',
      });

      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);

    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create account',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-blue-500 mb-4" />
            <p className="text-muted-foreground">Loading invitation...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !invitation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </div>
            <CardTitle className="text-center">Invalid Invitation</CardTitle>
            <CardDescription className="text-center">
              {error || 'This invitation link is invalid or has expired.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => navigate('/login')}
              className="w-full"
            >
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!invitation.is_valid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="h-16 w-16 rounded-full bg-orange-100 flex items-center justify-center">
                <XCircle className="h-8 w-8 text-orange-500" />
              </div>
            </div>
            <CardTitle className="text-center">Invitation {invitation.status}</CardTitle>
            <CardDescription className="text-center">
              {invitation.is_expired
                ? `This invitation expired on ${format(new Date(invitation.expires_at), 'MMMM d, yyyy')}`
                : `This invitation has already been ${invitation.status}.`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => navigate('/login')}
              className="w-full"
            >
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
              <Mail className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <CardTitle className="text-center">You're Invited!</CardTitle>
          <CardDescription className="text-center">
            {invitation.invited_by} has invited you to join KasaAI
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Invitation Details */}
          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{invitation.email}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span>Role: </span>
              <Badge variant="outline">{invitation.role}</Badge>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span>Expires: {format(new Date(invitation.expires_at), 'MMMM d, yyyy')}</span>
            </div>
            {invitation.message && (
              <Alert>
                <AlertDescription>
                  "{invitation.message}"
                </AlertDescription>
              </Alert>
            )}
            <Alert>
              <Gift className="h-4 w-4" />
              <AlertDescription>
                You'll be automatically enrolled in our affiliate program!
              </AlertDescription>
            </Alert>
          </div>

          {/* Sign Up Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  placeholder="John"
                  required
                />
              </div>
              <div>
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  placeholder="Doe"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="At least 8 characters"
                  className="pl-10"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="confirm_password"
                  type="password"
                  value={formData.confirm_password}
                  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                  placeholder="Confirm your password"
                  className="pl-10"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Accept & Create Account
                </>
              )}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Button
              variant="link"
              className="p-0 h-auto"
              onClick={() => navigate('/login')}
            >
              Sign in
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
