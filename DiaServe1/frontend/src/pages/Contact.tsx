import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { MapPin, Phone, Mail, Clock, Send, Globe } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Contact() {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    subject: "",
    message: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission
    setTimeout(() => {
      toast({
        title: "Message Sent!",
        description: "Thank you for contacting us. We'll get back to you within 24 hours.",
      });
      setFormData({
        name: "",
        email: "",
        phone: "",
        subject: "",
        message: "",
      });
      setIsSubmitting(false);
    }, 1000);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const contactInfo = [
    {
      icon: MapPin,
      title: "Ghana Office",
      details: ["Accra, Ghana"],
      type: "location",
    },
    {
      icon: Globe,
      title: "United States Office",
      details: ["4739 Verdana Loop", "Frederick, Maryland 21703"],
      type: "location",
    },
    {
      icon: Mail,
      title: "Email",
      details: ["info@diaservegroup.com", "sales@diaservegroup.com"],
      type: "email",
    },
    {
      icon: Phone,
      title: "Phone",
      details: ["+233 (0) XXX XXX XXX", "+1 (XXX) XXX-XXXX"],
      type: "phone",
    },
    {
      icon: Clock,
      title: "Business Hours",
      details: ["Monday - Friday: 8:00 AM - 6:00 PM (GMT)", "Saturday: 9:00 AM - 2:00 PM (GMT)", "Sunday: Closed"],
      type: "hours",
    },
  ];

  const officeLocations = [
    {
      name: "Ghana Headquarters",
      address: "Accra, Ghana",
      description: "Our main office serving clients across Ghana and West Africa",
    },
    {
      name: "United States Office",
      address: "4739 Verdana Loop, Frederick, MD 21703",
      description: "Serving diaspora clients in North America",
    },
    {
      name: "United Kingdom",
      address: "DiaServe UK Ltd",
      description: "Serving diaspora clients in Europe and the UK",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 py-16">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              Get in Touch
            </h1>
            <p className="text-xl text-muted-foreground">
              Ready to start your investment journey? We're here to help
            </p>
          </div>
        </div>
      </div>

      <div className="container py-12 space-y-12">
        {/* Contact Information Cards */}
        <section>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contactInfo.map((info, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <info.icon className="h-5 w-5 text-primary" />
                    </div>
                    {info.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    {info.details.map((detail, detailIndex) => (
                      <p key={detailIndex} className="text-muted-foreground">
                        {info.type === "email" ? (
                          <a href={`mailto:${detail}`} className="hover:text-primary transition-colors">
                            {detail}
                          </a>
                        ) : info.type === "phone" ? (
                          <a href={`tel:${detail.replace(/\s/g, "")}`} className="hover:text-primary transition-colors">
                            {detail}
                          </a>
                        ) : (
                          detail
                        )}
                      </p>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Main Content - Form and Office Locations */}
        <section className="grid lg:grid-cols-2 gap-8">
          {/* Contact Form */}
          <Card>
            <CardHeader>
              <CardTitle>Send Us a Message</CardTitle>
              <CardDescription>
                Fill out the form below and we'll get back to you within 24 hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    placeholder="John Doe"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    placeholder="john@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+233 XXX XXX XXX"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="subject">Subject *</Label>
                  <Input
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    placeholder="How can we help you?"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="message">Message *</Label>
                  <Textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    placeholder="Tell us about your investment goals or any questions you have..."
                    rows={6}
                  />
                </div>

                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>Sending...</>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Send Message
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Office Locations */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Our Offices</CardTitle>
                <CardDescription>
                  Find us in multiple locations to serve you better
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {officeLocations.map((office, index) => (
                  <div key={index} className="space-y-2 pb-6 border-b last:border-b-0 last:pb-0">
                    <div className="flex items-start gap-3">
                      <MapPin className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <div>
                        <h3 className="font-semibold">{office.name}</h3>
                        <p className="text-sm text-muted-foreground">{office.address}</p>
                        <p className="text-sm text-muted-foreground mt-1">{office.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card className="bg-primary text-primary-foreground">
              <CardContent className="pt-6 space-y-4">
                <h3 className="text-lg font-semibold">Looking for Something Specific?</h3>
                <div className="space-y-2">
                  <a
                    href="/properties"
                    className="block p-3 rounded-lg bg-primary-foreground/10 hover:bg-primary-foreground/20 transition-colors"
                  >
                    <div className="font-semibold">Browse Properties</div>
                    <div className="text-sm text-primary-foreground/80">
                      Explore our current listings
                    </div>
                  </a>
                  <a
                    href="/about"
                    className="block p-3 rounded-lg bg-primary-foreground/10 hover:bg-primary-foreground/20 transition-colors"
                  >
                    <div className="font-semibold">About DiaServe</div>
                    <div className="text-sm text-primary-foreground/80">
                      Learn more about our company
                    </div>
                  </a>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* FAQ Section */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Frequently Asked Questions</CardTitle>
              <CardDescription>
                Quick answers to common questions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-semibold">What services do you offer for diaspora clients?</h4>
                <p className="text-muted-foreground">
                  We offer comprehensive real estate services including property acquisition, management,
                  investment consulting, and business development specifically tailored for Ghanaians and
                  Africans living abroad.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">How can I invest in Ghana from abroad?</h4>
                <p className="text-muted-foreground">
                  We guide you through the entire investment process, from identifying suitable properties
                  to handling all legal and administrative requirements. Contact us to schedule a consultation.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">Do you provide property management services?</h4>
                <p className="text-muted-foreground">
                  Yes! We offer comprehensive property management services including tenant sourcing, rent
                  collection, maintenance, and regular property inspections for clients living abroad.
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">What are your consultation fees?</h4>
                <p className="text-muted-foreground">
                  Initial consultations are free. We'll discuss your investment goals and provide tailored
                  recommendations. Service fees vary based on the specific services required.
                </p>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Call to Action */}
        <section className="text-center">
          <Card className="bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 border-none">
            <CardContent className="pt-8 pb-8 space-y-4">
              <h2 className="text-2xl font-bold">Start Your Investment Journey Today</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Join hundreds of diaspora clients who have successfully invested in African real estate
                with DiaServe Group. Our expert team is ready to help you achieve your investment goals.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                <Button size="lg" asChild>
                  <a href="#contact-form" onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}>
                    Schedule a Consultation
                  </a>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <a href="/properties">View Available Properties</a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
