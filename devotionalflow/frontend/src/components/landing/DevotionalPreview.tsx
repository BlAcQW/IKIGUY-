import { motion } from "framer-motion";
import { Heart, MessageCircle, Bookmark, Share2, Play, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const DevotionalPreview = () => {
  return (
    <section id="preview" className="py-24 bg-background">
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
            A Reading Experience{" "}
            <span className="text-gradient-gold">Worth Savoring</span>
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Beautiful typography, gentle layouts, and thoughtful interactions 
            that honor every word.
          </p>
        </motion.div>

        {/* Preview Card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-3xl mx-auto"
        >
          <div className="bg-card rounded-3xl shadow-elevated border border-border/50 overflow-hidden">
            {/* Header */}
            <div className="px-8 py-6 border-b border-border/50 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  December 9, 2024
                </p>
                <span className="inline-block px-3 py-1 rounded-full bg-secondary/10 text-secondary text-xs font-medium">
                  Faith & Purpose
                </span>
              </div>
              <Button variant="ghost" size="icon" className="text-secondary">
                <Volume2 className="w-5 h-5" />
              </Button>
            </div>

            {/* Content */}
            <div className="px-8 py-10 md:px-12">
              <h3 className="font-serif text-3xl md:text-4xl font-bold text-foreground mb-6 leading-tight">
                Walking in Divine Purpose
              </h3>

              <div className="prose prose-lg max-w-none">
                <p className="text-foreground/90 leading-relaxed mb-6">
                  In the quiet moments of dawn, when the world still sleeps, God often whispers 
                  the deepest truths to our hearts. Today, I want to remind you that your life 
                  is not an accident—it is a masterpiece being painted by the Master Artist.
                </p>

                {/* Scripture Block */}
                <div className="bg-secondary/5 border-l-4 border-secondary rounded-r-xl p-6 my-8">
                  <p className="font-serif text-xl italic text-foreground/90 mb-3">
                    "For we are God's handiwork, created in Christ Jesus to do good works, 
                    which God prepared in advance for us to do."
                  </p>
                  <p className="text-sm text-secondary font-medium">
                    — Ephesians 2:10 (NIV)
                  </p>
                </div>

                <p className="text-foreground/90 leading-relaxed mb-6">
                  You are God's handiwork—His poiema, His poem. Every experience, every struggle, 
                  every joy has been woven together to create something beautiful. The question 
                  is not whether you have purpose, but whether you will embrace it.
                </p>

                <p className="text-foreground/90 leading-relaxed">
                  Today, take a step. Just one step toward the calling you feel stirring within. 
                  God doesn't ask for perfection—He asks for obedience. And in your obedience, 
                  watch how He multiplies your efforts beyond anything you could imagine.
                </p>
              </div>

              {/* AI Features */}
              <div className="mt-10 flex flex-wrap gap-3">
                <Button variant="outline" size="sm" className="gap-2">
                  <Play className="w-4 h-4" />
                  Listen (AI Voice)
                </Button>
                <Button variant="outline" size="sm">
                  Quick Summary
                </Button>
                <Button variant="outline" size="sm">
                  Scripture Context
                </Button>
              </div>
            </div>

            {/* Footer Engagement */}
            <div className="px-8 py-5 bg-muted/50 border-t border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <button className="flex items-center gap-2 text-muted-foreground hover:text-secondary transition-colors group">
                  <Heart className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">247</span>
                </button>
                <button className="flex items-center gap-2 text-muted-foreground hover:text-accent transition-colors group">
                  <MessageCircle className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">32</span>
                </button>
                <button className="text-muted-foreground hover:text-secondary transition-colors">
                  <Bookmark className="w-5 h-5" />
                </button>
              </div>
              <button className="flex items-center gap-2 text-muted-foreground hover:text-accent transition-colors">
                <Share2 className="w-5 h-5" />
                <span className="text-sm font-medium">Share</span>
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default DevotionalPreview;
