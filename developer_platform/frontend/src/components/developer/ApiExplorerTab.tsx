import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import {
  Play,
  Code2,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  BookOpen,
  Zap
} from "lucide-react";
import { toast } from "@/components/ui/use-toast";

/**
 * API endpoint definition
 */
interface ApiEndpoint {
  id: string;
  category: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  title: string;
  description: string;
  parameters?: Parameter[];
  requestBody?: Record<string, any>;
  exampleResponse?: Record<string, any>;
}

interface Parameter {
  name: string;
  type: "string" | "number" | "boolean" | "object";
  required: boolean;
  description: string;
  example?: any;
}

/**
 * Predefined API endpoints
 */
const API_ENDPOINTS: ApiEndpoint[] = [
  {
    id: "create-assistant",
    category: "Assistants",
    method: "POST",
    path: "/api/v1/assistants",
    title: "Create Assistant",
    description: "Create a new voice assistant with custom configuration",
    requestBody: {
      name: "My Assistant",
      voice: {
        provider: "elevenlabs",
        voice_id: "21m00Tcm4TlvDq8ikWAM"
      },
      model: {
        provider: "openai",
        model: "gpt-4"
      },
      first_message: "Hello! How can I help you?",
    },
    exampleResponse: {
      id: "asst_1234567890",
      name: "My Assistant",
      status: "active",
      created_at: "2025-10-23T12:00:00Z"
    }
  },
  {
    id: "list-assistants",
    category: "Assistants",
    method: "GET",
    path: "/api/v1/assistants",
    title: "List Assistants",
    description: "Retrieve a list of all assistants",
    parameters: [
      { name: "limit", type: "number", required: false, description: "Number of items to return", example: 20 },
      { name: "cursor", type: "string", required: false, description: "Pagination cursor", example: "" }
    ],
    exampleResponse: {
      data: [
        { id: "asst_1", name: "Assistant 1", status: "active" },
        { id: "asst_2", name: "Assistant 2", status: "active" }
      ],
      pagination: { has_more: false, next_cursor: null }
    }
  },
  {
    id: "create-call",
    category: "Calls",
    method: "POST",
    path: "/api/v1/calls",
    title: "Create Call",
    description: "Initiate a phone call with an assistant",
    requestBody: {
      assistant_id: "asst_1234567890",
      phone_number: "+1234567890",
      max_duration_minutes: 5
    },
    exampleResponse: {
      id: "call_9876543210",
      assistant_id: "asst_1234567890",
      status: "queued",
      created_at: "2025-10-23T12:05:00Z"
    }
  },
  {
    id: "get-call",
    category: "Calls",
    method: "GET",
    path: "/api/v1/calls/:call_id",
    title: "Get Call",
    description: "Retrieve details about a specific call",
    parameters: [
      { name: "call_id", type: "string", required: true, description: "The call ID", example: "call_123" }
    ],
    exampleResponse: {
      id: "call_123",
      status: "completed",
      duration_seconds: 45,
      cost: 0.50
    }
  },
  {
    id: "create-workflow",
    category: "Workflows",
    method: "POST",
    path: "/api/v1/workflows",
    title: "Create Workflow",
    description: "Create a new automation workflow",
    requestBody: {
      name: "My Workflow",
      trigger: { type: "webhook" },
      actions: []
    },
    exampleResponse: {
      id: "wf_1234567890",
      name: "My Workflow",
      status: "active"
    }
  },
  {
    id: "get-quota",
    category: "Usage",
    method: "GET",
    path: "/api/v1/usage/quota",
    title: "Get Quota Status",
    description: "Get current quota and usage information",
    parameters: [],
    exampleResponse: {
      plan: "free",
      daily: { limit: 100, used: 45, remaining: 55 },
      monthly: { limit: 1000, used: 456, remaining: 544 }
    }
  },
  {
    id: "get-usage-summary",
    category: "Usage",
    method: "GET",
    path: "/api/v1/usage/summary",
    title: "Get Usage Summary",
    description: "Get comprehensive usage summary",
    parameters: [],
    exampleResponse: {
      quota: { plan: "free", daily: {}, monthly: {} },
      rate_limit: { tokens_remaining: 8, tokens_capacity: 20 },
      stats: { total_requests: 150, total_cost: 125.5 }
    }
  },
];

const API_BASE_URL = "https://developer.ailabsafrica.com";

/**
 * HTTP method badge component
 */
const MethodBadge = ({ method }: { method: string }) => {
  const colors = {
    GET: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    POST: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    PUT: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
    PATCH: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    DELETE: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  };

  return (
    <Badge className={`${colors[method as keyof typeof colors]} font-mono font-bold`}>
      {method}
    </Badge>
  );
};

/**
 * Code example generator
 */
const generateCodeExample = (endpoint: ApiEndpoint, apiKey: string, parameters: Record<string, any>) => {
  const fullPath = endpoint.path.replace(/:(\w+)/g, (_, param) => parameters[param] || `:${param}`);
  const url = `${API_BASE_URL}${fullPath}`;

  const examples = {
    curl: `curl -X ${endpoint.method} ${url} \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json"${
    endpoint.requestBody ? ` \\
  -d '${JSON.stringify(endpoint.requestBody, null, 2)}'` : ''
  }`,

    python: `import requests

url = "${url}"
headers = {
    "X-API-Key": "${apiKey}",
    "Content-Type": "application/json"
}
${endpoint.requestBody ? `data = ${JSON.stringify(endpoint.requestBody, null, 2)}

response = requests.${endpoint.method.toLowerCase()}(url, headers=headers, json=data)` : `response = requests.${endpoint.method.toLowerCase()}(url, headers=headers)`}
print(response.json())`,

    javascript: `const response = await fetch("${url}", {
  method: "${endpoint.method}",
  headers: {
    "X-API-Key": "${apiKey}",
    "Content-Type": "application/json"
  }${endpoint.requestBody ? `,
  body: JSON.stringify(${JSON.stringify(endpoint.requestBody, null, 2)})` : ''}
});

const data = await response.json();
console.log(data);`,
  };

  return examples;
};

/**
 * Main API Explorer Tab Component
 */
export const ApiExplorerTab = () => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(API_ENDPOINTS[0]);
  const [apiKey, setApiKey] = useState("");
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [requestBody, setRequestBody] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<"curl" | "python" | "javascript">("curl");

  // Group endpoints by category
  const categories = Array.from(new Set(API_ENDPOINTS.map(e => e.category)));

  // Handle endpoint selection
  const handleEndpointSelect = (endpoint: ApiEndpoint) => {
    setSelectedEndpoint(endpoint);
    setParameters({});
    setRequestBody(endpoint.requestBody ? JSON.stringify(endpoint.requestBody, null, 2) : "");
    setResponse(null);
  };

  // Execute API request
  const executeRequest = async () => {
    if (!selectedEndpoint) return;
    if (!apiKey) {
      toast({
        title: "API Key Required",
        description: "Please enter your API key to make requests",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      // Replace path parameters
      let fullPath = selectedEndpoint.path;
      Object.keys(parameters).forEach(param => {
        fullPath = fullPath.replace(`:${param}`, parameters[param]);
      });

      const url = `${API_BASE_URL}${fullPath}`;
      const headers = {
        "X-API-Key": apiKey,
        "Content-Type": "application/json",
      };

      const options: RequestInit = {
        method: selectedEndpoint.method,
        headers,
      };

      if (selectedEndpoint.method !== "GET" && requestBody) {
        options.body = requestBody;
      }

      const res = await fetch(url, options);
      const data = await res.json();

      setResponse({
        status: res.status,
        statusText: res.statusText,
        headers: Object.fromEntries(res.headers.entries()),
        body: data,
      });

      if (res.ok) {
        toast({
          title: "Success",
          description: `${selectedEndpoint.title} executed successfully`,
        });
      }
    } catch (error: any) {
      setResponse({
        status: 0,
        statusText: "Error",
        body: { error: error.message },
      });
      toast({
        title: "Request Failed",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Copy code to clipboard
  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
    toast({ title: "Copied to clipboard" });
  };

  const codeExamples = selectedEndpoint && apiKey
    ? generateCodeExample(selectedEndpoint, apiKey, parameters)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                API Explorer
              </CardTitle>
              <CardDescription>
                Test API endpoints interactively with your API key
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <a href="https://docs.ailabsafrica.com" target="_blank" rel="noopener noreferrer">
                <BookOpen className="h-4 w-4 mr-2" />
                View Full Docs
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="api-key">API Key</Label>
            <Input
              id="api-key"
              type="password"
              placeholder="Enter your API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <p className="text-sm text-muted-foreground">
              Your API key is used to authenticate requests. Get one from the API Keys tab.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Endpoint List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm">Endpoints</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Accordion type="single" collapsible defaultValue={categories[0]}>
              {categories.map((category) => (
                <AccordionItem key={category} value={category} className="border-0">
                  <AccordionTrigger className="px-6 hover:bg-muted/50">
                    <span className="font-medium">{category}</span>
                  </AccordionTrigger>
                  <AccordionContent className="pb-0">
                    {API_ENDPOINTS.filter(e => e.category === category).map((endpoint) => (
                      <button
                        key={endpoint.id}
                        onClick={() => handleEndpointSelect(endpoint)}
                        className={`w-full text-left px-6 py-3 hover:bg-muted/50 transition-colors ${
                          selectedEndpoint?.id === endpoint.id ? "bg-muted" : ""
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <MethodBadge method={endpoint.method} />
                        </div>
                        <p className="text-sm font-medium">{endpoint.title}</p>
                        <p className="text-xs text-muted-foreground font-mono mt-1">
                          {endpoint.path}
                        </p>
                      </button>
                    ))}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>

        {/* Endpoint Details & Testing */}
        <div className="lg:col-span-2 space-y-6">
          {selectedEndpoint ? (
            <>
              {/* Endpoint Info */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <MethodBadge method={selectedEndpoint.method} />
                    <code className="text-sm font-mono">{selectedEndpoint.path}</code>
                  </div>
                  <CardTitle>{selectedEndpoint.title}</CardTitle>
                  <CardDescription>{selectedEndpoint.description}</CardDescription>
                </CardHeader>
              </Card>

              {/* Parameters & Body */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Request Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Path Parameters */}
                  {selectedEndpoint.parameters && selectedEndpoint.parameters.length > 0 && (
                    <div className="space-y-3">
                      <Label className="text-sm font-medium">Parameters</Label>
                      {selectedEndpoint.parameters.map((param) => (
                        <div key={param.name} className="space-y-2">
                          <Label htmlFor={param.name} className="text-sm flex items-center gap-2">
                            {param.name}
                            {param.required && (
                              <Badge variant="destructive" className="text-xs">Required</Badge>
                            )}
                            <span className="text-muted-foreground font-normal ml-auto">
                              {param.type}
                            </span>
                          </Label>
                          <Input
                            id={param.name}
                            placeholder={param.example?.toString() || param.description}
                            value={parameters[param.name] || ""}
                            onChange={(e) => setParameters({ ...parameters, [param.name]: e.target.value })}
                          />
                          <p className="text-xs text-muted-foreground">{param.description}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Request Body */}
                  {selectedEndpoint.method !== "GET" && (
                    <div className="space-y-2">
                      <Label htmlFor="request-body" className="text-sm font-medium">
                        Request Body (JSON)
                      </Label>
                      <Textarea
                        id="request-body"
                        placeholder="Enter JSON body"
                        value={requestBody}
                        onChange={(e) => setRequestBody(e.target.value)}
                        className="font-mono text-sm min-h-[200px]"
                      />
                    </div>
                  )}

                  {/* Execute Button */}
                  <Button
                    onClick={executeRequest}
                    disabled={loading || !apiKey}
                    className="w-full"
                    size="lg"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Execute Request
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Response */}
              {response && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">Response</CardTitle>
                      <Badge
                        variant={response.status >= 200 && response.status < 300 ? "default" : "destructive"}
                      >
                        {response.status} {response.statusText}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                      {JSON.stringify(response.body, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {/* Code Examples */}
              {codeExamples && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">Code Examples</CardTitle>
                      <Select value={selectedLanguage} onValueChange={(v: any) => setSelectedLanguage(v)}>
                        <SelectTrigger className="w-[140px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="curl">cURL</SelectItem>
                          <SelectItem value="python">Python</SelectItem>
                          <SelectItem value="javascript">JavaScript</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardHeader>
                  <CardContent className="relative">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="absolute top-2 right-2 z-10"
                      onClick={() => copyCode(codeExamples[selectedLanguage])}
                    >
                      {copiedCode ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                      <code>{codeExamples[selectedLanguage]}</code>
                    </pre>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center text-muted-foreground">
                  <Code2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select an endpoint to get started</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
