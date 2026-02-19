import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from '@/components/ui/accordion';
import { 
  Search, 
  HelpCircle, 
  MessageSquare, 
  Phone, 
  Bot, 
  CreditCard, 
  Shield, 
  Zap,
  Globe,
  Mail,
  Calendar
} from 'lucide-react';
import { Link } from 'react-router-dom';

const FAQ = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', label: 'All Categories', icon: HelpCircle },
    { id: 'general', label: 'General', icon: Globe },
    { id: 'assistants', label: 'AI Assistants', icon: Bot },
    { id: 'pricing', label: 'Pricing & Billing', icon: CreditCard },
    { id: 'technical', label: 'Technical', icon: Zap },
    { id: 'security', label: 'Security & Privacy', icon: Shield },
    { id: 'support', label: 'Support', icon: MessageSquare }
  ];

  const faqData = [
    {
      id: 1,
      category: 'general',
      question: 'What is AI Labs Africa?',
      answer: 'AI Labs Africa is a leading AI innovation company that specializes in creating intelligent voice and chat assistants for African businesses. We build AI solutions that understand local contexts, languages, and business needs across various industries including banking, insurance, healthcare, and retail.'
    },
    {
      id: 2,
      category: 'general',
      question: 'What industries do you serve?',
      answer: 'We serve a wide range of industries including Banking & Finance, Insurance, Healthcare, Real Estate, Retail & E-commerce, Professional Services, Education, and Government sectors. Our AI assistants are customized for each industry\'s specific needs and requirements.'
    },
    {
      id: 3,
      category: 'assistants',
      question: 'How do I create an AI assistant?',
      answer: 'Creating an AI assistant is simple! Click "Get Started" on our homepage or visit the "Create Assistant" page. Follow our step-by-step wizard where you\'ll choose your assistant type, select a voice, customize the behavior, and deploy your assistant. No technical knowledge required!'
    },
    {
      id: 4,
      category: 'assistants',
      question: 'What types of AI assistants can I create?',
      answer: 'You can create various types of assistants including Customer Service bots, Sales assistants, Appointment booking systems, Lead qualification tools, Help desk assistants, Survey collectors, Technical support bots, and Consultation assistants. Each type comes with pre-built templates and industry-specific knowledge.'
    },
    {
      id: 5,
      category: 'assistants',
      question: 'Can I customize my assistant\'s voice and personality?',
      answer: 'Yes! You can choose from a variety of professional voices and customize your assistant\'s personality, tone, and responses. Our platform offers multiple voice options optimized for African accents and languages, ensuring natural conversations with your customers.'
    },
    {
      id: 6,
      category: 'assistants',
      question: 'How long does it take to deploy an assistant?',
      answer: 'Most assistants can be created and deployed within 10-15 minutes using our guided wizard. Once deployed, your assistant is immediately available and you\'ll receive a demo URL to test and share with your team.'
    },
    {
      id: 7,
      category: 'pricing',
      question: 'How much does it cost to use your platform?',
      answer: 'We offer flexible pricing based on usage. You only pay for the minutes your assistants are actively engaged in conversations. We have bundle packages starting from 1K minutes for small businesses to 50K+ minutes for enterprises. Contact us for custom pricing.'
    },
    {
      id: 8,
      category: 'pricing',
      question: 'Is there a free trial?',
      answer: 'Yes! New users get free credits to test our platform and create their first assistant. You can create demos and test functionality before committing to a paid plan. Contact us to learn more about our trial offerings.'
    },
    {
      id: 9,
      category: 'pricing',
      question: 'What payment methods do you accept?',
      answer: 'We accept various payment methods including Mobile Money (MTN, Vodafone, AirtelTigo), Bank transfers, Credit/Debit cards, and PayPal. We support local payment methods across African countries for your convenience.'
    },
    {
      id: 10,
      category: 'technical',
      question: 'How do I integrate the assistant into my website?',
      answer: 'Integration is simple! After creating your assistant, you\'ll receive an HTML embed code that you can paste into your website. We also provide WordPress plugins, JavaScript SDK, and API endpoints for custom integrations. No complex setup required.'
    },
    {
      id: 11,
      category: 'technical',
      question: 'Can my assistant handle multiple languages?',
      answer: 'Yes! Our assistants support multiple African languages including English, Swahili, Hausa, Yoruba, Amharic, and French. You can configure your assistant to detect and respond in the user\'s preferred language automatically.'
    },
    {
      id: 12,
      category: 'technical',
      question: 'What happens if my assistant can\'t answer a question?',
      answer: 'When your assistant encounters a question it can\'t answer, it can escalate to human agents, collect contact information for follow-up, or provide alternative resources. You can customize these fallback behaviors based on your business needs.'
    },
    {
      id: 13,
      category: 'technical',
      question: 'Can I analyze my assistant\'s performance?',
      answer: 'Absolutely! Our dashboard provides detailed analytics including conversation metrics, user satisfaction scores, common questions, response times, and conversion rates. You can export reports and track ROI from your AI assistant.'
    },
    {
      id: 14,
      category: 'security',
      question: 'How secure is my data?',
      answer: 'We take security seriously. All data is encrypted in transit and at rest. We comply with international security standards and African data protection regulations. Your customer conversations and business data are stored securely and never shared with third parties.'
    },
    {
      id: 15,
      category: 'security',
      question: 'Where is my data stored?',
      answer: 'Your data is stored in secure, certified data centers with redundancy and backup systems. We ensure compliance with local data residency requirements and provide options for data location based on your business needs.'
    },
    {
      id: 16,
      category: 'security',
      question: 'Can I delete my data?',
      answer: 'Yes, you have full control over your data. You can delete conversation logs, customer data, and your entire account at any time. We provide data export options and ensure complete data removal upon request.'
    },
    {
      id: 17,
      category: 'support',
      question: 'What support do you provide?',
      answer: 'We offer comprehensive support including 24/7 technical assistance, onboarding help, training sessions, and dedicated account management for enterprise clients. Support is available via email, chat, and phone.'
    },
    {
      id: 18,
      category: 'support',
      question: 'How can I contact support?',
      answer: 'You can reach our support team via email at kasaai@ikieguy.com, phone at +233 54 569 9663, or through our contact form. We typically respond within 24 hours during business days, with priority support for urgent issues.'
    },
    {
      id: 19,
      category: 'support',
      question: 'Do you provide training for my team?',
      answer: 'Yes! We provide comprehensive training sessions for your team including platform orientation, best practices for AI assistant management, and ongoing optimization strategies. Training can be conducted remotely or on-site.'
    },
    {
      id: 20,
      category: 'general',
      question: 'Can I schedule a demo?',
      answer: 'Absolutely! You can schedule a personalized demo where we\'ll show you the platform, discuss your specific needs, and help you understand how AI assistants can benefit your business. Visit our Schedule Demo page or contact us directly.'
    }
  ];

  const filteredFAQs = faqData.filter(faq => {
    const matchesSearch = faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         faq.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container text-center">
          <h1 className="text-5xl font-bold mb-6">
            Frequently Asked Questions
          </h1>
          <p className="text-xl text-white/90 max-w-3xl mx-auto">
            Find answers to common questions about AI Labs Africa's AI assistant platform
          </p>
        </div>
      </section>

      {/* Search and Filter */}
      <section className="py-8 bg-muted/30">
        <div className="container">
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search FAQs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Category Filter */}
            <div className="flex flex-wrap gap-2 justify-center">
              {categories.map((category) => {
                const Icon = category.icon;
                return (
                  <Button
                    key={category.id}
                    variant={selectedCategory === category.id ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedCategory(category.id)}
                    className="flex items-center gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    {category.label}
                  </Button>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Content */}
      <section className="py-16">
        <div className="container max-w-4xl">
          {filteredFAQs.length === 0 ? (
            <Card className="text-center p-8">
              <CardContent>
                <HelpCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No FAQs found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your search terms or category filter
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <p className="text-muted-foreground">
                  Showing {filteredFAQs.length} {filteredFAQs.length === 1 ? 'question' : 'questions'}
                  {selectedCategory !== 'all' && (
                    <span> in {categories.find(c => c.id === selectedCategory)?.label}</span>
                  )}
                </p>
              </div>

              <Accordion type="single" collapsible className="space-y-4">
                {filteredFAQs.map((faq) => {
                  const category = categories.find(c => c.id === faq.category);
                  return (
                    <AccordionItem key={faq.id} value={faq.id.toString()}>
                      <Card>
                        <AccordionTrigger className="px-6 py-4 hover:no-underline">
                          <div className="flex items-start gap-3 text-left">
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary" className="text-xs">
                                {category?.label}
                              </Badge>
                            </div>
                            <h3 className="font-medium text-left">{faq.question}</h3>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="px-6 pb-4">
                          <p className="text-muted-foreground leading-relaxed">
                            {faq.answer}
                          </p>
                        </AccordionContent>
                      </Card>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </div>
          )}
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-16 bg-muted/30">
        <div className="container text-center">
          <h2 className="text-3xl font-bold mb-4">Still have questions?</h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Can't find what you're looking for? Our support team is here to help you get the answers you need.
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-8">
            <Card className="text-center p-6">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-lg flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-lg">Contact Support</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="mb-4">
                  Get help from our expert support team
                </CardDescription>
                <Button variant="outline" asChild>
                  <Link to="/contact">Contact Us</Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="text-center p-6">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Calendar className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-lg">Schedule a Demo</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="mb-4">
                  See our platform in action with a personalized demo
                </CardDescription>
                <Button variant="outline" asChild>
                  <Link to="/schedule-demo">Book Demo</Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="text-center p-6">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-tech-blue to-african-gold rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-lg">Call Us</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="mb-4">
                  Speak directly with our team
                </CardDescription>
                <Button variant="outline" asChild>
                  <a href="tel:+233545699663">+233 54 569 9663</a>
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild>
              <Link to="/create-assistant">
                Get Started
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/demos">
                View Demos
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default FAQ;
