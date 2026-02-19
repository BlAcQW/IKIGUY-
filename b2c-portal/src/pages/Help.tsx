import React, { useState } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BookOpen,
  Search,
  HelpCircle,
  FileText,
  Video,
  Mail,
  MessageCircle,
  Phone,
  Code,
  Zap,
  Settings,
  Users,
  Mic,
  Bot,
  BarChart,
  CreditCard,
  Key,
  Shield,
  ExternalLink,
  ChevronRight,
  Play
} from 'lucide-react';

const Help: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const features = [
    {
      icon: Bot,
      title: 'Voice Agents',
      description: 'Create and deploy AI-powered voice agents for automated conversations',
      link: '/voice-agent',
      topics: ['Creating agents', 'Configuring prompts', 'Testing calls', 'Deployment']
    },
    {
      icon: Zap,
      title: 'Automations',
      description: 'Build automated workflows with VAPI and N8N integrations',
      link: '/automations',
      topics: ['Templates', 'Quick deploy', 'Campaign management', 'Analytics']
    },
    {
      icon: Mic,
      title: 'Voice Labs',
      description: 'Test and experiment with TTS, STT, and voice cloning',
      link: '/tts-lab',
      topics: ['Text-to-Speech', 'Speech-to-Text', 'Voice cloning', 'Audio processing']
    },
    {
      icon: Users,
      title: 'Audiences',
      description: 'Manage and segment your contact lists for targeted campaigns',
      link: '/audiences',
      topics: ['Creating audiences', 'Importing contacts', 'Segmentation', 'Management']
    },
    {
      icon: BarChart,
      title: 'Analytics',
      description: 'Track performance and monitor automation metrics',
      link: '/analytics',
      topics: ['Call logs', 'Usage metrics', 'Cost analytics', 'Performance reports']
    },
    {
      icon: CreditCard,
      title: 'Billing',
      description: 'Manage your wallet, payments, and service costs',
      link: '/billing',
      topics: ['Top-up balance', 'Payment methods', 'Cost breakdown', 'Transaction history']
    }
  ];

  const faqs = [
    {
      question: 'How do I create my first voice agent?',
      answer: 'Navigate to Voice Agent from the sidebar, click "Create New Agent", configure your system prompt, select voice and model settings, then save and test your agent.'
    },
    {
      question: 'What payment methods are supported?',
      answer: 'We support multiple payment methods including Stripe (credit/debit cards), Flutterwave, MTN Mobile Money, Vodafone Cash, AirtelTigo Money, and M-Pesa.'
    },
    {
      question: 'How is billing calculated?',
      answer: 'Billing is based on actual usage across services: Telephony (call minutes), Speech-to-Text (transcription calls), Text-to-Speech (synthesis calls), and Automation (execution count). View detailed cost breakdown on the Billing page.'
    },
    {
      question: 'Can I integrate with external tools?',
      answer: 'Yes! KasaAI supports integrations with VAPI, N8N, HubSpot, Zendesk, and many other platforms. Visit the Integrations page to explore available options.'
    },
    {
      question: 'How do I deploy an automation?',
      answer: 'Use Quick Deploy for rapid setup, or go to Automations → Select Template → Configure settings → Choose audience → Deploy. Monitor performance in Analytics.'
    },
    {
      question: 'What languages are supported for voice agents?',
      answer: 'Our TTS and STT services support multiple languages including English, Twi, Ga, Ewe, and other African languages. Check the Voice Labs for available options.'
    },
    {
      question: 'How do I top up my wallet?',
      answer: 'Go to Billing → Add Credits → Select amount or enter custom amount → Choose payment method → Complete payment. Credits are added instantly.'
    },
    {
      question: 'Can I test automations before deploying?',
      answer: 'Yes! All automation configurations include a test mode where you can validate settings and run test scenarios before full deployment.'
    }
  ];

  const quickLinks = [
    { title: 'API Documentation', icon: Code, href: '/api-keys' },
    { title: 'Voice Agent Setup', icon: Bot, href: '/voice-agent' },
    { title: 'Quick Deploy Guide', icon: Zap, href: '/quick-deploy' },
    { title: 'Billing & Payments', icon: CreditCard, href: '/billing' },
    { title: 'Account Settings', icon: Settings, href: '/settings' },
    { title: 'Integration Guide', icon: Key, href: '/integrations' }
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <DashboardSidebar />
        <main className="flex-1 p-6">
          <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Help Center</h1>
            <p className="text-gray-600 mt-1">
              Everything you need to know about using KasaAI Voice AI Platform
            </p>
          </div>

          {/* Search Bar */}
          <Card>
            <CardContent className="p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  placeholder="Search for help articles, guides, or FAQs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="getting-started" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="getting-started">Getting Started</TabsTrigger>
            <TabsTrigger value="features">Features</TabsTrigger>
            <TabsTrigger value="faq">FAQ</TabsTrigger>
            <TabsTrigger value="support">Support</TabsTrigger>
          </TabsList>

          {/* Getting Started Tab */}
          <TabsContent value="getting-started" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-primary" />
                  Quick Start Guide
                </CardTitle>
                <CardDescription>
                  Get up and running with KasaAI in minutes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                    <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-bold">
                      1
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">Set Up Your Account</h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Complete your profile, add payment method, and top up your wallet with credits.
                      </p>
                      <Button variant="link" className="p-0 h-auto text-blue-600">
                        Go to Settings <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-100">
                    <div className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-bold">
                      2
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">Create Your First Voice Agent</h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Build an AI voice agent with custom prompts, voice selection, and model configuration.
                      </p>
                      <Button variant="link" className="p-0 h-auto text-purple-600">
                        Create Agent <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-100">
                    <div className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-bold">
                      3
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">Deploy an Automation</h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Use Quick Deploy to launch pre-built automation templates for common use cases.
                      </p>
                      <Button variant="link" className="p-0 h-auto text-green-600">
                        Quick Deploy <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-100">
                    <div className="bg-orange-600 text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-bold">
                      4
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">Monitor & Optimize</h3>
                      <p className="text-sm text-gray-600 mb-2">
                        Track performance, analyze costs, and optimize your automations using Analytics.
                      </p>
                      <Button variant="link" className="p-0 h-auto text-orange-600">
                        View Analytics <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Links</CardTitle>
                <CardDescription>Jump to commonly accessed features</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {quickLinks.map((link, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="justify-start h-auto py-3"
                      onClick={() => window.location.href = link.href}
                    >
                      <link.icon className="h-4 w-4 mr-2" />
                      {link.title}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Features Tab */}
          <TabsContent value="features" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {features.map((feature, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-lg">
                        <feature.icon className="h-5 w-5 text-white" />
                      </div>
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                    </div>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Topics covered:</p>
                        <div className="flex flex-wrap gap-2">
                          {feature.topics.map((topic, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button variant="link" className="p-0 h-auto w-full justify-start text-primary">
                        Learn more <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Video Tutorials Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="h-5 w-5 text-primary" />
                  Video Tutorials
                </CardTitle>
                <CardDescription>Watch step-by-step video guides</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="border rounded-lg p-4 hover:border-primary transition-colors cursor-pointer">
                    <div className="bg-gray-100 rounded-lg h-32 flex items-center justify-center mb-3">
                      <Play className="h-12 w-12 text-gray-400" />
                    </div>
                    <h4 className="font-semibold text-sm mb-1">Creating Your First Agent</h4>
                    <p className="text-xs text-gray-600">5:30 min</p>
                  </div>
                  <div className="border rounded-lg p-4 hover:border-primary transition-colors cursor-pointer">
                    <div className="bg-gray-100 rounded-lg h-32 flex items-center justify-center mb-3">
                      <Play className="h-12 w-12 text-gray-400" />
                    </div>
                    <h4 className="font-semibold text-sm mb-1">Deploying Automations</h4>
                    <p className="text-xs text-gray-600">8:15 min</p>
                  </div>
                  <div className="border rounded-lg p-4 hover:border-primary transition-colors cursor-pointer">
                    <div className="bg-gray-100 rounded-lg h-32 flex items-center justify-center mb-3">
                      <Play className="h-12 w-12 text-gray-400" />
                    </div>
                    <h4 className="font-semibold text-sm mb-1">Voice Cloning Tutorial</h4>
                    <p className="text-xs text-gray-600">6:45 min</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* FAQ Tab */}
          <TabsContent value="faq" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HelpCircle className="h-5 w-5 text-primary" />
                  Frequently Asked Questions
                </CardTitle>
                <CardDescription>
                  Find quick answers to common questions
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {faqs.map((faq, index) => (
                  <div key={index} className="border-b last:border-b-0 pb-4 last:pb-0">
                    <h3 className="font-semibold text-gray-900 mb-2">{faq.question}</h3>
                    <p className="text-sm text-gray-600">{faq.answer}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Support Tab */}
          <TabsContent value="support" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <div className="bg-blue-100 p-3 rounded-lg w-fit mb-2">
                    <Mail className="h-6 w-6 text-blue-600" />
                  </div>
                  <CardTitle>Email Support</CardTitle>
                  <CardDescription>Get help via email</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-3">
                    Send us an email and we'll respond within 24 hours.
                  </p>
                  <Button className="w-full" variant="outline">
                    <Mail className="h-4 w-4 mr-2" />
                    support@ailabsafrica.com
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="bg-green-100 p-3 rounded-lg w-fit mb-2">
                    <MessageCircle className="h-6 w-6 text-green-600" />
                  </div>
                  <CardTitle>Live Chat</CardTitle>
                  <CardDescription>Chat with our team</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-3">
                    Available Monday to Friday, 9 AM - 6 PM GMT
                  </p>
                  <Button className="w-full">
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Start Chat
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="bg-purple-100 p-3 rounded-lg w-fit mb-2">
                    <FileText className="h-6 w-6 text-purple-600" />
                  </div>
                  <CardTitle>Documentation</CardTitle>
                  <CardDescription>Developer resources</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-3">
                    Comprehensive API docs and integration guides
                  </p>
                  <Button className="w-full" variant="outline">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Docs
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Additional Resources */}
            <Card>
              <CardHeader>
                <CardTitle>Additional Resources</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    Security & Privacy Policy
                  </span>
                  <ExternalLink className="h-4 w-4" />
                </Button>
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Terms of Service
                  </span>
                  <ExternalLink className="h-4 w-4" />
                </Button>
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    API Reference
                  </span>
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Help;
