import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { 
  Play, 
  Pause, 
  Square, 
  Download, 
  Calendar,
  BarChart3,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Phone,
  MessageSquare
} from 'lucide-react';

interface CampaignActionsProps {
  campaign: any;
  onAction: (action: string, campaignId: string, data?: any) => Promise<void>;
}

interface ExportOptions {
  format: 'csv' | 'json' | 'xlsx';
  includeDetails: boolean;
  dateRange: 'all' | 'last7days' | 'last30days' | 'custom';
  customStartDate?: string;
  customEndDate?: string;
}

const CampaignActions: React.FC<CampaignActionsProps> = ({ campaign, onAction }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    includeDetails: true,
    dateRange: 'all'
  });
  const { toast } = useToast();

  const handleAction = async (action: string, data?: any) => {
    setIsLoading(true);
    try {
      await onAction(action, campaign.id, data);
      
      const actionMessages = {
        start: { title: "Campaign started", description: `${campaign.name} is now running` },
        pause: { title: "Campaign paused", description: `${campaign.name} has been paused` },
        resume: { title: "Campaign resumed", description: `${campaign.name} is now running again` },
        stop: { title: "Campaign stopped", description: `${campaign.name} has been stopped` },
        export: { title: "Export completed", description: "Campaign results have been exported" }
      };

      const message = actionMessages[action as keyof typeof actionMessages];
      if (message) {
        toast({
          title: message.title,
          description: message.description,
          variant: "default"
        });
      }

      if (action === 'export') {
        setExportDialogOpen(false);
      }
    } catch (error) {
      console.error(`Failed to ${action} campaign:`, error);
      toast({
        title: `Failed to ${action} campaign`,
        description: error.message || "An error occurred",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getActionButton = () => {
    switch (campaign.status) {
      case 'running':
        return (
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleAction('pause')}
            disabled={isLoading}
            className="border-accent/20 hover:border-accent"
          >
            <Pause className="h-4 w-4 mr-2" />
            Pause
          </Button>
        );
      case 'paused':
        return (
          <Button 
            size="sm"
            onClick={() => handleAction('resume')}
            disabled={isLoading}
            className="bg-gradient-premium text-accent-foreground shadow-accent"
          >
            <Play className="h-4 w-4 mr-2" />
            Resume
          </Button>
        );
      case 'scheduled':
        return (
          <Button 
            size="sm"
            onClick={() => handleAction('start')}
            disabled={isLoading}
            className="bg-gradient-premium text-accent-foreground shadow-accent"
          >
            <Play className="h-4 w-4 mr-2" />
            Start
          </Button>
        );
      case 'completed':
        return (
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleAction('start')}
            disabled={isLoading}
            className="border-accent/20 hover:border-accent"
          >
            <Play className="h-4 w-4 mr-2" />
            Restart
          </Button>
        );
      default:
        return (
          <Button 
            size="sm"
            onClick={() => handleAction('start')}
            disabled={isLoading}
            className="bg-gradient-premium text-accent-foreground shadow-accent"
          >
            <Play className="h-4 w-4 mr-2" />
            Start
          </Button>
        );
    }
  };

  const getStatusInfo = () => {
    const statusInfo = {
      running: {
        icon: <Play className="h-4 w-4 text-green-400" />,
        color: 'bg-green-500/20 text-green-600 border-green-500/30',
        description: 'Campaign is actively running'
      },
      paused: {
        icon: <Pause className="h-4 w-4 text-yellow-400" />,
        color: 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30',
        description: 'Campaign is paused'
      },
      scheduled: {
        icon: <Calendar className="h-4 w-4 text-blue-400" />,
        color: 'bg-blue-500/20 text-blue-600 border-blue-500/30',
        description: 'Campaign is scheduled to run'
      },
      completed: {
        icon: <CheckCircle className="h-4 w-4 text-green-400" />,
        color: 'bg-green-500/20 text-green-600 border-green-500/30',
        description: 'Campaign has completed'
      },
      stopped: {
        icon: <Square className="h-4 w-4 text-red-400" />,
        color: 'bg-red-500/20 text-red-600 border-red-500/30',
        description: 'Campaign has been stopped'
      }
    };

    return statusInfo[campaign.status as keyof typeof statusInfo] || statusInfo.running;
  };

  const exportResults = async () => {
    const exportData = {
      ...exportOptions,
      campaignId: campaign.id,
      campaignName: campaign.name
    };
    
    await handleAction('export', exportData);
  };

  const generateExportFilename = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    const format = exportOptions.format.toUpperCase();
    return `${campaign.name.replace(/[^a-zA-Z0-9]/g, '_')}_results_${timestamp}.${exportOptions.format}`;
  };

  return (
    <div className="flex space-x-3">
      {/* Status Badge */}
      <div className="flex items-center gap-2">
        {getStatusInfo().icon}
        <Badge className={`${getStatusInfo().color} border`}>
          {campaign.status}
        </Badge>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2">
        {getActionButton()}
        
        {campaign.status === 'running' && (
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleAction('stop')}
            disabled={isLoading}
            className="border-red-500/20 hover:border-red-500 text-red-600"
          >
            <Square className="h-4 w-4 mr-2" />
            Stop
          </Button>
        )}

        <Button size="sm" variant="outline">
          <Calendar className="h-4 w-4 mr-2" />
          Schedule
        </Button>

        <Button size="sm" variant="outline">
          <BarChart3 className="h-4 w-4 mr-2" />
          Analytics
        </Button>

        {/* Export Dialog */}
        <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md bg-gradient-card border-accent/20 shadow-glow">
            <DialogHeader>
              <DialogTitle className="text-xl font-playfair text-accent">
                Export Campaign Results
              </DialogTitle>
              <DialogDescription className="text-gray-600">
                Export {campaign.name} results and analytics
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="export-format">Export Format</Label>
                <Select 
                  value={exportOptions.format} 
                  onValueChange={(value: 'csv' | 'json' | 'xlsx') => 
                    setExportOptions(prev => ({ ...prev, format: value }))
                  }
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="date-range">Date Range</Label>
                <Select 
                  value={exportOptions.dateRange} 
                  onValueChange={(value: 'all' | 'last7days' | 'last30days' | 'custom') => 
                    setExportOptions(prev => ({ ...prev, dateRange: value }))
                  }
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Time</SelectItem>
                    <SelectItem value="last7days">Last 7 Days</SelectItem>
                    <SelectItem value="last30days">Last 30 Days</SelectItem>
                    <SelectItem value="custom">Custom Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {exportOptions.dateRange === 'custom' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="start-date">Start Date</Label>
                    <input
                      type="date"
                      id="start-date"
                      value={exportOptions.customStartDate || ''}
                      onChange={(e) => setExportOptions(prev => ({ 
                        ...prev, 
                        customStartDate: e.target.value 
                      }))}
                      className="w-full mt-1 px-3 py-2 border border-accent/20 rounded-md bg-input/50 focus:border-accent focus:outline-none"
                    />
                  </div>
                  <div>
                    <Label htmlFor="end-date">End Date</Label>
                    <input
                      type="date"
                      id="end-date"
                      value={exportOptions.customEndDate || ''}
                      onChange={(e) => setExportOptions(prev => ({ 
                        ...prev, 
                        customEndDate: e.target.value 
                      }))}
                      className="w-full mt-1 px-3 py-2 border border-accent/20 rounded-md bg-input/50 focus:border-accent focus:outline-none"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="include-details"
                  checked={exportOptions.includeDetails}
                  onChange={(e) => setExportOptions(prev => ({ 
                    ...prev, 
                    includeDetails: e.target.checked 
                  }))}
                  className="rounded border-accent/20 focus:border-accent"
                />
                <Label htmlFor="include-details" className="text-sm">
                  Include detailed conversation logs
                </Label>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setExportDialogOpen(false)}
                  className="border-accent/20 hover:border-accent"
                >
                  Cancel
                </Button>
                <Button
                  onClick={exportResults}
                  disabled={isLoading}
                  className="bg-gradient-premium text-accent-foreground shadow-accent"
                >
                  {isLoading ? (
                    <>
                      <div className="h-4 w-4 border-2 border-accent-foreground border-t-transparent rounded-full animate-spin mr-2" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Export Results
                    </>
                  )}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default CampaignActions; 