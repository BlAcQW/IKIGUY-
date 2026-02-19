import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Clock, Shield, CheckCircle } from 'lucide-react';

const InsuranceClaimsAssistant = () => {
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
              Insurance Claims Assistant
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Meet Ama, your AI-powered insurance claims assistant. She helps customers file claims, 
              track status, and collect necessary documents with ease and efficiency.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <FileText className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Claim Filing</div>
                  <div className="text-sm text-white/80">Easy submission process</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Status Updates</div>
                  <div className="text-sm text-white/80">Real-time tracking</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Shield className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Secure Process</div>
                  <div className="text-sm text-white/80">Protected information</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Document Help</div>
                  <div className="text-sm text-white/80">Guided collection</div>
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
              <CardTitle className="text-2xl">Try Ama - Insurance Claims Assistant</CardTitle>
              <CardDescription className="text-lg">
                Experience how Ama can help streamline your insurance claims process
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>New claim initiation</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Document upload guidance</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Claim status inquiries</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Policy information lookup</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Claims FAQ assistance</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Next steps guidance</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I need to file a claim for my car accident"</p>
                  <p><strong>Ama:</strong> "I'll help you file your auto claim. First, let me gather some basic information. What's your policy number and when did the accident occur?"</p>
                  <p><strong>You:</strong> "My policy is AUTO123456 and it happened yesterday"</p>
                  <p><strong>Ama:</strong> "Thank you. I've located your policy. Now I'll guide you through the documentation we'll need..."</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to start talking with Ama!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="96037449-9dd1-49d9-a092-b8d088d2b5c9"
        mode="voice"
        theme="dark"
        base-bg-color="#000000"
        accent-color="#1b2f5d"
        cta-button-color="#000000"
        cta-button-text-color="#b8860b"
        border-radius="large"
        size="full"
        position="bottom-right"
        title="TALK WITH AMA"
        start-button-text="Start"
        end-button-text="End Call"
        chat-first-message="Hi! I'm Ama, your insurance claims assistant. How can I help you today?"
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

export default InsuranceClaimsAssistant;