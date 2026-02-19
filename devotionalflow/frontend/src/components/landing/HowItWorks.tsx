import { motion } from "framer-motion";
import { BookOpen, MessageCircle, Users2, TrendingUp } from "lucide-react";

const steps = [
  {
    step: "01",
    icon: BookOpen,
    title: "Read Daily Devotionals",
    description: "Start each morning with fresh spiritual food. Browse devotionals by topic, listen to audio narrations, and explore interactive scripture references.",
  },
  {
    step: "02",
    icon: MessageCircle,
    title: "Engage & Reflect",
    description: "Dive deeper with comments and discussions. Share your insights, ask questions, and learn from fellow believers' perspectives on the same passage.",
  },
  {
    step: "03",
    icon: Users2,
    title: "Join Study Groups",
    description: "Connect with like-minded believers in Bible study groups. Collaborate on scripture, share prayer requests, and build authentic Christian fellowship.",
  },
  {
    step: "04",
    icon: TrendingUp,
    title: "Track Your Growth",
    description: "Build consistent spiritual habits with reading streaks. Bookmark favorites, review your journey, and watch your faith deepen day by day.",
  },
];

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="py-24 bg-background">
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
            Your Daily{" "}
            <span className="text-gradient-gold">Spiritual Rhythm</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Building a thriving faith life is simple with FreshManna. Here's how it works.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="max-w-5xl mx-auto">
          <div className="grid gap-8 lg:gap-12">
            {steps.map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`flex flex-col lg:flex-row items-center gap-8 ${
                  index % 2 === 1 ? "lg:flex-row-reverse" : ""
                }`}
              >
                {/* Visual */}
                <div className="flex-1 relative">
                  <div className="relative bg-gradient-card rounded-3xl p-8 shadow-soft border border-border/50">
                    {/* Step Number */}
                    <div className="absolute -top-4 -left-4 w-12 h-12 bg-secondary rounded-xl flex items-center justify-center shadow-gold">
                      <span className="font-serif font-bold text-secondary-foreground">
                        {item.step}
                      </span>
                    </div>

                    {/* Icon Display */}
                    <div className="flex items-center justify-center h-48">
                      <div className="relative">
                        <div className="absolute inset-0 bg-secondary/20 rounded-full blur-2xl" />
                        <div className="relative w-24 h-24 bg-secondary/10 rounded-2xl flex items-center justify-center border border-secondary/20">
                          <item.icon className="w-12 h-12 text-secondary" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Connecting Line (except last) */}
                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute left-1/2 -bottom-8 w-px h-8 bg-gradient-to-b from-border to-transparent" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 text-center lg:text-left">
                  <h3 className="font-serif text-2xl md:text-3xl font-bold text-foreground mb-4">
                    {item.title}
                  </h3>
                  <p className="text-lg text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
