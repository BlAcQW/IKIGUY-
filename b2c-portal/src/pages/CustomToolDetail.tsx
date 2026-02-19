/**
 * Custom Tool Detail Page
 *
 * Detailed view of a single custom tool with configuration and logs.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowLeft,
  Wrench,
  Settings,
  FileText,
  CheckCircle,
  AlertTriangle,
  Activity,
  Edit,
  Trash2,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { customToolsService } from '@/services/CustomToolsService';
import { ToolCallLogsTable } from '@/components/tool-calls/ToolCallLogsTable';
import { format } from 'date-fns';

interface CustomTool {
  id: string;
  name: string;
  description: string;
  tool_type: string;
  client_id?: string;
  is_active: boolean;
  config: any;
  created_at: string;
  updated_at: string;
}

/**
 * Map client_id to knowledge base company_name.
 * This is needed because tool call logs use the knowledge base company_name,
 * not the tool name.
 */
const getCompanyNameForTool = (tool: CustomTool): string => {
  // Map client_id to knowledge base company_name
  const clientToCompanyMap: Record<string, string> = {
    'premier-health': 'premier_health_production',
    'ghana-tourism': 'ghana_tourism_production',
    // Add more mappings as needed
  };

  if (tool.client_id && clientToCompanyMap[tool.client_id]) {
    return clientToCompanyMap[tool.client_id];
  }

  // Fallback to tool name if no mapping found
  return tool.name;
};

const CustomToolDetail: React.FC = () => {
  const { toolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [tool, setTool] = useState<CustomTool | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('config');

  // Delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Fetch tool details
  const fetchTool = async () => {
    if (!toolId) return;

    setLoading(true);
    try {
      const response = await customToolsService.getCustomToolById(toolId);
      // Response has structure: { success, tool, error }
      if (response.success && response.tool) {
        setTool(response.tool);
      } else {
        throw new Error(response.error || 'Tool not found');
      }
    } catch (error) {
      console.error('Error fetching tool:', error);
      toast({
        title: 'Failed to load tool',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
      navigate('/custom-tools');
    } finally {
      setLoading(false);
    }
  };

  // Delete tool
  const handleDelete = async () => {
    if (!tool) return;

    setDeleting(true);
    try {
      await customToolsService.deleteCustomTool(tool.id);
      toast({
        title: 'Tool deleted',
        description: `${tool.name} has been successfully removed.`,
      });
      navigate('/custom-tools');
    } catch (error) {
      console.error('Error deleting tool:', error);
      toast({
        title: 'Failed to delete tool',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  useEffect(() => {
    fetchTool();
  }, [toolId]);

  if (loading || !tool) {
    return (
      <div className="flex h-screen bg-gray-50">
        <DashboardSidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-gray-600">Loading tool details...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/custom-tools')}
                className="mb-3"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Custom Tools
              </Button>

              <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <Wrench className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold">{tool.name}</h1>
                    {tool.is_active ? (
                      <Badge variant="default" className="bg-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Inactive
                      </Badge>
                    )}
                    <Badge variant="outline" className="capitalize">
                      {tool.tool_type}
                    </Badge>
                  </div>
                  <p className="text-gray-600">{tool.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                    <span>Created: {format(new Date(tool.created_at), 'PPP')}</span>
                    <span>Updated: {format(new Date(tool.updated_at), 'PPP')}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  toast({
                    title: 'Edit functionality',
                    description: 'Tool editing will be implemented in the next phase.',
                  });
                }}
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs Content */}
        <div className="flex-1 overflow-auto p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="mb-6">
              <TabsTrigger value="config" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Configuration
              </TabsTrigger>
              <TabsTrigger value="logs" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Call Logs
              </TabsTrigger>
              <TabsTrigger value="analytics" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Analytics
              </TabsTrigger>
            </TabsList>

            {/* Configuration Tab */}
            <TabsContent value="config" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tool Configuration</CardTitle>
                  <CardDescription>
                    Manage the configuration and settings for this custom tool
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium mb-1">Tool ID</p>
                        <p className="text-sm text-gray-600 font-mono">{tool.id}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-1">Tool Type</p>
                        <p className="text-sm text-gray-600 capitalize">{tool.tool_type}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-1">Status</p>
                        <p className="text-sm text-gray-600">
                          {tool.is_active ? 'Active' : 'Inactive'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-1">Last Updated</p>
                        <p className="text-sm text-gray-600">
                          {format(new Date(tool.updated_at), 'PPpp')}
                        </p>
                      </div>
                    </div>

                    {/* Configuration Details */}
                    {tool.config && Object.keys(tool.config).length > 0 && (
                      <div className="mt-6">
                        <p className="text-sm font-medium mb-3">Configuration Details</p>
                        <div className="bg-muted p-4 rounded-md">
                          <pre className="text-xs overflow-x-auto">
                            {JSON.stringify(tool.config, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* N8N Configuration (if applicable) */}
              {tool.tool_type === 'n8n' && (
                <Card>
                  <CardHeader>
                    <CardTitle>N8N Integration</CardTitle>
                    <CardDescription>
                      N8N webhook and workflow configuration
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      {tool.config?.webhook_url && (
                        <div>
                          <p className="font-medium mb-1">Webhook URL</p>
                          <p className="text-gray-600 font-mono break-all">
                            {tool.config.webhook_url}
                          </p>
                        </div>
                      )}
                      {tool.config?.workflow_id && (
                        <div>
                          <p className="font-medium mb-1">Workflow ID</p>
                          <p className="text-gray-600 font-mono">
                            {tool.config.workflow_id}
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* VAPI Configuration (if applicable) */}
              {tool.tool_type === 'vapi' && (
                <Card>
                  <CardHeader>
                    <CardTitle>VAPI Integration</CardTitle>
                    <CardDescription>
                      VAPI server configuration for voice interactions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      {tool.config?.server_url && (
                        <div>
                          <p className="font-medium mb-1">Server URL</p>
                          <p className="text-gray-600 font-mono break-all">
                            {tool.config.server_url}
                          </p>
                        </div>
                      )}
                      {tool.config?.api_key && (
                        <div>
                          <p className="font-medium mb-1">API Key</p>
                          <p className="text-gray-600 font-mono">
                            {tool.config.api_key.substring(0, 8)}...
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Logs Tab */}
            <TabsContent value="logs" className="h-full">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Tool Call Logs</CardTitle>
                  <CardDescription>
                    View all calls made to this custom tool
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ToolCallLogsTable
                    companyName={getCompanyNameForTool(tool)}
                    showFilters={true}
                    showExport={true}
                    compact={false}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Analytics Tab */}
            <TabsContent value="analytics" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tool Analytics</CardTitle>
                  <CardDescription>
                    Performance metrics and usage statistics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12 text-gray-600">
                    <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Analytics dashboard coming soon</p>
                    <p className="text-sm mt-2">
                      Track execution count, response times, and error rates
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Custom Tool</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{tool.name}</strong>?
              This action cannot be undone and will remove all associated configurations and logs.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Tool'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CustomToolDetail;
