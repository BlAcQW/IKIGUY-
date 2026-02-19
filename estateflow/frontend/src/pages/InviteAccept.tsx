/**
 * Invitation Acceptance Page
 *
 * Allows users to accept invitations and create their account.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/lib/supabase";
import { API_BASE_URL } from "@/lib/api-config";
import {
  Building2,
  Mail,
  User,
  Shield,
  CheckCircle2,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react";

interface InvitationDetails {
  token: string;
  email: string;
  name: string | null;
  role: string;
  organization_id: string;
  organization_name: string;
  expires_at: string;
  valid: boolean;
}

export default function InviteAccept() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);

  // Load invitation details
  useEffect(() => {
    loadInvitation();
  }, [token]);

  const loadInvitation = async () => {
    if (!token) {
      setError("Invalid invitation link");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/users/invitations/${token}/validate`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Invalid invitation");
      }

      const data: InvitationDetails = await response.json();
      setInvitation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load invitation");
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!password || password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (!token || !invitation) {
      setError("Invalid invitation");
      return;
    }

    try {
      setAccepting(true);
      setError(null);

      // Accept invitation (creates user account)
      const response = await fetch(
        `${API_BASE_URL}/api/v1/users/invitations/${token}/accept`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ password }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to accept invitation");
      }

      const result = await response.json();

      // Show success message
      setSuccess(true);

      // Auto-login after 2 seconds
      setTimeout(async () => {
        try {
          // Login with the new credentials
          const { error: loginError } = await supabase.auth.signInWithPassword({
            email: invitation.email,
            password: password,
          });

          if (loginError) {
            console.error("Auto-login failed:", loginError);
            // Redirect to login page if auto-login fails
            navigate("/login");
          } else {
            // Redirect to dashboard on successful login
            navigate("/");
          }
        } catch (err) {
          console.error("Auto-login error:", err);
          navigate("/login");
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to accept invitation");
    } finally {
      setAccepting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/5">
        <Card className="w-full max-w-md">
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state (invalid/expired invitation)
  if (error && !invitation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/5 p-4">
        <Card className="w-full max-w-md border-destructive/50">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="rounded-full bg-destructive/10 p-3">
                <XCircle className="h-12 w-12 text-destructive" />
              </div>
            </div>
            <CardTitle className="text-center">Invalid Invitation</CardTitle>
            <CardDescription className="text-center">
              {error}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground text-center mb-6">
              This invitation link may have expired or has already been used.
              Please contact your administrator for a new invitation.
            </p>
            <Button
              onClick={() => navigate("/login")}
              className="w-full"
              variant="outline"
            >
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/5 p-4">
        <Card className="w-full max-w-md border-success/50">
          <CardHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="rounded-full bg-success/10 p-3">
                <CheckCircle2 className="h-12 w-12 text-success" />
              </div>
            </div>
            <CardTitle className="text-center">Welcome to Diaserve Properties!</CardTitle>
            <CardDescription className="text-center">
              Your account has been created successfully
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground text-center mb-4">
              Logging you in automatically...
            </p>
            <div className="flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main invitation acceptance form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-accent/5 p-4">
      <Card className="w-full max-w-md shadow-premium">
        <CardHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="rounded-full bg-gradient-to-br from-primary to-secondary p-3">
              <Mail className="h-12 w-12 text-white" />
            </div>
          </div>
          <CardTitle className="text-center text-2xl">
            You're Invited to Diaserve Properties
          </CardTitle>
          <CardDescription className="text-center">
            Create your account to join {invitation?.organization_name}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Invitation Details */}
          <div className="space-y-3 p-4 bg-muted/50 rounded-lg border">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Email:</span>
              <span className="font-medium">{invitation?.email}</span>
            </div>

            {invitation?.name && (
              <div className="flex items-center gap-2 text-sm">
                <User className="h-4 w-4 text-primary" />
                <span className="text-muted-foreground">Name:</span>
                <span className="font-medium">{invitation.name}</span>
              </div>
            )}

            <div className="flex items-center gap-2 text-sm">
              <Building2 className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Organization:</span>
              <span className="font-medium">{invitation?.organization_name}</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Shield className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Role:</span>
              <Badge variant="soft" className="capitalize">
                {invitation?.role}
              </Badge>
            </div>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Password Form */}
          <form onSubmit={handleAccept} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">Create Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password (min. 8 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={accepting}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                disabled={accepting}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={accepting}
              size="lg"
            >
              {accepting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                "Accept Invitation & Create Account"
              )}
            </Button>
          </form>

          <p className="text-xs text-center text-muted-foreground">
            By creating an account, you agree to Diaserve Properties' Terms of Service
            and Privacy Policy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
