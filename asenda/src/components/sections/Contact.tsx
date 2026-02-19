"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useState } from "react";
import {
  Mail,
  Phone,
  MapPin,
  Calendar,
  Check,
  ArrowRight,
  AlertCircle,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const benefits = [
  "Free 14-day trial with full features",
  "No credit card required",
  "Dedicated onboarding support",
  "Custom demo for your use case",
];

type FormType = "contact" | "demo";

export default function Contact() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });
  const [formType, setFormType] = useState<FormType>("demo");
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    company: "",
    phone: "",
    message: "",
    jobTitle: "",
    companySize: "",
    useCase: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const endpoint = formType === "demo" ? "/api/leads/demo" : "/api/leads/contact";
      const payload = formType === "demo"
        ? {
            name: formState.name,
            email: formState.email,
            company: formState.company,
            phone: formState.phone || null,
            job_title: formState.jobTitle || null,
            company_size: formState.companySize || null,
            use_case: formState.useCase || formState.message,
          }
        : {
            name: formState.name,
            email: formState.email,
            company: formState.company || null,
            phone: formState.phone || null,
            message: formState.message,
            source: "contact_form",
          };

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to submit form");
      }

      setIsSubmitted(true);
      setFormState({
        name: "",
        email: "",
        company: "",
        phone: "",
        message: "",
        jobTitle: "",
        companySize: "",
        useCase: "",
      });
    } catch (err) {
      setError("Something went wrong. Please try again or email us directly.");
      console.error("Form submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openCalendly = () => {
    // You can replace this with your actual Calendly link
    window.open("https://calendly.com/asenda-ai/demo", "_blank");
  };

  return (
    <section id="contact" className="section relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 sm:mb-12 lg:mb-16"
        >
          <span className="text-primary text-sm font-semibold tracking-wider uppercase mb-3 sm:mb-4 block">
            Get Started
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 px-2">
            Ready to Transform Your Business?
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base sm:text-lg px-2">
            Book a personalized demo and see how Asenda.ai can revolutionize your
            customer interactions.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-start">
          {/* Left Column - Info */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {/* Benefits */}
            <div className="mb-6 sm:mb-8 lg:mb-10">
              <h3 className="text-lg sm:text-xl font-semibold text-white mb-4 sm:mb-6">
                What you&apos;ll get
              </h3>
              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.li
                    key={benefit}
                    initial={{ opacity: 0, x: -20 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <span className="text-muted-foreground">{benefit}</span>
                  </motion.li>
                ))}
              </ul>
            </div>

            {/* Contact Info */}
            <div className="gradient-border p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-white mb-4 sm:mb-6">
                Contact Information
              </h3>
              <div className="space-y-3 sm:space-y-4">
                <a
                  href="mailto:hello@asenda.ai"
                  className="flex items-center gap-3 text-muted-foreground hover:text-white transition-colors"
                >
                  <Mail className="w-5 h-5 text-primary" />
                  hello@asenda.ai
                </a>
                <a
                  href="tel:+15551234567"
                  className="flex items-center gap-3 text-muted-foreground hover:text-white transition-colors"
                >
                  <Phone className="w-5 h-5 text-primary" />
                  +1 (555) 123-4567
                </a>
                <div className="flex items-start gap-3 text-muted-foreground">
                  <MapPin className="w-5 h-5 text-primary mt-0.5" />
                  <span>
                    123 AI Boulevard<br />
                    San Francisco, CA 94105
                  </span>
                </div>
              </div>
            </div>

            {/* Schedule Direct */}
            <div className="mt-4 sm:mt-6 p-4 sm:p-6 rounded-xl bg-card border border-border">
              <div className="flex items-center gap-3 mb-4">
                <Calendar className="w-5 h-5 text-secondary" />
                <h3 className="font-semibold text-white">Prefer to schedule directly?</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Pick a time that works for you and get a personalized demo with one of our AI specialists.
              </p>
              <button
                onClick={openCalendly}
                className="btn-secondary w-full flex items-center justify-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                Schedule a Call
              </button>
            </div>
          </motion.div>

          {/* Right Column - Form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="gradient-border p-4 sm:p-6 lg:p-8">
              {isSubmitted ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                    <Check className="w-8 h-8 text-green-500" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">
                    Thank You!
                  </h3>
                  <p className="text-muted-foreground mb-2">
                    We&apos;ve received your request and will be in touch within 24 hours.
                  </p>
                  <p className="text-sm text-muted-foreground mb-6">
                    Check your email for a confirmation message.
                  </p>
                  <button
                    onClick={() => setIsSubmitted(false)}
                    className="btn-secondary"
                  >
                    Submit Another Request
                  </button>
                </div>
              ) : (
                <>
                  {/* Form Type Toggle */}
                  <div className="flex gap-2 mb-4 sm:mb-6 p-1 bg-background rounded-lg">
                    <button
                      type="button"
                      onClick={() => setFormType("demo")}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        formType === "demo"
                          ? "bg-primary text-white"
                          : "text-muted-foreground hover:text-white"
                      }`}
                    >
                      Request Demo
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormType("contact")}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        formType === "contact"
                          ? "bg-primary text-white"
                          : "text-muted-foreground hover:text-white"
                      }`}
                    >
                      Contact Us
                    </button>
                  </div>

                  {error && (
                    <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <p className="text-sm text-red-400">{error}</p>
                    </div>
                  )}

                  <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                    <div className="grid sm:grid-cols-2 gap-4 sm:gap-6">
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Full Name *
                        </label>
                        <input
                          type="text"
                          required
                          value={formState.name}
                          onChange={(e) =>
                            setFormState({ ...formState, name: e.target.value })
                          }
                          className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                          placeholder="John Doe"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Work Email *
                        </label>
                        <input
                          type="email"
                          required
                          value={formState.email}
                          onChange={(e) =>
                            setFormState({ ...formState, email: e.target.value })
                          }
                          className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                          placeholder="john@company.com"
                        />
                      </div>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Company {formType === "demo" ? "*" : ""}
                        </label>
                        <input
                          type="text"
                          required={formType === "demo"}
                          value={formState.company}
                          onChange={(e) =>
                            setFormState({ ...formState, company: e.target.value })
                          }
                          className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                          placeholder="Company Inc."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white mb-2">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          value={formState.phone}
                          onChange={(e) =>
                            setFormState({ ...formState, phone: e.target.value })
                          }
                          className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                          placeholder="+1 (555) 000-0000"
                        />
                      </div>
                    </div>

                    {formType === "demo" && (
                      <div className="grid sm:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-white mb-2">
                            Job Title
                          </label>
                          <input
                            type="text"
                            value={formState.jobTitle}
                            onChange={(e) =>
                              setFormState({ ...formState, jobTitle: e.target.value })
                            }
                            className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                            placeholder="VP of Operations"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-white mb-2">
                            Company Size
                          </label>
                          <select
                            value={formState.companySize}
                            onChange={(e) =>
                              setFormState({ ...formState, companySize: e.target.value })
                            }
                            className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white"
                          >
                            <option value="">Select size</option>
                            <option value="1-10">1-10 employees</option>
                            <option value="11-50">11-50 employees</option>
                            <option value="51-200">51-200 employees</option>
                            <option value="201-500">201-500 employees</option>
                            <option value="501-1000">501-1000 employees</option>
                            <option value="1000+">1000+ employees</option>
                          </select>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        {formType === "demo" ? "Tell us about your use case" : "How can we help?"} *
                      </label>
                      <textarea
                        required
                        rows={4}
                        value={formType === "demo" ? formState.useCase : formState.message}
                        onChange={(e) =>
                          formType === "demo"
                            ? setFormState({ ...formState, useCase: e.target.value })
                            : setFormState({ ...formState, message: e.target.value })
                        }
                        className="w-full px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted resize-none"
                        placeholder={
                          formType === "demo"
                            ? "What challenges are you looking to solve with voice AI?"
                            : "Tell us about your use case and what you're looking to achieve..."
                        }
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="btn-primary w-full flex items-center justify-center gap-2 text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          {formType === "demo" ? "Request Demo" : "Send Message"}
                          <ArrowRight className="w-5 h-5" />
                        </>
                      )}
                    </button>

                    <p className="text-xs text-muted-foreground text-center">
                      By submitting, you agree to our{" "}
                      <a href="#" className="text-primary hover:underline">
                        Terms of Service
                      </a>{" "}
                      and{" "}
                      <a href="#" className="text-primary hover:underline">
                        Privacy Policy
                      </a>
                      .
                    </p>
                  </form>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
