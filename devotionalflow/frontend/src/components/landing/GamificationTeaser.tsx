/**
 * Gamification Teaser Component
 * Showcases streak system, achievements, and community engagement
 * Encourages sign-up by highlighting gamification features
 */

import { motion } from "framer-motion";
import { Flame, Trophy, Target, Users, ArrowRight, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

const features = [
  {
    icon: Flame,
    title: "Build Your Streak",
    description: "Read daily and watch your streak grow. Get rewards for consistency!",
    stat: "127 days",
    label: "Sarah's streak",
    color: "text-secondary",
    bgColor: "bg-secondary/10"
  },
  {
    icon: Trophy,
    title: "Unlock Achievements",
    description: "Earn badges and rewards as you grow in your faith journey.",
    stat: "20+",
    label: "achievements",
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10"
  },
  {
    icon: Target,
    title: "Level Up",
    description: "Complete daily challenges and climb through 100 spiritual levels.",
    stat: "Level 45",
    label: "John's level",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10"
  }
];

const GamificationTeaser = () => {
  const navigate = useNavigate();

  return (
    <section className="py-8 md:py-16 bg-gradient-to-b from-muted/30 to-background">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20 mb-4">
            <Zap className="w-4 h-4 text-secondary" />
            <span className="text-sm font-medium text-secondary">
              Track Your Spiritual Growth
            </span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl lg:text-4xl font-bold text-foreground mb-4">
            Turn Daily Devotions into a{" "}
            <span className="text-gradient-gold">Life-Changing Habit</span>
          </h2>
          <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
            Join 50,000+ believers building spiritual habits with streaks, achievements, and daily challenges
          </p>
        </motion.div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-card rounded-2xl border border-border/50 p-6 hover:shadow-lg transition-all duration-200"
              >
                <div className={cn(
                  "w-14 h-14 rounded-2xl flex items-center justify-center mb-4",
                  feature.bgColor
                )}>
                  <Icon className={cn("w-7 h-7", feature.color)} />
                </div>
                <h3 className="font-serif text-xl font-bold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {feature.description}
                </p>
                <div className="flex items-baseline gap-2">
                  <span className={cn("text-2xl font-bold", feature.color)}>
                    {feature.stat}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {feature.label}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Community Stats Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="bg-card rounded-2xl border border-border/50 p-6 md:p-8"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex-1 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-3">
                <Users className="w-5 h-5 text-secondary" />
                <h3 className="font-serif text-xl font-bold text-foreground">
                  Join an Active Community
                </h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                See how you rank, celebrate milestones together, and encourage fellow believers on their journey
              </p>
              <div className="grid grid-cols-3 gap-4 md:gap-6 text-center">
                <div>
                  <div className="font-serif text-2xl md:text-3xl font-bold text-secondary">50K+</div>
                  <div className="text-xs text-muted-foreground">Active users</div>
                </div>
                <div>
                  <div className="font-serif text-2xl md:text-3xl font-bold text-accent">2.1M</div>
                  <div className="text-xs text-muted-foreground">Devotionals read</div>
                </div>
                <div>
                  <div className="font-serif text-2xl md:text-3xl font-bold text-secondary">127</div>
                  <div className="text-xs text-muted-foreground">Avg. streak days</div>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-3 w-full md:w-auto">
              <Button
                onClick={() => navigate('/auth')}
                size="lg"
                className="w-full md:w-auto gap-2"
              >
                Start Your Journey
                <ArrowRight className="w-4 h-4" />
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                Free forever • No credit card required
              </p>
            </div>
          </div>
        </motion.div>

        {/* Achievement Preview Badges */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8 flex justify-center gap-4 flex-wrap"
        >
          {[
            { name: "Ignited", emoji: "🔥", color: "bg-secondary/10 border-secondary/30" },
            { name: "Devoted", emoji: "⭐", color: "bg-yellow-500/10 border-yellow-500/30" },
            { name: "Warrior", emoji: "⚔️", color: "bg-purple-500/10 border-purple-500/30" },
            { name: "Scholar", emoji: "📚", color: "bg-blue-500/10 border-blue-500/30" }
          ].map((badge, index) => (
            <motion.div
              key={badge.name}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.6 + index * 0.1 }}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full border",
                badge.color
              )}
            >
              <span className="text-xl">{badge.emoji}</span>
              <span className="text-sm font-medium text-foreground">{badge.name}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default GamificationTeaser;
