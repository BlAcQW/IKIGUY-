"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play, Sparkles, Bot, Mic } from "lucide-react";
import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-grid">
      {/* Background Effects */}
      <div className="absolute inset-0">
        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "-3s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent/10 rounded-full blur-3xl" />
      </div>

      {/* Noise overlay */}
      <div className="absolute inset-0 noise-overlay" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10 pt-28 sm:pt-32 pb-16 md:pb-20">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-border mb-6 sm:mb-8"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">Introducing Voice AI 2.0</span>
            <ArrowRight className="w-4 h-4 text-muted-foreground" />
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight mb-5 sm:mb-6 leading-tight"
          >
            Transform Every Call with{" "}
            <span className="gradient-text">Intelligent AI Agents</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto mb-8 sm:mb-10 px-2"
          >
            Asenda.ai delivers enterprise-grade voice AI and automation solutions
            that handle customer support, sales calls, and marketing campaigns
            with human-like intelligence and 24/7 availability.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-12 sm:mb-16"
          >
            <Link
              href="#contact"
              className="btn-primary text-lg px-8 py-4 inline-flex items-center gap-2 group"
            >
              Start Free Trial
              <motion.span
                className="inline-block"
                animate={{ x: [0, 4, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <ArrowRight className="w-5 h-5" />
              </motion.span>
            </Link>
            <button className="btn-secondary text-lg px-8 py-4 inline-flex items-center gap-2 group">
              <Play className="w-5 h-5 group-hover:text-primary transition-colors" />
              Watch Demo
            </button>
          </motion.div>

          {/* Animated Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="relative max-w-4xl mx-auto"
          >
            {/* Main Card */}
            <div className="gradient-border p-5 sm:p-8 md:p-12">
              <div className="relative">
                {/* Voice Wave Animation */}
                <div className="flex items-center justify-center gap-4 mb-8">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center"
                  >
                    <Mic className="w-8 h-8 text-white" />
                  </motion.div>

                  {/* Sound waves */}
                  <div className="flex items-center gap-1">
                    {[...Array(12)].map((_, i) => (
                      <motion.div
                        key={i}
                        animate={{ height: [12, Math.random() * 40 + 20, 12] }}
                        transition={{
                          duration: 0.5,
                          repeat: Infinity,
                          delay: i * 0.05,
                        }}
                        className="w-1 bg-gradient-to-t from-primary to-secondary rounded-full"
                        style={{ height: 12 }}
                      />
                    ))}
                  </div>

                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                    className="w-16 h-16 rounded-full bg-card border border-border flex items-center justify-center"
                  >
                    <Bot className="w-8 h-8 text-secondary" />
                  </motion.div>
                </div>

                {/* Conversation Preview */}
                <div className="space-y-4 max-w-lg mx-auto text-left">
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 }}
                    className="bg-card rounded-lg rounded-bl-none p-4 border border-border"
                  >
                    <p className="text-sm text-muted-foreground mb-1">Customer</p>
                    <p className="text-white">&ldquo;Hi, I need help with my recent order. It hasn&apos;t arrived yet.&rdquo;</p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.2 }}
                    className="bg-gradient-to-br from-primary/20 to-secondary/20 rounded-lg rounded-br-none p-4 border border-primary/30 ml-auto max-w-sm"
                  >
                    <p className="text-sm text-primary mb-1">Asenda AI</p>
                    <p className="text-white">&ldquo;I&apos;d be happy to help! Let me check your order status. I see it&apos;s currently in transit and should arrive tomorrow.&rdquo;</p>
                  </motion.div>
                </div>
              </div>
            </div>

            {/* Floating Stats */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.5 }}
              className="absolute -left-4 top-1/4 glass rounded-lg p-4 hidden lg:block"
            >
              <p className="text-2xl font-bold gradient-text">98%</p>
              <p className="text-xs text-muted-foreground">Resolution Rate</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.7 }}
              className="absolute -right-4 top-1/2 glass rounded-lg p-4 hidden lg:block"
            >
              <p className="text-2xl font-bold gradient-text">24/7</p>
              <p className="text-xs text-muted-foreground">Always Available</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.9 }}
              className="absolute -bottom-4 left-1/2 -translate-x-1/2 glass rounded-lg p-4 hidden lg:block"
            >
              <p className="text-2xl font-bold gradient-text">5x</p>
              <p className="text-xs text-muted-foreground">Cost Savings</p>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
}
