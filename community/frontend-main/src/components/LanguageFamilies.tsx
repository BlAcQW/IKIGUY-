import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  TreePine, 
  Globe, 
  Users, 
  BarChart3, 
  ArrowRight,
  Mic,
  FileText,
  Star
} from "lucide-react";

const languageFamilies = [
  {
    id: "niger-congo",
    name: "Niger-Congo",
    description: "The largest African language family with over 1,500 languages",
    subfamilies: ["Kwa", "Yoruboid", "Bantu"],
    languages: [
      { name: "Twi", speakers: "9M", progress: 85, tier: "tier-1" },
      { name: "Yoruba", speakers: "46M", progress: 78, tier: "tier-1" },
      { name: "Swahili", speakers: "98M", progress: 92, tier: "tier-1" },
      { name: "Ga", speakers: "745K", progress: 45, tier: "tier-2" },
    ],
    totalContributions: 125000,
    activeContributors: 1850,
    color: "primary"
  },
  {
    id: "afroasiatic",
    name: "Afroasiatic",
    description: "Ancient language family spanning North and East Africa",
    subfamilies: ["Cushitic", "Chadic", "Berber"],
    languages: [
      { name: "Amharic", speakers: "32M", progress: 65, tier: "tier-2" },
      { name: "Hausa", speakers: "63M", progress: 58, tier: "tier-2" },
      { name: "Oromo", speakers: "37M", progress: 42, tier: "tier-3" },
      { name: "Somali", speakers: "21M", progress: 35, tier: "tier-3" },
    ],
    totalContributions: 45000,
    activeContributors: 680,
    color: "cultural-warm"
  },
  {
    id: "nilo-saharan",
    name: "Nilo-Saharan",
    description: "Diverse family across the Sahel and Eastern Africa",
    subfamilies: ["Nilotic", "Central Sudanic"],
    languages: [
      { name: "Dinka", speakers: "2M", progress: 25, tier: "tier-3" },
      { name: "Luo", speakers: "4.2M", progress: 30, tier: "tier-3" },
      { name: "Kanuri", speakers: "4.8M", progress: 20, tier: "tier-3" },
    ],
    totalContributions: 15000,
    activeContributors: 280,
    color: "cultural-nature"
  }
];

const LanguageFamilies = () => {
  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center space-y-4 mb-16">
          <Badge className="community-gradient text-foreground border-community-gold/30 px-4 py-2">
            <TreePine className="h-4 w-4 mr-2" />
            Language Families
          </Badge>
          
          <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
            Organized by
            <span className="bg-gradient-to-r from-primary to-cultural-warm bg-clip-text text-transparent"> Linguistic Heritage</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Our platform organizes African languages by their family relationships, 
            enabling better transfer learning and preserving cultural connections.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {languageFamilies.map((family) => (
            <Card key={family.id} className="p-6 space-y-6 warm-shadow hover:elevation-shadow transition-all duration-300 border-border/50 group">
              {/* Family Header */}
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">
                      {family.name}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {family.description}
                    </p>
                  </div>
                  <div className={`p-2 rounded-lg bg-${family.color}/10`}>
                    <Globe className={`h-5 w-5 text-${family.color}`} />
                  </div>
                </div>

                {/* Subfamilies */}
                <div className="flex flex-wrap gap-2">
                  {family.subfamilies.map((subfamily) => (
                    <Badge key={subfamily} variant="outline" className="text-xs">
                      {subfamily}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Languages Preview */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Mic className="h-4 w-4" />
                  Top Languages
                </h4>
                
                {family.languages.slice(0, 3).map((language) => (
                  <div key={language.name} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{language.name}</span>
                        <Badge className={`${language.tier}-badge text-xs`}>
                          {language.tier === 'tier-1' ? 'Gold' : 
                           language.tier === 'tier-2' ? 'Community' : 'Submitted'}
                        </Badge>
                      </div>
                      <span className="text-muted-foreground text-xs">{language.speakers}</span>
                    </div>
                    <Progress value={language.progress} className="h-2" />
                  </div>
                ))}
                
                {family.languages.length > 3 && (
                  <div className="text-center pt-2">
                    <span className="text-xs text-muted-foreground">
                      +{family.languages.length - 3} more languages
                    </span>
                  </div>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                <div className="text-center space-y-1">
                  <div className="flex items-center justify-center gap-1">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-lg font-bold text-foreground">
                      {family.totalContributions.toLocaleString()}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">Contributions</div>
                </div>
                
                <div className="text-center space-y-1">
                  <div className="flex items-center justify-center gap-1">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-lg font-bold text-foreground">
                      {family.activeContributors.toLocaleString()}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">Contributors</div>
                </div>
              </div>

              {/* Action Button */}
              <Button variant="outline" className="w-full group-hover:border-primary group-hover:text-primary transition-colors">
                Explore Family
                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Card>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button variant="hero" size="lg">
            <TreePine className="h-5 w-5 mr-2" />
            Explore All Language Families
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </section>
  );
};

export default LanguageFamilies;