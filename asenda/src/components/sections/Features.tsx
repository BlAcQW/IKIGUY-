"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import {
  Brain,
  Globe,
  Zap,
  Lock,
  BarChart3,
  Plug,
  MessageSquare,
  Clock,
  Users,
  Layers,
  Workflow,
  HeartHandshake,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Advanced NLU",
    description: "Natural language understanding that grasps context, intent, and nuance in every conversation.",
  },
  {
    icon: Globe,
    title: "50+ Languages",
    description: "Communicate with customers in their native language, automatically detected and seamlessly switched.",
  },
  {
    icon: Zap,
    title: "Sub-second Response",
    description: "Lightning-fast processing ensures natural conversation flow without awkward pauses.",
  },
  {
    icon: Lock,
    title: "Enterprise Security",
    description: "SOC 2 Type II certified with end-to-end encryption and GDPR compliance built-in.",
  },
  {
    icon: BarChart3,
    title: "Real-time Analytics",
    description: "Deep insights into call performance, customer sentiment, and conversion metrics.",
  },
  {
    icon: Plug,
    title: "100+ Integrations",
    description: "Connect with your existing CRM, helpdesk, and business tools effortlessly.",
  },
  {
    icon: MessageSquare,
    title: "Omnichannel",
    description: "Unified experience across voice, chat, SMS, and email channels.",
  },
  {
    icon: Clock,
    title: "24/7 Availability",
    description: "Never miss a call. AI agents work round the clock without breaks or holidays.",
  },
  {
    icon: Users,
    title: "Human Handoff",
    description: "Smart escalation to human agents when needed, with full context transfer.",
  },
  {
    icon: Layers,
    title: "No-Code Builder",
    description: "Design custom conversation flows with our intuitive drag-and-drop interface.",
  },
  {
    icon: Workflow,
    title: "Custom Workflows",
    description: "Automate complex business processes triggered by voice interactions.",
  },
  {
    icon: HeartHandshake,
    title: "White Glove Support",
    description: "Dedicated success managers and 24/7 technical support for enterprise clients.",
  },
];

const integrations = [
  "Salesforce",
  "HubSpot",
  "Zendesk",
  "Slack",
  "Microsoft Teams",
  "Zapier",
  "Twilio",
  "AWS",
  "Google Cloud",
  "Shopify",
];

export default function Features() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section id="features" className="section relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 sm:mb-12 lg:mb-16"
        >
          <span className="text-primary text-sm font-semibold tracking-wider uppercase mb-3 sm:mb-4 block">
            Features
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 px-2">
            Enterprise-Grade Capabilities
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base sm:text-lg px-2">
            Everything you need to build, deploy, and scale intelligent voice AI
            experiences for your business.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-12 sm:mb-16 lg:mb-20">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="group p-4 sm:p-5 lg:p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-all card-hover"
            >
              <div className="w-10 sm:w-12 h-10 sm:h-12 rounded-lg sm:rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center mb-3 sm:mb-4 group-hover:from-primary/30 group-hover:to-secondary/30 transition-colors">
                <feature.icon className="w-5 sm:w-6 h-5 sm:h-6 text-primary" />
              </div>
              <h3 className="text-sm sm:text-base font-semibold text-white mb-1 sm:mb-2">{feature.title}</h3>
              <p className="text-xs sm:text-sm text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </div>

        {/* Integrations Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="gradient-border p-5 sm:p-8 md:p-12"
        >
          <div className="text-center mb-6 sm:mb-8 lg:mb-10">
            <h3 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-3 sm:mb-4">
              Seamless Integrations
            </h3>
            <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto px-2">
              Connect Asenda.ai with the tools you already use. No complex setup required.
            </p>
          </div>

          {/* Integration Logos */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4 mb-6 sm:mb-8">
            {integrations.map((integration, index) => (
              <motion.div
                key={integration}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={isInView ? { opacity: 1, scale: 1 } : {}}
                transition={{ duration: 0.3, delay: 0.4 + index * 0.05 }}
                className="p-4 rounded-xl bg-background border border-border hover:border-primary/30 transition-all flex items-center justify-center"
              >
                <span className="font-medium text-muted-foreground hover:text-white transition-colors">
                  {integration}
                </span>
              </motion.div>
            ))}
          </div>

          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              And 90+ more integrations available
            </p>
            <button className="btn-secondary inline-flex items-center gap-2">
              <Plug className="w-4 h-4" />
              View All Integrations
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
