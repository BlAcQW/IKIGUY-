import { motion } from "framer-motion";
import { Quote, BookOpen, Heart } from "lucide-react";
import bishopSuImage from "@/assets/bishop_su.jpg";

/**
 * FeaturedLeader - Elegant component featuring Bishop Suzanne Nti and Dave
 * Mobile-optimized and responsive design
 */
export function FeaturedLeader() {
  return (
    <section className="relative py-12 md:py-20 lg:py-24 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 via-transparent to-accent/5" />
      
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Image Section - Mobile First */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
              className="order-2 lg:order-1"
            >
              <div className="relative">
                {/* Decorative elements */}
                <div className="absolute -top-4 -left-4 w-24 h-24 bg-secondary/10 rounded-full blur-2xl -z-10" />
                <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-accent/10 rounded-full blur-2xl -z-10" />
                
                {/* Image container with elegant frame */}
                <div className="relative rounded-2xl md:rounded-3xl overflow-hidden shadow-elevated group">
                  {/* Gradient overlay for depth */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10" />
                  
                  {/* Image with proper aspect ratio container - landscape image */}
                  <div className="relative w-full">
                    <img
                      src={bishopSuImage}
                      alt="Bishop Suzanne Nti - Christmas and New Year Blessing"
                      className="w-full h-auto object-contain"
                      loading="lazy"
                    />
                  </div>
                  
                  {/* Decorative corner accent */}
                  <div className="absolute top-0 left-0 w-16 h-16 sm:w-20 sm:h-20 border-t-4 border-l-4 border-secondary/30 rounded-tl-2xl z-20" />
                  <div className="absolute bottom-0 right-0 w-16 h-16 sm:w-20 sm:h-20 border-b-4 border-r-4 border-secondary/30 rounded-br-2xl z-20" />
                </div>
                
                {/* Floating badge */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                  className="absolute -bottom-6 -right-6 md:-right-8 bg-card rounded-xl p-4 shadow-elevated border border-border hidden sm:block"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                      <Heart className="w-6 h-6 text-secondary" />
                    </div>
                    <div>
                      <div className="font-semibold text-foreground text-sm">Spiritual Leader</div>
                      <div className="text-xs text-muted-foreground">Inspiring Faith</div>
                    </div>
                  </div>
                </motion.div>
              </div>
            </motion.div>

            {/* Content Section */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="order-1 lg:order-2"
            >
              <div className="space-y-6 md:space-y-8">
                {/* Badge */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20"
                >
                  <BookOpen className="w-4 h-4 text-secondary" />
                  <span className="text-sm font-medium text-secondary">Featured Leader</span>
                </motion.div>

                {/* Heading */}
                <motion.h2
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 }}
                  className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-foreground leading-tight"
                >
                  Meet{" "}
                  <span className="text-gradient-orange">Suzanne and Dave</span>
                </motion.h2>

                {/* Description */}
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.3 }}
                  className="text-base md:text-lg text-muted-foreground leading-relaxed max-w-xl"
                >
                  Bishop Suzanne Nti and her husband Dave lead FreshManna, sharing daily 
                  devotionals that inspire, encourage, and strengthen faith. Join them as they 
                  take you through God's Word, sharing their reflections and prayers along the way.
                </motion.p>

                {/* Quote Section */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.4 }}
                  className="relative bg-card rounded-2xl p-6 md:p-8 border border-border shadow-soft"
                >
                  {/* Quote icon */}
                  <div className="absolute -top-4 -left-4 w-12 h-12 bg-secondary rounded-full flex items-center justify-center shadow-lg">
                    <Quote className="w-6 h-6 text-secondary-foreground" />
                  </div>
                  
                  <blockquote className="pt-4">
                    <p className="font-serif text-lg md:text-xl text-foreground italic leading-relaxed mb-4">
                      "God's Word is a lamp to our feet and a light to our path. 
                      Let us walk in His truth daily."
                    </p>
                    <footer className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center">
                        <span className="text-sm font-semibold text-secondary">SN</span>
                      </div>
                      <div>
                        <div className="font-semibold text-foreground text-sm">Bishop Suzanne Nti</div>
                        <div className="text-xs text-muted-foreground">With Dave Nti</div>
                      </div>
                    </footer>
                  </blockquote>
                </motion.div>

                {/* Stats */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.5 }}
                  className="grid grid-cols-3 gap-4 pt-4"
                >
                  <div className="text-center">
                    <div className="font-serif text-2xl md:text-3xl font-bold text-secondary mb-1">
                      100+
                    </div>
                    <div className="text-xs md:text-sm text-muted-foreground">
                      Devotionals
                    </div>
                  </div>
                  <div className="text-center border-x border-border">
                    <div className="font-serif text-2xl md:text-3xl font-bold text-secondary mb-1">
                      50K+
                    </div>
                    <div className="text-xs md:text-sm text-muted-foreground">
                      Readers
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="font-serif text-2xl md:text-3xl font-bold text-secondary mb-1">
                      4.9★
                    </div>
                    <div className="text-xs md:text-sm text-muted-foreground">
                      Rating
                    </div>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}

