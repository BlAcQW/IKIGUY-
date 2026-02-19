import React, { useState, useEffect } from 'react';
import { QrCode, Smartphone, CheckCircle2, XCircle, RefreshCw, Copy, Phone, AlertCircle, Radio } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS } from '@/config/api-config';
import { useToast } from '@/hooks/use-toast';

interface PhoneNumber {
  id: string;
  number: string;
  sip_username: string;
  sip_password: string;
  assigned_assistant_id?: string;
}

interface SIPRegistrationStatus {
  sip_username: string;
  status: string;
  registered: boolean;
  ip_address?: string;
  user_agent?: string;
  last_registration?: string;
}

interface ANTGateway {
  gateway_id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  sim_registered: boolean;
  network_provider: string;
  signal_strength: number;
  phone_numbers: string[];
  last_seen?: string;
}

interface ANTCellularStatus {
  success: boolean;
  gateways: ANTGateway[];
  total_gateways: number;
  online_gateways: number;
  registered_numbers: number;
  message?: string;
}

export const SIPRegistrationPanel: React.FC = () => {
  const { toast } = useToast();
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [selectedNumber, setSelectedNumber] = useState<PhoneNumber | null>(null);
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string | null>(null);
  const [sipUri, setSipUri] = useState<string>('');
  const [instructions, setInstructions] = useState<string>('');
  const [registrationStatus, setRegistrationStatus] = useState<SIPRegistrationStatus | null>(null);
  const [antCellularStatus, setAntCellularStatus] = useState<ANTCellularStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingQR, setIsGeneratingQR] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);

  // Fetch phone numbers
  const fetchPhoneNumbers = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_ENDPOINTS.phoneNumbers.list}`);
      if (!response.ok) throw new Error('Failed to fetch phone numbers');
      const data = await response.json();
      const numbers = data.numbers || [];
      setPhoneNumbers(numbers);

      // Auto-select first assigned number
      const assignedNumber = numbers.find((n: PhoneNumber) => n.assigned_assistant_id);
      if (assignedNumber && !selectedNumber) {
        setSelectedNumber(assignedNumber);
      }
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

  // Generate QR code
  const generateQRCode = async (phoneNumber: PhoneNumber) => {
    try {
      setIsGeneratingQR(true);
      const response = await fetch(API_ENDPOINTS.sipRegistration.generateQr, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phoneNumber.number,
          sip_username: phoneNumber.sip_username,
          sip_password: phoneNumber.sip_password,
          display_name: `KasaAI ${phoneNumber.number}`,
        }),
      });

      if (!response.ok) throw new Error('Failed to generate QR code');
      const data = await response.json();

      setQrCodeDataUrl(data.qr_code_data_url);
      setSipUri(data.sip_uri);
      setInstructions(data.instructions);

      toast({
        title: 'QR Code Generated',
        description: 'Scan with Linphone to register',
      });
    } catch (error: any) {
      console.error('Error generating QR code:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate QR code',
        variant: 'destructive',
      });
    } finally {
      setIsGeneratingQR(false);
    }
  };

  // Check registration status
  const checkRegistrationStatus = async (sipUsername: string) => {
    try {
      setIsCheckingStatus(true);
      const response = await fetch(API_ENDPOINTS.sipRegistration.status(sipUsername));

      if (!response.ok) throw new Error('Failed to check status');
      const data = await response.json();
      setRegistrationStatus(data);
    } catch (error: any) {
      console.error('Error checking registration status:', error);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  // Fetch ANT cellular status
  const fetchAntCellularStatus = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.sipRegistration.antCellular);

      if (!response.ok) throw new Error('Failed to fetch ANT status');
      const data = await response.json();
      setAntCellularStatus(data);
    } catch (error: any) {
      console.error('Error fetching ANT cellular status:', error);
    }
  };

  // Auto-refresh status when number is selected
  useEffect(() => {
    if (selectedNumber) {
      checkRegistrationStatus(selectedNumber.sip_username);

      // Poll every 5 seconds
      const interval = setInterval(() => {
        checkRegistrationStatus(selectedNumber.sip_username);
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [selectedNumber]);

  // Initial load
  useEffect(() => {
    fetchPhoneNumbers();
    fetchAntCellularStatus();

    // Refresh ANT status every 30 seconds
    const interval = setInterval(fetchAntCellularStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectNumber = (number: PhoneNumber) => {
    setSelectedNumber(number);
    setQrCodeDataUrl(null);
    setRegistrationStatus(null);
  };

  const handleGenerateQR = () => {
    if (selectedNumber) {
      generateQRCode(selectedNumber);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: `${label} copied to clipboard`,
    });
  };

  return (
    <div className="space-y-4">
      {/* ANT Cellular Status */}
      <Card className="border-l-4 border-l-yellow-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Radio className="h-5 w-5" />
                ANT Cellular Gateway Status
              </CardTitle>
              <CardDescription>
                Hardware cellular gateway registration status
              </CardDescription>
            </div>
            <Button onClick={fetchAntCellularStatus} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {antCellularStatus ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg bg-yellow-50 dark:bg-yellow-950">
                <div className="flex items-center gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  <div>
                    <p className="font-medium">{antCellularStatus.message || 'No gateways detected'}</p>
                    <p className="text-sm text-muted-foreground">
                      {antCellularStatus.total_gateways} total, {antCellularStatus.online_gateways} online
                    </p>
                  </div>
                </div>
                <Badge variant="outline" className="text-yellow-700">
                  {antCellularStatus.online_gateways === 0 ? 'Offline' : 'Online'}
                </Badge>
              </div>

              {antCellularStatus.gateways.length > 0 && (
                <div className="space-y-2">
                  {antCellularStatus.gateways.map((gateway) => (
                    <div key={gateway.gateway_id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{gateway.name}</p>
                          <p className="text-sm text-muted-foreground">{gateway.network_provider}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {gateway.status === 'online' ? (
                            <Badge variant="default" className="bg-green-500">Online</Badge>
                          ) : (
                            <Badge variant="outline">Offline</Badge>
                          )}
                          {gateway.sim_registered && (
                            <Badge variant="secondary">SIM Registered</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">Loading ANT status...</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SIP Registration with QR Code */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            SIP Registration - Use Your Phone
          </CardTitle>
          <CardDescription>
            Generate QR code to register your phone as a SIP gateway using Linphone
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Phone Number Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Select Phone Number</label>
            <div className="space-y-2">
              {phoneNumbers.map((number) => (
                <div
                  key={number.id}
                  onClick={() => handleSelectNumber(number)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedNumber?.id === number.id
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950'
                      : 'hover:bg-accent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Phone className="h-4 w-4" />
                      <span className="font-mono font-semibold">{number.number}</span>
                      {number.assigned_assistant_id && (
                        <Badge variant="secondary">Assigned</Badge>
                      )}
                    </div>
                    {selectedNumber?.id === number.id && (
                      <CheckCircle2 className="h-5 w-5 text-indigo-600" />
                    )}
                  </div>
                </div>
              ))}

              {phoneNumbers.length === 0 && !isLoading && (
                <div className="text-center py-4 text-muted-foreground">
                  <AlertCircle className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  <p>No phone numbers found</p>
                  <p className="text-sm">Go to Phone Numbers page to provision a number</p>
                </div>
              )}
            </div>
          </div>

          {/* QR Code Generation */}
          {selectedNumber && (
            <div className="space-y-4">
              <Button
                onClick={handleGenerateQR}
                disabled={isGeneratingQR}
                className="w-full"
              >
                <QrCode className={`h-4 w-4 mr-2 ${isGeneratingQR ? 'animate-spin' : ''}`} />
                {qrCodeDataUrl ? 'Regenerate QR Code' : 'Generate QR Code'}
              </Button>

              {/* QR Code Display */}
              {qrCodeDataUrl && (
                <div className="border rounded-lg p-6 bg-white dark:bg-gray-900">
                  <div className="flex flex-col items-center space-y-4">
                    <img
                      src={qrCodeDataUrl}
                      alt="SIP Registration QR Code"
                      className="w-64 h-64"
                    />
                    <div className="text-center">
                      <p className="font-semibold mb-1">Scan with Linphone App</p>
                      <p className="text-sm text-muted-foreground">
                        Open Linphone → Menu → "Scan QR Code"
                      </p>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <code className="px-2 py-1 bg-muted rounded break-all flex-1 text-xs">{sipUri}</code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(sipUri, 'SIP URI')}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Registration Status */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Radio className="h-4 w-4" />
                    Registration Status
                  </h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => checkRegistrationStatus(selectedNumber.sip_username)}
                    disabled={isCheckingStatus}
                  >
                    <RefreshCw className={`h-3 w-3 ${isCheckingStatus ? 'animate-spin' : ''}`} />
                  </Button>
                </div>

                {registrationStatus ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {registrationStatus.registered ? (
                        <>
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <Badge variant="default" className="bg-green-500">Registered</Badge>
                        </>
                      ) : (
                        <>
                          <XCircle className="h-5 w-5 text-red-500" />
                          <Badge variant="outline">Not Registered</Badge>
                        </>
                      )}
                    </div>

                    {registrationStatus.registered && (
                      <div className="text-sm space-y-1 text-muted-foreground">
                        {registrationStatus.ip_address && (
                          <p>IP: {registrationStatus.ip_address}</p>
                        )}
                        {registrationStatus.user_agent && (
                          <p>Device: {registrationStatus.user_agent}</p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Checking status...</p>
                )}
              </div>

              {/* Instructions */}
              {instructions && (
                <div className="border rounded-lg p-4 bg-muted">
                  <h4 className="font-semibold mb-2">Setup Instructions</h4>
                  <pre className="text-xs whitespace-pre-wrap text-muted-foreground">
                    {instructions}
                  </pre>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
