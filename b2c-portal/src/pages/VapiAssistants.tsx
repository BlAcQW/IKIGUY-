import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api-client';
import {
  Plus,
  Trash2,
  Edit,
  Phone,
  PhoneCall,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  Settings,
  History,
  Bot,
} from 'lucide-react';

interface Assistant {
  id: string;
  name: string;
  model: {
    provider: string;
    model: string;
    temperature: number;
    messages: Array<{ role: string; content: string }>;
  };
  voice: {
    provider: string;
    url: string;
    timeout: number;
  };
  firstMessage: string;
  createdAt: string;
  updatedAt: string;
}

interface PhoneNumber {
  id: string;
  number: string;
  name?: string;
  provider: string;
}

interface Call {
  id: string;
  assistantId: string;
  customer: {
    number: string;
    name?: string;
  };
  status: string;
  createdAt: string;
  endedAt?: string;
  duration?: number;
}

export default function VapiAssistants() {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [callHistory, setCallHistory] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [calling, setCalling] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showCallDialog, setShowCallDialog] = useState(false);
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    system_prompt: 'You are a helpful AI assistant.',
    first_message: 'Hello! How can I help you today?',
    model: 'gpt-4',
    voice_provider: 'styletts2',
    sample_rate: 24000,
    enable_recording: true,
    enable_transcription: true,
  });

  // Call form state
  const [callData, setCallData] = useState({
    phone_number: '',
    name: '',
  });

  // Fetch data
  const fetchAssistants = async () => {
    try {
      const response = await api.get('/api/vapi/assistants/');
      setAssistants(response.data.assistants || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch assistants',
        variant: 'destructive',
      });
    }
  };

  const fetchPhoneNumbers = async () => {
    try {
      const response = await api.get('/api/vapi/assistants/phone-numbers');
      setPhoneNumbers(response.data.phone_numbers || []);
    } catch (error: any) {
      console.error('Failed to fetch phone numbers:', error);
    }
  };

  const fetchCallHistory = async () => {
    try {
      const response = await api.get('/api/vapi/assistants/calls/history?limit=20');
      setCallHistory(response.data.calls || []);
    } catch (error: any) {
      console.error('Failed to fetch call history:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchAssistants(), fetchPhoneNumbers(), fetchCallHistory()]);
      setLoading(false);
    };
    loadData();
  }, []);

  // Create assistant
  const handleCreate = async () => {
    setCreating(true);
    try {
      const response = await api.post('/api/vapi/assistants/', formData);
      toast({
        title: 'Success',
        description: response.data.message || 'Assistant created successfully',
      });
      setShowCreateDialog(false);
      setFormData({
        name: '',
        system_prompt: 'You are a helpful AI assistant.',
        first_message: 'Hello! How can I help you today?',
        model: 'gpt-4',
        voice_provider: 'styletts2',
        sample_rate: 24000,
        enable_recording: true,
        enable_transcription: true,
      });
      await fetchAssistants();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create assistant',
        variant: 'destructive',
      });
    } finally {
      setCreating(false);
    }
  };

  // Delete assistant
  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this assistant?')) return;

    setDeleting(id);
    try {
      const response = await api.delete(`/api/vapi/assistants/${id}`);
      toast({
        title: 'Success',
        description: response.data.message || 'Assistant deleted successfully',
      });
      await fetchAssistants();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete assistant',
        variant: 'destructive',
      });
    } finally {
      setDeleting(null);
    }
  };

  // Make test call
  const handleCall = async () => {
    if (!selectedAssistant) return;

    setCalling(true);
    try {
      const response = await api.post('/api/vapi/assistants/call', {
        assistant_id: selectedAssistant.id,
        phone_number: callData.phone_number,
        name: callData.name || undefined,
      });

      toast({
        title: 'Success',
        description: response.data.message || 'Call initiated successfully',
      });

      setShowCallDialog(false);
      setCallData({ phone_number: '', name: '' });
      await fetchCallHistory();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to initiate call',
        variant: 'destructive',
      });
    } finally {
      setCalling(false);
    }
  };

  // Copy ID to clipboard
  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Format duration
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Vapi Assistants
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your Vapi voice assistants with custom TTS
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => {
              fetchAssistants();
              fetchPhoneNumbers();
              fetchCallHistory();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Assistant
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="assistants" className="space-y-6">
        <TabsList>
          <TabsTrigger value="assistants">Assistants</TabsTrigger>
          <TabsTrigger value="calls">Call History</TabsTrigger>
          <TabsTrigger value="numbers">Phone Numbers</TabsTrigger>
        </TabsList>

        {/* Assistants Tab */}
        <TabsContent value="assistants" className="space-y-4">
          {assistants.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  No assistants yet
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Create your first Vapi assistant with custom TTS
                </p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Assistant
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {assistants.map((assistant) => (
                <Card key={assistant.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="flex items-center gap-2">
                          {assistant.name}
                          <Badge variant="outline">
                            {assistant.model.model}
                          </Badge>
                        </CardTitle>
                        <CardDescription className="mt-2">
                          {assistant.model.messages[0]?.content || 'No system prompt'}
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedAssistant(assistant);
                            setShowCallDialog(true);
                          }}
                        >
                          <Phone className="h-4 w-4 mr-2" />
                          Test Call
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(assistant.id, assistant.id)}
                        >
                          {copiedId === assistant.id ? (
                            <Check className="h-4 w-4" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete(assistant.id)}
                          disabled={deleting === assistant.id}
                        >
                          {deleting === assistant.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <Label className="text-gray-600 dark:text-gray-400">
                          Assistant ID
                        </Label>
                        <p className="font-mono text-xs mt-1 truncate">
                          {assistant.id}
                        </p>
                      </div>
                      <div>
                        <Label className="text-gray-600 dark:text-gray-400">
                          Voice Provider
                        </Label>
                        <p className="mt-1">{assistant.voice.provider}</p>
                      </div>
                      <div>
                        <Label className="text-gray-600 dark:text-gray-400">
                          First Message
                        </Label>
                        <p className="mt-1 truncate">{assistant.firstMessage}</p>
                      </div>
                      <div>
                        <Label className="text-gray-600 dark:text-gray-400">
                          Created
                        </Label>
                        <p className="mt-1">{formatDate(assistant.createdAt)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Call History Tab */}
        <TabsContent value="calls">
          <Card>
            <CardHeader>
              <CardTitle>Recent Calls</CardTitle>
              <CardDescription>
                History of test calls made to Vapi assistants
              </CardDescription>
            </CardHeader>
            <CardContent>
              {callHistory.length === 0 ? (
                <div className="text-center py-12">
                  <PhoneCall className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No call history yet
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Call ID</TableHead>
                      <TableHead>Phone Number</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Started</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {callHistory.map((call) => (
                      <TableRow key={call.id}>
                        <TableCell className="font-mono text-xs">
                          {call.id.substring(0, 8)}...
                        </TableCell>
                        <TableCell>{call.customer.number}</TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              call.status === 'completed' ? 'default' : 'outline'
                            }
                          >
                            {call.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {call.duration ? formatDuration(call.duration) : '-'}
                        </TableCell>
                        <TableCell>{formatDate(call.createdAt)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Phone Numbers Tab */}
        <TabsContent value="numbers">
          <Card>
            <CardHeader>
              <CardTitle>Vapi Phone Numbers</CardTitle>
              <CardDescription>
                Phone numbers purchased in your Vapi account
              </CardDescription>
            </CardHeader>
            <CardContent>
              {phoneNumbers.length === 0 ? (
                <div className="text-center py-12">
                  <Phone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No phone numbers found
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Number</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Provider</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {phoneNumbers.map((number) => (
                      <TableRow key={number.id}>
                        <TableCell className="font-semibold">
                          {number.number}
                        </TableCell>
                        <TableCell>{number.name || '-'}</TableCell>
                        <TableCell>{number.provider}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Assistant Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Vapi Assistant</DialogTitle>
            <DialogDescription>
              Create a new voice assistant with custom TTS integration
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Assistant Name *</Label>
              <Input
                id="name"
                placeholder="Customer Support Bot"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="system_prompt">System Prompt *</Label>
              <Textarea
                id="system_prompt"
                placeholder="You are a helpful customer support agent..."
                rows={4}
                value={formData.system_prompt}
                onChange={(e) =>
                  setFormData({ ...formData, system_prompt: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="first_message">First Message *</Label>
              <Input
                id="first_message"
                placeholder="Hello! How can I help you?"
                value={formData.first_message}
                onChange={(e) =>
                  setFormData({ ...formData, first_message: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="model">LLM Model</Label>
                <Select
                  value={formData.model}
                  onValueChange={(value) =>
                    setFormData({ ...formData, model: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                    <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                    <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="voice_provider">Voice Provider</Label>
                <Select
                  value={formData.voice_provider}
                  onValueChange={(value) =>
                    setFormData({ ...formData, voice_provider: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="styletts2">StyleTTS2</SelectItem>
                    <SelectItem value="kokoro">Kokoro</SelectItem>
                    <SelectItem value="bark">Bark</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sample_rate">Sample Rate (Hz)</Label>
              <Select
                value={formData.sample_rate.toString()}
                onValueChange={(value) =>
                  setFormData({ ...formData, sample_rate: parseInt(value) })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="8000">8000 Hz</SelectItem>
                  <SelectItem value="16000">16000 Hz</SelectItem>
                  <SelectItem value="22050">22050 Hz</SelectItem>
                  <SelectItem value="24000">24000 Hz (Recommended)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
              disabled={creating}
            >
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={creating || !formData.name}>
              {creating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Assistant'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Call Dialog */}
      <Dialog open={showCallDialog} onOpenChange={setShowCallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Make Test Call</DialogTitle>
            <DialogDescription>
              Test your assistant with a phone call to {selectedAssistant?.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="phone_number">Phone Number *</Label>
              <Input
                id="phone_number"
                type="tel"
                placeholder="+1234567890"
                value={callData.phone_number}
                onChange={(e) =>
                  setCallData({ ...callData, phone_number: e.target.value })
                }
              />
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Must be in E.164 format (e.g., +1234567890)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="caller_name">Caller Name (Optional)</Label>
              <Input
                id="caller_name"
                placeholder="John Doe"
                value={callData.name}
                onChange={(e) =>
                  setCallData({ ...callData, name: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCallDialog(false)}
              disabled={calling}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCall}
              disabled={calling || !callData.phone_number}
            >
              {calling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Calling...
                </>
              ) : (
                <>
                  <PhoneCall className="h-4 w-4 mr-2" />
                  Make Call
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
