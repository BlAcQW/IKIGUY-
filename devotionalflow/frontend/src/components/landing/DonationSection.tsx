import { motion } from "framer-motion";
import { Heart, HandHeart, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import donationLogo from "@/assets/donation_logo.png";

/**
 * DonationSection - Elegant donation and partnership section
 * Mobile-optimized and responsive design
 */
export function DonationSection() {
  return (
    <section className="relative py-12 md:py-16 lg:py-20 overflow-hidden bg-gradient-to-br from-secondary/5 via-background to-accent/5">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Content Section */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
              className="order-2 lg:order-1"
            >
              <div className="space-y-6">
                {/* Badge */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20"
                >
                  <HandHeart className="w-4 h-4 text-secondary" />
                  <span className="text-sm font-medium text-secondary">Support Our Ministry</span>
                </motion.div>

                {/* Heading */}
                <motion.h2
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.1 }}
                  className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold text-foreground leading-tight"
                >
                  Partner with{" "}
                  <span className="text-gradient-orange">Bishop Suzanne Nti</span>
                </motion.h2>

                {/* Description */}
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 }}
                  className="text-base md:text-lg text-muted-foreground leading-relaxed"
                >
                  Your generous support helps us continue providing daily devotionals, 
                  spiritual guidance, and prayer ministry to believers worldwide. 
                  Together, we can reach more hearts and transform more lives.
                </motion.p>

                {/* Benefits */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.3 }}
                  className="space-y-3"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-secondary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles className="w-4 h-4 text-secondary" />
                    </div>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Support daily devotional content creation
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-secondary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Heart className="w-4 h-4 text-secondary" />
                    </div>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Enable prayer ministry and spiritual counseling
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-secondary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <HandHeart className="w-4 h-4 text-secondary" />
                    </div>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Help reach more believers with God's Word
                    </p>
                  </div>
                </motion.div>

                {/* CTA Button */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.4 }}
                >
                  <Button
                    size="lg"
                    variant="hero"
                    className="w-full sm:w-auto"
                    asChild
                  >
                    <a
                      href="https://donorbox.org/oew-online-prayer-ministry"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2"
                    >
                      <Heart className="w-5 h-5" />
                      Partner & Donate
                    </a>
                  </Button>
                </motion.div>
              </div>
            </motion.div>

            {/* Logo Section */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="order-1 lg:order-2"
            >
              <div className="relative">
                {/* Decorative elements */}
                <div className="absolute -top-4 -right-4 w-32 h-32 bg-secondary/10 rounded-full blur-2xl -z-10" />
                <div className="absolute -bottom-4 -left-4 w-24 h-24 bg-accent/10 rounded-full blur-2xl -z-10" />
                
                {/* Logo container */}
                <div className="relative bg-card rounded-2xl md:rounded-3xl p-6 md:p-8 border border-border shadow-elevated group hover:shadow-orange transition-shadow">
                  {/* Logo */}
                  <div className="relative aspect-square max-w-xs mx-auto">
                    <img
                      src={donationLogo}
                      alt="Bishop Suzanne Nti - Online Prayer Ministry"
                      className="w-full h-full object-contain"
                      loading="lazy"
                    />
                  </div>
                  
                  {/* Decorative corner accent */}
                  <div className="absolute top-0 left-0 w-16 h-16 sm:w-20 sm:h-20 border-t-4 border-l-4 border-secondary/30 rounded-tl-2xl" />
                  <div className="absolute bottom-0 right-0 w-16 h-16 sm:w-20 sm:h-20 border-b-4 border-r-4 border-secondary/30 rounded-br-2xl" />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}

