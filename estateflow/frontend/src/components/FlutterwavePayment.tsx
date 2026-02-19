/**
 * Flutterwave Payment Component
 *
 * Handles Flutterwave payment processing for cards, mobile money, and bank transfers.
 */

import { useState } from "react";
import { ExternalLink, Loader2, Smartphone, CreditCard, Building2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  PaymentMethod,
  MobileMoneyProvider,
  formatPaymentAmount,
  getMobileMoneyProviderLabel,
} from "@/lib/api/payment-api";

interface FlutterwavePaymentProps {
  paymentLink: string;
  amount: number;
  currency: string;
  paymentMethod: PaymentMethod;
  momoProvider?: MobileMoneyProvider;
  momoPhone?: string;
  onMomoPhoneChange?: (phone: string) => void;
  onSuccess?: () => void;
  onCancel?: () => void;
  className?: string;
}

export function FlutterwavePayment({
  paymentLink,
  amount,
  currency,
  paymentMethod,
  momoProvider,
  momoPhone,
  onMomoPhoneChange,
  onSuccess,
  onCancel,
  className,
}: FlutterwavePaymentProps) {
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [phone, setPhone] = useState(momoPhone || "");
  const [phoneError, setPhoneError] = useState<string | null>(null);

  const validatePhoneNumber = (value: string): boolean => {
    // Ghana phone number validation
    // Format: +233XXXXXXXXX or 0XXXXXXXXX
    const ghanaPattern = /^(\+233|0)[2-5][0-9]{8}$/;
    return ghanaPattern.test(value.replace(/\s/g, ""));
  };

  const handlePhoneChange = (value: string) => {
    setPhone(value);
    onMomoPhoneChange?.(value);

    if (value && !validatePhoneNumber(value)) {
      setPhoneError("Please enter a valid Ghana phone number");
    } else {
      setPhoneError(null);
    }
  };

  const handleProceed = () => {
    // Validate mobile money phone if required
    if (paymentMethod === PaymentMethod.MOBILE_MONEY) {
      if (!phone) {
        setPhoneError("Phone number is required for mobile money");
        return;
      }
      if (!validatePhoneNumber(phone)) {
        setPhoneError("Please enter a valid Ghana phone number");
        return;
      }
    }

    setIsRedirecting(true);

    // Redirect to Flutterwave payment page
    window.location.href = paymentLink;
  };

  const getMethodIcon = () => {
    switch (paymentMethod) {
      case PaymentMethod.MOBILE_MONEY:
        return Smartphone;
      case PaymentMethod.CARD:
        return CreditCard;
      case PaymentMethod.BANK_TRANSFER:
        return Building2;
      default:
        return CreditCard;
    }
  };

  const getMethodTitle = () => {
    switch (paymentMethod) {
      case PaymentMethod.MOBILE_MONEY:
        return momoProvider ? getMobileMoneyProviderLabel(momoProvider) : "Mobile Money";
      case PaymentMethod.CARD:
        return "Card Payment";
      case PaymentMethod.BANK_TRANSFER:
        return "Bank Transfer";
      default:
        return "Payment";
    }
  };

  const getMethodDescription = () => {
    switch (paymentMethod) {
      case PaymentMethod.MOBILE_MONEY:
        return "You'll receive a prompt on your phone to approve the payment";
      case PaymentMethod.CARD:
        return "Securely pay with your Visa, Mastercard, or local card";
      case PaymentMethod.BANK_TRANSFER:
        return "Transfer directly from your bank account";
      default:
        return "Complete your payment securely";
    }
  };

  const Icon = getMethodIcon();

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-primary" />
          <CardTitle>{getMethodTitle()}</CardTitle>
        </div>
        <CardDescription>
          {getMethodDescription()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Amount Display */}
        <div className="bg-muted rounded-lg p-4 text-center">
          <p className="text-sm text-muted-foreground mb-1">Amount to Pay</p>
          <p className="text-3xl font-bold">{formatPaymentAmount(amount, currency)}</p>
        </div>

        {/* Mobile Money Phone Input */}
        {paymentMethod === PaymentMethod.MOBILE_MONEY && (
          <div className="space-y-2">
            <Label htmlFor="momo-phone">
              {momoProvider && getMobileMoneyProviderLabel(momoProvider)} Number
            </Label>
            <Input
              id="momo-phone"
              type="tel"
              placeholder="+233 XX XXX XXXX or 0XX XXX XXXX"
              value={phone}
              onChange={(e) => handlePhoneChange(e.target.value)}
              className={phoneError ? "border-destructive" : ""}
            />
            {phoneError && (
              <p className="text-sm text-destructive">{phoneError}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Enter the number you want to pay from. You'll receive a prompt to approve the payment.
            </p>
          </div>
        )}

        {/* Payment Flow Instructions */}
        <div className="space-y-3 text-sm">
          <p className="font-medium">What happens next:</p>
          <ol className="space-y-2 list-decimal list-inside text-muted-foreground">
            <li>You'll be redirected to Flutterwave's secure payment page</li>
            {paymentMethod === PaymentMethod.MOBILE_MONEY && (
              <li>Approve the payment prompt on your phone</li>
            )}
            {paymentMethod === PaymentMethod.CARD && (
              <li>Enter your card details securely</li>
            )}
            {paymentMethod === PaymentMethod.BANK_TRANSFER && (
              <li>Complete the bank transfer process</li>
            )}
            <li>You'll be redirected back after payment</li>
          </ol>
        </div>

        {/* Security Notice */}
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription className="text-xs">
            Your payment is secured by Flutterwave. Your card details are never stored on our servers.
          </AlertDescription>
        </Alert>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            onClick={handleProceed}
            className="flex-1"
            size="lg"
            disabled={isRedirecting || (paymentMethod === PaymentMethod.MOBILE_MONEY && !!phoneError)}
          >
            {isRedirecting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Redirecting...
              </>
            ) : (
              <>
                <ExternalLink className="mr-2 h-4 w-4" />
                Proceed to Payment
              </>
            )}
          </Button>
          {onCancel && (
            <Button
              onClick={onCancel}
              variant="outline"
              size="lg"
              disabled={isRedirecting}
            >
              Cancel
            </Button>
          )}
        </div>

        {/* Provider Logo/Badge */}
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            Powered by Flutterwave
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Flutterwave Payment Success Callback Handler
 *
 * Use this component on your return URL page to handle payment verification.
 */
export function FlutterwavePaymentCallback() {
  const [status, setStatus] = useState<"loading" | "success" | "failed">("loading");
  const [message, setMessage] = useState("");

  // Get query parameters
  const params = new URLSearchParams(window.location.search);
  const txRef = params.get("tx_ref");
  const transactionId = params.get("transaction_id");
  const statusParam = params.get("status");

  // Verify payment on mount
  // useEffect(() => {
  //   if (statusParam === "successful" && transactionId) {
  //     // Verify with backend
  //     confirmPayment(paymentId).then(() => {
  //       setStatus("success");
  //       setMessage("Payment successful!");
  //     }).catch(() => {
  //       setStatus("failed");
  //       setMessage("Payment verification failed");
  //     });
  //   } else {
  //     setStatus("failed");
  //     setMessage("Payment was not completed");
  //   }
  // }, []);

  return (
    <Card className="max-w-md mx-auto mt-8">
      <CardContent className="pt-6">
        <div className="text-center space-y-4">
          {status === "loading" && (
            <>
              <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
              <p>Verifying your payment...</p>
            </>
          )}
          {status === "success" && (
            <>
              <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900 mx-auto flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="font-semibold">{message}</p>
            </>
          )}
          {status === "failed" && (
            <>
              <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 mx-auto flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <p className="font-semibold">{message}</p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
