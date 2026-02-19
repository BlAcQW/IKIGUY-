import { Link } from "react-router-dom";
import {
    Facebook,
    Twitter,
    Instagram,
    Linkedin,
    Mail,
    Phone,
    MapPin,
    ArrowRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Footer() {
    const currentYear = new Date().getFullYear();

    const quickLinks = [
        { name: "Properties", href: "/properties" },
        { name: "About Us", href: "/about" },
        { name: "Contact", href: "/contact" },
        { name: "Help Center", href: "/help" },
    ];

    const services = [
        { name: "Property Sales", href: "/properties" },
        { name: "Property Rentals", href: "/properties" },
        { name: "Property Management", href: "/about" },
        { name: "Investment Advisory", href: "/contact" },
    ];

    const socialLinks = [
        { icon: Facebook, href: "https://facebook.com", label: "Facebook" },
        { icon: Twitter, href: "https://twitter.com", label: "Twitter" },
        { icon: Instagram, href: "https://instagram.com", label: "Instagram" },
        { icon: Linkedin, href: "https://linkedin.com", label: "LinkedIn" },
    ];

    return (
        <footer className="bg-gray-900 text-gray-300">
            {/* Main Footer Content */}
            <div className="container py-16">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
                    {/* Brand Column */}
                    <div className="space-y-6">
                        <Link to="/" className="inline-block">
                            <img
                                src="/logo.png"
                                alt="DiaServe Properties"
                                className="h-16 w-auto brightness-0 invert"
                            />
                        </Link>
                        <p className="text-sm leading-relaxed">
                            DiaServe Group connects diaspora communities to lucrative investment
                            opportunities in Ghana and Africa. Your trusted partner for real estate
                            and property management.
                        </p>
                        {/* Social Links */}
                        <div className="flex items-center gap-3">
                            {socialLinks.map((social) => (
                                <a
                                    key={social.label}
                                    href={social.href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-primary hover:text-white transition-all duration-300"
                                    aria-label={social.label}
                                >
                                    <social.icon className="h-4 w-4" />
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Quick Links Column */}
                    <div>
                        <h3 className="text-white font-semibold text-lg mb-6 relative">
                            Quick Links
                            <span className="absolute bottom-0 left-0 w-12 h-0.5 bg-primary -mb-2"></span>
                        </h3>
                        <ul className="space-y-3">
                            {quickLinks.map((link) => (
                                <li key={link.name}>
                                    <Link
                                        to={link.href}
                                        className="text-sm hover:text-primary hover:pl-2 transition-all duration-300 flex items-center gap-2 group"
                                    >
                                        <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        {link.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Services Column */}
                    <div>
                        <h3 className="text-white font-semibold text-lg mb-6 relative">
                            Our Services
                            <span className="absolute bottom-0 left-0 w-12 h-0.5 bg-primary -mb-2"></span>
                        </h3>
                        <ul className="space-y-3">
                            {services.map((service) => (
                                <li key={service.name}>
                                    <Link
                                        to={service.href}
                                        className="text-sm hover:text-primary hover:pl-2 transition-all duration-300 flex items-center gap-2 group"
                                    >
                                        <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        {service.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Contact & Newsletter Column */}
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-white font-semibold text-lg mb-6 relative">
                                Contact Us
                                <span className="absolute bottom-0 left-0 w-12 h-0.5 bg-primary -mb-2"></span>
                            </h3>
                            <ul className="space-y-4">
                                <li className="flex items-start gap-3">
                                    <MapPin className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                    <span className="text-sm">Accra, Ghana</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Mail className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                    <a
                                        href="mailto:info@diaservegroup.com"
                                        className="text-sm hover:text-primary transition-colors"
                                    >
                                        info@diaservegroup.com
                                    </a>
                                </li>
                                <li className="flex items-start gap-3">
                                    <Phone className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                                    <a
                                        href="tel:+233000000000"
                                        className="text-sm hover:text-primary transition-colors"
                                    >
                                        +233 (0) XXX XXX XXX
                                    </a>
                                </li>
                            </ul>
                        </div>

                        {/* Newsletter */}
                        <div className="pt-4">
                            <h4 className="text-white font-medium mb-3">Subscribe to Newsletter</h4>
                            <div className="flex gap-2">
                                <Input
                                    type="email"
                                    placeholder="Your email"
                                    className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-primary"
                                />
                                <Button size="icon" className="shrink-0">
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Bar */}
            <div className="border-t border-gray-800">
                <div className="container py-6">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                        <p className="text-sm text-gray-500">
                            © {currentYear} DiaServe Properties. All rights reserved.
                        </p>
                        <div className="flex items-center gap-6 text-sm">
                            <Link to="/privacy" className="text-gray-500 hover:text-primary transition-colors">
                                Privacy Policy
                            </Link>
                            <Link to="/terms" className="text-gray-500 hover:text-primary transition-colors">
                                Terms of Service
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
