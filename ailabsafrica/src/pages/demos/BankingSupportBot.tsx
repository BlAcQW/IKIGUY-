import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, Phone, MessageSquare, Shield, Clock } from 'lucide-react';

const BankingSupportBot = () => {
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
              Banking Support Bot
            </h1>
            <p className="text-xl text-white/90 mb-8">
              Answer banking queries and guide customers through services with intelligent AI assistance.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Phone className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Voice + Chat</div>
                  <div className="text-white/80 text-sm">Multi-channel support</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">Secure & Compliant</div>
                  <div className="text-white/80 text-sm">Bank-grade security</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <Clock className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">24/7 Available</div>
                  <div className="text-white/80 text-sm">Always ready to help</div>
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
                <CardTitle className="text-2xl mb-4">Try Our Banking Support Bot</CardTitle>
                <CardDescription className="text-lg">
                  Experience how our AI assistant can help with banking queries, account information, and customer support.
                </CardDescription>
              </CardHeader>
              
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                  <div>
                    <h3 className="font-semibold mb-4 text-lg">Key Features</h3>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Account balance inquiries</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Transaction history</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Service information</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                        <span>Security verification</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-4 text-lg">Use Cases</h3>
                    <div className="space-y-3">
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"What's my account balance?"</div>
                        <div className="text-sm text-muted-foreground mt-1">Quick balance inquiries</div>
                      </div>
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"How do I reset my PIN?"</div>
                        <div className="text-sm text-muted-foreground mt-1">Service guidance</div>
                      </div>
                      <div className="p-3 bg-muted/50 rounded-lg">
                        <div className="font-medium">"I need help with a transaction"</div>
                        <div className="text-sm text-muted-foreground mt-1">Transaction support</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="text-center">
                  <p className="text-muted-foreground mb-6">
                    Click the widget below to start a conversation with our Banking Support Bot
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
        assistant-id="ed3b4e19-10da-410f-9fb4-d21ec191e748"
        mode="voice"
        theme="dark"
        base-bg-color="#000000"
        accent-color="#14B8A6"
        cta-button-color="#000000"
        cta-button-text-color="#ffffff"
        border-radius="large"
        size="full"
        position="bottom-right"
        title="TALK WITH AI"
        start-button-text="Start"
        end-button-text="End Call"
        chat-first-message="Hey, How can I help you today?"
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

export default BankingSupportBot;