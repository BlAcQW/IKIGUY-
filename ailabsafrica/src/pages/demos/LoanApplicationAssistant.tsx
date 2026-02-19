import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, CheckCircle, TrendingUp, MessageSquare } from 'lucide-react';

const LoanApplicationAssistant = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <section className="py-16 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container">
          <Button variant="outline" className="mb-8 border-white/30 text-white hover:bg-white/10" asChild>
            <Link to="/demos">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Demos
            </Link>
          </Button>
          
          <div className="max-w-4xl">
            <h1 className="text-5xl font-bold mb-6">
              Loan Application Assistant
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Your AI-powered loan application assistant that guides customers through the application process, 
              collects documents, and provides status updates with expertise and care.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <FileText className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Application Guidance</div>
                  <div className="text-sm text-white/80">Step-by-step help</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Document Collection</div>
                  <div className="text-sm text-white/80">Smart checklist</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Status Updates</div>
                  <div className="text-sm text-white/80">Real-time tracking</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Eligibility Check</div>
                  <div className="text-sm text-white/80">Quick assessment</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-16">
        <div className="container max-w-4xl">
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="text-2xl">Try Our Loan Application Assistant</CardTitle>
              <CardDescription className="text-lg">
                Experience guided loan application support and document management
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Application guidance</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Document collection</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Status updates</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Eligibility check</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Rate information</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Application tracking</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I want to apply for a personal loan"</p>
                  <p><strong>AI:</strong> "I'd be happy to help you with your personal loan application! Let me start by checking your eligibility. What's the loan amount you're looking for and what will you be using the funds for?"</p>
                  <p><strong>You:</strong> "I need $10,000 for home improvements"</p>
                  <p><strong>AI:</strong> "Perfect! Home improvement loans are a great investment. Based on your request, you may qualify for rates starting at 6.99%. Let me gather some basic information to get your application started. What's your current employment status and monthly income?"</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to start your loan application!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="ed539dbc-0b6e-42d4-9157-bef845b52e55"
        mode="voice"
        theme="dark"
        base-bg-color="#000000"
        accent-color="#1b2f5d"
        cta-button-color="#000000"
        cta-button-text-color="#b8860b"
        border-radius="large"
        size="full"
        position="bottom-right"
        title="TALK WITH AI"
        start-button-text="Start"
        end-button-text="End Call"
        chat-first-message="Hi! I'm here to help you with your loan application. What type of loan are you interested in today?"
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

export default LoanApplicationAssistant;