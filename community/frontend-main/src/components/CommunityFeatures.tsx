import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Trophy, 
  Target, 
  Users, 
  MessageSquare, 
  Star,
  Award,
  TrendingUp,
  Clock,
  Heart,
  Zap
} from "lucide-react";

const CommunityFeatures = () => {
  const leaderboard = [
    { name: "Kwame Asante", language: "Twi", contributions: 1247, tier: "tier-1", avatar: "KA" },
    { name: "Amina Hassan", language: "Hausa", contributions: 982, tier: "tier-1", avatar: "AH" },
    { name: "Chike Okafor", language: "Yoruba", contributions: 876, tier: "tier-2", avatar: "CO" },
    { name: "Fatima Diallo", language: "Wolof", contributions: 743, tier: "tier-2", avatar: "FD" },
    { name: "Mwangi Kimani", language: "Swahili", contributions: 689, tier: "tier-3", avatar: "MK" }
  ];

  const achievements = [
    { name: "Cultural Keeper", description: "Preserved 100+ traditional stories", icon: Heart, earned: true },
    { name: "Voice Champion", description: "Recorded 500+ audio samples", icon: Trophy, earned: true },
    { name: "Community Leader", description: "Helped 50+ new contributors", icon: Users, earned: false },
    { name: "Quality Guardian", description: "Validated 1000+ submissions", icon: Star, earned: false }
  ];

  const recentActivity = [
    { user: "Adaora", action: "validated", content: "Igbo proverb collection", time: "2 min ago" },
    { user: "Mensah", action: "contributed", content: "Ga traditional song", time: "5 min ago" },
    { user: "Zainab", action: "achieved", content: "Voice Champion badge", time: "12 min ago" },
    { user: "Kofi", action: "submitted", content: "Twi conversation", time: "18 min ago" }
  ];

  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <div className="text-center space-y-4 mb-16">
          <Badge className="community-gradient text-foreground border-community-gold/30 px-4 py-2">
            <Users className="h-4 w-4 mr-2" />
            Community Spirit
          </Badge>
          
          <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
            Powered by
            <span className="bg-gradient-to-r from-community-gold to-primary bg-clip-text text-transparent"> Community</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Join thousands of language enthusiasts working together to preserve African linguistic heritage. 
            Earn recognition, compete friendly, and make lasting connections.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Leaderboard */}
          <Card className="p-6 space-y-6 warm-shadow hover:elevation-shadow transition-all duration-300">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Trophy className="h-5 w-5 text-community-gold" />
                Top Contributors
              </h3>
              <Button variant="ghost" size="sm">View All</Button>
            </div>

            <div className="space-y-4">
              {leaderboard.map((contributor, index) => (
                <div key={contributor.name} className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`
                      flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold
                      ${index === 0 ? 'bg-community-gold text-primary-foreground' : 
                        index === 1 ? 'bg-community-silver text-foreground' :
                        index === 2 ? 'bg-community-bronze text-primary-foreground' :
                        'bg-muted text-muted-foreground'}
                    `}>
                      {index < 3 ? index + 1 : contributor.avatar}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{contributor.name}</span>
                        <Badge className={`${contributor.tier}-badge text-xs`}>
                          {contributor.language}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {contributor.contributions} contributions
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="community" className="w-full">
              <TrendingUp className="h-4 w-4 mr-2" />
              Join Leaderboard
            </Button>
          </Card>

          {/* Achievements */}
          <Card className="p-6 space-y-6 warm-shadow hover:elevation-shadow transition-all duration-300">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Award className="h-5 w-5 text-primary" />
                Achievements
              </h3>
              <Badge variant="outline" className="text-xs">4/12 Earned</Badge>
            </div>

            <div className="space-y-4">
              {achievements.map((achievement) => (
                <div key={achievement.name} className={`
                  flex items-center gap-3 p-3 rounded-lg border transition-all
                  ${achievement.earned 
                    ? 'bg-primary/5 border-primary/20 text-foreground' 
                    : 'bg-muted/30 border-border/50 text-muted-foreground'
                  }
                `}>
                  <div className={`
                    p-2 rounded-lg 
                    ${achievement.earned 
                      ? 'bg-primary/10 text-primary' 
                      : 'bg-muted text-muted-foreground'
                    }
                  `}>
                    <achievement.icon className="h-4 w-4" />
                  </div>
                  
                  <div className="flex-1">
                    <div className="text-sm font-medium">{achievement.name}</div>
                    <div className="text-xs opacity-75">{achievement.description}</div>
                  </div>

                  {achievement.earned && (
                    <div className="text-community-gold">
                      <Star className="h-4 w-4 fill-current" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Progress to next achievement</span>
                <span className="font-medium">75%</span>
              </div>
              <Progress value={75} className="h-2" />
            </div>
          </Card>

          {/* Recent Activity */}
          <Card className="p-6 space-y-6 warm-shadow hover:elevation-shadow transition-all duration-300">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Zap className="h-5 w-5 text-cultural-nature" />
                Live Activity
              </h3>
              <div className="flex items-center gap-1 text-xs text-cultural-nature">
                <div className="w-2 h-2 bg-cultural-nature rounded-full animate-pulse"></div>
                Live
              </div>
            </div>

            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-medium text-primary">
                      {activity.user.substring(0, 2)}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">
                      <span className="font-medium text-foreground">{activity.user}</span>
                      <span className="text-muted-foreground"> {activity.action} </span>
                      <span className="text-primary">{activity.content}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <Clock className="h-3 w-3" />
                      {activity.time}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="outline" className="w-full">
              <MessageSquare className="h-4 w-4 mr-2" />
              Join Discussion
            </Button>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default CommunityFeatures;