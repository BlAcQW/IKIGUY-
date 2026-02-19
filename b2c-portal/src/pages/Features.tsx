import React from 'react';
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowRight, 
  Bot, 
  Phone, 
  MessageSquare, 
  BarChart3,
  Users,
  Zap,
  Shield,
  Globe,
  Smartphone,
  Headphones,
  Clock,
  Target,
  Mic,
  Database,
  Settings,
  CheckCircle
} from "lucide-react";

const Features = () => {
  const mainFeatures = [
    {
      icon: <Bot className="h-12 w-12" />,
      title: "AI Assistant Builder",
      description: "Create intelligent voice, chat, and WhatsApp assistants using proven templates",
      features: ["Drag-and-drop interface", "50+ pre-built templates", "Custom conversation flows", "Multi-language support"]
    },
    {
      icon: <MessageSquare className="h-12 w-12" />,
      title: "Smart Campaigns",
      description: "Launch and manage automated outreach campaigns with intelligent scheduling",
      features: ["Bulk contact import", "Smart scheduling", "A/B testing", "Automated follow-ups"]
    },
    {
      icon: <BarChart3 className="h-12 w-12" />,
      title: "Real-time Analytics",
      description: "Comprehensive insights into campaign performance and customer interactions",
      features: ["Live dashboard", "Sentiment analysis", "Conversion tracking", "Custom reports"]
    },
    {
      icon: <Users className="h-12 w-12" />,
      title: "Audience Management",
      description: "Organize and segment your contacts for targeted campaigns",
      features: ["Smart segmentation", "CRM integration", "Contact scoring", "List management"]
    }
  ];

  const channels = [
    {
      icon: <Phone className="h-8 w-8" />,
      title: "Voice Calls",
      description: "Natural-sounding AI voice assistants for phone calls",
      capabilities: ["Human-like conversations", "Multiple voice options", "Real-time responses", "Call recording"]
    },
    {
      icon: <MessageSquare className="h-8 w-8" />,
      title: "WhatsApp Business",
      description: "Automated messaging through WhatsApp Business API",
      capabilities: ["Rich media support", "Quick replies", "Broadcast lists", "Template messages"]
    },
    {
      icon: <Globe className="h-8 w-8" />,
      title: "Web Chat",
      description: "Embeddable chat widgets for your website",
      capabilities: ["Customizable UI", "Visitor tracking", "File sharing", "Live handoff"]
    }
  ];

  const advanced = [
    {
      icon: <Shield className="h-6 w-6" />,
      title: "Enterprise Security",
      description: "Bank-level encryption and compliance"
    },
    {
      icon: <Database className="h-6 w-6" />,
      title: "CRM Integration", 
      description: "Sync with Salesforce, HubSpot, and more"
    },
    {
      icon: <Settings className="h-6 w-6" />,
      title: "Custom Workflows",
      description: "Build complex automation rules"
    },
    {
      icon: <Target className="h-6 w-6" />,
      title: "Lead Scoring",
      description: "AI-powered lead qualification"
    },
    {
      icon: <Clock className="h-6 w-6" />,
      title: "Scheduling Integration",
      description: "Calendar booking and reminders"
    },
    {
      icon: <Headphones className="h-6 w-6" />,
      title: "Live Agent Handoff",
      description: "Seamless transfer to human agents"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-indigo-600">KasaAI</span>
            </Link>
            <div className="hidden md:flex items-center space-x-6">
              <Link to="/features" className="text-foreground font-medium">Features</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-foreground transition-colors">Pricing</Link>
              <Link to="/about" className="text-gray-600 hover:text-foreground transition-colors">About</Link>
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
        <div className="container mx-auto max-w-4xl text-center">
          <Badge variant="secondary" className="px-3 py-1 mb-6">
            <Zap className="h-3 w-3 mr-1" />
            Powerful Features
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
            Everything You Need to Build
            <span className="bg-gradient-hero bg-clip-text text-transparent"> Intelligent Assistants</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            From simple chatbots to sophisticated voice assistants, KasaAI provides 
            all the tools you need to create, deploy, and optimize AI-powered customer interactions.
          </p>
          <Button variant="hero" size="lg" className="text-lg px-8" asChild>
            <Link to="/auth">
              Start Building Now
              <ArrowRight className="h-5 w-5 ml-2" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Core Features</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to create, deploy, and optimize AI assistants
            </p>
          </div>
          <div className="grid lg:grid-cols-2 gap-12">
            {mainFeatures.map((feature, index) => (
              <Card key={index} className="hover:shadow-xl transition-all duration-300">
                <CardHeader>
                  <div className="flex items-start space-x-4">
                    <div className="bg-gradient-primary rounded-xl p-3">
                      <div className="text-white">
                        {feature.icon}
                      </div>
                    </div>
                    <div>
                      <CardTitle className="text-xl mb-2">{feature.title}</CardTitle>
                      <CardDescription className="text-base">{feature.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feature.features.map((item, idx) => (
                      <li key={idx} className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-accent mr-3 flex-shrink-0" />
                        <span className="text-sm">{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Channels Section */}
      <section className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Multi-Channel Support</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Deploy your AI assistants across multiple communication channels
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {channels.map((channel, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardHeader className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-primary rounded-xl mb-4 mx-auto">
                    <div className="text-white">
                      {channel.icon}
                    </div>
                  </div>
                  <CardTitle className="text-lg">{channel.title}</CardTitle>
                  <CardDescription>{channel.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {channel.capabilities.map((capability, idx) => (
                      <li key={idx} className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-accent mr-3 flex-shrink-0" />
                        <span className="text-sm">{capability}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Advanced Features */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Advanced Capabilities</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Enterprise-grade features for sophisticated automation
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {advanced.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardContent className="p-6">
                  <div className="flex items-start space-x-3">
                    <div className="bg-primary/10 rounded-lg p-2">
                      <div className="text-indigo-600">
                        {feature.icon}
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{feature.title}</h3>
                      <p className="text-sm text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            See KasaAI in Action
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Watch how easy it is to create and deploy AI assistants
          </p>
          <div className="bg-gradient-to-br from-primary/10 to-accent/10 rounded-2xl p-12">
            <div className="text-8xl mb-6">🎬</div>
            <Button variant="hero" size="lg" className="text-lg px-8">
              <Mic className="h-5 w-5 mr-2" />
              Watch Interactive Demo
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
          <p className="text-xl text-white/90 mb-8">
            Start your free trial today and see how KasaAI can transform your business
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="glass" size="lg" className="text-lg px-8" asChild>
              <Link to="/auth">
                Start Free Trial
                <ArrowRight className="h-5 w-5 ml-2" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="bg-white text-indigo-600 hover:bg-gray-50 text-lg px-8" asChild>
              <Link to="/pricing">
                View Pricing
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Features;