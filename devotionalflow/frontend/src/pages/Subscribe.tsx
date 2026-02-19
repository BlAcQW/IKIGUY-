/**
 * Subscribe Page
 * 
 * Dedicated page for subscribing to daily devotionals via email, WhatsApp, or Facebook group.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, MessageCircle, Facebook, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { useAuth } from "@/contexts/AuthContext";

export default function Subscribe() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    whatsapp: "",
    facebook_group: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!formData.name.trim()) {
      setError("Please enter your name");
      setIsLoading(false);
      return;
    }

    if (!formData.email && !formData.whatsapp && !formData.facebook_group) {
      setError("Please select at least one subscription method (email, WhatsApp, or Facebook group)");
      setIsLoading(false);
      return;
    }

    try {
      await apiClient.subscribeToDevotionals({
        name: formData.name.trim(),
        email: formData.email.trim() || undefined,
        whatsapp: formData.whatsapp.trim() || undefined,
        facebook_group: formData.facebook_group,
      });

      setIsSuccess(true);
      
      toast({
        title: "Subscription successful!",
        description: formData.email 
          ? "Please check your email to verify your subscription."
          : formData.whatsapp
          ? "Please check your WhatsApp for verification instructions."
          : "Your subscription preferences have been saved.",
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
      <div className="min-h-screen bg-background">
        <MainNavigation />
        <div className="container mx-auto px-4 py-16 max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-teal-50 to-navy-50 dark:from-teal-950/20 dark:to-navy-950/20 rounded-2xl p-8 border border-teal-200/50 dark:border-teal-800/50 text-center space-y-6"
          >
            <div className="flex justify-center">
              <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-4">
                <CheckCircle2 className="w-12 h-12 text-teal-600 dark:text-teal-400" />
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-navy-900 dark:text-navy-100 mb-4">
                Subscription Successful!
              </h1>
              <p className="text-navy-700 dark:text-navy-300 text-lg">
                {formData.email && (
                  <>We've sent a verification email to <strong>{formData.email}</strong>. Please check your inbox and click the verification link.</>
                )}
                {formData.whatsapp && !formData.email && (
                  <>We've sent a verification message to <strong>{formData.whatsapp}</strong>. Please check your WhatsApp.</>
                )}
                {formData.facebook_group && !formData.email && !formData.whatsapp && (
                  <>Your Facebook group preference has been saved. You can join the group manually.</>
                )}
              </p>
            </div>
            <div className="pt-4">
              <Button
                onClick={() => {
                  setIsSuccess(false);
                  setFormData({
                    name: user?.name || "",
                    email: user?.email || "",
                    whatsapp: "",
                    facebook_group: false,
                  });
                }}
                variant="outline"
              >
                Subscribe Another Email/Number
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />
      <div className="container mx-auto px-4 py-16 max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-teal-50 to-navy-50 dark:from-teal-950/20 dark:to-navy-950/20 rounded-2xl p-8 border border-teal-200/50 dark:border-teal-800/50"
        >
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-navy-900 dark:text-navy-100 mb-3">
              Subscribe to Daily Devotionals
            </h1>
            <p className="text-navy-700 dark:text-navy-300">
              Choose how you'd like to receive daily spiritual content
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="name">Your Name *</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="h-12"
                required
                disabled={isLoading}
              />
            </div>

            {/* Email Subscription */}
            <div className="space-y-4 p-4 border border-teal-200/50 dark:border-teal-800/50 rounded-lg bg-white/50 dark:bg-navy-900/20">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-2">
                  <Mail className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                </div>
                <div>
                  <Label htmlFor="email" className="text-base font-semibold">Email Subscription</Label>
                  <p className="text-sm text-muted-foreground">Receive devotionals in your inbox</p>
                </div>
              </div>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="h-12"
                disabled={isLoading}
              />
            </div>

            {/* WhatsApp Subscription */}
            <div className="space-y-4 p-4 border border-teal-200/50 dark:border-teal-800/50 rounded-lg bg-white/50 dark:bg-navy-900/20">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-2">
                  <MessageCircle className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                </div>
                <div>
                  <Label htmlFor="whatsapp" className="text-base font-semibold">WhatsApp Subscription</Label>
                  <p className="text-sm text-muted-foreground">Receive devotionals via WhatsApp</p>
                </div>
              </div>
              <Input
                id="whatsapp"
                type="tel"
                placeholder="+233123456789"
                value={formData.whatsapp}
                onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
                className="h-12"
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Include country code (e.g., +233 for Ghana, +1 for USA)
              </p>
            </div>

            {/* Facebook Group */}
            <div className="space-y-4 p-4 border border-teal-200/50 dark:border-teal-800/50 rounded-lg bg-white/50 dark:bg-navy-900/20">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-2 mt-1">
                  <Facebook className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Checkbox
                      id="facebook_group"
                      checked={formData.facebook_group}
                      onCheckedChange={(checked) =>
                        setFormData({ ...formData, facebook_group: checked as boolean })
                      }
                      disabled={isLoading}
                    />
                    <Label htmlFor="facebook_group" className="text-base font-semibold cursor-pointer">
                      Join Facebook Group
                    </Label>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Join our Facebook community to discuss devotionals with others
                  </p>
                </div>
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
                  Subscribe Now
                </>
              )}
            </Button>

            <p className="text-xs text-center text-navy-600 dark:text-navy-400">
              By subscribing, you agree to receive daily devotionals. 
              You can unsubscribe at any time using the link in your emails or messages.
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  );
}

