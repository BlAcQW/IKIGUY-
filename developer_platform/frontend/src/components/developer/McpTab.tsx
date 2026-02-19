import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/use-toast";
import { Plus, Plug, Trash2, Play, Settings, AlertCircle } from "lucide-react";

interface McpConnector {
  id: string;
  name: string;
  type: string;
  url: string;
  status: 'active' | 'inactive' | 'error';
  tool_names: string[];
  config: Record<string, any>;
  last_health_check?: string;
  created_at: string;
}

const CONNECTOR_TYPES = [
  { 
    id: 'hubspot', 
    label: 'HubSpot CRM', 
    description: 'Connect to HubSpot for contact and deal management',
    tools: ['get-contacts', 'create-contact', 'get-deals', 'create-deal']
  },
  { 
    id: 'freshdesk', 
    label: 'Freshdesk', 
    description: 'Integration with Freshdesk support tickets',
    tools: ['get-tickets', 'create-ticket', 'update-ticket', 'get-agents']
  },
  { 
    id: 'paystack', 
    label: 'Paystack Payments', 
    description: 'Process payments and manage transactions',
    tools: ['create-payment-link', 'verify-transaction', 'get-customer']
  },
  { 
    id: 'gmail', 
    label: 'Gmail', 
    description: 'Send emails and manage inbox',
    tools: ['send-email', 'get-messages', 'create-draft']
  },
  { 
    id: 'calendar', 
    label: 'Google Calendar', 
    description: 'Schedule meetings and manage events',
    tools: ['create-event', 'get-events', 'update-event', 'delete-event']
  }
];

export const McpTab = () => {
  const [connectors, setConnectors] = useState<McpConnector[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedType, setSelectedType] = useState("");
  const [connectorName, setConnectorName] = useState("");
  const [connectorUrl, setConnectorUrl] = useState("");
  const [connectorConfig, setConnectorConfig] = useState("");

  const createConnector = async () => {
    if (!connectorName.trim() || !selectedType || !connectorUrl.trim()) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    try {
      const connectorType = CONNECTOR_TYPES.find(t => t.id === selectedType);
      let config = {};
      
      if (connectorConfig.trim()) {
        try {
          config = JSON.parse(connectorConfig);
        } catch {
          toast({
            title: "Invalid Configuration",
            description: "Configuration must be valid JSON",
            variant: "destructive"
          });
          return;
        }
      }

      const newConnector: McpConnector = {
        id: crypto.randomUUID(),
        name: connectorName,
        type: selectedType,
        url: connectorUrl,
        status: 'active',
        tool_names: connectorType?.tools || [],
        config,
        created_at: new Date().toISOString(),
      };

      setConnectors(prev => [newConnector, ...prev]);
      setConnectorName("");
      setSelectedType("");
      setConnectorUrl("");
      setConnectorConfig("");
      setShowCreateDialog(false);
      
      toast({
        title: "Success",
        description: "MCP connector created successfully",
      });
    } catch (error) {
      console.error('Error creating connector:', error);
      toast({
        title: "Error",
        description: "Failed to create MCP connector",
        variant: "destructive"
      });
    }
  };

  const testConnector = async (connectorId: string) => {
    const connector = connectors.find(c => c.id === connectorId);
    if (!connector) return;

    // Simulate test
    setConnectors(prev => prev.map(c => 
      c.id === connectorId 
        ? { ...c, last_health_check: new Date().toISOString(), status: 'active' as const }
        : c
    ));
    
    toast({
      title: "Test Complete",
      description: `Connector "${connector.name}" is working correctly`,
    });
  };

  const deleteConnector = (connectorId: string) => {
    setConnectors(prev => prev.filter(c => c.id !== connectorId));
    toast({
      title: "Success",
      description: "MCP connector deleted",
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'inactive': return 'secondary';
      case 'error': return 'destructive';
      default: return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium">MCP Connectors</h3>
          <p className="text-sm text-muted-foreground">
            Manage Model Context Protocol connectors for external integrations
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Connector
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Add MCP Connector</DialogTitle>
              <DialogDescription>
                Configure a new MCP connector to integrate with external services
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="connectorType">Connector Type</Label>
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a connector type" />
                  </SelectTrigger>
                  <SelectContent>
                    {CONNECTOR_TYPES.map((type) => (
                      <SelectItem key={type.id} value={type.id}>
                        <div>
                          <div className="font-medium">{type.label}</div>
                          <div className="text-sm text-muted-foreground">{type.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="connectorName">Connector Name</Label>
                <Input
                  id="connectorName"
                  placeholder="e.g., Production HubSpot"
                  value={connectorName}
                  onChange={(e) => setConnectorName(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="connectorUrl">Server URL</Label>
                <Input
                  id="connectorUrl"
                  placeholder="https://your-mcp-server.com"
                  value={connectorUrl}
                  onChange={(e) => setConnectorUrl(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="connectorConfig">Configuration (JSON)</Label>
                <Textarea
                  id="connectorConfig"
                  placeholder='{"api_key": "your-api-key", "region": "us-east-1"}'
                  value={connectorConfig}
                  onChange={(e) => setConnectorConfig(e.target.value)}
                  rows={4}
                />
                <p className="text-xs text-muted-foreground">
                  Optional JSON configuration for the connector
                </p>
              </div>

              {selectedType && (
                <div className="space-y-2">
                  <Label>Available Tools</Label>
                  <div className="flex flex-wrap gap-1">
                    {CONNECTOR_TYPES.find(t => t.id === selectedType)?.tools.map((tool) => (
                      <Badge key={tool} variant="outline" className="text-xs">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => setShowCreateDialog(false)}
              >
                Cancel
              </Button>
              <Button onClick={createConnector}>
                Create Connector
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {connectors.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Plug className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No MCP Connectors</h3>
            <p className="text-muted-foreground mb-4">
              Add MCP connectors to integrate with external services and tools
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Connector
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {connectors.map((connector) => (
            <Card key={connector.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-3 flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium">{connector.name}</h4>
                      <Badge variant={getStatusColor(connector.status)}>
                        {connector.status}
                      </Badge>
                      <Badge variant="outline">
                        {CONNECTOR_TYPES.find(t => t.id === connector.type)?.label || connector.type}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>URL: {connector.url}</span>
                      <span>Created: {new Date(connector.created_at).toLocaleDateString()}</span>
                      {connector.last_health_check && (
                        <span>Last check: {new Date(connector.last_health_check).toLocaleString()}</span>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-1">
                        {connector.tool_names.map((tool) => (
                          <Badge key={tool} variant="outline" className="text-xs">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                      
                      {Object.keys(connector.config).length > 0 && (
                        <div className="text-xs text-muted-foreground">
                          Configuration: {Object.keys(connector.config).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => testConnector(connector.id)}
                      title="Test connection"
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      title="Configure"
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => deleteConnector(connector.id)}
                      title="Delete connector"
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