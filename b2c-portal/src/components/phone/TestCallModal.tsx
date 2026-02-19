import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import {
  Phone,
  PhoneOff,
  Loader2,
  CheckCircle,
  XCircle,
  Volume2,
  Clock,
  Bot,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { API_ENDPOINTS } from '@/config/api-config';
import { PhoneNumber } from '@/lib/phone-api-client';

interface TestCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  phone?: PhoneNumber;
  assistants: Array<{ id: string; name: string }>;
}

type CallStatus = 'idle' | 'initiating' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no-answer';

interface CallState {
  status: CallStatus;
  startTime?: Date;
  answerTime?: Date;
  endTime?: Date;
  duration?: number;
  message?: string;
}

export const TestCallModal: React.FC<TestCallModalProps> = ({
  isOpen,
  onClose,
  phone,
  assistants,
}) => {
  const { toast } = useToast();
  const [destinationNumber, setDestinationNumber] = useState('');
  const [callState, setCallState] = useState<CallState>({ status: 'idle' });
  const [isLoading, setIsLoading] = useState(false);
  const [callDuration, setCallDuration] = useState(0);

  // Get assigned assistant info
  const assignedAssistant = phone?.assigned_assistant_id
    ? assistants.find(a => a.id === phone.assigned_assistant_id)
    : null;

  // Live call duration counter
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (callState.status === 'answered' && callState.answerTime) {
      interval = setInterval(() => {
        const duration = Math.floor((Date.now() - callState.answerTime!.getTime()) / 1000);
        setCallDuration(duration);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [callState.status, callState.answerTime]);

  const resetCall = () => {
    setDestinationNumber('');
    setCallState({ status: 'idle' });
    setIsLoading(false);
    setCallDuration(0);
  };

  const handleClose = () => {
    if (callState.status === 'initiating' || callState.status === 'ringing' || callState.status === 'answered') {
      if (!confirm('A call is in progress. Are you sure you want to close?')) {
        return;
      }
    }
    resetCall();
    onClose();
  };

  const makeTestCall = async () => {
    if (!destinationNumber.trim()) {
      toast({
        title: 'Invalid number',
        description: 'Please enter a destination number',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    setCallState({
      status: 'initiating',
      startTime: new Date(),
      message: 'Initiating call...',
    });

    try {
      const response = await fetch(API_ENDPOINTS.asterisk.originateCall, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          destination: destinationNumber,
          source_number: phone?.number || '0308249843',
          context: 'from-internal',
          timeout: 60,
          assistant_id: phone?.assigned_assistant_id, // Pass assistant ID if assigned
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to initiate call');
      }

      const data = await response.json();

      // Update to ringing status
      setCallState({
        status: 'ringing',
        startTime: callState.startTime,
        message: `Calling ${destinationNumber}...`,
      });

      // Set loading to false - call is now in progress
      setIsLoading(false);

      // Real call is now in progress
      // Call will continue until user manually ends it or backend reports completion
      // Show answered status after a short delay
      setTimeout(() => {
        setCallState((prev) => ({
          ...prev,
          status: 'answered',
          answerTime: new Date(),
          message: assignedAssistant
            ? `Connected - talking to ${assignedAssistant.name}`
            : 'Call connected',
        }));
      }, 2000);
    } catch (error: any) {
      console.error('Error making test call:', error);

      setCallState({
        status: 'failed',
        startTime: callState.startTime,
        endTime: new Date(),
        message: error.message || 'Call failed',
      });

      setIsLoading(false);

      toast({
        title: 'Call failed',
        description: error.message || 'Failed to initiate test call',
        variant: 'destructive',
      });
    }
  };

  const getStatusBadge = () => {
    switch (callState.status) {
      case 'idle':
        return null;
      case 'initiating':
        return (
          <Badge className="bg-blue-500">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Initiating
          </Badge>
        );
      case 'ringing':
        return (
          <Badge className="bg-yellow-500">
            <Phone className="w-3 h-3 mr-1 animate-pulse" />
            Ringing
          </Badge>
        );
      case 'answered':
        return (
          <Badge className="bg-green-500">
            <Volume2 className="w-3 h-3 mr-1" />
            Connected
          </Badge>
        );
      case 'completed':
        return (
          <Badge className="bg-gray-500">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      case 'busy':
        return (
          <Badge className="bg-orange-500">
            <PhoneOff className="w-3 h-3 mr-1" />
            Busy
          </Badge>
        );
      case 'no-answer':
        return (
          <Badge className="bg-gray-500">
            <Clock className="w-3 h-3 mr-1" />
            No Answer
          </Badge>
        );
      default:
        return null;
    }
  };

  const canMakeCall = callState.status === 'idle' || callState.status === 'completed' || callState.status === 'failed';

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-primary" />
            Test Call
          </DialogTitle>
          <DialogDescription>
            {assignedAssistant
              ? `Call will be answered by ${assignedAssistant.name}`
              : 'Make a test call to verify your telephony setup'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Assistant Info Banner */}
          {assignedAssistant && (
            <div className="p-3 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-green-600 dark:text-green-400" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    Assistant Assigned
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300">
                    The person who answers will be talking to <strong>{assignedAssistant.name}</strong>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Source Number */}
          <div className="space-y-2">
            <Label>From (Caller ID)</Label>
            <Input
              value={phone?.number || '0308249843'}
              disabled
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              Outbound calls will display this number
            </p>
          </div>

          {/* Destination Number */}
          <div className="space-y-2">
            <Label htmlFor="destination">To (Destination Number)</Label>
            <Input
              id="destination"
              placeholder="e.g., 0244123456 or 2348012345678"
              value={destinationNumber}
              onChange={(e) => setDestinationNumber(e.target.value)}
              disabled={!canMakeCall}
            />
            <p className="text-xs text-muted-foreground">
              Enter the number you want to call (local or international)
            </p>
          </div>

          {/* Call Status */}
          {callState.status !== 'idle' && (
            <div className="p-4 border border-border rounded-lg bg-card space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Call Status</span>
                {getStatusBadge()}
              </div>

              {callState.message && (
                <p className="text-sm text-muted-foreground">{callState.message}</p>
              )}

              {/* Show live duration when call is answered, final duration when completed */}
              {(callState.status === 'answered' || callState.duration !== undefined) && (
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span>
                    Duration: {callState.status === 'answered' ? callDuration : callState.duration} seconds
                    {callState.status === 'answered' && <span className="ml-2 text-green-600 animate-pulse">●</span>}
                  </span>
                </div>
              )}

              {callState.startTime && (
                <p className="text-xs text-muted-foreground">
                  Started: {callState.startTime.toLocaleTimeString()}
                </p>
              )}
            </div>
          )}

          {/* Call History Note */}
          <div className="p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-xs text-blue-800 dark:text-blue-200">
              <strong>Note:</strong> Test calls use your Ant Cellular trunk and will be billed
              accordingly. The call will ring the destination number for up to 60 seconds.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            {canMakeCall ? 'Close' : 'Cancel'}
          </Button>

          {canMakeCall ? (
            <Button onClick={makeTestCall} disabled={!destinationNumber.trim() || isLoading}>
              <Phone className="w-4 h-4 mr-2" />
              Make Call
            </Button>
          ) : (
            <Button
              variant="destructive"
              onClick={() => {
                const endTime = new Date();
                const duration = callState.answerTime
                  ? Math.floor((endTime.getTime() - callState.answerTime.getTime()) / 1000)
                  : 0;

                setCallState({
                  status: 'completed',
                  startTime: callState.startTime,
                  answerTime: callState.answerTime,
                  endTime,
                  duration,
                  message: `Call ended (${duration}s)`,
                });
                setIsLoading(false);

                toast({
                  title: 'Call ended',
                  description: assignedAssistant
                    ? `Test call with ${assignedAssistant.name} ended after ${duration} seconds`
                    : `Call ended after ${duration} seconds`,
                });
              }}
            >
              <PhoneOff className="w-4 h-4 mr-2" />
              End Call
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
