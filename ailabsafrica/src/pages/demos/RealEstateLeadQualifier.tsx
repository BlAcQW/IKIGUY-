import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, Home, Calendar, MapPin, TrendingUp } from 'lucide-react';

const RealEstateLeadQualifier = () => {
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
              Real Estate Lead Qualifier
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Meet Akosua, your AI-powered real estate assistant. She engages potential buyers, 
              qualifies leads, and schedules appointments to help you close more deals.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <Home className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Lead Qualification</div>
                  <div className="text-sm text-white/80">Smart screening</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <MapPin className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Property Match</div>
                  <div className="text-sm text-white/80">Perfect recommendations</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Calendar className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Appointment Scheduling</div>
                  <div className="text-sm text-white/80">Seamless booking</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Follow-up Calls</div>
                  <div className="text-sm text-white/80">Nurture leads</div>
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
              <CardTitle className="text-2xl">Talk to Akosua - Real Estate Assistant</CardTitle>
              <CardDescription className="text-lg">
                Experience how Akosua can help qualify leads and schedule viewings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Lead qualification</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Property recommendations</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Appointment scheduling</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Follow-up calls</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Market insights</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Budget assessment</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I'm looking to buy a home in Accra"</p>
                  <p><strong>Akosua:</strong> "That's exciting! I'd love to help you find the perfect home in Accra. What's your budget range and what type of property are you looking for?"</p>
                  <p><strong>You:</strong> "Around 500,000 GHS for a 3-bedroom house"</p>
                  <p><strong>Akosua:</strong> "Great! I have several excellent 3-bedroom properties in your budget. Which areas of Accra interest you most? I can schedule viewings for this weekend."</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to start talking with Akosua!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="730b032d-6606-40bf-afa3-072800b6d105"
        mode="voice"
        theme="dark"
        base-bg-color="#000000"
        accent-color="#1b2f5d"
        cta-button-color="#000000"
        cta-button-text-color="#b8860b"
        border-radius="large"
        size="full"
        position="bottom-right"
        title="TALK WITH AKOSUA"
        start-button-text="Start"
        end-button-text="End Call"
        chat-first-message="Hi! I'm Akosua, your real estate assistant. Are you looking to buy, sell, or rent a property today?"
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

export default RealEstateLeadQualifier;