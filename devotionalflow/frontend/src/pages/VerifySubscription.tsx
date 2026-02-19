/**
 * Verify Subscription Page
 * 
 * Handles email and WhatsApp subscription verification via token.
 */

import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient } from "@/lib/api";
import { MainNavigation } from "@/components/navigation/MainNavigation";

export default function VerifySubscription() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState<string>("");
  
  const subscriptionId = searchParams.get("id");
  const token = searchParams.get("token");
  const channel = searchParams.get("channel") || "email";

  useEffect(() => {
    const verify = async () => {
      if (!subscriptionId || !token) {
        setStatus("error");
        setMessage("Missing verification token or subscription ID");
        return;
      }

      try {
        const result = await apiClient.verifySubscription(subscriptionId, channel, token);
        
        if (result.success) {
          setStatus("success");
          setMessage(result.message || `${channel.charAt(0).toUpperCase() + channel.slice(1)} verified successfully!`);
        } else {
          setStatus("error");
          setMessage(result.message || "Verification failed");
        }
      } catch (err: any) {
        setStatus("error");
        setMessage(err.response?.data?.detail || "Failed to verify subscription. The link may be invalid or expired.");
      }
    };

    verify();
  }, [subscriptionId, token, channel]);

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />
      <div className="container mx-auto px-4 py-16 max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-teal-50 to-navy-50 dark:from-teal-950/20 dark:to-navy-950/20 rounded-2xl p-8 border border-teal-200/50 dark:border-teal-800/50 text-center space-y-6"
        >
          {status === "loading" && (
            <>
              <div className="flex justify-center">
                <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-4">
                  <Loader2 className="w-12 h-12 text-teal-600 dark:text-teal-400 animate-spin" />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-navy-900 dark:text-navy-100 mb-4">
                  Verifying Subscription...
                </h1>
                <p className="text-navy-700 dark:text-navy-300">
                  Please wait while we verify your subscription.
                </p>
              </div>
            </>
          )}

          {status === "success" && (
            <>
              <div className="flex justify-center">
                <div className="rounded-full bg-teal-100 dark:bg-teal-900/30 p-4">
                  <CheckCircle2 className="w-12 h-12 text-teal-600 dark:text-teal-400" />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-navy-900 dark:text-navy-100 mb-4">
                  Subscription Verified! ✅
                </h1>
                <p className="text-navy-700 dark:text-navy-300 text-lg mb-4">
                  {message}
                </p>
                <p className="text-navy-600 dark:text-navy-400">
                  You'll now receive daily devotionals via {channel === "email" ? "email" : "WhatsApp"}.
                </p>
              </div>
              <div className="pt-4 space-y-3">
                <Button
                  onClick={() => navigate("/")}
                  className="w-full bg-teal-600 hover:bg-teal-700"
                >
                  Go to Homepage
                </Button>
                <Button
                  onClick={() => navigate("/today")}
                  variant="outline"
                  className="w-full"
                >
                  Read Today's Devotional
                </Button>
              </div>
            </>
          )}

          {status === "error" && (
            <>
              <div className="flex justify-center">
                <div className="rounded-full bg-red-100 dark:bg-red-900/30 p-4">
                  <XCircle className="w-12 h-12 text-red-600 dark:text-red-400" />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-navy-900 dark:text-navy-100 mb-4">
                  Verification Failed
                </h1>
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{message}</AlertDescription>
                </Alert>
                <p className="text-navy-600 dark:text-navy-400 mb-4">
                  The verification link may be invalid or expired. Please try subscribing again.
                </p>
              </div>
              <div className="pt-4 space-y-3">
                <Button
                  onClick={() => navigate("/subscribe")}
                  className="w-full bg-teal-600 hover:bg-teal-700"
                >
                  Subscribe Again
                </Button>
                <Button
                  onClick={() => navigate("/")}
                  variant="outline"
                  className="w-full"
                >
                  Go to Homepage
                </Button>
              </div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}

