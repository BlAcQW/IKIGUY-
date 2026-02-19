import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Shield,
  FileText,
  AlertTriangle,
  DollarSign,
  Phone,
  Mail,
  Database,
  Settings,
  CheckCircle,
  Clock,
  Users
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { CampaignTemplate } from './CampaignTemplateSelector';

interface InsuranceAPIConfig {
  provider: 'custom' | 'guidewire' | 'duck_creek' | 'sapiens' | 'insurity';
  apiUrl: string;
  apiKey: string;
  version: string;
  timeout: number;
}

interface PolicyConfig {
  autoLookup: boolean;
  verificationRequired: boolean;
  supportedPolicyTypes: string[];
  policyDataFields: string[];
}

interface ClaimsWorkflowConfig {
  autoIntake: boolean;
  requireDocuments: boolean;
  fraudDetectionEnabled: boolean;
  settlementThresholds: {
    autoApprove: number;
    requireReview: number;
    requireInvestigation: number;
  };
  documentTypes: string[];
  notificationSettings: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    callEnabled: boolean;
    intervals: string[];
  };
}

interface ComplianceConfig {
  frameworks: string[];
  retentionPeriod: number;
  auditTrailEnabled: boolean;
  privacySettings: {
    dataEncryption: boolean;
    accessLogging: boolean;
    consentRequired: boolean;
  };
}

interface VAPIInsuranceConfig {
  assistantId: string;
  phoneNumberId: string;
  voiceId: string;
  model: string;
  maxDuration: number;
  silenceTimeoutMs: number;
  customPrompt: string;
  claimsFunctions: string[];
}

interface InsuranceClaimsConfig {
  name: string;
  description: string;
  phoneNumber: string;
  insuranceAPI: InsuranceAPIConfig;
  policyConfig: PolicyConfig;
  claimsWorkflow: ClaimsWorkflowConfig;
  complianceConfig: ComplianceConfig;
  vapiConfig: VAPIInsuranceConfig;
  integrations: {
    crmEnabled: boolean;
    crmProvider: string;
    emailProvider: string;
    smsProvider: string;
    documentStorage: string;
  };
}

interface InsuranceClaimsWizardProps {
  isOpen: boolean;
  onClose: () => void;
  template: CampaignTemplate;
  onCreateCampaign: (config: InsuranceClaimsConfig) => void;
  apiBaseUrl: string;
}

const INSURANCE_PROVIDERS = [
  { id: 'custom', name: 'Custom API' },
  { id: 'guidewire', name: 'Guidewire ClaimCenter' },
  { id: 'duck_creek', name: 'Duck Creek Claims' },
  { id: 'sapiens', name: 'Sapiens ALIS' },
  { id: 'insurity', name: 'Insurity' }
];

const POLICY_TYPES = [
  'Auto Insurance',
  'Home Insurance',
  'Life Insurance',
  'Health Insurance',
  'Commercial Property',
  'Workers Compensation',
  'Professional Liability',
  'Umbrella Policy'
];

const DOCUMENT_TYPES = [
  'Police Report',
  'Medical Records',
  'Repair Estimates',
  'Photos/Videos',
  'Witness Statements',
  'Property Damage Assessment',
  'Medical Bills',
  'Employment Records',
  'Financial Documents',
  'Proof of Loss'
];

const COMPLIANCE_FRAMEWORKS = [
  'NAIC (National Association of Insurance Commissioners)',
  'State Insurance Regulations',
  'GLBA (Gramm-Leach-Bliley Act)',
  'HIPAA (Health Insurance Portability)',
  'Fair Claims Settlement Practices',
  'Unfair Claims Settlement Practices Act',
  'SOX (Sarbanes-Oxley)',
  'GDPR (General Data Protection Regulation)'
];

const VOICE_OPTIONS = [
  { id: 'jennifer', name: 'Jennifer (Professional & Empathetic)' },
  { id: 'michael', name: 'Michael (Authoritative & Clear)' },
  { id: 'sarah', name: 'Sarah (Warm & Reassuring)' },
  { id: 'david', name: 'David (Calm & Knowledgeable)' }
];

const MODEL_OPTIONS = [
  { id: 'gpt-4', name: 'GPT-4 (Most Capable)' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo (Faster)' },
  { id: 'claude-3-haiku', name: 'Claude 3 Haiku (Efficient)' }
];

export const InsuranceClaimsWizard: React.FC<InsuranceClaimsWizardProps> = ({
  isOpen,
  onClose,
  template,
  onCreateCampaign,
  apiBaseUrl
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const { toast } = useToast();

  const [config, setConfig] = useState<InsuranceClaimsConfig>({
    name: '',
    description: '',
    phoneNumber: '',
    insuranceAPI: {
      provider: 'custom',
      apiUrl: '',
      apiKey: '',
      version: '1.0',
      timeout: 30000
    },
    policyConfig: {
      autoLookup: true,
      verificationRequired: true,
      supportedPolicyTypes: ['Auto Insurance', 'Home Insurance'],
      policyDataFields: ['policy_number', 'coverage_amount', 'deductible', 'effective_date']
    },
    claimsWorkflow: {
      autoIntake: true,
      requireDocuments: true,
      fraudDetectionEnabled: true,
      settlementThresholds: {
        autoApprove: 1000,
        requireReview: 10000,
        requireInvestigation: 50000
      },
      documentTypes: ['Police Report', 'Photos/Videos', 'Repair Estimates'],
      notificationSettings: {
        emailEnabled: true,
        smsEnabled: true,
        callEnabled: false,
        intervals: ['immediate', '24_hours', '72_hours', 'weekly']
      }
    },
    complianceConfig: {
      frameworks: ['NAIC (National Association of Insurance Commissioners)', 'State Insurance Regulations'],
      retentionPeriod: 7,
      auditTrailEnabled: true,
      privacySettings: {
        dataEncryption: true,
        accessLogging: true,
        consentRequired: true
      }
    },
    vapiConfig: {
      assistantId: '',
      phoneNumberId: '',
      voiceId: 'jennifer',
      model: 'gpt-4',
      maxDuration: 900,
      silenceTimeoutMs: 30000,
      customPrompt: `You are a professional insurance claims assistant. Your role is to help customers with their insurance claims process with empathy and efficiency.

## Core Responsibilities:
1. **Claims Intake**: Collect initial claim information including incident details, policy information, and contact details
2. **Document Collection**: Guide customers through required documentation and help them submit necessary files
3. **Status Updates**: Provide real-time updates on claim status and next steps
4. **Policy Verification**: Verify policy details and coverage information
5. **Settlement Processing**: Explain settlement offers and payment processes

## Communication Guidelines:
- Always be empathetic and understanding - customers are often dealing with stressful situations
- Speak clearly and avoid insurance jargon
- Be patient and allow time for customers to provide information
- Confirm important details before proceeding
- Maintain confidentiality and follow privacy guidelines

## Key Functions Available:
- Check policy status and coverage details
- Create new claims and update existing ones
- Collect and verify required documents
- Calculate settlement estimates
- Schedule adjuster appointments
- Escalate complex cases to human adjusters

How may I assist you with your insurance claim today?`,
      claimsFunctions: [
        'check_policy_status',
        'create_claim',
        'update_claim',
        'collect_documents',
        'calculate_settlement',
        'schedule_adjuster',
        'escalate_claim'
      ]
    },
    integrations: {
      crmEnabled: true,
      crmProvider: 'salesforce',
      emailProvider: 'sendgrid',
      smsProvider: 'twilio',
      documentStorage: 'aws_s3'
    }
  });

  const steps = [
    { id: 'basic', title: 'Basic Setup', icon: Settings },
    { id: 'insurance_api', title: 'Insurance API', icon: Database },
    { id: 'policy_config', title: 'Policy Config', icon: FileText },
    { id: 'claims_workflow', title: 'Claims Workflow', icon: Shield },
    { id: 'compliance', title: 'Compliance', icon: AlertTriangle },
    { id: 'voice_agent', title: 'Voice Agent', icon: Phone },
    { id: 'integrations', title: 'Integrations', icon: Users },
    { id: 'review', title: 'Review', icon: CheckCircle }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsCreating(true);
    try {
      await onCreateCampaign(config);
      toast({
        title: "Insurance Claims Campaign Created",
        description: "Your insurance claims processing campaign has been configured and is ready to use."
      });
      onClose();
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: "Failed to create insurance claims campaign. Please check your configuration.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const keys = path.split('.');
      const updated = { ...prev };
      let current = updated;

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const currentStepData = steps[currentStep];
  const StepIcon = currentStepData.icon;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <DialogTitle>Setup Insurance Claims Campaign</DialogTitle>
              <DialogDescription>
                Step {currentStep + 1} of {steps.length}: {currentStepData.title}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Progress */}
        <div className="flex justify-between mb-6 overflow-x-auto">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;

            return (
              <div
                key={step.id}
                className={`flex flex-col items-center gap-2 min-w-0 ${isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-gray-600'}`}
              >
                <div className={`p-2 rounded-full ${isActive ? 'bg-primary/10' : isCompleted ? 'bg-green-100' : 'bg-muted'}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-xs text-center whitespace-nowrap">{step.title}</span>
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Step 1: Basic Setup */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label htmlFor="campaign-name">Campaign Name</Label>
                  <Input
                    id="campaign-name"
                    value={config.name}
                    onChange={(e) => updateConfig('name', e.target.value)}
                    placeholder="e.g., Auto Claims Processing Center"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="campaign-description">Description</Label>
                  <Textarea
                    id="campaign-description"
                    value={config.description}
                    onChange={(e) => updateConfig('description', e.target.value)}
                    placeholder="Describe the purpose and scope of this claims processing campaign"
                    rows={3}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="phone-number">Claims Hotline Number</Label>
                  <Input
                    id="phone-number"
                    value={config.phoneNumber}
                    onChange={(e) => updateConfig('phoneNumber', e.target.value)}
                    placeholder="+1234567890"
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    The phone number customers will call to report claims
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Insurance API Configuration */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Insurance System Integration</CardTitle>
                  <CardDescription>Configure your insurance management system API connection</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="insurance-provider">Insurance System Provider</Label>
                    <Select
                      value={config.insuranceAPI.provider}
                      onValueChange={(value) => updateConfig('insuranceAPI.provider', value)}
                    >
                      <SelectTrigger id="insurance-provider" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {INSURANCE_PROVIDERS.map((provider) => (
                          <SelectItem key={provider.id} value={provider.id}>
                            {provider.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="api-url">API URL</Label>
                      <Input
                        id="api-url"
                        value={config.insuranceAPI.apiUrl}
                        onChange={(e) => updateConfig('insuranceAPI.apiUrl', e.target.value)}
                        placeholder="https://api.your-insurance-system.com"
                        className="mt-2"
                      />
                    </div>

                    <div>
                      <Label htmlFor="api-version">API Version</Label>
                      <Input
                        id="api-version"
                        value={config.insuranceAPI.version}
                        onChange={(e) => updateConfig('insuranceAPI.version', e.target.value)}
                        placeholder="1.0"
                        className="mt-2"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="api-key">API Key</Label>
                    <Input
                      id="api-key"
                      type="password"
                      value={config.insuranceAPI.apiKey}
                      onChange={(e) => updateConfig('insuranceAPI.apiKey', e.target.value)}
                      placeholder="Enter your insurance system API key"
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label htmlFor="api-timeout">Request Timeout (ms)</Label>
                    <Input
                      id="api-timeout"
                      type="number"
                      value={config.insuranceAPI.timeout}
                      onChange={(e) => updateConfig('insuranceAPI.timeout', parseInt(e.target.value))}
                      placeholder="30000"
                      className="mt-2"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 3: Policy Configuration */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Policy Configuration</CardTitle>
                  <CardDescription>Configure policy lookup and verification settings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-medium">Automatic Policy Lookup</Label>
                      <p className="text-sm text-gray-600">
                        Automatically retrieve policy information during claims intake
                      </p>
                    </div>
                    <Switch
                      checked={config.policyConfig.autoLookup}
                      onCheckedChange={(checked) => updateConfig('policyConfig.autoLookup', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-medium">Policy Verification Required</Label>
                      <p className="text-sm text-gray-600">
                        Require policy verification before processing claims
                      </p>
                    </div>
                    <Switch
                      checked={config.policyConfig.verificationRequired}
                      onCheckedChange={(checked) => updateConfig('policyConfig.verificationRequired', checked)}
                    />
                  </div>

                  <div>
                    <Label>Supported Policy Types</Label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {POLICY_TYPES.map((policyType) => (
                        <div key={policyType} className="flex items-center space-x-2">
                          <Checkbox
                            id={`policy-${policyType}`}
                            checked={config.policyConfig.supportedPolicyTypes.includes(policyType)}
                            onCheckedChange={(checked) => {
                              const currentTypes = config.policyConfig.supportedPolicyTypes;
                              const newTypes = checked
                                ? [...currentTypes, policyType]
                                : currentTypes.filter(t => t !== policyType);
                              updateConfig('policyConfig.supportedPolicyTypes', newTypes);
                            }}
                          />
                          <Label htmlFor={`policy-${policyType}`} className="text-sm">
                            {policyType}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 4: Claims Workflow */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Claims Processing Workflow</CardTitle>
                  <CardDescription>Configure automated claims processing rules and thresholds</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="text-base font-medium">Automatic Claims Intake</Label>
                        <p className="text-sm text-gray-600">
                          Automatically create claims from phone calls
                        </p>
                      </div>
                      <Switch
                        checked={config.claimsWorkflow.autoIntake}
                        onCheckedChange={(checked) => updateConfig('claimsWorkflow.autoIntake', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="text-base font-medium">Fraud Detection</Label>
                        <p className="text-sm text-gray-600">
                          Enable AI-powered fraud detection
                        </p>
                      </div>
                      <Switch
                        checked={config.claimsWorkflow.fraudDetectionEnabled}
                        onCheckedChange={(checked) => updateConfig('claimsWorkflow.fraudDetectionEnabled', checked)}
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-base font-medium mb-4 block">Settlement Thresholds ($)</Label>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="auto-approve">Auto Approve (≤)</Label>
                        <Input
                          id="auto-approve"
                          type="number"
                          value={config.claimsWorkflow.settlementThresholds.autoApprove}
                          onChange={(e) => updateConfig('claimsWorkflow.settlementThresholds.autoApprove', parseInt(e.target.value))}
                          className="mt-2"
                        />
                      </div>
                      <div>
                        <Label htmlFor="require-review">Require Review (≤)</Label>
                        <Input
                          id="require-review"
                          type="number"
                          value={config.claimsWorkflow.settlementThresholds.requireReview}
                          onChange={(e) => updateConfig('claimsWorkflow.settlementThresholds.requireReview', parseInt(e.target.value))}
                          className="mt-2"
                        />
                      </div>
                      <div>
                        <Label htmlFor="require-investigation">Investigation (&gt;)</Label>
                        <Input
                          id="require-investigation"
                          type="number"
                          value={config.claimsWorkflow.settlementThresholds.requireInvestigation}
                          onChange={(e) => updateConfig('claimsWorkflow.settlementThresholds.requireInvestigation', parseInt(e.target.value))}
                          className="mt-2"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <Label>Required Document Types</Label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {DOCUMENT_TYPES.map((docType) => (
                        <div key={docType} className="flex items-center space-x-2">
                          <Checkbox
                            id={`doc-${docType}`}
                            checked={config.claimsWorkflow.documentTypes.includes(docType)}
                            onCheckedChange={(checked) => {
                              const currentTypes = config.claimsWorkflow.documentTypes;
                              const newTypes = checked
                                ? [...currentTypes, docType]
                                : currentTypes.filter(t => t !== docType);
                              updateConfig('claimsWorkflow.documentTypes', newTypes);
                            }}
                          />
                          <Label htmlFor={`doc-${docType}`} className="text-sm">
                            {docType}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 5: Compliance Configuration */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Compliance & Regulatory Settings</CardTitle>
                  <CardDescription>Configure compliance frameworks and data privacy settings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label>Compliance Frameworks</Label>
                    <div className="grid grid-cols-1 gap-2 mt-2">
                      {COMPLIANCE_FRAMEWORKS.map((framework) => (
                        <div key={framework} className="flex items-center space-x-2">
                          <Checkbox
                            id={`compliance-${framework}`}
                            checked={config.complianceConfig.frameworks.includes(framework)}
                            onCheckedChange={(checked) => {
                              const currentFrameworks = config.complianceConfig.frameworks;
                              const newFrameworks = checked
                                ? [...currentFrameworks, framework]
                                : currentFrameworks.filter(f => f !== framework);
                              updateConfig('complianceConfig.frameworks', newFrameworks);
                            }}
                          />
                          <Label htmlFor={`compliance-${framework}`} className="text-sm">
                            {framework}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="retention-period">Data Retention Period (years)</Label>
                    <Input
                      id="retention-period"
                      type="number"
                      value={config.complianceConfig.retentionPeriod}
                      onChange={(e) => updateConfig('complianceConfig.retentionPeriod', parseInt(e.target.value))}
                      className="mt-2"
                    />
                  </div>

                  <div className="space-y-4">
                    <Label className="text-base font-medium">Privacy & Security Settings</Label>

                    <div className="grid grid-cols-1 gap-4">
                      <div className="flex items-center justify-between">
                        <Label>Data Encryption</Label>
                        <Switch
                          checked={config.complianceConfig.privacySettings.dataEncryption}
                          onCheckedChange={(checked) => updateConfig('complianceConfig.privacySettings.dataEncryption', checked)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label>Access Logging</Label>
                        <Switch
                          checked={config.complianceConfig.privacySettings.accessLogging}
                          onCheckedChange={(checked) => updateConfig('complianceConfig.privacySettings.accessLogging', checked)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label>Customer Consent Required</Label>
                        <Switch
                          checked={config.complianceConfig.privacySettings.consentRequired}
                          onCheckedChange={(checked) => updateConfig('complianceConfig.privacySettings.consentRequired', checked)}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <Label>Audit Trail Enabled</Label>
                        <Switch
                          checked={config.complianceConfig.auditTrailEnabled}
                          onCheckedChange={(checked) => updateConfig('complianceConfig.auditTrailEnabled', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 6: Voice Agent Configuration */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>VAPI Voice Agent Configuration</CardTitle>
                  <CardDescription>Configure your AI voice agent for claims processing</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="assistant-id">Assistant ID</Label>
                      <Input
                        id="assistant-id"
                        value={config.vapiConfig.assistantId}
                        onChange={(e) => updateConfig('vapiConfig.assistantId', e.target.value)}
                        placeholder="VAPI Assistant ID"
                        className="mt-2"
                      />
                    </div>

                    <div>
                      <Label htmlFor="phone-id">Phone Number ID</Label>
                      <Input
                        id="phone-id"
                        value={config.vapiConfig.phoneNumberId}
                        onChange={(e) => updateConfig('vapiConfig.phoneNumberId', e.target.value)}
                        placeholder="VAPI Phone Number ID"
                        className="mt-2"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="voice-id">Voice</Label>
                      <Select
                        value={config.vapiConfig.voiceId}
                        onValueChange={(value) => updateConfig('vapiConfig.voiceId', value)}
                      >
                        <SelectTrigger id="voice-id" className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {VOICE_OPTIONS.map((voice) => (
                            <SelectItem key={voice.id} value={voice.id}>
                              {voice.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="model">AI Model</Label>
                      <Select
                        value={config.vapiConfig.model}
                        onValueChange={(value) => updateConfig('vapiConfig.model', value)}
                      >
                        <SelectTrigger id="model" className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {MODEL_OPTIONS.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              {model.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="max-duration">Max Call Duration (seconds)</Label>
                    <Input
                      id="max-duration"
                      type="number"
                      value={config.vapiConfig.maxDuration}
                      onChange={(e) => updateConfig('vapiConfig.maxDuration', parseInt(e.target.value))}
                      className="mt-2"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Custom AI Prompt</CardTitle>
                  <CardDescription>Customize how your AI assistant handles claims calls</CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={config.vapiConfig.customPrompt}
                    onChange={(e) => updateConfig('vapiConfig.customPrompt', e.target.value)}
                    rows={10}
                    className="font-mono text-sm"
                  />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 7: Integrations */}
          {currentStep === 6 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>External Integrations</CardTitle>
                  <CardDescription>Configure external service integrations</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>CRM Integration</Label>
                    <Switch
                      checked={config.integrations.crmEnabled}
                      onCheckedChange={(checked) => updateConfig('integrations.crmEnabled', checked)}
                    />
                  </div>

                  {config.integrations.crmEnabled && (
                    <div>
                      <Label htmlFor="crm-provider">CRM Provider</Label>
                      <Select
                        value={config.integrations.crmProvider}
                        onValueChange={(value) => updateConfig('integrations.crmProvider', value)}
                      >
                        <SelectTrigger id="crm-provider" className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="salesforce">Salesforce</SelectItem>
                          <SelectItem value="hubspot">HubSpot</SelectItem>
                          <SelectItem value="pipedrive">Pipedrive</SelectItem>
                          <SelectItem value="zoho">Zoho CRM</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="email-provider">Email Provider</Label>
                      <Select
                        value={config.integrations.emailProvider}
                        onValueChange={(value) => updateConfig('integrations.emailProvider', value)}
                      >
                        <SelectTrigger id="email-provider" className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="sendgrid">SendGrid</SelectItem>
                          <SelectItem value="mailgun">Mailgun</SelectItem>
                          <SelectItem value="ses">Amazon SES</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="sms-provider">SMS Provider</Label>
                      <Select
                        value={config.integrations.smsProvider}
                        onValueChange={(value) => updateConfig('integrations.smsProvider', value)}
                      >
                        <SelectTrigger id="sms-provider" className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="twilio">Twilio</SelectItem>
                          <SelectItem value="nexmo">Vonage (Nexmo)</SelectItem>
                          <SelectItem value="messagebird">MessageBird</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="document-storage">Document Storage</Label>
                    <Select
                      value={config.integrations.documentStorage}
                      onValueChange={(value) => updateConfig('integrations.documentStorage', value)}
                    >
                      <SelectTrigger id="document-storage" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="aws_s3">Amazon S3</SelectItem>
                        <SelectItem value="azure_blob">Azure Blob Storage</SelectItem>
                        <SelectItem value="google_cloud">Google Cloud Storage</SelectItem>
                        <SelectItem value="dropbox">Dropbox Business</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 8: Review */}
          {currentStep === 7 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Configuration Review</CardTitle>
                  <CardDescription>Review your insurance claims processing campaign configuration</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2">Basic Information</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Name:</strong> {config.name}</div>
                        <div><strong>Phone:</strong> {config.phoneNumber}</div>
                        <div><strong>Description:</strong> {config.description}</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Insurance API</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Provider:</strong> {INSURANCE_PROVIDERS.find(p => p.id === config.insuranceAPI.provider)?.name}</div>
                        <div><strong>Version:</strong> {config.insuranceAPI.version}</div>
                        <div><strong>URL:</strong> {config.insuranceAPI.apiUrl || 'Not configured'}</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Claims Workflow</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Auto Intake:</strong> {config.claimsWorkflow.autoIntake ? 'Enabled' : 'Disabled'}</div>
                        <div><strong>Fraud Detection:</strong> {config.claimsWorkflow.fraudDetectionEnabled ? 'Enabled' : 'Disabled'}</div>
                        <div><strong>Auto Approve Limit:</strong> ${config.claimsWorkflow.settlementThresholds.autoApprove.toLocaleString()}</div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Compliance</h4>
                      <div className="text-sm space-y-1">
                        <div><strong>Frameworks:</strong> {config.complianceConfig.frameworks.length} selected</div>
                        <div><strong>Retention:</strong> {config.complianceConfig.retentionPeriod} years</div>
                        <div><strong>Audit Trail:</strong> {config.complianceConfig.auditTrailEnabled ? 'Enabled' : 'Disabled'}</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-muted rounded-lg">
                    <div className="flex items-start gap-2">
                      <Shield className="h-5 w-5 text-green-500 mt-0.5" />
                      <div className="text-sm">
                        <strong>Ready to Deploy</strong>
                        <p className="mt-1 text-gray-600">
                          Your insurance claims processing campaign is configured and ready to handle customer claims.
                          Make sure all your API integrations are tested before going live.
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t pt-4 flex justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            Previous
          </Button>

          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>

            {currentStep === steps.length - 1 ? (
              <Button onClick={handleSubmit} disabled={isCreating}>
                {isCreating ? 'Creating...' : 'Create Campaign'}
              </Button>
            ) : (
              <Button onClick={handleNext}>
                Next
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};