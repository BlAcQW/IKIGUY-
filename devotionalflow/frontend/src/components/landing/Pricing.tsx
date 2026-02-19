import { motion } from "framer-motion";
import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for getting started with your ministry online.",
    features: [
      "Up to 10 devotionals",
      "Basic analytics",
      "Comment moderation",
      "Mobile-optimized reading",
      "Community support",
    ],
    cta: "Start Free",
    variant: "outline" as const,
    popular: false,
  },
  {
    name: "Pro",
    price: "$12",
    period: "/month",
    description: "Everything you need to grow your digital ministry.",
    features: [
      "Unlimited devotionals",
      "Advanced analytics & insights",
      "AI Text-to-Speech narration",
      "AI Scripture explanations",
      "Priority push notifications",
      "Custom branding",
      "Social sharing templates",
      "Email support",
    ],
    cta: "Start 14-Day Trial",
    variant: "hero" as const,
    popular: true,
  },
  {
    name: "Ministry",
    price: "$29",
    period: "/month",
    description: "For churches and multi-pastor organizations.",
    features: [
      "Everything in Pro",
      "Up to 5 pastor accounts",
      "Shared content library",
      "Advanced scheduling",
      "Donation integration",
      "API access",
      "Dedicated support",
      "Custom domain",
    ],
    cta: "Contact Sales",
    variant: "outline" as const,
    popular: false,
  },
];

const Pricing = () => {
  return (
    <section id="pricing" className="py-24 bg-gradient-spiritual">
      <div className="container mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-6">
            Invest in Your{" "}
            <span className="text-gradient-gold">Ministry</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Simple, transparent pricing. Start free and upgrade as your community grows.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative rounded-3xl p-8 ${
                plan.popular
                  ? "bg-primary text-primary-foreground shadow-elevated scale-105"
                  : "bg-card border border-border shadow-soft"
              }`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-secondary text-secondary-foreground text-sm font-medium shadow-gold">
                    <Sparkles className="w-4 h-4" />
                    Most Popular
                  </div>
                </div>
              )}

              {/* Plan Info */}
              <div className="text-center mb-8">
                <h3
                  className={`font-serif text-2xl font-bold mb-2 ${
                    plan.popular ? "text-primary-foreground" : "text-foreground"
                  }`}
                >
                  {plan.name}
                </h3>
                <div className="mb-2">
                  <span
                    className={`font-serif text-5xl font-bold ${
                      plan.popular ? "text-secondary" : "text-foreground"
                    }`}
                  >
                    {plan.price}
                  </span>
                  <span
                    className={
                      plan.popular
                        ? "text-primary-foreground/70"
                        : "text-muted-foreground"
                    }
                  >
                    {plan.period}
                  </span>
                </div>
                <p
                  className={
                    plan.popular
                      ? "text-primary-foreground/80"
                      : "text-muted-foreground"
                  }
                >
                  {plan.description}
                </p>
              </div>

              {/* Features */}
              <ul className="space-y-4 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        plan.popular
                          ? "bg-primary text-primary-foreground"
                          : "bg-primary/10 text-primary"
                      }`}
                    >
                      <Check className="w-3 h-3" />
                    </div>
                    <span
                      className={
                        plan.popular
                          ? "text-primary-foreground/90"
                          : "text-muted-foreground"
                      }
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Button
                variant={plan.popular ? "hero" : "outline"}
                size="lg"
                className="w-full"
              >
                {plan.cta}
              </Button>
            </motion.div>
          ))}
        </div>

        {/* Reader Note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center text-muted-foreground mt-12"
        >
          Readers always access content for free. Optional "Support the Ministry" 
          subscriptions let your community contribute directly.
        </motion.p>
      </div>
    </section>
  );
};

export default Pricing;
