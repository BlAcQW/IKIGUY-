import React from 'react';
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowRight, 
  Bot, 
  Users, 
  Globe, 
  Award,
  Heart,
  Lightbulb,
  Target,
  Zap
} from "lucide-react";

const About = () => {
  const team = [
    {
      name: "Dr. Amara Okafor",
      role: "Co-Founder & CEO",
      bio: "Former Google AI researcher with 10+ years in conversational AI",
      image: "👩🏾‍💼"
    },
    {
      name: "Kwame Asante", 
      role: "Co-Founder & CTO",
      bio: "Ex-Microsoft engineer, specialist in scalable voice technologies",
      image: "👨🏿‍💻"
    },
    {
      name: "Fatima Al-Zahra",
      role: "Head of Product",
      bio: "Previously at Stripe, passionate about user-centric design",
      image: "👩🏽‍🎨"
    },
    {
      name: "Chen Wei",
      role: "Lead AI Engineer", 
      bio: "PhD in NLP, expert in multilingual voice synthesis",
      image: "👨🏻‍🔬"
    }
  ];

  const values = [
    {
      icon: <Heart className="h-8 w-8" />,
      title: "Human-Centered AI",
      description: "Technology should enhance human connections, not replace them"
    },
    {
      icon: <Globe className="h-8 w-8" />,
      title: "Global Accessibility", 
      description: "Making AI accessible to businesses of all sizes, everywhere"
    },
    {
      icon: <Lightbulb className="h-8 w-8" />,
      title: "Continuous Innovation",
      description: "Always pushing the boundaries of what's possible with AI"
    },
    {
      icon: <Target className="h-8 w-8" />,
      title: "Results-Driven",
      description: "Focused on delivering measurable impact for our customers"
    }
  ];

  const milestones = [
    { year: "2022", title: "Founded", description: "AI Labs Africa established in Lagos" },
    { year: "2023", title: "First Product", description: "Launched voice AI platform for enterprises" },
    { year: "2024", title: "KasaAI Beta", description: "Released self-serve platform for SMEs" },
    { year: "2024", title: "Global Expansion", description: "Serving customers across 15+ countries" }
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
              <Link to="/pricing" className="text-gray-600 hover:text-foreground transition-colors">Pricing</Link>
              <Link to="/about" className="text-foreground font-medium">About</Link>
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
            <Zap className="h-3 w-3 mr-1" />
            AI Labs Africa
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
            Democratizing AI for
            <span className="bg-gradient-hero bg-clip-text text-transparent"> African Businesses</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            We're on a mission to make advanced AI accessible to every business, 
            from Lagos startups to global enterprises. KasaAI is our flagship platform 
            for creating intelligent voice and chat assistants.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">Our Mission</h2>
              <p className="text-lg text-gray-600 leading-relaxed">
                Too many businesses struggle with customer engagement due to limited resources 
                and outdated tools. We believe every business deserves access to AI technology 
                that can transform how they connect with their customers.
              </p>
              <p className="text-lg text-gray-600 leading-relaxed">
                KasaAI makes it possible for any business to deploy sophisticated AI assistants 
                in minutes, not months. No technical expertise required.
              </p>
              <div className="flex items-center space-x-6 text-sm">
                <div className="flex items-center space-x-2">
                  <Award className="h-5 w-5 text-accent" />
                  <span className="font-medium">500+ Businesses Served</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-accent" />
                  <span className="font-medium">15+ Countries</span>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-primary/10 to-accent/10 rounded-2xl p-8 text-center">
                <div className="text-6xl mb-4">🌍</div>
                <h3 className="text-2xl font-bold mb-4">Global Impact</h3>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">2M+</div>
                    <div className="text-sm text-gray-600">Conversations</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">87%</div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">24/7</div>
                    <div className="text-sm text-gray-600">Availability</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">50+</div>
                    <div className="text-sm text-gray-600">Languages</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Values</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              The principles that guide everything we build
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardHeader className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-primary rounded-xl mb-4 mx-auto">
                    <div className="text-white">
                      {value.icon}
                    </div>
                  </div>
                  <CardTitle className="text-lg">{value.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center">
                    {value.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Meet Our Team</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Passionate innovators from around the world
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {team.map((member, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardHeader className="text-center">
                  <div className="text-6xl mb-4">{member.image}</div>
                  <CardTitle className="text-lg">{member.name}</CardTitle>
                  <Badge variant="secondary">{member.role}</Badge>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center text-sm">
                    {member.bio}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-16 px-4 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Journey</h2>
            <p className="text-xl text-gray-600">
              Building the future of AI, one milestone at a time
            </p>
          </div>
          <div className="space-y-6">
            {milestones.map((milestone, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200">
                <CardContent className="p-6">
                  <div className="flex items-start space-x-4">
                    <Badge variant="outline" className="text-indigo-600 border-primary">
                      {milestone.year}
                    </Badge>
                    <div>
                      <h3 className="font-semibold text-lg mb-1">{milestone.title}</h3>
                      <p className="text-gray-600">{milestone.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-hero">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Join Our Mission
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Be part of the AI revolution. Start building your intelligent assistant today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="glass" size="lg" className="text-lg px-8" asChild>
              <Link to="/auth">
                Get Started Now
                <ArrowRight className="h-5 w-5 ml-2" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" className="bg-white text-indigo-600 hover:bg-gray-50 text-lg px-8">
              Contact Our Team
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;