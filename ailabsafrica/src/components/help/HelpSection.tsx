import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  HelpCircle, 
  DollarSign, 
  Phone, 
  MessageSquare, 
  Video, 
  Wifi,
  Calculator,
  Info,
  BookOpen,
  Users,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Globe,
  TrendingUp,
  Clock,
  Zap
} from 'lucide-react';

interface HelpSectionProps {
  defaultTab?: string;
}

const HelpSection: React.FC<HelpSectionProps> = ({ defaultTab = 'pricing' }) => {
  const [selectedRegion, setSelectedRegion] = useState('GH');

  const regions = [
    { code: 'GH', name: 'Ghana', flag: '🇬🇭', currency: 'USD' },
    { code: 'NG', name: 'Nigeria', flag: '🇳🇬', currency: 'USD' },
    { code: 'KE', name: 'Kenya', flag: '🇰🇪', currency: 'USD' },
    { code: 'ZA', name: 'South Africa', flag: '🇿🇦', currency: 'USD' },
    { code: 'EG', name: 'Egypt', flag: '🇪🇬', currency: 'USD' },
    { code: 'US', name: 'United States', flag: '🇺🇸', currency: 'USD' },
  ];

  const pricingData = {
    GH: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.35, markup: 30, final: 0.455 },
      sms: { base: 0.35, markup: 30, final: 0.455 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    },
    NG: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.40, markup: 30, final: 0.52 },
      sms: { base: 0.40, markup: 30, final: 0.52 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    },
    KE: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.45, markup: 30, final: 0.585 },
      sms: { base: 0.45, markup: 30, final: 0.585 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    },
    ZA: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.50, markup: 30, final: 0.65 },
      sms: { base: 0.50, markup: 30, final: 0.65 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    },
    EG: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.55, markup: 30, final: 0.715 },
      sms: { base: 0.55, markup: 30, final: 0.715 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    },
    US: {
      webrtc: { base: 0.05, markup: 30, final: 0.065 },
      phone: { base: 0.60, markup: 30, final: 0.78 },
      sms: { base: 0.60, markup: 30, final: 0.78 },
      video: { base: 0.0041, markup: 100, final: 0.0082 }
    }
  };

  const bundles = {
    GH: [
      { name: 'Starter Bundle', minutes: 100, price: 5.50, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 24.50, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 45.00, savings: 30 }
    ],
    NG: [
      { name: 'Starter Bundle', minutes: 100, price: 6.00, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 27.00, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 50.00, savings: 30 }
    ],
    KE: [
      { name: 'Starter Bundle', minutes: 100, price: 6.50, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 29.50, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 55.00, savings: 30 }
    ],
    ZA: [
      { name: 'Starter Bundle', minutes: 100, price: 7.00, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 32.00, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 60.00, savings: 30 }
    ],
    EG: [
      { name: 'Starter Bundle', minutes: 100, price: 7.50, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 34.50, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 65.00, savings: 30 }
    ],
    US: [
      { name: 'Starter Bundle', minutes: 100, price: 8.00, savings: 15 },
      { name: 'Professional Bundle', minutes: 500, price: 37.00, savings: 25 },
      { name: 'Enterprise Bundle', minutes: 1000, price: 70.00, savings: 30 }
    ]
  };

  const faqs = [
    {
      question: "How does the pricing work?",
      answer: "We offer a hybrid pricing model with Pay-As-You-Go rates and discounted bundles. Pay-As-You-Go charges per minute of usage, while bundles offer significant savings for higher usage volumes. All pricing is transparent with base costs and markups clearly displayed."
    },
    {
      question: "What communication mediums are supported?",
      answer: "We support WebRTC (browser-based calls), Phone (PSTN calls), SMS messaging, and Video calls. Each medium has different pricing based on the underlying provider costs (Vapi for WebRTC, Vonage for Phone/SMS/Video)."
    },
    {
      question: "How do I add funds to my wallet?",
      answer: "You can add funds through the Wallet Dashboard. Click 'Add Funds' and choose your preferred payment method. We accept major credit cards and digital wallets. Funds are added instantly to your wallet balance."
    },
    {
      question: "What happens when my wallet balance is low?",
      answer: "You'll receive alerts when your balance drops below $5.00. We recommend adding funds or purchasing a bundle to ensure uninterrupted service. You can set up automatic notifications for low balance alerts."
    },
    {
      question: "Can I get a refund for unused bundle minutes?",
      answer: "Bundle minutes are valid for 12 months from purchase. Unused minutes cannot be refunded, but they can be transferred to another account or extended for a small fee. We recommend purchasing bundles based on your expected usage."
    },
    {
      question: "How do I track my usage?",
      answer: "The Usage Tracking Dashboard shows real-time usage statistics, broken down by communication medium, session duration, and costs. You can view historical data, export reports, and set up usage alerts."
    },
    {
      question: "What's the difference between Pay-As-You-Go and bundles?",
      answer: "Pay-As-You-Go charges per minute at standard rates, ideal for occasional users. Bundles offer discounted rates for bulk purchases, perfect for regular users or businesses. Bundles provide 15-30% savings compared to Pay-As-You-Go rates."
    },
    {
      question: "How do regional pricing differences work?",
      answer: "Pricing varies by region based on local provider costs. We support 6 regions: Ghana, Nigeria, Kenya, South Africa, Egypt, and the US. Each region has optimized pricing for local market conditions and provider costs."
    }
  ];

  const getCurrentRegion = () => regions.find(r => r.code === selectedRegion);

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <HelpCircle className="h-8 w-8 text-primary" />
          Help & Support Center
        </h1>
        <p className="text-muted-foreground">
          Find answers to common questions, understand pricing, and get support
        </p>
      </div>

      <Tabs defaultValue={defaultTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pricing">Pricing Guide</TabsTrigger>
          <TabsTrigger value="faq">FAQ</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="support">Support</TabsTrigger>
        </TabsList>

        <TabsContent value="pricing" className="space-y-6">
          {/* Region Selector */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Regional Pricing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">Select your region:</span>
                <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {regions.map(region => (
                      <SelectItem key={region.code} value={region.code}>
                        <span className="flex items-center gap-2">
                          <span>{region.flag}</span>
                          <span>{region.name}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Pay-As-You-Go Pricing */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Pay-As-You-Go Pricing - {getCurrentRegion()?.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Wifi className="h-5 w-5 text-blue-600" />
                    <h3 className="font-medium">WebRTC</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Base Cost:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].webrtc.base.toFixed(4)}/min</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Markup:</span>
                      <span>{pricingData[selectedRegion as keyof typeof pricingData].webrtc.markup}%</span>
                    </div>
                    <div className="flex justify-between font-medium text-green-600">
                      <span>Your Price:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].webrtc.final.toFixed(4)}/min</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Phone className="h-5 w-5 text-green-600" />
                    <h3 className="font-medium">Phone (PSTN)</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Base Cost:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].phone.base.toFixed(4)}/min</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Markup:</span>
                      <span>{pricingData[selectedRegion as keyof typeof pricingData].phone.markup}%</span>
                    </div>
                    <div className="flex justify-between font-medium text-green-600">
                      <span>Your Price:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].phone.final.toFixed(4)}/min</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <MessageSquare className="h-5 w-5 text-purple-600" />
                    <h3 className="font-medium">SMS</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Base Cost:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].sms.base.toFixed(4)}/SMS</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Markup:</span>
                      <span>{pricingData[selectedRegion as keyof typeof pricingData].sms.markup}%</span>
                    </div>
                    <div className="flex justify-between font-medium text-green-600">
                      <span>Your Price:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].sms.final.toFixed(4)}/SMS</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Video className="h-5 w-5 text-red-600" />
                    <h3 className="font-medium">Video</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Base Cost:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].video.base.toFixed(4)}/min</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Markup:</span>
                      <span>{pricingData[selectedRegion as keyof typeof pricingData].video.markup}%</span>
                    </div>
                    <div className="flex justify-between font-medium text-green-600">
                      <span>Your Price:</span>
                      <span>${pricingData[selectedRegion as keyof typeof pricingData].video.final.toFixed(4)}/min</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bundle Pricing */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Bundle Pricing - {getCurrentRegion()?.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {bundles[selectedRegion as keyof typeof bundles].map((bundle, index) => (
                  <div key={index} className="border rounded-lg p-4 relative">
                    <Badge className="absolute top-2 right-2 bg-green-100 text-green-800">
                      Save {bundle.savings}%
                    </Badge>
                    <h3 className="font-medium mb-2">{bundle.name}</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Minutes:</span>
                        <span className="font-medium">{bundle.minutes}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Bundle Price:</span>
                        <span className="font-bold text-lg">${bundle.price.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm text-muted-foreground">
                        <span>Effective Rate:</span>
                        <span>${(bundle.price / bundle.minutes).toFixed(4)}/min</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Pricing Model Explanation */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Understanding Our Pricing Model
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Pay-As-You-Go</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Pay only for what you use</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>No upfront commitment</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Perfect for occasional users</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Transparent per-minute pricing</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Bundles</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Significant savings (15-30%)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Predictable costs</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>Ideal for regular users</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      <span>12-month validity</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="faq" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Frequently Asked Questions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {faqs.map((faq, index) => (
                  <AccordionItem key={index} value={`item-${index}`}>
                    <AccordionTrigger className="text-left">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent>
                      <p className="text-muted-foreground">{faq.answer}</p>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Key Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="text-center p-4 border rounded-lg">
                  <Wifi className="h-8 w-8 mx-auto mb-3 text-blue-600" />
                  <h3 className="font-medium mb-2">WebRTC Voice</h3>
                  <p className="text-sm text-muted-foreground">
                    High-quality browser-based voice calls with real-time transcription
                  </p>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <Phone className="h-8 w-8 mx-auto mb-3 text-green-600" />
                  <h3 className="font-medium mb-2">PSTN Integration</h3>
                  <p className="text-sm text-muted-foreground">
                    Traditional phone calls with local number support
                  </p>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <MessageSquare className="h-8 w-8 mx-auto mb-3 text-purple-600" />
                  <h3 className="font-medium mb-2">SMS Messaging</h3>
                  <p className="text-sm text-muted-foreground">
                    Text messaging with AI-powered responses
                  </p>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <Video className="h-8 w-8 mx-auto mb-3 text-red-600" />
                  <h3 className="font-medium mb-2">Video Calls</h3>
                  <p className="text-sm text-muted-foreground">
                    Face-to-face video conversations with AI assistance
                  </p>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <TrendingUp className="h-8 w-8 mx-auto mb-3 text-orange-600" />
                  <h3 className="font-medium mb-2">Usage Analytics</h3>
                  <p className="text-sm text-muted-foreground">
                    Detailed insights into your usage patterns and costs
                  </p>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <AlertTriangle className="h-8 w-8 mx-auto mb-3 text-yellow-600" />
                  <h3 className="font-medium mb-2">Smart Alerts</h3>
                  <p className="text-sm text-muted-foreground">
                    Automated notifications for low balance and high usage
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="support" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Get Support
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Contact Information</h4>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-blue-100">
                        <HelpCircle className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium">Email Support</p>
                        <p className="text-sm text-muted-foreground">support@ailabsafrica.com</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-green-100">
                        <Phone className="h-4 w-4 text-green-600" />
                      </div>
                      <div>
                        <p className="font-medium">Phone Support</p>
                        <p className="text-sm text-muted-foreground">+233 XX XXX XXXX</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-full bg-purple-100">
                        <MessageSquare className="h-4 w-4 text-purple-600" />
                      </div>
                      <div>
                        <p className="font-medium">Live Chat</p>
                        <p className="text-sm text-muted-foreground">Available 24/7</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Support Hours</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Monday - Friday:</span>
                      <span>8:00 AM - 6:00 PM GMT</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Saturday:</span>
                      <span>9:00 AM - 3:00 PM GMT</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Sunday:</span>
                      <span>Emergency Support Only</span>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Emergency Support:</strong> For critical issues outside business hours, 
                      please email with "URGENT" in the subject line.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default HelpSection;
