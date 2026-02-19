import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  DollarSign, 
  TrendingUp, 
  Globe, 
  Phone, 
  MessageSquare, 
  Video, 
  Wifi,
  Calculator,
  Info,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import HelpTooltip from '../help/HelpTooltip';

interface PricingConfig {
  region: string;
  currency: string;
  communication_medium: string;
  provider: string;
  base_cost_per_minute: number;
  markup_percentage: number;
  final_cost_per_minute: number;
}

interface RegionalBundle {
  id: string;
  region: string;
  currency: string;
  name: string;
  description: string;
  price: number;
  minutes: number;
  communication_medium: string;
}

const PricingDashboard: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [pricingConfigs, setPricingConfigs] = useState<PricingConfig[]>([]);
  const [regionalBundles, setRegionalBundles] = useState<RegionalBundle[]>([]);
  const [selectedRegion, setSelectedRegion] = useState('GH');
  const [loading, setLoading] = useState(true);

  const regions = [
    { code: 'GH', name: 'Ghana', flag: '🇬🇭', currency: 'USD' },
    { code: 'NG', name: 'Nigeria', flag: '🇳🇬', currency: 'USD' },
    { code: 'KE', name: 'Kenya', flag: '🇰🇪', currency: 'USD' },
    { code: 'ZA', name: 'South Africa', flag: '🇿🇦', currency: 'USD' },
    { code: 'EG', name: 'Egypt', flag: '🇪🇬', currency: 'USD' },
    { code: 'US', name: 'United States', flag: '🇺🇸', currency: 'USD' },
  ];

  const communicationMediums = [
    { key: 'webrtc', name: 'WebRTC', icon: Wifi, description: 'Browser-based voice calls' },
    { key: 'phone', name: 'Phone (PSTN)', icon: Phone, description: 'Traditional phone calls' },
    { key: 'sms', name: 'SMS', icon: MessageSquare, description: 'Text messaging' },
    { key: 'video', name: 'Video', icon: Video, description: 'Video calls' },
  ];

  useEffect(() => {
    loadPricingData();
  }, [selectedRegion]);

  const loadPricingData = async () => {
    setLoading(true);
    try {
      // Load pricing configurations
      const { data: pricingData } = await supabase
        .from('pricing_config')
        .select('*')
        .eq('is_active', true)
        .eq('region', selectedRegion);

      if (pricingData) {
        setPricingConfigs(pricingData);
      }

      // Load regional bundles
      const { data: bundlesData } = await supabase
        .from('regional_pricing_bundles')
        .select('*')
        .eq('region', selectedRegion)
        .eq('is_active', true)
        .order('price', { ascending: true });

      if (bundlesData) {
        setRegionalBundles(bundlesData);
      }

    } catch (error: any) {
      console.error('Error loading pricing data:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load pricing data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const getPricingForMedium = (medium: string) => {
    return pricingConfigs.find(p => p.communication_medium === medium);
  };

  const calculateSavings = (bundle: RegionalBundle) => {
    const paygCost = bundle.minutes * (getPricingForMedium(bundle.communication_medium)?.final_cost_per_minute || 0);
    const savings = paygCost - bundle.price;
    const savingsPercentage = (savings / paygCost) * 100;
    return { savings, savingsPercentage };
  };

  const getCurrentRegion = () => {
    return regions.find(r => r.code === selectedRegion);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading pricing data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Transparent Pricing Dashboard</h1>
        <p className="text-muted-foreground">
          See our costs, markups, and your savings. We believe in complete transparency.
        </p>
      </div>

      {/* Region Selector */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Select Your Region
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Region:</span>
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

      {/* Pricing Transparency Info */}
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-800">
            <Info className="h-5 w-5" />
            How Our Pricing Works
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-white rounded-lg border">
              <DollarSign className="h-8 w-8 mx-auto mb-2 text-blue-600" />
              <h3 className="font-medium">Base Cost</h3>
              <p className="text-sm text-muted-foreground">
                What we pay to providers (Vonage, Vapi)
              </p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border">
              <TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-600" />
              <h3 className="font-medium">Markup</h3>
              <p className="text-sm text-muted-foreground">
                Our service fee (typically 30-50%)
              </p>
            </div>
            <div className="text-center p-4 bg-white rounded-lg border">
              <Calculator className="h-8 w-8 mx-auto mb-2 text-purple-600" />
              <h3 className="font-medium">Your Price</h3>
              <p className="text-sm text-muted-foreground">
                Final cost to you
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="payg" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="payg">Pay-As-You-Go</TabsTrigger>
          <TabsTrigger value="bundles">Bundles & Savings</TabsTrigger>
        </TabsList>

        <TabsContent value="payg" className="space-y-6">
          {/* Pay-As-You-Go Pricing */}
          <Card>
            <CardHeader>
              <CardTitle>Pay-As-You-Go Pricing - {getCurrentRegion()?.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {communicationMediums.map(medium => {
                  const Icon = medium.icon;
                  const pricing = getPricingForMedium(medium.key);
                  
                  if (!pricing) return null;

                  return (
                    <div key={medium.key} className="border rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Icon className="h-6 w-6 text-primary" />
                        <div>
                          <h3 className="font-medium">{medium.name}</h3>
                          <p className="text-sm text-muted-foreground">{medium.description}</p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded">
                          <p className="text-sm text-muted-foreground">Base Cost</p>
                          <p className="text-lg font-bold text-gray-600">
                            ${pricing.base_cost_per_minute.toFixed(4)}
                          </p>
                          <p className="text-xs text-muted-foreground">per minute</p>
                        </div>
                        
                        <div className="text-center p-3 bg-blue-50 rounded">
                          <p className="text-sm text-muted-foreground">Markup</p>
                          <p className="text-lg font-bold text-blue-600">
                            {pricing.markup_percentage}%
                          </p>
                          <p className="text-xs text-muted-foreground">service fee</p>
                        </div>
                        
                        <div className="text-center p-3 bg-green-50 rounded">
                          <p className="text-sm text-muted-foreground">Your Price</p>
                          <p className="text-lg font-bold text-green-600">
                            ${pricing.final_cost_per_minute.toFixed(4)}
                          </p>
                          <p className="text-xs text-muted-foreground">per minute</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Pricing Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Regional Pricing Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Region</th>
                      <th className="text-center p-2">WebRTC</th>
                      <th className="text-center p-2">Phone</th>
                      <th className="text-center p-2">SMS</th>
                      <th className="text-center p-2">Video</th>
                    </tr>
                  </thead>
                  <tbody>
                    {regions.map(region => {
                      const regionPricing = pricingConfigs.filter(p => p.region === region.code);
                      const webrtc = regionPricing.find(p => p.communication_medium === 'webrtc');
                      const phone = regionPricing.find(p => p.communication_medium === 'phone');
                      const sms = regionPricing.find(p => p.communication_medium === 'sms');
                      const video = regionPricing.find(p => p.communication_medium === 'video');

                      return (
                        <tr key={region.code} className={`border-b ${region.code === selectedRegion ? 'bg-blue-50' : ''}`}>
                          <td className="p-2 font-medium">
                            <span className="flex items-center gap-2">
                              <span>{region.flag}</span>
                              <span>{region.name}</span>
                            </span>
                          </td>
                          <td className="text-center p-2">
                            ${webrtc?.final_cost_per_minute.toFixed(4) || '0.0000'}
                          </td>
                          <td className="text-center p-2">
                            ${phone?.final_cost_per_minute.toFixed(4) || '0.0000'}
                          </td>
                          <td className="text-center p-2">
                            ${sms?.final_cost_per_minute.toFixed(4) || '0.0000'}
                          </td>
                          <td className="text-center p-2">
                            ${video?.final_cost_per_minute.toFixed(4) || '0.0000'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bundles" className="space-y-6">
          {/* Bundle Pricing */}
          <Card>
            <CardHeader>
              <CardTitle>Regional Bundles - {getCurrentRegion()?.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {regionalBundles.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {regionalBundles.map(bundle => {
                    const savings = calculateSavings(bundle);
                    
                    return (
                      <div key={bundle.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{bundle.name}</h3>
                          <Badge variant="secondary" className="capitalize">
                            {bundle.communication_medium}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-muted-foreground mb-3">
                          {bundle.description}
                        </p>
                        
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
                            <span>PayG Cost:</span>
                            <span>${(bundle.minutes * (getPricingForMedium(bundle.communication_medium)?.final_cost_per_minute || 0)).toFixed(2)}</span>
                          </div>
                          
                          {savings.savings > 0 && (
                            <div className="flex justify-between text-sm text-green-600">
                              <span>You Save:</span>
                              <span className="font-medium">
                                ${savings.savings.toFixed(2)} ({savings.savingsPercentage.toFixed(0)}%)
                              </span>
                            </div>
                          )}
                        </div>
                        
                        <Button className="w-full mt-4">
                          Purchase Bundle
                        </Button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-muted-foreground">No bundles available for this region.</p>
              )}
            </CardContent>
          </Card>

          {/* Bundle Benefits */}
          <Card>
            <CardHeader>
              <CardTitle>Why Choose Bundles?</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium">Save Money</h4>
                    <p className="text-sm text-muted-foreground">
                      Bundle pricing offers significant discounts compared to pay-as-you-go rates.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium">Predictable Costs</h4>
                    <p className="text-sm text-muted-foreground">
                      Know exactly how much you'll spend with upfront bundle purchases.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium">No Surprises</h4>
                    <p className="text-sm text-muted-foreground">
                      Avoid unexpected charges with pre-paid bundle minutes.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium">Flexible Usage</h4>
                    <p className="text-sm text-muted-foreground">
                      Use your bundle minutes across different communication mediums.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Pricing Model Explanation */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Our Pricing Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <h3 className="font-medium mb-2">Pay-As-You-Go</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Perfect for casual users and testing
                </p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• No upfront commitment</li>
                  <li>• Pay only for what you use</li>
                  <li>• Higher per-minute rates</li>
                </ul>
              </div>
              
              <div className="text-center p-4 border rounded-lg bg-blue-50">
                <h3 className="font-medium mb-2">Bundles</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Best for regular users and businesses
                </p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• Significant cost savings</li>
                  <li>• Predictable monthly costs</li>
                  <li>• Bulk discount pricing</li>
                </ul>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <h3 className="font-medium mb-2">Enterprise</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Custom solutions for large organizations
                </p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• Custom pricing plans</li>
                  <li>• Dedicated support</li>
                  <li>• Volume discounts</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PricingDashboard;
