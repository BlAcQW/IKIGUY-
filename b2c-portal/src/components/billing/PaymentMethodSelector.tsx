import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { paymentApi } from '@/lib/core-api';
import {
  CreditCard,
  Smartphone,
  Building,
  Check,
  ChevronRight,
  Loader2,
  Globe
} from 'lucide-react';

interface PaymentMethod {
  id: string;
  type: 'card' | 'mobile_money' | 'bank_transfer' | 'stripe';
  provider: string;
  display_name: string;
  last4?: string;
  phone_number?: string;
  is_default: boolean;
  logo?: string;
}

interface PaymentMethodSelectorProps {
  amount: number;
  currency?: string;
  onPaymentMethodSelected: (method: PaymentMethod, additionalData?: any) => void;
  onCancel?: () => void;
}

const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  amount,
  currency = 'USD',
  onPaymentMethodSelected,
  onCancel
}) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [savedMethods, setSavedMethods] = useState<PaymentMethod[]>([]);
  const [showNewMethod, setShowNewMethod] = useState(false);
  const [loading, setLoading] = useState(false);

  // New payment method form state
  const [newMethodType, setNewMethodType] = useState<string>('card');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [selectedNetwork, setSelectedNetwork] = useState('');

  const [providers, setProviders] = useState<any[]>([]);
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);

  // Fetch available providers from API
  useEffect(() => {
    const fetchProviders = async () => {
      setIsLoadingProviders(true);
      try {
        const response = await paymentApi.getPaymentProviders();

        // Validate response structure
        if (!response || !response.providers || !Array.isArray(response.providers)) {
          console.error('Invalid payment providers response:', response);
          setProviders([
            {
              id: 'stripe',
              name: 'Credit/Debit Card',
              description: 'Worldwide',
              icon: CreditCard,
              type: 'card',
              fee: '2.9%',
              currencies: ['USD', 'GHS'],
              popular: true
            }
          ]);
          setIsLoadingProviders(false);
          return;
        }

        // Transform API response to component format
        const transformedProviders = response.providers.map((p: any) => {
          let icon = Globe;
          let type = 'card';
          let popular = false;

          // Determine icon and type based on provider
          if (p.methods.includes('mobile_money')) {
            icon = Smartphone;
            type = 'mobile_money';
            // Mark MTN MoMo and M-Pesa as popular
            if (p.provider === 'mtn_momo' || p.provider === 'mpesa') {
              popular = true;
            }
          } else if (p.methods.includes('bank_transfer')) {
            icon = Building;
            type = 'bank_transfer';
          } else if (p.methods.includes('card')) {
            icon = CreditCard;
            type = 'card';
            // Mark Stripe as popular
            if (p.provider === 'stripe') {
              popular = true;
            }
          }

          return {
            id: p.provider,
            name: p.name,
            description: p.countries.join(', '),
            icon,
            type,
            fee: '1-3%', // Generic fee description
            currencies: p.currencies,
            country: p.countries[0],
            popular,
            methods: p.methods
          };
        });

        setProviders(transformedProviders);
      } catch (error) {
        console.error('Failed to fetch payment providers:', error);
        // Fallback to minimal defaults if API fails
        setProviders([
          {
            id: 'stripe',
            name: 'Credit/Debit Card',
            description: 'Worldwide',
            icon: CreditCard,
            type: 'card',
            fee: '2.9%',
            currencies: ['USD', 'GHS'],
            popular: true
          }
        ]);
      } finally {
        setIsLoadingProviders(false);
      }
    };

    fetchProviders();
  }, []);

  // Filter providers based on currency
  const availableProviders = providers.filter(p =>
    p.currencies.includes(currency)
  );

  useEffect(() => {
    // Load saved payment methods from API
    fetchSavedPaymentMethods();
  }, []);

  const fetchSavedPaymentMethods = async () => {
    try {
      const methods = await paymentApi.getPaymentMethods();
      // Transform backend format to component format
      const transformedMethods: PaymentMethod[] = methods.map((m: any) => ({
        id: m.id,
        type: m.method_type,
        provider: m.provider,
        display_name: m.display_name,
        last4: m.card_last4,
        phone_number: m.phone_number_masked,
        is_default: m.is_default,
      }));
      setSavedMethods(transformedMethods);
    } catch (error) {
      console.error('Failed to load payment methods:', error);
      setSavedMethods([]);
    }
  };

  const handleProviderSelect = (providerId: string) => {
    setSelectedProvider(providerId);
    const provider = providers.find(p => p.id === providerId);

    if (provider?.type === 'card') {
      // For cards, we'll need to integrate Stripe Elements
      setShowNewMethod(true);
      setNewMethodType('card');
    } else if (provider?.type === 'mobile_money') {
      setShowNewMethod(true);
      setNewMethodType('mobile_money');
      setSelectedNetwork(providerId);
    } else if (provider?.type === 'bank_transfer') {
      setShowNewMethod(true);
      setNewMethodType('bank_transfer');
    }
  };

  const handleSubmitNewMethod = async () => {
    setLoading(true);
    try {
      const provider = providers.find(p => p.id === selectedProvider);

      if (newMethodType === 'mobile_money') {
        // Create mobile money payment
        const paymentData = {
          provider: selectedProvider,
          method_type: 'mobile_money',
          display_name: `${provider?.name}`,
          phone_number: phoneNumber,
          amount: amount,
          currency: currency
        };

        onPaymentMethodSelected(paymentData as any, { phone_number: phoneNumber });
      } else if (newMethodType === 'card') {
        // For cards, we'd typically show Stripe Elements here
        // For now, show a message to integrate Stripe
        alert('Card payment integration requires Stripe Elements setup');
      } else if (newMethodType === 'bank_transfer') {
        // Bank transfer - generate account details
        const paymentData = {
          provider: 'flutterwave',
          method_type: 'bank_transfer',
          display_name: 'Bank Transfer',
          amount: amount,
          currency: currency
        };

        onPaymentMethodSelected(paymentData as any);
      }
    } catch (error) {
      console.error('Payment method submission failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPhoneNumber = (value: string) => {
    // Remove non-numeric characters
    const numbers = value.replace(/\D/g, '');

    // Format based on selected network
    if (selectedNetwork.includes('momo') || selectedNetwork.includes('vodafone') || selectedNetwork.includes('airteltigo')) {
      // Ghana format: +233 XX XXX XXXX
      if (numbers.startsWith('233')) {
        return `+${numbers}`;
      } else if (numbers.startsWith('0')) {
        return `+233${numbers.slice(1)}`;
      }
      return `+233${numbers}`;
    } else if (selectedNetwork === 'mpesa') {
      // Kenya format: +254 XXX XXX XXX
      if (numbers.startsWith('254')) {
        return `+${numbers}`;
      } else if (numbers.startsWith('0')) {
        return `+254${numbers.slice(1)}`;
      }
      return `+254${numbers}`;
    }

    return value;
  };

  return (
    <div className="space-y-6">
      {/* Amount Summary */}
      <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 p-4 rounded-lg border border-purple-500/20">
        <div className="flex justify-between items-center">
          <span className="text-sm text-muted-foreground">Amount to pay</span>
          <span className="text-2xl font-bold">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: currency
            }).format(amount)}
          </span>
        </div>
      </div>

      {/* Saved Payment Methods */}
      {savedMethods.length > 0 && !showNewMethod && (
        <div className="space-y-3">
          <Label>Saved Payment Methods</Label>
          {savedMethods.map((method) => (
            <Card
              key={method.id}
              className="p-4 cursor-pointer hover:border-primary transition-colors"
              onClick={() => onPaymentMethodSelected(method)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {method.type === 'card' ? (
                    <CreditCard className="h-5 w-5" />
                  ) : (
                    <Smartphone className="h-5 w-5" />
                  )}
                  <div>
                    <p className="font-medium">{method.display_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {method.last4 && `•••• ${method.last4}`}
                      {method.phone_number && method.phone_number}
                    </p>
                  </div>
                </div>
                {method.is_default && (
                  <Badge variant="secondary">Default</Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Payment Provider Selection */}
      {!showNewMethod ? (
        <div className="space-y-3">
          <Label className="flex items-center justify-between">
            <span>Select Payment Method</span>
            <span className="text-xs text-muted-foreground">Currency: {currency}</span>
          </Label>

          {isLoadingProviders ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
              <span className="ml-2 text-sm text-gray-600">Loading payment methods...</span>
            </div>
          ) : availableProviders.length === 0 ? (
            <div className="text-center py-8 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm text-yellow-800">
                No payment methods available for {currency}
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                Please select a different currency
              </p>
            </div>
          ) : (
            <RadioGroup value={selectedProvider} onValueChange={handleProviderSelect}>
              <div className="space-y-2">
                {availableProviders.map((provider) => (
                <Card
                  key={provider.id}
                  className={`p-4 cursor-pointer transition-all ${
                    selectedProvider === provider.id
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  } ${provider.popular ? 'border-l-4 border-l-blue-500' : ''}`}
                  onClick={() => handleProviderSelect(provider.id)}
                >
                  <div className="flex items-center gap-3">
                    <RadioGroupItem value={provider.id} id={provider.id} />
                    <provider.icon className="h-5 w-5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Label htmlFor={provider.id} className="cursor-pointer font-medium">
                          {provider.name}
                        </Label>
                        {provider.popular && (
                          <Badge variant="secondary" className="text-xs">Popular</Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{provider.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">Fee: {provider.fee}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Card>
                ))}
              </div>
            </RadioGroup>
          )}
        </div>
      ) : null}

      {/* New Mobile Money Form */}
      {showNewMethod && newMethodType === 'mobile_money' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Enter Mobile Money Number</Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowNewMethod(false);
                setSelectedProvider('');
              }}
            >
              Change Method
            </Button>
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <Input
              id="phone"
              type="tel"
              placeholder={
                selectedNetwork.includes('momo')
                  ? '+233 24 123 4567'
                  : selectedNetwork === 'mpesa'
                  ? '+254 712 345 678'
                  : '+233 XX XXX XXXX'
              }
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(formatPhoneNumber(e.target.value))}
              className="text-lg"
            />
            <p className="text-xs text-muted-foreground">
              Enter the number registered with {providers.find(p => p.id === selectedProvider)?.name}
            </p>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
            <p className="text-sm">
              <strong>Next steps:</strong>
              <br />
              1. You'll receive a prompt on your phone
              <br />
              2. Approve the payment with your PIN
              <br />
              3. Your wallet will be credited instantly
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowNewMethod(false);
                setSelectedProvider('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitNewMethod}
              disabled={!phoneNumber || loading}
              className="flex-1 bg-gradient-premium"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Pay {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: currency
                  }).format(amount)}
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* New Card Form (Placeholder) */}
      {showNewMethod && newMethodType === 'card' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Card Payment</Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowNewMethod(false);
                setSelectedProvider('');
              }}
            >
              Change Method
            </Button>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
            <p className="text-sm">
              <strong>Stripe Card Payment</strong>
              <br />
              Card payment requires Stripe Elements integration.
              <br />
              This will be added in the next update.
            </p>
          </div>

          <Button
            variant="outline"
            onClick={() => {
              setShowNewMethod(false);
              setSelectedProvider('');
            }}
            className="w-full"
          >
            Choose Different Method
          </Button>
        </div>
      )}

      {/* Bank Transfer Form */}
      {showNewMethod && newMethodType === 'bank_transfer' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Bank Transfer</Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowNewMethod(false);
                setSelectedProvider('');
              }}
            >
              Change Method
            </Button>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 space-y-2">
            <p className="text-sm">
              <strong>Transfer Details</strong>
              <br />
              You'll receive unique account details to transfer to.
              <br />
              Your wallet will be credited automatically once payment is confirmed.
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowNewMethod(false);
                setSelectedProvider('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitNewMethod}
              disabled={loading}
              className="flex-1 bg-gradient-premium"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Building className="h-4 w-4 mr-2" />
                  Get Transfer Details
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentMethodSelector;
