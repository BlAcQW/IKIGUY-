"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import {
  Building2,
  Stethoscope,
  ShoppingCart,
  Landmark,
  GraduationCap,
  Plane,
  ArrowRight,
} from "lucide-react";

const industries = [
  {
    icon: Building2,
    title: "Enterprise",
    description:
      "Scale customer operations with AI that handles millions of interactions while maintaining brand consistency.",
    useCases: ["IT Support Automation", "Employee Helpdesk", "Vendor Management"],
    color: "from-blue-500 to-indigo-500",
  },
  {
    icon: Stethoscope,
    title: "Healthcare",
    description:
      "HIPAA-compliant voice AI for patient scheduling, prescription refills, and appointment reminders.",
    useCases: ["Patient Scheduling", "Prescription Refills", "Care Follow-ups"],
    color: "from-emerald-500 to-teal-500",
  },
  {
    icon: ShoppingCart,
    title: "E-Commerce",
    description:
      "Turn customer service into a revenue driver with AI that upsells, handles returns, and provides personalized support.",
    useCases: ["Order Support", "Product Recommendations", "Returns Processing"],
    color: "from-orange-500 to-amber-500",
  },
  {
    icon: Landmark,
    title: "Financial Services",
    description:
      "Secure, compliant voice AI for account inquiries, fraud alerts, and financial guidance.",
    useCases: ["Account Services", "Fraud Detection", "Loan Processing"],
    color: "from-violet-500 to-purple-500",
  },
  {
    icon: GraduationCap,
    title: "Education",
    description:
      "Support students and parents with enrollment assistance, course information, and administrative queries.",
    useCases: ["Enrollment Support", "Course Registration", "Parent Communication"],
    color: "from-pink-500 to-rose-500",
  },
  {
    icon: Plane,
    title: "Travel & Hospitality",
    description:
      "Deliver exceptional guest experiences with AI-powered booking, concierge, and support services.",
    useCases: ["Booking Assistance", "Concierge Services", "Travel Updates"],
    color: "from-cyan-500 to-sky-500",
  },
];

export default function Solutions() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section id="solutions" className="section bg-card relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-grid opacity-30" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 sm:mb-12 lg:mb-16"
        >
          <span className="text-primary text-sm font-semibold tracking-wider uppercase mb-3 sm:mb-4 block">
            Industry Solutions
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 px-2">
            Built for Your Industry
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base sm:text-lg px-2">
            Pre-trained AI models and templates designed for specific industry needs,
            ready to deploy in days, not months.
          </p>
        </motion.div>

        {/* Industries Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {industries.map((industry, index) => (
            <motion.div
              key={industry.title}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group relative overflow-hidden rounded-2xl bg-background border border-border hover:border-primary/30 transition-all card-hover"
            >
              {/* Gradient Header */}
              <div className={`h-2 bg-gradient-to-r ${industry.color}`} />

              <div className="p-5 sm:p-6 lg:p-8">
                <div
                  className={`w-12 sm:w-14 h-12 sm:h-14 rounded-xl sm:rounded-2xl bg-gradient-to-br ${industry.color} flex items-center justify-center mb-4 sm:mb-6`}
                >
                  <industry.icon className="w-6 sm:w-7 h-6 sm:h-7 text-white" />
                </div>

                <h3 className="text-lg sm:text-xl font-bold text-white mb-2 sm:mb-3">
                  {industry.title}
                </h3>
                <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6">
                  {industry.description}
                </p>

                {/* Use Cases */}
                <div className="space-y-2 mb-4 sm:mb-6">
                  {industry.useCases.map((useCase) => (
                    <div
                      key={useCase}
                      className="flex items-center gap-2 text-sm text-muted-foreground"
                    >
                      <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-r ${industry.color}`} />
                      {useCase}
                    </div>
                  ))}
                </div>

                {/* Learn More Link */}
                <button className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:gap-3 transition-all">
                  Explore Solution
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="text-center mt-16"
        >
          <p className="text-muted-foreground mb-6">
            Don&apos;t see your industry? We build custom solutions too.
          </p>
          <button className="btn-primary inline-flex items-center gap-2">
            Talk to Our Experts
            <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    </section>
  );
}
