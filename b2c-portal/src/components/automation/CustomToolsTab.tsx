/**
 * Custom Tools Tab Component
 * Displays available custom business tools for N8N and VAPI agents
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Search,
  Settings,
  Play,
  Code,
  Copy,
  ExternalLink,
  Wrench,
  Heart,
  Activity,
  MessageSquare,
  Phone,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Server,
  Zap,
  Database,
  Mail,
  Shield,
  Globe,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  customToolsService,
  type CustomTool,
  type CustomToolsResponse
} from '@/services/CustomToolsService';

// Category icons mapping
const categoryIcons = {
  healthcare: Heart,
  communication: MessageSquare,
  database: Database,
  email: Mail,
  security: Shield,
  web: Globe,
  general: Wrench,
};

// Method color mapping
const methodColors = {
  GET: 'bg-green-100 text-green-800 border-green-200',
  POST: 'bg-blue-100 text-blue-800 border-blue-200',
  PUT: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  DELETE: 'bg-red-100 text-red-800 border-red-200',
  PATCH: 'bg-purple-100 text-purple-800 border-purple-200',
};

const CustomToolsTab: React.FC = () => {
  const { toast } = useToast();
  const [tools, setTools] = useState<CustomTool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedTool, setSelectedTool] = useState<CustomTool | null>(null);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [testParams, setTestParams] = useState<Record<string, any>>({});
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // Fetch custom tools
  const fetchCustomTools = async () => {
    setLoading(true);
    try {
      const response: CustomToolsResponse = await customToolsService.getCustomTools();
      setTools(response.tools);
      setCategories(response.categories);
    } catch (error) {
      console.error('Error fetching custom tools:', error);
      toast({
        title: "Failed to load custom tools",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomTools();
  }, []);

  // Filter tools
  const filteredTools = tools.filter(tool => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCategory = categoryFilter === 'all' || tool.category === categoryFilter;

    return matchesSearch && matchesCategory && tool.is_active;
  });

  // Test a tool
  const handleTestTool = async (tool: CustomTool) => {
    setTestLoading(true);
    try {
      const result = await customToolsService.executeCustomTool({
        tool_name: tool.name,
        parameters: testParams,
      });
      setTestResult(result);
      toast({
        title: "Tool executed successfully",
        description: `Execution completed in ${result.execution_time_ms}ms`,
      });
    } catch (error) {
      console.error('Error testing tool:', error);
      toast({
        title: "Tool execution failed",
        description: "Please check your parameters and try again.",
        variant: "destructive"
      });
    } finally {
      setTestLoading(false);
    }
  };

  // Copy configuration
  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast({
        title: "Copied to clipboard",
        description: `${type} configuration copied successfully.`,
      });
    });
  };

  // Get N8N configuration
  const getN8NConfig = (tool: CustomTool) => {
    return JSON.stringify(customToolsService.getN8NToolConfig(tool), null, 2);
  };

  // Get VAPI configuration
  const getVAPIConfig = (tool: CustomTool) => {
    return JSON.stringify(customToolsService.getVAPIToolConfig(tool), null, 2);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading custom tools...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Custom Tools</h2>
          <p className="text-gray-600">
            Business logic tools for your N8N workflows and VAPI voice agents
          </p>
        </div>
        <Badge variant="outline" className="gap-1">
          <Server className="h-3 w-3" />
          {tools.filter(t => t.is_active).length} Active Tools
        </Badge>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
          <Input
            placeholder="Search tools by name, description, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Tools Grid */}
      {filteredTools.length === 0 ? (
        <Card className="p-8 text-center">
          <div className="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
            <Wrench className="h-6 w-6 text-gray-600" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {tools.length === 0 ? 'No custom tools available' : 'No tools match your filters'}
          </h3>
          <p className="text-gray-600 mb-4">
            {tools.length === 0
              ? 'Custom tools will appear here when they are registered in the system.'
              : 'Try adjusting your search or filter criteria.'
            }
          </p>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTools.map((tool) => {
            const CategoryIcon = categoryIcons[tool.category as keyof typeof categoryIcons] || Wrench;
            const methodColor = methodColors[tool.method as keyof typeof methodColors] || 'bg-gray-100 text-gray-800 border-gray-200';

            return (
              <Card key={tool.name} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <CategoryIcon className="h-5 w-5 text-indigo-600" />
                      <div>
                        <CardTitle className="text-lg">{tool.name.replace(/^healthcare_/, '').replace(/_/g, ' ')}</CardTitle>
                        <CardDescription className="mt-1">
                          {tool.description}
                        </CardDescription>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className={methodColor}>
                      {tool.method}
                    </Badge>
                    <Badge variant="outline">
                      {tool.category}
                    </Badge>
                    {tool.tags.slice(0, 2).map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {tool.tags.length > 2 && (
                      <Badge variant="secondary" className="text-xs">
                        +{tool.tags.length - 2}
                      </Badge>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="text-sm">
                    <div className="font-medium mb-1">Endpoint:</div>
                    <code className="text-xs bg-muted p-1 rounded break-all">
                      {tool.endpoint}
                    </code>
                  </div>

                  <Accordion type="single" collapsible className="w-full">
                    <AccordionItem value="details">
                      <AccordionTrigger className="text-sm">
                        View Details
                      </AccordionTrigger>
                      <AccordionContent className="space-y-3">
                        <div>
                          <div className="font-medium text-xs mb-1">Required Parameters:</div>
                          <div className="text-xs bg-muted p-2 rounded">
                            {tool.parameters_schema.required?.length ? (
                              <ul className="list-disc list-inside space-y-1">
                                {tool.parameters_schema.required.map((param) => (
                                  <li key={param}>{param}</li>
                                ))}
                              </ul>
                            ) : (
                              <span className="text-gray-600">No required parameters</span>
                            )}
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button size="sm" variant="outline" className="gap-1">
                                <Code className="h-3 w-3" />
                                N8N Config
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>N8N Configuration</DialogTitle>
                                <DialogDescription>
                                  Copy this configuration to use in your N8N workflow
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4">
                                <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-96">
                                  {getN8NConfig(tool)}
                                </pre>
                                <Button
                                  onClick={() => copyToClipboard(getN8NConfig(tool), 'N8N')}
                                  className="gap-2"
                                >
                                  <Copy className="h-4 w-4" />
                                  Copy Configuration
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>

                          <Dialog>
                            <DialogTrigger asChild>
                              <Button size="sm" variant="outline" className="gap-1">
                                <Zap className="h-3 w-3" />
                                VAPI Config
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>VAPI Configuration</DialogTitle>
                                <DialogDescription>
                                  Copy this configuration to use in your VAPI voice agent
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4">
                                <pre className="bg-muted p-4 rounded text-xs overflow-auto max-h-96">
                                  {getVAPIConfig(tool)}
                                </pre>
                                <Button
                                  onClick={() => copyToClipboard(getVAPIConfig(tool), 'VAPI')}
                                  className="gap-2"
                                >
                                  <Copy className="h-4 w-4" />
                                  Copy Configuration
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>

                        {/* Test Tool (Healthcare tools only for now) */}
                        {tool.category === 'healthcare' && (
                          <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
                            <DialogTrigger asChild>
                              <Button
                                size="sm"
                                className="gap-1 w-full"
                                onClick={() => {
                                  setSelectedTool(tool);
                                  setTestParams({});
                                  setTestResult(null);
                                }}
                              >
                                <Play className="h-3 w-3" />
                                Test Tool
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Test {selectedTool?.name}</DialogTitle>
                                <DialogDescription>
                                  Test this tool with sample parameters
                                </DialogDescription>
                              </DialogHeader>

                              {selectedTool && (
                                <div className="space-y-4">
                                  {/* Test parameters would go here */}
                                  <div className="text-sm">
                                    <p className="mb-2">This tool can be tested directly from your workflows once configured.</p>
                                    <div className="bg-muted p-3 rounded">
                                      <div className="font-medium">Example usage:</div>
                                      <div className="text-xs mt-1">
                                        Call this endpoint from N8N HTTP Request node or VAPI function call
                                      </div>
                                    </div>
                                  </div>

                                  <Button
                                    onClick={() => setShowTestDialog(false)}
                                    className="w-full"
                                  >
                                    Got it
                                  </Button>
                                </div>
                              )}
                            </DialogContent>
                          </Dialog>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Help Section */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Activity className="h-5 w-5" />
            Using Custom Tools
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-blue-800">
          <div>
            <strong>For N8N Workflows:</strong> Copy the N8N configuration and paste it into an HTTP Request node in your workflow.
          </div>
          <div>
            <strong>For VAPI Voice Agents:</strong> Copy the VAPI configuration and add it to your assistant's tools array.
          </div>
          <div>
            <strong>Authentication:</strong> All tools use your API authentication automatically when called from integrated workflows.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CustomToolsTab;