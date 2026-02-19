import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { 
  Edit, 
  Save, 
  Copy, 
  Trash2, 
  Heart, 
  HeartOff, 
  Eye, 
  EyeOff,
  Plus,
  Search,
  Filter,
  Star,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';

export interface CustomTemplate {
  id: string;
  user_id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  system_prompt: string;
  sample_questions: string[];
  use_cases: string[];
  tags: string[];
  features: string[];
  is_public: boolean;
  is_favorite: boolean;
  usage_count: number;
  success_rate: number;
  parent_template_id?: string;
  version: number;
  created_at: string;
  updated_at: string;
  // Integration configuration fields (same as VoiceTemplate)
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

interface TemplateCustomizationProps {
  selectedTemplate?: VoiceTemplate | null;
  onTemplateSelect: (template: VoiceTemplate | CustomTemplate) => void;
  onClose: () => void;
}

const TemplateCustomization: React.FC<TemplateCustomizationProps> = ({
  selectedTemplate,
  onTemplateSelect,
  onClose
}) => {
  const { toast } = useToast();
  const [customTemplates, setCustomTemplates] = useState<CustomTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showPublicOnly, setShowPublicOnly] = useState(false);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<CustomTemplate | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<CustomTemplate | null>(null);

  // Form state for creating/editing templates
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    difficulty: 'Beginner' as 'Beginner' | 'Intermediate' | 'Advanced',
    system_prompt: '',
    sample_questions: [] as string[],
    use_cases: [] as string[],
    tags: [] as string[],
    features: [] as string[],
    is_public: false
  });

  const [newQuestion, setNewQuestion] = useState('');
  const [newUseCase, setNewUseCase] = useState('');
  const [newTag, setNewTag] = useState('');
  const [newFeature, setNewFeature] = useState('');

  const categories = [
    { id: 'all', name: 'All Categories' },
    { id: 'Customer Service', name: 'Customer Service' },
    { id: 'Sales', name: 'Sales' },
    { id: 'Scheduling', name: 'Scheduling' },
    { id: 'Research', name: 'Research' },
    { id: 'Insurance', name: 'Insurance' },
    { id: 'Real Estate', name: 'Real Estate' },
    { id: 'Healthcare', name: 'Healthcare' },
    { id: 'Banking', name: 'Banking' }
  ];

  useEffect(() => {
    loadCustomTemplates();
  }, []);

  useEffect(() => {
    if (selectedTemplate) {
      initializeFormFromTemplate(selectedTemplate);
    }
  }, [selectedTemplate]);

  const loadCustomTemplates = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('manage-custom-templates', {
        body: { action: 'list' }
      });

      if (error) throw error;
      setCustomTemplates(data.templates || []);
    } catch (error: any) {
      console.error('Failed to load custom templates:', error);
      toast({
        title: "Error",
        description: "Failed to load custom templates",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const initializeFormFromTemplate = (template: VoiceTemplate | CustomTemplate) => {
    setFormData({
      name: template.name,
      description: template.description,
      category: template.category,
      difficulty: template.difficulty,
      system_prompt: 'systemPrompt' in template ? template.systemPrompt : template.system_prompt,
      sample_questions: 'sampleQuestions' in template ? template.sampleQuestions : template.sample_questions,
      use_cases: 'useCases' in template ? template.useCases : template.use_cases,
      tags: template.tags,
      features: template.features,
      is_public: false
    });
  };

  const saveCustomTemplate = async () => {
    if (!formData.name || !formData.category || !formData.system_prompt) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    setSaving(true);
    try {
      const action = editingTemplate ? 'update' : 'create';
      const body = editingTemplate 
        ? { action, id: editingTemplate.id, ...formData }
        : { action, ...formData };

      const { data, error } = await supabase.functions.invoke('manage-custom-templates', {
        body
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: editingTemplate ? "Template updated successfully" : "Template saved successfully"
      });

      setEditingTemplate(null);
      loadCustomTemplates();
      onClose();
    } catch (error: any) {
      console.error('Failed to save template:', error);
      toast({
        title: "Error",
        description: "Failed to save template",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const duplicateTemplate = async (template: CustomTemplate) => {
    try {
      const { data, error } = await supabase.functions.invoke('manage-custom-templates', {
        body: { 
          action: 'duplicate', 
          id: template.id,
          new_name: `${template.name} (Copy)`
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Template duplicated successfully"
      });

      loadCustomTemplates();
    } catch (error: any) {
      console.error('Failed to duplicate template:', error);
      toast({
        title: "Error",
        description: "Failed to duplicate template",
        variant: "destructive"
      });
    }
  };

  const deleteTemplate = async (template: CustomTemplate) => {
    if (!confirm(`Are you sure you want to delete "${template.name}"?`)) return;

    try {
      const { error } = await supabase.functions.invoke('manage-custom-templates', {
        body: { action: 'delete', id: template.id }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Template deleted successfully"
      });

      loadCustomTemplates();
    } catch (error: any) {
      console.error('Failed to delete template:', error);
      toast({
        title: "Error",
        description: "Failed to delete template",
        variant: "destructive"
      });
    }
  };

  const toggleFavorite = async (template: CustomTemplate) => {
    try {
      const { data, error } = await supabase.functions.invoke('manage-custom-templates', {
        body: { action: 'toggle_favorite', id: template.id }
      });

      if (error) throw error;

      loadCustomTemplates();
    } catch (error: any) {
      console.error('Failed to toggle favorite:', error);
      toast({
        title: "Error",
        description: "Failed to update favorite status",
        variant: "destructive"
      });
    }
  };

  const addArrayItem = (field: keyof typeof formData, value: string) => {
    if (!value.trim()) return;
    
    setFormData(prev => ({
      ...prev,
      [field]: [...(prev[field] as string[]), value.trim()]
    }));

    // Clear the input
    switch (field) {
      case 'sample_questions':
        setNewQuestion('');
        break;
      case 'use_cases':
        setNewUseCase('');
        break;
      case 'tags':
        setNewTag('');
        break;
      case 'features':
        setNewFeature('');
        break;
    }
  };

  const removeArrayItem = (field: keyof typeof formData, index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== index)
    }));
  };

  const filteredTemplates = customTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesPublic = !showPublicOnly || template.is_public;
    const matchesFavorites = !showFavoritesOnly || template.is_favorite;
    
    return matchesSearch && matchesCategory && matchesPublic && matchesFavorites;
  });

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return 'bg-green-100 text-green-800';
      case 'Intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'Advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Template Customization</h2>
          <p className="text-muted-foreground">
            Create, edit, and manage your custom voice agent templates
          </p>
        </div>
        <Button onClick={onClose} variant="outline">
          Close
        </Button>
      </div>

      <Tabs defaultValue="create" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="create">Create/Edit</TabsTrigger>
          <TabsTrigger value="library">My Library</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Template Details</CardTitle>
              <CardDescription>
                {editingTemplate ? 'Edit your custom template' : 'Create a new custom template'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Template Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter template name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.slice(1).map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this template is for"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <Select
                    value={formData.difficulty}
                    onValueChange={(value: 'Beginner' | 'Intermediate' | 'Advanced') => 
                      setFormData(prev => ({ ...prev, difficulty: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Beginner">Beginner</SelectItem>
                      <SelectItem value="Intermediate">Intermediate</SelectItem>
                      <SelectItem value="Advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="is_public">Visibility</Label>
                  <Select
                    value={formData.is_public ? 'public' : 'private'}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, is_public: value === 'public' }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="private">Private (Only you)</SelectItem>
                      <SelectItem value="public">Public (Share with community)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="system_prompt">System Prompt *</Label>
                <Textarea
                  id="system_prompt"
                  value={formData.system_prompt}
                  onChange={(e) => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                  placeholder="Enter the system prompt for your voice agent"
                  rows={8}
                  className="font-mono text-sm"
                />
              </div>

              {/* Sample Questions */}
              <div className="space-y-2">
                <Label>Sample Questions</Label>
                <div className="flex gap-2">
                  <Input
                    value={newQuestion}
                    onChange={(e) => setNewQuestion(e.target.value)}
                    placeholder="Add a sample question"
                    onKeyPress={(e) => e.key === 'Enter' && addArrayItem('sample_questions', newQuestion)}
                  />
                  <Button
                    size="sm"
                    onClick={() => addArrayItem('sample_questions', newQuestion)}
                    disabled={!newQuestion.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.sample_questions.map((question, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      {question}
                      <button
                        onClick={() => removeArrayItem('sample_questions', index)}
                        className="ml-1 hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Use Cases */}
              <div className="space-y-2">
                <Label>Use Cases</Label>
                <div className="flex gap-2">
                  <Input
                    value={newUseCase}
                    onChange={(e) => setNewUseCase(e.target.value)}
                    placeholder="Add a use case"
                    onKeyPress={(e) => e.key === 'Enter' && addArrayItem('use_cases', newUseCase)}
                  />
                  <Button
                    size="sm"
                    onClick={() => addArrayItem('use_cases', newUseCase)}
                    disabled={!newUseCase.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.use_cases.map((useCase, index) => (
                    <Badge key={index} variant="outline" className="flex items-center gap-1">
                      {useCase}
                      <button
                        onClick={() => removeArrayItem('use_cases', index)}
                        className="ml-1 hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    onKeyPress={(e) => e.key === 'Enter' && addArrayItem('tags', newTag)}
                  />
                  <Button
                    size="sm"
                    onClick={() => addArrayItem('tags', newTag)}
                    disabled={!newTag.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="flex items-center gap-1">
                      #{tag}
                      <button
                        onClick={() => removeArrayItem('tags', index)}
                        className="ml-1 hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Features */}
              <div className="space-y-2">
                <Label>Features</Label>
                <div className="flex gap-2">
                  <Input
                    value={newFeature}
                    onChange={(e) => setNewFeature(e.target.value)}
                    placeholder="Add a feature"
                    onKeyPress={(e) => e.key === 'Enter' && addArrayItem('features', newFeature)}
                  />
                  <Button
                    size="sm"
                    onClick={() => addArrayItem('features', newFeature)}
                    disabled={!newFeature.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.features.map((feature, index) => (
                    <Badge key={index} variant="outline" className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {feature}
                      <button
                        onClick={() => removeArrayItem('features', index)}
                        className="ml-1 hover:text-destructive"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={saveCustomTemplate}
                  disabled={saving}
                  className="flex items-center gap-2"
                >
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {editingTemplate ? 'Update Template' : 'Save Template'}
                </Button>
                {editingTemplate && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setEditingTemplate(null);
                      initializeFormFromTemplate(selectedTemplate!);
                    }}
                  >
                    Cancel Edit
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="library" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>My Template Library</CardTitle>
              <CardDescription>
                Manage your custom templates and favorites
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Search and Filters */}
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                    <Input
                      placeholder="Search templates..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    variant={showPublicOnly ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowPublicOnly(!showPublicOnly)}
                  >
                    <Users className="h-4 w-4 mr-1" />
                    Public
                  </Button>
                  <Button
                    variant={showFavoritesOnly ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                  >
                    <Heart className="h-4 w-4 mr-1" />
                    Favorites
                  </Button>
                </div>
              </div>

              {/* Templates Grid */}
              {loading ? (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p>Loading templates...</p>
                </div>
              ) : filteredTemplates.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No templates found</p>
                  <p className="text-sm">Create your first custom template to get started</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredTemplates.map((template) => (
                    <Card key={template.id} className="relative">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg">{template.name}</CardTitle>
                            <CardDescription className="mt-1">
                              {template.description}
                            </CardDescription>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleFavorite(template)}
                            >
                              {template.is_favorite ? (
                                <Heart className="h-4 w-4 text-red-500 fill-current" />
                              ) : (
                                <Heart className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setPreviewTemplate(template)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-3">
                          <div className="flex items-center gap-2">
                            <Badge className={getDifficultyColor(template.difficulty)}>
                              {template.difficulty}
                            </Badge>
                            <Badge variant="outline">
                              {template.category}
                            </Badge>
                            {template.is_public && (
                              <Badge variant="secondary">
                                <Users className="h-3 w-3 mr-1" />
                                Public
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Star className="h-3 w-3" />
                              {template.usage_count} uses
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              v{template.version}
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-1">
                            {template.tags.slice(0, 3).map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                #{tag}
                              </Badge>
                            ))}
                            {template.tags.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{template.tags.length - 3} more
                              </Badge>
                            )}
                          </div>

                          <div className="flex gap-2 pt-2">
                            <Button
                              size="sm"
                              onClick={() => {
                                setEditingTemplate(template);
                                setFormData({
                                  name: template.name,
                                  description: template.description,
                                  category: template.category,
                                  difficulty: template.difficulty,
                                  system_prompt: template.system_prompt,
                                  sample_questions: template.sample_questions,
                                  use_cases: template.use_cases,
                                  tags: template.tags,
                                  features: template.features,
                                  is_public: template.is_public
                                });
                              }}
                            >
                              <Edit className="h-3 w-3 mr-1" />
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => duplicateTemplate(template)}
                            >
                              <Copy className="h-3 w-3 mr-1" />
                              Duplicate
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => onTemplateSelect(template)}
                            >
                              Use
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteTemplate(template)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Template Preview</CardTitle>
              <CardDescription>
                Preview your template before using it
              </CardDescription>
            </CardHeader>
            <CardContent>
              {previewTemplate ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold">{previewTemplate.name}</h3>
                      <p className="text-muted-foreground">{previewTemplate.description}</p>
                    </div>
                    <Button onClick={() => onTemplateSelect(previewTemplate)}>
                      Use This Template
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">Details</h4>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge className={getDifficultyColor(previewTemplate.difficulty)}>
                              {previewTemplate.difficulty}
                            </Badge>
                            <Badge variant="outline">{previewTemplate.category}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Created: {new Date(previewTemplate.created_at).toLocaleDateString()}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Version: {previewTemplate.version}
                          </div>
                        </div>
                      </div>

                      {previewTemplate.sample_questions.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Sample Questions</h4>
                          <ul className="space-y-1">
                            {previewTemplate.sample_questions.map((question, index) => (
                              <li key={index} className="text-sm">• {question}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {previewTemplate.use_cases.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Use Cases</h4>
                          <div className="flex flex-wrap gap-1">
                            {previewTemplate.use_cases.map((useCase, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {useCase}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2">System Prompt</h4>
                        <div className="bg-muted p-4 rounded-lg">
                          <pre className="text-sm whitespace-pre-wrap font-mono">
                            {previewTemplate.system_prompt}
                          </pre>
                        </div>
                      </div>

                      {previewTemplate.features.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Features</h4>
                          <div className="flex flex-wrap gap-1">
                            {previewTemplate.features.map((feature, index) => (
                              <Badge key={index} variant="secondary" className="text-xs">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {feature}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {previewTemplate.tags.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Tags</h4>
                          <div className="flex flex-wrap gap-1">
                            {previewTemplate.tags.map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                #{tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a template to preview</p>
                  <p className="text-sm">Go to the Library tab to select a template</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TemplateCustomization;
