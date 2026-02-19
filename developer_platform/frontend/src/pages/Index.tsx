import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { Code, Zap, Shield, Globe } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <Badge variant="outline" className="mb-4">
            KasaAI Developer Platform
          </Badge>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Build AI-Powered Applications with KasaAI API
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Access cutting-edge AI models, manage your API keys, monitor usage, and build intelligent applications with our comprehensive developer platform.
          </p>
          
          <div className="flex gap-4 justify-center mb-16">
            <Button asChild size="lg">
              <Link to="/auth">Get Started</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#features">Learn More</a>
            </Button>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <Card>
            <CardHeader>
              <Code className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Easy Integration</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Simple REST API with comprehensive documentation and SDKs for popular languages.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Zap className="h-8 w-8 text-primary mb-2" />
              <CardTitle>High Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Lightning-fast responses with 99.9% uptime and global edge deployment.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Shield className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Secure & Reliable</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Enterprise-grade security with API key management and usage monitoring.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Globe className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Global Scale</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Worldwide infrastructure ensuring low latency for your users everywhere.
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="text-center bg-muted/30 rounded-lg p-8">
          <h2 className="text-3xl font-bold mb-4">Ready to Start Building?</h2>
          <p className="text-muted-foreground mb-6">
            Join thousands of developers using KasaAI to power their applications
          </p>
          <Button asChild size="lg">
            <Link to="/auth">Access Developer Console</Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Index;
