import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { Shield, Smartphone, QrCode, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface TwoFactorAuthProps {
  onClose?: () => void;
}

interface TwoFactorSetup {
  secret: string;
  qrCode: string;
  backupCodes: string[];
}

const TwoFactorAuth: React.FC<TwoFactorAuthProps> = ({ onClose }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [setupData, setSetupData] = useState<TwoFactorSetup | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  useEffect(() => {
    checkTwoFactorStatus();
  }, []);

  const checkTwoFactorStatus = async () => {
    try {
      const { data: { user: currentUser } } = await supabase.auth.getUser();
      if (currentUser) {
        // Check if 2FA is enabled by looking at user metadata
        const is2FAEnabled = currentUser.user_metadata?.two_factor_enabled || false;
        setIsEnabled(is2FAEnabled);
      }
    } catch (error) {
      console.error('Error checking 2FA status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateTwoFactorSetup = async () => {
    try {
      setIsLoading(true);
      const { data, error } = await supabase.functions.invoke('setup-two-factor', {
        body: { userId: user?.id }
      });

      if (error) throw error;

      if (data) {
        setSetupData(data);
        setBackupCodes(data.backupCodes);
        setShowSetup(true);
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to generate 2FA setup",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const verifyAndEnableTwoFactor = async () => {
    if (!verificationCode.trim()) {
      toast({
        title: "Verification Required",
        description: "Please enter the verification code",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsVerifying(true);
      const { data, error } = await supabase.functions.invoke('verify-two-factor', {
        body: {
          userId: user?.id,
          code: verificationCode,
          secret: setupData?.secret
        }
      });

      if (error) throw error;

      if (data.success) {
        setIsEnabled(true);
        setShowSetup(false);
        setSetupData(null);
        setVerificationCode('');
        toast({
          title: "Success",
          description: "Two-factor authentication has been enabled",
        });
        
        // Update user metadata
        await supabase.auth.updateUser({
          data: { two_factor_enabled: true }
        });
      }
    } catch (error: any) {
      toast({
        title: "Verification Failed",
        description: error.message || "Invalid verification code",
        variant: "destructive",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const disableTwoFactor = async () => {
    try {
      setIsLoading(true);
      const { data, error } = await supabase.functions.invoke('disable-two-factor', {
        body: { userId: user?.id }
      });

      if (error) throw error;

      if (data.success) {
        setIsEnabled(false);
        toast({
          title: "Success",
          description: "Two-factor authentication has been disabled",
        });
        
        // Update user metadata
        await supabase.auth.updateUser({
          data: { two_factor_enabled: false }
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to disable 2FA",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateNewBackupCodes = async () => {
    try {
      setIsLoading(true);
      const { data, error } = await supabase.functions.invoke('generate-backup-codes', {
        body: { userId: user?.id }
      });

      if (error) throw error;

      if (data.backupCodes) {
        setBackupCodes(data.backupCodes);
        toast({
          title: "Success",
          description: "New backup codes generated",
        });
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to generate backup codes",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Two-Factor Authentication
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Two-Factor Authentication
        </CardTitle>
        <CardDescription>
          Add an extra layer of security to your account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Section */}
        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="flex items-center gap-2">
            <Smartphone className="h-4 w-4" />
            <span className="text-sm font-medium">Status</span>
          </div>
          <Badge variant={isEnabled ? "default" : "secondary"}>
            {isEnabled ? (
              <span className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Enabled
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Disabled
              </span>
            )}
          </Badge>
        </div>

        {/* Setup Section */}
        {!isEnabled && !showSetup && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Enable two-factor authentication to protect your account with a second verification method.
            </p>
            <Button 
              onClick={generateTwoFactorSetup}
              disabled={isLoading}
              className="w-full"
            >
              <Shield className="h-4 w-4 mr-2" />
              Enable 2FA
            </Button>
          </div>
        )}

        {/* QR Code Setup */}
        {showSetup && setupData && (
          <div className="space-y-4 p-4 border rounded-lg bg-muted/50">
            <div className="text-center">
              <h4 className="font-medium mb-2">Scan QR Code</h4>
              <p className="text-sm text-muted-foreground mb-4">
                Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
              </p>
              <div className="flex justify-center mb-4">
                <img 
                  src={setupData.qrCode} 
                  alt="QR Code for 2FA setup" 
                  className="border rounded-lg"
                  width={200}
                  height={200}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="verification-code">Verification Code</Label>
              <Input
                id="verification-code"
                type="text"
                placeholder="Enter 6-digit code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                maxLength={6}
                className="text-center text-lg tracking-widest"
              />
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={verifyAndEnableTwoFactor}
                disabled={isVerifying || !verificationCode.trim()}
                className="flex-1"
              >
                {isVerifying ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Verify & Enable
              </Button>
              <Button 
                variant="outline"
                onClick={() => {
                  setShowSetup(false);
                  setSetupData(null);
                  setVerificationCode('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Backup Codes Section */}
        {backupCodes.length > 0 && (
          <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Backup Codes</h4>
              <Button
                variant="outline"
                size="sm"
                onClick={generateNewBackupCodes}
                disabled={isLoading}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Generate New
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Save these backup codes in a secure location. You can use them to access your account if you lose your authenticator device.
            </p>
            <div className="grid grid-cols-2 gap-2">
              {backupCodes.map((code, index) => (
                <div
                  key={index}
                  className="p-2 bg-background border rounded text-center font-mono text-sm"
                >
                  {code}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Disable Section */}
        {isEnabled && (
          <div className="space-y-3">
            <Button 
              variant="destructive"
              onClick={disableTwoFactor}
              disabled={isLoading}
              className="w-full"
            >
              <AlertCircle className="h-4 w-4 mr-2" />
              Disable 2FA
            </Button>
            <p className="text-xs text-muted-foreground text-center">
              Warning: Disabling 2FA will make your account less secure
            </p>
          </div>
        )}

        {onClose && (
          <Button variant="outline" onClick={onClose} className="w-full">
            Close
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default TwoFactorAuth;
