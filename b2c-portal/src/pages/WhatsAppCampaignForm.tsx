/**
 * WhatsApp Campaign Form Page
 *
 * Multi-step form for creating WhatsApp campaigns with template selection,
 * audience targeting, media upload, and interactive buttons
 */

import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { useOrganization } from '@/contexts/OrganizationContext';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Users,
  Image as ImageIcon,
  MessageSquare,
  Settings,
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  Save,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import { WhatsAppTemplateSelector } from '@/components/whatsapp/WhatsAppTemplateSelector';
import { WhatsAppMediaUploader } from '@/components/whatsapp/WhatsAppMediaUploader';
import { WhatsAppButtonEditor } from '@/components/whatsapp/WhatsAppButtonEditor';
import {
  createWhatsAppCampaign,
  WhatsAppTemplate,
  WhatsAppButton,
  CreateWhatsAppCampaignRequest
} from '@/lib/whatsapp-campaigns-api';

interface CampaignFormData {
  name: string;
  description: string;
  template_name: string;
  audience_id: string;
  phone_number_id: string;
  send_rate_per_second: number;
  batch_size: number;
  retry_failed: boolean;
  max_retries: number;
  scheduled_time: string;
  enable_media: boolean;
  media_url: string;
  media_type: 'image' | 'video' | 'audio' | 'document' | undefined;
  media_caption: string;
  enable_buttons: boolean;
  buttons: WhatsAppButton[];
}

interface Audience {
  id: string;
  name: string;
  size: number;
  status: string;
}

const STEPS = [
  { id: 'basic', title: 'Campaign Info', icon: FileText, description: 'Name and description' },
  { id: 'template', title: 'Template', icon: MessageSquare, description: 'Select WhatsApp template' },
  { id: 'audience', title: 'Audience', icon: Users, description: 'Target recipients' },
  { id: 'media', title: 'Media', icon: ImageIcon, description: 'Optional media attachment' },
  { id: 'buttons', title: 'Buttons', icon: Sparkles, description: 'Interactive buttons' },
  { id: 'settings', title: 'Settings', icon: Settings, description: 'Campaign configuration' }
];

const WhatsAppCampaignForm: React.FC = () => {
  const { toast } = useToast();
  const { currentOrganization } = useOrganization();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<WhatsAppTemplate | null>(null);
  const [templateVariables, setTemplateVariables] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    description: '',
    template_name: '',
    audience_id: '',
    phone_number_id: '',
    send_rate_per_second: 1,
    batch_size: 100,
    retry_failed: true,
    max_retries: 3,
    scheduled_time: '',
    enable_media: false,
    media_url: '',
    media_type: undefined,
    media_caption: '',
    enable_buttons: false,
    buttons: []
  });

  useEffect(() => {
    loadAudiences();
  }, [currentOrganization]);

  const loadAudiences = async () => {
    try {
      // Load audiences from API
      // For now, using placeholder data
      setAudiences([
        { id: '1', name: 'All Customers', size: 1500, status: 'active' },
        { id: '2', name: 'Premium Members', size: 450, status: 'active' },
        { id: '3', name: 'Newsletter Subscribers', size: 2300, status: 'active' }
      ]);
    } catch (error) {
      console.error('Error loading audiences:', error);
    }
  };

  const handleTemplateSelect = (template: WhatsAppTemplate) => {
    setSelectedTemplate(template);
    setFormData(prev => ({ ...prev, template_name: template.name }));
  };

  const handleMediaChange = (config: { url?: string; type?: 'image' | 'video' | 'audio' | 'document'; caption?: string }) => {
    setFormData(prev => ({
      ...prev,
      media_url: config.url || '',
      media_type: config.type,
      media_caption: config.caption || ''
    }));
  };

  const handleButtonsChange = (buttons: WhatsAppButton[]) => {
    setFormData(prev => ({ ...prev, buttons }));
  };

  const validateStep = (step: number): string | null => {
    switch (step) {
      case 0: // Basic Info
        if (!formData.name.trim()) return 'Campaign name is required';
        if (formData.name.length < 3) return 'Campaign name must be at least 3 characters';
        return null;

      case 1: // Template
        if (!selectedTemplate) return 'Please select a WhatsApp template';
        if (!formData.template_name) return 'Template name is required';
        return null;

      case 2: // Audience
        if (!formData.audience_id) return 'Please select an audience';
        return null;

      case 3: // Media
        if (formData.enable_media) {
          if (!formData.media_url) return 'Media URL is required when media is enabled';
          if (!formData.media_type) return 'Media type is required';
        }
        return null;

      case 4: // Buttons
        if (formData.enable_buttons) {
          if (formData.buttons.length === 0) return 'Add at least one button or disable buttons';
          for (const button of formData.buttons) {
            if (!button.title) return 'All buttons must have a title';
            if (button.type === 'url' && !button.url) return 'URL buttons must have a URL';
            if (button.type === 'phone_number' && !button.phone_number) return 'Phone buttons must have a phone number';
          }
        }
        return null;

      case 5: // Settings
        if (!formData.phone_number_id) return 'WhatsApp phone number ID is required';
        if (formData.send_rate_per_second < 0.1 || formData.send_rate_per_second > 1000) {
          return 'Send rate must be between 0.1 and 1000 messages per second';
        }
        return null;

      default:
        return null;
    }
  };

  const handleNext = () => {
    const error = validateStep(currentStep);
    if (error) {
      toast({
        title: "Validation Error",
        description: error,
        variant: "destructive"
      });
      return;
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    // Validate all steps
    for (let i = 0; i < STEPS.length; i++) {
      const error = validateStep(i);
      if (error) {
        toast({
          title: `Validation Error (Step ${i + 1})`,
          description: error,
          variant: "destructive"
        });
        setCurrentStep(i);
        return;
      }
    }

    setLoading(true);
    try {
      const payload: CreateWhatsAppCampaignRequest = {
        name: formData.name,
        template_name: formData.template_name,
        audience_id: formData.audience_id || undefined,
        config: {
          phone_number_id: formData.phone_number_id,
          send_rate_per_second: formData.send_rate_per_second,
          batch_size: formData.batch_size,
          retry_failed: formData.retry_failed,
          max_retries: formData.max_retries,
          scheduled_time: formData.scheduled_time || undefined,
          template_name: formData.template_name,
          enable_media: formData.enable_media,
          media_url: formData.enable_media ? formData.media_url : undefined,
          media_type: formData.enable_media ? formData.media_type : undefined,
          media_caption: formData.enable_media ? formData.media_caption : undefined,
          enable_buttons: formData.enable_buttons,
          buttons: formData.enable_buttons ? formData.buttons : []
        }
      };

      await createWhatsAppCampaign(payload);

      toast({
        title: "Campaign created",
        description: "Your WhatsApp campaign has been created successfully."
      });

      navigate('/whatsapp-campaigns');
    } catch (error: any) {
      console.error('Error creating campaign:', error);
      toast({
        title: "Failed to create campaign",
        description: error.message || "Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const currentStepData = STEPS[currentStep];
  const StepIcon = currentStepData.icon;
  const progress = ((currentStep + 1) / STEPS.length) * 100;

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 pb-12 max-w-4xl">
          {/* Header */}
          <div className="mb-8">
            <Button
              variant="ghost"
              onClick={() => navigate('/whatsapp-campaigns')}
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Campaigns
            </Button>

            <h1 className="text-3xl font-bold text-foreground mb-2">
              Create WhatsApp Campaign
            </h1>
            <p className="text-gray-600">
              Send targeted WhatsApp messages using approved templates
            </p>
          </div>

          {/* Progress Bar */}
          <Card className="mb-8">
            <CardContent className="pt-6">
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">
                    Step {currentStep + 1} of {STEPS.length}: {currentStepData.title}
                  </span>
                  <span className="text-gray-600">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Step Indicators */}
              <div className="flex justify-between">
                {STEPS.map((step, index) => {
                  const Icon = step.icon;
                  const isActive = index === currentStep;
                  const isCompleted = index < currentStep;

                  return (
                    <div
                      key={step.id}
                      className={`flex flex-col items-center gap-2 ${
                        isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-gray-400'
                      }`}
                    >
                      <div
                        className={`p-2 rounded-full ${
                          isActive
                            ? 'bg-primary/10 ring-2 ring-primary'
                            : isCompleted
                            ? 'bg-green-100'
                            : 'bg-muted'
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : (
                          <Icon className="h-5 w-5" />
                        )}
                      </div>
                      <span className="text-xs text-center hidden sm:block">{step.title}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Step Content */}
          <Card className="mb-8">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <StepIcon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>{currentStepData.title}</CardTitle>
                  <CardDescription>{currentStepData.description}</CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Step 1: Basic Info */}
              {currentStep === 0 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Campaign Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Product Launch Announcement"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                    <p className="text-xs text-gray-500">
                      A descriptive name to identify your campaign
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Description (Optional)</Label>
                    <Textarea
                      id="description"
                      placeholder="Describe the purpose and goals of this campaign..."
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={4}
                    />
                  </div>
                </div>
              )}

              {/* Step 2: Template Selection */}
              {currentStep === 1 && (
                <WhatsAppTemplateSelector
                  selectedTemplate={selectedTemplate}
                  onSelect={handleTemplateSelect}
                  variableValues={templateVariables}
                  onVariableChange={setTemplateVariables}
                />
              )}

              {/* Step 3: Audience Selection */}
              {currentStep === 2 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="audience">Select Audience *</Label>
                    <Select
                      value={formData.audience_id}
                      onValueChange={(value) => setFormData({ ...formData, audience_id: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose an audience" />
                      </SelectTrigger>
                      <SelectContent>
                        {audiences.map((audience) => (
                          <SelectItem key={audience.id} value={audience.id}>
                            <div className="flex items-center justify-between w-full">
                              <span>{audience.name}</span>
                              <span className="text-xs text-gray-500 ml-4">
                                {audience.size.toLocaleString()} contacts
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">
                      Select the group of contacts to receive this campaign
                    </p>
                  </div>

                  {formData.audience_id && (
                    <Alert>
                      <Users className="h-4 w-4" />
                      <AlertDescription>
                        {audiences.find(a => a.id === formData.audience_id)?.size.toLocaleString() || 0} contacts
                        will receive this campaign
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Step 4: Media Upload */}
              {currentStep === 3 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="enable_media">Enable Media Attachment</Label>
                      <p className="text-xs text-gray-500">Add images, videos, audio, or documents</p>
                    </div>
                    <Switch
                      id="enable_media"
                      checked={formData.enable_media}
                      onCheckedChange={(checked) => setFormData({ ...formData, enable_media: checked })}
                    />
                  </div>

                  {formData.enable_media && (
                    <WhatsAppMediaUploader
                      mediaConfig={{
                        url: formData.media_url,
                        type: formData.media_type,
                        caption: formData.media_caption
                      }}
                      onChange={handleMediaChange}
                    />
                  )}

                  {!formData.enable_media && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Media attachments are optional. Your campaign will use text-only messages.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Step 5: Interactive Buttons */}
              {currentStep === 4 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="enable_buttons">Enable Interactive Buttons</Label>
                      <p className="text-xs text-gray-500">Add buttons for quick actions</p>
                    </div>
                    <Switch
                      id="enable_buttons"
                      checked={formData.enable_buttons}
                      onCheckedChange={(checked) => setFormData({ ...formData, enable_buttons: checked })}
                    />
                  </div>

                  {formData.enable_buttons && (
                    <WhatsAppButtonEditor
                      buttons={formData.buttons}
                      onChange={handleButtonsChange}
                    />
                  )}

                  {!formData.enable_buttons && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Interactive buttons are optional. Recipients can still reply to your messages normally.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Step 6: Campaign Settings */}
              {currentStep === 5 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone_number_id">WhatsApp Phone Number ID *</Label>
                    <Input
                      id="phone_number_id"
                      placeholder="e.g., 102290129340398"
                      value={formData.phone_number_id}
                      onChange={(e) => setFormData({ ...formData, phone_number_id: e.target.value })}
                    />
                    <p className="text-xs text-gray-500">
                      Your WhatsApp Business phone number ID from Meta Business Suite
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="send_rate">Send Rate (msg/sec)</Label>
                      <Input
                        id="send_rate"
                        type="number"
                        min="0.1"
                        max="1000"
                        step="0.1"
                        value={formData.send_rate_per_second}
                        onChange={(e) =>
                          setFormData({ ...formData, send_rate_per_second: parseFloat(e.target.value) })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="batch_size">Batch Size</Label>
                      <Input
                        id="batch_size"
                        type="number"
                        min="1"
                        max="1000"
                        value={formData.batch_size}
                        onChange={(e) => setFormData({ ...formData, batch_size: parseInt(e.target.value) })}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="retry_failed">Retry Failed Messages</Label>
                      <p className="text-xs text-gray-500">Automatically retry if sending fails</p>
                    </div>
                    <Switch
                      id="retry_failed"
                      checked={formData.retry_failed}
                      onCheckedChange={(checked) => setFormData({ ...formData, retry_failed: checked })}
                    />
                  </div>

                  {formData.retry_failed && (
                    <div className="space-y-2">
                      <Label htmlFor="max_retries">Maximum Retries</Label>
                      <Select
                        value={formData.max_retries.toString()}
                        onValueChange={(value) =>
                          setFormData({ ...formData, max_retries: parseInt(value) })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 4, 5].map((num) => (
                            <SelectItem key={num} value={num.toString()}>
                              {num} {num === 1 ? 'retry' : 'retries'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="scheduled_time">Schedule for Later (Optional)</Label>
                    <Input
                      id="scheduled_time"
                      type="datetime-local"
                      value={formData.scheduled_time}
                      onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                      min={new Date().toISOString().slice(0, 16)}
                    />
                    <p className="text-xs text-gray-500">
                      Leave empty to create as draft and start manually
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 0 || loading}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => navigate('/whatsapp-campaigns')}
                disabled={loading}
              >
                Cancel
              </Button>

              {currentStep < STEPS.length - 1 ? (
                <Button onClick={handleNext} disabled={loading}>
                  Next
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button onClick={handleSubmit} disabled={loading}>
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Create Campaign
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppCampaignForm;
