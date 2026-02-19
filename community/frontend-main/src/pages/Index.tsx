import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import LanguageFamilies from "@/components/LanguageFamilies";
import CommunityFeatures from "@/components/CommunityFeatures";
import NotebookExplorer from "@/components/NotebookExplorer";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <HeroSection />
        <LanguageFamilies />
        <section id="notebooks" className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">AI Model Notebooks</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Access notebooks for training and using AI models across African languages
            </p>
          </div>
          <NotebookExplorer />
        </section>
        <CommunityFeatures />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
