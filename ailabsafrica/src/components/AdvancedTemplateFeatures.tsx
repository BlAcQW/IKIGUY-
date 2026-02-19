import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { CustomTemplate } from './TemplateCustomization';
import { 
  Code,
  Zap,
  GitBranch,
  Variable,
  Function,
  Settings,
  Play,
  Pause,
  Stop,
  Save,
  Loader2,
  CheckCircle,
  AlertCircle,
  Plus,
  Minus,
  Copy,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  Download,
  Upload,
  Trash2,
  Edit3,
  Search,
  Filter,
  SortAsc,
  SortDesc,
  MoreHorizontal,
  FileText,
  Database,
  Link,
  Unlink,
  Lock,
  Unlock,
  Shield,
  Globe,
  User,
  Users,
  Calendar,
  Clock,
  Tag,
  Hash,
  Star,
  Heart,
  Bookmark,
  Share2,
  ExternalLink,
  Settings as SettingsIcon,
  Palette,
  Layers,
  GitMerge,
  GitPullRequest,
  GitCommit,
  GitCompare,
  GitBranch as GitBranchIcon,
  GitFork,
  GitPullRequestClosed,
  GitPullRequestDraft,
  GitPullRequestOpen,
  GitPullRequestClosed as GitPullRequestClosedIcon,
  GitPullRequestDraft as GitPullRequestDraftIcon,
  GitPullRequestOpen as GitPullRequestOpenIcon,
  GitPullRequest as GitPullRequestIcon,
  GitCompare as GitCompareIcon,
  GitFork as GitForkIcon,
  GitCommit as GitCommitIcon,
  GitBranchIcon as GitBranchIcon2,
  GitPullRequestIcon as GitPullRequestIcon2,
  GitCompareIcon as GitCompareIcon2,
  GitForkIcon as GitForkIcon2,
  GitCommitIcon as GitCommitIcon2,
  GitBranchIcon2 as GitBranchIcon3,
  GitPullRequestIcon2 as GitPullRequestIcon3,
  GitCompareIcon2 as GitCompareIcon3,
  GitForkIcon2 as GitForkIcon3,
  GitCommitIcon2 as GitCommitIcon3
} from 'lucide-react';

interface ConditionalLogic {
  id: string;
  condition: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'exists' | 'not_exists';
  value: string;
  action: 'show' | 'hide' | 'modify' | 'redirect' | 'custom';
  target: string;
  priority: number;
  isActive: boolean;
}

interface DynamicContent {
  id: string;
  variable: string;
  source: 'user_input' | 'system_data' | 'external_api' | 'database' | 'calculated';
  defaultValue: string;
  validation: string;
  transform: string;
  isRequired: boolean;
  isSensitive: boolean;
}

interface TemplateInheritance {
  id: string;
  parentTemplateId: string;
  parentTemplateName: string;
  inheritanceType: 'full' | 'partial' | 'composition';
  overrides: Record<string, any>;
  extensions: Record<string, any>;
  conflicts: string[];
  isActive: boolean;
}

interface AdvancedTemplateFeaturesProps {
  template: VoiceTemplate | CustomTemplate;
  onClose: () => void;
  onSave?: (advancedFeatures: {
    conditionalLogic: ConditionalLogic[];
    dynamicContent: DynamicContent[];
    inheritance: TemplateInheritance[];
  }) => void;
}

const AdvancedTemplateFeatures: React.FC<AdvancedTemplateFeaturesProps> = ({ template, onClose, onSave }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('conditional');
  const [conditionalLogic, setConditionalLogic] = useState<ConditionalLogic[]>([]);
  const [dynamicContent, setDynamicContent] = useState<DynamicContent[]>([]);
  const [inheritance, setInheritance] = useState<TemplateInheritance[]>([]);
  const [loading, setLoading] = useState(false);
  const [showConditionalDialog, setShowConditionalDialog] = useState(false);
  const [showDynamicDialog, setShowDynamicDialog] = useState(false);
  const [showInheritanceDialog, setShowInheritanceDialog] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const { toast } = useToast();

  // Generate mock data
  useEffect(() => {
    generateMockData();
  }, []);

  const generateMockData = () => {
    const mockConditionalLogic: ConditionalLogic[] = [
      {
        id: '1',
        condition: 'user_type',
        operator: 'equals',
        value: 'premium',
        action: 'show',
        target: 'advanced_features',
        priority: 1,
        isActive: true
      },
      {
        id: '2',
        condition: 'conversation_length',
        operator: 'greater_than',
        value: '10',
        action: 'modify',
        target: 'response_style',
        priority: 2,
        isActive: true
      }
    ];

    const mockDynamicContent: DynamicContent[] = [
      {
        id: '1',
        variable: 'user_name',
        source: 'user_input',
        defaultValue: 'Guest',
        validation: 'string',
        transform: 'capitalize',
        isRequired: false,
        isSensitive: false
      },
      {
        id: '2',
        variable: 'current_time',
        source: 'system_data',
        defaultValue: '',
        validation: 'datetime',
        transform: 'format_12h',
        isRequired: true,
        isSensitive: false
      }
    ];

    const mockInheritance: TemplateInheritance[] = [
      {
        id: '1',
        parentTemplateId: 'parent-1',
        parentTemplateName: 'Base Customer Service Template',
        inheritanceType: 'partial',
        overrides: {
          systemPrompt: 'Custom system prompt override',
          sampleQuestions: ['Custom question 1', 'Custom question 2']
        },
        extensions: {
          additionalFeatures: ['feature1', 'feature2'],
          customIntegrations: ['integration1']
        },
        conflicts: [],
        isActive: true
      }
    ];

    setConditionalLogic(mockConditionalLogic);
    setDynamicContent(mockDynamicContent);
    setInheritance(mockInheritance);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Simulate save process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Advanced Features Saved",
        description: "Template advanced features have been updated successfully",
      });

      if (onSave) {
        onSave({
          conditionalLogic,
          dynamicContent,
          inheritance
        });
      }
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Failed to save advanced features. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const renderConditionalLogicTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Conditional Logic</h3>
        <Button
          onClick={() => {
            setEditingItem(null);
            setShowConditionalDialog(true);
          }}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Condition
        </Button>
      </div>

      <div className="space-y-4">
        {conditionalLogic.map((condition) => (
          <Card key={condition.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{condition.condition}</h4>
                    <Badge variant={condition.isActive ? "default" : "secondary"}>
                      {condition.isActive ? "Active" : "Inactive"}
                    </Badge>
                    <Badge variant="outline">Priority: {condition.priority}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {condition.condition} {condition.operator} "{condition.value}" → {condition.action} {condition.target}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingItem(condition);
                      setShowConditionalDialog(true);
                    }}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setConditionalLogic(prev => 
                        prev.map(c => 
                          c.id === condition.id 
                            ? { ...c, isActive: !c.isActive }
                            : c
                        )
                      );
                    }}
                  >
                    {condition.isActive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderDynamicContentTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Dynamic Content</h3>
        <Button
          onClick={() => {
            setEditingItem(null);
            setShowDynamicDialog(true);
          }}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Variable
        </Button>
      </div>

      <div className="space-y-4">
        {dynamicContent.map((content) => (
          <Card key={content.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">${content.variable}</h4>
                    <Badge variant="outline">{content.source}</Badge>
                    {content.isRequired && <Badge className="bg-red-100 text-red-800">Required</Badge>}
                    {content.isSensitive && <Badge className="bg-yellow-100 text-yellow-800">Sensitive</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Default: "{content.defaultValue}" | Validation: {content.validation} | Transform: {content.transform}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingItem(content);
                      setShowDynamicDialog(true);
                    }}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderInheritanceTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Template Inheritance</h3>
        <Button
          onClick={() => {
            setEditingItem(null);
            setShowInheritanceDialog(true);
          }}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Inheritance
        </Button>
      </div>

      <div className="space-y-4">
        {inheritance.map((inherit) => (
          <Card key={inherit.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{inherit.parentTemplateName}</h4>
                    <Badge variant={inherit.isActive ? "default" : "secondary"}>
                      {inherit.isActive ? "Active" : "Inactive"}
                    </Badge>
                    <Badge variant="outline">{inherit.inheritanceType}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {Object.keys(inherit.overrides).length} overrides, {Object.keys(inherit.extensions).length} extensions
                    {inherit.conflicts.length > 0 && `, ${inherit.conflicts.length} conflicts`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingItem(inherit);
                      setShowInheritanceDialog(true);
                    }}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInheritance(prev => 
                        prev.map(i => 
                          i.id === inherit.id 
                            ? { ...i, isActive: !i.isActive }
                            : i
                        )
                      );
                    }}
                  >
                    {inherit.isActive ? <Unlink className="h-4 w-4" /> : <Link className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Advanced Template Features
          </DialogTitle>
          <DialogDescription>
            Configure conditional logic, dynamic content, and template inheritance
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="conditional">Conditional Logic</TabsTrigger>
            <TabsTrigger value="dynamic">Dynamic Content</TabsTrigger>
            <TabsTrigger value="inheritance">Inheritance</TabsTrigger>
          </TabsList>

          <TabsContent value="conditional" className="space-y-6">
            {renderConditionalLogicTab()}
          </TabsContent>

          <TabsContent value="dynamic" className="space-y-6">
            {renderDynamicContentTab()}
          </TabsContent>

          <TabsContent value="inheritance" className="space-y-6">
            {renderInheritanceTab()}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AdvancedTemplateFeatures;
