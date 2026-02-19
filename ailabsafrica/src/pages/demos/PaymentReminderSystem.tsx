import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, CreditCard, Phone, MessageSquare, Calendar } from 'lucide-react';

const PaymentReminderSystem = () => {
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
              Payment Reminder System
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Your AI-powered payment assistant that sends friendly reminders, offers payment plans, 
              and helps customers manage their financial obligations with care.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <Phone className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Payment Reminders</div>
                  <div className="text-sm text-white/80">Friendly calls</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Calendar className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Payment Plans</div>
                  <div className="text-sm text-white/80">Flexible options</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <CreditCard className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Balance Inquiries</div>
                  <div className="text-sm text-white/80">Account information</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-8 w-8 text-african-gold" />
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
              <CardTitle className="text-2xl">Try Our Payment Reminder System</CardTitle>
              <CardDescription className="text-lg">
                Experience compassionate and effective payment management assistance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Payment reminders</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Payment plans</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Balance inquiries</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Receipt confirmation</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Payment processing</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Hardship assistance</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>AI:</strong> "Hi John, this is a friendly reminder that your payment of $250 is due tomorrow. Would you like to make a payment now or discuss payment options?"</p>
                  <p><strong>You:</strong> "I'm having some financial difficulties this month. Can we work something out?"</p>
                  <p><strong>AI:</strong> "I completely understand, and I'm here to help. We have several payment plan options available. Would you prefer to split this into smaller payments over the next few months, or would you like to discuss a temporary payment reduction?"</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to manage your payment options!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="37a98ad8-7df4-4263-bbd5-9f717768ea89"
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
        chat-first-message="Hi! I'm calling about your account. How can I help you with your payment today?"
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

export default PaymentReminderSystem;