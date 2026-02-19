import { motion } from "framer-motion";
import { BookOpen, Users, Calendar, Heart, Sparkles, Shield, Facebook } from "lucide-react";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DonationSection } from "@/components/landing/DonationSection";
import { InviteToSpeak } from "@/components/landing/InviteToSpeak";
import { useNavigate } from "react-router-dom";

export default function About() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Calendar,
      title: "Daily Devotionals",
      description: "Fresh spiritual content delivered every day to nourish your faith journey"
    },
    {
      icon: Users,
      title: "Community Driven",
      description: "Connect with believers worldwide through comments, likes, and shared experiences"
    },
    {
      icon: Sparkles,
      title: "Gamification",
      description: "Track your reading streaks, earn achievements, and grow in your spiritual discipline"
    },
    {
      icon: Heart,
      title: "Personalized Experience",
      description: "Bookmark favorites, track reading history, and get recommendations tailored to you"
    },
    {
      icon: BookOpen,
      title: "Quality Content",
      description: "Carefully curated devotionals from trusted authors and spiritual leaders"
    },
    {
      icon: Shield,
      title: "Safe & Moderated",
      description: "All content is reviewed to ensure it aligns with biblical truth and values"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <div className="container py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="w-20 h-20 rounded-2xl bg-secondary flex items-center justify-center mx-auto mb-6">
            <BookOpen className="w-10 h-10 text-secondary-foreground" />
          </div>
          <h1 className="text-5xl font-serif font-bold text-foreground mb-4">
            About Devotionals with Suzanne and Dave
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            Your daily source of spiritual nourishment and biblical encouragement
          </p>
          <p className="text-lg text-muted-foreground leading-relaxed">
            FreshManna is led by Bishop Suzanne Nti and her husband Dave, who share daily 
            devotionals that inspire, encourage, and strengthen faith. Together, they take you 
            through God's Word, sharing their reflections, prayers, and biblical wisdom along 
            the way. We believe in the power of God's Word to transform lives, and our mission 
            is to make quality biblical content accessible to everyone, everywhere.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-16"
        >
          <h2 className="text-3xl font-serif font-bold text-center text-foreground mb-12">
            Why Choose FreshManna?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <Card className="h-full hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 rounded-lg bg-secondary/20 flex items-center justify-center mb-4">
                      <feature.icon className="w-6 h-6 text-secondary-foreground" />
                    </div>
                    <h3 className="font-bold text-lg text-foreground mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Our Mission */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-secondary/10 rounded-2xl p-12 mb-16 text-center"
        >
          <h2 className="text-3xl font-serif font-bold text-foreground mb-4">
            Our Mission
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            To empower believers around the world with daily spiritual nourishment through
            quality devotionals, fostering a community of faith that grows together in Christ.
            We strive to make biblical wisdom accessible, engaging, and practical for everyday life.
          </p>
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-center max-w-2xl mx-auto"
        >
          <h2 className="text-3xl font-serif font-bold text-foreground mb-4">
            Ready to Start Your Journey?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join thousands of believers who are growing in their faith with FreshManna
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="lg" onClick={() => navigate('/auth')}>
              Get Started Free
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/browse')}>
              Browse Devotionals
            </Button>
            <a
              href="https://www.facebook.com/profile.php?id=61563563450448"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#1877F2] hover:bg-[#1877F2]/90 text-white transition-colors"
              aria-label="Follow us on Facebook"
            >
              <Facebook className="w-5 h-5" />
              <span>Follow on Facebook</span>
            </a>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 pt-16 border-t border-border"
        >
          <div className="text-center">
            <div className="text-4xl font-bold text-foreground mb-2">500+</div>
            <div className="text-sm text-muted-foreground">Devotionals</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-foreground mb-2">10K+</div>
            <div className="text-sm text-muted-foreground">Active Users</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-foreground mb-2">50K+</div>
            <div className="text-sm text-muted-foreground">Devotionals Read</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-foreground mb-2">99%</div>
            <div className="text-sm text-muted-foreground">Satisfaction Rate</div>
          </div>
        </motion.div>

        {/* Donation Section */}
        <DonationSection />

        {/* Invite to Speak Section */}
        <InviteToSpeak />
      </div>
    </div>
  );
}
