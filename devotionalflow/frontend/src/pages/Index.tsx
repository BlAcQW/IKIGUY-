import Navbar from "@/components/landing/Navbar";
import { AppHeader } from "@/components/navigation/AppHeader";
import Hero from "@/components/landing/Hero";
import TodaysFeaturedDevotional from "@/components/landing/TodaysFeaturedDevotional";
import CategoryBrowser from "@/components/landing/CategoryBrowser";
import TrendingDevotionals from "@/components/landing/TrendingDevotionals";
import GamificationTeaser from "@/components/landing/GamificationTeaser";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import DevotionalPreview from "@/components/landing/DevotionalPreview";
import CommunityShowcase from "@/components/landing/CommunityShowcase";
import { FeaturedLeader } from "@/components/landing/FeaturedLeader";
import { DonationSection } from "@/components/landing/DonationSection";
import { InviteToSpeak } from "@/components/landing/InviteToSpeak";
import EmailSubscription from "@/components/landing/EmailSubscription";
import Footer from "@/components/landing/Footer";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  return (
    <main className="min-h-screen bg-background">
      {/* Desktop Navigation - Hidden on mobile */}
      <div className="hidden md:block">
        <Navbar />
      </div>

      {/* Mobile App Header - Hidden on desktop */}
      <div className="md:hidden">
        <AppHeader
          title="Fresh Manna"
          showBack={false}
          showSearch={true}
          showNotifications={true}
          onSearch={() => navigate('/discover')}
          onNotifications={() => navigate('/profile')}
        />
      </div>

      {/* Content */}
      <div>
        {/* Hero Section */}
        <Hero />

        {/* Mobile-First Content (visible on mobile, optional on desktop) */}
        <div className="md:hidden">
          <TodaysFeaturedDevotional />
          <CategoryBrowser />
          <FeaturedLeader />
          <TrendingDevotionals />
          <GamificationTeaser />
          <div className="container mx-auto px-4 py-8">
            <EmailSubscription />
          </div>
          <DonationSection />
          <InviteToSpeak />
        </div>

        {/* Desktop Content (hidden on mobile, visible on desktop) */}
        <div className="hidden md:block">
          <TodaysFeaturedDevotional />
          <CategoryBrowser />
          <Features />
          <FeaturedLeader />
          <TrendingDevotionals />
          <GamificationTeaser />
          <HowItWorks />
          <DevotionalPreview />
          <CommunityShowcase />
          <div className="container mx-auto px-4 py-16">
            <EmailSubscription />
          </div>
          <DonationSection />
          <InviteToSpeak />
        </div>

        <Footer />
      </div>

      {/* Mobile Bottom Navigation - Hidden on desktop */}
      <div className="md:hidden">
      </div>
    </main>
  );
};

export default Index;
