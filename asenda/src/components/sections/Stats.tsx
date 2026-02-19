"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useState, useEffect } from "react";

const stats = [
  { value: 500, suffix: "+", label: "Enterprise Clients", description: "Trusted by leading companies" },
  { value: 10, suffix: "M+", label: "Calls Handled", description: "Monthly conversations processed" },
  { value: 98, suffix: "%", label: "Customer Satisfaction", description: "Average CSAT score" },
  { value: 8, suffix: ":1", label: "ROI Ratio", description: "Average return on investment" },
];

function AnimatedNumber({ value, suffix }: { value: number; suffix: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const duration = 2000;
      const steps = 60;
      const increment = value / steps;
      let current = 0;
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          setCount(value);
          clearInterval(timer);
        } else {
          setCount(Math.floor(current));
        }
      }, duration / steps);
      return () => clearInterval(timer);
    }
  }, [isInView, value]);

  return (
    <span ref={ref} className="gradient-text">
      {count}
      {suffix}
    </span>
  );
}

export default function Stats() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section className="section bg-card relative overflow-hidden">
      {/* Background effect */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      <div className="container mx-auto px-4 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Trusted by Industry Leaders
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our AI voice agents deliver measurable results across thousands of businesses worldwide.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="text-center"
            >
              <div className="gradient-border p-4 sm:p-6 md:p-8 h-full">
                <div className="text-3xl sm:text-4xl md:text-5xl font-bold mb-2">
                  <AnimatedNumber value={stat.value} suffix={stat.suffix} />
                </div>
                <h3 className="text-sm sm:text-base lg:text-lg font-semibold text-white mb-1">
                  {stat.label}
                </h3>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  {stat.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Logo Carousel */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-16 pt-16 border-t border-border"
        >
          <p className="text-center text-sm text-muted-foreground mb-8">
            Powering conversations for innovative companies
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 opacity-50">
            {["Acme Corp", "TechFlow", "GlobalSoft", "Innovate Inc", "DataDrive", "CloudScale"].map((company) => (
              <div
                key={company}
                className="text-xl md:text-2xl font-bold text-muted tracking-wider"
              >
                {company}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
