import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Calendar, Users, Settings } from 'lucide-react';
import { useConfirmationHelpers } from '@/hooks/use-confirmation';

interface NewCampaignDialogProps {
  trigger?: React.ReactNode;
  assistants: Array<{ id: string; name: string; channel: string }>;
  audiences: Array<{ id: string; name: string; size: number }>;
  onCreateCampaign: (campaign: any) => void;
}

export const NewCampaignDialog = ({ trigger, assistants, audiences, onCreateCampaign }: NewCampaignDialogProps) => {
  const [open, setOpen] = useState(false);
  const { confirmCancel, ConfirmationDialog } = useConfirmationHelpers();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    assistantId: '',
    audienceId: '',
    schedule: 'immediate',
    scheduledDate: '',
    scheduledTime: '',
    pacing: {
      ccr: 0.3,
      retries: 2,
      retryDelayMin: 60
    }
  });

  const hasUnsavedChanges = () => {
    return (
      formData.name.trim() !== '' ||
      formData.description.trim() !== '' ||
      formData.assistantId !== '' ||
      formData.audienceId !== '' ||
      formData.scheduledDate !== '' ||
      formData.scheduledTime !== ''
    );
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      assistantId: '',
      audienceId: '',
      schedule: 'immediate',
      scheduledDate: '',
      scheduledTime: '',
      pacing: {
        ccr: 0.3,
        retries: 2,
        retryDelayMin: 60
      }
    });
  };

  const handleCancel = async () => {
    if (hasUnsavedChanges()) {
      const confirmed = await confirmCancel();
      if (confirmed) {
        resetForm();
        setOpen(false);
      }
    } else {
      setOpen(false);
    }
  };

  const handleSubmit = () => {
    const selectedAudience = audiences.find(a => a.id === formData.audienceId);
    const selectedAssistant = assistants.find(a => a.id === formData.assistantId);
    
    const newCampaign = {
      id: Date.now().toString(),
      name: formData.name,
      description: formData.description,
      assistant_id: formData.assistantId,
      audience_size: selectedAudience?.size || 0,
      status: formData.schedule === 'immediate' ? 'running' : 'scheduled',
      created_at: new Date().toISOString(),
      stats: {
        dialed: 0,
        connected: 0,
        completed: 0
      },
      schedule: formData.schedule === 'scheduled' ? {
        date: formData.scheduledDate,
        time: formData.scheduledTime
      } : {},
      pacing: formData.pacing
    };

    onCreateCampaign(newCampaign);
    resetForm();
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Campaign</DialogTitle>
          <DialogDescription>
            Set up a new outreach campaign with your selected assistant and audience.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="basics" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basics">Campaign Details</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="basics" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Campaign Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Q1 Lead Generation Campaign"
                />
              </div>

              <div>
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe the goal and strategy of this campaign..."
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="assistant">Select Assistant</Label>
                <Select value={formData.assistantId} onValueChange={(value) => setFormData(prev => ({ ...prev, assistantId: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an assistant for this campaign" />
                  </SelectTrigger>
                  <SelectContent>
                    {assistants.map((assistant) => (
                      <SelectItem key={assistant.id} value={assistant.id}>
                        <div className="flex items-center gap-2">
                          <span>{assistant.name}</span>
                          <span className="text-xs text-gray-600">({assistant.channel})</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="audience">Select Audience</Label>
                <Select value={formData.audienceId} onValueChange={(value) => setFormData(prev => ({ ...prev, audienceId: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose your target audience" />
                  </SelectTrigger>
                  <SelectContent>
                    {audiences.map((audience) => (
                      <SelectItem key={audience.id} value={audience.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>{audience.name}</span>
                          <span className="text-xs text-gray-600 ml-2">{audience.size.toLocaleString()} contacts</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="schedule" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Campaign Schedule
                </CardTitle>
                <CardDescription>
                  Choose when to start your campaign
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="immediate"
                      name="schedule"
                      value="immediate"
                      checked={formData.schedule === 'immediate'}
                      onChange={(e) => setFormData(prev => ({ ...prev, schedule: e.target.value }))}
                      className="text-indigo-600"
                    />
                    <Label htmlFor="immediate">Start immediately</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="scheduled"
                      name="schedule"
                      value="scheduled"
                      checked={formData.schedule === 'scheduled'}
                      onChange={(e) => setFormData(prev => ({ ...prev, schedule: e.target.value }))}
                      className="text-indigo-600"
                    />
                    <Label htmlFor="scheduled">Schedule for later</Label>
                  </div>

                  {formData.schedule === 'scheduled' && (
                    <div className="ml-6 grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="date">Date</Label>
                        <Input
                          id="date"
                          type="date"
                          value={formData.scheduledDate}
                          onChange={(e) => setFormData(prev => ({ ...prev, scheduledDate: e.target.value }))}
                        />
                      </div>
                      <div>
                        <Label htmlFor="time">Time</Label>
                        <Input
                          id="time"
                          type="time"
                          value={formData.scheduledTime}
                          onChange={(e) => setFormData(prev => ({ ...prev, scheduledTime: e.target.value }))}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Campaign Settings
                </CardTitle>
                <CardDescription>
                  Configure call pacing and retry settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="ccr">Call Connection Rate (0.1 - 1.0)</Label>
                  <Input
                    id="ccr"
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="1.0"
                    value={formData.pacing.ccr}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      pacing: { ...prev.pacing, ccr: parseFloat(e.target.value) }
                    }))}
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Controls how aggressively calls are made (0.3 = moderate pace)
                  </p>
                </div>

                <div>
                  <Label htmlFor="retries">Max Retries</Label>
                  <Input
                    id="retries"
                    type="number"
                    min="0"
                    max="5"
                    value={formData.pacing.retries}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      pacing: { ...prev.pacing, retries: parseInt(e.target.value) }
                    }))}
                  />
                </div>

                <div>
                  <Label htmlFor="retryDelay">Retry Delay (minutes)</Label>
                  <Input
                    id="retryDelay"
                    type="number"
                    min="5"
                    max="1440"
                    value={formData.pacing.retryDelayMin}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      pacing: { ...prev.pacing, retryDelayMin: parseInt(e.target.value) }
                    }))}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={!formData.name || !formData.assistantId || !formData.audienceId}
          >
            Create Campaign
          </Button>
        </div>
      </DialogContent>
      
      {/* Confirmation Dialog */}
      <ConfirmationDialog />
    </Dialog>
  );
};