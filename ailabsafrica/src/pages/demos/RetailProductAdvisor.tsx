import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ArrowLeft, ShoppingCart, Package, TrendingUp, MessageSquare } from 'lucide-react';

const RetailProductAdvisor = () => {
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
              Retail Product Advisor
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-3xl">
              Your AI-powered shopping assistant that helps customers find the perfect products, 
              complete purchases, and provides personalized recommendations.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6 mt-12">
              <div className="flex items-center space-x-3">
                <ShoppingCart className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Product Match</div>
                  <div className="text-sm text-white/80">Perfect recommendations</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Package className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Inventory Check</div>
                  <div className="text-sm text-white/80">Real-time availability</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Upselling</div>
                  <div className="text-sm text-white/80">Smart suggestions</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-8 w-8 text-african-gold" />
                <div>
                  <div className="font-semibold">Multi-channel</div>
                  <div className="text-sm text-white/80">WhatsApp & Web</div>
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
              <CardTitle className="text-2xl">Try Our Retail Product Advisor</CardTitle>
              <CardDescription className="text-lg">
                Experience personalized shopping assistance and product recommendations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Key Features:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Product recommendations</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Order assistance</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Inventory check</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Upselling suggestions</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Size & fit guidance</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-african-gold rounded-full"></div>
                      <span>Payment processing</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Conversation:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>You:</strong> "I'm looking for a new smartphone under $500"</p>
                  <p><strong>AI:</strong> "I'd be happy to help you find the perfect smartphone! Based on your budget, I have several excellent options. What features are most important to you - camera quality, battery life, or performance?"</p>
                  <p><strong>You:</strong> "Camera quality is my priority"</p>
                  <p><strong>AI:</strong> "Perfect! I recommend the Samsung Galaxy A54 5G at $449. It has an excellent 50MP camera with great low-light performance. Would you like to see more details or check availability?"</p>
                </div>
              </div>
              
              <p className="text-center text-lg">
                Click the chat widget below to start shopping with our AI advisor!
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* VAPI Widget */}
      <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="79cff77e-8603-4602-b830-87ec890fe745"
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
        chat-first-message="Hi! I'm your retail product advisor. What can I help you find today?"
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

export default RetailProductAdvisor;