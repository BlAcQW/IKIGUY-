import { TopBar } from '@/components/layout/TopBar';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { HeroCarousel } from '@/components/sections/HeroCarousel';
import { ProductsHighlight } from '@/components/sections/ProductsHighlight';
import { AboutSection } from '@/components/sections/AboutSection';
import { WhyChooseUs } from '@/components/sections/WhyChooseUs';
import { CTABanner } from '@/components/sections/CTABanner';
import { NewsSection } from '@/components/sections/NewsSection';
import { ChatWidget } from '@/components/chat/ChatWidget';

export default function App() {
  return (
    <div className="min-h-screen font-poppins">
      <TopBar />
      <Navbar />
      <main>
        <HeroCarousel />
        <ProductsHighlight />
        <AboutSection />
        <WhyChooseUs />
        <CTABanner />
        <NewsSection />
      </main>
      <Footer />
      <ChatWidget />
    </div>
  );
}
