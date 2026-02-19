import { motion } from "framer-motion";
import { Mic, Calendar, Mail, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * InviteToSpeak - Component for inviting Bishop Suzanne Nti to speak at events
 * Mobile-optimized and responsive design
 */
export function InviteToSpeak() {
  return (
    <section className="relative py-12 md:py-16 lg:py-20 overflow-hidden bg-gradient-to-br from-secondary/5 via-background to-accent/5">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="bg-card rounded-2xl md:rounded-3xl p-8 md:p-12 border border-border shadow-elevated"
          >
            <div className="text-center mb-8">
              {/* Icon */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-secondary/10 flex items-center justify-center mx-auto mb-6"
              >
                <Mic className="w-8 h-8 md:w-10 md:h-10 text-secondary" />
              </motion.div>

              {/* Heading */}
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4"
              >
                Invite{" "}
                <span className="text-gradient-orange">Bishop Suzanne Nti</span>{" "}
                to Speak
              </motion.h2>

              {/* Description */}
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="text-base md:text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto mb-8"
              >
                Bishop Suzanne Nti is available to speak at your church, conference, 
                or event. Share God's Word and inspire your community with powerful 
                messages of faith, hope, and transformation.
              </motion.p>
            </div>

            {/* Features */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
            >
              <div className="flex items-start gap-4 p-4 rounded-xl bg-secondary/5 border border-secondary/10">
                <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-5 h-5 text-secondary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Flexible Scheduling</h3>
                  <p className="text-sm text-muted-foreground">
                    Available for conferences, church services, workshops, and special events
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-xl bg-secondary/5 border border-secondary/10">
                <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                  <Mic className="w-5 h-5 text-secondary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Custom Messages</h3>
                  <p className="text-sm text-muted-foreground">
                    Tailored messages to meet your event's theme and audience needs
                  </p>
                </div>
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Button
                size="lg"
                variant="hero"
                className="w-full sm:w-auto flex items-center gap-2"
                asChild
              >
                <a
                  href="mailto:speaking@freshmanna.org?subject=Speaking Request - Invite Bishop Suzanne Nti"
                  className="inline-flex items-center gap-2"
                >
                  <Mail className="w-5 h-5" />
                  Send Speaking Request
                </a>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto flex items-center gap-2"
                asChild
              >
                <a
                  href="tel:+1234567890"
                  className="inline-flex items-center gap-2"
                >
                  <Phone className="w-5 h-5" />
                  Call Us
                </a>
              </Button>
            </motion.div>

            {/* Additional Info */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5 }}
              className="mt-8 pt-8 border-t border-border text-center"
            >
              <p className="text-sm text-muted-foreground">
                For speaking inquiries, please include your event details, preferred dates, 
                and audience information. We'll respond within 48 hours.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}


