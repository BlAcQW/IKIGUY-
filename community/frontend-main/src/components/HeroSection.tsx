import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Play, Users, Globe, Award, ArrowRight, Mic, FileText, Link } from "lucide-react";
import heroImage from "@/assets/hero-image.jpg";

const HeroSection = () => {
  return (
    <section className="relative overflow-hidden">
      {/* Hero Background */}
      <div className="absolute inset-0 z-0">
        <img 
          src={heroImage} 
          alt="African languages community collaboration" 
          className="w-full h-full object-cover opacity-20"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-20 lg:py-28">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Hero Content */}
          <div className="space-y-8 animate-fade-in">
            <div className="space-y-4">
              <Badge className="community-gradient text-foreground border-community-gold/30 px-4 py-2">
                <Globe className="h-4 w-4 mr-2" />
                100+ African Languages
              </Badge>
              
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                <span className="bg-gradient-to-r from-primary via-cultural-warm to-cultural-nature bg-clip-text text-transparent">
                  Preserve
                </span>
                <br />
                <span className="text-foreground">African Languages</span>
                <br />
                <span className="text-muted-foreground text-4xl lg:text-5xl">
                  Together
                </span>
              </h1>

              <p className="text-xl text-muted-foreground max-w-lg leading-relaxed">
                Join the world's largest community-driven platform for collecting and preserving African language data. 
                Your voice shapes the future of African AI.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button variant="hero" size="lg" className="group">
                <Play className="h-5 w-5 mr-2 group-hover:scale-110 transition-transform" />
                Start Contributing
                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              
              <Button variant="outline" size="lg" className="group">
                <Users className="h-5 w-5 mr-2" />
                Explore Languages
              </Button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-6 pt-8">
              <div className="text-center space-y-2">
                <div className="text-3xl font-bold text-primary">150K+</div>
                <div className="text-sm text-muted-foreground">Audio Samples</div>
              </div>
              <div className="text-center space-y-2">
                <div className="text-3xl font-bold text-cultural-warm">25+</div>
                <div className="text-sm text-muted-foreground">Languages</div>
              </div>
              <div className="text-center space-y-2">
                <div className="text-3xl font-bold text-cultural-nature">2.5K+</div>
                <div className="text-sm text-muted-foreground">Contributors</div>
              </div>
            </div>
          </div>

          {/* Hero Cards */}
          <div className="space-y-6 animate-slide-up">
            {/* Contribution Types */}
            <Card className="p-6 warm-shadow hover:elevation-shadow transition-all duration-300 border-border/50">
              <h3 className="text-lg font-semibold mb-4 text-foreground">Contribute Your Voice</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/50 hover:bg-accent transition-colors cursor-pointer">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Mic className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">Audio Recordings</div>
                    <div className="text-xs text-muted-foreground">Voice samples, stories, conversations</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/50 hover:bg-accent transition-colors cursor-pointer">
                  <div className="p-2 rounded-lg bg-cultural-warm/10">
                    <FileText className="h-4 w-4 text-cultural-warm" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">Text Content</div>
                    <div className="text-xs text-muted-foreground">Proverbs, translations, stories</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/50 hover:bg-accent transition-colors cursor-pointer">
                  <div className="p-2 rounded-lg bg-cultural-nature/10">
                    <Link className="h-4 w-4 text-cultural-nature" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">External Resources</div>
                    <div className="text-xs text-muted-foreground">Educational links, research</div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Quality System */}
            <Card className="p-6 warm-shadow hover:elevation-shadow transition-all duration-300 border-border/50">
              <h3 className="text-lg font-semibold mb-4 text-foreground">Quality Assurance</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-tier-1" />
                    <span className="text-sm font-medium">Gold Standard</span>
                  </div>
                  <Badge className="tier-1-badge text-xs">3+ Validators</Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-tier-2" />
                    <span className="text-sm font-medium">Community Reviewed</span>
                  </div>
                  <Badge className="tier-2-badge text-xs">2 Validators</Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Play className="h-4 w-4 text-tier-3" />
                    <span className="text-sm font-medium">Submitted</span>
                  </div>
                  <Badge className="tier-3-badge text-xs">Pending Review</Badge>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;