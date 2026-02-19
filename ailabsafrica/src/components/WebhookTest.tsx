import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { CheckCircle, XCircle, Loader2, Zap, Phone, Settings } from 'lucide-react';

const WebhookTest: React.FC = () => {
  const { toast } = useToast();
  const [assistantName, setAssistantName] = useState('Test Assistant with Webhook');
  const [creating, setCreating] = useState(false);
  const [assistantId, setAssistantId] = useState<string | null>(null);
  const [webhookStatus, setWebhookStatus] = useState<'pending' | 'success' | 'failed'>('pending');

  const createTestAssistant = async () => {
    setCreating(true);
    setAssistantId(null);
    setWebhookStatus('pending');

    try {
      console.log('[WebhookTest] Creating test assistant with webhook configuration...');

      const requestBody = {
        assistantName,
        description: 'Test assistant to verify webhook configuration',
        websiteUrl: 'https://example.com',
        assistantType: 'help_desk',
        voiceId: 'Paige',
        knowledgeBaseFileIds: [],
        systemPromptOverride: 'You are a helpful test assistant. Your purpose is to verify that webhook configuration is working correctly.',
        useTemplate: true
      };

      const { data, error } = await supabase.functions.invoke('create-assistant', {
        body: requestBody
      });

      if (error) {
        console.error('[WebhookTest] Error creating assistant:', error);
        throw error;
      }

      console.log('[WebhookTest] Assistant created successfully:', data);
      setAssistantId(data.assistant_id);

      // Wait a moment for the assistant to be fully created, then verify webhook
      setTimeout(() => {
        verifyWebhookConfiguration(data.assistant_id);
      }, 2000);

      toast({
        title: "Assistant Created",
        description: `Test assistant "${assistantName}" created successfully. Verifying webhook configuration...`,
      });

    } catch (error: any) {
      console.error('[WebhookTest] Failed to create assistant:', error);
      setWebhookStatus('failed');
      toast({
        title: "Error",
        description: error.message || "Failed to create test assistant",
        variant: "destructive"
      });
    } finally {
      setCreating(false);
    }
  };

  const verifyWebhookConfiguration = async (id: string) => {
    try {
      console.log('[WebhookTest] Verifying webhook configuration for assistant:', id);

      // Get the assistant details from Vapi to check webhook configuration
      const response = await fetch(`https://api.vapi.ai/assistant/${id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${import.meta.env.VAPI_PRIVATE_KEY}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch assistant details: ${response.status}`);
      }

      const assistant = await response.json();
      console.log('[WebhookTest] Assistant details:', assistant);

      // Check if webhook is configured
      const hasWebhook = assistant.server && assistant.server.url;
      const hasServerMessages = assistant.serverMessages && assistant.serverMessages.length > 0;

      if (hasWebhook && hasServerMessages) {
        setWebhookStatus('success');
        toast({
          title: "Webhook Configured Successfully",
          description: `Assistant has webhook URL: ${assistant.server.url.substring(0, 50)}...`,
        });
      } else {
        setWebhookStatus('failed');
        toast({
          title: "Webhook Configuration Failed",
          description: "Assistant was created but webhook is not properly configured",
          variant: "destructive"
        });
      }

    } catch (error: any) {
      console.error('[WebhookTest] Failed to verify webhook:', error);
      setWebhookStatus('failed');
      toast({
        title: "Verification Failed",
        description: error.message || "Failed to verify webhook configuration",
        variant: "destructive"
      });
    }
  };

  const getStatusIcon = (status: 'pending' | 'success' | 'failed') => {
    if (status === 'pending') return <Loader2 className="h-4 w-4 animate-spin" />;
    return status === 'success' ? <CheckCircle className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-red-600" />;
  };

  const getStatusText = (status: 'pending' | 'success' | 'failed') => {
    switch (status) {
      case 'pending': return 'Verifying...';
      case 'success': return 'Webhook Configured';
      case 'failed': return 'Webhook Failed';
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Webhook Configuration Test
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="assistant-name">Assistant Name</Label>
          <Input
            id="assistant-name"
            value={assistantName}
            onChange={(e) => setAssistantName(e.target.value)}
            placeholder="Enter assistant name"
          />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Create test assistant with webhook</span>
          <Button 
            onClick={createTestAssistant} 
            disabled={creating || !assistantName.trim()}
            className="flex items-center gap-2"
          >
            {creating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Create & Test
              </>
            )}
          </Button>
        </div>

        {assistantId && (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                {getStatusIcon(webhookStatus)}
                <div>
                  <div className="font-medium flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Webhook Configuration
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Assistant ID: {assistantId}
                  </div>
                </div>
              </div>
              <div className={`text-sm font-medium ${
                webhookStatus === 'success' ? 'text-green-600' : 
                webhookStatus === 'failed' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {getStatusText(webhookStatus)}
              </div>
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground mt-4">
          <p>This test creates a new assistant and verifies that the webhook URL is automatically configured.</p>
          <p>The webhook will receive real-time call events including call-start, call-end, transcripts, and more.</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default WebhookTest;
