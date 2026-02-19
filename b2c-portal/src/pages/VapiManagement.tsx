import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Activity,
  Play,
  Settings,
  BarChart3,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Copy,
  Download,
  Phone,
  PhoneCall,
  Users,
  Plus,
  Trash2,
  Edit,
  Clock,
} from 'lucide-react';
import { api } from '@/lib/api-client';
import { useToast } from '../components/ui/use-toast';

interface VapiConfig {
  tts_providers: {
    default: string;
    fallback: string;
    available: string[];
  };
  rate_limits: {
    user: { requests_per_minute: number; requests_per_hour: number };
    organization: { requests_per_minute: number; requests_per_hour: number };
  };
  audio_formats: {
    output: string;
    supported_sample_rates: number[];
    bit_depth: number;
    channels: number;
  };
}

interface VapiHealth {
  status: string;
  stats: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    fallback_used: number;
  };
}

interface VapiAssistant {
  id: string;
  name: string;
  model?: { model?: string };
  voice?: { provider?: string };
  firstMessage?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface VapiCall {
  id: string;
  assistantId?: string;
  customer?: { number?: string; name?: string };
  status?: string;
  startedAt?: string;
  endedAt?: string;
  duration?: number;
  cost?: number;
}

const VapiManagement: React.FC = () => {
  const { toast } = useToast();
  const [config, setConfig] = useState<VapiConfig | null>(null);
  const [health, setHealth] = useState<VapiHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [testText, setTestText] = useState('Hello! This is a test of the KasaAI custom TTS system for Vapi.');
  const [sampleRate, setSampleRate] = useState(24000);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Assistants state
  const [assistants, setAssistants] = useState<VapiAssistant[]>([]);
  const [loadingAssistants, setLoadingAssistants] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [callDialogOpen, setCallDialogOpen] = useState(false);
  const [selectedAssistant, setSelectedAssistant] = useState<VapiAssistant | null>(null);

  // Call history state
  const [callHistory, setCallHistory] = useState<VapiCall[]>([]);
  const [loadingCalls, setLoadingCalls] = useState(false);

  // Create assistant form
  const [newAssistant, setNewAssistant] = useState({
    name: '',
    system_prompt: 'You are a helpful AI assistant.',
    first_message: 'Hello! How can I help you today?',
    model: 'gpt-4',
    voice_provider: 'styletts2',
    sample_rate: 24000,
    enable_recording: true,
    enable_transcription: true,
  });

  // Test call form
  const [callRequest, setCallRequest] = useState({
    phone_number: '',
    name: '',
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    await Promise.all([fetchConfig(), fetchHealth()]);
    setLoading(false);
  };

  const fetchConfig = async () => {
    try {
      const response = await api.get('/api/vapi/config');
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  const fetchHealth = async () => {
    try {
      const response = await api.get('/api/vapi/health');
      setHealth(response.data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
    }
  };

  const fetchAssistants = async () => {
    setLoadingAssistants(true);
    try {
      const response = await api.get('/api/vapi/assistants/');
      setAssistants(response.data.assistants || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch assistants',
        variant: 'destructive',
      });
    } finally {
      setLoadingAssistants(false);
    }
  };

  const fetchCallHistory = async () => {
    setLoadingCalls(true);
    try {
      const response = await api.get('/api/vapi/assistants/calls/history', {
        params: { limit: 20 },
      });
      setCallHistory(response.data.calls || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch call history',
        variant: 'destructive',
      });
    } finally {
      setLoadingCalls(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await api.post(
        '/api/vapi/test',
        {
          text: testText,
          sample_rate: sampleRate,
        },
        {
          responseType: 'blob',
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `vapi_test_${sampleRate}hz.pcm`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setTestResult({
        success: true,
        message: `✓ Test successful! Audio downloaded as vapi_test_${sampleRate}hz.pcm`,
      });

      // Refresh health stats
      await fetchHealth();
    } catch (error: any) {
      setTestResult({
        success: false,
        message: `✗ Test failed: ${error.response?.data?.detail || error.message}`,
      });
    } finally {
      setTesting(false);
    }
  };

  const handleCreateAssistant = async () => {
    try {
      const response = await api.post('/api/vapi/assistants/', newAssistant);

      toast({
        title: 'Success',
        description: response.data.message || 'Assistant created successfully',
      });

      setCreateDialogOpen(false);
      setNewAssistant({
        name: '',
        system_prompt: 'You are a helpful AI assistant.',
        first_message: 'Hello! How can I help you today?',
        model: 'gpt-4',
        voice_provider: 'styletts2',
        sample_rate: 24000,
        enable_recording: true,
        enable_transcription: true,
      });

      // Refresh assistants list
      await fetchAssistants();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create assistant',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteAssistant = async (assistantId: string) => {
    if (!confirm('Are you sure you want to delete this assistant?')) {
      return;
    }

    try {
      await api.delete(`/api/vapi/assistants/${assistantId}`);

      toast({
        title: 'Success',
        description: 'Assistant deleted successfully',
      });

      // Refresh assistants list
      await fetchAssistants();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete assistant',
        variant: 'destructive',
      });
    }
  };

  const handleMakeCall = async () => {
    if (!selectedAssistant) return;

    try {
      const response = await api.post('/api/vapi/assistants/call', {
        assistant_id: selectedAssistant.id,
        phone_number: callRequest.phone_number,
        name: callRequest.name || undefined,
      });

      toast({
        title: 'Success',
        description: response.data.message || 'Call initiated successfully',
      });

      setCallDialogOpen(false);
      setCallRequest({ phone_number: '', name: '' });

      // Refresh call history
      await fetchCallHistory();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to make call',
        variant: 'destructive',
      });
    }
  };

  const copyWebhookURL = () => {
    const url = `${window.location.origin}/api/vapi/webhook`;
    navigator.clipboard.writeText(url);
    toast({
      title: 'Copied',
      description: 'Webhook URL copied to clipboard!',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading Vapi configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Vapi TTS Management</h1>
        <p className="text-gray-600 mt-2">
          Manage your custom TTS webhook for Vapi voice assistants
        </p>
      </div>

      {/* Health Status */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Service Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className={`text-2xl font-bold ${getStatusColor(health.status)}`}>
                  {health.status.toUpperCase()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold">{health.stats.total_requests.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <div>
                  <p className="text-2xl font-bold">{(health.stats.success_rate * 100).toFixed(1)}%</p>
                  <Progress value={health.stats.success_rate * 100} className="mt-2" />
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600">Fallback Used</p>
                <p className="text-2xl font-bold">{health.stats.fallback_used}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="configuration" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configuration">
            <Settings className="h-4 w-4 mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="test">
            <Play className="h-4 w-4 mr-2" />
            Test Webhook
          </TabsTrigger>
          <TabsTrigger value="assistants" onClick={() => fetchAssistants()}>
            <Users className="h-4 w-4 mr-2" />
            Assistants
          </TabsTrigger>
          <TabsTrigger value="calls" onClick={() => fetchCallHistory()}>
            <PhoneCall className="h-4 w-4 mr-2" />
            Call History
          </TabsTrigger>
          <TabsTrigger value="statistics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Statistics
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Webhook URL</CardTitle>
              <CardDescription>
                Use this URL in your Vapi assistant configuration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={`${window.location.origin}/api/vapi/webhook`}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button onClick={copyWebhookURL} variant="outline">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Add this URL to your Vapi assistant's voice configuration as a custom TTS provider.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {config && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>TTS Providers</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Default Provider</Label>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="default">{config.tts_providers.default}</Badge>
                      <span className="text-sm text-gray-600">
                        Primary provider for all requests
                      </span>
                    </div>
                  </div>

                  <div>
                    <Label>Fallback Provider</Label>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary">{config.tts_providers.fallback}</Badge>
                      <span className="text-sm text-gray-600">
                        Used if primary fails
                      </span>
                    </div>
                  </div>

                  <div>
                    <Label>Available Providers ({config.tts_providers.available.length})</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {config.tts_providers.available.slice(0, 10).map((provider) => (
                        <Badge key={provider} variant="outline">
                          {provider}
                        </Badge>
                      ))}
                      {config.tts_providers.available.length > 10 && (
                        <Badge variant="outline">
                          +{config.tts_providers.available.length - 10} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Rate Limits</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Per User</Label>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm">
                          {config.rate_limits.user.requests_per_minute} requests/minute
                        </p>
                        <p className="text-sm">
                          {config.rate_limits.user.requests_per_hour} requests/hour
                        </p>
                      </div>
                    </div>
                    <div>
                      <Label>Per Organization</Label>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm">
                          {config.rate_limits.organization.requests_per_minute} requests/minute
                        </p>
                        <p className="text-sm">
                          {config.rate_limits.organization.requests_per_hour} requests/hour
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Audio Format</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <Label>Output</Label>
                      <p className="mt-1 font-mono">{config.audio_formats.output}</p>
                    </div>
                    <div>
                      <Label>Bit Depth</Label>
                      <p className="mt-1">{config.audio_formats.bit_depth}-bit</p>
                    </div>
                    <div>
                      <Label>Channels</Label>
                      <p className="mt-1">Mono ({config.audio_formats.channels})</p>
                    </div>
                    <div>
                      <Label>Sample Rates</Label>
                      <p className="mt-1">{config.audio_formats.supported_sample_rates.join(', ')} Hz</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Vapi Webhook</CardTitle>
              <CardDescription>
                Test the webhook with custom text and download the generated audio
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="test-text">Text to Synthesize</Label>
                <Textarea
                  id="test-text"
                  value={testText}
                  onChange={(e) => setTestText(e.target.value)}
                  rows={3}
                  placeholder="Enter text to convert to speech..."
                  className="mt-2"
                />
              </div>

              <div>
                <Label htmlFor="sample-rate">Sample Rate</Label>
                <Select
                  value={sampleRate.toString()}
                  onValueChange={(value) => setSampleRate(parseInt(value))}
                >
                  <SelectTrigger id="sample-rate" className="mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="8000">8000 Hz (Phone Quality)</SelectItem>
                    <SelectItem value="16000">16000 Hz (Wideband)</SelectItem>
                    <SelectItem value="22050">22050 Hz (CD Quality)</SelectItem>
                    <SelectItem value="24000">24000 Hz (HD Quality)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={handleTest}
                disabled={testing || !testText.trim()}
                className="w-full"
              >
                {testing ? (
                  <>
                    <Activity className="h-4 w-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Test Webhook
                  </>
                )}
              </Button>

              {testResult && (
                <Alert variant={testResult.success ? 'default' : 'destructive'}>
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    <XCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>{testResult.message}</AlertDescription>
                </Alert>
              )}

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  The audio will be downloaded as a .pcm file. Use ffplay to play:
                  <code className="block mt-2 p-2 bg-gray-100 rounded text-sm">
                    ffplay -f s16le -ar {sampleRate} -ac 1 vapi_test_{sampleRate}hz.pcm
                  </code>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Assistants Tab */}
        <TabsContent value="assistants" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Vapi Assistants</h3>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Assistant
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Vapi Assistant</DialogTitle>
                  <DialogDescription>
                    Create a new voice assistant with custom TTS integration
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label htmlFor="name">Assistant Name</Label>
                    <Input
                      id="name"
                      value={newAssistant.name}
                      onChange={(e) => setNewAssistant({ ...newAssistant, name: e.target.value })}
                      placeholder="Customer Support Bot"
                    />
                  </div>
                  <div>
                    <Label htmlFor="system-prompt">System Prompt</Label>
                    <Textarea
                      id="system-prompt"
                      value={newAssistant.system_prompt}
                      onChange={(e) => setNewAssistant({ ...newAssistant, system_prompt: e.target.value })}
                      rows={3}
                      placeholder="You are a helpful assistant..."
                    />
                  </div>
                  <div>
                    <Label htmlFor="first-message">First Message</Label>
                    <Input
                      id="first-message"
                      value={newAssistant.first_message}
                      onChange={(e) => setNewAssistant({ ...newAssistant, first_message: e.target.value })}
                      placeholder="Hello! How can I help you?"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="model">LLM Model</Label>
                      <Select
                        value={newAssistant.model}
                        onValueChange={(value) => setNewAssistant({ ...newAssistant, model: value })}
                      >
                        <SelectTrigger id="model">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="voice-provider">Voice Provider</Label>
                      <Select
                        value={newAssistant.voice_provider}
                        onValueChange={(value) => setNewAssistant({ ...newAssistant, voice_provider: value })}
                      >
                        <SelectTrigger id="voice-provider">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="styletts2">StyleTTS2</SelectItem>
                          <SelectItem value="kokoro">Kokoro</SelectItem>
                          <SelectItem value="chatterbox">Chatterbox</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateAssistant} disabled={!newAssistant.name}>
                    Create Assistant
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loadingAssistants ? (
            <div className="flex justify-center py-8">
              <Activity className="h-6 w-6 animate-spin" />
            </div>
          ) : assistants.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                No assistants found. Create one to get started!
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {assistants.map((assistant) => (
                <Card key={assistant.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle>{assistant.name}</CardTitle>
                        <CardDescription>
                          Model: {assistant.model?.model || 'N/A'} |
                          Voice: {assistant.voice?.provider || 'custom-tts'}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Dialog open={callDialogOpen && selectedAssistant?.id === assistant.id} onOpenChange={(open) => {
                          setCallDialogOpen(open);
                          if (open) setSelectedAssistant(assistant);
                        }}>
                          <DialogTrigger asChild>
                            <Button size="sm" variant="outline">
                              <Phone className="h-4 w-4 mr-2" />
                              Test Call
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Make Test Call</DialogTitle>
                              <DialogDescription>
                                Call a phone number using {assistant.name}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                              <div>
                                <Label htmlFor="phone">Phone Number (E.164 format)</Label>
                                <Input
                                  id="phone"
                                  value={callRequest.phone_number}
                                  onChange={(e) => setCallRequest({ ...callRequest, phone_number: e.target.value })}
                                  placeholder="+1234567890"
                                />
                              </div>
                              <div>
                                <Label htmlFor="caller-name">Name (Optional)</Label>
                                <Input
                                  id="caller-name"
                                  value={callRequest.name}
                                  onChange={(e) => setCallRequest({ ...callRequest, name: e.target.value })}
                                  placeholder="John Doe"
                                />
                              </div>
                            </div>
                            <DialogFooter>
                              <Button variant="outline" onClick={() => setCallDialogOpen(false)}>
                                Cancel
                              </Button>
                              <Button onClick={handleMakeCall} disabled={!callRequest.phone_number}>
                                <Phone className="h-4 w-4 mr-2" />
                                Make Call
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteAssistant(assistant.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">{assistant.firstMessage || 'No first message set'}</p>
                    <p className="text-xs text-gray-400 mt-2">
                      Created: {formatDate(assistant.createdAt)}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Call History Tab */}
        <TabsContent value="calls" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Recent Calls</h3>
            <Button variant="outline" onClick={fetchCallHistory}>
              <Clock className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          {loadingCalls ? (
            <div className="flex justify-center py-8">
              <Activity className="h-6 w-6 animate-spin" />
            </div>
          ) : callHistory.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                No call history found
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {callHistory.map((call) => (
                <Card key={call.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base">
                          {call.customer?.number || 'Unknown'}
                        </CardTitle>
                        <CardDescription>
                          {call.customer?.name || 'No name'}
                        </CardDescription>
                      </div>
                      <Badge variant={call.status === 'completed' ? 'default' : 'secondary'}>
                        {call.status || 'unknown'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Started</p>
                        <p className="font-medium">{formatDate(call.startedAt)}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Duration</p>
                        <p className="font-medium">{formatDuration(call.duration)}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Cost</p>
                        <p className="font-medium">${call.cost?.toFixed(2) || '0.00'}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Call ID</p>
                        <p className="font-mono text-xs">{call.id.slice(0, 12)}...</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Statistics Tab */}
        <TabsContent value="statistics" className="space-y-4">
          {health && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Request Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Total Requests</span>
                    <span className="font-bold">{health.stats.total_requests}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Successful</span>
                    <span className="font-bold text-green-600">
                      {health.stats.successful_requests}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Failed</span>
                    <span className="font-bold text-red-600">
                      {health.stats.failed_requests}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Fallback Used</span>
                    <span className="font-bold text-yellow-600">
                      {health.stats.fallback_used}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Success Rate</span>
                      <span className="font-bold">
                        {(health.stats.success_rate * 100).toFixed(2)}%
                      </span>
                    </div>
                    <Progress value={health.stats.success_rate * 100} />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Fallback Rate</span>
                      <span className="font-bold">
                        {health.stats.total_requests > 0
                          ? ((health.stats.fallback_used / health.stats.total_requests) * 100).toFixed(2)
                          : 0}%
                      </span>
                    </div>
                    <Progress
                      value={
                        health.stats.total_requests > 0
                          ? (health.stats.fallback_used / health.stats.total_requests) * 100
                          : 0
                      }
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Cost Savings</CardTitle>
              <CardDescription>
                Estimated savings compared to third-party TTS providers
              </CardDescription>
            </CardHeader>
            <CardContent>
              {health && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-gray-600">vs. ElevenLabs</p>
                      <p className="text-2xl font-bold text-green-600">
                        ${((health.stats.total_requests * 0.03)).toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500">saved</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">vs. PlayHT</p>
                      <p className="text-2xl font-bold text-green-600">
                        ${((health.stats.total_requests * 0.025)).toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500">saved</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">vs. Deepgram Aura</p>
                      <p className="text-2xl font-bold text-green-600">
                        ${((health.stats.total_requests * 0.015)).toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500">saved</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 text-center">
                    Based on {health.stats.total_requests} requests processed
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VapiManagement;
