import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, XCircle, Phone, MapPin, Clock } from 'lucide-react';

interface SIPPeerDetails {
  username: string;
  status: string;
  registered: boolean;
  contact?: string;
  ip_address?: string;
  port?: number;
  user_agent?: string;
  last_registration?: string;
  expires?: number;
}

interface SIPPeerDetailsModalProps {
  peer: SIPPeerDetails | null;
  isOpen: boolean;
  onClose: () => void;
}

export const SIPPeerDetailsModal: React.FC<SIPPeerDetailsModalProps> = ({
  peer,
  isOpen,
  onClose,
}) => {
  if (!peer) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5 text-indigo-600" />
            SIP Peer Details
          </DialogTitle>
          <DialogDescription>
            Detailed information for SIP endpoint
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Status</span>
            <div className="flex items-center gap-2">
              {peer.registered ? (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <Badge variant="default" className="bg-green-500">
                    Registered
                  </Badge>
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-red-500" />
                  <Badge variant="destructive">Not Registered</Badge>
                </>
              )}
            </div>
          </div>

          <Separator />

          {/* Peer Information */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Peer Information</h4>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted-foreground">Username:</span>
                <p className="font-mono font-medium">{peer.username}</p>
              </div>

              <div>
                <span className="text-muted-foreground">Status:</span>
                <p className="font-medium capitalize">{peer.status}</p>
              </div>

              {peer.ip_address && (
                <div>
                  <span className="text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    IP Address:
                  </span>
                  <p className="font-mono font-medium">{peer.ip_address}</p>
                </div>
              )}

              {peer.port && (
                <div>
                  <span className="text-muted-foreground">Port:</span>
                  <p className="font-mono font-medium">{peer.port}</p>
                </div>
              )}
            </div>
          </div>

          {peer.contact && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-semibold mb-2">Contact URI</h4>
                <div className="bg-muted p-3 rounded-md">
                  <p className="text-xs font-mono break-all">{peer.contact}</p>
                </div>
              </div>
            </>
          )}

          {peer.user_agent && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-semibold mb-2">User Agent</h4>
                <p className="text-sm">{peer.user_agent}</p>
              </div>
            </>
          )}

          {(peer.last_registration || peer.expires) && (
            <>
              <Separator />
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  Registration Info
                </h4>

                {peer.last_registration && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">Last Registration:</span>
                    <p className="font-medium">{peer.last_registration}</p>
                  </div>
                )}

                {peer.expires && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">Expires In:</span>
                    <p className="font-medium">{peer.expires} seconds</p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
