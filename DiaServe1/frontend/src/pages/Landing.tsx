import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Building2,
  MapPin,
  Home,
  Briefcase,
  Globe,
  Users,
  CheckCircle,
  ArrowRight,
  Play,
  Phone,
  Star,
  TrendingUp,
  Shield,
  HeartHandshake
} from "lucide-react";
import { useState } from "react";

export default function Landing() {
  const navigate = useNavigate();
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);

  const services = [
    {
      icon: Home,
      title: "Residential Properties",
      description: "Find your dream home with our extensive collection of residential properties across Ghana and Africa.",
      link: "/properties",
    },
    {
      icon: Building2,
      title: "Commercial Real Estate",
      description: "Premium commercial spaces for businesses looking to establish or expand their presence.",
      link: "/properties",
    },
    {
      icon: Briefcase,
      title: "Property Management",
      description: "Full-service property management for diaspora clients who need trusted local oversight.",
      link: "/about",
    },
    {
      icon: TrendingUp,
      title: "Investment Advisory",
      description: "Expert guidance on real estate investment opportunities with high ROI potential.",
      link: "/contact",
    },
  ];

  const stats = [
    { value: "20+", label: "Years Experience" },
    { value: "500+", label: "Properties Sold" },
    { value: "1000+", label: "Happy Clients" },
    { value: "3", label: "Countries" },
  ];

  const features = [
    "Trusted diaspora real estate partner",
    "20+ years of industry experience",
    "Properties in prime locations",
    "Full property management services",
    "Legal and documentation support",
    "Virtual property tours available",
  ];

  const testimonials = [
    {
      name: "Kwame Asante",
      location: "Maryland, USA",
      text: "DiaServe made my dream of owning property in Ghana a reality. Their team handled everything professionally from start to finish.",
      rating: 5,
    },
    {
      name: "Ama Mensah",
      location: "London, UK",
      text: "As a diaspora member, I was hesitant about investing in Ghana. DiaServe's transparent process and regular updates gave me complete peace of mind.",
      rating: 5,
    },
    {
      name: "Kofi Boateng",
      location: "Toronto, Canada",
      text: "Excellent property management services. My rental property is well-maintained and I receive my payments on time every month.",
      rating: 5,
    },
  ];

  return (
    <div className="flex flex-col">
      {/* Hero Section - Full Screen with Background */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        {/* Background Image with Overlay */}
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1973&q=80')`,
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/60 to-black/40" />

        {/* Hero Content */}
        <div className="container relative z-10 py-20">
          <div className="max-w-3xl space-y-8">
            <div className="space-y-2">
              <span className="inline-block px-4 py-1.5 bg-primary/20 text-primary rounded-full text-sm font-medium backdrop-blur-sm border border-primary/30">
                Your Trusted Real Estate Partner
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight">
              Connecting Diaspora to
              <span className="text-primary"> African Real Estate</span> Opportunities
            </h1>
            <p className="text-lg md:text-xl text-gray-300 max-w-2xl">
              DiaServe Group is your gateway to investing in premium properties across Ghana and Africa.
              With over 20 years of experience, we make property ownership simple, secure, and profitable.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button
                size="lg"
                onClick={() => navigate("/properties")}
                className="text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
              >
                Explore Properties
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/contact")}
                className="text-lg px-8 py-6 bg-white/10 border-white/30 text-white hover:bg-white/20 backdrop-blur-sm"
              >
                <Phone className="mr-2 h-5 w-5" />
                Contact Us
              </Button>
            </div>

            {/* Quick Stats in Hero */}
            <div className="flex flex-wrap gap-8 pt-8 border-t border-white/20">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-primary">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center pt-2">
            <div className="w-1 h-2 bg-white rounded-full animate-pulse" />
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-20 bg-white">
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Image Side */}
            <div className="relative">
              <div className="aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1560520653-9e0e4c89eb11?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                  alt="DiaServe Team"
                  className="w-full h-full object-cover"
                />
              </div>
              {/* Floating Card */}
              <div className="absolute -bottom-6 -right-6 bg-primary text-white p-6 rounded-xl shadow-xl hidden md:block">
                <div className="text-4xl font-bold">20+</div>
                <div className="text-sm opacity-90">Years of Excellence</div>
              </div>
            </div>

            {/* Content Side */}
            <div className="space-y-6">
              <div className="space-y-2">
                <span className="text-primary font-semibold uppercase tracking-wider text-sm">About DiaServe Group</span>
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
                  The Only Diaspora Service Connoisseurs
                </h2>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                DiaServe Group connects clients, particularly Ghanaians living abroad, to lucrative
                investment opportunities in Ghana and other parts of Africa. We bridge the gap between
                diaspora communities and the African real estate market.
              </p>
              <p className="text-gray-600 leading-relaxed">
                Founded in 2019, DiaServe Group operates as a dynamic organization committed to creating
                meaningful impacts across industries. We leverage technology, finance, and logistics to
                provide integrated solutions that meet the unique needs of our diaspora clientele.
              </p>

              {/* Feature Checklist */}
              <div className="grid sm:grid-cols-2 gap-3 pt-4">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="pt-4">
                <Button
                  onClick={() => navigate("/about")}
                  className="group"
                  size="lg"
                >
                  Learn More About Us
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 bg-gray-50">
        <div className="container">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-primary font-semibold uppercase tracking-wider text-sm">Our Services</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2">
              Comprehensive Real Estate Solutions
            </h2>
            <p className="text-gray-600 mt-4">
              From property acquisition to management, we provide end-to-end services tailored for diaspora clients.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {services.map((service, index) => (
              <Card
                key={index}
                className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-none bg-white"
              >
                <CardContent className="p-6 space-y-4">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-colors">
                    <service.icon className="h-7 w-7 text-primary group-hover:text-white transition-colors" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900">{service.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{service.description}</p>
                  <Link
                    to={service.link}
                    className="inline-flex items-center text-primary font-medium text-sm hover:gap-2 transition-all"
                  >
                    Learn More
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="py-20 bg-gray-900 text-white">
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-2">
                <span className="text-primary font-semibold uppercase tracking-wider text-sm">Why Choose Us</span>
                <h2 className="text-3xl md:text-4xl font-bold">
                  Your Trusted Partner in African Real Estate
                </h2>
              </div>

              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Globe className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">Global Reach, Local Expertise</h3>
                    <p className="text-gray-400">With offices in Ghana, USA, and UK, we bridge continents to bring you the best opportunities.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Shield className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">Secure & Transparent</h3>
                    <p className="text-gray-400">We handle all legal documentation and provide regular updates on your investment.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <HeartHandshake className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">Diaspora-Focused Service</h3>
                    <p className="text-gray-400">We understand the unique challenges of investing from abroad and tailor our services accordingly.</p>
                  </div>
                </div>
              </div>

              <Button
                size="lg"
                onClick={() => navigate("/contact")}
                className="mt-4"
              >
                Get Started Today
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            {/* Image Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-4">
                <div className="aspect-square rounded-2xl overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
                    alt="Property 1"
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                  />
                </div>
                <div className="aspect-video rounded-2xl overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
                    alt="Property 2"
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                  />
                </div>
              </div>
              <div className="space-y-4 pt-8">
                <div className="aspect-video rounded-2xl overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
                    alt="Property 3"
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                  />
                </div>
                <div className="aspect-square rounded-2xl overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
                    alt="Property 4"
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-white">
        <div className="container">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-primary font-semibold uppercase tracking-wider text-sm">Testimonials</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2">
              What Our Clients Say
            </h2>
            <p className="text-gray-600 mt-4">
              Hear from diaspora members who have successfully invested with DiaServe Group.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border-none shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-8">
                  {/* Stars */}
                  <div className="flex gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-gray-600 mb-6 leading-relaxed italic">"{testimonial.text}"</p>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <Users className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{testimonial.name}</div>
                      <div className="text-sm text-gray-500 flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {testimonial.location}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Ready to Invest in Your Future?
            </h2>
            <p className="text-xl text-white/80">
              Take the first step towards owning property in Africa. Our team is ready to guide you
              through every step of the process.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Button
                size="lg"
                onClick={() => navigate("/properties")}
                className="bg-white text-primary hover:bg-gray-100 text-lg px-8 py-6 shadow-lg"
              >
                Browse Properties
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/contact")}
                className="border-white text-white hover:bg-white/10 text-lg px-8 py-6"
              >
                Schedule Consultation
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
