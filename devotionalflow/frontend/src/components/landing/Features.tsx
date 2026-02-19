import { motion } from "framer-motion";
import { 
  PenLine, 
  Users, 
  Sparkles, 
  Calendar, 
  MessageCircle, 
  Share2,
  Mic,
  BookOpen,
  Heart
} from "lucide-react";

const features = [
  {
    icon: BookOpen,
    title: "Daily Devotionals",
    description: "Start each day with fresh inspiration. Beautifully crafted devotionals from pastors worldwide, delivered to your feed.",
    color: "secondary",
  },
  {
    icon: Users,
    title: "Vibrant Community",
    description: "Connect with fellow believers. Join discussions, share insights, and grow together through comments and study groups.",
    color: "accent",
  },
  {
    icon: Sparkles,
    title: "Interactive Scripture",
    description: "Tap any Bible verse to explore context, translations, and AI-powered explanations. Make God's Word come alive.",
    color: "secondary",
  },
  {
    icon: Mic,
    title: "Audio Devotionals",
    description: "Listen on the go with AI-narrated devotionals. Perfect for commutes, workouts, or morning routines.",
    color: "accent",
  },
  {
    icon: MessageCircle,
    title: "Study Groups",
    description: "Join or create Bible study groups. Collaborate on scripture, share reflections, and build lasting fellowship.",
    color: "secondary",
  },
  {
    icon: Heart,
    title: "Track Your Growth",
    description: "Build spiritual habits with reading streaks, bookmarks, and personalized insights. Watch your faith journey unfold.",
    color: "accent",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 },
  },
};

const Features = () => {
  return (
    <section id="features" className="py-24 bg-gradient-spiritual">
      <div className="container mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20 mb-6">
            <Heart className="w-4 h-4 text-secondary" />
            <span className="text-sm font-medium text-muted-foreground">
              Everything You Need
            </span>
          </div>
          <h2 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-6">
            Everything You Need to{" "}
            <span className="text-gradient-gold">Grow in Faith</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            A complete spiritual growth platform designed to deepen your relationship
            with God and connect you with believers worldwide.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="group relative bg-card rounded-2xl p-8 shadow-soft hover:shadow-elevated transition-all duration-300 border border-border/50 hover:border-secondary/30"
            >
              {/* Icon */}
              <div
                className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110 ${
                  feature.color === "secondary"
                    ? "bg-secondary/10 text-secondary"
                    : "bg-accent/10 text-accent"
                }`}
              >
                <feature.icon className="w-7 h-7" />
              </div>

              {/* Content */}
              <h3 className="font-serif text-xl font-semibold text-foreground mb-3">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>

              {/* Hover Glow */}
              <div
                className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none ${
                  feature.color === "secondary"
                    ? "bg-gradient-to-br from-secondary/5 to-transparent"
                    : "bg-gradient-to-br from-accent/5 to-transparent"
                }`}
              />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default Features;
