import { 
  Sparkles, 
  FileText, 
  PenTool, 
  Share2, 
  Briefcase,
  FileCheck,
  Wrench,
  MessageSquare,
  ArrowRight,
  Zap
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

const aiTools = [
  {
    id: "listing-enhancer",
    name: "AI Listing Enhancer",
    description: "Generate high-performing property descriptions, titles, and marketing copy automatically.",
    icon: PenTool,
    features: [
      "SEO-optimized descriptions",
      "Social media ad copy",
      "Email marketing content",
      "Target audience customization",
    ],
    color: "text-accent",
    bg: "bg-accent/10",
    popular: true,
  },
  {
    id: "document-automation",
    name: "Document Automation",
    description: "Generate lease agreements, offer letters, and contracts with auto-populated fields.",
    icon: FileText,
    features: [
      "Lease agreements",
      "Rental applications",
      "Inspection checklists",
      "Tenant screening summaries",
    ],
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    popular: false,
  },
  {
    id: "property-manager",
    name: "Property Manager Assistant",
    description: "Automate tenant communications, maintenance requests, and follow-ups.",
    icon: Wrench,
    features: [
      "Maintenance request handling",
      "Vendor assignment",
      "Invoice generation",
      "Automated follow-ups",
    ],
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    popular: false,
  },
  {
    id: "smart-search",
    name: "Smart Property Search",
    description: "Natural language search with AI-powered matching and alternatives.",
    icon: Sparkles,
    features: [
      "Natural language queries",
      "Intent-based scoring",
      "Smart alternatives",
      "Preference learning",
    ],
    color: "text-purple-500",
    bg: "bg-purple-500/10",
    popular: true,
  },
  {
    id: "social-generator",
    name: "Social Content Generator",
    description: "Create engaging social media posts and ad campaigns for your listings.",
    icon: Share2,
    features: [
      "Instagram/Facebook posts",
      "Story templates",
      "Hashtag optimization",
      "A/B test variants",
    ],
    color: "text-pink-500",
    bg: "bg-pink-500/10",
    popular: false,
  },
  {
    id: "contract-analyzer",
    name: "Contract Analyzer",
    description: "AI-powered contract review and risk identification.",
    icon: FileCheck,
    features: [
      "Clause analysis",
      "Risk identification",
      "Compliance checking",
      "Summary generation",
    ],
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    popular: false,
  },
];

const recentActivity = [
  { action: "Generated listing for 'Luxury Penthouse Suite'", time: "5 min ago", tool: "Listing Enhancer" },
  { action: "Created lease agreement for Mike Johnson", time: "1 hour ago", tool: "Document Automation" },
  { action: "Processed 12 maintenance requests", time: "3 hours ago", tool: "Property Manager" },
  { action: "Generated 5 social posts for new listings", time: "Yesterday", tool: "Social Generator" },
];

export default function AIAssistant() {
  return (
    <div className="min-h-screen">
      <Header 
        title="AI Assistant" 
        subtitle="Powerful AI tools for property management"
        showSearch={false}
      />

      <div className="p-6 space-y-6">
        {/* Hero Section */}
        <Card className="gradient-primary text-white overflow-hidden relative">
          <div className="absolute inset-0 opacity-50" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='30' height='30' viewBox='0 0 30 30' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='1.5' cy='1.5' r='1.5' fill='rgba(255,255,255,0.07)'/%3E%3C/svg%3E\")" }} />
          <CardContent className="p-8 relative">
            <div className="flex items-center gap-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-sm">
                <Sparkles className="h-8 w-8" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold">AI-Powered Property Management</h2>
                <p className="text-white/80 mt-1 max-w-xl">
                  Save hours every week with intelligent automation. Generate content, 
                  manage documents, and streamline operations with AI.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link to="/ai-chat">
                  <Button variant="glass" size="lg" className="gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Open AI Chat
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Tools Grid */}
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-4">AI Tools</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {aiTools.map((tool) => (
              <Card key={tool.id} variant="interactive" className="relative overflow-hidden group">
                {tool.popular && (
                  <Badge variant="accent" className="absolute top-4 right-4">
                    Popular
                  </Badge>
                )}
                <CardHeader>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${tool.bg} mb-2`}>
                    <tool.icon className={`h-6 w-6 ${tool.color}`} />
                  </div>
                  <CardTitle className="text-lg">{tool.name}</CardTitle>
                  <CardDescription>{tool.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-4">
                    {tool.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Zap className="h-3 w-3 text-accent" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button variant="outline" className="w-full group-hover:bg-accent group-hover:text-accent-foreground group-hover:border-accent transition-colors">
                    Open Tool
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent AI Activity</CardTitle>
            <CardDescription>Latest actions performed by AI tools</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-center gap-4 p-3 rounded-xl bg-secondary/50"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                    <Sparkles className="h-5 w-5 text-accent" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{activity.action}</p>
                    <p className="text-xs text-muted-foreground">{activity.time}</p>
                  </div>
                  <Badge variant="muted">{activity.tool}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
