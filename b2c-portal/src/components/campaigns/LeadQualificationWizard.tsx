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
import { ArrowLeft, ArrowRight, Users, Target, Zap, Star, FileText, BarChart, CheckCircle } from 'lucide-react';

interface LeadQualificationConfig {
  name: string;
  description: string;
  phoneNumber: string;
  leadSources: {
    webForms: {
      enabled: boolean;
      webhookUrl?: string;
    };
    coldOutreach: {
      enabled: boolean;
      listSources: string[];
    };
    referrals: {
      enabled: boolean;
      trackingMethod: 'code' | 'link' | 'manual';
    };
    events: {
      enabled: boolean;
      eventTypes: string[];
    };
  };
  qualificationCriteria: {
    budget: {
      enabled: boolean;
      minimum: number;
      maximum: number;
      currency: string;
    };
    authority: {
      enabled: boolean;
      roles: string[];
      decisionMakingProcess: string;
    };
    need: {
      enabled: boolean;
      painPoints: string[];
      priorityLevel: 'low' | 'medium' | 'high' | 'critical';
    };
    timeline: {
      enabled: boolean;
      urgency: 'immediate' | 'this_quarter' | 'next_quarter' | 'this_year' | 'no_timeline';
      specificDate?: string;
    };
    fit: {
      enabled: boolean;
      companySize: string[];
      industry: string[];
      geography: string[];
    };
  };
  scoringRules: {
    weightings: {
      budget: number;
      authority: number;
      need: number;
      timeline: number;
      fit: number;
    };
    thresholds: {
      hot: number;
      warm: number;
      cold: number;
    };
    automatedActions: {
      hotLeads: {
        action: 'immediate_call' | 'priority_assignment' | 'calendar_booking';
        assignTo?: string;
      };
      warmLeads: {
        action: 'follow_up_sequence' | 'nurture_campaign' | 'schedule_call';
        delay: number;
      };
      coldLeads: {
        action: 'long_nurture' | 'disqualify' | 'future_follow_up';
        revisitDays: number;
      };
    };
  };
  conversationFlow: {
    greeting: string;
    qualificationQuestions: Array<{
      id: string;
      question: string;
      category: 'budget' | 'authority' | 'need' | 'timeline' | 'fit';
      required: boolean;
      followUp?: string;
    }>;
    objectionHandling: {
      budgetConcerns: string;
      timingIssues: string;
      authorityQuestions: string;
      competitorMentions: string;
    };
    closingStatements: {
      qualified: string;
      needsNurturing: string;
      notQualified: string;
    };
  };
  integrations: {
    crm: {
      enabled: boolean;
      provider: 'salesforce' | 'hubspot' | 'pipedrive' | 'freshsales';
      leadRouting: {
        hotLeads: string;
        warmLeads: string;
        coldLeads: string;
      };
    };
    calendar: {
      enabled: boolean;
      provider: 'calendly' | 'acuity' | 'google_calendar';
      bookingLinks: {
        discovery: string;
        demo: string;
        consultation: string;
      };
    };
    notifications: {
      slack: {
        enabled: boolean;
        channelId?: string;
        mentionUsers?: string[];
      };
      email: {
        enabled: boolean;
        recipients: string[];
        template: string;
      };
    };
  };
  n8nConfig?: {
    enabled: boolean;
    templateId: number;
    workflowSettings: {
      realTimeScoring: boolean;
      autoAssignment: boolean;
      responseTracking: boolean;
    };
  };
  reportingConfig: {
    metrics: string[];
    dashboardUrl?: string;
    reports: {
      frequency: 'daily' | 'weekly' | 'monthly';
      recipients: string[];
      includeConversions: boolean;
    };
  };
}

interface LeadQualificationWizardProps {
  onSave: (config: LeadQualificationConfig) => void;
  onCancel: () => void;
  initialConfig?: Partial<LeadQualificationConfig>;
}

export const LeadQualificationWizard: React.FC<LeadQualificationWizardProps> = ({
  onSave,
  onCancel,
  initialConfig
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<LeadQualificationConfig>({
    name: initialConfig?.name || '',
    description: initialConfig?.description || '',
    phoneNumber: initialConfig?.phoneNumber || '',
    leadSources: {
      webForms: {
        enabled: true,
        webhookUrl: '',
      },
      coldOutreach: {
        enabled: true,
        listSources: ['linkedin', 'industry_lists', 'referrals'],
      },
      referrals: {
        enabled: true,
        trackingMethod: 'code',
      },
      events: {
        enabled: false,
        eventTypes: ['trade_shows', 'webinars', 'conferences'],
      },
      ...initialConfig?.leadSources
    },
    qualificationCriteria: {
      budget: {
        enabled: true,
        minimum: 5000,
        maximum: 100000,
        currency: 'USD',
      },
      authority: {
        enabled: true,
        roles: ['CEO', 'CTO', 'VP Sales', 'Director'],
        decisionMakingProcess: 'Individual decision maker',
      },
      need: {
        enabled: true,
        painPoints: ['manual_processes', 'scaling_issues', 'efficiency_problems'],
        priorityLevel: 'high',
      },
      timeline: {
        enabled: true,
        urgency: 'this_quarter',
        specificDate: '',
      },
      fit: {
        enabled: true,
        companySize: ['11-50', '51-200', '201-1000'],
        industry: ['technology', 'saas', 'professional_services'],
        geography: ['north_america', 'europe'],
      },
      ...initialConfig?.qualificationCriteria
    },
    scoringRules: {
      weightings: {
        budget: 25,
        authority: 20,
        need: 30,
        timeline: 15,
        fit: 10,
      },
      thresholds: {
        hot: 80,
        warm: 60,
        cold: 40,
      },
      automatedActions: {
        hotLeads: {
          action: 'immediate_call',
          assignTo: '',
        },
        warmLeads: {
          action: 'follow_up_sequence',
          delay: 24,
        },
        coldLeads: {
          action: 'long_nurture',
          revisitDays: 90,
        },
      },
      ...initialConfig?.scoringRules
    },
    conversationFlow: {
      greeting: 'Hi [Name], you expressed interest in [Product/Service]. I\'d like to understand your needs better to see how we can help. What\'s your biggest challenge with [specific area]?',
      qualificationQuestions: [
        {
          id: 'budget_discovery',
          question: 'What budget range have you allocated for solving this challenge?',
          category: 'budget',
          required: true,
          followUp: 'That helps me understand the scope. Have you worked with similar solutions before?',
        },
        {
          id: 'decision_authority',
          question: 'Who else would be involved in evaluating and deciding on a solution like this?',
          category: 'authority',
          required: true,
          followUp: 'Great, it\'s important to include all stakeholders in the process.',
        },
        {
          id: 'pain_discovery',
          question: 'Can you tell me more about the specific challenges you\'re facing with your current process?',
          category: 'need',
          required: true,
          followUp: 'I understand how frustrating that must be. How is this impacting your business?',
        },
        {
          id: 'timeline_urgency',
          question: 'What\'s your ideal timeline for implementing a solution?',
          category: 'timeline',
          required: true,
          followUp: 'That timeline makes sense given what you\'ve shared about your challenges.',
        },
      ],
      objectionHandling: {
        budgetConcerns: 'I understand budget is a key consideration. Let\'s focus on the value and ROI first, then we can explore options that fit your budget.',
        timingIssues: 'Timing is important. Can you help me understand what would need to change for the timing to be right?',
        authorityQuestions: 'Of course, involving the right stakeholders is crucial. Would it be helpful if I prepared some materials for your team review?',
        competitorMentions: 'That\'s great that you\'re evaluating options. What criteria are most important to you in making this decision?',
      },
      closingStatements: {
        qualified: 'Based on our conversation, it sounds like there might be a good fit. I\'d love to show you how we\'ve helped similar companies. Can we schedule a brief demo?',
        needsNurturing: 'Thank you for sharing that information. I\'ll send you some relevant resources, and let\'s reconnect in a few weeks to see how things evolve.',
        notQualified: 'I appreciate your time today. While it doesn\'t seem like the right fit right now, please keep us in mind for the future.',
      },
      ...initialConfig?.conversationFlow
    },
    integrations: {
      crm: {
        enabled: false,
        provider: 'salesforce',
        leadRouting: {
          hotLeads: '',
          warmLeads: '',
          coldLeads: '',
        },
      },
      calendar: {
        enabled: false,
        provider: 'calendly',
        bookingLinks: {
          discovery: '',
          demo: '',
          consultation: '',
        },
      },
      notifications: {
        slack: {
          enabled: false,
          channelId: '',
          mentionUsers: [],
        },
        email: {
          enabled: true,
          recipients: [],
          template: 'New qualified lead: [Name] from [Company] scored [Score]% and is ready for [Next Steps].',
        },
      },
      ...initialConfig?.integrations
    },
    n8nConfig: {
      enabled: true,
      templateId: 4458,
      workflowSettings: {
        realTimeScoring: true,
        autoAssignment: true,
        responseTracking: true,
      },
      ...initialConfig?.n8nConfig
    },
    reportingConfig: {
      metrics: ['conversion_rate', 'qualification_score', 'pipeline_velocity', 'lead_quality'],
      dashboardUrl: '',
      reports: {
        frequency: 'weekly',
        recipients: [],
        includeConversions: true,
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

  const addQualificationQuestion = () => {
    const newQuestion = {
      id: `question_${Date.now()}`,
      question: '',
      category: 'need' as const,
      required: false,
      followUp: ''
    };
    setConfig(prev => ({
      ...prev,
      conversationFlow: {
        ...prev.conversationFlow,
        qualificationQuestions: [...prev.conversationFlow.qualificationQuestions, newQuestion]
      }
    }));
  };

  const removeQualificationQuestion = (id: string) => {
    setConfig(prev => ({
      ...prev,
      conversationFlow: {
        ...prev.conversationFlow,
        qualificationQuestions: prev.conversationFlow.qualificationQuestions.filter(q => q.id !== id)
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
                placeholder="e.g., Q1 Lead Qualification Campaign"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={config.description}
                onChange={(e) => updateConfig('description', e.target.value)}
                placeholder="Describe the goals and target outcomes for this lead qualification campaign..."
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
              <h4 className="font-medium">Lead Sources</h4>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Web Forms</p>
                  <p className="text-sm text-gray-600">Contact forms, landing pages, sign-ups</p>
                </div>
                <Switch
                  checked={config.leadSources.webForms.enabled}
                  onCheckedChange={(checked) => updateConfig('leadSources.webForms.enabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Cold Outreach</p>
                  <p className="text-sm text-gray-600">LinkedIn, email campaigns, cold calls</p>
                </div>
                <Switch
                  checked={config.leadSources.coldOutreach.enabled}
                  onCheckedChange={(checked) => updateConfig('leadSources.coldOutreach.enabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Referrals</p>
                  <p className="text-sm text-gray-600">Customer and partner referrals</p>
                </div>
                <Switch
                  checked={config.leadSources.referrals.enabled}
                  onCheckedChange={(checked) => updateConfig('leadSources.referrals.enabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Events</p>
                  <p className="text-sm text-gray-600">Trade shows, webinars, conferences</p>
                </div>
                <Switch
                  checked={config.leadSources.events.enabled}
                  onCheckedChange={(checked) => updateConfig('leadSources.events.enabled', checked)}
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <p className="font-medium">Budget Qualification</p>
                  <Switch
                    checked={config.qualificationCriteria.budget.enabled}
                    onCheckedChange={(checked) => updateConfig('qualificationCriteria.budget.enabled', checked)}
                  />
                </div>
                {config.qualificationCriteria.budget.enabled && (
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    <Input
                      type="number"
                      placeholder="Min budget"
                      value={config.qualificationCriteria.budget.minimum}
                      onChange={(e) => updateConfig('qualificationCriteria.budget.minimum', parseInt(e.target.value) || 0)}
                    />
                    <Input
                      type="number"
                      placeholder="Max budget"
                      value={config.qualificationCriteria.budget.maximum}
                      onChange={(e) => updateConfig('qualificationCriteria.budget.maximum', parseInt(e.target.value) || 0)}
                    />
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
                )}
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <p className="font-medium">Authority Assessment</p>
                  <Switch
                    checked={config.qualificationCriteria.authority.enabled}
                    onCheckedChange={(checked) => updateConfig('qualificationCriteria.authority.enabled', checked)}
                  />
                </div>
                {config.qualificationCriteria.authority.enabled && (
                  <div className="space-y-2">
                    <Input
                      placeholder="Decision maker roles (comma-separated)"
                      value={config.qualificationCriteria.authority.roles.join(', ')}
                      onChange={(e) => updateConfig('qualificationCriteria.authority.roles', e.target.value.split(', ').filter(r => r.trim()))}
                    />
                    <Input
                      placeholder="Decision making process"
                      value={config.qualificationCriteria.authority.decisionMakingProcess}
                      onChange={(e) => updateConfig('qualificationCriteria.authority.decisionMakingProcess', e.target.value)}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <p className="font-medium">Need Identification</p>
                  <Switch
                    checked={config.qualificationCriteria.need.enabled}
                    onCheckedChange={(checked) => updateConfig('qualificationCriteria.need.enabled', checked)}
                  />
                </div>
                {config.qualificationCriteria.need.enabled && (
                  <div className="space-y-2">
                    <Input
                      placeholder="Pain points (comma-separated)"
                      value={config.qualificationCriteria.need.painPoints.join(', ')}
                      onChange={(e) => updateConfig('qualificationCriteria.need.painPoints', e.target.value.split(', ').filter(p => p.trim()))}
                    />
                    <Select
                      value={config.qualificationCriteria.need.priorityLevel}
                      onValueChange={(value) => updateConfig('qualificationCriteria.need.priorityLevel', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low Priority</SelectItem>
                        <SelectItem value="medium">Medium Priority</SelectItem>
                        <SelectItem value="high">High Priority</SelectItem>
                        <SelectItem value="critical">Critical Priority</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <p className="font-medium">Timeline Assessment</p>
                  <Switch
                    checked={config.qualificationCriteria.timeline.enabled}
                    onCheckedChange={(checked) => updateConfig('qualificationCriteria.timeline.enabled', checked)}
                  />
                </div>
                {config.qualificationCriteria.timeline.enabled && (
                  <Select
                    value={config.qualificationCriteria.timeline.urgency}
                    onValueChange={(value) => updateConfig('qualificationCriteria.timeline.urgency', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="immediate">Immediate (this month)</SelectItem>
                      <SelectItem value="this_quarter">This Quarter</SelectItem>
                      <SelectItem value="next_quarter">Next Quarter</SelectItem>
                      <SelectItem value="this_year">This Year</SelectItem>
                      <SelectItem value="no_timeline">No Specific Timeline</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-5 gap-4">
              <div>
                <Label htmlFor="budgetWeight">Budget %</Label>
                <Input
                  id="budgetWeight"
                  type="number"
                  value={config.scoringRules.weightings.budget}
                  onChange={(e) => updateConfig('scoringRules.weightings.budget', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="authorityWeight">Authority %</Label>
                <Input
                  id="authorityWeight"
                  type="number"
                  value={config.scoringRules.weightings.authority}
                  onChange={(e) => updateConfig('scoringRules.weightings.authority', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="needWeight">Need %</Label>
                <Input
                  id="needWeight"
                  type="number"
                  value={config.scoringRules.weightings.need}
                  onChange={(e) => updateConfig('scoringRules.weightings.need', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="timelineWeight">Timeline %</Label>
                <Input
                  id="timelineWeight"
                  type="number"
                  value={config.scoringRules.weightings.timeline}
                  onChange={(e) => updateConfig('scoringRules.weightings.timeline', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="fitWeight">Fit %</Label>
                <Input
                  id="fitWeight"
                  type="number"
                  value={config.scoringRules.weightings.fit}
                  onChange={(e) => updateConfig('scoringRules.weightings.fit', parseInt(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="hotThreshold">Hot Lead Threshold</Label>
                <Input
                  id="hotThreshold"
                  type="number"
                  value={config.scoringRules.thresholds.hot}
                  onChange={(e) => updateConfig('scoringRules.thresholds.hot', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="warmThreshold">Warm Lead Threshold</Label>
                <Input
                  id="warmThreshold"
                  type="number"
                  value={config.scoringRules.thresholds.warm}
                  onChange={(e) => updateConfig('scoringRules.thresholds.warm', parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <Label htmlFor="coldThreshold">Cold Lead Threshold</Label>
                <Input
                  id="coldThreshold"
                  type="number"
                  value={config.scoringRules.thresholds.cold}
                  onChange={(e) => updateConfig('scoringRules.thresholds.cold', parseInt(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Automated Actions</h4>

              <div className="p-4 border rounded-lg">
                <Label className="font-medium text-green-600">Hot Leads (🔥)</Label>
                <div className="mt-2 space-y-2">
                  <Select
                    value={config.scoringRules.automatedActions.hotLeads.action}
                    onValueChange={(value) => updateConfig('scoringRules.automatedActions.hotLeads.action', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="immediate_call">Immediate Call</SelectItem>
                      <SelectItem value="priority_assignment">Priority Assignment</SelectItem>
                      <SelectItem value="calendar_booking">Auto Calendar Booking</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input
                    placeholder="Assign to (email or name)"
                    value={config.scoringRules.automatedActions.hotLeads.assignTo || ''}
                    onChange={(e) => updateConfig('scoringRules.automatedActions.hotLeads.assignTo', e.target.value)}
                  />
                </div>
              </div>

              <div className="p-4 border rounded-lg">
                <Label className="font-medium text-yellow-600">Warm Leads (🌤)</Label>
                <div className="mt-2 space-y-2">
                  <Select
                    value={config.scoringRules.automatedActions.warmLeads.action}
                    onValueChange={(value) => updateConfig('scoringRules.automatedActions.warmLeads.action', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="follow_up_sequence">Follow-up Sequence</SelectItem>
                      <SelectItem value="nurture_campaign">Nurture Campaign</SelectItem>
                      <SelectItem value="schedule_call">Schedule Call</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="flex items-center gap-2">
                    <Label>Delay (hours):</Label>
                    <Input
                      type="number"
                      value={config.scoringRules.automatedActions.warmLeads.delay}
                      onChange={(e) => updateConfig('scoringRules.automatedActions.warmLeads.delay', parseInt(e.target.value) || 0)}
                      className="w-20"
                    />
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg">
                <Label className="font-medium text-blue-600">Cold Leads (❄️)</Label>
                <div className="mt-2 space-y-2">
                  <Select
                    value={config.scoringRules.automatedActions.coldLeads.action}
                    onValueChange={(value) => updateConfig('scoringRules.automatedActions.coldLeads.action', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="long_nurture">Long-term Nurture</SelectItem>
                      <SelectItem value="disqualify">Disqualify</SelectItem>
                      <SelectItem value="future_follow_up">Future Follow-up</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="flex items-center gap-2">
                    <Label>Revisit (days):</Label>
                    <Input
                      type="number"
                      value={config.scoringRules.automatedActions.coldLeads.revisitDays}
                      onChange={(e) => updateConfig('scoringRules.automatedActions.coldLeads.revisitDays', parseInt(e.target.value) || 0)}
                      className="w-20"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="greeting">Opening Greeting</Label>
              <Textarea
                id="greeting"
                value={config.conversationFlow.greeting}
                onChange={(e) => updateConfig('conversationFlow.greeting', e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">Qualification Questions</h4>
                <Button onClick={addQualificationQuestion} size="sm">Add Question</Button>
              </div>

              {config.conversationFlow.qualificationQuestions.map((question, index) => (
                <div key={question.id} className="p-4 border rounded-lg space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Question {index + 1}</Label>
                    <div className="flex items-center gap-2">
                      <Select
                        value={question.category}
                        onValueChange={(value) => updateConfig(`conversationFlow.qualificationQuestions.${index}.category`, value)}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="budget">Budget</SelectItem>
                          <SelectItem value="authority">Authority</SelectItem>
                          <SelectItem value="need">Need</SelectItem>
                          <SelectItem value="timeline">Timeline</SelectItem>
                          <SelectItem value="fit">Fit</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeQualificationQuestion(question.id)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                  <Textarea
                    value={question.question}
                    onChange={(e) => updateConfig(`conversationFlow.qualificationQuestions.${index}.question`, e.target.value)}
                    placeholder="Enter your qualification question..."
                    rows={2}
                  />
                  <Input
                    value={question.followUp || ''}
                    onChange={(e) => updateConfig(`conversationFlow.qualificationQuestions.${index}.followUp`, e.target.value)}
                    placeholder="Follow-up response (optional)..."
                  />
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={question.required}
                      onCheckedChange={(checked) => updateConfig(`conversationFlow.qualificationQuestions.${index}.required`, checked)}
                    />
                    <Label>Required Question</Label>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Objection Handling</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="budgetObjection">Budget Concerns</Label>
                  <Textarea
                    id="budgetObjection"
                    value={config.conversationFlow.objectionHandling.budgetConcerns}
                    onChange={(e) => updateConfig('conversationFlow.objectionHandling.budgetConcerns', e.target.value)}
                    rows={2}
                  />
                </div>
                <div>
                  <Label htmlFor="timingObjection">Timing Issues</Label>
                  <Textarea
                    id="timingObjection"
                    value={config.conversationFlow.objectionHandling.timingIssues}
                    onChange={(e) => updateConfig('conversationFlow.objectionHandling.timingIssues', e.target.value)}
                    rows={2}
                  />
                </div>
                <div>
                  <Label htmlFor="authorityObjection">Authority Questions</Label>
                  <Textarea
                    id="authorityObjection"
                    value={config.conversationFlow.objectionHandling.authorityQuestions}
                    onChange={(e) => updateConfig('conversationFlow.objectionHandling.authorityQuestions', e.target.value)}
                    rows={2}
                  />
                </div>
                <div>
                  <Label htmlFor="competitorObjection">Competitor Mentions</Label>
                  <Textarea
                    id="competitorObjection"
                    value={config.conversationFlow.objectionHandling.competitorMentions}
                    onChange={(e) => updateConfig('conversationFlow.objectionHandling.competitorMentions', e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">CRM Integration</p>
                <p className="text-sm text-gray-600">Sync qualified leads to CRM</p>
              </div>
              <Switch
                checked={config.integrations.crm.enabled}
                onCheckedChange={(checked) => updateConfig('integrations.crm.enabled', checked)}
              />
            </div>

            {config.integrations.crm.enabled && (
              <div className="p-4 border rounded-lg space-y-4">
                <div>
                  <Label>CRM Provider</Label>
                  <Select
                    value={config.integrations.crm.provider}
                    onValueChange={(value) => updateConfig('integrations.crm.provider', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="salesforce">Salesforce</SelectItem>
                      <SelectItem value="hubspot">HubSpot</SelectItem>
                      <SelectItem value="pipedrive">Pipedrive</SelectItem>
                      <SelectItem value="freshsales">Freshsales</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="hotLeadRoute">Hot Leads →</Label>
                    <Input
                      id="hotLeadRoute"
                      value={config.integrations.crm.leadRouting.hotLeads}
                      onChange={(e) => updateConfig('integrations.crm.leadRouting.hotLeads', e.target.value)}
                      placeholder="sales@company.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="warmLeadRoute">Warm Leads →</Label>
                    <Input
                      id="warmLeadRoute"
                      value={config.integrations.crm.leadRouting.warmLeads}
                      onChange={(e) => updateConfig('integrations.crm.leadRouting.warmLeads', e.target.value)}
                      placeholder="nurture@company.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="coldLeadRoute">Cold Leads →</Label>
                    <Input
                      id="coldLeadRoute"
                      value={config.integrations.crm.leadRouting.coldLeads}
                      onChange={(e) => updateConfig('integrations.crm.leadRouting.coldLeads', e.target.value)}
                      placeholder="marketing@company.com"
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Calendar Integration</p>
                <p className="text-sm text-gray-600">Auto-book qualified prospects</p>
              </div>
              <Switch
                checked={config.integrations.calendar.enabled}
                onCheckedChange={(checked) => updateConfig('integrations.calendar.enabled', checked)}
              />
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Notifications</h4>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Slack Notifications</p>
                  <p className="text-sm text-gray-600">Real-time qualified lead alerts</p>
                </div>
                <Switch
                  checked={config.integrations.notifications.slack.enabled}
                  onCheckedChange={(checked) => updateConfig('integrations.notifications.slack.enabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-gray-600">Email alerts for qualified leads</p>
                </div>
                <Switch
                  checked={config.integrations.notifications.email.enabled}
                  onCheckedChange={(checked) => updateConfig('integrations.notifications.email.enabled', checked)}
                />
              </div>

              {config.integrations.notifications.email.enabled && (
                <div className="p-4 border rounded-lg space-y-4">
                  <div>
                    <Label htmlFor="emailRecipients">Email Recipients (comma-separated)</Label>
                    <Input
                      id="emailRecipients"
                      value={config.integrations.notifications.email.recipients.join(', ')}
                      onChange={(e) => updateConfig('integrations.notifications.email.recipients', e.target.value.split(', ').filter(email => email.trim()))}
                      placeholder="sales@company.com, manager@company.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="emailTemplate">Email Template</Label>
                    <Textarea
                      id="emailTemplate"
                      value={config.integrations.notifications.email.template}
                      onChange={(e) => updateConfig('integrations.notifications.email.template', e.target.value)}
                      rows={3}
                    />
                  </div>
                </div>
              )}
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
                  <Label>Real-time Scoring</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.realTimeScoring}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.realTimeScoring', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Auto Assignment</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.autoAssignment}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.autoAssignment', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Response Tracking</Label>
                  <Switch
                    checked={config.n8nConfig.workflowSettings.responseTracking}
                    onCheckedChange={(checked) => updateConfig('n8nConfig.workflowSettings.responseTracking', checked)}
                  />
                </div>
              </div>
            )}

            <div className="space-y-4">
              <h4 className="font-medium">Reporting Configuration</h4>
              <div>
                <Label>Report Frequency</Label>
                <Select
                  value={config.reportingConfig.reports.frequency}
                  onValueChange={(value) => updateConfig('reportingConfig.reports.frequency', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="reportRecipients">Report Recipients (comma-separated emails)</Label>
                <Input
                  id="reportRecipients"
                  value={config.reportingConfig.reports.recipients.join(', ')}
                  onChange={(e) => updateConfig('reportingConfig.reports.recipients', e.target.value.split(', ').filter(email => email.trim()))}
                  placeholder="manager@company.com, team@company.com"
                />
              </div>
              <div>
                <Label htmlFor="customMetrics">Custom Metrics (comma-separated)</Label>
                <Input
                  id="customMetrics"
                  value={config.reportingConfig.metrics.join(', ')}
                  onChange={(e) => updateConfig('reportingConfig.metrics', e.target.value.split(', ').filter(metric => metric.trim()))}
                  placeholder="conversion_rate, qualification_score, pipeline_velocity"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label>Include Conversion Tracking</Label>
                <Switch
                  checked={config.reportingConfig.reports.includeConversions}
                  onCheckedChange={(checked) => updateConfig('reportingConfig.reports.includeConversions', checked)}
                />
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
      'Basic Setup & Sources',
      'Qualification Criteria',
      'Scoring & Actions',
      'Conversation Flow',
      'Integrations',
      'Automation & Reporting'
    ];
    return titles[currentStep - 1];
  };

  const getStepIcon = () => {
    const icons = [FileText, Target, Star, Users, Zap, BarChart];
    const Icon = icons[currentStep - 1];
    return <Icon className="h-5 w-5" />;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          {getStepIcon()}
          <h1 className="text-2xl font-bold">Lead Qualification Setup</h1>
          <Badge variant="outline">Step {currentStep} of {totalSteps}</Badge>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{getStepTitle()}</CardTitle>
          <CardDescription>
            Configure your lead qualification and scoring system
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