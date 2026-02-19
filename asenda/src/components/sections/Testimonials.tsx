"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, useState, useEffect } from "react";
import { Quote, ChevronLeft, ChevronRight, Star } from "lucide-react";

const testimonials = [
  {
    id: 1,
    content:
      "Asenda.ai transformed our customer support operations. We reduced response times by 80% while maintaining exceptional quality. The AI agents handle complex queries that we thought only humans could manage.",
    author: "Sarah Chen",
    role: "VP of Customer Experience",
    company: "TechFlow Solutions",
    rating: 5,
    image: "/testimonials/sarah.jpg",
  },
  {
    id: 2,
    content:
      "The ROI was immediate. Within the first month, our sales team closed 3x more deals thanks to Asenda's AI-powered lead qualification and follow-up system. It's like having an army of top performers.",
    author: "Michael Rodriguez",
    role: "Chief Revenue Officer",
    company: "GlobalScale Inc",
    rating: 5,
    image: "/testimonials/michael.jpg",
  },
  {
    id: 3,
    content:
      "We were skeptical about AI handling sensitive patient scheduling, but Asenda exceeded our expectations. The accuracy and natural conversation flow impressed both our staff and patients.",
    author: "Dr. Emily Watson",
    role: "Medical Director",
    company: "HealthFirst Clinics",
    rating: 5,
    image: "/testimonials/emily.jpg",
  },
  {
    id: 4,
    content:
      "As a startup, we couldn't afford a large support team. Asenda's AI agents gave us enterprise-level customer service at a fraction of the cost. Our NPS score jumped 40 points.",
    author: "James Park",
    role: "CEO & Founder",
    company: "Innovate Labs",
    rating: 5,
    image: "/testimonials/james.jpg",
  },
  {
    id: 5,
    content:
      "The multilingual support is a game-changer. We now handle customer calls in 12 languages without hiring additional staff. Asenda made global expansion actually feasible.",
    author: "Maria Santos",
    role: "Head of Operations",
    company: "WorldConnect",
    rating: 5,
    image: "/testimonials/maria.jpg",
  },
];

export default function Testimonials() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const goToNext = () => {
    setIsAutoPlaying(false);
    setActiveIndex((prev) => (prev + 1) % testimonials.length);
  };

  const goToPrev = () => {
    setIsAutoPlaying(false);
    setActiveIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  return (
    <section id="testimonials" className="section bg-card relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />

      <div className="container mx-auto px-4 sm:px-6 md:px-8 relative z-10" ref={containerRef}>
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-10 sm:mb-12 lg:mb-16"
        >
          <span className="text-primary text-sm font-semibold tracking-wider uppercase mb-3 sm:mb-4 block">
            Testimonials
          </span>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 px-2">
            Loved by Businesses Worldwide
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base sm:text-lg px-2">
            See how companies are transforming their operations with Asenda.ai
          </p>
        </motion.div>

        {/* Main Testimonial Carousel */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-4xl mx-auto"
        >
          <div className="relative">
            {/* Testimonial Card */}
            <div className="gradient-border p-5 sm:p-8 md:p-12">
              <Quote className="w-10 sm:w-12 h-10 sm:h-12 text-primary/30 mb-4 sm:mb-6" />

              <motion.div
                key={activeIndex}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <p className="text-base sm:text-xl md:text-2xl text-white leading-relaxed mb-6 sm:mb-8">
                  &ldquo;{testimonials[activeIndex].content}&rdquo;
                </p>

                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold text-lg">
                      {testimonials[activeIndex].author.charAt(0)}
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">
                        {testimonials[activeIndex].author}
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        {testimonials[activeIndex].role} at{" "}
                        <span className="text-primary">
                          {testimonials[activeIndex].company}
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    {[...Array(testimonials[activeIndex].rating)].map((_, i) => (
                      <Star
                        key={i}
                        className="w-5 h-5 fill-yellow-500 text-yellow-500"
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-center gap-4 mt-8">
              <button
                onClick={goToPrev}
                className="w-12 h-12 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground hover:text-white hover:border-primary transition-all"
                aria-label="Previous testimonial"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>

              {/* Dots */}
              <div className="flex items-center gap-2">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setIsAutoPlaying(false);
                      setActiveIndex(index);
                    }}
                    className={`w-2 h-2 rounded-full transition-all ${
                      index === activeIndex
                        ? "w-8 bg-primary"
                        : "bg-border hover:bg-muted"
                    }`}
                    aria-label={`Go to testimonial ${index + 1}`}
                  />
                ))}
              </div>

              <button
                onClick={goToNext}
                className="w-12 h-12 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground hover:text-white hover:border-primary transition-all"
                aria-label="Next testimonial"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </motion.div>

        {/* Mini Testimonials Grid */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mt-10 sm:mt-12 lg:mt-16"
        >
          {testimonials.slice(0, 3).map((testimonial, index) => (
            <div
              key={testimonial.id}
              className={`p-6 rounded-xl border transition-all cursor-pointer ${
                index === activeIndex % 3
                  ? "bg-card border-primary/30"
                  : "bg-transparent border-border hover:bg-card/50"
              }`}
              onClick={() => {
                setIsAutoPlaying(false);
                setActiveIndex(index);
              }}
            >
              <div className="flex items-center gap-1 mb-3">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-4 h-4 fill-yellow-500 text-yellow-500"
                  />
                ))}
              </div>
              <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                &ldquo;{testimonial.content}&rdquo;
              </p>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-xs font-bold">
                  {testimonial.author.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium text-white">
                    {testimonial.author}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {testimonial.company}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
