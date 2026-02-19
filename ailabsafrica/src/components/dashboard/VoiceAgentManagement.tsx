import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Play, 
  Pause, 
  Trash2, 
  Edit, 
  Copy, 
  Phone, 
  Calendar,
  Users,
  Activity,
  RefreshCw,
  CheckSquare,
  Square,
  AlertTriangle
} from 'lucide-react';

interface VoiceAgent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'deleted';
  model: string;
  voice_id: string;
  created_at: string;
  updated_at: string;
  total_calls?: number;
  total_duration?: number;
  last_call_at?: string;
}

const VoiceAgentManagement: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [agents, setAgents] = useState<VoiceAgent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedAgents, setSelectedAgents] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  const loadAgents = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('voice_agents')
        .select('*')
        .eq('user_id', user.id)
        .neq('status', 'deleted')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setAgents(data || []);
    } catch (error: any) {
      console.error('Error loading voice agents:', error);
      toast({
        title: "Error loading agents",
        description: error.message || "Failed to load voice agents",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, [user]);

  const handleAction = async (action: 'pause' | 'resume' | 'delete', agentId: string) => {
    if (!user) return;

    setActionLoading(agentId);
    try {
      const { data, error } = await supabase.functions.invoke('manage-assistant', {
        body: {
          action,
          assistant_id: agentId,
          user_id: user.id
        }
      });

      if (error) throw error;

      if (data?.success) {
        toast({
          title: "Success",
          description: data.message,
        });
        
        // Update local state
        setAgents(prev => prev.map(agent => {
          if (agent.id === agentId) {
            if (action === 'delete') {
              return { ...agent, status: 'deleted' as const };
            }
            return { 
              ...agent, 
              status: action === 'pause' ? 'paused' : 'active',
              updated_at: new Date().toISOString()
            };
          }
          return agent;
        }));

        // Remove deleted agents from the list
        if (action === 'delete') {
          setAgents(prev => prev.filter(agent => agent.id !== agentId));
        }
      } else {
        throw new Error(data?.error || 'Action failed');
      }
    } catch (error: any) {
      console.error('Agent action error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to perform action",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'deleted':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'paused':
        return 'Paused';
      case 'deleted':
        return 'Deleted';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  // Bulk operations functions
  const handleSelectAll = () => {
    if (selectedAgents.size === agents.length) {
      setSelectedAgents(new Set());
    } else {
      setSelectedAgents(new Set(agents.map(agent => agent.id)));
    }
  };

  const handleSelectAgent = (agentId: string) => {
    const newSelected = new Set(selectedAgents);
    if (newSelected.has(agentId)) {
      newSelected.delete(agentId);
    } else {
      newSelected.add(agentId);
    }
    setSelectedAgents(newSelected);
  };

  const handleBulkAction = async (action: 'pause' | 'resume' | 'delete') => {
    if (!user || selectedAgents.size === 0) return;

    const selectedAgentIds = Array.from(selectedAgents);
    const selectedAgentNames = agents
      .filter(agent => selectedAgentIds.includes(agent.id))
      .map(agent => agent.name);

    // Confirmation for destructive actions
    if (action === 'delete') {
      const confirmed = confirm(
        `Are you sure you want to delete ${selectedAgentIds.length} agent(s)?\n\n` +
        `Selected agents:\n${selectedAgentNames.join('\n')}\n\n` +
        `This action cannot be undone.`
      );
      if (!confirmed) return;
    }

    setBulkActionLoading(true);
    try {
      // Perform bulk action
      const promises = selectedAgentIds.map(agentId =>
        supabase.functions.invoke('manage-assistant', {
          body: {
            action,
            assistant_id: agentId,
            user_id: user.id
          }
        })
      );

      const results = await Promise.allSettled(promises);
      
      // Count successes and failures
      const successful = results.filter(result => 
        result.status === 'fulfilled' && result.value.data?.success
      ).length;
      
      const failed = results.length - successful;

      // Update local state
      setAgents(prev => prev.map(agent => {
        if (selectedAgentIds.includes(agent.id)) {
          if (action === 'delete') {
            return { ...agent, status: 'deleted' as const };
          }
          return { 
            ...agent, 
            status: action === 'pause' ? 'paused' : 'active',
            updated_at: new Date().toISOString()
          };
        }
        return agent;
      }));

      // Remove deleted agents from the list
      if (action === 'delete') {
        setAgents(prev => prev.filter(agent => !selectedAgentIds.includes(agent.id)));
      }

      // Clear selection
      setSelectedAgents(new Set());

      // Show results
      if (failed === 0) {
        toast({
          title: "Bulk action completed",
          description: `Successfully ${action}ed ${successful} agent(s)`,
        });
      } else {
        toast({
          title: "Bulk action partially completed",
          description: `Successfully ${action}ed ${successful} agent(s), ${failed} failed`,
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error('Bulk action error:', error);
      toast({
        title: "Bulk action failed",
        description: error.message || "Failed to perform bulk action",
        variant: "destructive",
      });
    } finally {
      setBulkActionLoading(false);
    }
  };

  const getBulkActionButtonText = (action: 'pause' | 'resume' | 'delete') => {
    const count = selectedAgents.size;
    switch (action) {
      case 'pause':
        return `Pause ${count} Agent${count !== 1 ? 's' : ''}`;
      case 'resume':
        return `Resume ${count} Agent${count !== 1 ? 's' : ''}`;
      case 'delete':
        return `Delete ${count} Agent${count !== 1 ? 's' : ''}`;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Voice Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSpinner text="Loading voice agents..." />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Voice Agents</CardTitle>
            <CardDescription>
              Manage your AI voice assistants and their status
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAgents}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {agents.length === 0 ? (
          <div className="text-center py-8">
            <Phone className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No voice agents found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Create your first voice agent to get started.
            </p>
            <Button className="mt-4" asChild>
              <a href="/create-assistant">Create Voice Agent</a>
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Bulk Operations Header */}
            {agents.length > 0 && (
              <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/30">
                <div className="flex items-center gap-3">
                  <Checkbox
                    checked={selectedAgents.size === agents.length}
                    onCheckedChange={handleSelectAll}
                    disabled={bulkActionLoading}
                  />
                  <span className="text-sm font-medium">
                    {selectedAgents.size === 0 
                      ? 'Select agents for bulk operations'
                      : `${selectedAgents.size} of ${agents.length} agents selected`
                    }
                  </span>
                </div>
                
                {selectedAgents.size > 0 && (
                  <div className="flex items-center gap-2">
                    {/* Bulk Pause */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleBulkAction('pause')}
                      disabled={bulkActionLoading}
                      className="text-yellow-600 hover:text-yellow-700"
                    >
                      {bulkActionLoading ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Pause className="h-4 w-4 mr-1" />
                      )}
                      {getBulkActionButtonText('pause')}
                    </Button>
                    
                    {/* Bulk Resume */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleBulkAction('resume')}
                      disabled={bulkActionLoading}
                      className="text-green-600 hover:text-green-700"
                    >
                      {bulkActionLoading ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Play className="h-4 w-4 mr-1" />
                      )}
                      {getBulkActionButtonText('resume')}
                    </Button>
                    
                    {/* Bulk Delete */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleBulkAction('delete')}
                      disabled={bulkActionLoading}
                      className="text-red-600 hover:text-red-700"
                    >
                      {bulkActionLoading ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-1" />
                      )}
                      {getBulkActionButtonText('delete')}
                    </Button>
                  </div>
                )}
              </div>
            )}
            
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors ${
                  selectedAgents.has(agent.id) ? 'ring-2 ring-primary bg-primary/5' : ''
                }`}
              >
                <div className="flex items-center gap-3 flex-1">
                  <Checkbox
                    checked={selectedAgents.has(agent.id)}
                    onCheckedChange={() => handleSelectAgent(agent.id)}
                    disabled={bulkActionLoading || actionLoading === agent.id}
                  />
                  <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-medium">{agent.name}</h3>
                    <Badge className={getStatusColor(agent.status)}>
                      {getStatusText(agent.status)}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-2">
                    {agent.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Created {formatDate(agent.created_at)}
                    </div>
                    {agent.total_calls && (
                      <div className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {agent.total_calls} calls
                      </div>
                    )}
                    {agent.last_call_at && (
                      <div className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        Last call {formatDate(agent.last_call_at)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
                
              <div className="flex items-center gap-2">
                  {/* Copy Agent ID */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(agent.id, 'Agent ID')}
                    title="Copy Agent ID"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  
                  {/* Status Actions */}
                  {agent.status === 'active' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAction('pause', agent.id)}
                      disabled={actionLoading === agent.id}
                      title="Pause Agent"
                    >
                      {actionLoading === agent.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Pause className="h-4 w-4" />
                      )}
                    </Button>
                  ) : agent.status === 'paused' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAction('resume', agent.id)}
                      disabled={actionLoading === agent.id}
                      title="Resume Agent"
                    >
                      {actionLoading === agent.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  ) : null}
                  
                  {/* Edit Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(`/create-assistant?edit=${agent.id}`, '_blank')}
                    title="Edit Agent"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  
                  {/* Delete Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete "${agent.name}"? This action cannot be undone.`)) {
                        handleAction('delete', agent.id);
                      }
                    }}
                    disabled={actionLoading === agent.id}
                    title="Delete Agent"
                    className="text-red-600 hover:text-red-700"
                  >
                    {actionLoading === agent.id ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default VoiceAgentManagement;
