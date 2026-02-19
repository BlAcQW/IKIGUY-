import Hero from "@/components/sections/Hero";
import Stats from "@/components/sections/Stats";
import Services from "@/components/sections/Services";
import Solutions from "@/components/sections/Solutions";
import Features from "@/components/sections/Features";
import Testimonials from "@/components/sections/Testimonials";
import Contact from "@/components/sections/Contact";
import CTA from "@/components/sections/CTA";

export default function Home() {
  return (
    <div className="flex flex-col">
      <Hero />
      <Stats />
      <Services />
      <Solutions />
      <Features />
      <Testimonials />
      <CTA />
      <Contact />
    </div>
  );
}
