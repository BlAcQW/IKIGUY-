import { BookOpen, Heart, Facebook, HandHeart } from "lucide-react";
import { Button } from "@/components/ui/button";
import donationLogo from "@/assets/donation_logo.png";

const Footer = () => {
  const footerLinks = {
    Product: ["Features", "Pricing", "Roadmap", "Updates"],
    Resources: ["Documentation", "Help Center", "Community", "Blog"],
    Company: ["About", "Careers", "Press", "Contact"],
    Legal: ["Privacy", "Terms", "Cookies"],
  };

  return (
    <footer className="bg-primary text-primary-foreground">
      {/* CTA Section */}
      <div className="border-b border-primary-foreground/10">
        <div className="container mx-auto px-4 py-16 text-center">
          <h2 className="font-serif text-3xl md:text-4xl font-bold mb-4">
            Ready to Grow Your Faith?
          </h2>
          <p className="text-primary-foreground/70 max-w-2xl mx-auto mb-8">
            Join 150,000+ believers experiencing daily spiritual growth through devotionals,
            scripture study, and authentic community.
          </p>
          <Button variant="hero" size="xl" asChild>
            <a href="/auth">Join FreshManna Free</a>
          </Button>
        </div>
      </div>

      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <a href="#" className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-secondary-foreground" />
              </div>
              <span className="font-serif text-xl font-semibold">
                FreshManna
              </span>
            </a>
            <p className="text-primary-foreground/60 text-sm mb-4">
              Devotionals with Suzanne and Dave. Your daily companion for spiritual growth and community.
            </p>
            {/* Social Media Links */}
            <div className="flex items-center gap-3">
              <a
                href="https://www.facebook.com/profile.php?id=61563563450448"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-lg bg-primary-foreground/10 hover:bg-primary-foreground/20 flex items-center justify-center transition-colors group"
                aria-label="Follow us on Facebook"
              >
                <Facebook className="w-5 h-5 text-primary-foreground group-hover:scale-110 transition-transform" />
              </a>
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-semibold mb-4">{category}</h4>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-primary-foreground/60 hover:text-primary-foreground transition-colors text-sm"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Donation Section */}
        <div className="mt-12 pt-8 border-t border-primary-foreground/10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <img
                src={donationLogo}
                alt="Bishop Suzanne Nti - Online Prayer Ministry"
                className="h-12 md:h-16 w-auto object-contain"
                loading="lazy"
              />
              <div className="text-center sm:text-left">
                <p className="text-primary-foreground/80 text-sm font-medium mb-1">
                  Partner with Our Ministry
                </p>
                <p className="text-primary-foreground/60 text-xs">
                  Support daily devotionals and prayer ministry
                </p>
              </div>
            </div>
            <Button
              size="sm"
              variant="heroOutline"
              className="flex items-center gap-2"
              asChild
            >
              <a
                href="https://donorbox.org/oew-online-prayer-ministry"
                target="_blank"
                rel="noopener noreferrer"
              >
                <HandHeart className="w-4 h-4" />
                Donate
              </a>
            </Button>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-8 pt-8 border-t border-primary-foreground/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-primary-foreground/60 text-sm">
            © 2024 FreshManna. All rights reserved.
          </p>
          <p className="text-primary-foreground/60 text-sm flex items-center gap-1">
            Made with <Heart className="w-4 h-4 text-secondary fill-secondary" /> for believers worldwide
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
