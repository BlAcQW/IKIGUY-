import { Menu, User, LogIn, Heart, ChevronDown } from "lucide-react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function PublicHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const publicNav = [
    { name: "Home", href: "/" },
    { name: "Properties", href: "/properties" },
    { name: "About", href: "/about" },
    { name: "Contact", href: "/contact" },
  ];

  const isActive = (href: string) => {
    if (href === "/") return location.pathname === "/";
    return location.pathname.startsWith(href);
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur-md shadow-sm border-b border-gray-100">
      <div className="container">
        <div className="flex h-20 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <img
              src="/logo.png"
              alt="DiaServe Properties"
              className="h-14 w-auto transition-transform duration-300 group-hover:scale-105"
            />
          </Link>

          {/* Desktop Navigation - Centered */}
          <nav className="hidden lg:flex items-center gap-1">
            {publicNav.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "px-5 py-2.5 text-sm font-medium tracking-wide transition-all duration-300 rounded-lg relative group",
                  isActive(item.href)
                    ? "text-primary"
                    : "text-gray-700 hover:text-primary hover:bg-primary/5"
                )}
              >
                {item.name}
                {/* Active indicator */}
                <span
                  className={cn(
                    "absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 bg-primary transition-all duration-300",
                    isActive(item.href) ? "w-6" : "w-0 group-hover:w-6"
                  )}
                />
              </Link>
            ))}

            {/* Services Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger className="px-5 py-2.5 text-sm font-medium tracking-wide text-gray-700 hover:text-primary hover:bg-primary/5 transition-all duration-300 rounded-lg flex items-center gap-1 outline-none">
                Services
                <ChevronDown className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem asChild>
                  <Link to="/properties" className="cursor-pointer">
                    Property Sales
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/properties" className="cursor-pointer">
                    Property Rentals
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/about" className="cursor-pointer">
                    Property Management
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/contact" className="cursor-pointer">
                    Investment Advisory
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>

          {/* Desktop Actions */}
          <div className="hidden lg:flex items-center gap-3">
            {user ? (
              <>
                <Button
                  onClick={() => navigate("/my-properties")}
                  variant="ghost"
                  className="gap-2 text-gray-700 hover:text-primary hover:bg-primary/5"
                >
                  <Heart className="h-4 w-4" />
                  Saved
                </Button>
                <Button
                  onClick={() => navigate("/dashboard")}
                  className="gap-2 px-6 shadow-md hover:shadow-lg transition-shadow"
                >
                  <User className="h-4 w-4" />
                  Dashboard
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => navigate("/login")}
                  variant="ghost"
                  className="gap-2 text-gray-700 hover:text-primary hover:bg-primary/5"
                >
                  <LogIn className="h-4 w-4" />
                  Staff Login
                </Button>
                <Button
                  onClick={() => navigate("/properties")}
                  className="px-6 shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
                >
                  View Properties
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild className="lg:hidden">
              <Button variant="ghost" size="icon" className="text-gray-700">
                <Menu className="h-6 w-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] p-0">
              <div className="flex flex-col h-full">
                {/* Mobile Header */}
                <div className="p-6 border-b">
                  <img
                    src="/logo.png"
                    alt="DiaServe Properties"
                    className="h-12 w-auto"
                  />
                </div>

                {/* Mobile Navigation */}
                <div className="flex-1 overflow-auto py-6">
                  <nav className="space-y-1 px-4">
                    {publicNav.map((item) => (
                      <Link
                        key={item.name}
                        to={item.href}
                        className={cn(
                          "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                          isActive(item.href)
                            ? "bg-primary/10 text-primary"
                            : "text-gray-700 hover:bg-gray-100"
                        )}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        {item.name}
                      </Link>
                    ))}

                    {/* Mobile Services Section */}
                    <div className="pt-4 pb-2">
                      <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Services
                      </p>
                    </div>
                    <Link
                      to="/properties"
                      className="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Property Sales & Rentals
                    </Link>
                    <Link
                      to="/about"
                      className="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Property Management
                    </Link>
                  </nav>
                </div>

                {/* Mobile Actions */}
                <div className="p-6 border-t space-y-3">
                  {user ? (
                    <>
                      <Button
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate("/my-properties");
                        }}
                        variant="outline"
                        className="w-full gap-2"
                      >
                        <Heart className="h-4 w-4" />
                        Saved Properties
                      </Button>
                      <Button
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate("/dashboard");
                        }}
                        className="w-full gap-2"
                      >
                        <User className="h-4 w-4" />
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
                        variant="outline"
                        className="w-full gap-2"
                      >
                        <LogIn className="h-4 w-4" />
                        Staff Login
                      </Button>
                      <Button
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate("/properties");
                        }}
                        className="w-full"
                      >
                        View Properties
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
