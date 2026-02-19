import { motion } from "framer-motion";
import { Users, MessageSquare, BookMarked, Quote } from "lucide-react";

const communityStats = [
  {
    icon: Users,
    number: "150K+",
    label: "Active Believers",
    description: "Growing in faith together",
    color: "secondary",
  },
  {
    icon: BookMarked,
    number: "500+",
    label: "Study Groups",
    description: "Collaborative Bible learning",
    color: "accent",
  },
  {
    icon: MessageSquare,
    number: "2M+",
    label: "Discussions",
    description: "Meaningful conversations daily",
    color: "secondary",
  },
];

const testimonials = [
  {
    name: "Sarah Mitchell",
    role: "Community Member",
    content: "FreshManna transformed my morning routine. The daily devotionals and study groups have deepened my understanding of Scripture in ways I never imagined.",
    image: "👩🏽",
  },
  {
    name: "David Chen",
    role: "Study Group Leader",
    content: "Our Bible study group meets here every week. The interactive scripture features and discussion tools make studying God's Word together so engaging and meaningful.",
    image: "👨🏻",
  },
  {
    name: "Grace Okonkwo",
    role: "Daily Reader",
    content: "I love the audio devotionals for my commute. Being able to bookmark favorites and track my reading streak keeps me accountable to spending time with God daily.",
    image: "👩🏿",
  },
];

const CommunityShowcase = () => {
  return (
    <section id="community" className="py-24 bg-gradient-spiritual">
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
            Join a Thriving{" "}
            <span className="text-gradient-gold">Community of Faith</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            You're never alone on your spiritual journey. Connect with thousands
            of believers growing together every day.
          </p>
        </motion.div>

        {/* Community Stats */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-20">
          {communityStats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative bg-card rounded-2xl p-8 shadow-soft border border-border/50 text-center group hover:shadow-elevated transition-all"
            >
              {/* Icon */}
              <div
                className={`w-16 h-16 mx-auto mb-6 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 ${
                  stat.color === "secondary"
                    ? "bg-secondary/10 text-secondary"
                    : "bg-accent/10 text-accent"
                }`}
              >
                <stat.icon className="w-8 h-8" />
              </div>

              {/* Stats */}
              <div className="font-serif text-4xl font-bold text-foreground mb-2">
                {stat.number}
              </div>
              <div className="text-xl font-semibold text-foreground mb-2">
                {stat.label}
              </div>
              <div className="text-muted-foreground">{stat.description}</div>

              {/* Hover Glow */}
              <div
                className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none ${
                  stat.color === "secondary"
                    ? "bg-gradient-to-br from-secondary/5 to-transparent"
                    : "bg-gradient-to-br from-accent/5 to-transparent"
                }`}
              />
            </motion.div>
          ))}
        </div>

        {/* Testimonials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-6xl mx-auto"
        >
          <h3 className="font-serif text-2xl md:text-3xl font-bold text-center text-foreground mb-12">
            Stories from Our Community
          </h3>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-card rounded-2xl p-6 shadow-soft border border-border/50 relative"
              >
                {/* Quote Icon */}
                <div className="absolute -top-3 left-6 w-8 h-8 bg-secondary rounded-lg flex items-center justify-center">
                  <Quote className="w-4 h-4 text-secondary-foreground" />
                </div>

                {/* Content */}
                <p className="text-muted-foreground leading-relaxed mb-6 mt-4">
                  "{testimonial.content}"
                </p>

                {/* Author */}
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-spiritual flex items-center justify-center text-2xl">
                    {testimonial.image}
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">
                      {testimonial.name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {testimonial.role}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CommunityShowcase;
