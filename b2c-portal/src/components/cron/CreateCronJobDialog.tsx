/**
 * Create Cron Job Dialog Component
 *
 * Dialog for creating custom cron jobs with webhook or script execution.
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info } from 'lucide-react';
import { cronManagementService } from '@/services/CronManagementService';
import { useToast } from '@/hooks/use-toast';

interface CreateCronJobDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const CreateCronJobDialog: React.FC<CreateCronJobDialogProps> = ({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const { toast } = useToast();

  const [jobName, setJobName] = useState('');
  const [description, setDescription] = useState('');
  const [cronExpression, setCronExpression] = useState('');
  const [jobType, setJobType] = useState('custom');
  const [executionType, setExecutionType] = useState<'webhook' | 'script'>('webhook');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [scriptPath, setScriptPath] = useState('');
  const [creating, setCreating] = useState(false);

  const handleSubmit = async () => {
    // Validation
    if (!jobName.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Job name is required',
        variant: 'destructive',
      });
      return;
    }

    if (!cronExpression.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Cron expression is required',
        variant: 'destructive',
      });
      return;
    }

    if (executionType === 'webhook' && !webhookUrl.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Webhook URL is required',
        variant: 'destructive',
      });
      return;
    }

    if (executionType === 'script' && !scriptPath.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Script path is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setCreating(true);

      await cronManagementService.createCronJob({
        name: jobName,
        description: description || `Custom ${executionType} job`,
        cron_expression: cronExpression,
        job_type: jobType,
        webhook_url: executionType === 'webhook' ? webhookUrl : undefined,
        script_path: executionType === 'script' ? scriptPath : undefined,
      });

      toast({
        title: 'Success',
        description: `Cron job "${jobName}" created successfully`,
      });

      // Reset form
      setJobName('');
      setDescription('');
      setCronExpression('');
      setWebhookUrl('');
      setScriptPath('');

      onOpenChange(false);
      onSuccess();
    } catch (error) {
      toast({
        title: 'Failed to create job',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setCreating(false);
    }
  };

  const cronExamples = [
    { label: 'Every 5 minutes', value: '*/5 * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Every 6 hours', value: '0 */6 * * *' },
    { label: 'Daily at 2 AM', value: '0 2 * * *' },
    { label: 'Daily at 9 AM', value: '0 9 * * *' },
    { label: 'Weekly (Monday 9 AM)', value: '0 9 * * 1' },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Cron Job</DialogTitle>
          <DialogDescription>
            Create a custom cron job that runs on a schedule. You can call a webhook or execute a script.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Basic Info */}
          <div>
            <Label htmlFor="jobName">Job Name *</Label>
            <Input
              id="jobName"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              placeholder="e.g., Daily Backup"
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this job does..."
              rows={2}
            />
          </div>

          {/* Cron Expression */}
          <div>
            <Label htmlFor="cronExpression">Cron Expression *</Label>
            <Input
              id="cronExpression"
              value={cronExpression}
              onChange={(e) => setCronExpression(e.target.value)}
              placeholder="e.g., 0 */6 * * *"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Format: minute hour day month day_of_week
            </p>

            {/* Examples */}
            <div className="mt-2 grid grid-cols-2 gap-2">
              {cronExamples.map((example) => (
                <Button
                  key={example.value}
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="justify-start text-xs h-8"
                  onClick={() => setCronExpression(example.value)}
                >
                  <span className="font-normal text-muted-foreground">{example.label}:</span>
                  <span className="ml-1 font-mono">{example.value}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Job Type */}
          <div>
            <Label htmlFor="jobType">Job Type</Label>
            <Select value={jobType} onValueChange={setJobType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="custom">Custom</SelectItem>
                <SelectItem value="system">System</SelectItem>
                <SelectItem value="campaign">Campaign</SelectItem>
                <SelectItem value="maintenance">Maintenance</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Execution Type */}
          <div>
            <Label>Execution Type *</Label>
            <Tabs value={executionType} onValueChange={(v) => setExecutionType(v as 'webhook' | 'script')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="webhook">Webhook</TabsTrigger>
                <TabsTrigger value="script">Script</TabsTrigger>
              </TabsList>

              <TabsContent value="webhook" className="space-y-2">
                <Label htmlFor="webhookUrl">Webhook URL *</Label>
                <Input
                  id="webhookUrl"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://api.example.com/webhook"
                  type="url"
                />
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    The webhook will receive a POST request with job details (job_id, job_name, timestamp)
                  </AlertDescription>
                </Alert>
              </TabsContent>

              <TabsContent value="script" className="space-y-2">
                <Label htmlFor="scriptPath">Script Path *</Label>
                <Input
                  id="scriptPath"
                  value={scriptPath}
                  onChange={(e) => setScriptPath(e.target.value)}
                  placeholder="/path/to/script.sh"
                />
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    The script must be executable and accessible by the backend service user
                  </AlertDescription>
                </Alert>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={creating}>
            {creating ? 'Creating...' : 'Create Job'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateCronJobDialog;
