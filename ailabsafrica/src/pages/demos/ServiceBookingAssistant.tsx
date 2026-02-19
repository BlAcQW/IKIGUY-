import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calendar, CheckCircle, MessageSquare, Users } from 'lucide-react';

const ServiceBookingAssistant = () => {
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
              Service Booking Assistant
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Your AI-powered service booking assistant that helps clients schedule consultations, 
              check availability, and manage appointments across multiple channels.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <Calendar className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Service Booking</div>
                  <div className="text-sm text-white/80">Easy scheduling</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Availability Check</div>
                  <div className="text-sm text-white/80">Real-time slots</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Confirmation SMS</div>
                  <div className="text-sm text-white/80">Instant updates</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Users className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Multi-channel</div>
                  <div className="text-sm text-white/80">Voice, chat, SMS</div>
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
              <CardTitle className="text-2xl">Try Our Service Booking Assistant</CardTitle>
              <CardDescription className="text-lg">
                Experience seamless service appointment scheduling and management
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Service booking</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Availability check</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Confirmation SMS</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Follow-up calls</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Service recommendations</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Rescheduling support</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I need to book a consultation for legal services"</p>
                  <p><strong>AI:</strong> "I'd be happy to help you schedule a legal consultation. What type of legal matter do you need assistance with, and do you have a preferred date and time?"</p>
                  <p><strong>You:</strong> "It's about contract review, and I'm available next week"</p>
                  <p><strong>AI:</strong> "Perfect! For contract review consultations, we have availability on Tuesday at 3 PM, Wednesday at 11 AM, or Friday at 2 PM. Which works best for you? I'll send you a confirmation SMS with all the details."</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to book your service appointment!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="0d006e82-a07e-438a-9324-90b468b71803"
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
        chat-first-message="Hi! I'm your service booking assistant. What service would you like to schedule today?"
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

export default ServiceBookingAssistant;