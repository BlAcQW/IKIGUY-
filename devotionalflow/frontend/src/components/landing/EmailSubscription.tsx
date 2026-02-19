/**
 * Email Subscription Component
 * 
 * Allows visitors to subscribe to daily devotionals via email.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function EmailSubscription() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!email.trim()) {
      setError("Please enter your email address");
      setIsLoading(false);
      return;
    }

    if (!name.trim()) {
      setError("Please enter your name");
      setIsLoading(false);
      return;
    }

    try {
      await apiClient.subscribeToDevotionals({
        name: name.trim(),
        email: email.trim(),
      });

      setIsSuccess(true);
      setEmail("");
      setName("");
      
      toast({
        title: "Subscription successful!",
        description: "Please check your email to verify your subscription.",
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || "Failed to subscribe. Please try again.";
      setError(errorMessage);
      
      toast({
        title: "Subscription failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-teal-50 to-navy-50 dark:from-teal-950/20 dark:to-navy-950/20 rounded-2xl p-8 border border-teal-200/50 dark:border-teal-800/50"
      >
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-3">
              <CheckCircle2 className="w-8 h-8 text-teal-600 dark:text-teal-400" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-navy-900 dark:text-navy-100 mb-2">
              Check Your Email!
            </h3>
            <p className="text-navy-700 dark:text-navy-300">
              We've sent a verification email to <strong>{email}</strong>. 
              Please click the link in the email to confirm your subscription.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              setIsSuccess(false);
              setEmail("");
              setName("");
            }}
            className="mt-4"
          >
            Subscribe Another Email
          </Button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-teal-50 to-navy-50 dark:from-teal-950/20 dark:to-navy-950/20 rounded-2xl p-8 border border-teal-200/50 dark:border-teal-800/50"
    >
      <div className="text-center mb-6">
        <div className="flex justify-center mb-4">
          <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-3">
            <Mail className="w-8 h-8 text-teal-600 dark:text-teal-400" />
          </div>
        </div>
        <h3 className="text-2xl font-bold text-navy-900 dark:text-navy-100 mb-2">
          Get Daily Devotionals
        </h3>
        <p className="text-navy-700 dark:text-navy-300">
          Subscribe to receive daily spiritual content delivered straight to your inbox
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="subscription-name">Your Name</Label>
          <Input
            id="subscription-name"
            type="text"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="h-12"
            required
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subscription-email">Email Address</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              id="subscription-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="pl-10 h-12"
              required
              disabled={isLoading}
              autoComplete="email"
            />
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-12 bg-teal-600 hover:bg-teal-700 text-white"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Subscribing...
            </>
          ) : (
            <>
              <Mail className="mr-2 h-4 w-4" />
              Subscribe via Email
            </>
          )}
        </Button>

        <p className="text-xs text-center text-navy-600 dark:text-navy-400">
          By subscribing, you agree to receive daily devotionals. 
          You can unsubscribe at any time.
        </p>
      </form>
    </motion.div>
  );
}

