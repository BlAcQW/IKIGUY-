import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Users, Globe, TrendingUp, Shield, Award } from "lucide-react";

export default function About() {
  const values = [
    {
      icon: Shield,
      title: "Innovation",
      description: "Leveraging cutting-edge technology to deliver exceptional real estate solutions",
    },
    {
      icon: Award,
      title: "Integrity",
      description: "Building trust through transparency, honesty, and ethical business practices",
    },
    {
      icon: TrendingUp,
      title: "Growth",
      description: "Committed to continuous improvement and expanding opportunities for our clients",
    },
    {
      icon: Users,
      title: "Collaboration",
      description: "Fostering an inclusive environment where creativity thrives and ideas flourish",
    },
  ];

  const services = [
    {
      title: "Real Estate Services",
      items: [
        "Commercial & Residential Leasing",
        "Investment & Sales Services",
        "Property Management",
        "Real Estate Brokerage",
        "Business Development",
      ],
    },
    {
      title: "Management Consulting",
      items: [
        "Sales Strategy Development",
        "New Business Development",
        "Diaspora Market Entry",
        "Market Expansion Consulting",
        "Client Relationship Management",
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 py-16">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              About DiaServe Group
            </h1>
            <p className="text-xl text-muted-foreground">
              The only diaspora service connoisseurs offering professional real asset management services
            </p>
          </div>
        </div>
      </div>

      <div className="container py-12 space-y-16">
        {/* Mission Section */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Building2 className="h-6 w-6 text-primary" />
                Our Mission
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lg text-muted-foreground">
                With over <span className="font-semibold text-foreground">twenty years of experience</span>,
                DiaServe Group connects clients, particularly Ghanaians living abroad, to lucrative investment
                opportunities in Ghana and other parts of Africa. We bridge the gap between diaspora communities
                and the African real estate market, making it easier for our clients to build wealth and secure
                their financial future through strategic property investments.
              </p>
              <p className="text-lg text-muted-foreground">
                Founded in 2019 in its current form, DiaServe Group operates as a dynamic and forward-thinking
                organization committed to creating meaningful impacts across industries. While primarily focused
                on real estate, we leverage technology, finance, and logistics to provide diverse, integrated
                solutions that meet the unique needs of our diaspora clientele.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Values Section */}
        <section>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">Our Core Values</h2>
            <p className="text-muted-foreground">
              The principles that guide everything we do
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <Card key={index} className="text-center">
                <CardContent className="pt-6 space-y-4">
                  <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <value.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-semibold text-lg">{value.title}</h3>
                  <p className="text-sm text-muted-foreground">{value.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Services Section */}
        <section>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">What We Offer</h2>
            <p className="text-muted-foreground">
              Comprehensive solutions for diaspora investment and business development
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {services.map((service, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-xl">{service.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {service.items.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-start gap-2">
                        <div className="mt-1 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                        <span className="text-muted-foreground">{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Stats Section */}
        <section>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="text-center">
              <CardContent className="pt-6 space-y-2">
                <div className="text-4xl font-bold text-primary">20+</div>
                <div className="text-muted-foreground">Years of Experience</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="pt-6 space-y-2">
                <div className="text-4xl font-bold text-primary">
                  <Globe className="h-10 w-10 mx-auto" />
                </div>
                <div className="text-muted-foreground">Ghana & International Presence</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="pt-6 space-y-2">
                <div className="text-4xl font-bold text-primary">
                  <Users className="h-10 w-10 mx-auto" />
                </div>
                <div className="text-muted-foreground">Diaspora-Focused Service</div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Why Choose Us Section */}
        <section>
          <Card className="bg-gradient-to-br from-primary/5 via-secondary/5 to-accent/5 border-none">
            <CardHeader>
              <CardTitle className="text-2xl text-center">Why Choose DiaServe Group?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Award className="h-5 w-5 text-primary" />
                    Diaspora Expertise
                  </h4>
                  <p className="text-muted-foreground">
                    As the only dedicated diaspora service connoisseurs, we understand the unique challenges
                    and opportunities facing Africans abroad seeking to invest back home.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-primary" />
                    Comprehensive Solutions
                  </h4>
                  <p className="text-muted-foreground">
                    From property acquisition to management and business development, we provide end-to-end
                    services that simplify your investment journey.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Globe className="h-5 w-5 text-primary" />
                    Local & Global Reach
                  </h4>
                  <p className="text-muted-foreground">
                    With operations in Ghana and presence in the United States and UK, we bridge continents
                    to bring you the best investment opportunities.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Proven Track Record
                  </h4>
                  <p className="text-muted-foreground">
                    Two decades of experience in connecting diaspora clients with profitable African real
                    estate and business ventures.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Work Culture Section */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Users className="h-6 w-6 text-primary" />
                Our Work Culture
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lg text-muted-foreground">
                At DiaServe Group, we foster an <span className="font-semibold text-foreground">inclusive workplace</span> where
                employees receive ongoing training and skill development opportunities. We believe that our team's growth
                directly translates to better service for our clients.
              </p>
              <p className="text-lg text-muted-foreground">
                We promote a collaborative environment where creativity thrives and ideas are welcomed. Every team member
                contributes to our mission of creating meaningful impacts across industries and helping diaspora communities
                build lasting wealth in Africa.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Call to Action */}
        <section className="text-center">
          <Card className="bg-primary text-primary-foreground">
            <CardContent className="pt-6 pb-6 space-y-4">
              <h2 className="text-2xl font-bold">Ready to Start Your Investment Journey?</h2>
              <p className="text-primary-foreground/90">
                Partner with DiaServe Group to unlock opportunities in African real estate and business development
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                <a
                  href="/contact"
                  className="inline-flex items-center justify-center rounded-md bg-background text-foreground px-8 py-3 font-semibold hover:bg-background/90 transition-colors"
                >
                  Contact Us
                </a>
                <a
                  href="/properties"
                  className="inline-flex items-center justify-center rounded-md border border-primary-foreground/20 px-8 py-3 font-semibold hover:bg-primary-foreground/10 transition-colors"
                >
                  View Properties
                </a>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
