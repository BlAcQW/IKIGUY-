import { motion } from "framer-motion";
import { Play, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import heroBackground from "@/assets/hero-background.jpg";

const Hero = () => {
  return (
    <section className="relative min-h-[50vh] sm:min-h-[60vh] md:min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0">
        <img
          src={heroBackground}
          alt="Spiritual sunrise through clouds"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-primary/80 via-primary/70 to-primary/90" />
        <div className="absolute inset-0 bg-gradient-to-r from-primary/50 via-transparent to-primary/50" />
      </div>

      {/* Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{ y: [-10, 10, -10] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-secondary/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [10, -10, 10] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl"
        />
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 pt-12 pb-6 md:pt-20 md:pb-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-foreground/20 border border-primary-foreground/30 backdrop-blur-sm mb-8"
          >
            <Sparkles className="w-4 h-4 text-primary-foreground" />
            <span className="text-sm font-medium text-primary-foreground/90">
              Start every day in God's Word
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-serif text-2xl sm:text-3xl md:text-6xl lg:text-7xl font-bold text-primary-foreground leading-tight mb-3 md:mb-6"
          >
            Devotionals with{" "}
            <span className="text-primary-foreground drop-shadow-lg">Suzanne and Dave</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-sm sm:text-base md:text-lg lg:text-xl text-primary-foreground/80 max-w-2xl mx-auto mb-4 md:mb-10 leading-relaxed"
          >
            Join Suzanne and Dave on an inspiring and adventurous journey through the bible, one day at a time.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button variant="hero" size="xl" asChild>
              <a href="/auth">
                Join FreshManna Free
                <ArrowRight className="w-5 h-5" />
              </a>
            </Button>
            <Button variant="heroOutline" size="xl" asChild>
              <a href="#preview">
                <Play className="w-5 h-5" />
                See How It Works
              </a>
            </Button>
          </motion.div>

          {/* Trust Indicators - Hidden on mobile for app-like feel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="hidden md:block mt-12 md:mt-16 pt-6 md:pt-8 border-t border-primary-foreground/10"
          >
            <p className="text-sm text-primary-foreground/60 mb-4">
              Join thousands growing in faith together
            </p>
            <div className="flex flex-wrap items-center justify-center gap-8 text-primary-foreground/40">
              <div className="text-center">
                <div className="font-serif text-3xl font-bold text-primary-foreground">150K+</div>
                <div className="text-sm">Believers</div>
              </div>
              <div className="w-px h-12 bg-primary-foreground/20" />
              <div className="text-center">
                <div className="font-serif text-3xl font-bold text-primary-foreground">1M+</div>
                <div className="text-sm">Devotionals Enjoyed</div>
              </div>
              <div className="w-px h-12 bg-primary-foreground/20" />
              <div className="text-center">
                <div className="font-serif text-3xl font-bold text-primary-foreground">500+</div>
                <div className="text-sm">Study Groups</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
};

export default Hero;
