import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Loader2, Lock, Mail, Users } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LeadForm } from "@/components/LeadForm";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { signIn, user } = useAuth();
  const { toast } = useToast();

  // Redirect if already logged in
  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { error } = await signIn(email, password);

      if (error) {
        toast({
          title: "Error",
          description: error.message || "Failed to sign in",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Success",
          description: "Welcome back!",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-secondary p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <img src="/logo.png" alt="Diaserve Properties" className="h-36 w-auto" />
          </div>
          <p className="text-muted-foreground">Premier Real Estate Management Portal</p>
        </div>

        <Card className="border-border/50 shadow-2xl overflow-hidden glass">
          <div className="h-2 bg-gradient-to-r from-primary via-accent to-secondary" />
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Staff Login</CardTitle>
            <CardDescription className="text-center">
              Access the administrative dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@estateflow.local"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 focus-visible:ring-primary h-12"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 focus-visible:ring-primary h-12"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full h-12 text-lg font-bold" variant="gradient" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Authenticating...
                  </>
                ) : (
                  "Login"
                )}
              </Button>
            </form>

            <div className="mt-8 pt-6 border-t border-border text-center text-sm text-muted-foreground">
              <p className="font-semibold mb-2">Internal Staff Only</p>
              <div className="bg-muted/50 p-4 rounded-xl border border-border/50 space-y-1 font-mono text-xs">
                <p>Email: admin@estateflow.local</p>
                <p>Pass: Admin@123!</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="text-center">
          <Link to="/properties" className="text-sm font-medium text-primary hover:underline flex items-center justify-center gap-2">
            <Users className="h-4 w-4" />
            Browse as Client
          </Link>
        </div>
      </div>
    </div>
  );
}
