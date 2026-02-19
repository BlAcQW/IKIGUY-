import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { 
  Play, 
  Square, 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  MessageSquare, 
  Download, 
  Copy,
  Volume2,
  VolumeX,
  Settings,
  Clock,
  User,
  Bot,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface TestSandboxDialogProps {
  assistant: any;
  children: React.ReactNode;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence?: number;
    intent?: string;
    entities?: any[];
    grounding?: any[];
  };
}

interface TestSession {
  id: string;
  assistant: any;
  messages: Message[];
  startTime: Date;
  endTime?: Date;
  status: 'idle' | 'connecting' | 'active' | 'ended' | 'error';
  duration?: number;
  transcript?: string;
}

const TestSandboxDialog: React.FC<TestSandboxDialogProps> = ({ assistant, children }) => {
  const [open, setOpen] = useState(false);
  const [testSession, setTestSession] = useState<TestSession | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [testMode, setTestMode] = useState<'voice' | 'chat'>('voice');
  const [testScenario, setTestScenario] = useState('general');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const testScenarios = [
    { value: 'general', label: 'General Conversation', description: 'Test basic conversation flow' },
    { value: 'sales', label: 'Sales Inquiry', description: 'Test sales qualification and conversion' },
    { value: 'support', label: 'Support Request', description: 'Test technical support scenarios' },
    { value: 'scheduling', label: 'Appointment Booking', description: 'Test scheduling and booking flow' },
    { value: 'custom', label: 'Custom Scenario', description: 'Define your own test scenario' }
  ];

  const startTestSession = async () => {
    setIsLoading(true);
    try {
      const session: TestSession = {
        id: `test-${Date.now()}`,
        assistant,
        messages: [],
        startTime: new Date(),
        status: 'connecting'
      };

      setTestSession(session);

      // Simulate connection delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setTestSession(prev => prev ? { ...prev, status: 'active' } : null);
      
      // Add welcome message
      const welcomeMessage: Message = {
        id: `msg-${Date.now()}`,
        type: 'assistant',
        content: `Hello! I'm ${assistant.name}. I'm ready to help you with ${assistant.template === 'sales' ? 'sales and lead qualification' : assistant.template === 'support' ? 'technical support' : assistant.template === 'scheduling' ? 'appointment scheduling' : 'your inquiries'}. How can I assist you today?`,
        timestamp: new Date(),
        metadata: {
          confidence: 0.95,
          intent: 'greeting',
          grounding: []
        }
      };

      setTestSession(prev => prev ? {
        ...prev,
        messages: [welcomeMessage]
      } : null);

      toast({
        title: "Test session started",
        description: `Connected to ${assistant.name} successfully`,
        variant: "default"
      });

    } catch (error) {
      console.error('Failed to start test session:', error);
      setTestSession(prev => prev ? { ...prev, status: 'error' } : null);
      toast({
        title: "Connection failed",
        description: "Unable to connect to the assistant. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const endTestSession = () => {
    if (testSession) {
      const endTime = new Date();
      const duration = Math.round((endTime.getTime() - testSession.startTime.getTime()) / 1000);
      
      setTestSession(prev => prev ? {
        ...prev,
        endTime,
        duration,
        status: 'ended',
        transcript: generateTranscript(prev.messages)
      } : null);

      setIsRecording(false);
      setIsMuted(false);
    }
  };

  const sendMessage = async (content: string) => {
    if (!testSession || testSession.status !== 'active') return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date()
    };

    setTestSession(prev => prev ? {
      ...prev,
      messages: [...prev.messages, userMessage]
    } : null);

    setUserInput('');
    setIsLoading(true);

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        type: 'assistant',
        content: generateAssistantResponse(content, testScenario),
        timestamp: new Date(),
        metadata: {
          confidence: 0.87,
          intent: 'response',
          grounding: []
        }
      };

      setTestSession(prev => prev ? {
        ...prev,
        messages: [...prev.messages, assistantMessage]
      } : null);

      setIsLoading(false);
    }, 1000 + Math.random() * 2000); // Random delay between 1-3 seconds
  };

  const generateAssistantResponse = (userInput: string, scenario: string): string => {
    const responses = {
      general: [
        "I understand your question. Let me help you with that.",
        "That's a great point. Here's what I can tell you about that.",
        "I appreciate you asking that. Let me provide you with some information."
      ],
      sales: [
        "I'd be happy to help you with our products and services. What specific information are you looking for?",
        "I can help you find the right solution for your needs. What's your primary concern?",
        "Let me understand your requirements better so I can recommend the best options."
      ],
      support: [
        "I'm here to help you resolve this issue. Let me gather some information first.",
        "I understand the problem you're experiencing. Let me walk you through the solution.",
        "I can help you troubleshoot this. Let's start by checking a few things."
      ],
      scheduling: [
        "I'd be happy to help you schedule an appointment. What time works best for you?",
        "Let me check our availability and find a time that works for you.",
        "I can help you book that appointment. What date and time would you prefer?"
      ]
    };

    const scenarioResponses = responses[scenario as keyof typeof responses] || responses.general;
    return scenarioResponses[Math.floor(Math.random() * scenarioResponses.length)];
  };

  const generateTranscript = (messages: Message[]): string => {
    return messages.map(msg => {
      const timestamp = msg.timestamp.toLocaleTimeString();
      const speaker = msg.type === 'user' ? 'User' : 'Assistant';
      return `[${timestamp}] ${speaker}: ${msg.content}`;
    }).join('\n\n');
  };

  const downloadTranscript = () => {
    if (!testSession?.transcript) return;

    const blob = new Blob([testSession.transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-transcript-${assistant.name}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Transcript downloaded",
      description: "Test transcript has been saved to your device",
      variant: "default"
    });
  };

  const copyTranscript = () => {
    if (!testSession?.transcript) return;

    navigator.clipboard.writeText(testSession.transcript);
    toast({
      title: "Transcript copied",
      description: "Test transcript has been copied to clipboard",
      variant: "default"
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connecting':
        return <div className="h-4 w-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />;
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'ended':
        return <Clock className="h-4 w-4 text-gray-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connecting':
        return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
      case 'active':
        return 'bg-green-500/20 text-green-600 border-green-500/30';
      case 'ended':
        return 'bg-blue-500/20 text-blue-600 border-blue-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-600 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-600 border-gray-500/30';
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden bg-gradient-card border-accent/20 shadow-glow">
        <DialogHeader>
          <DialogTitle className="text-2xl font-playfair text-accent">
            Test Sandbox - {assistant.name}
          </DialogTitle>
          <DialogDescription className="text-gray-600">
            Test your assistant with a short demo conversation and view the transcript
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col h-full">
          {/* Test Configuration */}
          {!testSession && (
            <Card className="mb-6 bg-gradient-card border-accent/20">
              <CardHeader>
                <CardTitle className="text-lg text-accent">Test Configuration</CardTitle>
                <CardDescription>Configure your test session parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="test-mode">Test Mode</Label>
                    <Select value={testMode} onValueChange={(value: 'voice' | 'chat') => setTestMode(value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="voice">Voice Call</SelectItem>
                        <SelectItem value="chat">Text Chat</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="test-scenario">Test Scenario</Label>
                    <Select value={testScenario} onValueChange={setTestScenario}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {testScenarios.map(scenario => (
                          <SelectItem key={scenario.value} value={scenario.value}>
                            {scenario.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button 
                  onClick={startTestSession} 
                  disabled={isLoading}
                  className="w-full bg-gradient-premium text-accent-foreground shadow-accent"
                >
                  {isLoading ? (
                    <>
                      <div className="h-4 w-4 border-2 border-accent-foreground border-t-transparent rounded-full animate-spin mr-2" />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Start Test Session
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Active Test Session */}
          {testSession && (
            <div className="flex flex-col h-full">
              {/* Session Status */}
              <Card className="mb-4 bg-gradient-card border-accent/20">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(testSession.status)}
                      <div>
                        <p className="font-medium text-accent">Test Session Active</p>
                        <p className="text-sm text-gray-600">
                          {testSession.status === 'connecting' && 'Establishing connection...'}
                          {testSession.status === 'active' && `Duration: ${Math.round((Date.now() - testSession.startTime.getTime()) / 1000)}s`}
                          {testSession.status === 'ended' && `Duration: ${testSession.duration}s`}
                          {testSession.status === 'error' && 'Connection failed'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={`${getStatusColor(testSession.status)} border`}>
                        {testSession.status}
                      </Badge>
                      {testSession.status === 'active' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setIsMuted(!isMuted)}
                          className="border-accent/20 hover:border-accent"
                        >
                          {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                        </Button>
                      )}
                      {testSession.status === 'active' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={endTestSession}
                          className="border-accent/20 hover:border-accent"
                        >
                          <Square className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Conversation Area */}
              <div className="flex-1 flex flex-col min-h-0">
                <Tabs defaultValue="conversation" className="flex-1 flex flex-col">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="conversation">Live Conversation</TabsTrigger>
                    <TabsTrigger value="transcript">Transcript</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="conversation" className="flex-1 flex flex-col min-h-0">
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-secondary/20 rounded-lg">
                      {testSession.messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg p-3 ${
                              message.type === 'user'
                                ? 'bg-accent text-accent-foreground'
                                : 'bg-card border border-accent/20'
                            }`}
                          >
                            <div className="flex items-center gap-2 mb-1">
                              {message.type === 'user' ? (
                                <User className="h-4 w-4" />
                              ) : (
                                <Bot className="h-4 w-4" />
                              )}
                              <span className="text-xs text-gray-600">
                                {message.timestamp.toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm">{message.content}</p>
                            {message.metadata && (
                              <div className="mt-2 text-xs text-gray-600">
                                {message.metadata.confidence && (
                                  <span>Confidence: {Math.round(message.metadata.confidence * 100)}%</span>
                                )}
                                {message.metadata.intent && (
                                  <span className="ml-2">Intent: {message.metadata.intent}</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {isLoading && (
                        <div className="flex justify-start">
                          <div className="bg-card border border-accent/20 rounded-lg p-3">
                            <div className="flex items-center gap-2">
                              <Bot className="h-4 w-4" />
                              <div className="flex space-x-1">
                                <div className="h-2 w-2 bg-accent rounded-full animate-bounce"></div>
                                <div className="h-2 w-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                <div className="h-2 w-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Input Area */}
                    {testSession.status === 'active' && testMode === 'chat' && (
                      <div className="mt-4 flex gap-2">
                        <Input
                          value={userInput}
                          onChange={(e) => setUserInput(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && userInput.trim()) {
                              sendMessage(userInput.trim());
                            }
                          }}
                          placeholder="Type your message..."
                          className="flex-1"
                        />
                        <Button
                          onClick={() => userInput.trim() && sendMessage(userInput.trim())}
                          disabled={!userInput.trim() || isLoading}
                          className="bg-gradient-premium text-accent-foreground"
                        >
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                      </div>
                    )}

                    {/* Voice Controls */}
                    {testSession.status === 'active' && testMode === 'voice' && (
                      <div className="mt-4 flex justify-center gap-4">
                        <Button
                          onClick={() => setIsRecording(!isRecording)}
                          disabled={isLoading}
                          className={`${
                            isRecording 
                              ? 'bg-red-500 hover:bg-red-600' 
                              : 'bg-gradient-premium text-accent-foreground'
                          } shadow-accent`}
                        >
                          {isRecording ? <MicOff className="h-4 w-4 mr-2" /> : <Mic className="h-4 w-4 mr-2" />}
                          {isRecording ? 'Stop Recording' : 'Start Recording'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setIsMuted(!isMuted)}
                          className="border-accent/20 hover:border-accent"
                        >
                          {isMuted ? <VolumeX className="h-4 w-4 mr-2" /> : <Volume2 className="h-4 w-4 mr-2" />}
                          {isMuted ? 'Unmute' : 'Mute'}
                        </Button>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="transcript" className="flex-1 flex flex-col min-h-0">
                    <div className="flex-1 overflow-y-auto p-4 bg-secondary/20 rounded-lg">
                      {testSession.transcript ? (
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <h4 className="font-medium text-accent">Test Transcript</h4>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={copyTranscript}
                                className="border-accent/20 hover:border-accent"
                              >
                                <Copy className="h-4 w-4 mr-2" />
                                Copy
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={downloadTranscript}
                                className="border-accent/20 hover:border-accent"
                              >
                                <Download className="h-4 w-4 mr-2" />
                                Download
                              </Button>
                            </div>
                          </div>
                          <div className="bg-card border border-accent/20 rounded-lg p-4">
                            <pre className="text-sm whitespace-pre-wrap font-mono text-gray-600">
                              {testSession.transcript}
                            </pre>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                          <p className="text-gray-600">No transcript available yet</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          )}

          {/* Session Actions */}
          {testSession?.status === 'ended' && (
            <div className="mt-4 flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Session completed • Duration: {testSession.duration}s • Messages: {testSession.messages.length}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setTestSession(null)}
                  className="border-accent/20 hover:border-accent"
                >
                  Start New Test
                </Button>
                <Button
                  onClick={downloadTranscript}
                  className="bg-gradient-premium text-accent-foreground shadow-accent"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Transcript
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TestSandboxDialog; 