import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, Mail, Lock, User, ArrowRight, Eye, EyeOff, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api";

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [isResetting, setIsResetting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "user" as const, // Default role for all signups
  });

  const navigate = useNavigate();
  const { toast } = useToast();
  const { login, signup } = useAuth();

  const validateForm = (): boolean => {
    setError(null);

    if (!isLogin && !formData.name.trim()) {
      setError("Please enter your full name");
      return false;
    }

    if (!formData.email.trim()) {
      setError("Please enter your email address");
      return false;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }

    if (!formData.password) {
      setError("Please enter your password");
      return false;
    }

    if (!isLogin && formData.password.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (isLogin) {
        // Login
        await login(formData.email, formData.password);

        toast({
          title: "Welcome back!",
          description: "You've been signed in successfully.",
        });

        // Navigate based on user role (will be determined by the API response)
        // The AuthContext will have the user object with role after login
        setTimeout(() => {
          navigate("/feed");
        }, 100);
      } else {
        // Signup
        await signup({
          email: formData.email,
          password: formData.password,
          name: formData.name,
          role: formData.role,
        });

        toast({
          title: "Account created!",
          description: "Welcome to FreshManna. You can now start your spiritual journey.",
        });

        // All public signups go to feed
        navigate("/feed");
      }
    } catch (err: any) {
      console.error('Auth error:', err);

      // Parse error message
      let errorMessage = "An unexpected error occurred. Please try again.";

      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      // Handle specific error cases
      if (errorMessage.includes("Invalid credentials") || errorMessage.includes("401")) {
        errorMessage = "Invalid email or password. Please try again.";
      } else if (errorMessage.includes("already exists") || errorMessage.includes("409")) {
        errorMessage = "An account with this email already exists.";
      } else if (errorMessage.includes("Network Error") || errorMessage.includes("Failed to fetch")) {
        errorMessage = "Connection error. Please check your internet and try again.";
      }

      setError(errorMessage);
      toast({
        title: isLogin ? "Sign in failed" : "Sign up failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    // Reset form when switching modes
    if (isLogin) {
      // Switching to signup - keep email and password if entered
      setFormData({
        ...formData,
        name: "",
      });
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!resetEmail.trim()) {
      toast({
        title: "Email required",
        description: "Please enter your email address",
        variant: "destructive",
      });
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(resetEmail)) {
      toast({
        title: "Invalid email",
        description: "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    setIsResetting(true);

    try {
      await apiClient.forgotPassword(resetEmail);

      toast({
        title: "Email sent!",
        description: "If an account exists with this email, you'll receive password reset instructions shortly.",
      });

      setShowForgotPassword(false);
      setResetEmail("");
    } catch (err: any) {
      console.error('Password reset error:', err);

      toast({
        title: "Error",
        description: "Failed to send reset email. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-spiritual flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <a href="/" className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center shadow-gold">
              <BookOpen className="w-5 h-5 text-secondary-foreground" />
            </div>
            <span className="font-serif text-xl font-semibold text-foreground">
              FreshManna
            </span>
          </a>

          {/* Header */}
          <div className="mb-8">
            <h1 className="font-serif text-3xl font-bold text-foreground mb-2">
              {isLogin ? "Welcome back" : "Join FreshManna"}
            </h1>
            <p className="text-muted-foreground">
              {isLogin
                ? "Sign in to continue your spiritual journey"
                : "Start growing in faith with daily devotionals and community"}
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6"
            >
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Smith"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="pl-10 h-12"
                    required
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="pl-10 h-12"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="pl-10 pr-10 h-12"
                  required
                  minLength={8}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
              {!isLogin && (
                <p className="text-xs text-muted-foreground">
                  Must be at least 8 characters long
                </p>
              )}
            </div>

            {isLogin && (
              <div className="flex items-center justify-end">
                <a
                  href="#"
                  className="text-sm text-secondary hover:underline"
                  onClick={(e) => {
                    e.preventDefault();
                    setShowForgotPassword(true);
                  }}
                >
                  Forgot password?
                </a>
              </div>
            )}

            <Button
              type="submit"
              variant="hero"
              size="lg"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-5 h-5 border-2 border-secondary-foreground/30 border-t-secondary-foreground rounded-full animate-spin" />
                  {isLogin ? "Signing in..." : "Creating account..."}
                </span>
              ) : (
                <>
                  {isLogin ? "Sign In" : "Create Account"}
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </Button>
          </form>

          {/* Toggle */}
          <p className="mt-8 text-center text-muted-foreground">
            {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
            <button
              onClick={handleToggleMode}
              className="text-secondary font-medium hover:underline"
              disabled={isLoading}
            >
              {isLogin ? "Sign up" : "Sign in"}
            </button>
          </p>

          {/* Demo Accounts */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-8 p-4 bg-muted/50 rounded-xl border border-border">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Demo Accounts (Development Only)
              </p>
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>User: user@example.com / password123</p>
                <p>Admin: admin@ailabsafrica.com / admin123</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Right Side - Visual */}
      <div className="hidden lg:flex flex-1 bg-primary items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-lg text-center"
        >
          <div className="w-24 h-24 mx-auto mb-8 rounded-2xl bg-primary-foreground/20 flex items-center justify-center">
            <BookOpen className="w-12 h-12 text-primary-foreground" />
          </div>
          <h2 className="font-serif text-3xl font-bold text-primary-foreground mb-4">
            Grow Your Faith Daily
          </h2>
          <p className="text-primary-foreground/90 leading-relaxed">
            Join 150,000+ believers experiencing spiritual growth through daily devotionals,
            deep scripture study, and vibrant community.
          </p>
          <div className="mt-12 grid grid-cols-3 gap-6 text-center">
            <div>
              <div className="font-serif text-2xl font-bold text-primary-foreground">150K+</div>
              <div className="text-sm text-primary-foreground/70">Believers</div>
            </div>
            <div>
              <div className="font-serif text-2xl font-bold text-primary-foreground">1M+</div>
              <div className="text-sm text-primary-foreground/70">Devotionals</div>
            </div>
            <div>
              <div className="font-serif text-2xl font-bold text-primary-foreground">500+</div>
              <div className="text-sm text-primary-foreground/70">Groups</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Reset your password</DialogTitle>
            <DialogDescription>
              Enter your email address and we'll send you instructions to reset your password.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleForgotPassword} className="space-y-4">
            <div>
              <Label htmlFor="reset-email">Email address</Label>
              <div className="relative mt-2">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="reset-email"
                  type="email"
                  placeholder="your@email.com"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowForgotPassword(false);
                  setResetEmail("");
                }}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="hero"
                disabled={isResetting}
                className="flex-1"
              >
                {isResetting ? "Sending..." : "Send Reset Link"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
