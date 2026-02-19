import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Building2, Search, Shield, Sparkles, TrendingUp, Users } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Building2,
      title: "Property Management",
      description: "Comprehensive tools to manage your real estate portfolio efficiently",
    },
    {
      icon: Search,
      title: "Smart Search",
      description: "Find your perfect property with AI-powered search and filters",
    },
    {
      icon: Sparkles,
      title: "AI-Powered",
      description: "Get intelligent insights and automated assistance for better decisions",
    },
    {
      icon: Shield,
      title: "Secure & Reliable",
      description: "Enterprise-grade security to protect your data and transactions",
    },
    {
      icon: TrendingUp,
      title: "Analytics",
      description: "Track performance with detailed analytics and reporting tools",
    },
    {
      icon: Users,
      title: "Client Management",
      description: "Manage relationships with clients, tenants, and stakeholders",
    },
  ];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10" />
        <div className="container relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                AI-Powered Real Estate
              </span>
              <br />
              Management Platform
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Streamline your property management with intelligent automation, powerful analytics,
              and seamless communication tools.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate("/properties")}
                className="text-lg px-8"
              >
                Browse Properties
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/login")}
                className="text-lg px-8"
              >
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="container">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold">
              Everything You Need
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful features designed to help you manage properties, engage clients,
              and grow your business
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} variant="elevated" className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6 space-y-4">
                  <div className="p-3 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 w-fit">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container">
          <Card variant="premium" className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20" />
            <CardContent className="relative p-12 md:p-16 text-center space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                Ready to Transform Your Real Estate Business?
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Join thousands of property managers and real estate professionals who trust Diaserve Properties
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  size="lg"
                  onClick={() => navigate("/login")}
                  className="text-lg px-8"
                >
                  Start Free Trial
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate("/properties")}
                  className="text-lg px-8"
                >
                  View Properties
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-muted/30">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Building2 className="h-6 w-6 text-primary" />
                <span className="font-bold text-lg">Diaserve Properties</span>
              </div>
              <p className="text-sm text-muted-foreground">
                AI-powered real estate management platform
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="/properties" className="hover:text-foreground">Properties</a></li>
                <li><a href="/login" className="hover:text-foreground">Features</a></li>
                <li><a href="/login" className="hover:text-foreground">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="/about" className="hover:text-foreground">About</a></li>
                <li><a href="/contact" className="hover:text-foreground">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">Privacy</a></li>
                <li><a href="#" className="hover:text-foreground">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} Diaserve Properties. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
