/**
 * Register Tool Page
 *
 * Page for registering custom tools in MongoDB and VAPI platform
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  Wrench,
  Upload,
  Database,
  Cloud,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { API_BASE_URL } from '@/config/api-config';
import { getAuthHeaders } from '@/lib/auth-utils';

interface RegistrationResult {
  success: boolean;
  message: string;
  tool_id?: string;
  error?: string;
}

const RegisterTool: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // MongoDB Registration State
  const [mongoForm, setMongoForm] = useState({
    file_path: '',
    client_id: '',
    industry: 'general',
    category: 'utility',
    description: '',
  });
  const [mongoLoading, setMongoLoading] = useState(false);
  const [mongoResult, setMongoResult] = useState<RegistrationResult | null>(null);

  // VAPI Registration State
  const [vapiForm, setVapiForm] = useState({
    tool_name: '',
    description: '',
    server_url: '',
    function_name: '',
    parameters_json: '{}',
  });
  const [vapiLoading, setVapiLoading] = useState(false);
  const [vapiResult, setVapiResult] = useState<RegistrationResult | null>(null);

  // Quick Register RAG Tools
  const [ragLoading, setRagLoading] = useState(false);

  // Handle MongoDB Registration
  const handleMongoRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setMongoLoading(true);
    setMongoResult(null);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/register`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mongoForm),
      });

      const data = await response.json();

      if (response.ok) {
        setMongoResult({
          success: true,
          message: data.message || 'Tool registered successfully',
          tool_id: data.tool_ids?.[0],
        });
        toast({
          title: 'Success',
          description: 'Tool registered in MongoDB',
        });
        // Reset form
        setMongoForm({
          file_path: '',
          client_id: '',
          industry: 'general',
          category: 'utility',
          description: '',
        });
      } else {
        throw new Error(data.detail || data.error || 'Registration failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      setMongoResult({
        success: false,
        message: '',
        error: errorMessage,
      });
      toast({
        title: 'Registration failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setMongoLoading(false);
    }
  };

  // Handle VAPI Registration
  const handleVapiRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setVapiLoading(true);
    setVapiResult(null);

    try {
      const headers = await getAuthHeaders();

      // Parse parameters JSON
      let parameters;
      try {
        parameters = JSON.parse(vapiForm.parameters_json);
      } catch {
        throw new Error('Invalid JSON in parameters field');
      }

      const toolConfig = {
        type: 'function',
        async: false,
        messages: [
          {
            type: 'request-start',
            content: 'Processing your request...',
          },
          {
            type: 'request-failed',
            content: 'I encountered an issue. Let me try another way.',
          },
        ],
        function: {
          name: vapiForm.function_name,
          description: vapiForm.description,
          parameters: parameters,
        },
        server: {
          url: vapiForm.server_url,
          timeoutSeconds: 20,
        },
      };

      const response = await fetch(`${API_BASE_URL}/vapi/tools/register`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tool_config: toolConfig }),
      });

      const data = await response.json();

      if (response.ok) {
        setVapiResult({
          success: true,
          message: 'Tool registered on VAPI platform',
          tool_id: data.tool_id,
        });
        toast({
          title: 'Success',
          description: `VAPI Tool ID: ${data.tool_id}`,
        });
      } else {
        throw new Error(data.detail || data.error || 'VAPI registration failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'VAPI registration failed';
      setVapiResult({
        success: false,
        message: '',
        error: errorMessage,
      });
      toast({
        title: 'VAPI registration failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setVapiLoading(false);
    }
  };

  // Quick Register Premier Health RAG Tools
  const handleQuickRegisterRAG = async () => {
    setRagLoading(true);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/custom-tools/init-rag-tools`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: 'Success',
          description: data.message || 'RAG tools registered successfully',
        });
        // Navigate to custom tools page after 1.5 seconds
        setTimeout(() => {
          navigate('/custom-tools');
        }, 1500);
      } else {
        throw new Error(data.detail || data.error || 'Failed to register RAG tools');
      }
    } catch (error) {
      toast({
        title: 'Registration failed',
        description: error instanceof Error ? error.message : 'Failed to register RAG tools',
        variant: 'destructive',
      });
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/custom-tools')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Wrench className="h-6 w-6" />
                Register Custom Tool
              </h1>
              <p className="text-gray-600">
                Register tools in MongoDB or VAPI platform
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {/* Quick Register RAG Tools */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cloud className="h-5 w-5" />
                Quick Register: Premier Health & Ghana Tourism RAG Tools
              </CardTitle>
              <CardDescription>
                Register Premier Health and Ghana Tourism RAG tools with one click.
                These tools are already configured and ready to use with VAPI assistants.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Button
                  onClick={handleQuickRegisterRAG}
                  disabled={ragLoading}
                  size="lg"
                >
                  {ragLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Registering...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Register RAG Tools
                    </>
                  )}
                </Button>
                <div className="text-sm text-gray-600">
                  <p>This will register:</p>
                  <ul className="list-disc list-inside mt-1">
                    <li>Premier Health Knowledge Base Tool (VAPI ID: 560adfee-43bf-4614-baa8-0d5ccfbe9769)</li>
                    <li>Ghana Tourism Knowledge Base Tool (VAPI ID: 2bac26dc-5f8e-4d3d-82b2-ca55286ddf36)</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="mongodb" className="w-full">
            <TabsList className="grid w-full grid-cols-2 max-w-md">
              <TabsTrigger value="mongodb">
                <Database className="h-4 w-4 mr-2" />
                MongoDB Tools
              </TabsTrigger>
              <TabsTrigger value="vapi">
                <Cloud className="h-4 w-4 mr-2" />
                VAPI Tools
              </TabsTrigger>
            </TabsList>

            {/* MongoDB Registration */}
            <TabsContent value="mongodb" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Register Tool in MongoDB</CardTitle>
                  <CardDescription>
                    Register a custom tool from a Python file for use in N8N workflows and automations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleMongoRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="file_path">File Path *</Label>
                      <Input
                        id="file_path"
                        placeholder="/opt/kasaai/apps/automations/example/tools.py"
                        value={mongoForm.file_path}
                        onChange={(e) => setMongoForm({ ...mongoForm, file_path: e.target.value })}
                        required
                      />
                      <p className="text-xs text-gray-600">
                        Absolute path to Python file containing tool functions
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="client_id">Client ID *</Label>
                      <Input
                        id="client_id"
                        placeholder="premier-health"
                        value={mongoForm.client_id}
                        onChange={(e) => setMongoForm({ ...mongoForm, client_id: e.target.value })}
                        required
                      />
                      <p className="text-xs text-gray-600">
                        Unique identifier for the client/project
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="industry">Industry</Label>
                        <Select
                          value={mongoForm.industry}
                          onValueChange={(value) => setMongoForm({ ...mongoForm, industry: value })}
                        >
                          <SelectTrigger id="industry">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="general">General</SelectItem>
                            <SelectItem value="healthcare">Healthcare</SelectItem>
                            <SelectItem value="tourism">Tourism</SelectItem>
                            <SelectItem value="finance">Finance</SelectItem>
                            <SelectItem value="education">Education</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="category">Category</Label>
                        <Select
                          value={mongoForm.category}
                          onValueChange={(value) => setMongoForm({ ...mongoForm, category: value })}
                        >
                          <SelectTrigger id="category">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="utility">Utility</SelectItem>
                            <SelectItem value="provider_search">Provider Search</SelectItem>
                            <SelectItem value="data_retrieval">Data Retrieval</SelectItem>
                            <SelectItem value="analytics">Analytics</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        placeholder="Describe what this tool does..."
                        value={mongoForm.description}
                        onChange={(e) => setMongoForm({ ...mongoForm, description: e.target.value })}
                        rows={3}
                      />
                    </div>

                    {mongoResult && (
                      <div className={`p-4 rounded-lg border ${mongoResult.success ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800'}`}>
                        <div className="flex items-start gap-2">
                          {mongoResult.success ? (
                            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className={`font-medium ${mongoResult.success ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'}`}>
                              {mongoResult.success ? 'Registration Successful' : 'Registration Failed'}
                            </p>
                            <p className={`text-sm ${mongoResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                              {mongoResult.message || mongoResult.error}
                            </p>
                            {mongoResult.tool_id && (
                              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                                Tool ID: {mongoResult.tool_id}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button type="submit" disabled={mongoLoading}>
                        {mongoLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Registering...
                          </>
                        ) : (
                          <>
                            <Database className="h-4 w-4 mr-2" />
                            Register in MongoDB
                          </>
                        )}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => navigate('/custom-tools')}
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            {/* VAPI Registration */}
            <TabsContent value="vapi" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Register Tool on VAPI Platform</CardTitle>
                  <CardDescription>
                    Register a custom function tool on VAPI for use in voice assistants
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleVapiRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="tool_name">Tool Name *</Label>
                      <Input
                        id="tool_name"
                        placeholder="my_custom_tool"
                        value={vapiForm.tool_name}
                        onChange={(e) => setVapiForm({ ...vapiForm, tool_name: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="function_name">Function Name *</Label>
                      <Input
                        id="function_name"
                        placeholder="query_knowledge_base"
                        value={vapiForm.function_name}
                        onChange={(e) => setVapiForm({ ...vapiForm, function_name: e.target.value })}
                        required
                      />
                      <p className="text-xs text-gray-600">
                        Name of the function as it will be called by the assistant
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="server_url">Server URL *</Label>
                      <Input
                        id="server_url"
                        placeholder="https://flow-api.ailabsafrica.com/knowledge-base/query"
                        value={vapiForm.server_url}
                        onChange={(e) => setVapiForm({ ...vapiForm, server_url: e.target.value })}
                        required
                      />
                      <p className="text-xs text-gray-600">
                        Full URL endpoint that will handle the tool call
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="vapi_description">Description *</Label>
                      <Textarea
                        id="vapi_description"
                        placeholder="Describe what this tool does and when to use it..."
                        value={vapiForm.description}
                        onChange={(e) => setVapiForm({ ...vapiForm, description: e.target.value })}
                        rows={3}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="parameters_json">Parameters (JSON Schema) *</Label>
                      <Textarea
                        id="parameters_json"
                        placeholder='{"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}'
                        value={vapiForm.parameters_json}
                        onChange={(e) => setVapiForm({ ...vapiForm, parameters_json: e.target.value })}
                        rows={6}
                        className="font-mono text-sm"
                        required
                      />
                      <p className="text-xs text-gray-600">
                        JSON Schema defining the function parameters
                      </p>
                    </div>

                    {vapiResult && (
                      <div className={`p-4 rounded-lg border ${vapiResult.success ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800'}`}>
                        <div className="flex items-start gap-2">
                          {vapiResult.success ? (
                            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                          ) : (
                            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className={`font-medium ${vapiResult.success ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'}`}>
                              {vapiResult.success ? 'VAPI Registration Successful' : 'VAPI Registration Failed'}
                            </p>
                            <p className={`text-sm ${vapiResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                              {vapiResult.message || vapiResult.error}
                            </p>
                            {vapiResult.tool_id && (
                              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                                VAPI Tool ID: {vapiResult.tool_id}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button type="submit" disabled={vapiLoading}>
                        {vapiLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Registering...
                          </>
                        ) : (
                          <>
                            <Cloud className="h-4 w-4 mr-2" />
                            Register on VAPI
                          </>
                        )}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => navigate('/custom-tools')}
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default RegisterTool;
