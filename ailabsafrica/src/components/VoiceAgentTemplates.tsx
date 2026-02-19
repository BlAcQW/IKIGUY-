import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { 
  Phone, 
  MessageSquare, 
  ShoppingCart, 
  Heart, 
  Building, 
  GraduationCap, 
  Car, 
  Home,
  Star,
  Users,
  Target,
  Zap,
  Clock,
  CheckCircle,
  ArrowRight,
  Info,
  Search,
  Calendar,
  ClipboardList,
  Shield,
  Settings,
  Share2,
  Code
} from 'lucide-react';
import TemplateConfiguration from './TemplateCustomization';
import TemplateTesting from './TemplateTesting';
import TemplateIntegrationConfig from './TemplateIntegrationConfig';
import TemplateAnalytics from './TemplateAnalytics';
import TemplateSharing from './TemplateSharing';
import TemplateMarketplace from './TemplateMarketplace';
import AdvancedTemplateFeatures from './AdvancedTemplateFeatures';

export interface VoiceTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedTime: string;
  features: string[];
  systemPrompt: string;
  sampleQuestions: string[];
  useCases: string[];
  tags: string[];
  popularity: number;
  integrations?: {
    calendar?: {
      type: 'google' | 'outlook' | 'calendly' | 'custom';
      calendarId?: string;
      apiKey?: string;
    };
    email?: {
      provider: 'gmail' | 'outlook' | 'sendgrid' | 'mailgun' | 'custom';
      emailAddress?: string;
      apiKey?: string;
      templates?: {
        confirmation?: string;
        reminder?: string;
        cancellation?: string;
      };
    };
    whatsapp?: {
      enabled: boolean;
      phoneNumber?: string;
      apiKey?: string;
      provider?: 'twilio' | 'whatsapp-business' | 'custom';
    };
    sheets?: {
      enabled: boolean;
      spreadsheetId?: string;
      apiKey?: string;
      sheets?: {
        appointments?: string;
        contacts?: string;
        analytics?: string;
      };
    };
    crm?: {
      enabled: boolean;
      provider: 'salesforce' | 'hubspot' | 'pipedrive' | 'custom';
      apiKey?: string;
      baseUrl?: string;
    };
    database?: {
      enabled: boolean;
      type: 'supabase' | 'firebase' | 'mongodb' | 'postgresql' | 'custom';
      connectionString?: string;
      tables?: {
        appointments?: string;
        contacts?: string;
        interactions?: string;
      };
    };
  };
}

// Helper function to render icons
const renderIcon = (iconName: string, className: string = "h-6 w-6") => {
  if (typeof iconName !== 'string') {
    return <MessageSquare className={className} />;
  }
  
  const normalizedIconName = iconName.trim();
  
  switch (normalizedIconName) {
    case 'MessageSquare':
      return <MessageSquare className={className} />;
    case 'Phone':
      return <Phone className={className} />;
    case 'Calendar':
      return <Calendar className={className} />;
    case 'ClipboardList':
      return <ClipboardList className={className} />;
    case 'ShoppingCart':
      return <ShoppingCart className={className} />;
    case 'Heart':
      return <Heart className={className} />;
    case 'Building':
      return <Building className={className} />;
    case 'GraduationCap':
      return <GraduationCap className={className} />;
    case 'Car':
      return <Car className={className} />;
    case 'Home':
      return <Home className={className} />;
    case 'Users':
      return <Users className={className} />;
    case 'Shield':
      return <Shield className={className} />;
    case 'Star':
      return <Star className={className} />;
    case 'Settings':
      return <Settings className={className} />;
    default:
      return <MessageSquare className={className} />;
  }
};

const templates: VoiceTemplate[] = [
  {
    id: 'customer-support',
    name: 'Customer Support Agent',
    description: 'Handle customer inquiries, troubleshoot issues, and provide product support',
    category: 'Customer Service',
    icon: 'MessageSquare',
    difficulty: 'Beginner',
    estimatedTime: '15-30 minutes',
    features: ['Issue Resolution', 'Product Information', 'Ticket Creation', 'FAQ Handling'],
    systemPrompt: `You are a helpful customer support agent for {company_name}. Your role is to:
- Greet customers warmly and identify their needs
- Provide accurate product information and troubleshooting steps
- Create support tickets when issues cannot be resolved immediately
- Escalate complex issues to human agents when necessary
- Maintain a professional and empathetic tone throughout the conversation

Always ask for clarification if the customer's request is unclear and confirm solutions before ending the call.`,
    sampleQuestions: [
      'How do I reset my password?',
      'What are your return policies?',
      'I need help with my order',
      'Can you explain your warranty coverage?'
    ],
    useCases: ['E-commerce Support', 'SaaS Customer Service', 'Product Support', 'Technical Help'],
    tags: ['support', 'customer-service', 'help-desk', 'troubleshooting'],
    popularity: 95
  },
  {
    id: 'appointment-scheduler',
    name: 'Appointment Scheduler',
    description: 'Schedule appointments, manage calendars, and send confirmations',
    category: 'Scheduling',
    icon: 'Calendar',
    difficulty: 'Beginner',
    estimatedTime: '10-20 minutes',
    features: ['Calendar Management', 'Availability Checking', 'Confirmation Emails', 'Reminder Notifications'],
    systemPrompt: `You are an appointment scheduling assistant for {business_name}. Your responsibilities include:
- Greet callers warmly and identify their scheduling needs
- Check available time slots and suggest optimal appointment times
- Confirm appointment details including date, time, and duration
- Send confirmation emails or SMS reminders
- Handle rescheduling and cancellation requests professionally

Always confirm the caller's contact information and provide clear instructions for the appointment.`,
    sampleQuestions: [
      'What type of appointment do you need?',
      'What is your preferred date and time?',
      'How long should I schedule for this appointment?',
      'Would you like a reminder sent to your phone or email?'
    ],
    useCases: ['Medical Offices', 'Salons', 'Consulting Services', 'Real Estate'],
    tags: ['scheduling', 'appointments', 'calendar', 'booking'],
    popularity: 92
  }
];

const categories = [
  { id: 'all', name: 'All Templates', icon: 'Star' },
  { id: 'customer-service', name: 'Customer Service', icon: 'MessageSquare' },
  { id: 'scheduling', name: 'Scheduling', icon: 'Calendar' }
];

interface VoiceAgentTemplatesProps {
  onTemplateSelect: (template: VoiceTemplate) => void;
  selectedTemplate?: VoiceTemplate | null;
}

const VoiceAgentTemplates: React.FC<VoiceAgentTemplatesProps> = ({ 
  onTemplateSelect, 
  selectedTemplate 
}) => {
  const { toast } = useToast();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [templateToConfigure, setTemplateToConfigure] = useState<VoiceTemplate | null>(null);
  const [templateToTest, setTemplateToTest] = useState<VoiceTemplate | null>(null);
  const [templateToIntegrate, setTemplateToIntegrate] = useState<VoiceTemplate | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [templateToShare, setTemplateToShare] = useState<VoiceTemplate | null>(null);
  const [showMarketplace, setShowMarketplace] = useState(false);
  const [showAdvancedFeatures, setShowAdvancedFeatures] = useState(false);
  const [templateForAdvancedFeatures, setTemplateForAdvancedFeatures] = useState<VoiceTemplate | null>(null);
  const [isConfirmingTemplate, setIsConfirmingTemplate] = useState(false);
  const [templateConfirmed, setTemplateConfirmed] = useState(false);

  const filteredTemplates = selectedCategory === 'all' 
    ? templates 
    : templates.filter(template => {
        const templateCategoryId = template.category.toLowerCase().replace(/\s+/g, '-');
        return templateCategoryId === selectedCategory;
      });

  // Reset confirmation state when selected template changes
  React.useEffect(() => {
    setTemplateConfirmed(false);
  }, [selectedTemplate?.id]);

  const sortedTemplates = [...filteredTemplates].sort((a, b) => b.popularity - a.popularity);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return 'bg-green-100 text-green-800';
      case 'Intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'Advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleConfigureTemplate = (template: VoiceTemplate) => {
    setTemplateToConfigure(template);
  };

  const handleTestTemplate = (template: VoiceTemplate) => {
    setTemplateToTest(template);
  };

  const handleIntegrateTemplate = (template: VoiceTemplate) => {
    setTemplateToIntegrate(template);
  };

  const handleShowAnalytics = () => {
    setShowAnalytics(true);
  };

  const handleShareTemplate = (template: VoiceTemplate) => {
    setTemplateToShare(template);
  };

  const handleShowMarketplace = () => {
    setShowMarketplace(true);
  };

  const handleShowAdvancedFeatures = (template: VoiceTemplate) => {
    setTemplateForAdvancedFeatures(template);
    setShowAdvancedFeatures(true);
  };

  const handleConfigurationComplete = (configuredTemplate: VoiceTemplate) => {
    onTemplateSelect(configuredTemplate);
    setTemplateToConfigure(null);
    
    // Show success message for configuration completion
    toast({
      title: "Configuration Saved",
      description: `${configuredTemplate.name} configuration has been saved and applied. You can now proceed with the assistant creation.`,
      duration: 4000,
    });
  };

  const handleUseTemplate = async () => {
    if (!selectedTemplate) return;
    
    setIsConfirmingTemplate(true);
    
    try {
      // Simulate a brief delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 500));
      
      onTemplateSelect(selectedTemplate);
      setTemplateConfirmed(true);
      
      toast({
        title: "Template Selected",
        description: `${selectedTemplate.name} has been selected and is ready to use.`,
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to select template. Please try again.",
        variant: "destructive",
        duration: 3000,
      });
    } finally {
      setIsConfirmingTemplate(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold">Voice Agent Templates</h2>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Choose from our pre-built templates to quickly create professional voice agents. 
          Each template includes optimized prompts, sample questions, and best practices.
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 justify-center">
        {categories.map((category) => (
          <Button
            key={category.id}
            variant={selectedCategory === category.id ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(category.id)}
            className="flex items-center gap-2"
          >
            {renderIcon(category.icon, "h-4 w-4")}
            {category.name}
          </Button>
        ))}
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedTemplates.map((template) => (
          <Card 
            key={template.id} 
            className={`cursor-pointer transition-all hover:shadow-lg ${
              selectedTemplate?.id === template.id ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => onTemplateSelect(template)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    {renderIcon(template.icon)}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {template.category}
                    </CardDescription>
                  </div>
                </div>
                <Badge className={getDifficultyColor(template.difficulty)}>
                  {template.difficulty}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {template.description}
              </p>
              
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {template.estimatedTime}
              </div>
              
              <div className="flex flex-wrap gap-1">
                {template.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {template.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{template.tags.length - 3}
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  {template.popularity}% popular
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleConfigureTemplate(template);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Settings className="h-3 w-3" />
                    Configure
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTestTemplate(template);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Zap className="h-3 w-3" />
                    Test
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleIntegrateTemplate(template);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Shield className="h-3 w-3" />
                    Integrate
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShowAnalytics();
                    }}
                    className="flex items-center gap-1"
                  >
                    <Info className="h-3 w-3" />
                    Analytics
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShareTemplate(template);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Share2 className="h-3 w-3" />
                    Share
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShowMarketplace();
                    }}
                    className="flex items-center gap-1"
                  >
                    <ShoppingCart className="h-3 w-3" />
                    Marketplace
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShowAdvancedFeatures(template);
                    }}
                    className="flex items-center gap-1"
                  >
                    <Code className="h-3 w-3" />
                    Advanced
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Selected Template Summary */}
      {selectedTemplate && (
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Template Selected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  {renderIcon(selectedTemplate.icon)}
                </div>
                <div>
                  <h3 className="font-semibold">{selectedTemplate.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedTemplate.description}
                  </p>
                </div>
              </div>
              <Button 
                variant={templateConfirmed ? "default" : "outline"}
                onClick={handleUseTemplate}
                disabled={isConfirmingTemplate}
                className={templateConfirmed ? "bg-green-600 hover:bg-green-700" : ""}
              >
                {isConfirmingTemplate ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-2" />
                    Confirming...
                  </>
                ) : templateConfirmed ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Template Ready
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Use This Template
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Templates Found */}
      {sortedTemplates.length === 0 && (
        <div className="text-center py-12">
          <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-4">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No templates found</h3>
          <p className="text-muted-foreground">
            Try selecting a different category or check back later for new templates.
          </p>
        </div>
      )}

      {/* Template Configuration Dialog */}
      {templateToConfigure && (
        <TemplateConfiguration
          template={templateToConfigure}
          onConfigurationComplete={handleConfigurationComplete}
          onClose={() => {
            setTemplateToConfigure(null);
          }}
        />
      )}

      {/* Template Testing Dialog */}
      {templateToTest && (
        <TemplateTesting
          template={templateToTest}
          onClose={() => {
            setTemplateToTest(null);
          }}
          onSave={(testResults) => {
            console.log('Test results saved:', testResults);
            toast({
              title: "Test Results Saved",
              description: "Template test results have been saved successfully",
            });
          }}
        />
      )}

      {/* Template Integration Configuration Dialog */}
      {templateToIntegrate && (
        <TemplateIntegrationConfig
          templateId={templateToIntegrate.id}
          initialConfig={templateToIntegrate.integrations}
          onSave={(config) => {
            console.log('Integration config saved:', config);
            toast({
              title: "Integration Configuration Saved",
              description: "Template integration configuration has been saved successfully",
            });
            // Update the template with new integration config
            const updatedTemplate = {
              ...templateToIntegrate,
              integrations: config
            };
            // Here you would typically save this to the database
            setTemplateToIntegrate(null);
          }}
          onClose={() => {
            setTemplateToIntegrate(null);
          }}
        />
      )}

      {/* Template Analytics Dialog */}
      {showAnalytics && (
        <TemplateAnalytics
          templates={templates}
          onClose={() => {
            setShowAnalytics(false);
          }}
        />
      )}

      {/* Template Sharing Dialog */}
      {templateToShare && (
        <TemplateSharing
          template={templateToShare}
          onClose={() => {
            setTemplateToShare(null);
          }}
        />
      )}

      {/* Template Marketplace Dialog */}
      {showMarketplace && (
        <TemplateMarketplace
          onClose={() => {
            setShowMarketplace(false);
          }}
        />
      )}

      {/* Advanced Template Features Dialog */}
      {showAdvancedFeatures && templateForAdvancedFeatures && (
        <AdvancedTemplateFeatures
          template={templateForAdvancedFeatures}
          onClose={() => {
            setShowAdvancedFeatures(false);
            setTemplateForAdvancedFeatures(null);
          }}
          onSave={(advancedFeatures) => {
            console.log('Advanced features saved:', advancedFeatures);
            toast({
              title: "Advanced Features Saved",
              description: "Template advanced features have been saved successfully",
            });
            setShowAdvancedFeatures(false);
            setTemplateForAdvancedFeatures(null);
          }}
        />
      )}
    </div>
  );
};

export default VoiceAgentTemplates;
