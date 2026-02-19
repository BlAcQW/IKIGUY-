import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "@/components/ui/use-toast";
import { Plus, Webhook, Trash2, Play, Pause, Eye } from "lucide-react";

interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  enabled: boolean;
  secret: string;
  description?: string;
  created_at: string;
  delivery_stats: {
    delivered: number;
    failed: number;
    pending: number;
  };
}

const AVAILABLE_EVENTS = [
  { id: 'assistant.created', label: 'Assistant Created', description: 'When a new assistant is created' },
  { id: 'assistant.updated', label: 'Assistant Updated', description: 'When an assistant is modified' },
  { id: 'campaign.started', label: 'Campaign Started', description: 'When a campaign begins execution' },
  { id: 'campaign.completed', label: 'Campaign Completed', description: 'When a campaign finishes' },
  { id: 'call.started', label: 'Call Started', description: 'When a call is initiated' },
  { id: 'call.completed', label: 'Call Completed', description: 'When a call ends' },
  { id: 'kb.source.uploaded', label: 'KB Source Uploaded', description: 'When a knowledge base source is uploaded' },
  { id: 'usage.quota.exceeded', label: 'Quota Exceeded', description: 'When usage quota is exceeded' }
];

export const WebhooksTab = () => {
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newWebhookUrl, setNewWebhookUrl] = useState("");
  const [newWebhookDescription, setNewWebhookDescription] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);

  const createWebhook = async () => {
    if (!newWebhookUrl.trim() || selectedEvents.length === 0) {
      toast({
        title: "Validation Error",
        description: "Please provide a URL and select at least one event",
        variant: "destructive"
      });
      return;
    }

    try {
      // Generate webhook secret
      const secret = `whsec_${crypto.randomUUID().replace(/-/g, '')}`;

      const newWebhook: WebhookEndpoint = {
        id: crypto.randomUUID(),
        url: newWebhookUrl,
        events: selectedEvents,
        enabled: true,
        secret,
        description: newWebhookDescription || undefined,
        created_at: new Date().toISOString(),
        delivery_stats: {
          delivered: 0,
          failed: 0,
          pending: 0
        }
      };

      setWebhooks(prev => [newWebhook, ...prev]);
      setNewWebhookUrl("");
      setNewWebhookDescription("");
      setSelectedEvents([]);
      setShowCreateDialog(false);
      
      toast({
        title: "Success",
        description: "Webhook endpoint created successfully",
      });
    } catch (error) {
      console.error('Error creating webhook:', error);
      toast({
        title: "Error",
        description: "Failed to create webhook endpoint",
        variant: "destructive"
      });
    }
  };

  const toggleWebhook = (webhookId: string) => {
    setWebhooks(prev => prev.map(webhook => 
      webhook.id === webhookId 
        ? { ...webhook, enabled: !webhook.enabled }
        : webhook
    ));
    
    toast({
      title: "Success",
      description: "Webhook endpoint updated",
    });
  };

  const deleteWebhook = (webhookId: string) => {
    setWebhooks(prev => prev.filter(webhook => webhook.id !== webhookId));
    toast({
      title: "Success",
      description: "Webhook endpoint deleted",
    });
  };

  const testWebhook = async (webhookId: string) => {
    const webhook = webhooks.find(w => w.id === webhookId);
    if (!webhook) return;

    toast({
      title: "Test Sent",
      description: `Test payload sent to ${webhook.url}`,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium">Webhooks</h3>
          <p className="text-sm text-muted-foreground">
            Configure webhook endpoints to receive real-time event notifications
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Endpoint
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Add Webhook Endpoint</DialogTitle>
              <DialogDescription>
                Configure a new webhook endpoint to receive event notifications
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="webhookUrl">Endpoint URL</Label>
                <Input
                  id="webhookUrl"
                  placeholder="https://your-domain.com/webhooks"
                  value={newWebhookUrl}
                  onChange={(e) => setNewWebhookUrl(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="webhookDescription">Description (optional)</Label>
                <Input
                  id="webhookDescription"
                  placeholder="Production webhook endpoint"
                  value={newWebhookDescription}
                  onChange={(e) => setNewWebhookDescription(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Events to Send</Label>
                <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto">
                  {AVAILABLE_EVENTS.map((event) => (
                    <div key={event.id} className="flex items-start space-x-2">
                      <Checkbox
                        id={event.id}
                        checked={selectedEvents.includes(event.id)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedEvents([...selectedEvents, event.id]);
                          } else {
                            setSelectedEvents(selectedEvents.filter(e => e !== event.id));
                          }
                        }}
                      />
                      <div className="space-y-1 leading-none">
                        <Label htmlFor={event.id} className="text-sm font-medium">
                          {event.label}
                        </Label>
                        <p className="text-xs text-muted-foreground">
                          {event.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </Button>
              <Button onClick={createWebhook}>
                Create Endpoint
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {webhooks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Webhook className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Webhook Endpoints</h3>
            <p className="text-muted-foreground mb-4">
              Add a webhook endpoint to receive real-time event notifications
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Endpoint
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {webhooks.map((webhook) => (
            <Card key={webhook.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-3 flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium">{webhook.url}</h4>
                      <Badge variant={webhook.enabled ? 'default' : 'secondary'}>
                        {webhook.enabled ? 'Active' : 'Paused'}
                      </Badge>
                    </div>
                    
                    {webhook.description && (
                      <p className="text-sm text-muted-foreground">
                        {webhook.description}
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>Created: {new Date(webhook.created_at).toLocaleDateString()}</span>
                      <span>Events: {webhook.events.length}</span>
                      <span>Secret: {webhook.secret.substring(0, 12)}•••</span>
                    </div>
                    
                    <div className="flex flex-wrap gap-1">
                      {webhook.events.map((event) => (
                        <Badge key={event} variant="outline" className="text-xs">
                          {event}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="text-green-600">
                        ✓ {webhook.delivery_stats.delivered} delivered
                      </span>
                      <span className="text-red-600">
                        ✗ {webhook.delivery_stats.failed} failed
                      </span>
                      <span className="text-yellow-600">
                        ⏳ {webhook.delivery_stats.pending} pending
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => testWebhook(webhook.id)}
                      title="Send test event"
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => toggleWebhook(webhook.id)}
                      title={webhook.enabled ? 'Pause endpoint' : 'Resume endpoint'}
                    >
                      {webhook.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => deleteWebhook(webhook.id)}
                      title="Delete endpoint"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};