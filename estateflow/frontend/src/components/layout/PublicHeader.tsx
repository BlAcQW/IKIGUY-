import { Building2, Menu, User, LogIn, Heart } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";

export function PublicHeader() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const publicNav = [
    { name: "Properties", href: "/properties" },
    { name: "About", href: "/about" },
    { name: "Contact", href: "/contact" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Building2 className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Diaserve Properties
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {publicNav.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {item.name}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-2">
          {user ? (
            <>
              <Button onClick={() => navigate("/my-properties")} variant="ghost">
                <Heart className="h-4 w-4 mr-2" />
                My Properties
              </Button>
              <Button onClick={() => navigate("/dashboard")} variant="default">
                <User className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate("/login")} variant="ghost">
                <LogIn className="h-4 w-4 mr-2" />
                Sign In
              </Button>
              <Button onClick={() => navigate("/login")} variant="default">
                Get Started
              </Button>
            </>
          )}
        </div>

        {/* Mobile Menu */}
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[300px]">
            <div className="flex flex-col gap-4 mt-8">
              {publicNav.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
              <div className="border-t pt-4 space-y-2">
                {user ? (
                  <>
                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate("/my-properties");
                      }}
                      variant="ghost"
                      className="w-full"
                    >
                      <Heart className="h-4 w-4 mr-2" />
                      My Properties
                    </Button>
                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate("/dashboard");
                      }}
                      variant="default"
                      className="w-full"
                    >
                      <User className="h-4 w-4 mr-2" />
                      Dashboard
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate("/login");
                      }}
                      variant="ghost"
                      className="w-full"
                    >
                      <LogIn className="h-4 w-4 mr-2" />
                      Sign In
                    </Button>
                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate("/login");
                      }}
                      variant="default"
                      className="w-full"
                    >
                      Get Started
                    </Button>
                  </>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
