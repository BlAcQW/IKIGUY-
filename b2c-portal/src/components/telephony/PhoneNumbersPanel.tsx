import React, { useState, useEffect } from 'react';
import { Phone, Plus, Trash2, UserCheck, AlertCircle, Copy, CheckCircle2, Globe, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS } from '@/config/api-config';
import { useToast } from '@/hooks/use-toast';

interface PhoneNumber {
  id: string;
  number: string;
  provider: string;
  type: string;
  status: string;
  country: string;
  country_code: string;
  capabilities: string[];
  monthly_cost?: number;
  sip_username?: string;
  assigned_assistant_id?: string;
  assigned_at?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

interface PhoneNumbersPanelProps {
  onRefresh?: () => void;
}

export const PhoneNumbersPanel: React.FC<PhoneNumbersPanelProps> = ({ onRefresh }) => {
  const { toast } = useToast();
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedNumber, setCopiedNumber] = useState<string | null>(null);

  // Fetch phone numbers
  const fetchPhoneNumbers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_ENDPOINTS.phoneNumbers.list);
      if (!response.ok) throw new Error('Failed to fetch phone numbers');
      const data = await response.json();
      setPhoneNumbers(data.numbers || []);
    } catch (error: any) {
      console.error('Error fetching phone numbers:', error);
      toast({
        title: 'Error',
        description: 'Failed to load phone numbers',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPhoneNumbers();
  }, []);

  // Copy number to clipboard
  const handleCopyNumber = (number: string) => {
    navigator.clipboard.writeText(number);
    setCopiedNumber(number);
    setTimeout(() => setCopiedNumber(null), 2000);
    toast({
      title: 'Copied',
      description: 'Phone number copied to clipboard',
    });
  };

  // Calculate stats
  const stats = {
    total: phoneNumbers.length,
    active: phoneNumbers.filter(p => p.status === 'active').length,
    assigned: phoneNumbers.filter(p => p.assigned_assistant_id).length,
    countries: new Set(phoneNumbers.map(p => p.country)).size,
    monthlyCost: phoneNumbers.reduce((sum, p) => sum + (p.monthly_cost || 0), 0),
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-2 text-sm text-muted-foreground">Loading phone numbers...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Numbers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Phone className="h-5 w-5 text-blue-500" />
              <span className="text-2xl font-bold">{stats.total}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span className="text-2xl font-bold">{stats.active}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Assigned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-purple-500" />
              <span className="text-2xl font-bold">{stats.assigned}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Countries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-indigo-500" />
              <span className="text-2xl font-bold">{stats.countries}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Monthly Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              <span className="text-2xl font-bold">${stats.monthlyCost.toFixed(2)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Phone Numbers List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Virtual Phone Numbers
              </CardTitle>
              <CardDescription>
                Manage provisioned numbers and their Vapi assistant assignments
              </CardDescription>
            </div>
            <Button onClick={fetchPhoneNumbers} variant="outline" size="sm">
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {phoneNumbers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No phone numbers provisioned</p>
              <p className="text-sm mt-1">Visit the Phone Numbers page to provision a number</p>
            </div>
          ) : (
            <div className="space-y-2">
              {phoneNumbers.map((phone) => (
                <div
                  key={phone.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  {/* Left side: Number and details */}
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full ${
                      phone.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                    }`} />

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-lg">{phone.number}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyNumber(phone.number)}
                          className="h-6 w-6 p-0"
                        >
                          {copiedNumber === phone.number ? (
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>

                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {phone.provider.toUpperCase()}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {phone.country}
                        </Badge>
                        {phone.capabilities.map((cap) => (
                          <Badge key={cap} variant="secondary" className="text-xs">
                            {cap}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right side: Assignment and actions */}
                  <div className="flex items-center gap-3">
                    {phone.assigned_assistant_id ? (
                      <Badge variant="default" className="bg-purple-500">
                        <UserCheck className="h-3 w-3 mr-1" />
                        Assigned to Assistant
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">
                        Unassigned
                      </Badge>
                    )}

                    {phone.monthly_cost && (
                      <span className="text-sm text-muted-foreground">
                        ${phone.monthly_cost.toFixed(2)}/mo
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
