import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, Mail, CheckCircle, AlertCircle } from 'lucide-react';

const Auth = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const { signIn, signUp, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      console.log('[Auth Page] User detected, redirecting to home', {
        userId: user.id,
        email: user.email
      });
      navigate('/');
    }
  }, [user, navigate]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[Auth Page] Sign in form submitted', {
      email,
      hasPassword: !!password,
      timestamp: new Date().toISOString()
    });
    
    setIsLoading(true);

    const { error } = await signIn(email, password);
    
    if (error) {
      console.error('[Auth Page] Sign in failed:', {
        message: error.message,
        email,
        errorCode: error.status
      });
      
      toast({
        title: "Error signing in",
        description: error.message,
        variant: "destructive",
      });
    } else {
      console.log('[Auth Page] Sign in successful, showing success message');
      toast({
        title: "Welcome back!",
        description: "You've been signed in successfully.",
      });
    }
    
    setIsLoading(false);
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[Auth Page] Sign up form submitted', {
      email,
      fullName,
      company,
      phone,
      hasPassword: !!password,
      timestamp: new Date().toISOString()
    });
    
    setIsLoading(true);

    const { error } = await signUp(email, password, {
      full_name: fullName,
      company_name: company,
      phone
    });
    
    if (error) {
      console.error('[Auth Page] Sign up failed:', {
        message: error.message,
        email,
        errorCode: error.status
      });
      
      toast({
        title: "Error creating account",
        description: error.message,
        variant: "destructive",
      });
    } else {
      console.log('[Auth Page] Sign up successful, showing confirmation message');
      setEmailVerificationSent(true);
      toast({
        title: "Account created!",
        description: "Please check your email to verify your account.",
      });
    }
    
    setIsLoading(false);
  };

  const handleResendVerification = async () => {
    setIsLoading(true);
    
    try {
      const { error } = await signUp(email, password, {
        full_name: fullName,
        company_name: company,
        phone
      });
      
      if (error) {
        toast({
          title: "Error resending verification",
          description: error.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Verification email sent!",
          description: "Please check your email again.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to resend verification email.",
        variant: "destructive",
      });
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-tech-blue to-tech-blue-light bg-clip-text text-transparent">
            AI Labs Africa
          </h1>
          <p className="text-muted-foreground mt-2">
            Access your AI assistant platform
          </p>
        </div>

        {emailVerificationSent ? (
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-blue-500" />
                Verify Your Email
              </CardTitle>
              <CardDescription>
                We've sent a verification link to your email address
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <p className="text-sm text-muted-foreground">
                  Please check your email at <strong>{email}</strong> and click the verification link to activate your account.
                </p>
              </div>
              
              <div className="space-y-2">
                <Button 
                  onClick={handleResendVerification}
                  variant="outline"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Resend Verification Email
                </Button>
                
                <Button 
                  onClick={() => setEmailVerificationSent(false)}
                  variant="ghost"
                  className="w-full"
                >
                  Back to Sign Up
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              Sign in to your account or create a new one
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="signin" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="signin">Sign In</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>
              
              <TabsContent value="signin">
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signin-email">Email</Label>
                    <Input
                      id="signin-email"
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signin-password">Password</Label>
                    <Input
                      id="signin-password"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isLoading}
                  >
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Sign In
                  </Button>
                  
                  <div className="text-center">
                    <Button asChild variant="link" size="sm">
                      <Link to="/forgot-password">
                        Forgot your password?
                      </Link>
                    </Button>
                  </div>
                </form>
              </TabsContent>

              <TabsContent value="signup">
                <form onSubmit={handleSignUp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-name">Full Name</Label>
                    <Input
                      id="signup-name"
                      type="text"
                      placeholder="Enter your full name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-company">Company (Optional)</Label>
                    <Input
                      id="signup-company"
                      type="text"
                      placeholder="Enter your company name"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-phone">Phone Number</Label>
                    <Input
                      id="signup-phone"
                      type="tel"
                      placeholder="+233XXXXXXXXX"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input
                      id="signup-email"
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input
                      id="signup-password"
                      type="password"
                      placeholder="Create a password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isLoading}
                  >
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Create Account
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        )}
      </div>
    </div>
  );
};

export default Auth;