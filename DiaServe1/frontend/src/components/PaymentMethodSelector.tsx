/**
 * Payment Method Selector Component
 *
 * Allows users to select payment gateway and method.
 */

import { useState } from "react";
import { CreditCard, Smartphone, Building2, Banknote, FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  PaymentGateway,
  PaymentMethod,
  MobileMoneyProvider,
  getPaymentMethodLabel,
  getMobileMoneyProviderLabel,
} from "@/lib/api/payment-api";

interface PaymentMethodSelectorProps {
  selectedGateway: PaymentGateway;
  selectedMethod: PaymentMethod;
  selectedMomoProvider?: MobileMoneyProvider;
  onGatewayChange: (gateway: PaymentGateway) => void;
  onMethodChange: (method: PaymentMethod) => void;
  onMomoProviderChange?: (provider: MobileMoneyProvider) => void;
  className?: string;
}

export function PaymentMethodSelector({
  selectedGateway,
  selectedMethod,
  selectedMomoProvider,
  onGatewayChange,
  onMethodChange,
  onMomoProviderChange,
  className,
}: PaymentMethodSelectorProps) {
  const [showMomoProviders, setShowMomoProviders] = useState(
    selectedMethod === PaymentMethod.MOBILE_MONEY
  );

  const handleMethodChange = (method: PaymentMethod) => {
    onMethodChange(method);
    setShowMomoProviders(method === PaymentMethod.MOBILE_MONEY);

    // Auto-select appropriate gateway
    if (method === PaymentMethod.MOBILE_MONEY || method === PaymentMethod.BANK_TRANSFER) {
      onGatewayChange(PaymentGateway.FLUTTERWAVE);
    } else if (method === PaymentMethod.CARD) {
      // Keep current gateway or default to Stripe
      if (selectedGateway === PaymentGateway.MANUAL) {
        onGatewayChange(PaymentGateway.STRIPE);
      }
    } else {
      onGatewayChange(PaymentGateway.MANUAL);
    }
  };

  const paymentMethods = [
    {
      value: PaymentMethod.CARD,
      label: "Credit/Debit Card",
      description: "Pay with Visa, Mastercard, or American Express",
      icon: CreditCard,
      popular: true,
    },
    {
      value: PaymentMethod.MOBILE_MONEY,
      label: "Mobile Money",
      description: "MTN, Vodafone, or AirtelTigo",
      icon: Smartphone,
      popular: true,
    },
    {
      value: PaymentMethod.BANK_TRANSFER,
      label: "Bank Transfer",
      description: "Direct bank transfer",
      icon: Building2,
      popular: false,
    },
    {
      value: PaymentMethod.CASH,
      label: "Cash",
      description: "Pay in cash at our office",
      icon: Banknote,
      popular: false,
    },
    {
      value: PaymentMethod.CHECK,
      label: "Check",
      description: "Pay by check",
      icon: FileText,
      popular: false,
    },
  ];

  const momoProviders = [
    {
      value: MobileMoneyProvider.MTN_MOMO,
      label: "MTN Mobile Money",
      description: "Most popular in Ghana",
    },
    {
      value: MobileMoneyProvider.VODAFONE_CASH,
      label: "Vodafone Cash",
      description: "Fast and secure",
    },
    {
      value: MobileMoneyProvider.AIRTELTIGO_MONEY,
      label: "AirtelTigo Money",
      description: "Reliable service",
    },
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Select Payment Method</CardTitle>
        <CardDescription>
          Choose how you'd like to pay for this transaction
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Payment Methods */}
        <RadioGroup value={selectedMethod} onValueChange={(value) => handleMethodChange(value as PaymentMethod)}>
          <div className="grid grid-cols-1 gap-4">
            {paymentMethods.map((method) => {
              const Icon = method.icon;
              const isSelected = selectedMethod === method.value;

              return (
                <div key={method.value} className="relative">
                  <RadioGroupItem
                    value={method.value}
                    id={method.value}
                    className="peer sr-only"
                  />
                  <Label
                    htmlFor={method.value}
                    className={cn(
                      "flex items-start gap-4 rounded-lg border-2 border-border p-4 cursor-pointer transition-all",
                      "hover:border-primary/50 hover:bg-accent/5",
                      "peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2",
                      isSelected && "border-primary bg-primary/5"
                    )}
                  >
                    <div className={cn(
                      "mt-1 p-2 rounded-lg bg-muted transition-colors",
                      isSelected && "bg-primary/10"
                    )}>
                      <Icon className={cn(
                        "h-5 w-5 text-muted-foreground",
                        isSelected && "text-primary"
                      )} />
                    </div>

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{method.label}</p>
                        {method.popular && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                            Popular
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{method.description}</p>
                    </div>

                    {isSelected && (
                      <div className="mt-1 h-5 w-5 rounded-full border-2 border-primary flex items-center justify-center">
                        <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                      </div>
                    )}
                  </Label>
                </div>
              );
            })}
          </div>
        </RadioGroup>

        {/* Mobile Money Provider Selection */}
        {showMomoProviders && (
          <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            <Label>Select Mobile Money Provider</Label>
            <Select
              value={selectedMomoProvider}
              onValueChange={(value) => onMomoProviderChange?.(value as MobileMoneyProvider)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Choose your provider" />
              </SelectTrigger>
              <SelectContent>
                {momoProviders.map((provider) => (
                  <SelectItem key={provider.value} value={provider.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{provider.label}</span>
                      <span className="text-xs text-muted-foreground">{provider.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Gateway Info (for debugging/transparency) */}
        {selectedGateway !== PaymentGateway.MANUAL && (
          <div className="text-xs text-muted-foreground text-center pt-2 border-t">
            Powered by {selectedGateway === PaymentGateway.STRIPE ? "Stripe" : "Flutterwave"}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
