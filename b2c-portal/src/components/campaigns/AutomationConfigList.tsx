import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Bot,
  Calendar,
  Edit,
  Trash2,
  Play,
  Pause,
  Search,
  Plus,
  ExternalLink,
  Clock,
  Loader2,
  Filter
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  automationOrchestrationService,
  type AutomationConfig
} from '@/services/AutomationOrchestrationService';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AutomationConfigListProps {
  onEditConfig: (configId: string) => void;
  onCreateNew: () => void;
}

export const AutomationConfigList: React.FC<AutomationConfigListProps> = ({
  onEditConfig,
  onCreateNew
}) => {
  const [configs, setConfigs] = useState<AutomationConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadConfigs();
  }, [statusFilter]);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const filters = statusFilter !== 'all' ? { status: statusFilter as any } : undefined;
      const result = await automationOrchestrationService.listConfigurations(filters);
      setConfigs(result.configurations);
    } catch (error) {
      toast({
        title: "Load Failed",
        description: "Failed to load automation configurations",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async (config: AutomationConfig) => {
    setActionLoading(config.id);
    try {
      const result = await automationOrchestrationService.deployConfiguration(config.id);
      if (result.success) {
        await loadConfigs(); // Refresh the list
        toast({
          title: "Deployed Successfully",
          description: `"${config.automationName}" is now active`
        });
      } else {
        throw new Error(result.error || 'Deployment failed');
      }
    } catch (error) {
      toast({
        title: "Deployment Failed",
        description: error instanceof Error ? error.message : "Failed to deploy automation",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async (config: AutomationConfig) => {
    const confirmed = window.confirm(
      `Are you sure you want to stop "${config.automationName}"?`
    );
    if (!confirmed) return;

    setActionLoading(config.id);
    try {
      const result = await automationOrchestrationService.stopConfiguration(config.id);
      if (result.success) {
        await loadConfigs(); // Refresh the list
        toast({
          title: "Stopped Successfully",
          description: `"${config.automationName}" has been stopped`
        });
      } else {
        throw new Error(result.error || 'Stop failed');
      }
    } catch (error) {
      toast({
        title: "Stop Failed",
        description: error instanceof Error ? error.message : "Failed to stop automation",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (config: AutomationConfig) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${config.automationName}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setActionLoading(config.id);
    try {
      await automationOrchestrationService.deleteConfiguration(config.id);
      await loadConfigs(); // Refresh the list
      toast({
        title: "Deleted Successfully",
        description: `"${config.automationName}" has been deleted`
      });
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: error instanceof Error ? error.message : "Failed to delete automation",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDuplicate = async (config: AutomationConfig) => {
    const newName = prompt(`Enter a name for the duplicate:`, `${config.automationName} (Copy)`);
    if (!newName) return;

    setActionLoading(config.id);
    try {
      await automationOrchestrationService.duplicateConfiguration(config.id, newName);
      await loadConfigs(); // Refresh the list
      toast({
        title: "Duplicated Successfully",
        description: `"${newName}" has been created`
      });
    } catch (error) {
      toast({
        title: "Duplicate Failed",
        description: error instanceof Error ? error.message : "Failed to duplicate automation",
        variant: "destructive"
      });
    } finally {
      setActionLoading(null);
    }
  };

  const filteredConfigs = configs.filter(config =>
    config.automationName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    config.companyInfo.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'deployed':
        return <Badge className="bg-green-100 text-green-800 border-green-200">✅ Active</Badge>;
      case 'stopped':
        return <Badge className="bg-red-100 text-red-800 border-red-200">⏸️ Stopped</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800 border-gray-200">📝 Draft</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading automations...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Automation Configurations</h2>
          <p className="text-gray-600">Manage your saved automation configurations</p>
        </div>
        <Button onClick={onCreateNew} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create New
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
          <Input
            placeholder="Search automations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="deployed">Active</SelectItem>
            <SelectItem value="stopped">Stopped</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Config List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredConfigs.map((config) => (
          <Card key={config.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg truncate">{config.automationName}</CardTitle>
                  <CardDescription className="mt-1">
                    {config.companyInfo.name}
                  </CardDescription>
                </div>
                {getStatusBadge(config.status)}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Quick Info */}
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-gray-600" />
                  <span>Voice: {config.vapiAgent.voiceSettings.voiceId}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-600" />
                  <span>Updated: {formatDate(config.updatedAt)}</span>
                </div>
              </div>

              {/* Demo URL */}
              {config.demoSettings.enableDemo && config.demoSettings.demoUrl && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(config.demoSettings.demoUrl, '_blank')}
                  className="w-full flex items-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  View Demo
                </Button>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEditConfig(config.id)}
                  className="flex-1"
                >
                  <Edit className="h-4 w-4" />
                </Button>

                {config.status === 'draft' || config.status === 'stopped' ? (
                  <Button
                    size="sm"
                    onClick={() => handleDeploy(config)}
                    disabled={actionLoading === config.id}
                    className="flex-1"
                  >
                    {actionLoading === config.id ? (
                      <Clock className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleStop(config)}
                    disabled={actionLoading === config.id}
                    className="flex-1"
                  >
                    {actionLoading === config.id ? (
                      <Clock className="h-4 w-4 animate-spin" />
                    ) : (
                      <Pause className="h-4 w-4" />
                    )}
                  </Button>
                )}

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(config)}
                  disabled={actionLoading === config.id}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>

              {/* Duplicate button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDuplicate(config)}
                disabled={actionLoading === config.id}
                className="w-full"
              >
                Create Copy
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredConfigs.length === 0 && (
        <div className="text-center py-12">
          <Bot className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No automations found</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || statusFilter !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Create your first automation to get started'}
          </p>
          {!searchTerm && statusFilter === 'all' && (
            <Button onClick={onCreateNew} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Create Your First Automation
            </Button>
          )}
        </div>
      )}
    </div>
  );
};