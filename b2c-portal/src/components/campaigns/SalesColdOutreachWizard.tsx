import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, ArrowRight, PhoneCall, Users, Calendar, Zap, Target, Database } from 'lucide-react';

interface SalesColdOutreachConfig {
  name: string;
  description: string;
  phoneNumber: string;
  targetAudience: {
    demographics: string;
    geography: string;
    industry: string;
    companySize: string;
  };
  leadSources: {
    enabled: boolean;
    apifyConfig?: {
      searchKeywords: string[];
      geographic_location: string;
      industry_filter: string;
    };
    manualUpload?: {
      enabled: boolean;
      csvTemplate: string;
    };
  };
  outreachConfig: {
    callScript: string;
    followUpSequence: string[];
    maxAttempts: number;
    callWindow: {
      start: string;
      end: string;
      timezone: string;
    };
  };
  crmIntegration: {
    enabled: boolean;
    provider: 'pipedrive' | 'freshsales' | 'hubspot' | 'salesforce';
    apiConfig?: {
      apiKey: string;
      baseUrl: string;
    };
  };
  qualificationCriteria: {
    budget: {
      minimum: number;
      currency: string;
    };
    timeframe: string;
    authority: string;
    need: string;
  };
  n8nConfig?: {
    enabled: boolean;
    templateId: number;
    workflowSettings: {
      batchSize: number;
      delayBetweenCalls: number;
      retryLogic: boolean;
    };
  };
  vapiConfig?: {
    enabled: boolean;
    assistantType: string;
    voiceSettings: {
      voice: string;
      speed: number;
      stability: number;
    };
  };
}

interface SalesColdOutreachWizardProps {
  onSave: (config: SalesColdOutreachConfig) => void;
  onCancel: () => void;
  initialConfig?: Partial<SalesColdOutreachConfig>;
}

export const SalesColdOutreachWizard: React.FC<SalesColdOutreachWizardProps> = ({
  onSave,
  onCancel,
  initialConfig
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<SalesColdOutreachConfig>({
    name: initialConfig?.name || '',
    description: initialConfig?.description || '',
    phoneNumber: initialConfig?.phoneNumber || '',
    targetAudience: {
      demographics: '',
      geography: '',
      industry: '',
      companySize: '',
      ...initialConfig?.targetAudience
    },
    leadSources: {
      enabled: true,
      apifyConfig: {
        searchKeywords: [],
        geographic_location: '',
        industry_filter: '',
      },
      manualUpload: {
        enabled: true,
        csvTemplate: 'name,email,phone,company,role',
      },
      ...initialConfig?.leadSources
    },
    outreachConfig: {
      callScript: `Hello [Name], I'm calling from [Company]. I noticed you might be interested in [Product/Service]. Would you have a few minutes to discuss how we can help you achieve [specific benefit]?`,
      followUpSequence: [
        'Left voicemail - follow up in 2 days',
        'Second attempt - try different time',
        'Final attempt - email follow-up'
      ],
      maxAttempts: 3,
      callWindow: {
        start: '09:00',
        end: '17:00',
        timezone: 'America/New_York',
      },
      ...initialConfig?.outreachConfig
    },
    crmIntegration: {
      enabled: false,
      provider: 'pipedrive',
      ...initialConfig?.crmIntegration
    },
    qualificationCriteria: {
      budget: {
        minimum: 1000,
        currency: 'USD',
      },
      timeframe: '3 months',
      authority: 'Decision maker',
      need: 'Specific business need',
      ...initialConfig?.qualificationCriteria
    },
    n8nConfig: {
      enabled: true,
      templateId: 5449,
      workflowSettings: {
        batchSize: 10,
        delayBetweenCalls: 30,
        retryLogic: true,
      },
      ...initialConfig?.n8nConfig
    },
    vapiConfig: {
      enabled: true,
      assistantType: 'sales_outreach_agent',
      voiceSettings: {
        voice: 'nova',
        speed: 1.0,
        stability: 0.75,
      },
      ...initialConfig?.vapiConfig
    }
  });

  const totalSteps = 6;
  const progress = (currentStep / totalSteps) * 100;

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSave = () => {
    onSave(config);
  };

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const keys = path.split('.');
      const newConfig = { ...prev };
      let current: any = newConfig;

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="name">Campaign Name</Label>
              <Input
                id="name"
                value={config.name}
                onChange={(e) => updateConfig('name', e.target.value)}
                placeholder="e.g., Q1 Sales Outreach Campaign"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={config.description}
                onChange={(e) => updateConfig('description', e.target.value)}
                placeholder="Describe the goals and target outcomes for this cold outreach campaign..."
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                value={config.phoneNumber}
                onChange={(e) => updateConfig('phoneNumber', e.target.value)}
                placeholder="+1 (555) 000-0000"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="demographics">Target Demographics</Label>
              <Input
                id="demographics"
                value={config.targetAudience.demographics}
                onChange={(e) => updateConfig('targetAudience.demographics', e.target.value)}
                placeholder="e.g., CEOs, CTOs, VPs of Sales"
              />
            </div>
            <div>
              <Label htmlFor="geography">Geographic Location</Label>
              <Input
                id="geography"
                value={config.targetAudience.geography}
                onChange={(e) => updateConfig('targetAudience.geography', e.target.value)}
                placeholder="e.g., North America, Europe, specific cities"
              />
            </div>
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                value={config.targetAudience.industry}
                onChange={(e) => updateConfig('targetAudience.industry', e.target.value)}
                placeholder="e.g., SaaS, Healthcare, Manufacturing"
              />
            </div>
            <div>
              <Label htmlFor="companySize">Company Size</Label>
              <Select
                value={config.targetAudience.companySize}
                onValueChange={(value) => updateConfig('targetAudience.companySize', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select company size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="startup">Startup (1-10 employees)</SelectItem>
                  <SelectItem value="small">Small (11-50 employees)</SelectItem>
                  <SelectItem value="medium">Medium (51-200 employees)</SelectItem>
                  <SelectItem value="large">Large (201-1000 employees)</SelectItem>
                  <SelectItem value="enterprise">Enterprise (1000+ employees)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <Label>Automated Lead Sourcing</Label>
              <Switch
                checked={config.leadSources.enabled}
                onCheckedChange={(checked) => updateConfig('leadSources.enabled', checked)}
              />
            </div>

            {config.leadSources.enabled && (
              <div className="space-y-4 p-4 border rounded-lg">
                <h4 className="font-medium">Apify Lead Scraping Configuration</h4>
                <div>
                  <Label htmlFor="keywords">Search Keywords (comma-separated)</Label>
                  <Input
                    id="keywords"
                    value={config.leadSources.apifyConfig?.searchKeywords.join(', ') || ''}
                    onChange={(e) => updateConfig('leadSources.apifyConfig.searchKeywords', e.target.value.split(', ').filter(k => k.trim()))}
                    placeholder="software company, tech startup, digital agency"
                  />
                </div>
                <div>
                  <Label htmlFor="location">Geographic Filter</Label>
                  <Input
                    id="location"
                    value={config.leadSources.apifyConfig?.geographic_location || ''}
                    onChange={(e) => updateConfig('leadSources.apifyConfig.geographic_location', e.target.value)}
                    placeholder="United States, California, New York"
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <Label>Manual CSV Upload</Label>
              <Switch
                checked={config.leadSources.manualUpload?.enabled || false}
                onCheckedChange={(checked) => updateConfig('leadSources.manualUpload.enabled', checked)}
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="script">Call Script</Label>
              <Textarea
                id="script"
                value={config.outreachConfig.callScript}
                onChange={(e) => updateConfig('outreachConfig.callScript', e.target.value)}
                rows={4}
                placeholder="Your personalized cold call script..."
              />
            </div>
            <div>
              <Label htmlFor="maxAttempts">Maximum Call Attempts</Label>
              <Select
                value={config.outreachConfig.maxAttempts.toString()}
                onValueChange={(value) => updateConfig('outreachConfig.maxAttempts', parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 attempt</SelectItem>
                  <SelectItem value="2">2 attempts</SelectItem>
                  <SelectItem value="3">3 attempts</SelectItem>
                  <SelectItem value="4">4 attempts</SelectItem>
                  <SelectItem value="5">5 attempts</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="startTime">Call Window Start</Label>
                <Input
                  id="startTime"
                  type="time"
                  value={config.outreachConfig.callWindow.start}
                  onChange={(e) => updateConfig('outreachConfig.callWindow.start', e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="endTime">Call Window End</Label>
                <Input
                  id="endTime"
                  type="time"
                  value={config.outreachConfig.callWindow.end}
                  onChange={(e) => updateConfig('outreachConfig.callWindow.end', e.target.value)}
                />
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <Label>CRM Integration</Label>
              <Switch
                checked={config.crmIntegration.enabled}
                onCheckedChange={(checked) => updateConfig('crmIntegration.enabled', checked)}
              />
            </div>

            {config.crmIntegration.enabled && (
              <div className="space-y-4 p-4 border rounded-lg">
                <div>
                  <Label>CRM Provider</Label>
                  <Select
                    value={config.crmIntegration.provider}
                    onValueChange={(value) => updateConfig('crmIntegration.provider', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pipedrive">Pipedrive</SelectItem>
                      <SelectItem value="freshsales">Freshsales</SelectItem>
                      <SelectItem value="hubspot">HubSpot</SelectItem>
                      <SelectItem value="salesforce">Salesforce</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h4 className="font-medium">Lead Qualification Criteria</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="budget">Minimum Budget</Label>
                  <Input
                    id="budget"
                    type="number"
                    value={config.qualificationCriteria.budget.minimum}
                    onChange={(e) => updateConfig('qualificationCriteria.budget.minimum', parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label htmlFor="currency">Currency</Label>
                  <Select
                    value={config.qualificationCriteria.budget.currency}
                    onValueChange={(value) => updateConfig('qualificationCriteria.budget.currency', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label htmlFor="timeframe">Decision Timeframe</Label>
                <Input
                  id="timeframe"
                  value={config.qualificationCriteria.timeframe}
                  onChange={(e) => updateConfig('qualificationCriteria.timeframe', e.target.value)}
                  placeholder="e.g., 3 months, Q1 2024"
                />
              </div>
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <Label>N8N Workflow Automation</Label>
              <Switch
                checked={config.n8nConfig?.enabled || false}
                onCheckedChange={(checked) => updateConfig('n8nConfig.enabled', checked)}
              />
            </div>

            {config.n8nConfig?.enabled && (
              <div className="space-y-4 p-4 border rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="batchSize">Batch Size</Label>
                    <Input
                      id="batchSize"
                      type="number"
                      value={config.n8nConfig.workflowSettings.batchSize}
                      onChange={(e) => updateConfig('n8nConfig.workflowSettings.batchSize', parseInt(e.target.value) || 10)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="delay">Delay Between Calls (seconds)</Label>
                    <Input
                      id="delay"
                      type="number"
                      value={config.n8nConfig.workflowSettings.delayBetweenCalls}
                      onChange={(e) => updateConfig('n8nConfig.workflowSettings.delayBetweenCalls', parseInt(e.target.value) || 30)}
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <Label>VAPI Voice Assistant</Label>
              <Switch
                checked={config.vapiConfig?.enabled || false}
                onCheckedChange={(checked) => updateConfig('vapiConfig.enabled', checked)}
              />
            </div>

            {config.vapiConfig?.enabled && (
              <div className="space-y-4 p-4 border rounded-lg">
                <div>
                  <Label>Voice Model</Label>
                  <Select
                    value={config.vapiConfig.voiceSettings.voice}
                    onValueChange={(value) => updateConfig('vapiConfig.voiceSettings.voice', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nova">Nova (Conversational)</SelectItem>
                      <SelectItem value="alloy">Alloy (Professional)</SelectItem>
                      <SelectItem value="echo">Echo (Warm)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const getStepTitle = () => {
    const titles = [
      'Basic Information',
      'Target Audience',
      'Lead Sources',
      'Outreach Configuration',
      'CRM & Qualification',
      'AI & Automation'
    ];
    return titles[currentStep - 1];
  };

  const getStepIcon = () => {
    const icons = [FileText, Users, Database, PhoneCall, Target, Zap];
    const Icon = icons[currentStep - 1];
    return <Icon className="h-5 w-5" />;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          {getStepIcon()}
          <h1 className="text-2xl font-bold">Sales Cold Outreach Setup</h1>
          <Badge variant="outline">Step {currentStep} of {totalSteps}</Badge>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{getStepTitle()}</CardTitle>
          <CardDescription>
            Configure your sales cold outreach campaign settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderStepContent()}
        </CardContent>
      </Card>

      <div className="flex justify-between mt-6">
        <Button
          variant="outline"
          onClick={currentStep === 1 ? onCancel : handlePrevious}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          {currentStep === 1 ? 'Cancel' : 'Previous'}
        </Button>

        {currentStep === totalSteps ? (
          <Button onClick={handleSave} className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Create Campaign
          </Button>
        ) : (
          <Button onClick={handleNext} className="flex items-center gap-2">
            Next
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
};