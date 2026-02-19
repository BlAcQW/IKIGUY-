import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Plus, Phone, Users, Database, Settings, Calendar, Mail, Trash2, Filter, Bot } from 'lucide-react';
import { useConfirmationHelpers } from '@/hooks/use-confirmation';
import { useToast } from '@/hooks/use-toast';

interface VoiceAgent {
  id: string;
  name: string;
  description: string;
  status: string;
  agentType: string;
}

interface DatabaseConnection {
  id: string;
  name: string;
  type: 'mysql' | 'postgresql' | 'sqlite';
  host: string;
  database: string;
}

interface DatabaseTable {
  name: string;
  columns: Array<{
    name: string;
    type: string;
    nullable: boolean;
  }>;
}

interface FilterCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'is_null' | 'is_not_null';
  value: string;
}

interface VoiceCampaignConfig {
  // Basic Info
  name: string;
  description: string;
  campaignType: string;
  
  // Voice Agent Selection
  voiceAgentId: string;
  
  // Audience Selection
  audienceType: 'predefined' | 'database';
  predefinedAudienceId: string;
  
  // Database Configuration
  databaseConnectionId: string;
  selectedTable: string;
  filterConditions: FilterCondition[];
  
  // Call Configuration
  maxConcurrentCalls: number;
  callSchedule: 'immediate' | 'scheduled';
  scheduledDate: string;
  scheduledTime: string;
  
  // Follow-up Configuration  
  enableEmailSummaries: boolean;
  emailTemplate: string;
  
  // Integration Configuration
  enableCalendlyBooking: boolean;
  calendlySettings: {
    eventTypeUrl: string;
    apiKey: string;
  };
}

interface VoiceCampaignDialogProps {
  trigger?: React.ReactNode;
  onCreateCampaign: (campaign: any) => void;
  apiBaseUrl: string;
}

const CAMPAIGN_TEMPLATES = [
  {
    id: 'contributions',
    name: 'Contribution Collection',
    description: 'Collect donations and contributions from supporters',
    icon: '💰',
    defaultPrompt: 'You are calling to request financial contributions for our important cause. Be respectful and understanding if they cannot contribute.',
  },
  {
    id: 'appointment_booking',
    name: 'Appointment Booking',
    description: 'Schedule appointments with leads and customers',
    icon: '📅',
    defaultPrompt: 'You are helping schedule appointments. Check availability and book convenient times for callers.',
  },
  {
    id: 'survey_research',
    name: 'Survey & Research',
    description: 'Conduct surveys and collect research data',
    icon: '📋',
    defaultPrompt: 'You are conducting a research survey. Ask questions clearly and record responses accurately.',
  },
  {
    id: 'event_promotion',
    name: 'Event Promotion',
    description: 'Promote events and gather RSVPs',
    icon: '🎉',
    defaultPrompt: 'You are promoting our upcoming event. Provide details and encourage attendance.',
  },
  {
    id: 'follow_up',
    name: 'Follow-up Calls',
    description: 'Follow up on previous interactions or purchases',
    icon: '📞',
    defaultPrompt: 'You are following up on previous interactions. Be helpful and address any concerns.',
  }
];

const FILTER_OPERATORS = [
  { id: 'equals', name: 'Equals', symbol: '=' },
  { id: 'not_equals', name: 'Not Equals', symbol: '≠' },
  { id: 'greater_than', name: 'Greater Than', symbol: '>' },
  { id: 'less_than', name: 'Less Than', symbol: '<' },
  { id: 'contains', name: 'Contains', symbol: 'LIKE' },
  { id: 'is_null', name: 'Is Empty', symbol: 'IS NULL' },
  { id: 'is_not_null', name: 'Is Not Empty', symbol: 'IS NOT NULL' }
];

export const VoiceCampaignDialog: React.FC<VoiceCampaignDialogProps> = ({
  trigger,
  onCreateCampaign,
  apiBaseUrl
}) => {
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const { confirmCancel, ConfirmationDialog } = useConfirmationHelpers();
  const { toast } = useToast();

  const [voiceAgents, setVoiceAgents] = useState<VoiceAgent[]>([]);
  const [databaseConnections, setDatabaseConnections] = useState<DatabaseConnection[]>([]);
  const [availableTables, setAvailableTables] = useState<string[]>([]);
  const [tableColumns, setTableColumns] = useState<DatabaseTable['columns']>([]);
  const [predefinedAudiences, setPredefinedAudiences] = useState<Array<{ id: string; name: string; size: number }>>([]);

  const [config, setConfig] = useState<VoiceCampaignConfig>({
    name: '',
    description: '',
    campaignType: '',
    voiceAgentId: '',
    audienceType: 'predefined',
    predefinedAudienceId: '',
    databaseConnectionId: '',
    selectedTable: '',
    filterConditions: [],
    maxConcurrentCalls: 3,
    callSchedule: 'immediate',
    scheduledDate: '',
    scheduledTime: '',
    enableEmailSummaries: true,
    emailTemplate: '',
    enableCalendlyBooking: false,
    calendlySettings: {
      eventTypeUrl: '',
      apiKey: ''
    }
  });

  const steps = [
    { id: 'basic', title: 'Campaign Info', icon: Bot },
    { id: 'agent', title: 'Voice Agent', icon: Phone },
    { id: 'audience', title: 'Target Audience', icon: Users },
    { id: 'filters', title: 'Audience Filters', icon: Filter },
    { id: 'calls', title: 'Call Settings', icon: Settings },
    { id: 'followup', title: 'Follow-up', icon: Mail }
  ];

  // Load data when dialog opens
  useEffect(() => {
    if (open) {
      loadVoiceAgents();
      loadDatabaseConnections();
      loadPredefinedAudiences();
    }
  }, [open]);

  // Load available tables when database connection changes
  useEffect(() => {
    if (config.databaseConnectionId) {
      loadDatabaseTables(config.databaseConnectionId);
    }
  }, [config.databaseConnectionId]);

  // Load table columns when table changes
  useEffect(() => {
    if (config.databaseConnectionId && config.selectedTable) {
      loadTableColumns(config.databaseConnectionId, config.selectedTable);
    }
  }, [config.databaseConnectionId, config.selectedTable]);

  const loadVoiceAgents = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/voice/assistants/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // The voice/assistants endpoint returns an array directly
        setVoiceAgents(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Failed to load voice agents:', error);
    }
  };

  const loadDatabaseConnections = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/campaigns/database-connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-service-token': localStorage.getItem('service_token') || 'kasaai-b2c-portal'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDatabaseConnections(data.connections || []);
      }
    } catch (error) {
      console.error('Failed to load database connections:', error);
    }
  };

  const loadDatabaseTables = async (connectionId: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/campaigns/database-tables/${connectionId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-service-token': localStorage.getItem('service_token') || 'kasaai-b2c-portal'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAvailableTables(data.tables || []);
      }
    } catch (error) {
      console.error('Failed to load database tables:', error);
    }
  };

  const loadTableColumns = async (connectionId: string, tableName: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/campaigns/table-columns/${connectionId}/${tableName}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'x-service-token': localStorage.getItem('service_token') || 'kasaai-b2c-portal'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTableColumns(data.columns || []);
      }
    } catch (error) {
      console.error('Failed to load table columns:', error);
    }
  };

  const loadPredefinedAudiences = async () => {
    try {
      // This would load existing predefined audiences
      setPredefinedAudiences([
        { id: 'all_customers', name: 'All Customers', size: 1250 },
        { id: 'active_subscribers', name: 'Active Subscribers', size: 850 },
        { id: 'leads', name: 'Potential Leads', size: 320 }
      ]);
    } catch (error) {
      console.error('Failed to load predefined audiences:', error);
    }
  };

  const hasUnsavedChanges = () => {
    return (
      config.name.trim() !== '' ||
      config.description.trim() !== '' ||
      config.campaignType !== '' ||
      config.voiceAgentId !== '' ||
      currentStep > 0
    );
  };

  const resetForm = () => {
    setCurrentStep(0);
    setConfig({
      name: '',
      description: '',
      campaignType: '',
      voiceAgentId: '',
      audienceType: 'predefined',
      predefinedAudienceId: '',
      databaseConnectionId: '',
      selectedTable: '',
      filterConditions: [],
      maxConcurrentCalls: 3,
      callSchedule: 'immediate',
      scheduledDate: '',
      scheduledTime: '',
      enableEmailSummaries: true,
      emailTemplate: '',
      enableCalendlyBooking: false,
      calendlySettings: {
        eventTypeUrl: '',
        apiKey: ''
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

  const addFilterCondition = () => {
    setConfig(prev => ({
      ...prev,
      filterConditions: [
        ...prev.filterConditions,
        { field: '', operator: 'equals', value: '' }
      ]
    }));
  };

  const updateFilterCondition = (index: number, field: keyof FilterCondition, value: string) => {
    setConfig(prev => ({
      ...prev,
      filterConditions: prev.filterConditions.map((condition, i) =>
        i === index ? { ...condition, [field]: value } : condition
      )
    }));
  };

  const removeFilterCondition = (index: number) => {
    setConfig(prev => ({
      ...prev,
      filterConditions: prev.filterConditions.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/campaigns/voice-campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const campaign = await response.json();
        onCreateCampaign(campaign);
        resetForm();
        setOpen(false);
        
        toast({
          title: "Campaign Created",
          description: "Your voice campaign has been created and will start processing."
        });
      } else {
        throw new Error('Failed to create campaign');
      }
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: "Failed to create campaign. Please try again.",
        variant: "destructive"
      });
    }
  };

  const currentStepData = steps[currentStep];
  const StepIcon = currentStepData.icon;

  if (!open) return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Voice Campaign
          </Button>
        )}
      </DialogTrigger>
    </Dialog>
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <DialogHeader className="border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <StepIcon className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <DialogTitle>Create Voice Campaign</DialogTitle>
              <DialogDescription>
                Step {currentStep + 1} of {steps.length}: {currentStepData.title}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Progress */}
        <div className="flex justify-between mb-6">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            
            return (
              <div 
                key={step.id}
                className={`flex flex-col items-center gap-2 ${isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-gray-600'}`}
              >
                <div className={`p-2 rounded-full ${isActive ? 'bg-primary/10' : isCompleted ? 'bg-green-100' : 'bg-muted'}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-xs text-center">{step.title}</span>
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Step 1: Basic Campaign Info */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Choose Campaign Template
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {CAMPAIGN_TEMPLATES.map((template) => (
                    <Card 
                      key={template.id}
                      className={`cursor-pointer transition-colors ${config.campaignType === template.id ? 'ring-2 ring-primary' : 'hover:bg-muted/50'}`}
                      onClick={() => setConfig(prev => ({ ...prev, campaignType: template.id }))}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{template.icon}</span>
                          <div>
                            <h3 className="font-medium">{template.name}</h3>
                            <p className="text-sm text-gray-600">{template.description}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div>
                  <Label htmlFor="campaign-name" className="text-sm font-medium">
                    Campaign Name *
                  </Label>
                  <Input
                    id="campaign-name"
                    value={config.name}
                    onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter campaign name"
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label htmlFor="campaign-description" className="text-sm font-medium">
                    Description
                  </Label>
                  <Textarea
                    id="campaign-description"
                    value={config.description}
                    onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe your campaign goals and strategy"
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Voice Agent Selection */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Select Voice Agent
                </Label>
                <div className="grid grid-cols-1 gap-4">
                  {voiceAgents.map((agent) => (
                    <Card 
                      key={agent.id}
                      className={`cursor-pointer transition-colors ${config.voiceAgentId === agent.id ? 'ring-2 ring-primary' : 'hover:bg-muted/50'}`}
                      onClick={() => setConfig(prev => ({ ...prev, voiceAgentId: agent.id }))}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-medium">{agent.name}</h3>
                            <p className="text-sm text-gray-600">{agent.description}</p>
                            <Badge variant="secondary" className="mt-2">
                              {agent.agentType}
                            </Badge>
                          </div>
                          <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                            {agent.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {voiceAgents.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-600">No voice agents found. Create a voice agent first.</p>
                    <Button variant="outline" className="mt-4">
                      Create Voice Agent
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Audience Selection */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Select Target Audience
                </Label>
                <Tabs 
                  value={config.audienceType} 
                  onValueChange={(value) => setConfig(prev => ({ ...prev, audienceType: value as any }))}
                >
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="predefined">Predefined Lists</TabsTrigger>
                    <TabsTrigger value="database">Database Table</TabsTrigger>
                  </TabsList>

                  <TabsContent value="predefined" className="space-y-4">
                    <div className="grid grid-cols-1 gap-4">
                      {predefinedAudiences.map((audience) => (
                        <Card 
                          key={audience.id}
                          className={`cursor-pointer transition-colors ${config.predefinedAudienceId === audience.id ? 'ring-2 ring-primary' : 'hover:bg-muted/50'}`}
                          onClick={() => setConfig(prev => ({ ...prev, predefinedAudienceId: audience.id }))}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <h3 className="font-medium">{audience.name}</h3>
                                <p className="text-sm text-gray-600">{audience.size} contacts</p>
                              </div>
                              <Badge variant="secondary">{audience.size}</Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="database" className="space-y-4">
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="db-connection">Database Connection</Label>
                        <Select 
                          value={config.databaseConnectionId} 
                          onValueChange={(value) => setConfig(prev => ({ ...prev, databaseConnectionId: value }))}
                        >
                          <SelectTrigger className="mt-2">
                            <SelectValue placeholder="Select database connection" />
                          </SelectTrigger>
                          <SelectContent>
                            {databaseConnections.map((conn) => (
                              <SelectItem key={conn.id} value={conn.id}>
                                {conn.name} ({conn.type})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {config.databaseConnectionId && (
                        <div>
                          <Label htmlFor="table-select">Table</Label>
                          <Select 
                            value={config.selectedTable} 
                            onValueChange={(value) => setConfig(prev => ({ ...prev, selectedTable: value }))}
                          >
                            <SelectTrigger className="mt-2">
                              <SelectValue placeholder="Select table" />
                            </SelectTrigger>
                            <SelectContent>
                              {availableTables.map((table) => (
                                <SelectItem key={table} value={table}>
                                  {table}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {databaseConnections.length === 0 && (
                        <div className="text-center py-8">
                          <p className="text-gray-600">No database connections found.</p>
                          <Button variant="outline" className="mt-4">
                            Add Database Connection
                          </Button>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          )}

          {/* Step 4: Audience Filters */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Filter Audience
                </Label>
                
                {config.audienceType === 'database' && config.selectedTable && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-600">
                        Add conditions to filter your audience from {config.selectedTable}
                      </p>
                      <Button onClick={addFilterCondition} size="sm">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Condition
                      </Button>
                    </div>

                    {config.filterConditions.map((condition, index) => (
                      <Card key={index}>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-4">
                            <Select 
                              value={condition.field} 
                              onValueChange={(value) => updateFilterCondition(index, 'field', value)}
                            >
                              <SelectTrigger className="flex-1">
                                <SelectValue placeholder="Select field" />
                              </SelectTrigger>
                              <SelectContent>
                                {tableColumns.map((column) => (
                                  <SelectItem key={column.name} value={column.name}>
                                    {column.name} ({column.type})
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>

                            <Select 
                              value={condition.operator} 
                              onValueChange={(value) => updateFilterCondition(index, 'operator', value)}
                            >
                              <SelectTrigger className="w-40">
                                <SelectValue placeholder="Operator" />
                              </SelectTrigger>
                              <SelectContent>
                                {FILTER_OPERATORS.map((op) => (
                                  <SelectItem key={op.id} value={op.id}>
                                    {op.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>

                            {!['is_null', 'is_not_null'].includes(condition.operator) && (
                              <Input
                                value={condition.value}
                                onChange={(e) => updateFilterCondition(index, 'value', e.target.value)}
                                placeholder="Value"
                                className="flex-1"
                              />
                            )}

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFilterCondition(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {config.filterConditions.length === 0 && (
                      <div className="text-center py-8 border-2 border-dashed border-muted-foreground rounded-lg">
                        <p className="text-gray-600">No filters applied. All records from the table will be included.</p>
                      </div>
                    )}
                  </div>
                )}

                {config.audienceType === 'predefined' && (
                  <div className="text-center py-8">
                    <p className="text-gray-600">Predefined audiences don't need additional filtering.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 5: Call Settings */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Call Configuration
                </Label>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="concurrent-calls">Maximum Concurrent Calls</Label>
                    <Select 
                      value={config.maxConcurrentCalls.toString()} 
                      onValueChange={(value) => setConfig(prev => ({ ...prev, maxConcurrentCalls: parseInt(value) }))}
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5].map((num) => (
                          <SelectItem key={num} value={num.toString()}>
                            {num} call{num > 1 ? 's' : ''} at a time
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-600 mt-1">
                      Limited to 5 concurrent calls maximum
                    </p>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Schedule</Label>
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="immediate"
                          name="schedule"
                          value="immediate"
                          checked={config.callSchedule === 'immediate'}
                          onChange={(e) => setConfig(prev => ({ ...prev, callSchedule: e.target.value as any }))}
                        />
                        <Label htmlFor="immediate">Start immediately</Label>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="scheduled"
                          name="schedule"
                          value="scheduled"
                          checked={config.callSchedule === 'scheduled'}
                          onChange={(e) => setConfig(prev => ({ ...prev, callSchedule: e.target.value as any }))}
                        />
                        <Label htmlFor="scheduled">Schedule for later</Label>
                      </div>

                      {config.callSchedule === 'scheduled' && (
                        <div className="ml-6 grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="date">Date</Label>
                            <Input
                              id="date"
                              type="date"
                              value={config.scheduledDate}
                              onChange={(e) => setConfig(prev => ({ ...prev, scheduledDate: e.target.value }))}
                              min={new Date().toISOString().split('T')[0]}
                            />
                          </div>
                          <div>
                            <Label htmlFor="time">Time</Label>
                            <Input
                              id="time"
                              type="time"
                              value={config.scheduledTime}
                              onChange={(e) => setConfig(prev => ({ ...prev, scheduledTime: e.target.value }))}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 6: Follow-up Configuration */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base font-medium mb-4 block">
                  Follow-up Configuration
                </Label>
                
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">Email Summaries</CardTitle>
                          <CardDescription>
                            Send email summaries of call transcripts
                          </CardDescription>
                        </div>
                        <Switch
                          checked={config.enableEmailSummaries}
                          onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enableEmailSummaries: checked }))}
                        />
                      </div>
                    </CardHeader>
                    
                    {config.enableEmailSummaries && (
                      <CardContent>
                        <div>
                          <Label htmlFor="email-template">Email Template</Label>
                          <Textarea
                            id="email-template"
                            value={config.emailTemplate}
                            onChange={(e) => setConfig(prev => ({ ...prev, emailTemplate: e.target.value }))}
                            placeholder="Enter email template. Use {{transcript}} for call transcript and {{summary}} for AI summary."
                            rows={4}
                            className="mt-2"
                          />
                          <p className="text-xs text-gray-600 mt-1">
                            Available variables: {{transcript}}, {{summary}}, {{duration}}, {{caller_name}}, {{phone_number}}
                          </p>
                        </div>
                      </CardContent>
                    )}
                  </Card>

                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">Calendly Booking</CardTitle>
                          <CardDescription>
                            Enable appointment booking during calls
                          </CardDescription>
                        </div>
                        <Switch
                          checked={config.enableCalendlyBooking}
                          onCheckedChange={(checked) => setConfig(prev => ({ ...prev, enableCalendlyBooking: checked }))}
                        />
                      </div>
                    </CardHeader>
                    
                    {config.enableCalendlyBooking && (
                      <CardContent className="space-y-4">
                        <div>
                          <Label htmlFor="calendly-url">Calendly Event Type URL</Label>
                          <Input
                            id="calendly-url"
                            value={config.calendlySettings.eventTypeUrl}
                            onChange={(e) => setConfig(prev => ({ 
                              ...prev, 
                              calendlySettings: { ...prev.calendlySettings, eventTypeUrl: e.target.value }
                            }))}
                            placeholder="https://calendly.com/your-name/meeting"
                            className="mt-2"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="calendly-api-key">Calendly API Key</Label>
                          <Input
                            id="calendly-api-key"
                            type="password"
                            value={config.calendlySettings.apiKey}
                            onChange={(e) => setConfig(prev => ({ 
                              ...prev, 
                              calendlySettings: { ...prev.calendlySettings, apiKey: e.target.value }
                            }))}
                            placeholder="Enter your Calendly API key"
                            className="mt-2"
                          />
                        </div>
                      </CardContent>
                    )}
                  </Card>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t pt-4 flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            
            {currentStep === steps.length - 1 ? (
              <Button onClick={handleSubmit}>
                Create Campaign
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))}
                disabled={currentStep === 0 && (!config.name || !config.campaignType)}
              >
                Next
              </Button>
            )}
          </div>
        </div>

        <ConfirmationDialog />
      </DialogContent>
    </Dialog>
  );
};