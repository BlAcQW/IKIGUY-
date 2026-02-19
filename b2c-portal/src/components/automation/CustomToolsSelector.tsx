import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Search,
  Filter,
  Plus,
  Minus,
  Settings,
  Code,
  Globe,
  Shield,
  Database,
  MessageSquare,
  RefreshCw,
  BarChart3,
  Upload,
  Download,
  Eye,
  Edit,
  Trash2,
  AlertTriangle,
  LayoutGrid,
  List
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface CustomTool {
  id: string;
  name: string;
  client_id: string;
  industry: string;
  category: string;
  description: string;
  endpoint: string;
  method: string;
  schema: any;
  active: boolean;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  version?: string;
  tags?: string[];
  source?: string;
  analytics?: {
    execution_count: number;
    last_executed: string | null;
    average_response_time: number;
    error_count: number;
  };
}

interface ToolAnalytics {
  execution_count: number;
  last_executed: string | null;
  average_response_time: number;
  error_count: number;
}

interface ClientSummary {
  total_tools: number;
  active_tools: number;
  total_executions: number;
  total_errors: number;
  categories: string[];
  industries: string[];
  success_rate: number;
}

interface CustomToolsSelectorProps {
  selectedTools: CustomTool[];
  onToolsChange: (tools: CustomTool[]) => void;
  industry?: string;
  clientId?: string;
  className?: string;
  availableTools?: CustomTool[]; // Pre-loaded tools from parent to avoid duplicate fetching
  showAnalytics?: boolean; // Whether to show analytics UI
  maxHeight?: string; // Max height for scrollable area
}

const CustomToolsSelector: React.FC<CustomToolsSelectorProps> = ({
  selectedTools,
  onToolsChange,
  industry = "",
  clientId = "",
  className = "",
  availableTools: providedTools,
  showAnalytics = true,
  maxHeight = "600px"
}) => {
  const [availableTools, setAvailableTools] = useState<CustomTool[]>(providedTools || []);
  const [filteredTools, setFilteredTools] = useState<CustomTool[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedIndustry, setSelectedIndustry] = useState(industry || 'all');
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table'); // Default to table view
  const [clientSummary, setClientSummary] = useState<ClientSummary | null>(null);
  const [showRegistrationDialog, setShowRegistrationDialog] = useState(false);
  const [showAnalyticsDialog, setShowAnalyticsDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedTool, setSelectedTool] = useState<CustomTool | null>(null);
  const [selectedToolAnalytics, setSelectedToolAnalytics] = useState<{ tool: CustomTool; analytics: ToolAnalytics } | null>(null);
  const [newToolData, setNewToolData] = useState({
    name: '',
    description: '',
    category: 'utility',
    industry: 'general',
    code: '',
    schema: ''
  });
  const { toast } = useToast();

  const categories = [
    { value: 'all', label: 'All Categories', icon: Globe },
    { value: 'provider_search', label: 'Provider Search', icon: Search },
    { value: 'communication', label: 'Communication', icon: MessageSquare },
    { value: 'data', label: 'Data Processing', icon: Database },
    { value: 'security', label: 'Security', icon: Shield },
    { value: 'utility', label: 'Utility', icon: Settings }
  ];

  const industries = [
    { value: 'all', label: 'All Industries' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'finance', label: 'Finance' },
    { value: 'retail', label: 'Retail' },
    { value: 'general', label: 'General' }
  ];

  const loadCustomTools = async () => {
    // Skip loading if tools are provided by parent
    if (providedTools && providedTools.length > 0) {
      setAvailableTools(providedTools);
      return;
    }

    setIsLoading(true);
    try {
      const headers = await getAuthHeaders();

      // Use search endpoint for better functionality
      if (searchTerm) {
        const queryParams = new URLSearchParams();
        queryParams.append('query', searchTerm);
        if (clientId) queryParams.append('client_id', clientId);
        if (selectedIndustry && selectedIndustry !== 'all') {
          queryParams.append('industry', selectedIndustry);
        }
        if (selectedCategory && selectedCategory !== 'all') {
          queryParams.append('category', selectedCategory);
        }

        const response = await fetch(`${API_BASE_URL}/custom-tools/search?${queryParams}`, {
          headers: {
            'Content-Type': 'application/json',
            ...headers
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to search custom tools: ${response.statusText}`);
        }

        const data = await response.json();
        setAvailableTools(data.tools || []);
      } else {
        // Use regular endpoint for listing
        const queryParams = new URLSearchParams();
        if (clientId) queryParams.append('client_id', clientId);
        if (selectedIndustry && selectedIndustry !== 'all') {
          queryParams.append('industry', selectedIndustry);
        }

        const response = await fetch(`${API_BASE_URL}/custom-tools?${queryParams}`, {
          headers: {
            'Content-Type': 'application/json',
            ...headers
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to load custom tools: ${response.statusText}`);
        }

        const data = await response.json();
        setAvailableTools(data.tools || []);
      }

      // Load client summary if clientId is provided
      if (clientId) {
        await loadClientSummary();
      }

    } catch (error) {
      console.error('Failed to load custom tools:', error);
      toast({
        title: "Loading Failed",
        description: "Could not load custom tools. Please try again.",
        variant: "destructive"
      });
      setAvailableTools([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadClientSummary = async () => {
    if (!clientId) return;

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/summary/${clientId}`, {
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });

      if (response.ok) {
        const data = await response.json();
        setClientSummary(data.summary);
      }
    } catch (error) {
      console.error('Failed to load client summary:', error);
    }
  };

  const registerNewTool = async () => {
    try {
      const headers = await getAuthHeaders();

      let schema;
      try {
        schema = JSON.parse(newToolData.schema || '{}');
      } catch {
        schema = {
          type: "function",
          function: {
            name: newToolData.name,
            description: newToolData.description,
            parameters: {
              type: "object",
              properties: {},
              required: []
            }
          }
        };
      }

      const payload = {
        name: newToolData.name,
        description: newToolData.description,
        category: newToolData.category,
        industry: newToolData.industry,
        client_id: clientId || 'default',
        schema,
        code: newToolData.code || null
      };

      const response = await fetch(buildApiUrl('/custom-tools/db/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Failed to register tool: ${response.statusText}`);
      }

      const data = await response.json();
      toast({
        title: "Tool Registered",
        description: data.message
      });

      // Reset form and reload tools
      setNewToolData({
        name: '',
        description: '',
        category: 'utility',
        industry: 'general',
        code: '',
        schema: ''
      });
      setShowRegistrationDialog(false);
      await loadCustomTools();

    } catch (error) {
      console.error('Failed to register tool:', error);
      toast({
        title: "Registration Failed",
        description: "Could not register the tool. Please try again.",
        variant: "destructive"
      });
    }
  };

  const updateTool = async () => {
    if (!selectedTool) return;

    try {
      const headers = await getAuthHeaders();

      let schema;
      try {
        schema = JSON.parse(newToolData.schema || '{}');
      } catch {
        schema = {
          type: "function",
          function: {
            name: newToolData.name,
            description: newToolData.description,
            parameters: {
              type: "object",
              properties: {},
              required: []
            }
          }
        };
      }

      const updates = {
        name: newToolData.name,
        description: newToolData.description,
        category: newToolData.category,
        schema,
        metadata: { code: newToolData.code }
      };

      const response = await fetch(`${API_BASE_URL}/custom-tools/${selectedTool.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error(`Failed to update tool: ${response.statusText}`);
      }

      toast({
        title: "Tool Updated",
        description: `Tool "${newToolData.name}" has been updated successfully.`
      });

      // Reset form and reload tools
      setNewToolData({
        name: '',
        description: '',
        category: 'utility',
        industry: 'general',
        code: '',
        schema: ''
      });
      setShowEditDialog(false);
      setSelectedTool(null);
      await loadCustomTools();

    } catch (error) {
      console.error('Failed to update tool:', error);
      toast({
        title: "Update Failed",
        description: "Could not update the tool. Please try again.",
        variant: "destructive"
      });
    }
  };

  const deleteTool = async () => {
    if (!selectedTool) return;

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/${selectedTool.id}`, {
        method: 'DELETE',
        headers: headers
      });

      if (!response.ok) {
        throw new Error(`Failed to delete tool: ${response.statusText}`);
      }

      toast({
        title: "Tool Deleted",
        description: `Tool "${selectedTool.name}" has been deleted successfully.`
      });

      setShowDeleteDialog(false);
      setSelectedTool(null);
      await loadCustomTools();

    } catch (error) {
      console.error('Failed to delete tool:', error);
      toast({
        title: "Delete Failed",
        description: "Could not delete the tool. Please try again.",
        variant: "destructive"
      });
    }
  };

  const openEditDialog = (tool: CustomTool) => {
    setSelectedTool(tool);
    setNewToolData({
      name: tool.name,
      description: tool.description,
      category: tool.category,
      industry: tool.industry,
      code: tool.metadata?.code || '',
      schema: JSON.stringify(tool.schema, null, 2)
    });
    setShowEditDialog(true);
  };

  const openDeleteDialog = (tool: CustomTool) => {
    setSelectedTool(tool);
    setShowDeleteDialog(true);
  };

  const viewToolAnalytics = async (tool: CustomTool) => {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/analytics/${tool.id}`, {
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to load analytics: ${response.statusText}`);
      }

      const data = await response.json();
      setSelectedToolAnalytics({ tool, analytics: data.analytics });
      setShowAnalyticsDialog(true);

    } catch (error) {
      console.error('Failed to load analytics:', error);
      toast({
        title: "Analytics Failed",
        description: "Could not load tool analytics. Please try again.",
        variant: "destructive"
      });
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadCustomTools();
    }, searchTerm ? 500 : 0); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [clientId, selectedIndustry, searchTerm, selectedCategory]);

  useEffect(() => {
    // For basic filtering when not using search
    if (!searchTerm) {
      let filtered = [...availableTools];

      // Filter by category
      if (selectedCategory && selectedCategory !== 'all') {
        filtered = filtered.filter(tool => tool.category === selectedCategory);
      }

      setFilteredTools(filtered);
    } else {
      // Search results are already filtered by the API
      setFilteredTools(availableTools);
    }
  }, [availableTools, selectedCategory, searchTerm]);

  const handleToolToggle = (tool: CustomTool, isSelected: boolean) => {
    let updatedTools: CustomTool[];

    if (isSelected) {
      // Add tool if not already selected
      if (!selectedTools.find(t => t.id === tool.id)) {
        updatedTools = [...selectedTools, tool];
      } else {
        updatedTools = selectedTools;
      }
    } else {
      // Remove tool
      updatedTools = selectedTools.filter(t => t.id !== tool.id);
    }

    onToolsChange(updatedTools);
  };

  const isToolSelected = (toolId: string) => {
    return selectedTools.some(tool => tool.id === toolId);
  };

  const getCategoryIcon = (category: string) => {
    const categoryData = categories.find(cat => cat.value === category);
    const IconComponent = categoryData?.icon || Settings;
    return <IconComponent className="h-4 w-4" />;
  };

  const initializePremierHealthTools = async () => {
    setIsLoading(true);
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(buildApiUrl('/custom-tools/init/premier-health'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize Premier Health tools: ${response.statusText}`);
      }

      const data = await response.json();
      toast({
        title: "Tools Initialized",
        description: data.message
      });

      // Reload tools
      await loadCustomTools();

    } catch (error) {
      console.error('Failed to initialize Premier Health tools:', error);
      toast({
        title: "Initialization Failed",
        description: "Could not initialize Premier Health tools. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Custom Tools Selection
              </CardTitle>
              <CardDescription>
                Select client-specific custom tools for your automation workflow
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadCustomTools}
                disabled={isLoading}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>

              <Dialog open={showRegistrationDialog} onOpenChange={setShowRegistrationDialog}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    Register Tool
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Register New Custom Tool</DialogTitle>
                    <DialogDescription>
                      Create a new custom tool that can be used in automation workflows
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="tool-name">Tool Name</Label>
                        <Input
                          id="tool-name"
                          value={newToolData.name}
                          onChange={(e) => setNewToolData(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="e.g., search_providers"
                        />
                      </div>
                      <div>
                        <Label htmlFor="tool-category">Category</Label>
                        <select
                          id="tool-category"
                          value={newToolData.category}
                          onChange={(e) => setNewToolData(prev => ({ ...prev, category: e.target.value }))}
                          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                        >
                          {categories.slice(1).map(category => (
                            <option key={category.value} value={category.value}>
                              {category.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="tool-description">Description</Label>
                      <Textarea
                        id="tool-description"
                        value={newToolData.description}
                        onChange={(e) => setNewToolData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe what this tool does..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <Label htmlFor="tool-code">Python Code (Optional)</Label>
                      <Textarea
                        id="tool-code"
                        value={newToolData.code}
                        onChange={(e) => setNewToolData(prev => ({ ...prev, code: e.target.value }))}
                        placeholder="# Python code for inline execution&#10;def main(parameters):&#10;    # Your tool logic here&#10;    result = {'status': 'success'}&#10;    return result"
                        rows={6}
                        className="font-mono text-sm"
                      />
                    </div>

                    <div>
                      <Label htmlFor="tool-schema">JSON Schema (Optional)</Label>
                      <Textarea
                        id="tool-schema"
                        value={newToolData.schema}
                        onChange={(e) => setNewToolData(prev => ({ ...prev, schema: e.target.value }))}
                        placeholder='{"type": "function", "function": {"name": "tool_name", "description": "Tool description", "parameters": {"type": "object", "properties": {}, "required": []}}}'
                        rows={4}
                        className="font-mono text-sm"
                      />
                    </div>

                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setShowRegistrationDialog(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={registerNewTool}
                        disabled={!newToolData.name || !newToolData.description}
                      >
                        Register Tool
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              {selectedIndustry === 'healthcare' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={initializePremierHealthTools}
                  disabled={isLoading}
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Init Premier Health
                </Button>
              )}

              {clientSummary && (
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  title={`${clientSummary.total_tools} tools, ${clientSummary.success_rate.toFixed(1)}% success rate`}
                >
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Search and Filters */}
          <div className="space-y-4 mb-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="search">Search Tools</Label>
                <div className="relative mt-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="search"
                    placeholder="Search by name, description, or category..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="w-48">
                <Label htmlFor="industry">Industry</Label>
                <select
                  id="industry"
                  value={selectedIndustry}
                  onChange={(e) => setSelectedIndustry(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
                >
                  {industries.map(industry => (
                    <option key={industry.value} value={industry.value}>
                      {industry.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Category Filter */}
            <div>
              <Label>Category</Label>
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2 mt-2">
                  {categories.map(category => (
                    <Button
                      key={category.value}
                      variant={selectedCategory === category.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedCategory(category.value)}
                      className="gap-2"
                    >
                      <category.icon className="h-4 w-4" />
                      {category.label}
                    </Button>
                  ))}
                </div>

                {/* View Mode Toggle */}
                <div className="flex border rounded-md">
                  <Button
                    variant={viewMode === 'table' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('table')}
                    className="rounded-r-none"
                  >
                    <List className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'card' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('card')}
                    className="rounded-l-none"
                  >
                    <LayoutGrid className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <Tabs defaultValue="available" className="space-y-4">
            <TabsList>
              <TabsTrigger value="available">
                Available Tools ({filteredTools.length})
              </TabsTrigger>
              <TabsTrigger value="selected">
                Selected Tools ({selectedTools.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="available" className="space-y-4">
              <div style={{ maxHeight: maxHeight, overflowY: 'auto' }}>
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                    Loading custom tools...
                  </div>
                ) : filteredTools.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {availableTools.length === 0 ? (
                    <>
                      <Code className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>No custom tools available</p>
                      <p className="text-sm">Register custom tools to get started</p>
                    </>
                  ) : (
                    <>
                      <Search className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                      <p>No tools match your search criteria</p>
                      <p className="text-sm">Try adjusting your filters</p>
                    </>
                  )}
                </div>
              ) : viewMode === 'table' ? (
                /* Table View */
                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12"></TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Industry</TableHead>
                        <TableHead>Method</TableHead>
                        <TableHead>Executions</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTools.map(tool => {
                        const isSelected = isToolSelected(tool.id);
                        return (
                          <TableRow
                            key={tool.id}
                            className={`cursor-pointer ${isSelected ? 'bg-blue-50' : 'hover:bg-accent/50'}`}
                            onClick={() => handleToolToggle(tool, !isSelected)}
                          >
                            <TableCell onClick={(e) => e.stopPropagation()}>
                              <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => handleToolToggle(tool, !!checked)}
                              />
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {getCategoryIcon(tool.category)}
                                <div>
                                  <div className="font-medium">{tool.name}</div>
                                  <div className="text-xs text-gray-600 line-clamp-1">
                                    {tool.description}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="secondary" className="text-xs">
                                {tool.category}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs">
                                {tool.industry}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {tool.method}
                            </TableCell>
                            <TableCell className="text-sm">
                              {tool.analytics?.execution_count || 0}
                            </TableCell>
                            <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                              <div className="flex justify-end gap-1">
                                {showAnalytics && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => viewToolAnalytics(tool)}
                                    title="View Analytics"
                                  >
                                    <BarChart3 className="h-4 w-4" />
                                  </Button>
                                )}
                                {tool.schema && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      // Show schema in a modal
                                      alert(JSON.stringify(tool.schema, null, 2));
                                    }}
                                    title="View Schema"
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openEditDialog(tool)}
                                  title="Edit Tool"
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openDeleteDialog(tool)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  title="Delete Tool"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </Card>
              ) : (
                /* Card View */
                <div className="grid gap-4">
                  {filteredTools.map(tool => {
                    const isSelected = isToolSelected(tool.id);
                    return (
                      <Card
                        key={tool.id}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
                        }`}
                        onClick={() => handleToolToggle(tool, !isSelected)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => handleToolToggle(tool, !!checked)}
                                className="mt-1"
                              />
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  {getCategoryIcon(tool.category)}
                                  <h4 className="font-medium">{tool.name}</h4>
                                  <Badge variant="outline" className="text-xs">
                                    {tool.client_id}
                                  </Badge>
                                  <Badge variant="secondary" className="text-xs">
                                    {tool.category}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-600 mb-2">
                                  {tool.description}
                                </p>
                                <div className="flex items-center gap-4 text-xs text-gray-500">
                                  <span>Industry: {tool.industry}</span>
                                  <span>Method: {tool.method}</span>
                                  <span>Endpoint: {tool.endpoint}</span>
                                  {tool.analytics && tool.analytics.execution_count > 0 && (
                                    <span className="text-blue-600">
                                      Executions: {tool.analytics.execution_count}
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 mt-2">
                                  {tool.version && (
                                    <Badge variant="outline" className="text-xs">
                                      v{tool.version}
                                    </Badge>
                                  )}
                                  {tool.source && (
                                    <Badge variant="outline" className="text-xs">
                                      {tool.source}
                                    </Badge>
                                  )}
                                  {tool.tags && tool.tags.length > 0 && (
                                    <div className="flex gap-1">
                                      {tool.tags.slice(0, 2).map(tag => (
                                        <Badge key={tag} variant="secondary" className="text-xs">
                                          {tag}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="flex flex-col gap-1">
                              {showAnalytics && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    viewToolAnalytics(tool);
                                  }}
                                  className="h-8 w-8 p-0"
                                  title="View Analytics"
                                >
                                  <BarChart3 className="h-4 w-4" />
                                </Button>
                              )}
                              {tool.schema && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 w-8 p-0"
                                  title="View Schema"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    // Could show schema in a modal
                                  }}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openEditDialog(tool);
                                }}
                                className="h-8 w-8 p-0"
                                title="Edit Tool"
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openDeleteDialog(tool);
                                }}
                                className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                                title="Delete Tool"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
              </div>
            </TabsContent>

            <TabsContent value="selected" className="space-y-4">
              {selectedTools.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No tools selected</p>
                  <p className="text-sm">Select tools from the Available Tools tab</p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {selectedTools.map(tool => (
                    <Card key={tool.id} className="border-blue-200 bg-blue-50">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                {getCategoryIcon(tool.category)}
                                <h4 className="font-medium">{tool.name}</h4>
                                <Badge variant="outline" className="text-xs">
                                  {tool.client_id}
                                </Badge>
                                <Badge variant="secondary" className="text-xs">
                                  {tool.category}
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600 mb-2">
                                {tool.description}
                              </p>
                              <div className="flex items-center gap-4 text-xs text-gray-500">
                                <span>Industry: {tool.industry}</span>
                                <span>Method: {tool.method}</span>
                                <span>Endpoint: {tool.endpoint}</span>
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToolToggle(tool, false)}
                            className="ml-2"
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>

          {/* Selected Tools Summary */}
          {selectedTools.length > 0 && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h5 className="font-medium mb-2">Selected Tools Summary</h5>
              <div className="flex flex-wrap gap-2">
                {selectedTools.map(tool => (
                  <Badge key={tool.id} variant="secondary" className="text-xs">
                    {tool.name}
                  </Badge>
                ))}
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {selectedTools.length} custom tool{selectedTools.length !== 1 ? 's' : ''} will be available in your automation workflow
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analytics Dialog */}
      <Dialog open={showAnalyticsDialog} onOpenChange={setShowAnalyticsDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Tool Analytics</DialogTitle>
            <DialogDescription>
              Performance metrics for {selectedToolAnalytics?.tool.name}
            </DialogDescription>
          </DialogHeader>
          {selectedToolAnalytics && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedToolAnalytics.analytics.execution_count}
                    </div>
                    <div className="text-sm text-gray-600">Total Executions</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedToolAnalytics.analytics.average_response_time.toFixed(2)}s
                    </div>
                    <div className="text-sm text-gray-600">Avg Response Time</div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-2xl font-bold text-red-600">
                      {selectedToolAnalytics.analytics.error_count}
                    </div>
                    <div className="text-sm text-gray-600">Total Errors</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedToolAnalytics.analytics.execution_count > 0
                        ? (((selectedToolAnalytics.analytics.execution_count - selectedToolAnalytics.analytics.error_count) / selectedToolAnalytics.analytics.execution_count) * 100).toFixed(1)
                        : 0}%
                    </div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </CardContent>
                </Card>
              </div>

              {selectedToolAnalytics.analytics.last_executed && (
                <div>
                  <Label>Last Executed</Label>
                  <div className="text-sm text-gray-600 mt-1">
                    {new Date(selectedToolAnalytics.analytics.last_executed).toLocaleString()}
                  </div>
                </div>
              )}

              <div className="flex justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowAnalyticsDialog(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Tool Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Tool: {selectedTool?.name}</DialogTitle>
            <DialogDescription>
              Update the tool configuration and settings
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-name">Tool Name</Label>
                <Input
                  id="edit-name"
                  value={newToolData.name}
                  onChange={(e) => setNewToolData({...newToolData, name: e.target.value})}
                  placeholder="Enter tool name"
                />
              </div>
              <div>
                <Label htmlFor="edit-category">Category</Label>
                <Select value={newToolData.category} onValueChange={(value) => setNewToolData({...newToolData, category: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="utility">Utility</SelectItem>
                    <SelectItem value="communication">Communication</SelectItem>
                    <SelectItem value="data">Data Processing</SelectItem>
                    <SelectItem value="provider_search">Provider Search</SelectItem>
                    <SelectItem value="security">Security</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                value={newToolData.description}
                onChange={(e) => setNewToolData({...newToolData, description: e.target.value})}
                placeholder="Describe what this tool does"
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="edit-schema">Schema (JSON)</Label>
              <Textarea
                id="edit-schema"
                value={newToolData.schema}
                onChange={(e) => setNewToolData({...newToolData, schema: e.target.value})}
                placeholder="Enter JSON schema"
                rows={8}
                className="font-mono text-sm"
              />
            </div>

            <div>
              <Label htmlFor="edit-code">Code (optional)</Label>
              <Textarea
                id="edit-code"
                value={newToolData.code}
                onChange={(e) => setNewToolData({...newToolData, code: e.target.value})}
                placeholder="Enter custom code for this tool"
                rows={6}
                className="font-mono text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={updateTool} disabled={!newToolData.name || !newToolData.description}>
              Update Tool
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Delete Tool
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedTool?.name}"? This action cannot be undone and will remove the tool from all configurations.
            </DialogDescription>
          </DialogHeader>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={deleteTool}>
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Tool
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CustomToolsSelector;