import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import heroImage from "@/assets/hero-image.jpg";
import { 
  Phone, 
  MessageSquare, 
  BarChart3, 
  Zap, 
  Users, 
  CreditCard,
  ArrowRight,
  CheckCircle,
  Mic,
  Bot,
  Smartphone,
  Globe
} from "lucide-react";

const Index = () => {
  const features = [
    {
      icon: <Bot className="h-8 w-8" />,
      title: "AI Assistants",
      description: "Create voice, chat, and WhatsApp assistants from proven templates"
    },
    {
      icon: <Users className="h-8 w-8" />,
      title: "Smart Campaigns",
      description: "Launch one-time or recurring campaigns with intelligent scheduling"
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: "Live Analytics",
      description: "Real-time insights on connect rates, outcomes, and sentiment"
    },
    {
      icon: <CreditCard className="h-8 w-8" />,
      title: "Flexible Billing",
      description: "Pay-as-you-go with bundles or recurring plans. No hidden fees."
    }
  ];

  const templates = [
    { name: "Insurance Claims", icon: "🛡️", popular: true },
    { name: "Banking Support", icon: "🏦", popular: true },
    { name: "Real Estate Leads", icon: "🏠", popular: false },
    { name: "Retail Customer Care", icon: "🛍️", popular: false },
    { name: "Church Outreach", icon: "⛪", popular: false },
    { name: "Political Campaigns", icon: "🗳️", popular: false }
  ];

  const channels = [
    { name: "Voice Calls", icon: <Phone className="h-5 w-5" />, desc: "AI-powered voice assistants" },
    { name: "WhatsApp", icon: <MessageSquare className="h-5 w-5" />, desc: "Interactive messaging" },
    { name: "Web Chat", icon: <Globe className="h-5 w-5" />, desc: "Website integration" }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-indigo-600">KasaAI</span>
            </div>
            <div className="hidden md:flex items-center space-x-6">
              <a href="#features" className="text-gray-600 hover:text-foreground transition-colors">Features</a>
              <a href="#templates" className="text-gray-600 hover:text-foreground transition-colors">Templates</a>
              <a href="#pricing" className="text-gray-600 hover:text-foreground transition-colors">Pricing</a>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/auth">Sign In</Link>
              </Button>
              <Button variant="hero" size="sm" asChild>
                <Link to="/auth">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4 bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <div className="container mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <Badge variant="secondary" className="px-3 py-1">
                  <Zap className="h-3 w-3 mr-1" />
                  AI Labs Africa
                </Badge>
                <h1 className="text-4xl md:text-6xl font-bold text-foreground leading-tight">
                  Build AI Assistants
                  <span className="bg-gradient-hero bg-clip-text text-transparent"> That Actually Work</span>
                </h1>
                <p className="text-xl text-gray-600 leading-relaxed">
                  Create voice, chat, and WhatsApp assistants in minutes. Launch smart campaigns, 
                  track real results, and scale your customer engagement with KasaAI's self-serve platform.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button variant="hero" size="lg" className="text-lg px-8" asChild>
                  <Link to="/auth">
                    Start Building Free
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </Link>
                </Button>
                <Button variant="outline" size="lg" className="text-lg px-8">
                  <Mic className="h-5 w-5 mr-2" />
                  Watch Demo
                </Button>
              </div>

              <div className="flex items-center space-x-6 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-accent" />
                  <span>No setup fees</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-accent" />
                  <span>5-minute setup</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-accent" />
                  <span>Free trial included</span>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl">
                <img 
                  src={heroImage} 
                  alt="KasaAI AI Assistant Platform" 
                  className="w-full h-auto"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-primary/20 to-transparent" />
              </div>
              {/* Floating cards */}
              <div className="absolute -top-4 -right-4 bg-card border shadow-lg rounded-lg p-3 animate-bounce">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-xs font-medium">Campaign Active</span>
                </div>
              </div>
              <div className="absolute -bottom-4 -left-4 bg-card border shadow-lg rounded-lg p-3">
                <div className="text-xs text-gray-600">Connect Rate</div>
                <div className="text-lg font-bold text-accent">87%</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Channel Options */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-bold mb-8">Choose Your Channel</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {channels.map((channel, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200 border-2 hover:border-accent/50">
                <CardContent className="pt-6 text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg mb-4">
                    {channel.icon}
                  </div>
                  <h3 className="font-semibold mb-2">{channel.name}</h3>
                  <p className="text-sm text-gray-600">{channel.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything You Need to Scale</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              From templates to analytics, KasaAI provides all the tools to create, 
              deploy, and optimize your AI assistant campaigns.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <CardHeader className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-primary rounded-xl mb-4 mx-auto">
                    <div className="text-white">
                      {feature.icon}
                    </div>
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Templates Section */}
      <section id="templates" className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready-Made Templates</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Start with proven templates designed for your industry. 
              Customize and deploy in minutes, not weeks.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200 relative">
                {template.popular && (
                  <Badge className="absolute -top-3 left-4 bg-accent text-accent-foreground">
                    Popular
                  </Badge>
                )}
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{template.icon}</span>
                    <div>
                      <h3 className="font-semibold">{template.name}</h3>
                      <p className="text-sm text-gray-600">Ready to customize</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="text-center mt-12">
            <Button variant="outline" size="lg">
              View All Templates
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-hero">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Build Your AI Assistant?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join thousands of businesses using KasaAI to automate customer engagement 
            and drive better results with AI-powered conversations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="glass" size="lg" className="text-lg px-8">
              Start Free Trial
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
            <Button variant="outline" size="lg" className="bg-white text-indigo-600 hover:bg-gray-50 text-lg px-8">
              Schedule Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold text-indigo-600">KasaAI</span>
              </div>
              <p className="text-gray-600">
                AI-powered assistant platform for modern businesses.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-600">
                <li><a href="#" className="hover:text-foreground transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Templates</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">API</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-600">
                <li><a href="#" className="hover:text-foreground transition-colors">About</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-600">
                <li><a href="#" className="hover:text-foreground transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Status</a></li>
                <li><a href="#" className="hover:text-foreground transition-colors">Privacy</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border mt-8 pt-8 text-center text-gray-600">
            <p>&copy; 2024 AI Labs Africa. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;