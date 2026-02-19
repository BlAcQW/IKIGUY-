import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { Send, Phone, MessageSquare } from 'lucide-react';
import { sendSMS } from '@/utils/smsUtils';

const SMSTester = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleSendSMS = async () => {
    if (!phoneNumber.trim() || !message.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter both phone number and message',
        variant: 'destructive'
      });
      return;
    }

    setSending(true);
    try {
      const result = await sendSMS(phoneNumber.trim(), message.trim(), user?.id);

      if (result.success) {
        toast({
          title: 'SMS Sent Successfully!',
          description: `Message sent to ${phoneNumber}`,
        });

        // Clear form
        setPhoneNumber('');
        setMessage('');
      } else {
        throw new Error(result.error || 'Failed to send SMS');
      }
    } catch (error: any) {
      console.error('Error sending SMS:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to send SMS',
        variant: 'destructive'
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          SMS Tester
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <Phone className="h-4 w-4" />
            Phone Number
          </label>
          <Input
            type="tel"
            placeholder="+1234567890"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            disabled={sending}
          />
          <p className="text-xs text-muted-foreground">
            Use international format (e.g., +1234567890)
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Message</label>
          <Textarea
            placeholder="Enter your message here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={sending}
            maxLength={160}
            rows={3}
          />
          <p className="text-xs text-muted-foreground">
            {message.length}/160 characters
          </p>
        </div>

        <Button
          onClick={handleSendSMS}
          disabled={sending || !phoneNumber.trim() || !message.trim()}
          className="w-full"
        >
          {sending ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
              Sending...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Send SMS
            </>
          )}
        </Button>

        <div className="text-xs text-muted-foreground text-center">
          This will send an SMS using the Vonage number configured in Supabase OTP
        </div>
      </CardContent>
    </Card>
  );
};

export default SMSTester;
