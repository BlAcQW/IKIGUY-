/**
 * Stripe Payment Form Component
 *
 * Handles Stripe payment processing with Elements.
 * Note: Requires @stripe/stripe-js and @stripe/react-stripe-js packages.
 */

import { useState, useEffect } from "react";
import { Loader2, CreditCard, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { formatPaymentAmount } from "@/lib/api/payment-api";

interface StripePaymentFormProps {
  clientSecret: string;
  amount: number;
  currency: string;
  onSuccess: () => void;
  onError: (error: string) => void;
  className?: string;
}

export function StripePaymentForm({
  clientSecret,
  amount,
  currency,
  onSuccess,
  onError,
  className,
}: StripePaymentFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stripeLoaded, setStripeLoaded] = useState(false);

  // Placeholder for Stripe Elements
  // In production, you would use:
  // import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
  // import { loadStripe } from '@stripe/stripe-js';

  useEffect(() => {
    // Simulate Stripe loading
    // In production: loadStripe(publishableKey)
    const timer = setTimeout(() => setStripeLoaded(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // In production, use Stripe Elements:
      // const stripe = useStripe();
      // const elements = useElements();
      // const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
      //   payment_method: {
      //     card: elements.getElement(CardElement),
      //   }
      // });

      // For now, show instructions
      setError("Stripe Elements not configured. Add @stripe/stripe-js and @stripe/react-stripe-js packages.");

      // Simulate success for demo
      setTimeout(() => {
        setIsLoading(false);
        // onSuccess(); // Uncomment when Stripe is configured
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Payment failed");
      onError(err.message);
      setIsLoading(false);
    }
  };

  if (!stripeLoaded) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          <CardTitle>Card Payment</CardTitle>
        </div>
        <CardDescription>
          Enter your card details to complete the payment of{" "}
          <span className="font-semibold">{formatPaymentAmount(amount, currency)}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Stripe Elements Placeholder */}
          <div className="space-y-4">
            {/* In production, replace with: <CardElement /> */}
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center space-y-2">
              <CreditCard className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-sm font-medium">Stripe Card Element</p>
              <p className="text-xs text-muted-foreground">
                Install @stripe/stripe-js and @stripe/react-stripe-js
              </p>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                npm install @stripe/stripe-js @stripe/react-stripe-js
              </code>
            </div>

            {/* Temporary placeholder fields */}
            <div className="space-y-3 opacity-50">
              <div>
                <Label htmlFor="card-number">Card Number</Label>
                <Input
                  id="card-number"
                  placeholder="4242 4242 4242 4242"
                  disabled
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="expiry">Expiry</Label>
                  <Input
                    id="expiry"
                    placeholder="MM/YY"
                    disabled
                  />
                </div>
                <div>
                  <Label htmlFor="cvc">CVC</Label>
                  <Input
                    id="cvc"
                    placeholder="123"
                    disabled
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Security Notice */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Lock className="h-3 w-3" />
            <span>Your payment is secured by Stripe</span>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Lock className="mr-2 h-4 w-4" />
                Pay {formatPaymentAmount(amount, currency)}
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

/**
 * Installation Instructions Component
 */
export function StripeSetupInstructions() {
  return (
    <Card className="border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20">
      <CardHeader>
        <CardTitle className="text-yellow-900 dark:text-yellow-100">
          Stripe Integration Setup Required
        </CardTitle>
        <CardDescription className="text-yellow-800 dark:text-yellow-200">
          To enable card payments, install the Stripe packages and configure your publishable key
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm font-medium mb-2">1. Install packages:</p>
          <code className="block bg-black text-white p-3 rounded text-sm">
            npm install @stripe/stripe-js @stripe/react-stripe-js
          </code>
        </div>

        <div>
          <p className="text-sm font-medium mb-2">2. Add to .env:</p>
          <code className="block bg-black text-white p-3 rounded text-sm">
            VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
          </code>
        </div>

        <div>
          <p className="text-sm font-medium mb-2">3. Update StripePaymentForm.tsx:</p>
          <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
            <li>Import Elements, CardElement from @stripe/react-stripe-js</li>
            <li>Wrap component with Elements provider</li>
            <li>Replace placeholder with CardElement</li>
            <li>Implement stripe.confirmCardPayment()</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
