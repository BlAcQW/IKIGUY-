/**
 * Campaign Creation Wizard
 *
 * Multi-step wizard for creating marketing campaigns across channels:
 * - Step 1: Campaign basics (name, type)
 * - Step 2: Message template (channel-specific content)
 * - Step 3: Audience targeting (segment builder)
 * - Step 4: Review and launch
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Phone, Mail, MessageSquare, MessageCircle, ArrowLeft, ArrowRight, CheckCircle } from 'lucide-react';
import { useCreateCampaign, useSegmentPreview } from '@/hooks/use-campaigns';
import type { CampaignType, CampaignCreate, SegmentFilter, MessageTemplate } from '@/lib/api/campaign-api';

interface CampaignWizardProps {
  open: boolean;
  onClose: () => void;
}

type WizardStep = 1 | 2 | 3 | 4;

interface CampaignFormData {
  name: string;
  campaign_type: CampaignType | '';
  message_template: MessageTemplate;
  segment_filter: SegmentFilter;
}

const CAMPAIGN_TYPES: Array<{ value: CampaignType; label: string; icon: any; description: string }> = [
  {
    value: 'voice',
    label: 'Voice Call',
    icon: Phone,
    description: 'AI-powered voice calls using Vapi assistants',
  },
  {
    value: 'sms',
    label: 'SMS',
    icon: MessageSquare,
    description: 'Text messages via Arkesel',
  },
  {
    value: 'whatsapp',
    label: 'WhatsApp',
    icon: MessageCircle,
    description: 'WhatsApp Business messages',
  },
  {
    value: 'email',
    label: 'Email',
    icon: Mail,
    description: 'Email campaigns via iRedMail',
  },
];

const INTEREST_STATUSES = ['hot', 'warm', 'cold', 'unqualified'];
const LEAD_STATUSES = ['new', 'contacted', 'qualified', 'negotiating', 'converted', 'lost'];
const PROPERTY_TYPES = ['apartment', 'house', 'villa', 'penthouse', 'loft', 'townhouse', 'land', 'commercial'];

export function CampaignWizard({ open, onClose }: CampaignWizardProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    campaign_type: '',
    message_template: {},
    segment_filter: {
      exclude_opted_out: true,
    },
  });

  const createMutation = useCreateCampaign();

  // Segment preview (only fetch when on step 3 or 4)
  const { data: segmentPreview, isLoading: isPreviewLoading } = useSegmentPreview(
    formData.segment_filter,
    formData.campaign_type as CampaignType,
    currentStep >= 3 && !!formData.campaign_type
  );

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep((prev) => (prev + 1) as WizardStep);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as WizardStep);
    }
  };

  const handleSubmit = async () => {
    if (!formData.campaign_type) return;

    const campaignData: CampaignCreate = {
      name: formData.name,
      campaign_type: formData.campaign_type as CampaignType,
      message_template: formData.message_template,
      segment_filter: Object.keys(formData.segment_filter).length > 1
        ? formData.segment_filter
        : undefined,
    };

    createMutation.mutate(campaignData, {
      onSuccess: (campaign) => {
        onClose();
        navigate(`/campaigns/${campaign.id}`);
      },
    });
  };

  const updateFormData = (updates: Partial<CampaignFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  const updateMessageTemplate = (updates: Partial<MessageTemplate>) => {
    setFormData((prev) => ({
      ...prev,
      message_template: { ...prev.message_template, ...updates },
    }));
  };

  const updateSegmentFilter = (updates: Partial<SegmentFilter>) => {
    setFormData((prev) => ({
      ...prev,
      segment_filter: { ...prev.segment_filter, ...updates },
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.name && formData.campaign_type;
      case 2:
        if (formData.campaign_type === 'voice') {
          return !!formData.message_template.voice_id;
        }
        if (formData.campaign_type === 'sms' || formData.campaign_type === 'whatsapp') {
          return !!formData.message_template.text_content;
        }
        if (formData.campaign_type === 'email') {
          return formData.message_template.subject && formData.message_template.html_content;
        }
        return false;
      case 3:
        return true; // Segment is optional
      case 4:
        return true;
      default:
        return false;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" aria-describedby="campaign-wizard-description">
        <DialogHeader>
          <DialogTitle>Create New Campaign</DialogTitle>
          <p id="campaign-wizard-description" className="sr-only">
            Multi-step wizard to create a new marketing campaign with message templates and audience targeting
          </p>
        </DialogHeader>

        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-6">
          {[1, 2, 3, 4].map((step) => (
            <div key={step} className="flex items-center flex-1">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${currentStep >= step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                `}
              >
                {currentStep > step ? <CheckCircle className="w-5 h-5" /> : step}
              </div>
              {step < 4 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 1 && <Step1Basics formData={formData} updateFormData={updateFormData} />}
          {currentStep === 2 && (
            <Step2Message
              campaignType={formData.campaign_type as CampaignType}
              messageTemplate={formData.message_template}
              updateMessageTemplate={updateMessageTemplate}
            />
          )}
          {currentStep === 3 && (
            <Step3Audience
              segmentFilter={formData.segment_filter}
              updateSegmentFilter={updateSegmentFilter}
              segmentPreview={segmentPreview}
              isPreviewLoading={isPreviewLoading}
            />
          )}
          {currentStep === 4 && (
            <Step4Review
              formData={formData}
              segmentPreview={segmentPreview}
            />
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>

            {currentStep < 4 ? (
              <Button onClick={handleNext} disabled={!canProceed()}>
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={!canProceed() || createMutation.isPending}
              >
                {createMutation.isPending && (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                )}
                Create Campaign
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ==================== Step 1: Campaign Basics ====================

interface Step1Props {
  formData: CampaignFormData;
  updateFormData: (updates: Partial<CampaignFormData>) => void;
}

function Step1Basics({ formData, updateFormData }: Step1Props) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="campaign-name">Campaign Name</Label>
        <Input
          id="campaign-name"
          placeholder="e.g., New Property Launch - Accra"
          value={formData.name}
          onChange={(e) => updateFormData({ name: e.target.value })}
        />
      </div>

      <div className="space-y-3">
        <Label>Campaign Type</Label>
        <div className="grid grid-cols-2 gap-3">
          {CAMPAIGN_TYPES.map((type) => {
            const Icon = type.icon;
            const isSelected = formData.campaign_type === type.value;

            return (
              <button
                key={type.value}
                onClick={() => updateFormData({ campaign_type: type.value })}
                className={`
                  p-4 rounded-lg border-2 text-left transition-all
                  ${isSelected
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`w-5 h-5 mt-0.5 ${isSelected ? 'text-blue-600' : 'text-gray-500'}`} />
                  <div className="flex-1">
                    <div className="font-medium">{type.label}</div>
                    <div className="text-sm text-gray-500 mt-1">{type.description}</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ==================== Step 2: Message Template ====================

interface Step2Props {
  campaignType: CampaignType;
  messageTemplate: MessageTemplate;
  updateMessageTemplate: (updates: Partial<MessageTemplate>) => void;
}

function Step2Message({ campaignType, messageTemplate, updateMessageTemplate }: Step2Props) {
  if (!campaignType) {
    return <div className="text-gray-500">Please select a campaign type first</div>;
  }

  return (
    <div className="space-y-6">
      {campaignType === 'voice' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="voice-id">Vapi Assistant ID</Label>
            <Input
              id="voice-id"
              placeholder="Enter your Vapi assistant ID"
              value={messageTemplate.voice_id || ''}
              onChange={(e) => updateMessageTemplate({ voice_id: e.target.value })}
            />
            <p className="text-sm text-gray-500">
              The AI assistant will make personalized calls to each contact
            </p>
          </div>
        </>
      )}

      {(campaignType === 'sms' || campaignType === 'whatsapp') && (
        <>
          <div className="space-y-2">
            <Label htmlFor="text-content">Message Content</Label>
            <Textarea
              id="text-content"
              placeholder="Your message here... Use {{name}} for personalization"
              value={messageTemplate.text_content || ''}
              onChange={(e) => updateMessageTemplate({ text_content: e.target.value })}
              rows={6}
            />
            <p className="text-sm text-gray-500">
              Available variables: {'{'}{'{'} name {'}'}{'}'}, {'{'}{'{'} property_type {'}'}{'}'}, {'{'}{'{'} budget {'}'}
              {'}'}
            </p>
          </div>
          <div className="text-sm text-gray-700">
            Character count: {messageTemplate.text_content?.length || 0} / 160
          </div>
        </>
      )}

      {campaignType === 'email' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="email-subject">Subject Line</Label>
            <Input
              id="email-subject"
              placeholder="e.g., New Properties Available in Accra"
              value={messageTemplate.subject || ''}
              onChange={(e) => updateMessageTemplate({ subject: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email-html">Email Content (HTML)</Label>
            <Textarea
              id="email-html"
              placeholder="<h1>Hello {{name}}</h1><p>Check out our new properties...</p>"
              value={messageTemplate.html_content || ''}
              onChange={(e) => updateMessageTemplate({ html_content: e.target.value })}
              rows={12}
            />
            <p className="text-sm text-gray-500">
              Use HTML for rich formatting. Available variables: {'{'}{'{'} name {'}'}{'}'}, {'{'}{'{'} email {'}'}
              {'}'}
            </p>
          </div>
        </>
      )}
    </div>
  );
}

// ==================== Step 3: Audience Targeting ====================

interface Step3Props {
  segmentFilter: SegmentFilter;
  updateSegmentFilter: (updates: Partial<SegmentFilter>) => void;
  segmentPreview?: { contact_count: number; estimated_cost: number };
  isPreviewLoading: boolean;
}

function Step3Audience({
  segmentFilter,
  updateSegmentFilter,
  segmentPreview,
  isPreviewLoading,
}: Step3Props) {
  const toggleArrayItem = (field: keyof SegmentFilter, value: string) => {
    const currentArray = (segmentFilter[field] as string[]) || [];
    const newArray = currentArray.includes(value)
      ? currentArray.filter((item) => item !== value)
      : [...currentArray, value];
    updateSegmentFilter({ [field]: newArray.length > 0 ? newArray : undefined });
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Segment Preview</div>
            {isPreviewLoading ? (
              <div className="text-sm text-gray-600 mt-1">Calculating...</div>
            ) : segmentPreview ? (
              <div className="text-sm text-gray-600 mt-1">
                {segmentPreview.contact_count} contacts • Est. cost: GHS{' '}
                {segmentPreview.estimated_cost.toFixed(2)}
              </div>
            ) : (
              <div className="text-sm text-gray-600 mt-1">Add filters to see preview</div>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Property Types</Label>
        <div className="flex flex-wrap gap-2">
          {PROPERTY_TYPES.map((type) => {
            const isSelected = segmentFilter.property_types?.includes(type);
            return (
              <Badge
                key={type}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleArrayItem('property_types', type)}
              >
                {type}
              </Badge>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Interest Status</Label>
        <div className="flex flex-wrap gap-2">
          {INTEREST_STATUSES.map((status) => {
            const isSelected = segmentFilter.interest_statuses?.includes(status as any);
            return (
              <Badge
                key={status}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleArrayItem('interest_statuses', status)}
              >
                {status}
              </Badge>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Lead Status</Label>
        <div className="flex flex-wrap gap-2">
          {LEAD_STATUSES.map((status) => {
            const isSelected = segmentFilter.lead_statuses?.includes(status as any);
            return (
              <Badge
                key={status}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleArrayItem('lead_statuses', status)}
              >
                {status}
              </Badge>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="budget-min">Min Budget (GHS)</Label>
          <Input
            id="budget-min"
            type="number"
            placeholder="50000"
            value={segmentFilter.budget_min || ''}
            onChange={(e) =>
              updateSegmentFilter({
                budget_min: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="budget-max">Max Budget (GHS)</Label>
          <Input
            id="budget-max"
            type="number"
            placeholder="500000"
            value={segmentFilter.budget_max || ''}
            onChange={(e) =>
              updateSegmentFilter({
                budget_max: e.target.value ? parseFloat(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>
    </div>
  );
}

// ==================== Step 4: Review ====================

interface Step4Props {
  formData: CampaignFormData;
  segmentPreview?: { contact_count: number; estimated_cost: number };
}

function Step4Review({ formData, segmentPreview }: Step4Props) {
  const campaignTypeInfo = CAMPAIGN_TYPES.find((t) => t.value === formData.campaign_type);

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg p-4 space-y-4">
        <div>
          <div className="text-sm text-gray-500">Campaign Name</div>
          <div className="font-medium mt-1">{formData.name}</div>
        </div>

        <div>
          <div className="text-sm text-gray-500">Campaign Type</div>
          <div className="flex items-center gap-2 mt-1">
            {campaignTypeInfo && (
              <>
                <campaignTypeInfo.icon className="w-4 h-4" />
                <span className="font-medium">{campaignTypeInfo.label}</span>
              </>
            )}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-500">Message Preview</div>
          <div className="mt-1">
            {formData.campaign_type === 'voice' && (
              <div className="text-sm">Assistant ID: {formData.message_template.voice_id}</div>
            )}
            {(formData.campaign_type === 'sms' || formData.campaign_type === 'whatsapp') && (
              <div className="text-sm bg-white p-3 rounded border">
                {formData.message_template.text_content}
              </div>
            )}
            {formData.campaign_type === 'email' && (
              <div>
                <div className="text-sm font-medium">Subject: {formData.message_template.subject}</div>
                <div className="text-sm bg-white p-3 rounded border mt-2 max-h-32 overflow-auto">
                  <div dangerouslySetInnerHTML={{ __html: formData.message_template.html_content || '' }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {segmentPreview && (
          <div>
            <div className="text-sm text-gray-500">Target Audience</div>
            <div className="mt-1 space-y-1">
              <div className="text-sm">
                <span className="font-medium">{segmentPreview.contact_count}</span> contacts
              </div>
              <div className="text-sm">
                Estimated cost: <span className="font-medium">GHS {segmentPreview.estimated_cost.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="font-medium text-yellow-900">Ready to launch?</div>
        <div className="text-sm text-yellow-700 mt-1">
          Once created, the campaign will be in draft status. You can review and launch it from the campaigns page.
        </div>
      </div>
    </div>
  );
}
