import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Check, CreditCard, Clock, DollarSign } from 'lucide-react';

interface Bundle {
  id: string;
  name: string;
  description: string;
  price: number;
  minutes: number;
  is_active: boolean;
}

interface BundlePurchaseProps {
  onComplete: () => void;
  onCancel: () => void;
}

const BundlePurchase = ({ onComplete, onCancel }: BundlePurchaseProps) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [selectedBundle, setSelectedBundle] = useState<Bundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [purchasing, setPurchasing] = useState(false);

  useEffect(() => {
    loadBundles();
  }, []);

  const loadBundles = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('usage_bundles')
        .select('*')
        .eq('is_active', true)
        .order('price', { ascending: true });

      if (error) throw error;
      setBundles(data || []);
    } catch (error: any) {
      console.error('Error loading bundles:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load bundles',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBundleSelect = (bundle: Bundle) => {
    setSelectedBundle(bundle);
  };

  const handlePurchase = async () => {
    if (!selectedBundle || !user) return;

    setPurchasing(true);
    try {
      // Call the Edge Function to process the purchase
      const { data, error } = await supabase.functions.invoke('process-bundle-purchase', {
        body: {
          bundleId: selectedBundle.id,
          amount: selectedBundle.price,
          minutes: selectedBundle.minutes
        }
      });

      if (error) throw error;

      toast({
        title: 'Success',
        description: `Successfully purchased ${selectedBundle.minutes} minutes for $${selectedBundle.price}!`
      });

      onComplete();
    } catch (error: any) {
      console.error('Error purchasing bundle:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to purchase bundle',
        variant: 'destructive'
      });
    } finally {
      setPurchasing(false);
    }
  };

  const getBundleValue = (bundle: Bundle) => {
    const minutesPerDollar = bundle.minutes / bundle.price;
    return minutesPerDollar.toFixed(1);
  };

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Purchase Usage Bundle
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Bundle Selection */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Select a Bundle</h3>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {bundles.map((bundle) => (
                  <Card 
                    key={bundle.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedBundle?.id === bundle.id 
                        ? 'ring-2 ring-primary border-primary' 
                        : ''
                    }`}
                    onClick={() => handleBundleSelect(bundle)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{bundle.name}</CardTitle>
                        {selectedBundle?.id === bundle.id && (
                          <Check className="h-5 w-5 text-primary" />
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        {bundle.description}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="font-semibold">{bundle.minutes} min</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span className="font-semibold">${bundle.price}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Value:</span>
                        <Badge variant="secondary">
                          {getBundleValue(bundle)} min/$
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Selected Bundle Summary */}
          {selectedBundle && (
            <Card className="bg-muted/50">
              <CardHeader>
                <CardTitle className="text-lg">Purchase Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Bundle:</span>
                  <span className="font-semibold">{selectedBundle.name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Minutes:</span>
                  <span className="font-semibold">{selectedBundle.minutes} min</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Price:</span>
                  <span className="font-semibold">${selectedBundle.price}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Value:</span>
                  <span className="font-semibold text-green-600">
                    {getBundleValue(selectedBundle)} min/$
                  </span>
                </div>
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between text-lg font-bold">
                    <span>Total:</span>
                    <span>${selectedBundle.price}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button 
              onClick={handlePurchase}
              disabled={!selectedBundle || purchasing}
              className="flex items-center gap-2"
            >
              {purchasing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Processing...
                </>
              ) : (
                <>
                  <CreditCard className="h-4 w-4" />
                  Purchase Bundle
                </>
              )}
            </Button>
          </div>

          {/* Additional Info */}
          <div className="text-sm text-muted-foreground space-y-2">
            <p>• Usage is charged at $0.50 per minute</p>
            <p>• Bundles provide better value than pay-per-minute</p>
            <p>• Unused minutes don't expire</p>
            <p>• You can pause assistants to stop usage</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BundlePurchase;
