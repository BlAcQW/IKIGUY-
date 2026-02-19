import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "@/components/ui/use-toast";
import { Plus, Copy, Trash2, Eye, EyeOff, Key, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  status: string;
  created_at: string;
  last_used_at?: string;
}

const AVAILABLE_SCOPES = [
  { id: 'assistants:read', label: 'Read Assistants', description: 'View assistant configurations' },
  { id: 'assistants:write', label: 'Manage Assistants', description: 'Create and modify assistants' },
  { id: 'campaigns:read', label: 'Read Campaigns', description: 'View campaign data' },
  { id: 'campaigns:write', label: 'Manage Campaigns', description: 'Create and control campaigns' },
  { id: 'kb:read', label: 'Read Knowledge Base', description: 'Access knowledge base content' },
  { id: 'kb:write', label: 'Manage Knowledge Base', description: 'Upload and manage KB sources' },
  { id: 'webhooks:manage', label: 'Manage Webhooks', description: 'Create and configure webhooks' },
  { id: 'mcp:manage', label: 'Manage MCP', description: 'Configure MCP connectors' },
  { id: 'analytics:read', label: 'Read Analytics', description: 'Access usage analytics' }
];

export const ApiKeysTab = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);

  const createApiKey = async () => {
    if (!newKeyName.trim() || selectedScopes.length === 0) {
      toast({
        title: "Validation Error",
        description: "Please provide a name and select at least one scope",
        variant: "destructive"
      });
      return;
    }

    setCreating(true);
    try {
      // Generate API key
      const keyId = crypto.randomUUID();
      const fullKey = `kas_pk_${keyId.replace(/-/g, '')}`;
      const keyPrefix = fullKey.substring(0, 12);

      const newKey: ApiKey = {
        id: keyId,
        name: newKeyName,
        key_prefix: keyPrefix,
        scopes: selectedScopes,
        status: 'active',
        created_at: new Date().toISOString(),
      };

      setApiKeys(prev => [newKey, ...prev]);
      setCreatedKey(fullKey);
      setNewKeyName("");
      setSelectedScopes([]);
      
      toast({
        title: "Success",
        description: "API key created successfully",
      });
    } catch (error) {
      console.error('Error creating API key:', error);
      toast({
        title: "Error",
        description: "Failed to create API key",
        variant: "destructive"
      });
    } finally {
      setCreating(false);
    }
  };

  const deleteApiKey = async (keyId: string) => {
    setApiKeys(prev => prev.filter(key => key.id !== keyId));
    toast({
      title: "Success",
      description: "API key deleted successfully",
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "API key copied to clipboard",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium">API Keys</h3>
          <p className="text-sm text-muted-foreground">
            Manage your API keys for accessing KasaAI services
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Generate a new API key with specific permissions
              </DialogDescription>
            </DialogHeader>
            
            {createdKey ? (
              <div className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <Label className="text-sm font-medium">Your new API key</Label>
                  <div className="flex items-center space-x-2 mt-2">
                    <Input
                      value={showKey ? createdKey : '•'.repeat(createdKey.length)}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => setShowKey(!showKey)}
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => copyToClipboard(createdKey)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    ⚠️ Copy this key now. You won't be able to see it again.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="keyName">Key Name</Label>
                  <Input
                    id="keyName"
                    placeholder="e.g., Production API Key"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Permissions</Label>
                  <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto">
                    {AVAILABLE_SCOPES.map((scope) => (
                      <div key={scope.id} className="flex items-start space-x-2">
                        <Checkbox
                          id={scope.id}
                          checked={selectedScopes.includes(scope.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedScopes([...selectedScopes, scope.id]);
                            } else {
                              setSelectedScopes(selectedScopes.filter(s => s !== scope.id));
                            }
                          }}
                        />
                        <div className="space-y-1 leading-none">
                          <Label htmlFor={scope.id} className="text-sm font-medium">
                            {scope.label}
                          </Label>
                          <p className="text-xs text-muted-foreground">
                            {scope.description}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            <DialogFooter>
              {createdKey ? (
                <Button 
                  onClick={() => {
                    setCreatedKey(null);
                    setShowCreateDialog(false);
                  }}
                >
                  Done
                </Button>
              ) : (
                <>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowCreateDialog(false)}
                  >
                    Cancel
                  </Button>
                  <Button onClick={createApiKey} disabled={creating}>
                    {creating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Creating...
                      </>
                    ) : (
                      'Create Key'
                    )}
                  </Button>
                </>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {apiKeys.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Key className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No API Keys</h3>
            <p className="text-muted-foreground mb-4">
              Create your first API key to start using the KasaAI API
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create API Key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {apiKeys.map((key) => (
            <Card key={key.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium">{key.name}</h4>
                      <Badge variant={key.status === 'active' ? 'default' : 'secondary'}>
                        {key.status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>Key: {key.key_prefix}••••••••••••</span>
                      <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                      {key.last_used_at && (
                        <span>Last used: {new Date(key.last_used_at).toLocaleDateString()}</span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => deleteApiKey(key.id)}
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