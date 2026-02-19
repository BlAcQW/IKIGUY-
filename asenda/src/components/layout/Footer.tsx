"use client";

import Link from "next/link";
import { useState } from "react";
import { Zap, Mail, Phone, MapPin, Linkedin, Twitter, Github, ArrowRight, Check } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const footerLinks = {
  product: [
    { label: "Voice AI Agents", href: "#services" },
    { label: "AI Helpdesk", href: "#services" },
    { label: "Sales Automation", href: "#services" },
    { label: "Integrations", href: "#features" },
    { label: "Pricing", href: "#pricing" },
  ],
  company: [
    { label: "About Us", href: "#about" },
    { label: "Careers", href: "#careers" },
    { label: "Blog", href: "#blog" },
    { label: "Press", href: "#press" },
    { label: "Partners", href: "#partners" },
  ],
  resources: [
    { label: "Documentation", href: "#docs" },
    { label: "API Reference", href: "#api" },
    { label: "Case Studies", href: "#case-studies" },
    { label: "Webinars", href: "#webinars" },
    { label: "Support", href: "#support" },
  ],
  legal: [
    { label: "Privacy Policy", href: "#privacy" },
    { label: "Terms of Service", href: "#terms" },
    { label: "Security", href: "#security" },
    { label: "GDPR", href: "#gdpr" },
  ],
};

const socialLinks = [
  { icon: Linkedin, href: "#", label: "LinkedIn" },
  { icon: Twitter, href: "#", label: "Twitter" },
  { icon: Github, href: "#", label: "GitHub" },
];

export default function Footer() {
  const [email, setEmail] = useState("");
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubscribing(true);
    try {
      const response = await fetch(`${API_BASE}/api/leads/newsletter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setIsSubscribed(true);
        setEmail("");
      }
    } catch (err) {
      console.error("Newsletter subscription error:", err);
    } finally {
      setIsSubscribing(false);
    }
  };

  return (
    <footer className="bg-card border-t border-border">
      {/* Newsletter Section */}
      <div className="border-b border-border">
        <div className="container mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 lg:py-12">
          <div className="max-w-4xl mx-auto text-center">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2 sm:mb-3">
              Stay Updated on Voice AI
            </h3>
            <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6 px-2">
              Get the latest insights on voice AI, automation, and customer experience delivered to your inbox.
            </p>
            {isSubscribed ? (
              <div className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-green-500/10 border border-green-500/30">
                <Check className="w-5 h-5 text-green-500" />
                <span className="text-green-400">Thanks for subscribing! Check your email.</span>
              </div>
            ) : (
              <form onSubmit={handleNewsletterSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-3 rounded-lg bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-white placeholder-muted"
                />
                <button
                  type="submit"
                  disabled={isSubscribing}
                  className="btn-primary px-6 py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isSubscribing ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      Subscribe
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 md:px-8 py-10 sm:py-12 lg:py-16">
        {/* Top Section */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6 sm:gap-8 mb-8 sm:mb-10 lg:mb-12">
          {/* Brand Column */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4 sm:mb-6">
              <div className="w-9 sm:w-10 h-9 sm:h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Zap className="w-5 sm:w-6 h-5 sm:h-6 text-white" />
              </div>
              <span className="text-lg sm:text-xl font-bold tracking-tight">
                asenda<span className="gradient-text">.ai</span>
              </span>
            </Link>
            <p className="text-muted-foreground text-xs sm:text-sm mb-4 sm:mb-6 max-w-xs">
              Transforming customer interactions with intelligent voice AI and automation solutions.
            </p>
            <div className="flex items-center gap-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  className="w-10 h-10 rounded-lg bg-background border border-border flex items-center justify-center text-muted-foreground hover:text-white hover:border-primary transition-all"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="text-sm sm:text-base font-semibold text-white mb-3 sm:mb-4">Product</h4>
            <ul className="space-y-2 sm:space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs sm:text-sm text-muted-foreground hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="text-sm sm:text-base font-semibold text-white mb-3 sm:mb-4">Company</h4>
            <ul className="space-y-2 sm:space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs sm:text-sm text-muted-foreground hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="text-sm sm:text-base font-semibold text-white mb-3 sm:mb-4">Resources</h4>
            <ul className="space-y-2 sm:space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs sm:text-sm text-muted-foreground hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h4 className="text-sm sm:text-base font-semibold text-white mb-3 sm:mb-4">Contact</h4>
            <ul className="space-y-2 sm:space-y-3">
              <li className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
                <Mail className="w-3.5 sm:w-4 h-3.5 sm:h-4 flex-shrink-0" />
                hello@asenda.ai
              </li>
              <li className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
                <Phone className="w-3.5 sm:w-4 h-3.5 sm:h-4 flex-shrink-0" />
                +1 (555) 123-4567
              </li>
              <li className="flex items-start gap-2 text-xs sm:text-sm text-muted-foreground">
                <MapPin className="w-3.5 sm:w-4 h-3.5 sm:h-4 mt-0.5 flex-shrink-0" />
                <span>San Francisco, CA<br />United States</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="pt-6 sm:pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs sm:text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Asenda AI. All rights reserved.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
            {footerLinks.legal.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="text-xs sm:text-sm text-muted-foreground hover:text-white transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
