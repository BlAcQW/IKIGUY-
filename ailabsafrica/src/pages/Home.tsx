import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot, MessageSquare, Phone, Shield, Zap, Globe } from 'lucide-react';
import ImageOptimizer, { BackgroundImage } from '@/components/ImageOptimizer';
import MetaTags from '@/components/SEO/MetaTags';
import { OrganizationSchema, WebsiteSchema, SoftwareApplicationSchema } from '@/components/SEO/StructuredData';
import heroBackground from '@/assets/hero-bg.jpg';
import kasaaiProduct from '@/assets/kasaai-product.jpg';

const Home = () => {
  return (
    <>
      <MetaTags />
      <OrganizationSchema />
      <WebsiteSchema />
      <SoftwareApplicationSchema />
      <div className="min-h-screen">
      {/* Hero Section */}
      <BackgroundImage
        src={heroBackground}
        alt="AI Labs Africa Hero Background"
        className="min-h-[80vh]"
        priority={true}
        overlay={true}
        overlayColor="rgba(0, 123, 255, 0.8)"
      >
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="relative z-10 container text-center text-white">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white to-african-gold bg-clip-text text-transparent">
              AI Labs Africa
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-white/90 max-w-3xl mx-auto">
              Pioneering AI innovation across Africa with intelligent solutions that transform businesses and communities
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" asChild>
                <Link to="/demos" className="bg-african-gold hover:bg-african-gold-dark text-black">
                  Explore Demos <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="border-white/30 text-white hover:bg-white/10">
                <Link to="/create-assistant">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </BackgroundImage>

      {/* About Section */}
      <section className="py-24 bg-background">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-tech-blue to-african-gold bg-clip-text text-transparent">
              Transforming Africa with AI Innovation
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              We're building the future of artificial intelligence in Africa, creating solutions that understand local contexts and drive meaningful change across industries.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Bot className="h-6 w-6 text-white" />
                </div>
                <CardTitle>AI-First Approach</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Cutting-edge artificial intelligence solutions designed specifically for African markets and languages.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Globe className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Local Innovation</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Built by Africans, for Africa. Our solutions understand local cultures, languages, and business needs.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <div className="w-12 h-12 bg-gradient-to-br from-tech-blue to-african-gold rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <CardTitle>Scalable Impact</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  From startups to enterprises, our AI solutions scale with your business and amplify your impact.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* KasaAI Product Section */}
      <section className="py-24 bg-muted/30">
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold mb-6 bg-gradient-to-r from-tech-blue to-african-gold bg-clip-text text-transparent">
                Meet KasaAI
              </h2>
              <p className="text-xl text-muted-foreground mb-8">
                Intelligent Conversations for the Future
              </p>
              <p className="text-lg mb-6">
                KasaAI is a next-generation AI-powered voice and chat automation platform designed to help businesses engage customers, drive sales, and streamline operations effortlessly. With natural, human-like conversations, KasaAI connects with your customers across voice calls, WhatsApp, SMS, and web chat — 24/7, in multiple languages.
              </p>

              <div className="grid sm:grid-cols-2 gap-4 mb-8">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-full flex items-center justify-center">
                    <MessageSquare className="h-4 w-4 text-white" />
                  </div>
                  <span>Multi-channel Support</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-tech-blue to-tech-blue-light rounded-full flex items-center justify-center">
                    <Phone className="h-4 w-4 text-white" />
                  </div>
                  <span>Voice Automation</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-full flex items-center justify-center">
                    <Globe className="h-4 w-4 text-white" />
                  </div>
                  <span>Multiple Languages</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-full flex items-center justify-center">
                    <Shield className="h-4 w-4 text-white" />
                  </div>
                  <span>Enterprise Security</span>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button size="lg" asChild>
                  <Link to="/demos">Try Live Demos</Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link to="/schedule-demo">Schedule Demo</Link>
                </Button>
              </div>
            </div>

            <div className="relative">
              <ImageOptimizer
                src={kasaaiProduct}
                alt="KasaAI Platform Interface"
                className="rounded-lg shadow-2xl"
                loading="lazy"
                quality={85}
              />
              <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-gradient-to-br from-african-gold to-african-gold-dark rounded-full flex items-center justify-center">
                <Bot className="h-12 w-12 text-white" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Industries Section */}
      <section className="py-24 bg-background">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Industries We Serve</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              KasaAI transforms customer engagement across multiple sectors
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              'Insurance',
              'Banking & Finance',
              'Real Estate',
              'Retail & E-commerce',
              'Healthcare',
              'Government Services'
            ].map((industry) => (
              <Card key={industry} className="text-center p-6 hover:shadow-lg transition-all duration-300 border-0 bg-gradient-to-br from-muted/30 to-muted/10">
                <CardHeader>
                  <CardTitle className="text-lg">{industry}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
        <div className="container text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Business?</h2>
          <p className="text-xl mb-8 text-white/90 max-w-2xl mx-auto">
            Join the AI revolution in Africa. Experience the power of KasaAI and see how intelligent conversations can drive your business forward.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" variant="secondary" asChild>
              <Link to="/demos" className="bg-african-gold hover:bg-african-gold-dark text-black">
                Explore Demos
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="border-white/30 text-white hover:bg-white/10">
              <Link to="/schedule-demo">Schedule Demo</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
    </>
  );
};

export default Home;