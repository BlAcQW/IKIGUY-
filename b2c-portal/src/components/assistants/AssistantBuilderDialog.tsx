import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Plus, MessageSquare, Phone, MessageCircle, Mic, Globe, Zap, Users, Clock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useConfirmationHelpers } from '@/hooks/use-confirmation';

interface AssistantBuilderDialogProps {
  onAssistantCreated: (assistant: any) => void;
}

const TEMPLATES = [
  {
    id: "sales",
    name: "Sales Assistant",
    description: "Engage prospects, qualify leads, and book appointments",
    icon: Zap,
    features: ["Lead qualification", "Appointment booking", "Follow-up automation"],
    channels: ["voice", "chat"],
  },
  {
    id: "faq",
    name: "FAQ Support",
    description: "Answer common questions and provide instant support",
    icon: MessageSquare,
    features: ["Knowledge base", "Instant responses", "Escalation handling"],
    channels: ["chat", "voice", "whatsapp"],
  },
  {
    id: "reminder",
    name: "Reminder Assistant",
    description: "Send scheduled reminders and follow-ups",
    icon: Clock,
    features: ["Scheduled calls", "Payment reminders", "Appointment confirmations"],
    channels: ["voice", "whatsapp"],
  },
  {
    id: "custom",
    name: "Custom Assistant",
    description: "Build your own assistant from scratch",
    icon: Users,
    features: ["Full customization", "Custom prompts", "Advanced settings"],
    channels: ["voice", "chat", "whatsapp"],
  },
];

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
];

const VOICES = [
  { id: "sarah", name: "Sarah", description: "Professional, clear" },
  { id: "david", name: "David", description: "Warm, friendly" },
  { id: "emma", name: "Emma", description: "Energetic, youthful" },
  { id: "michael", name: "Michael", description: "Authoritative, confident" },
];

export const AssistantBuilderDialog = ({ onAssistantCreated }: AssistantBuilderDialogProps) => {
  const [open, setOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: "",
    template: "",
    channel: "",
    language: "en",
    voice: "sarah",
    prompt: "",
    enableConsent: true,
    enableGrounding: true,
  });
  const { toast } = useToast();
  const { confirmCancel, ConfirmationDialog } = useConfirmationHelpers();

  const handleTemplateSelect = (templateId: string) => {
    const template = TEMPLATES.find(t => t.id === templateId);
    setSelectedTemplate(templateId);
    setFormData(prev => ({ 
      ...prev, 
      template: templateId,
      name: template?.name || "",
      prompt: getTemplatePrompt(templateId),
    }));
    setStep(2);
  };

  const getTemplatePrompt = (templateId: string) => {
    const prompts = {
      sales: "You are a professional sales assistant. Your goal is to engage prospects, qualify leads, and book appointments. Be friendly but focused, ask qualifying questions, and guide conversations toward scheduling a meeting.",
      faq: "You are a helpful support assistant. Answer customer questions clearly and accurately using the provided knowledge base. If you don't know something, acknowledge it and offer to connect them with a human agent.",
      reminder: "You are a reminder assistant. Make professional, courteous calls and messages to remind people about appointments, payments, or other scheduled items. Be brief and to the point.",
      custom: "",
    };
    return prompts[templateId as keyof typeof prompts] || "";
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.template || !formData.channel) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    const newAssistant = {
      id: `assistant-${Date.now()}`,
      ...formData,
      status: "draft",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    onAssistantCreated(newAssistant);
    toast({
      title: "Assistant Created",
      description: `${formData.name} has been created successfully.`,
    });

    // Reset form
    resetForm();
    setOpen(false);
  };

  const hasUnsavedChanges = () => {
    return (
      formData.name.trim() !== '' ||
      formData.template !== '' ||
      formData.channel !== '' ||
      formData.prompt.trim() !== '' ||
      step > 1
    );
  };

  const resetForm = () => {
    setStep(1);
    setSelectedTemplate('');
    setFormData({
      name: '',
      template: '',
      channel: '',
      language: 'en',
      voice: 'sarah',
      prompt: '',
      enableConsent: true,
      enableGrounding: true,
    });
  };

  const handleCancel = async () => {
    if (hasUnsavedChanges()) {
      const confirmed = await confirmCancel();
      if (confirmed) {
        resetForm();
        setOpen(false);
      }
    } else {
      setOpen(false);
    }
  };

  const renderChannelIcon = (channel: string) => {
    switch (channel) {
      case "voice": return <Phone className="h-4 w-4" />;
      case "chat": return <MessageSquare className="h-4 w-4" />;
      case "whatsapp": return <MessageCircle className="h-4 w-4" />;
      default: return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Create Assistant
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Assistant</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Choose a Template</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TEMPLATES.map((template) => {
                  const Icon = template.icon;
                  return (
                    <Card
                      key={template.id}
                      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
                      onClick={() => handleTemplateSelect(template.id)}
                    >
                      <CardHeader>
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-primary/10">
                            <Icon className="h-5 w-5 text-indigo-600" />
                          </div>
                          <div>
                            <CardTitle className="text-base">{template.name}</CardTitle>
                            <CardDescription className="text-sm">
                              {template.description}
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm font-medium mb-2">Features:</p>
                            <div className="flex flex-wrap gap-1">
                              {template.features.map((feature) => (
                                <Badge key={feature} variant="secondary" className="text-xs">
                                  {feature}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-sm font-medium mb-2">Channels:</p>
                            <div className="flex gap-2">
                              {template.channels.map((channel) => (
                                <div key={channel} className="flex items-center gap-1 text-xs text-gray-600">
                                  {renderChannelIcon(channel)}
                                  {channel}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <h3 className="text-lg font-semibold">Configure Your Assistant</h3>
            </div>

            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="channel">Channel</TabsTrigger>
                <TabsTrigger value="voice">Voice</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Assistant Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter assistant name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    <Select value={formData.language} onValueChange={(value) => setFormData(prev => ({ ...prev, language: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LANGUAGES.map((lang) => (
                          <SelectItem key={lang.code} value={lang.code}>
                            {lang.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="prompt">Custom Instructions</Label>
                  <Textarea
                    id="prompt"
                    value={formData.prompt}
                    onChange={(e) => setFormData(prev => ({ ...prev, prompt: e.target.value }))}
                    placeholder="Add custom instructions for your assistant..."
                    rows={4}
                  />
                </div>
              </TabsContent>

              <TabsContent value="channel" className="space-y-4">
                <div className="space-y-4">
                  <div>
                    <Label>Select Channel</Label>
                    <div className="grid grid-cols-3 gap-4 mt-2">
                      {["voice", "chat", "whatsapp"].map((channel) => (
                        <Card
                          key={channel}
                          className={`cursor-pointer transition-all ${
                            formData.channel === channel ? "border-primary bg-primary/5" : ""
                          }`}
                          onClick={() => setFormData(prev => ({ ...prev, channel }))}
                        >
                          <CardContent className="p-4 text-center">
                            <div className="flex flex-col items-center gap-2">
                              {renderChannelIcon(channel)}
                              <span className="text-sm font-medium capitalize">{channel}</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="voice" className="space-y-4">
                <div className="space-y-2">
                  <Label>Voice Selection</Label>
                  <div className="grid grid-cols-2 gap-4">
                    {VOICES.map((voice) => (
                      <Card
                        key={voice.id}
                        className={`cursor-pointer transition-all ${
                          formData.voice === voice.id ? "border-primary bg-primary/5" : ""
                        }`}
                        onClick={() => setFormData(prev => ({ ...prev, voice: voice.id }))}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center gap-3">
                            <Mic className="h-5 w-5 text-indigo-600" />
                            <div>
                              <p className="font-medium">{voice.name}</p>
                              <p className="text-sm text-gray-600">{voice.description}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="consent">Enable Consent Prompts</Label>
                      <p className="text-sm text-gray-600">Ask for consent before recording or storing data</p>
                    </div>
                    <Switch
                      id="consent"
                      checked={formData.enableConsent}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, enableConsent: checked }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="grounding">Enable Grounding</Label>
                      <p className="text-sm text-gray-600">Only provide answers based on knowledge base</p>
                    </div>
                    <Switch
                      id="grounding"
                      checked={formData.enableGrounding}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, enableGrounding: checked }))}
                    />
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                Create Assistant
              </Button>
            </div>
          </div>
        )}
      </DialogContent>

      {/* Confirmation Dialog */}
      <ConfirmationDialog />
    </Dialog>
  );
};