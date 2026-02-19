"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useState } from "react";
import {
  Headphones,
  Phone,
  Megaphone,
  Calendar,
  ShieldCheck,
  Zap,
  ArrowRight,
} from "lucide-react";

const services = [
  {
    id: "helpdesk",
    icon: Headphones,
    title: "AI Helpdesk",
    description: "Intelligent customer support that resolves issues instantly, 24/7.",
    features: [
      "Natural language understanding",
      "Multi-language support",
      "Seamless human handoff",
      "Knowledge base integration",
    ],
    color: "from-blue-500 to-cyan-500",
    stats: { value: "85%", label: "First-call resolution" },
  },
  {
    id: "sales",
    icon: Phone,
    title: "Voice AI Sales",
    description: "Convert leads into customers with personalized AI-powered sales calls.",
    features: [
      "Lead qualification",
      "Objection handling",
      "CRM integration",
      "Real-time analytics",
    ],
    color: "from-purple-500 to-pink-500",
    stats: { value: "3x", label: "Conversion increase" },
  },
  {
    id: "marketing",
    icon: Megaphone,
    title: "Marketing Automation",
    description: "Scale your outreach with intelligent voice campaigns and follow-ups.",
    features: [
      "Automated follow-ups",
      "Personalized messaging",
      "Campaign analytics",
      "A/B testing",
    ],
    color: "from-orange-500 to-red-500",
    stats: { value: "10x", label: "Outreach capacity" },
  },
  {
    id: "scheduling",
    icon: Calendar,
    title: "Smart Scheduling",
    description: "AI agents that book appointments and manage calendars effortlessly.",
    features: [
      "Calendar integration",
      "Timezone management",
      "Rescheduling handling",
      "Reminder automation",
    ],
    color: "from-green-500 to-emerald-500",
    stats: { value: "95%", label: "Booking accuracy" },
  },
  {
    id: "verification",
    icon: ShieldCheck,
    title: "Identity Verification",
    description: "Secure voice-based authentication and verification services.",
    features: [
      "Voice biometrics",
      "Multi-factor auth",
      "Fraud detection",
      "Compliance ready",
    ],
    color: "from-indigo-500 to-violet-500",
    stats: { value: "99.9%", label: "Security rate" },
  },
  {
    id: "custom",
    icon: Zap,
    title: "Custom AI Agents",
    description: "Tailored voice AI solutions designed for your unique business needs.",
    features: [
      "Custom workflows",
      "Industry-specific training",
      "API access",
      "White-label options",
    ],
    color: "from-cyan-500 to-blue-500",
    stats: { value: "100%", label: "Customizable" },
  },
];

export default function Services() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });
  const [activeService, setActiveService] = useState(services[0].id);

  const activeServiceData = services.find((s) => s.id === activeService)!;

  return (
    <section id="services" className="section relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-secondary/10 rounded-full blur-3xl" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 sm:mb-12 lg:mb-16"
        >
          <span className="text-primary text-sm font-semibold tracking-wider uppercase mb-3 sm:mb-4 block">
            Our Services
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 px-2">
            Voice AI Solutions for Every Need
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base sm:text-lg px-2">
            From customer support to sales automation, our AI agents handle it all
            with human-like intelligence and efficiency.
          </p>
        </motion.div>

        {/* Services Tabs - Desktop */}
        <div className="hidden lg:grid lg:grid-cols-3 gap-8">
          {/* Service Selector */}
          <div className="space-y-3">
            {services.map((service, index) => (
              <motion.button
                key={service.id}
                initial={{ opacity: 0, x: -20 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                onClick={() => setActiveService(service.id)}
                className={`w-full text-left p-4 rounded-xl transition-all ${
                  activeService === service.id
                    ? "bg-card border border-primary/50 shadow-lg shadow-primary/10"
                    : "bg-transparent border border-transparent hover:bg-card/50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-lg bg-gradient-to-br ${service.color} flex items-center justify-center`}
                  >
                    <service.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{service.title}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {service.description}
                    </p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>

          {/* Active Service Detail */}
          <motion.div
            key={activeService}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="col-span-2 gradient-border p-8"
          >
            <div className="flex items-start gap-6 mb-8">
              <div
                className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${activeServiceData.color} flex items-center justify-center flex-shrink-0`}
              >
                <activeServiceData.icon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">
                  {activeServiceData.title}
                </h3>
                <p className="text-muted-foreground text-lg">
                  {activeServiceData.description}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                  Key Features
                </h4>
                <ul className="space-y-3">
                  {activeServiceData.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-br ${activeServiceData.color}`} />
                      <span className="text-white">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex flex-col justify-between">
                <div className="text-center p-6 bg-background rounded-xl border border-border">
                  <div className={`text-4xl font-bold bg-gradient-to-r ${activeServiceData.color} bg-clip-text text-transparent`}>
                    {activeServiceData.stats.value}
                  </div>
                  <p className="text-muted-foreground mt-1">
                    {activeServiceData.stats.label}
                  </p>
                </div>
                <button className="btn-primary mt-6 flex items-center justify-center gap-2">
                  Learn More
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Services Cards - Mobile */}
        <div className="lg:hidden grid sm:grid-cols-2 gap-4 sm:gap-6">
          {services.map((service, index) => (
            <motion.div
              key={service.id}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              className="gradient-border p-4 sm:p-6 card-hover"
            >
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${service.color} flex items-center justify-center mb-4`}
              >
                <service.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">
                {service.title}
              </h3>
              <p className="text-muted-foreground text-sm mb-4">
                {service.description}
              </p>
              <div className="flex items-center justify-between pt-4 border-t border-border">
                <div>
                  <span className={`text-lg font-bold bg-gradient-to-r ${service.color} bg-clip-text text-transparent`}>
                    {service.stats.value}
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {service.stats.label}
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
