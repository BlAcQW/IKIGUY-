import React from 'react';
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Check, 
  ArrowRight, 
  Bot, 
  Phone, 
  MessageSquare, 
  BarChart3,
  CreditCard,
  Zap,
  Star
} from "lucide-react";

const Pricing = () => {
  const plans = [
    {
      name: "Starter",
      price: 29,
      period: "month",
      description: "Perfect for individuals and small teams getting started",
      features: [
        "1 AI Assistant",
        "500 minutes/month",
        "Basic templates",
        "Email support",
        "Basic analytics"
      ],
      popular: false,
      cta: "Start Free Trial"
    },
    {
      name: "Professional",
      price: 99,
      period: "month", 
      description: "For growing businesses that need more power",
      features: [
        "5 AI Assistants",
        "2,500 minutes/month",
        "All templates",
        "Priority support",
        "Advanced analytics",
        "WhatsApp integration",
        "Custom voice cloning"
      ],
      popular: true,
      cta: "Start Free Trial"
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "",
      description: "For large organizations with custom requirements",
      features: [
        "Unlimited assistants",
        "Unlimited minutes",
        "Custom templates",
        "Dedicated support",
        "White-label options",
        "API access",
        "Custom integrations",
        "SLA guarantee"
      ],
      popular: false,
      cta: "Contact Sales"
    }
  ];

  const addOns = [
    { name: "Extra Voice Minutes", price: "$0.05/minute" },
    { name: "WhatsApp Messages", price: "$0.02/message" },
    { name: "Premium Voice Cloning", price: "$49/month" },
    { name: "Dedicated Phone Number", price: "$15/month" }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-indigo-600">KasaAI</span>
            </Link>
            <div className="hidden md:flex items-center space-x-6">
              <Link to="/#features" className="text-gray-600 hover:text-foreground transition-colors">Features</Link>
              <Link to="/pricing" className="text-foreground font-medium">Pricing</Link>
              <Link to="/about" className="text-gray-600 hover:text-foreground transition-colors">About</Link>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/auth">Sign In</Link>
              </Button>
              <Button variant="hero" size="sm" asChild>
                <Link to="/auth">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4 bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <div className="container mx-auto max-w-4xl text-center">
          <Badge variant="secondary" className="px-3 py-1 mb-6">
            <Star className="h-3 w-3 mr-1" />
            Simple, Transparent Pricing
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
            Choose the Perfect Plan
            <span className="bg-gradient-hero bg-clip-text text-transparent"> for Your Business</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Start free, scale as you grow. No hidden fees, no surprises. 
            Cancel anytime with our flexible pricing options.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <Card key={index} className={`relative hover:shadow-xl transition-all duration-300 ${plan.popular ? 'border-2 border-primary shadow-lg scale-105' : ''}`}>
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-indigo-600 text-primary-foreground">
                    Most Popular
                  </Badge>
                )}
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="my-4">
                    {typeof plan.price === 'number' ? (
                      <div className="flex items-baseline justify-center">
                        <span className="text-4xl font-bold text-foreground">${plan.price}</span>
                        <span className="text-gray-600 ml-1">/{plan.period}</span>
                      </div>
                    ) : (
                      <div className="text-4xl font-bold text-foreground">{plan.price}</div>
                    )}
                  </div>
                  <CardDescription className="text-base">{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <ul className="space-y-3">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center">
                        <Check className="h-4 w-4 text-accent mr-3 flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className={`w-full ${plan.popular ? 'variant-hero' : 'variant-outline'}`}
                    variant={plan.popular ? "default" : "outline"}
                    size="lg"
                    asChild
                  >
                    <Link to="/auth">
                      {plan.cta}
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Add-ons Section */}
      <section className="py-16 px-4 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Add-ons & Extensions</h2>
            <p className="text-gray-600">
              Enhance your plan with additional features and capacity
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {addOns.map((addon, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardContent className="p-6">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold">{addon.name}</h3>
                    <Badge variant="secondary">{addon.price}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Frequently Asked Questions</h2>
          </div>
          <div className="space-y-6">
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold mb-2">Can I change plans anytime?</h3>
                <p className="text-gray-600">Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold mb-2">What happens if I exceed my minutes?</h3>
                <p className="text-gray-600">Overage charges apply at $0.05 per minute. You'll receive notifications as you approach your limit.</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold mb-2">Is there a free trial?</h3>
                <p className="text-gray-600">Yes! All plans include a 14-day free trial with full access to features. No credit card required.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-hero">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Try KasaAI free for 14 days. No credit card required.
          </p>
          <Button variant="glass" size="lg" className="text-lg px-8" asChild>
            <Link to="/auth">
              Start Your Free Trial
              <ArrowRight className="h-5 w-5 ml-2" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default Pricing;