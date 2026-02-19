import { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  Building2,
  Search,
  FileText,
  Calendar,
  Phone,
  Loader2
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const suggestedPrompts = [
  { icon: Search, text: "Find me a 3-bed apartment under $500k near good schools" },
  { icon: FileText, text: "Generate a listing description for my new property" },
  { icon: Calendar, text: "Schedule property tours for my hot leads this week" },
  { icon: Building2, text: "Create a market analysis for downtown properties" },
];

const initialMessages: Message[] = [
  {
    id: "1",
    role: "assistant",
    content: "Hello! I'm your AI property assistant. I can help you with:\n\n• **Property Search** - Find listings using natural language\n• **Listing Enhancement** - Generate compelling descriptions\n• **Document Creation** - Lease agreements, contracts, etc.\n• **Lead Management** - Follow-ups and scheduling\n• **Market Analysis** - Get insights on any area\n\nHow can I help you today?",
    timestamp: new Date(),
  },
];

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const responses: Record<string, string> = {
        default: "I understand you're looking for help with that. Let me analyze your request and provide you with the best options. Based on our current listings and market data, here are some recommendations...",
      };

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: input.toLowerCase().includes("3-bed") || input.toLowerCase().includes("apartment")
          ? "Great! I found **12 properties** matching your criteria:\n\n🏠 **Sunrise Heights Apartment**\n• 3 beds, 2 baths | 1,450 sqft\n• $485,000 | Near Lincoln Elementary (9/10)\n\n🏠 **Park View Residence**\n• 3 beds, 2.5 baths | 1,620 sqft\n• $498,000 | Near Roosevelt Academy (8/10)\n\n🏠 **Garden District Condo**\n• 3 beds, 2 baths | 1,380 sqft\n• $465,000 | Near Washington Primary (9/10)\n\nWould you like me to schedule tours for any of these properties?"
          : input.toLowerCase().includes("description") || input.toLowerCase().includes("listing")
          ? "I'd be happy to help create a compelling listing description! Please share:\n\n1. **Property type** (apartment, house, condo)\n2. **Key features** (bedrooms, bathrooms, special amenities)\n3. **Location highlights**\n4. **Target audience** (families, investors, first-time buyers)\n\nOr if you'd like, share the property address and I'll pull the details automatically."
          : responses.default,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handlePromptClick = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header 
        title="AI Chat Assistant" 
        subtitle="Your intelligent property management companion"
        showSearch={false}
      />

      <div className="flex-1 flex">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 animate-slide-up ${
                  message.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                <div
                  className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${
                    message.role === "assistant"
                      ? "bg-gradient-to-br from-accent to-orange-600"
                      : "bg-primary"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <Bot className="h-5 w-5 text-white" />
                  ) : (
                    <User className="h-5 w-5 text-primary-foreground" />
                  )}
                </div>
                <div
                  className={`max-w-2xl rounded-2xl px-5 py-4 ${
                    message.role === "assistant"
                      ? "bg-card border border-border"
                      : "bg-primary text-primary-foreground"
                  }`}
                >
                  <div 
                    className={`text-sm leading-relaxed whitespace-pre-wrap ${
                      message.role === "assistant" ? "text-foreground" : ""
                    }`}
                    dangerouslySetInnerHTML={{ 
                      __html: message.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br/>')
                    }}
                  />
                  <p
                    className={`text-xs mt-2 ${
                      message.role === "assistant"
                        ? "text-muted-foreground"
                        : "text-primary-foreground/70"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4 animate-slide-up">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-accent to-orange-600">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <div className="bg-card border border-border rounded-2xl px-5 py-4">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompts */}
          {messages.length === 1 && (
            <div className="px-6 pb-4">
              <p className="text-sm text-muted-foreground mb-3">Try asking:</p>
              <div className="grid grid-cols-2 gap-3">
                {suggestedPrompts.map((prompt, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="justify-start gap-3 h-auto py-3 px-4 text-left"
                    onClick={() => handlePromptClick(prompt.text)}
                  >
                    <prompt.icon className="h-4 w-4 text-accent flex-shrink-0" />
                    <span className="text-sm">{prompt.text}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t border-border p-4 bg-background">
            <div className="flex gap-3 max-w-4xl mx-auto">
              <div className="flex-1 relative">
                <Input
                  placeholder="Ask me anything about properties, leads, or documents..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  className="pr-12 h-12 text-base"
                />
                <Button
                  size="icon"
                  variant="accent"
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9 w-9"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-3">
              AI can make mistakes. Always verify important information.
            </p>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 border-l border-border bg-secondary/30 p-4 space-y-4 hidden xl:block">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-accent" />
                AI Capabilities
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { name: "Property Search", desc: "Natural language queries" },
                { name: "Content Generation", desc: "Listings, emails, ads" },
                { name: "Document Automation", desc: "Contracts, agreements" },
                { name: "Lead Management", desc: "Follow-ups, scheduling" },
                { name: "Market Analysis", desc: "Trends and insights" },
              ].map((cap) => (
                <div key={cap.name} className="flex items-start gap-3 p-2 rounded-lg hover:bg-secondary transition-colors">
                  <div className="h-2 w-2 rounded-full bg-success mt-1.5" />
                  <div>
                    <p className="text-sm font-medium text-foreground">{cap.name}</p>
                    <p className="text-xs text-muted-foreground">{cap.desc}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Recent Conversations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                "Property search: Downtown apartments",
                "Generated listing for 123 Oak St",
                "Scheduled 5 property tours",
              ].map((conv, i) => (
                <Button key={i} variant="ghost" className="w-full justify-start text-sm h-auto py-2">
                  {conv}
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
