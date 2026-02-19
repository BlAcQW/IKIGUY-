import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { 
  Phone, 
  MessageSquare, 
  Calendar, 
  CreditCard, 
  HeadphonesIcon, 
  ShoppingCart,
  Building,
  Heart,
  Play,
  ExternalLink
} from 'lucide-react';

// Declare the custom vapi-widget element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'vapi-widget': {
        'assistant-id': string;
        'public-key': string;
        'mode'?: string;
        'theme'?: string;
        'base-bg-color'?: string;
        'accent-color'?: string;
        'cta-button-color'?: string;
        'cta-button-text-color'?: string;
        'border-radius'?: string;
        'size'?: string;
        'position'?: string;
        'title'?: string;
        'start-button-text'?: string;
        'end-button-text'?: string;
        'chat-first-message'?: string;
        'chat-placeholder'?: string;
        'voice-show-transcript'?: string;
        'consent-required'?: string;
        'consent-title'?: string;
        'consent-content'?: string;
        'consent-storage-key'?: string;
        key?: string;
      };
    }
  }
}

const Demos = () => {
  const [activeWidget, setActiveWidget] = useState<string | null>(null);

  console.log('Demos render - activeWidget:', activeWidget);

  const widgetConfigs = {
    'Insurance Claims Assistant': {
      assistantId: "96037449-9dd1-49d9-a092-b8d088d2b5c9",
      title: "Talk With Ama, Our Insurance Claims Assistant"
    },
    'Insurance Sales Expert': {
      assistantId: "96037449-9dd1-49d9-a092-b8d088d2b5c9",
      title: "Talk With Ama, Our Insurance Sales Expert"
    },
    'Bank Loans Sales Expert': {
      assistantId: "aa7807e2-fad0-4be6-afe7-fb42e699ab8d",
      title: "Talk to Afua, Our Bank and Loans Sales Expert"
    },
    'Real Estate Lead Qualifier': {
      assistantId: "730b032d-6606-40bf-afa3-072800b6d105",
      title: "Talk With Akosua, Our Real Estate Sales Assistant"
    },
    'Retail Product Advisor': {
      assistantId: "79cff77e-8603-4602-b830-87ec890fe745",
      title: "Talk With Our Retail Product Advisor"
    },
    'Healthcare Appointment Bot': {
      assistantId: "d297ad5a-b5ce-48ec-9517-360667c0e161",
      title: "Talk With Our Healthcare Appointment Bot"
    },
    'Service Booking Assistant': {
      assistantId: "0d006e82-a07e-438a-9324-90b468b71803",
      title: "Talk With Our Service Booking Assistant"
    },
    'Payment Reminder System': {
      assistantId: "37a98ad8-7df4-4263-bbd5-9f717768ea89",
      title: "Talk With Our Payment Reminder System"
    },
    'Loan Application Assistant': {
      assistantId: "ed539dbc-0b6e-42d4-9157-bef845b52e55",
      title: "Talk With Our Loan Application Assistant"
    },
    'Banking Support Bot': {
      assistantId: "ed3b4e19-10da-410f-9fb4-d21ec191e748",
      title: "Talk With Our Banking Support Bot"
    },
    'Insurance Helpdesk': {
      assistantId: "96037449-9dd1-49d9-a092-b8d088d2b5c9",
      title: "Talk With Kofi, Our Insurance Customer Service Expert"
    },
    'German Therapist': {
      assistantId: "mara-german-therapist-id", // Replace with actual assistant ID
      title: "Spreche mit Mara, deiner neurodiversitäts-affirmativen Tages-Coachin"
    },
    'French Helpdesk': {
      assistantId: "youpilabs-french-helpdesk-id", // Replace with actual assistant ID
      title: "Parlez avec notre assistant clientèle francophone"
    },
    'Green Book': {
      assistantId: "green-book-assistant-id", // Replace with actual assistant ID
      title: "Talk with Abena about NDC achievements from the Green Book"
    },
    'Kojo Bonsu Campaign': {
      assistantId: "kojo-bonsu-campaign-id", // Replace with actual assistant ID
      title: "Talk with Kofi about Honourable Kojo Bonsu's campaign"
    }
  };

  const demoCategories = [
    {
      title: "Customer Support",
      icon: HeadphonesIcon,
      description: "24/7 automated customer service with intelligent responses",
      demos: [
        {
          name: "Insurance Claims Assistant",
          description: "Help customers file and track insurance claims seamlessly",
          industry: "Insurance",
          type: "Voice + Chat",
          features: ["Claim filing", "Document collection", "Status updates", "FAQ handling"]
        },
        {
          name: "Insurance Helpdesk",
          description: "Kofi provides calm and courteous assistance with claims, payments, and policy questions",
          industry: "Insurance",
          type: "Voice + Chat",
          features: ["Claims guidance", "Payment assistance", "Product information", "Timeline transparency"]
        },
        {
          name: "Banking Support Bot",
          description: "Answer banking queries and guide customers through services",
          industry: "Banking",
          type: "Voice + Chat",
          features: ["Account balance", "Transaction history", "Service information", "Security verification"]
        },
        {
          name: "French Helpdesk",
          description: "Professional French-speaking customer support for YoupiLabs",
          industry: "Technology",
          type: "Voice + Chat",
          features: ["Multilingual support", "Technical assistance", "Product guidance", "Customer service"]
        }
      ]
    },
    {
      title: "Sales & Marketing",
      icon: ShoppingCart,
      description: "Automated outreach and lead qualification systems",
      demos: [
        {
          name: "Insurance Sales Expert",
          description: "Ama helps customers find the perfect insurance coverage",
          industry: "Insurance",
          type: "Voice Calls",
          features: ["Policy recommendations", "Coverage analysis", "Quote generation", "Customer education"]
        },
        {
          name: "Bank Loans Sales Expert",
          description: "Afua guides customers through loan options and applications",
          industry: "Banking",
          type: "Voice Calls",
          features: ["Loan qualification", "Rate comparison", "Application assistance", "Financial consultation"]
        },
        {
          name: "Real Estate Lead Qualifier",
          description: "Engage potential buyers and qualify leads automatically",
          industry: "Real Estate",
          type: "Voice Calls",
          features: ["Lead qualification", "Property recommendations", "Appointment scheduling", "Follow-up calls"]
        },
        {
          name: "Retail Product Advisor",
          description: "Help customers find products and complete purchases",
          industry: "Retail",
          type: "WhatsApp + Web Chat",
          features: ["Product recommendations", "Order assistance", "Inventory check", "Upselling"]
        }
      ]
    },
    {
      title: "Appointment & Booking",
      icon: Calendar,
      description: "Intelligent scheduling and appointment management",
      demos: [
        {
          name: "Healthcare Appointment Bot",
          description: "Schedule, reschedule, and manage medical appointments",
          industry: "Healthcare",
          type: "Voice + SMS",
          features: ["Appointment booking", "Reminder calls", "Rescheduling", "Health screening"]
        },
        {
          name: "Service Booking Assistant",
          description: "Book consultations and manage service appointments",
          industry: "Professional Services",
          type: "Multi-channel",
          features: ["Service booking", "Availability check", "Confirmation SMS", "Follow-up"]
        }
      ]
    },
    {
      title: "Payment & Finance",
      icon: CreditCard,
      description: "Automated payment reminders and financial assistance",
      demos: [
        {
          name: "Payment Reminder System",
          description: "Friendly payment reminders with flexible options",
          industry: "Finance",
          type: "Voice + SMS",
          features: ["Payment reminders", "Payment plans", "Balance inquiries", "Receipt confirmation"]
        },
        {
          name: "Loan Application Assistant",
          description: "Guide customers through loan applications",
          industry: "Banking",
          type: "Voice + Chat",
          features: ["Application guidance", "Document collection", "Status updates", "Eligibility check"]
        }
      ]
    },
    {
      title: "Community & Campaigns",
      icon: Building,
      description: "Engage communities and run campaign outreach",
      demos: [
        {
          name: "Church Events and Follow up",
          description: "Automate event announcements, RSVPs, and follow-ups",
          industry: "Community",
          type: "WhatsApp + Voice",
          features: ["Event announcements", "RSVP collection", "Reminders", "Follow-up messages"]
        },
        {
          name: "Elections Campaign",
          description: "Run voter outreach and organize campaign communications",
          industry: "Public Sector",
          type: "Voice + WhatsApp",
          features: ["Voter outreach", "Event reminders", "Volunteer coordination", "FAQ handling"]
        }
      ]
    },
    {
      title: "Health & Wellness",
      icon: Heart,
      description: "Supportive AI companions for mental health and daily wellness",
      demos: [
        {
          name: "German Therapist",
          description: "Mara, your neurodiversity-affirmative daily coach who guides you through tasks with compassion and understanding",
          industry: "Mental Health",
          type: "Voice + Chat",
          features: ["ADHD support", "Autism-friendly", "Task breakdown", "Body doubling", "Self-compassion"]
        }
      ]
    },
    {
      title: "Political Campaigns",
      icon: Building,
      description: "AI-powered campaign assistants and political education tools",
      demos: [
        {
          name: "Green Book",
          description: "Abena provides detailed information about NDC achievements from the 'Accounting to the People' document",
          industry: "Politics",
          type: "Voice + Chat",
          features: ["Political education", "Historical data", "Achievement tracking", "Policy information"]
        },
        {
          name: "Kojo Bonsu Campaign",
          description: "Kofi, campaign manager for Honourable Kojo Bonsu, presents his vision for Ghana and NDC leadership",
          industry: "Politics",
          type: "Voice + Chat",
          features: ["Campaign outreach", "Policy presentation", "Voter engagement", "Political advocacy"]
        }
      ]
    }
  ];

  const getIcon = (IconComponent: any) => {
    return <IconComponent className="h-6 w-6" />;
  };

  const getIndustryColor = (industry: string) => {
    const colors: { [key: string]: string } = {
      'Insurance': 'bg-blue-100 text-blue-800',
      'Banking': 'bg-green-100 text-green-800',
      'Real Estate': 'bg-purple-100 text-purple-800',
      'Retail': 'bg-orange-100 text-orange-800',
      'Healthcare': 'bg-red-100 text-red-800',
      'Professional Services': 'bg-indigo-100 text-indigo-800',
      'Finance': 'bg-yellow-100 text-yellow-800',
      'Mental Health': 'bg-pink-100 text-pink-800',
      'Technology': 'bg-cyan-100 text-cyan-800',
      'Politics': 'bg-emerald-100 text-emerald-800'
    };
    return colors[industry] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container text-center">
          <h1 className="text-5xl font-bold mb-6">
            Experience KasaAI in Action
          </h1>
          <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8">
            Discover how KasaAI transforms customer interactions across different industries. 
            Try our interactive demos and see the power of intelligent conversations.
          </p>
          <Badge variant="secondary" className="bg-african-gold text-black text-lg px-4 py-2">
            All demos are live and interactive
          </Badge>
        </div>
      </section>

      {/* Demo Categories */}
      <section className="py-16">
        <div className="container">
          {demoCategories.map((category, categoryIndex) => (
            <div key={categoryIndex} className="mb-16">
              <div className="flex items-center mb-8">
                <div className="w-12 h-12 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-lg flex items-center justify-center mr-4">
                  {getIcon(category.icon)}
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-foreground">{category.title}</h2>
                  <p className="text-muted-foreground">{category.description}</p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {category.demos.map((demo, demoIndex) => (
                  <Card key={demoIndex} className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-xl mb-2">{demo.name}</CardTitle>
                          <CardDescription className="text-base">{demo.description}</CardDescription>
                        </div>
                        <Badge className={getIndustryColor(demo.industry)}>
                          {demo.industry}
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge variant="outline">{demo.type}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <h4 className="font-semibold mb-2 text-sm text-muted-foreground">KEY FEATURES</h4>
                        <div className="grid grid-cols-2 gap-2">
                          {demo.features.map((feature, featureIndex) => (
                            <div key={featureIndex} className="flex items-center space-x-2 text-sm">
                              <div className="w-1.5 h-1.5 bg-african-gold rounded-full"></div>
                              <span>{feature}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex space-x-3">
                        {demo.name === 'Banking Support Bot' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/banking.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Bank Loans Sales Expert' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/banking-loans.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Insurance Claims Assistant' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/claims.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Insurance Helpdesk' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/helpdesk.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Insurance Sales Expert' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/insurance-sales.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Real Estate Lead Qualifier' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/realestate.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Retail Product Advisor' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/retail.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Healthcare Appointment Bot' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/medical.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Service Booking Assistant' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/business.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Payment Reminder System' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/payment.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Loan Application Assistant' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/loan.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Church Events and Follow up' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/church-assistant.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'Elections Campaign' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/elections-campaign.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'French Helpdesk' && (
                          <Button size="sm" className="w-full" asChild>
                            <a href="https://ailabsafrica.com/demos/youpilabs.html" target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Open Demo
                            </a>
                          </Button>
                        )}
                        {demo.name === 'German Therapist' && (
                          <Button size="sm" className="w-full" asChild>
                            <Link to="/demos/german-therapist">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              View Details
                            </Link>
                          </Button>
                        )}
                        {demo.name === 'Green Book' && (
                          <Button size="sm" className="w-full" asChild>
                            <Link to="/demos/green-book">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              View Details
                            </Link>
                          </Button>
                        )}
                        {demo.name === 'Kojo Bonsu Campaign' && (
                          <Button size="sm" className="w-full" asChild>
                            <Link to="/demos/kojo-bonsu-campaign">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              View Details
                            </Link>
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section className="py-16 bg-muted/30">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-tech-blue to-african-gold bg-clip-text text-transparent">
              Try KasaAI Live
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Experience the power of conversational AI with our interactive demo. 
              Choose your preferred channel and start a conversation.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <Card className="text-center p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-2 hover:border-primary">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-full flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-8 w-8 text-white" />
                </div>
                <CardTitle>Voice Call Demo</CardTitle>
                <CardDescription>Experience AI voice conversations</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">Start Voice Demo</Button>
              </CardContent>
            </Card>

            <Card className="text-center p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-2 hover:border-primary">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="h-8 w-8 text-white" />
                </div>
                <CardTitle>Chat Demo</CardTitle>
                <CardDescription>Interactive text conversations</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full" variant="outline">Start Chat Demo</Button>
              </CardContent>
            </Card>

            <Card className="text-center p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-2 hover:border-primary">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-tech-blue to-african-gold rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="h-8 w-8 text-white" />
                </div>
                <CardTitle>WhatsApp Demo</CardTitle>
                <CardDescription>Experience WhatsApp automation</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full" variant="secondary">Start WhatsApp Demo</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Implement KasaAI?</h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Contact us to discuss your specific use case and get a customized demo for your industry.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link to="/contact" className="bg-african-gold hover:bg-african-gold-dark text-black">
                Request Custom Demo
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="border-white/30 text-white hover:bg-white/10">
              <Link to="/">Learn More</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Single Dynamic Widget */}
      {(() => {
        console.log('Widget render check - activeWidget:', activeWidget);
        
        if (activeWidget && widgetConfigs[activeWidget as keyof typeof widgetConfigs]) {
          console.log('Rendering widget for:', activeWidget);
          console.log('Assistant ID:', widgetConfigs[activeWidget as keyof typeof widgetConfigs].assistantId);
          
          return (
            <vapi-widget
              key={activeWidget}
              public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
              assistant-id={widgetConfigs[activeWidget as keyof typeof widgetConfigs].assistantId}
              title={widgetConfigs[activeWidget as keyof typeof widgetConfigs].title}
            />
          );
        }
        
        return null;
      })()}
    </div>
  );
};

export default Demos;