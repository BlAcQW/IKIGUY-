import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { API_ENDPOINTS } from '@/config/api-config';
import { Loader2, Key, Phone, Link, Shield } from 'lucide-react';

interface SIPPeerManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  mode: 'create' | 'edit';
  existingPeer?: {
    username: string;
    number: string;
  };
}

export const SIPPeerManagementModal: React.FC<SIPPeerManagementModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  mode,
  existingPeer,
}) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    number: existingPeer?.number || '',
    sip_username: existingPeer?.username || '',
    sip_password: '',
    webhook_url: '',
    context: 'kasaai-virtual',
  });

  // Generate random password
  const generatePassword = () => {
    const length = 16;
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < length; i++) {
      password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    setFormData({ ...formData, sip_password: password });
  };

  // Generate SIP username from timestamp
  const generateUsername = () => {
    const timestamp = Date.now();
    const username = `kasaai_${timestamp}`;
    setFormData({ ...formData, sip_username: username });
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Validate form
      if (!formData.number || !formData.sip_username || !formData.sip_password) {
        toast({
          title: 'Validation Error',
          description: 'Please fill in all required fields',
          variant: 'destructive',
        });
        setIsLoading(false);
        return;
      }

      // Create SIP peer
      const response = await fetch(API_ENDPOINTS.asterisk.sip.peer, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create SIP peer');
      }

      const data = await response.json();

      toast({
        title: 'Success',
        description: data.message || 'SIP peer created successfully',
      });

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error creating SIP peer:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to create SIP peer',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5 text-indigo-600" />
            {mode === 'create' ? 'Create SIP Peer' : 'Edit SIP Peer'}
          </DialogTitle>
          <DialogDescription>
            Configure SIP endpoint for phone number provisioning
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Phone Number */}
          <div className="space-y-2">
            <Label htmlFor="number" className="flex items-center gap-1">
              <Phone className="h-3 w-3" />
              Phone Number *
            </Label>
            <Input
              id="number"
              placeholder="+1234567890"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: e.target.value })}
              disabled={mode === 'edit'}
              required
            />
            <p className="text-xs text-muted-foreground">E.164 format (e.g., +1234567890)</p>
          </div>

          {/* SIP Username */}
          <div className="space-y-2">
            <Label htmlFor="sip_username" className="flex items-center gap-1">
              <Shield className="h-3 w-3" />
              SIP Username *
            </Label>
            <div className="flex gap-2">
              <Input
                id="sip_username"
                placeholder="kasaai_1234567890"
                value={formData.sip_username}
                onChange={(e) => setFormData({ ...formData, sip_username: e.target.value })}
                disabled={mode === 'edit'}
                required
                className="flex-1"
              />
              {mode === 'create' && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={generateUsername}
                >
                  Generate
                </Button>
              )}
            </div>
          </div>

          {/* SIP Password */}
          <div className="space-y-2">
            <Label htmlFor="sip_password" className="flex items-center gap-1">
              <Key className="h-3 w-3" />
              SIP Password *
            </Label>
            <div className="flex gap-2">
              <Input
                id="sip_password"
                type="password"
                placeholder="••••••••••••••••"
                value={formData.sip_password}
                onChange={(e) => setFormData({ ...formData, sip_password: e.target.value })}
                required
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={generatePassword}
              >
                Generate
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Minimum 16 characters recommended</p>
          </div>

          {/* Webhook URL */}
          <div className="space-y-2">
            <Label htmlFor="webhook_url" className="flex items-center gap-1">
              <Link className="h-3 w-3" />
              Webhook URL
            </Label>
            <Input
              id="webhook_url"
              placeholder="https://api.example.com/webhook"
              value={formData.webhook_url}
              onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              URL to receive incoming call notifications
            </p>
          </div>

          {/* Context */}
          <div className="space-y-2">
            <Label htmlFor="context">Asterisk Context</Label>
            <Input
              id="context"
              value={formData.context}
              onChange={(e) => setFormData({ ...formData, context: e.target.value })}
              disabled
            />
            <p className="text-xs text-muted-foreground">
              Asterisk dialplan context (default: kasaai-virtual)
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {mode === 'create' ? 'Create Peer' : 'Update Peer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
