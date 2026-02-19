import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calendar, Clock, Heart, Phone } from 'lucide-react';

const HealthcareAppointmentBot = () => {
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
              Healthcare Appointment Bot
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Your AI-powered healthcare assistant that schedules appointments, sends reminders, 
              and manages medical consultations with care and precision.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <Calendar className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Appointment Booking</div>
                  <div className="text-sm text-white/80">Easy scheduling</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Reminder Calls</div>
                  <div className="text-sm text-white/80">Timely notifications</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Heart className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Health Screening</div>
                  <div className="text-sm text-white/80">Pre-visit assessment</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Phone className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Multi-channel</div>
                  <div className="text-sm text-white/80">Voice & SMS</div>
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
              <CardTitle className="text-2xl">Try Our Healthcare Appointment Bot</CardTitle>
              <CardDescription className="text-lg">
                Experience seamless medical appointment scheduling and management
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Appointment booking</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Reminder calls</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Rescheduling</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Health screening</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Doctor availability</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Insurance verification</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I need to schedule a checkup with Dr. Smith"</p>
                  <p><strong>AI:</strong> "I'd be happy to help you schedule an appointment with Dr. Smith. What type of appointment do you need - routine checkup, follow-up, or something specific?"</p>
                  <p><strong>You:</strong> "Just a routine annual checkup"</p>
                  <p><strong>AI:</strong> "Perfect! Dr. Smith has availability next Tuesday at 2 PM or Thursday at 10 AM. Which time works better for you? I'll also need to verify your insurance information."</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to schedule your appointment!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="d297ad5a-b5ce-48ec-9517-360667c0e161"
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
        chat-first-message="Hi! I'm your healthcare appointment assistant. How can I help you schedule or manage your appointment today?"
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

export default HealthcareAppointmentBot;