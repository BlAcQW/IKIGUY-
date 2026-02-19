import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Github, 
  Twitter, 
  Mail, 
  Heart, 
  Globe,
  BookOpen,
  Users,
  Shield
} from "lucide-react";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-muted/30 border-t border-border/50">
      <div className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center text-primary-foreground font-bold text-sm">
                AL
              </div>
              <div className="flex flex-col">
                <h3 className="text-lg font-bold text-foreground">AfriLang</h3>
                <p className="text-xs text-muted-foreground -mt-1">Community</p>
              </div>
            </div>
            
            <p className="text-sm text-muted-foreground leading-relaxed">
              Preserving African languages through community collaboration. 
              Building the future of African voice AI together.
            </p>

            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon">
                <Github className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Twitter className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Mail className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Platform */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">Platform</h4>
            <nav className="space-y-2">
              <a href="/languages" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Browse Languages
              </a>
              <a href="/submit" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Contribute Data
              </a>
              <a href="/validate" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Validate Submissions
              </a>
              <a href="/quality" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Quality Standards
              </a>
            </nav>
          </div>

          {/* Community */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">Community</h4>
            <nav className="space-y-2">
              <a href="/leaderboard" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Leaderboard
              </a>
              <a href="/achievements" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Achievements
              </a>
              <a href="/forums" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Discussion Forums
              </a>
              <a href="/events" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Community Events
              </a>
            </nav>
          </div>

          {/* Resources */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-foreground">Resources</h4>
            <nav className="space-y-2">
              <a href="/docs" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Documentation
              </a>
              <a href="/api" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                API Reference
              </a>
              <a href="/research" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Research Papers
              </a>
              <a href="/guidelines" className="block text-sm text-muted-foreground hover:text-primary transition-colors">
                Guidelines
              </a>
            </nav>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="mt-12 pt-8 border-t border-border/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>© {currentYear} AfriLang Community Platform</span>
              <span>•</span>
              <a href="/privacy" className="hover:text-primary transition-colors">Privacy Policy</a>
              <span>•</span>
              <a href="/terms" className="hover:text-primary transition-colors">Terms of Service</a>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Made with</span>
              <Heart className="h-4 w-4 text-cultural-warm fill-current" />
              <span className="text-muted-foreground">for African languages</span>
            </div>
          </div>

          {/* Stats Summary */}
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-6 p-6 rounded-lg bg-primary/5 border border-primary/10">
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1">
                <Globe className="h-4 w-4 text-primary" />
                <span className="text-lg font-bold text-foreground">25+</span>
              </div>
              <div className="text-xs text-muted-foreground">Languages</div>
            </div>
            
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1">
                <Users className="h-4 w-4 text-cultural-warm" />
                <span className="text-lg font-bold text-foreground">2.5K+</span>
              </div>
              <div className="text-xs text-muted-foreground">Contributors</div>
            </div>
            
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1">
                <BookOpen className="h-4 w-4 text-cultural-nature" />
                <span className="text-lg font-bold text-foreground">150K+</span>
              </div>
              <div className="text-xs text-muted-foreground">Contributions</div>
            </div>
            
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1">
                <Shield className="h-4 w-4 text-community-gold" />
                <span className="text-lg font-bold text-foreground">98%</span>
              </div>
              <div className="text-xs text-muted-foreground">Quality Score</div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;