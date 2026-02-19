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
import { ArrowLeft, ArrowRight, Heart, Calendar, AlertTriangle, FileText, DollarSign, Zap, CheckCircle } from 'lucide-react';

interface InsuranceRenewalConfig {
  name: string;
  description: string;
  phoneNumber: string;
  policyTypes: {
    enabled: string[];
    customTypes: string[];
  };
  renewalTiming: {
    advanceNoticeDays: number;
    reminderSequence: Array<{
      daysBeforeExpiry: number;
      channel: 'voice' | 'sms' | 'email';
      template: string;
    }>;
    finalNoticeDay: number;
  };
  customerSegmentation: {
    byPolicyValue: {
      enabled: boolean;
      tiers: Array<{
        name: string;
        minValue: number;
        maxValue: number;
        priorityLevel: 'high' | 'medium' | 'low';
      }>;
    };
    byRisk: {
      enabled: boolean;
      factors: string[];
      scoringCriteria: string;
    };
    byLoyalty: {
      enabled: boolean;
      yearsTiers: Array<{
        name: string;
        minYears: number;
        benefits: string[];
      }>;
    };
  };
  quotingSystem: {
    autoQuote: {
      enabled: boolean;
      baseRateAdjustment: number;
      loyaltyDiscounts: Array<{
        yearsThreshold: number;
        discountPercent: number;
      }>;
      riskFactorAdjustments: Array<{
        factor: string;
        adjustment: number;
      }>;
    };
    manualReview: {
      enabled: boolean;
      triggers: string[];
      assignToAgent: string;
    };
  };
  conversationFlow: {
    greeting: string;
    policyLookup: string;
    renewalPresentation: string;
    objectionHandling: {
      priceObjections: string;
      coverageQuestions: string;
      competitorComparisons: string;
      timingConcerns: string;
    };
    closingScripts: {
      renewal: string;
      modification: string;
      decline: string;
    };
  };
  paymentProcessing: {
    enabled: boolean;
    providers: string[];
    autoPaySetup: {
      enabled: boolean;
      incentives: string[];
    };
    paymentPlans: {
      enabled: boolean;
      options: Array<{
        name: string;
        installments: number;
        feePercent: number;
      }>;
    };
  };
  complianceSettings: {
    recordingConsent: boolean;
    disclosureRequirements: string[];
    regulatoryNotices: string[];
    dataRetention: {
      callRecordings: number;
      customerData: number;
      paymentInfo: number;
    };
  };
  integrations: {
    policyManagement: {
      enabled: boolean;
      provider: string;
      apiConfig?: {
        endpoint: string;
        apiKey: string;
      };
    };
    crm: {
      enabled: boolean;
      provider: 'salesforce' | 'hubspot' | 'custom';
      syncSettings: {
        renewalStatus: boolean;
        paymentHistory: boolean;
        customerNotes: boolean;
      };
    };
    accounting: {
      enabled: boolean;
      provider: 'quickbooks' | 'xero' | 'sage';
      autoInvoicing: boolean;
    };
  };
  n8nConfig?: {
    enabled: boolean;
    templateId: number;
    workflowSettings: {
      contractMonitoring: boolean;
      renewalNotifications: boolean;
      approvalWorkflow: boolean;
      vendorOutreach: boolean;
    };
  };
  reportingConfig: {
    kpis: string[];
    dashboards: {
      renewalRates: boolean;
      revenueTracking: boolean;
      customerSatisfaction: boolean;
      agentPerformance: boolean;
    };
    alerts: {
      lowRenewalRates: {
        enabled: boolean;
        threshold: number;
      };
      highChurnRisk: {
        enabled: boolean;
        criteria: string[];
      };
    };
  };
}

interface InsuranceRenewalWizardProps {
  onSave: (config: InsuranceRenewalConfig) => void;
  onCancel: () => void;
  initialConfig?: Partial<InsuranceRenewalConfig>;
}

export const InsuranceRenewalWizard: React.FC<InsuranceRenewalWizardProps> = ({
  onSave,
  onCancel,
  initialConfig
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<InsuranceRenewalConfig>({
    name: initialConfig?.name || '',
    description: initialConfig?.description || '',
    phoneNumber: initialConfig?.phoneNumber || '',
    policyTypes: {
      enabled: ['auto', 'home', 'life', 'health'],
      customTypes: [],
      ...initialConfig?.policyTypes
    },
    renewalTiming: {
      advanceNoticeDays: 60,
      reminderSequence: [
        {
          daysBeforeExpiry: 60,
          channel: 'email',
          template: 'Your policy renewal is coming up in 60 days. Let\'s review your coverage.',
        },
        {
          daysBeforeExpiry: 30,
          channel: 'voice',
          template: 'Hello [Name], your [Policy Type] policy expires in 30 days. I\'m calling to help you renew and discuss any changes to your coverage needs.',
        },
        {
          daysBeforeExpiry: 7,
          channel: 'sms',
          template: 'URGENT: Your insurance expires in 7 days! Call us to renew: [Phone]',
        },
      ],
      finalNoticeDay: 3,
      ...initialConfig?.renewalTiming
    },
    customerSegmentation: {
      byPolicyValue: {
        enabled: true,
        tiers: [
          { name: 'Premium', minValue: 5000, maxValue: 999999, priorityLevel: 'high' },
          { name: 'Standard', minValue: 1000, maxValue: 4999, priorityLevel: 'medium' },
          { name: 'Basic', minValue: 0, maxValue: 999, priorityLevel: 'low' },
        ],
      },
      byRisk: {
        enabled: true,
        factors: ['claims_history', 'payment_history', 'risk_score'],
        scoringCriteria: 'AI-based risk assessment using historical data',
      },
      byLoyalty: {
        enabled: true,
        yearsTiers: [
          { name: 'Gold (5+ years)', minYears: 5, benefits: ['10% discount', 'priority service', 'no deductible increase'] },
          { name: 'Silver (2-4 years)', minYears: 2, benefits: ['5% discount', 'extended grace period'] },
          { name: 'New (0-1 years)', minYears: 0, benefits: ['standard terms'] },
        ],
      },
      ...initialConfig?.customerSegmentation
    },
    quotingSystem: {
      autoQuote: {
        enabled: true,
        baseRateAdjustment: 0,
        loyaltyDiscounts: [
          { yearsThreshold: 5, discountPercent: 10 },
          { yearsThreshold: 2, discountPercent: 5 },
        ],
        riskFactorAdjustments: [
          { factor: 'good_driver', adjustment: -10 },
          { factor: 'claims_free', adjustment: -5 },
          { factor: 'security_features', adjustment: -3 },
        ],
      },
      manualReview: {
        enabled: true,
        triggers: ['high_risk_profile', 'multiple_claims', 'coverage_changes'],
        assignToAgent: 'senior_underwriter@company.com',
      },
      ...initialConfig?.quotingSystem
    },
    conversationFlow: {
      greeting: 'Hello [Name], your [Policy Type] policy is expiring on [Date]. I\'m calling to help you renew and discuss any changes to your coverage needs.',
      policyLookup: 'Let me pull up your current policy details. I see you have [Policy Details] with a premium of [Amount].',
      renewalPresentation: 'For your renewal, I can offer you [New Quote] which includes [Coverage Changes]. This represents [Savings/Increase] from your current premium.',
      objectionHandling: {
        priceObjections: 'I understand cost is important. Let me review available discounts and see if we can adjust your coverage to better fit your budget.',
        coverageQuestions: 'That\'s a great question about coverage. Let me explain exactly what\'s included and how it protects you.',
        competitorComparisons: 'I appreciate you shopping around. Let me show you what makes our coverage unique and ensure you\'re comparing similar benefits.',
        timingConcerns: 'I understand timing can be challenging. We can set up automatic renewal or discuss payment plan options to make this easier.',
      },
      closingScripts: {
        renewal: 'Excellent! I\'ll process your renewal right now. You\'ll receive confirmation within 24 hours, and your coverage will continue seamlessly.',
        modification: 'Perfect! Let me update your policy with these changes and provide you with a new quote. This will take just a moment.',
        decline: 'I understand this isn\'t the right time. I\'ll note your account and we can reconnect before your next renewal period. Is there anything else I can help with?',
      },
      ...initialConfig?.conversationFlow
    },
    paymentProcessing: {
      enabled: true,
      providers: ['stripe', 'paypal', 'ach'],
      autoPaySetup: {
        enabled: true,
        incentives: ['2% discount', 'no processing fees', 'automatic renewal'],
      },
      paymentPlans: {
        enabled: true,
        options: [
          { name: 'Annual', installments: 1, feePercent: 0 },
          { name: 'Semi-Annual', installments: 2, feePercent: 2 },
          { name: 'Quarterly', installments: 4, feePercent: 4 },
          { name: 'Monthly', installments: 12, feePercent: 8 },
        ],
      },
      ...initialConfig?.paymentProcessing
    },
    complianceSettings: {
      recordingConsent: true,
      disclosureRequirements: [
        'rates_subject_to_change',
        'coverage_limitations',
        'cancellation_policy',
        'complaint_procedures',
      ],
      regulatoryNotices: [
        'state_insurance_commission',
        'fair_credit_reporting',
        'privacy_notice',
      ],
      dataRetention: {
        callRecordings: 1095, // 3 years
        customerData: 2555, // 7 years
        paymentInfo: 365, // 1 year
      },
      ...initialConfig?.complianceSettings
    },
    integrations: {
      policyManagement: {
        enabled: false,
        provider: '',
      },
      crm: {
        enabled: false,
        provider: 'salesforce',
        syncSettings: {
          renewalStatus: true,
          paymentHistory: true,
          customerNotes: true,
        },
      },
      accounting: {
        enabled: false,
        provider: 'quickbooks',
        autoInvoicing: true,
      },
      ...initialConfig?.integrations
    },
    n8nConfig: {
      enabled: true,
      templateId: 6935,
      workflowSettings: {
        contractMonitoring: true,
        renewalNotifications: true,
        approvalWorkflow: true,
        vendorOutreach: false,
      },
      ...initialConfig?.n8nConfig
    },
    reportingConfig: {
      kpis: ['renewal_rate', 'revenue_retention', 'customer_satisfaction', 'average_premium'],
      dashboards: {
        renewalRates: true,
        revenueTracking: true,
        customerSatisfaction: true,
        agentPerformance: true,
      },
      alerts: {
        lowRenewalRates: {
          enabled: true,
          threshold: 80,
        },
        highChurnRisk: {
          enabled: true,
          criteria: ['payment_delays', 'complaint_history', 'coverage_reductions'],
        },
      },
      ...initialConfig?.reportingConfig
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

  const addCustomPolicyType = () => {
    const newType = prompt('Enter custom policy type:');
    if (newType) {
      setConfig(prev => ({
        ...prev,
        policyTypes: {
          ...prev.policyTypes,
          customTypes: [...prev.policyTypes.customTypes, newType]
        }
      }));
    }
  };

  const addReminderStep = () => {
    const newReminder = {
      daysBeforeExpiry: 14,
      channel: 'email' as const,
      template: 'Your policy expires in 14 days. Please contact us to renew.',
    };
    setConfig(prev => ({
      ...prev,
      renewalTiming: {
        ...prev.renewalTiming,
        reminderSequence: [...prev.renewalTiming.reminderSequence, newReminder]
      }
    }));
  };

  const removeReminderStep = (index: number) => {
    setConfig(prev => ({
      ...prev,
      renewalTiming: {
        ...prev.renewalTiming,
        reminderSequence: prev.renewalTiming.reminderSequence.filter((_, i) => i !== index)
      }
    }));
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
                placeholder="e.g., Q1 Insurance Renewal Campaign"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={config.description}
                onChange={(e) => updateConfig('description', e.target.value)}
                placeholder="Describe the goals and scope of this renewal campaign..."
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

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Policy Types</h4>
                <Button onClick={addCustomPolicyType} size="sm" variant="outline">Add Custom</Button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {['auto', 'home', 'life', 'health', 'business', 'disability'].map((type) => (
                  <div key={type} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={type}
                      checked={config.policyTypes.enabled.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateConfig('policyTypes.enabled', [...config.policyTypes.enabled, type]);
                        } else {
                          updateConfig('policyTypes.enabled', config.policyTypes.enabled.filter(t => t !== type));
                        }
                      }}
                    />
                    <Label htmlFor={type} className="capitalize">{type} Insurance</Label>
                  </div>
                ))}
              </div>

              {config.policyTypes.customTypes.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Custom Types:</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {config.policyTypes.customTypes.map((type, index) => (
                      <Badge key={index} variant="secondary">
                        {type}
                        <button
                          onClick={() => updateConfig('policyTypes.customTypes', config.policyTypes.customTypes.filter((_, i) => i !== index))}
                          className="ml-2 text-xs"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="advanceNotice">Advance Notice Period (days)</Label>
              <Input
                id="advanceNotice"
                type="number"
                value={config.renewalTiming.advanceNoticeDays}
                onChange={(e) => updateConfig('renewalTiming.advanceNoticeDays', parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Reminder Sequence</h4>
                <Button onClick={addReminderStep} size="sm">Add Reminder</Button>
              </div>

              {config.renewalTiming.reminderSequence.map((reminder, index) => (
                <div key={index} className="p-4 border rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Reminder {index + 1}</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeReminderStep(index)}
                    >
                      Remove
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor={`days-${index}`}>Days Before Expiry</Label>
                      <Input
                        id={`days-${index}`}
                        type="number"
                        value={reminder.daysBeforeExpiry}
                        onChange={(e) => updateConfig(`renewalTiming.reminderSequence.${index}.daysBeforeExpiry`, parseInt(e.target.value) || 0)}
                      />
                    </div>
                    <div>
                      <Label htmlFor={`channel-${index}`}>Channel</Label>
                      <Select
                        value={reminder.channel}
                        onValueChange={(value) => updateConfig(`renewalTiming.reminderSequence.${index}.channel`, value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="voice">Voice Call</SelectItem>
                          <SelectItem value="email">Email</SelectItem>
                          <SelectItem value="sms">SMS</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label htmlFor={`template-${index}`}>Message Template</Label>
                    <Textarea
                      id={`template-${index}`}
                      value={reminder.template}
                      onChange={(e) => updateConfig(`renewalTiming.reminderSequence.${index}.template`, e.target.value)}
                      rows={2}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div>
              <Label htmlFor="finalNotice">Final Notice (days before expiry)</Label>
              <Input
                id="finalNotice"
                type="number"
                value={config.renewalTiming.finalNoticeDay}
                onChange={(e) => updateConfig('renewalTiming.finalNoticeDay', parseInt(e.target.value) || 0)}
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Policy Value Segmentation</p>
                <p className="text-sm text-gray-600">Prioritize by premium amount</p>
              </div>
              <Switch
                checked={config.customerSegmentation.byPolicyValue.enabled}
                onCheckedChange={(checked) => updateConfig('customerSegmentation.byPolicyValue.enabled', checked)}
              />
            </div>

            {config.customerSegmentation.byPolicyValue.enabled && (
              <div className="p-4 border rounded-lg space-y-4">
                <h5 className="font-medium">Value Tiers</h5>
                {config.customerSegmentation.byPolicyValue.tiers.map((tier, index) => (
                  <div key={index} className="grid grid-cols-4 gap-4 items-center">
                    <Input
                      value={tier.name}
                      onChange={(e) => updateConfig(`customerSegmentation.byPolicyValue.tiers.${index}.name`, e.target.value)}
                      placeholder="Tier name"
                    />
                    <Input
                      type="number"
                      value={tier.minValue}
                      onChange={(e) => updateConfig(`customerSegmentation.byPolicyValue.tiers.${index}.minValue`, parseInt(e.target.value) || 0)}
                      placeholder="Min value"
                    />
                    <Input
                      type="number"
                      value={tier.maxValue}
                      onChange={(e) => updateConfig(`customerSegmentation.byPolicyValue.tiers.${index}.maxValue`, parseInt(e.target.value) || 0)}
                      placeholder="Max value"
                    />
                    <Select
                      value={tier.priorityLevel}
                      onValueChange={(value) => updateConfig(`customerSegmentation.byPolicyValue.tiers.${index}.priorityLevel`, value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="high">High Priority</SelectItem>
                        <SelectItem value="medium">Medium Priority</SelectItem>
                        <SelectItem value="low">Low Priority</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Risk-Based Segmentation</p>
                <p className="text-sm text-gray-600">Segment by risk factors</p>
              </div>
              <Switch
                checked={config.customerSegmentation.byRisk.enabled}
                onCheckedChange={(checked) => updateConfig('customerSegmentation.byRisk.enabled', checked)}
              />
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Loyalty Segmentation</p>
                <p className="text-sm text-gray-600">Segment by years as customer</p>
              </div>
              <Switch
                checked={config.customerSegmentation.byLoyalty.enabled}
                onCheckedChange={(checked) => updateConfig('customerSegmentation.byLoyalty.enabled', checked)}
              />
            </div>

            {config.customerSegmentation.byLoyalty.enabled && (
              <div className="p-4 border rounded-lg space-y-4">
                <h5 className="font-medium">Loyalty Tiers</h5>
                {config.customerSegmentation.byLoyalty.yearsTiers.map((tier, index) => (
                  <div key={index} className="space-y-2">
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        value={tier.name}
                        onChange={(e) => updateConfig(`customerSegmentation.byLoyalty.yearsTiers.${index}.name`, e.target.value)}
                        placeholder="Tier name"
                      />
                      <Input
                        type="number"
                        value={tier.minYears}
                        onChange={(e) => updateConfig(`customerSegmentation.byLoyalty.yearsTiers.${index}.minYears`, parseInt(e.target.value) || 0)}
                        placeholder="Min years"
                      />
                    </div>
                    <Input
                      value={tier.benefits.join(', ')}
                      onChange={(e) => updateConfig(`customerSegmentation.byLoyalty.yearsTiers.${index}.benefits`, e.target.value.split(', ').filter(b => b.trim()))}
                      placeholder="Benefits (comma-separated)"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Auto-Quote Generation</p>
                <p className="text-sm text-gray-600">Automatically generate renewal quotes</p>
              </div>
              <Switch
                checked={config.quotingSystem.autoQuote.enabled}
                onCheckedChange={(checked) => updateConfig('quotingSystem.autoQuote.enabled', checked)}
              />
            </div>

            {config.quotingSystem.autoQuote.enabled && (
              <div className="p-4 border rounded-lg space-y-4">
                <div>
                  <Label htmlFor="baseRate">Base Rate Adjustment (%)</Label>
                  <Input
                    id="baseRate"
                    type="number"
                    value={config.quotingSystem.autoQuote.baseRateAdjustment}
                    onChange={(e) => updateConfig('quotingSystem.autoQuote.baseRateAdjustment', parseFloat(e.target.value) || 0)}
                    placeholder="0 for no change, positive for increase, negative for decrease"
                  />
                </div>

                <div>
                  <h5 className="font-medium">Loyalty Discounts</h5>
                  {config.quotingSystem.autoQuote.loyaltyDiscounts.map((discount, index) => (
                    <div key={index} className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor={`years-${index}`}>Years Threshold</Label>
                        <Input
                          id={`years-${index}`}
                          type="number"
                          value={discount.yearsThreshold}
                          onChange={(e) => updateConfig(`quotingSystem.autoQuote.loyaltyDiscounts.${index}.yearsThreshold`, parseInt(e.target.value) || 0)}
                        />
                      </div>
                      <div>
                        <Label htmlFor={`discount-${index}`}>Discount %</Label>
                        <Input
                          id={`discount-${index}`}
                          type="number"
                          value={discount.discountPercent}
                          onChange={(e) => updateConfig(`quotingSystem.autoQuote.loyaltyDiscounts.${index}.discountPercent`, parseInt(e.target.value) || 0)}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Manual Review Queue</p>
                <p className="text-sm text-gray-600">Flag complex cases for human review</p>
              </div>
              <Switch
                checked={config.quotingSystem.manualReview.enabled}
                onCheckedChange={(checked) => updateConfig('quotingSystem.manualReview.enabled', checked)}
              />
            </div>

            {config.quotingSystem.manualReview.enabled && (
              <div className="p-4 border rounded-lg space-y-4">
                <div>
                  <Label htmlFor="reviewTriggers">Review Triggers (comma-separated)</Label>
                  <Input
                    id="reviewTriggers"
                    value={config.quotingSystem.manualReview.triggers.join(', ')}
                    onChange={(e) => updateConfig('quotingSystem.manualReview.triggers', e.target.value.split(', ').filter(t => t.trim()))}
                    placeholder="high_risk_profile, multiple_claims, coverage_changes"
                  />
                </div>
                <div>
                  <Label htmlFor="assignAgent">Assign to Agent</Label>
                  <Input
                    id="assignAgent"
                    value={config.quotingSystem.manualReview.assignToAgent}
                    onChange={(e) => updateConfig('quotingSystem.manualReview.assignToAgent', e.target.value)}
                    placeholder="agent@company.com"
                  />
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h4 className="font-medium">Conversation Scripts</h4>
              <div>
                <Label htmlFor="greeting">Greeting Script</Label>
                <Textarea
                  id="greeting"
                  value={config.conversationFlow.greeting}
                  onChange={(e) => updateConfig('conversationFlow.greeting', e.target.value)}
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="policyLookup">Policy Lookup Script</Label>
                <Textarea
                  id="policyLookup"
                  value={config.conversationFlow.policyLookup}
                  onChange={(e) => updateConfig('conversationFlow.policyLookup', e.target.value)}
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="renewalPresentation">Renewal Presentation Script</Label>
                <Textarea
                  id="renewalPresentation"
                  value={config.conversationFlow.renewalPresentation}
                  onChange={(e) => updateConfig('conversationFlow.renewalPresentation', e.target.value)}
                  rows={2}
                />
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Payment Processing</p>
                <p className="text-sm text-gray-600">Accept payments during renewal calls</p>
              </div>
              <Switch
                checked={config.paymentProcessing.enabled}
                onCheckedChange={(checked) => updateConfig('paymentProcessing.enabled', checked)}
              />
            </div>

            {config.paymentProcessing.enabled && (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="paymentProviders">Payment Providers (comma-separated)</Label>
                  <Input
                    id="paymentProviders"
                    value={config.paymentProcessing.providers.join(', ')}
                    onChange={(e) => updateConfig('paymentProcessing.providers', e.target.value.split(', ').filter(p => p.trim()))}
                    placeholder="stripe, paypal, ach"
                  />
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Auto-Pay Setup</p>
                    <p className="text-sm text-gray-600">Encourage automatic payments</p>
                  </div>
                  <Switch
                    checked={config.paymentProcessing.autoPaySetup.enabled}
                    onCheckedChange={(checked) => updateConfig('paymentProcessing.autoPaySetup.enabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Payment Plans</p>
                    <p className="text-sm text-gray-600">Offer installment options</p>
                  </div>
                  <Switch
                    checked={config.paymentProcessing.paymentPlans.enabled}
                    onCheckedChange={(checked) => updateConfig('paymentProcessing.paymentPlans.enabled', checked)}
                  />
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h4 className="font-medium">Compliance Settings</h4>

              <div className="flex items-center justify-between">
                <Label>Recording Consent Required</Label>
                <Switch
                  checked={config.complianceSettings.recordingConsent}
                  onCheckedChange={(checked) => updateConfig('complianceSettings.recordingConsent', checked)}
                />
              </div>

              <div>
                <Label htmlFor="disclosures">Disclosure Requirements (comma-separated)</Label>
                <Input
                  id="disclosures"
                  value={config.complianceSettings.disclosureRequirements.join(', ')}
                  onChange={(e) => updateConfig('complianceSettings.disclosureRequirements', e.target.value.split(', ').filter(d => d.trim()))}
                  placeholder="rates_subject_to_change, coverage_limitations"
                />
              </div>

              <div>
                <Label htmlFor="regulatory">Regulatory Notices (comma-separated)</Label>
                <Input
                  id="regulatory"
                  value={config.complianceSettings.regulatoryNotices.join(', ')}
                  onChange={(e) => updateConfig('complianceSettings.regulatoryNotices', e.target.value.split(', ').filter(n => n.trim()))}
                  placeholder="state_insurance_commission, fair_credit_reporting"
                />
              </div>

              <div className="space-y-2">
                <h5 className="font-medium">Data Retention (days)</h5>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="callRetention">Call Recordings</Label>
                    <Input
                      id="callRetention"
                      type="number"
                      value={config.complianceSettings.dataRetention.callRecordings}
                      onChange={(e) => updateConfig('complianceSettings.dataRetention.callRecordings', parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="customerRetention">Customer Data</Label>
                    <Input
                      id="customerRetention"
                      type="number"
                      value={config.complianceSettings.dataRetention.customerData}
                      onChange={(e) => updateConfig('complianceSettings.dataRetention.customerData', parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="paymentRetention">Payment Info</Label>
                    <Input
                      id="paymentRetention"
                      type="number"
                      value={config.complianceSettings.dataRetention.paymentInfo}
                      onChange={(e) => updateConfig('complianceSettings.dataRetention.paymentInfo', parseInt(e.target.value) || 0)}
                    />
                  </div>
                </div>
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
                <div className="flex items-center justify-between">
                  <Label>Contract Monitoring</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.contractMonitoring}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.contractMonitoring', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Renewal Notifications</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.renewalNotifications}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.renewalNotifications', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Approval Workflow</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.approvalWorkflow}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.approvalWorkflow', checked)}
                  />
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h4 className="font-medium">Reporting & Dashboards</h4>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <Label>Renewal Rates</Label>
                  <Switch
                    checked={config.reportingConfig.dashboards.renewalRates}
                    onCheckedChange={(checked) => updateConfig('reportingConfig.dashboards.renewalRates', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Revenue Tracking</Label>
                  <Switch
                    checked={config.reportingConfig.dashboards.revenueTracking}
                    onCheckedChange={(checked) => updateConfig('reportingConfig.dashboards.revenueTracking', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Customer Satisfaction</Label>
                  <Switch
                    checked={config.reportingConfig.dashboards.customerSatisfaction}
                    onCheckedChange={(checked) => updateConfig('reportingConfig.dashboards.customerSatisfaction', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Agent Performance</Label>
                  <Switch
                    checked={config.reportingConfig.dashboards.agentPerformance}
                    onCheckedChange={(checked) => updateConfig('reportingConfig.dashboards.agentPerformance', checked)}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="kpis">Key Performance Indicators (comma-separated)</Label>
                <Input
                  id="kpis"
                  value={config.reportingConfig.kpis.join(', ')}
                  onChange={(e) => updateConfig('reportingConfig.kpis', e.target.value.split(', ').filter(kpi => kpi.trim()))}
                  placeholder="renewal_rate, revenue_retention, customer_satisfaction"
                />
              </div>

              <div className="space-y-4">
                <h5 className="font-medium">Alerts Configuration</h5>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Low Renewal Rate Alert</p>
                    <p className="text-sm text-gray-600">Alert when renewal rate drops below threshold</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Label className="text-sm">Threshold %:</Label>
                      <Input
                        type="number"
                        value={config.reportingConfig.alerts.lowRenewalRates.threshold}
                        onChange={(e) => updateConfig('reportingConfig.alerts.lowRenewalRates.threshold', parseInt(e.target.value) || 0)}
                        className="w-20"
                      />
                    </div>
                    <Switch
                      checked={config.reportingConfig.alerts.lowRenewalRates.enabled}
                      onCheckedChange={(checked) => updateConfig('reportingConfig.alerts.lowRenewalRates.enabled', checked)}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">High Churn Risk Alert</p>
                    <p className="text-sm text-gray-600">Alert for customers at risk of churning</p>
                  </div>
                  <Switch
                    checked={config.reportingConfig.alerts.highChurnRisk.enabled}
                    onCheckedChange={(checked) => updateConfig('reportingConfig.alerts.highChurnRisk.enabled', checked)}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const getStepTitle = () => {
    const titles = [
      'Basic Setup & Policy Types',
      'Renewal Timing & Reminders',
      'Customer Segmentation',
      'Quoting & Conversation Flow',
      'Payments & Compliance',
      'Automation & Reporting'
    ];
    return titles[currentStep - 1];
  };

  const getStepIcon = () => {
    const icons = [FileText, Calendar, Users, DollarSign, AlertTriangle, Zap];
    const Icon = icons[currentStep - 1];
    return <Icon className="h-5 w-5" />;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          {getStepIcon()}
          <h1 className="text-2xl font-bold">Insurance Renewal Setup</h1>
          <Badge variant="outline">Step {currentStep} of {totalSteps}</Badge>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{getStepTitle()}</CardTitle>
          <CardDescription>
            Configure your insurance renewal campaign settings
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