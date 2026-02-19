/**
 * New Payment Page
 *
 * Allows users to create and process payments.
 */

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { PaymentMethodSelector } from "@/components/PaymentMethodSelector";
import { StripePaymentForm } from "@/components/StripePaymentForm";
import { FlutterwavePayment } from "@/components/FlutterwavePayment";
import { PaymentStatusDialog } from "@/components/PaymentStatusDialog";
import {
  createPayment,
  createPaymentIntent,
  confirmPayment,
  Payment,
  PaymentGateway,
  PaymentMethod,
  PaymentPurpose,
  MobileMoneyProvider,
  formatPaymentAmount,
} from "@/lib/api/payment-api";

export default function NewPayment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  // Payment form state
  const [amount, setAmount] = useState(searchParams.get("amount") || "");
  const [currency, setCurrency] = useState(searchParams.get("currency") || "GHS");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState<PaymentPurpose>(PaymentPurpose.OTHER);
  const [selectedGateway, setSelectedGateway] = useState<PaymentGateway>(PaymentGateway.STRIPE);
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>(PaymentMethod.CARD);
  const [momoProvider, setMomoProvider] = useState<MobileMoneyProvider | undefined>();
  const [momoPhone, setMomoPhone] = useState("");

  // Payment flow state
  const [step, setStep] = useState<"details" | "payment" | "status">("details");
  const [isLoading, setIsLoading] = useState(false);
  const [createdPayment, setCreatedPayment] = useState<Payment | null>(null);
  const [paymentIntent, setPaymentIntent] = useState<any | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<"processing" | "success" | "failed">("processing");
  const [showStatusDialog, setShowStatusDialog] = useState(false);

  // Pre-fill from query params
  const propertyId = searchParams.get("property_id");
  const invoiceId = searchParams.get("invoice_id");
  const bookingId = searchParams.get("booking_id");

  const handleCreatePayment = async () => {
    // Validation
    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid payment amount",
        variant: "destructive",
      });
      return;
    }

    if (!description) {
      toast({
        title: "Description Required",
        description: "Please provide a payment description",
        variant: "destructive",
      });
      return;
    }

    if (selectedMethod === PaymentMethod.MOBILE_MONEY && !momoProvider) {
      toast({
        title: "Provider Required",
        description: "Please select your mobile money provider",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      // Create payment
      const payment = await createPayment({
        amount: parseFloat(amount),
        currency,
        description,
        purpose,
        gateway: selectedGateway,
        payment_method: selectedMethod,
        property_id: propertyId || undefined,
        invoice_id: invoiceId || undefined,
        booking_id: bookingId || undefined,
        mobile_money_provider: momoProvider,
        mobile_money_phone: momoPhone || undefined,
        return_url: `${window.location.origin}/payments/callback`,
        cancel_url: `${window.location.origin}/payments/new`,
      });

      setCreatedPayment(payment);

      // Create payment intent if using gateway
      if (selectedGateway !== PaymentGateway.MANUAL) {
        const intent = await createPaymentIntent(payment.id);
        setPaymentIntent(intent);
      }

      // Move to payment step
      setStep("payment");

      toast({
        title: "Payment Created",
        description: "Complete the payment to proceed",
      });
    } catch (error: any) {
      console.error("Failed to create payment:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to create payment",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePaymentSuccess = async () => {
    if (!createdPayment) return;

    setPaymentStatus("processing");
    setShowStatusDialog(true);

    try {
      // Confirm payment with backend
      const confirmedPayment = await confirmPayment(createdPayment.id);
      setCreatedPayment(confirmedPayment);
      setPaymentStatus("success");

      toast({
        title: "Payment Successful",
        description: "Your payment has been processed",
      });
    } catch (error: any) {
      console.error("Payment confirmation failed:", error);
      setPaymentStatus("failed");

      toast({
        title: "Payment Failed",
        description: error.message || "Could not confirm payment",
        variant: "destructive",
      });
    }
  };

  const handlePaymentError = (error: string) => {
    setPaymentStatus("failed");
    setShowStatusDialog(true);

    toast({
      title: "Payment Failed",
      description: error,
      variant: "destructive",
    });
  };

  const handleRetry = () => {
    setShowStatusDialog(false);
    setStep("details");
    setCreatedPayment(null);
    setPaymentIntent(null);
  };

  const handleViewPayment = () => {
    if (createdPayment) {
      navigate(`/payments/${createdPayment.id}`);
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20 md:pb-0">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">New Payment</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {step === "details" && "Enter payment details"}
              {step === "payment" && "Complete your payment"}
              {step === "status" && "Payment confirmation"}
            </p>
          </div>
        </div>

        <div className="max-w-3xl mx-auto">
          {/* Step 1: Payment Details */}
          {step === "details" && (
            <div className="space-y-6">
              {/* Amount & Currency */}
              <Card>
                <CardHeader>
                  <CardTitle>Payment Information</CardTitle>
                  <CardDescription>
                    Provide the payment details below
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="amount">Amount*</Label>
                      <Input
                        id="amount"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="0.00"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                      />
                    </div>

                    <div>
                      <Label htmlFor="currency">Currency</Label>
                      <Select value={currency} onValueChange={setCurrency}>
                        <SelectTrigger id="currency">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="GHS">GHS (Ghana Cedi)</SelectItem>
                          <SelectItem value="USD">USD (US Dollar)</SelectItem>
                          <SelectItem value="EUR">EUR (Euro)</SelectItem>
                          <SelectItem value="GBP">GBP (Pound Sterling)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="purpose">Purpose</Label>
                    <Select value={purpose} onValueChange={(value) => setPurpose(value as PaymentPurpose)}>
                      <SelectTrigger id="purpose">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={PaymentPurpose.RENT}>Rent</SelectItem>
                        <SelectItem value={PaymentPurpose.SECURITY_DEPOSIT}>Security Deposit</SelectItem>
                        <SelectItem value={PaymentPurpose.PURCHASE}>Property Purchase</SelectItem>
                        <SelectItem value={PaymentPurpose.BOOKING_FEE}>Booking Fee</SelectItem>
                        <SelectItem value={PaymentPurpose.SERVICE_FEE}>Service Fee</SelectItem>
                        <SelectItem value={PaymentPurpose.OTHER}>Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="description">Description*</Label>
                    <Textarea
                      id="description"
                      placeholder="Payment for..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={3}
                    />
                  </div>

                  {/* Preview */}
                  {amount && parseFloat(amount) > 0 && (
                    <div className="bg-muted rounded-lg p-4 mt-4">
                      <p className="text-sm text-muted-foreground mb-1">Total Amount</p>
                      <p className="text-2xl font-bold">
                        {formatPaymentAmount(parseFloat(amount), currency)}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Payment Method Selection */}
              <PaymentMethodSelector
                selectedGateway={selectedGateway}
                selectedMethod={selectedMethod}
                selectedMomoProvider={momoProvider}
                onGatewayChange={setSelectedGateway}
                onMethodChange={setSelectedMethod}
                onMomoProviderChange={setMomoProvider}
              />

              {/* Continue Button */}
              <Button
                onClick={handleCreatePayment}
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Payment...
                  </>
                ) : (
                  "Continue to Payment"
                )}
              </Button>
            </div>
          )}

          {/* Step 2: Payment Processing */}
          {step === "payment" && createdPayment && (
            <div className="space-y-6">
              {/* Stripe Payment */}
              {selectedGateway === PaymentGateway.STRIPE && paymentIntent?.client_secret && (
                <StripePaymentForm
                  clientSecret={paymentIntent.client_secret}
                  amount={createdPayment.amount}
                  currency={createdPayment.currency}
                  onSuccess={handlePaymentSuccess}
                  onError={handlePaymentError}
                />
              )}

              {/* Flutterwave Payment */}
              {selectedGateway === PaymentGateway.FLUTTERWAVE && paymentIntent?.client_secret && (
                <FlutterwavePayment
                  paymentLink={paymentIntent.client_secret}
                  amount={createdPayment.amount}
                  currency={createdPayment.currency}
                  paymentMethod={selectedMethod}
                  momoProvider={momoProvider}
                  momoPhone={momoPhone}
                  onMomoPhoneChange={setMomoPhone}
                  onSuccess={handlePaymentSuccess}
                  onCancel={() => setStep("details")}
                />
              )}

              {/* Manual Payment */}
              {selectedGateway === PaymentGateway.MANUAL && (
                <Card>
                  <CardHeader>
                    <CardTitle>Manual Payment</CardTitle>
                    <CardDescription>
                      Payment recorded. Please complete the payment offline.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={() => navigate("/payments")}
                      className="w-full"
                    >
                      View Payments
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>

        {/* Payment Status Dialog */}
        <PaymentStatusDialog
          open={showStatusDialog}
          onOpenChange={setShowStatusDialog}
          payment={createdPayment}
          status={paymentStatus}
          onViewPayment={handleViewPayment}
          onRetry={handleRetry}
        />
      </div>
    </div>
  );
}
