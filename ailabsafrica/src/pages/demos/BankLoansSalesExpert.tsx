import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, Phone, Calculator, TrendingUp, FileText } from 'lucide-react';

const BankLoansSalesExpert = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container">
          <div className="flex items-center mb-6">
            <Button variant="ghost" size="sm" asChild className="text-white hover:bg-white/20 mr-4">
              <Link to="/demos">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Demos
              </Link>
            </Button>
          </div>
          
          <div className="max-w-4xl">
            <Badge className="bg-green-100 text-green-800 mb-4">Banking</Badge>
            <h1 className="text-5xl font-bold mb-6">
              Bank Loans Sales Expert
            </h1>
            <p className="text-xl text-white/90 mb-8">
              Meet Afua, your dedicated AI assistant who guides customers through loan options and applications with expertise and care.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Phone className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Voice Calls</div>
                  <div className="text-white/80 text-sm">Personal consultation</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Calculator className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Smart Analysis</div>
                  <div className="text-white/80 text-sm">Loan qualification</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Expert Guidance</div>
                  <div className="text-white/80 text-sm">Financial consultation</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-16">
        <div className="container">
          <div className="max-w-4xl mx-auto">
            <Card className="p-8 shadow-xl border-0">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl mb-4">Talk to Afua, Our Bank Loans Sales Expert</CardTitle>
                <CardDescription className="text-lg">
                  Experience how Afua can help you find the perfect loan solution for your needs.
                </CardDescription>
              </CardHeader>
              
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                  <div>
                    <h3 className="font-semibold mb-4 text-lg">Key Features</h3>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Loan qualification assessment</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Rate comparison and analysis</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Application assistance</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Financial consultation</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-4 text-lg">Sample Conversations</h3>
                    <div className="space-y-3">
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"I need a personal loan"</div>
                        <div className="text-sm text-muted-foreground mt-1">Loan qualification and options</div>
                      </div>
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"What are your mortgage rates?"</div>
                        <div className="text-sm text-muted-foreground mt-1">Rate comparison and analysis</div>
                      </div>
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"Help me with my application"</div>
                        <div className="text-sm text-muted-foreground mt-1">Application guidance</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="text-center">
                  <p className="text-muted-foreground mb-6">
                    Click the widget below to start a conversation with Afua
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="aa7807e2-fad0-4be6-afe7-fb42e699ab8d"
        mode="voice"
        theme="dark"
        base-bg-color="#000000"
        accent-color="#14B8A6"
        cta-button-color="#000000"
        cta-button-text-color="#ffffff"
        border-radius="large"
        size="full"
        position="bottom-right"
        title="TALK WITH AFUA"
        start-button-text="Start"
        end-button-text="End Call"
        chat-first-message="Hello! I'm Afua, your bank loans expert. How can I help you with your financing needs today?"
        chat-placeholder="Type your message..."
        voice-show-transcript="true"
        consent-required="true"
        consent-title="Terms and conditions"
        consent-content="By clicking 'Agree,' and each time I interact with this AI agent, I consent to the recording, storage, and sharing of my communications with third-party service providers, and as otherwise described in our Terms of Service."
        consent-storage-key="vapi_widget_consent"
      />
    </div>
  );
};

export default BankLoansSalesExpert;