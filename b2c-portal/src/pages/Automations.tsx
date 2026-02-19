import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { getAuthHeaders } from '@/lib/auth-utils';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Zap,
  Search,
  Filter,
  Plus,
  Play,
  Pause,
  Settings,
  MoreHorizontal,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Wrench,
  ChevronDown,
  Activity,
  Calendar,
  TrendingUp,
  Users,
  ArrowRight,
  Sparkles,
  Edit,
  Trash2,
  LayoutGrid,
  List,
  Download,
  BarChart3,
  Phone,
  Database,
  RefreshCw,
  Shield,
  Mic
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  automationOrchestrationService,
  type AutomationConfig,
  type AutomationStatusResponse as AutomationStatus
} from '@/services/AutomationOrchestrationService';
import { AutomationAnalyticsModal } from '@/components/analytics/AutomationAnalyticsModal';
import { AdminAnalyticsModal } from '@/components/analytics/AdminAnalyticsModal';
import { AutomationSettingsModal } from '@/components/automation/AutomationSettingsModal';
import CampaignManagementModal from '@/components/CampaignManagementModal';
import KnowledgeBaseManagementModal from '@/components/KnowledgeBaseManagementModal';
import { ConversationSettingsModal } from '@/components/automations/ConversationSettingsModal';


const AutomationsRefactored: React.FC = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { user, getTenantId } = useMongoAuth();
  const { currentOrganization, isUniversalAdmin } = useOrganization();
  const [automations, setAutomations] = useState<AutomationConfig[]>([]);
  const [automationStats, setAutomationStats] = useState<Record<string, AutomationStatus>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table'); // Default to table view
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [showImportModal, setShowImportModal] = useState(false);
  const [importAssistantId, setImportAssistantId] = useState('');
  const [importAutomationName, setImportAutomationName] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [analyticsModal, setAnalyticsModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [audienceModal, setAudienceModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [knowledgeBaseModal, setKnowledgeBaseModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [adminAnalyticsModal, setAdminAnalyticsModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [settingsModal, setSettingsModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [conversationSettingsModal, setConversationSettingsModal] = useState<{
    isOpen: boolean;
    automation: AutomationConfig | null;
  }>({ isOpen: false, automation: null });
  const [selectedAutomations, setSelectedAutomations] = useState<Set<string>>(new Set());
  const [showBulkDeleteConfirmation, setShowBulkDeleteConfirmation] = useState(false);

  // Fetch automations
  const fetchAutomations = async () => {
    setLoading(true);
    try {
      const response = await automationOrchestrationService.listConfigurations();
      setAutomations(response.configurations);

      // Fetch stats for each automation
      for (const automation of response.configurations) {
        fetchAutomationStats(automation.id);
      }
    } catch (error) {
      console.error('Error fetching automations:', error);
      toast({
        title: "Failed to load automations",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch automation stats
  const fetchAutomationStats = async (automationId: string) => {
    try {
      const stats = await automationOrchestrationService.getConfigurationStatus(automationId);
      setAutomationStats(prev => ({
        ...prev,
        [automationId]: stats
      }));
    } catch (error) {
      console.error(`Error fetching stats for automation ${automationId}:`, error);
    }
  };

  // Deploy automation
  const handleDeployAutomation = async (automationId: string) => {
    try {
      const result = await automationOrchestrationService.deployConfiguration(automationId);

      if (result.success) {
        toast({
          title: "Automation deployed",
          description: "Your automation has been deployed successfully."
        });
        fetchAutomations();
      } else {
        toast({
          title: "Failed to deploy automation",
          description: result.error,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error deploying automation:', error);
      toast({
        title: "Failed to deploy automation",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Stop automation
  const handleStopAutomation = async (automationId: string) => {
    try {
      const result = await automationOrchestrationService.stopConfiguration(automationId);

      if (result.success) {
        toast({
          title: "Automation stopped",
          description: "Your automation has been stopped."
        });
        fetchAutomations();
      } else {
        toast({
          title: "Failed to stop automation",
          description: result.error,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error stopping automation:', error);
      toast({
        title: "Failed to stop automation",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Edit automation (continue draft or edit existing)
  const handleEditAutomation = async (automation: AutomationConfig) => {
    // Navigate to deployment wizard with existing config
    navigate('/automations/deploy', {
      state: {
        existingConfig: automation,
        isEditing: true
      }
    });
  };

  // Pull VAPI config (sync from VAPI)
  const handlePullVapiConfig = async (automationId: string, automationName: string) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://flow-api.ailabsafrica.com';
      const headers = await getAuthHeaders();

      toast({
        title: "Syncing from VAPI",
        description: `Pulling latest configuration for ${automationName}...`
      });

      const response = await fetch(
        `${API_BASE_URL}/automation-configs/${automationId}/sync-from-vapi?force=true`,
        {
          method: 'POST',
          headers
        }
      );

      if (!response.ok) {
        throw new Error('Failed to sync from VAPI');
      }

      const result = await response.json();

      if (result.success) {
        const changeMessage = result.changed
          ? result.changes_summary?.length > 0
            ? `Updated: ${result.changes_summary.join(', ')}`
            : 'Configuration updated successfully'
          : 'Configuration is already up-to-date';

        toast({
          title: "VAPI Sync Complete",
          description: changeMessage
        });
        fetchAutomations();
      } else {
        toast({
          title: "Sync failed",
          description: result.error || "Failed to sync from VAPI",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error syncing from VAPI:', error);
      toast({
        title: "Sync failed",
        description: "Failed to pull VAPI configuration. Please try again.",
        variant: "destructive"
      });
    }
  };

  // Show delete confirmation dialog
  const showDeleteConfirmation = (automationId: string) => {
    const automation = automations.find(a => a.id === automationId);
    if (automation) {
      setDeleteConfirmation({ isOpen: true, automation });
    }
  };

  // Delete automation
  const handleDeleteAutomation = async () => {
    const automation = deleteConfirmation.automation;
    if (!automation) return;

    try {
      const isDeployed = automation.status === 'deployed';

      // Stop automation first if it's deployed
      if (isDeployed) {
        await automationOrchestrationService.stopConfiguration(automation.id);
      }

      await automationOrchestrationService.deleteConfiguration(automation.id);
      toast({
        title: "Automation deleted",
        description: `${automation.automation_name} has been deleted successfully.`
      });
      fetchAutomations();
      setDeleteConfirmation({ isOpen: false, automation: null });
    } catch (error) {
      console.error('Error deleting automation:', error);
      toast({
        title: "Failed to delete automation",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Toggle individual automation selection
  const toggleAutomationSelection = (automationId: string) => {
    setSelectedAutomations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(automationId)) {
        newSet.delete(automationId);
      } else {
        newSet.add(automationId);
      }
      return newSet;
    });
  };

  // Toggle select all
  const toggleSelectAll = () => {
    if (selectedAutomations.size === filteredAutomations.length) {
      // Deselect all
      setSelectedAutomations(new Set());
    } else {
      // Select all
      setSelectedAutomations(new Set(filteredAutomations.map(a => a.id)));
    }
  };

  // Bulk delete automations
  const handleBulkDeleteAutomations = async () => {
    if (selectedAutomations.size === 0) return;

    try {
      const automationsToDelete = Array.from(selectedAutomations);
      let successCount = 0;
      let failCount = 0;

      for (const automationId of automationsToDelete) {
        try {
          const automation = automations.find(a => a.id === automationId);
          if (!automation) continue;

          const isDeployed = automation.status === 'deployed';

          // Stop automation first if it's deployed
          if (isDeployed) {
            await automationOrchestrationService.stopConfiguration(automationId);
          }

          await automationOrchestrationService.deleteConfiguration(automationId);
          successCount++;
        } catch (error) {
          console.error(`Error deleting automation ${automationId}:`, error);
          failCount++;
        }
      }

      // Show results
      if (successCount > 0) {
        toast({
          title: "Bulk deletion complete",
          description: `Successfully deleted ${successCount} automation${successCount > 1 ? 's' : ''}.${failCount > 0 ? ` Failed to delete ${failCount}.` : ''}`
        });
      } else {
        toast({
          title: "Bulk deletion failed",
          description: "Failed to delete selected automations.",
          variant: "destructive"
        });
      }

      // Clear selection and refresh
      setSelectedAutomations(new Set());
      setShowBulkDeleteConfirmation(false);
      fetchAutomations();
    } catch (error) {
      console.error('Error in bulk delete:', error);
      toast({
        title: "Failed to delete automations",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Trigger test call
  const handleTriggerCall = async (automationId: string, automationName: string) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com';
      const response = await fetch(`${API_BASE_URL}/automation-configs/${automationId}/trigger-call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...await getAuthHeaders()
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to trigger call');
      }

      const result = await response.json();

      toast({
        title: "Call initiated",
        description: `Test call to ${result.customer_number} started successfully. Call ID: ${result.call_id}`
      });
    } catch (error: any) {
      console.error('Error triggering call:', error);
      toast({
        title: "Failed to trigger call",
        description: error.message || "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Import VAPI assistant
  const handleImportAssistant = async () => {
    if (!importAssistantId.trim()) {
      toast({
        title: "Assistant ID required",
        description: "Please enter a VAPI assistant ID.",
        variant: "destructive"
      });
      return;
    }

    setIsImporting(true);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com';
      const response = await fetch(`${API_BASE_URL}/automation-configs/import-vapi-assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...await getAuthHeaders()
        },
        body: JSON.stringify({
          assistant_id: importAssistantId,
          automation_name: importAutomationName || undefined
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to import assistant');
      }

      const importedConfig = await response.json();

      toast({
        title: "Assistant imported successfully",
        description: `${importedConfig.automation_name} has been imported and saved. You can now configure voice settings when editing.`
      });

      // Reset form and close modal
      setImportAssistantId('');
      setImportAutomationName('');
      setShowImportModal(false);

      // Refresh automations list
      fetchAutomations();
      
      // Optionally navigate to edit the imported automation
      // navigate('/automations/deploy', {
      //   state: {
      //     existingConfig: importedConfig,
      //     isEditing: true
      //   }
      // });
    } catch (error: any) {
      console.error('Error importing VAPI assistant:', error);
      toast({
        title: "Failed to import assistant",
        description: error.message || "Please check the assistant ID and try again.",
        variant: "destructive"
      });
    } finally {
      setIsImporting(false);
    }
  };

  // Reason: Fetch automations when component mounts or when organization changes
  // This ensures automations are refreshed when user switches organizations
  useEffect(() => {
    if (currentOrganization) {
      fetchAutomations();
    }
  }, [currentOrganization]);

  // Filter automations
  const filteredAutomations = automations.filter(automation => {
    const matchesSearch = automation.automation_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         automation.config.user_config?.company_info?.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         automation.config.user_config?.company_info?.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || automation.status === statusFilter;
    const matchesType = typeFilter === 'all' ||
                       (typeFilter === 'template' && automation.template_id) ||
                       (typeFilter === 'custom' && !automation.template_id);

    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'deployed':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Deployed</Badge>;
      case 'stopped':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Stopped</Badge>;
      case 'draft':
        return <Badge variant="outline">Draft</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'deployed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'stopped':
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'draft':
        return <Clock className="h-4 w-4 text-gray-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTypeIcon = (automation: AutomationConfig) => {
    if (automation.template_id) {
      return <FileText className="h-4 w-4 text-purple-600" />;
    } else {
      return <Wrench className="h-4 w-4 text-orange-600" />;
    }
  };

  const handleCreateFromTemplate = () => {
    setShowCreateModal(false);
    navigate('/automations/templates');
  };

  const handleCreateCustom = () => {
    setShowCreateModal(false);
    navigate('/automations/custom');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">Loading automations...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Automations</h1>
              <p className="text-gray-600">
                Manage your deployed business automation workflows
              </p>
            </div>

            <div className="flex gap-2">
              {/* Import Button */}
              <Dialog open={showImportModal} onOpenChange={setShowImportModal}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <Download className="h-4 w-4" />
                    Import
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Import VAPI Assistant</DialogTitle>
                    <DialogDescription>
                      Import an existing VAPI assistant to create an automation config
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <label htmlFor="assistant-id" className="text-sm font-medium">
                        VAPI Assistant ID *
                      </label>
                      <Input
                        id="assistant-id"
                        placeholder="e.g., asst_1234567890abcdef"
                        value={importAssistantId}
                        onChange={(e) => setImportAssistantId(e.target.value)}
                        disabled={isImporting}
                      />
                    </div>
                    <div className="grid gap-2">
                      <label htmlFor="automation-name" className="text-sm font-medium">
                        Automation Name (Optional)
                      </label>
                      <Input
                        id="automation-name"
                        placeholder="Custom name for this automation"
                        value={importAutomationName}
                        onChange={(e) => setImportAutomationName(e.target.value)}
                        disabled={isImporting}
                      />
                      <p className="text-xs text-gray-600">
                        Leave blank to use the assistant's name
                      </p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowImportModal(false);
                        setImportAssistantId('');
                        setImportAutomationName('');
                      }}
                      disabled={isImporting}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleImportAssistant}
                      disabled={isImporting || !importAssistantId.trim()}
                    >
                      {isImporting ? "Importing..." : "Import"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              {/* Create Button */}
              <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Automation
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Create New Automation</DialogTitle>
                  <DialogDescription>
                    Choose how you'd like to create your automation workflow
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <Button
                    variant="outline"
                    className="h-auto p-4 justify-start"
                    onClick={handleCreateFromTemplate}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <FileText className="h-5 w-5 text-purple-600" />
                      </div>
                      <div className="text-left">
                        <div className="font-semibold">From Template</div>
                        <div className="text-sm text-gray-600">
                          Start with 148+ pre-built templates
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 ml-auto" />
                  </Button>

                  <Button
                    variant="outline"
                    className="h-auto p-4 justify-start"
                    onClick={handleCreateCustom}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Wrench className="h-5 w-5 text-orange-600" />
                      </div>
                      <div className="text-left">
                        <div className="font-semibold">Custom Automation</div>
                        <div className="text-sm text-gray-600">
                          Build your own workflow from scratch
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 ml-auto" />
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          </div>

          {/* Filters and Bulk Actions */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
              <Input
                placeholder="Search automations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              {/* Bulk Delete Button - Shows when items are selected */}
              {selectedAutomations.size > 0 && (
                <Button
                  variant="destructive"
                  onClick={() => setShowBulkDeleteConfirmation(true)}
                  className="gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete ({selectedAutomations.size})
                </Button>
              )}
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="deployed">Deployed</SelectItem>
                  <SelectItem value="stopped">Stopped</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                </SelectContent>
              </Select>

              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="template">Template</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode Toggle */}
              <div className="flex border rounded-md">
                <Button
                  variant={viewMode === 'table' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className="rounded-r-none"
                >
                  <List className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'card' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('card')}
                  className="rounded-l-none"
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Automations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{automations.length}</div>
                <p className="text-xs text-gray-600">
                  {automations.filter(a => a.status === 'deployed').length} deployed
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Object.values(automationStats).length > 0
                    ? Math.round(Object.values(automationStats).reduce((acc, stats) => acc + (stats.successRate || 0), 0) / Object.values(automationStats).length)
                    : 0}%
                </div>
                <p className="text-xs text-gray-600">
                  Average across all automations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Monthly Executions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Object.values(automationStats).reduce((acc, stats) => acc + (stats.callCount || 0), 0)}
                </div>
                <p className="text-xs text-gray-600">
                  Total this month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Templates Used</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {automations.filter(a => a.template_id).length}
                </div>
                <p className="text-xs text-gray-600">
                  From template library
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Automation List/Grid */}
          {filteredAutomations.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-gray-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {automations.length === 0 ? 'No automations deployed' : 'No automations match your filters'}
              </h3>
              <p className="text-gray-600 mb-4">
                {automations.length === 0
                  ? 'Create your first automation to streamline your business processes.'
                  : 'Try adjusting your search or filter criteria.'
                }
              </p>
              {automations.length === 0 && (
                <Button onClick={() => setShowCreateModal(true)} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Automation
                </Button>
              )}
            </Card>
          ) : viewMode === 'table' ? (
            /* Table View */
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedAutomations.size === filteredAutomations.length && filteredAutomations.length > 0}
                        onCheckedChange={toggleSelectAll}
                        aria-label="Select all automations"
                      />
                    </TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAutomations.map((automation) => (
                    <TableRow
                      key={automation.id}
                      className="hover:bg-accent/50"
                    >
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={selectedAutomations.has(automation.id)}
                          onCheckedChange={() => toggleAutomationSelection(automation.id)}
                          aria-label={`Select ${automation.automation_name}`}
                        />
                      </TableCell>
                      <TableCell
                        className="cursor-pointer"
                        onClick={() => handleEditAutomation(automation)}
                      >
                        <div className="flex items-center gap-2">
                          {getStatusIcon(automation.status)}
                          <div>
                            <div className="font-medium">{automation.automation_name}</div>
                            <div className="text-xs text-gray-600">
                              {automation.config.user_config?.company_info?.name}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {getTypeIcon(automation)}
                          <span className="text-xs capitalize">
                            {automation.template_id ? 'template' : 'custom'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(automation.status)}</TableCell>
                      <TableCell className="text-sm text-gray-600">
                        {new Date(automation.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-2">
                          {automation.status === 'deployed' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setAudienceModal({ isOpen: true, automation })}
                              className="gap-1"
                            >
                              <Play className="h-3 w-3" />
                              Manage Campaigns
                            </Button>
                          )}
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {automation.status === 'deployed' && (
                              <>
                                <DropdownMenuItem onClick={() => handleTriggerCall(automation.id, automation.automation_name)}>
                                  <Phone className="h-4 w-4 mr-2 text-green-600" />
                                  Make Test Call
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setAudienceModal({ isOpen: true, automation })}>
                                  <Users className="h-4 w-4 mr-2 text-blue-600" />
                                  Manage Campaigns
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setKnowledgeBaseModal({ isOpen: true, automation })}>
                                  <Database className="h-4 w-4 mr-2 text-purple-600" />
                                  Manage Knowledge Base
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setAnalyticsModal({ isOpen: true, automation })}>
                                  <BarChart3 className="h-4 w-4 mr-2" />
                                  View Analytics
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setConversationSettingsModal({ isOpen: true, automation })}>
                                  <Mic className="h-4 w-4 mr-2 text-purple-600" />
                                  Conversation Settings
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handlePullVapiConfig(automation.id, automation.automation_name)}>
                                  <RefreshCw className="h-4 w-4 mr-2 text-orange-600" />
                                  Pull VAPI Config
                                </DropdownMenuItem>
                                {/* Admin-only menu items */}
                                {isUniversalAdmin && (
                                  <>
                                    <DropdownMenuItem onClick={() => setAdminAnalyticsModal({ isOpen: true, automation })}>
                                      <Shield className="h-4 w-4 mr-2 text-orange-500" />
                                      Admin Analytics
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => setSettingsModal({ isOpen: true, automation })}>
                                      <Settings className="h-4 w-4 mr-2 text-gray-600" />
                                      Cost Settings
                                    </DropdownMenuItem>
                                  </>
                                )}
                              </>
                            )}
                            <DropdownMenuItem onClick={() => handleEditAutomation(automation)}>
                              <Edit className="h-4 w-4 mr-2" />
                              {automation.status === 'draft' ? 'Continue Editing' : 'Edit Configuration'}
                            </DropdownMenuItem>
                            {automation.status === 'deployed' && (
                              <DropdownMenuItem onClick={() => handleStopAutomation(automation.id)}>
                                <Pause className="h-4 w-4 mr-2" />
                                Stop
                              </DropdownMenuItem>
                            )}
                            {automation.status === 'stopped' && (
                              <DropdownMenuItem onClick={() => handleDeployAutomation(automation.id)}>
                                <Play className="h-4 w-4 mr-2 text-green-600" />
                                Deploy
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => showDeleteConfirmation(automation.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              {automation.status === 'draft' ? 'Delete Draft' : 'Delete Automation'}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          ) : (
            /* Card View */
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredAutomations.map((automation) => {
                const stats = automationStats[automation.id];
                return (
                  <Card key={automation.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(automation.status)}
                          <div>
                            <CardTitle className="text-lg">{automation.automation_name}</CardTitle>
                            <CardDescription className="mt-1">
                              {automation.config.user_config?.company_info?.description || 'No description'}
                            </CardDescription>
                          </div>
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {automation.status === 'deployed' && (
                              <>
                                <DropdownMenuItem onClick={() => handleTriggerCall(automation.id, automation.automation_name)}>
                                  <Phone className="h-4 w-4 mr-2 text-green-600" />
                                  Make Test Call
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setAudienceModal({ isOpen: true, automation })}>
                                  <Users className="h-4 w-4 mr-2 text-blue-600" />
                                  Manage Campaigns
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setKnowledgeBaseModal({ isOpen: true, automation })}>
                                  <Database className="h-4 w-4 mr-2 text-purple-600" />
                                  Manage Knowledge Base
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setAnalyticsModal({ isOpen: true, automation })}>
                                  <BarChart3 className="h-4 w-4 mr-2" />
                                  View Analytics
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setConversationSettingsModal({ isOpen: true, automation })}>
                                  <Mic className="h-4 w-4 mr-2 text-purple-600" />
                                  Conversation Settings
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handlePullVapiConfig(automation.id, automation.automation_name)}>
                                  <RefreshCw className="h-4 w-4 mr-2 text-orange-600" />
                                  Pull VAPI Config
                                </DropdownMenuItem>
                                {/* Admin-only menu items */}
                                {isUniversalAdmin && (
                                  <>
                                    <DropdownMenuItem onClick={() => setAdminAnalyticsModal({ isOpen: true, automation })}>
                                      <Shield className="h-4 w-4 mr-2 text-orange-500" />
                                      Admin Analytics
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => setSettingsModal({ isOpen: true, automation })}>
                                      <Settings className="h-4 w-4 mr-2 text-gray-600" />
                                      Cost Settings
                                    </DropdownMenuItem>
                                  </>
                                )}
                              </>
                            )}
                            <DropdownMenuItem onClick={() => handleEditAutomation(automation)}>
                              <Edit className="h-4 w-4 mr-2" />
                              {automation.status === 'draft' ? 'Continue Editing' : 'Edit Configuration'}
                            </DropdownMenuItem>
                            {automation.status === 'deployed' && (
                              <DropdownMenuItem onClick={() => handleStopAutomation(automation.id)}>
                                <Pause className="h-4 w-4 mr-2" />
                                Stop
                              </DropdownMenuItem>
                            )}
                            {automation.status === 'stopped' && (
                              <DropdownMenuItem onClick={() => handleDeployAutomation(automation.id)}>
                                <Play className="h-4 w-4 mr-2 text-green-600" />
                                Deploy
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => showDeleteConfirmation(automation.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              {automation.status === 'draft' ? 'Delete Draft' : 'Delete Automation'}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex items-center gap-1">
                          {getTypeIcon(automation)}
                          <span className="text-xs text-gray-600 capitalize">
                            {automation.template_id ? 'template' : 'custom'}
                          </span>
                        </div>
                        {getStatusBadge(automation.status)}
                        <span className="text-xs text-gray-600">
                          {new Date(automation.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {automation.template_id && (
                        <div className="flex items-center gap-1 mt-1">
                          <Sparkles className="h-3 w-3 text-purple-500" />
                          <span className="text-xs text-purple-600 font-medium">
                            Template ID: {automation.template_id}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center gap-1 mt-1">
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {automation.config.user_config?.company_info?.name}
                        </span>
                      </div>
                    </CardHeader>

                    <CardContent className="space-y-4">
                      {stats && (
                        <>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2">
                              <Activity className="h-4 w-4 text-gray-600" />
                              <div>
                                <div className="font-medium">{stats.callCount || 0}</div>
                                <div className="text-gray-600">Calls</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-gray-600" />
                              <div>
                                <div className="font-medium">{stats.successRate || 0}%</div>
                                <div className="text-gray-600">Success Rate</div>
                              </div>
                            </div>
                          </div>

                          {stats.lastActivity && (
                            <div className="text-xs text-gray-600">
                              <div>Last activity: {new Date(stats.lastActivity).toLocaleDateString()}</div>
                              {stats.uptime && <div>Uptime: {stats.uptime}</div>}
                            </div>
                          )}
                        </>
                      )}

                      <div className="flex gap-2 pt-2">
                        {automation.status === 'draft' ? (
                          <Button
                            size="sm"
                            className="flex-1 gap-2"
                            onClick={() => handleEditAutomation(automation)}
                          >
                            <Edit className="h-3 w-3" />
                            Continue Editing
                          </Button>
                        ) : automation.status === 'stopped' ? (
                          <Button
                            size="sm"
                            className="flex-1 gap-2"
                            onClick={() => handleDeployAutomation(automation.id)}
                          >
                            <Play className="h-3 w-3" />
                            Deploy
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 gap-2"
                            onClick={() => handleStopAutomation(automation.id)}
                          >
                            <Pause className="h-3 w-3" />
                            Stop
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditAutomation(automation)}
                        >
                          Configure
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteConfirmation.isOpen} onOpenChange={(open) =>
        setDeleteConfirmation({ isOpen: open, automation: open ? deleteConfirmation.automation : null })
      }>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Automation</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteConfirmation.automation && (
                <>
                  Are you sure you want to delete "{deleteConfirmation.automation.automation_name}"?
                  {deleteConfirmation.automation.status === 'deployed' && (
                    <span className="block mt-2 text-red-600 font-medium">
                      This will stop the deployed automation and permanently delete all configuration data.
                    </span>
                  )}
                  <span className="block mt-2">This action cannot be undone.</span>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteConfirmation({ isOpen: false, automation: null })}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAutomation}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bulk Delete Confirmation Dialog */}
      <AlertDialog open={showBulkDeleteConfirmation} onOpenChange={setShowBulkDeleteConfirmation}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Multiple Automations</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete {selectedAutomations.size} automation{selectedAutomations.size > 1 ? 's' : ''}?
              {Array.from(selectedAutomations).some(id => {
                const auto = automations.find(a => a.id === id);
                return auto?.status === 'deployed';
              }) && (
                <span className="block mt-2 text-red-600 font-medium">
                  This will stop any deployed automations and permanently delete all configuration data.
                </span>
              )}
              <span className="block mt-2">This action cannot be undone.</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setShowBulkDeleteConfirmation(false)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDeleteAutomations}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete {selectedAutomations.size} Automation{selectedAutomations.size > 1 ? 's' : ''}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Analytics Modal */}
      {analyticsModal.automation && (
        <AutomationAnalyticsModal
          isOpen={analyticsModal.isOpen}
          onClose={() => setAnalyticsModal({ isOpen: false, automation: null })}
          automationId={analyticsModal.automation.id}
          automationName={analyticsModal.automation.automation_name}
        />
      )}

      {/* Campaign Management Modal */}
      {audienceModal.automation && (
        <CampaignManagementModal
          open={audienceModal.isOpen}
          onOpenChange={(open) => setAudienceModal({ isOpen: open, automation: open ? audienceModal.automation : null })}
          automationId={audienceModal.automation.id}
          automationName={audienceModal.automation.automation_name}
          onCampaignCreated={() => {
            fetchAutomations();
            toast({
              title: "Campaign created",
              description: "Your campaign has been created and is ready to start."
            });
          }}
        />
      )}

      {/* Knowledge Base Management Modal */}
      {knowledgeBaseModal.automation && (
        <KnowledgeBaseManagementModal
          open={knowledgeBaseModal.isOpen}
          onOpenChange={(open) => setKnowledgeBaseModal({ isOpen: open, automation: open ? knowledgeBaseModal.automation : null })}
          automationId={knowledgeBaseModal.automation.id}
          automationName={knowledgeBaseModal.automation.automation_name}
        />
      )}

      {/* Conversation Settings Modal */}
      {conversationSettingsModal.automation && (
        <ConversationSettingsModal
          isOpen={conversationSettingsModal.isOpen}
          onClose={() => setConversationSettingsModal({ isOpen: false, automation: null })}
          automation={conversationSettingsModal.automation}
          onSave={() => {
            fetchAutomations();
          }}
        />
      )}

      {/* Admin Analytics Modal (universal_admin only) */}
      {adminAnalyticsModal.automation && (
        <AdminAnalyticsModal
          isOpen={adminAnalyticsModal.isOpen}
          onClose={() => setAdminAnalyticsModal({ isOpen: false, automation: null })}
          automationId={adminAnalyticsModal.automation.id}
          automationName={adminAnalyticsModal.automation.automation_name}
        />
      )}

      {/* Automation Settings Modal (universal_admin only) */}
      {settingsModal.automation && (
        <AutomationSettingsModal
          isOpen={settingsModal.isOpen}
          onClose={() => setSettingsModal({ isOpen: false, automation: null })}
          automationId={settingsModal.automation.id}
          automationName={settingsModal.automation.automation_name}
        />
      )}
    </div>
  );
};

export default AutomationsRefactored;