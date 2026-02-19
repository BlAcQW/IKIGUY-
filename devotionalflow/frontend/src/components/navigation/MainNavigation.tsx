import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { BookOpen, Menu, X, Bell, Shield, BookmarkIcon, Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";

export function MainNavigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const getInitials = (name: string | undefined) => {
    if (!name) return "U";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const isAdmin = user?.role === 'admin';

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-secondary-foreground" />
          </div>
          <span className="font-serif font-bold text-xl text-foreground hidden sm:inline">
            FreshManna
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          {user ? (
            // Authenticated Navigation
            <>
              <Link
                to="/today"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/today')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Today
                {isActive('/today') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/feed"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/feed')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Feed
                {isActive('/feed') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/browse"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/browse')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Browse
                {isActive('/browse') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/series"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/series')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Series
                {isActive('/series') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/bookmarks"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/bookmarks')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Bookmarks
                {isActive('/bookmarks') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/discussions"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/discussions')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Discussions
                {isActive('/discussions') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/groups"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/groups')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Groups
                {isActive('/groups') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
            </>
          ) : (
            // Unauthenticated Navigation
            <>
              <Link
                to="/"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Home
                {isActive('/') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/browse"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/browse')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Browse
                {isActive('/browse') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/series"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/series')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Series
                {isActive('/series') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/today"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/today')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Today's Devotional
                {isActive('/today') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
              <Link
                to="/about"
                className={`text-sm font-medium transition-colors relative ${
                  isActive('/about')
                    ? 'text-secondary font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                About
                {isActive('/about') && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-secondary" />
                )}
              </Link>
            </>
          )}
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-3">
          {user ? (
            // Authenticated User Actions
            <>
              {/* Admin Panel Button */}
              {isAdmin && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/admin')}
                  className="hidden md:flex"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Admin Panel
                </Button>
              )}

              {/* Notifications */}
              <Button variant="ghost" size="icon" className="hidden md:flex">
                <Bell className="w-5 h-5" />
              </Button>

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                    <Avatar className="h-9 w-9">
                      <AvatarImage src={user.avatar_url} alt={user.name} />
                      <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user.name}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/profile')}>
                    My Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/bookmarks')}>
                    <BookmarkIcon className="w-4 h-4 mr-2" />
                    Bookmarks
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/profile')}>
                    Reading History
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/profile')}>
                    Achievements
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {isAdmin && (
                    <>
                      <DropdownMenuItem onClick={() => navigate('/admin')}>
                        <Shield className="w-4 h-4 mr-2" />
                        Admin Panel
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                    </>
                  )}
                  <DropdownMenuItem onClick={handleLogout}>
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            // Unauthenticated Actions
            <>
              <Button
                variant="ghost"
                onClick={() => navigate('/auth')}
                className="hidden md:inline-flex"
              >
                Login
              </Button>
              <Button onClick={() => navigate('/auth')}>
                Sign Up
              </Button>
            </>
          )}

          {/* Mobile Menu Toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border">
          <div className="container py-4 space-y-3">
            {user ? (
              // Authenticated Mobile Menu
              <>
                <Link
                  to="/today"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/today')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Today
                </Link>
                <Link
                  to="/feed"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/feed')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Feed
                </Link>
                <Link
                  to="/browse"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/browse')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Browse
                </Link>
                <Link
                  to="/bookmarks"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/bookmarks')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Bookmarks
                </Link>
                <Link
                  to="/discussions"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/discussions')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Discussions
                </Link>
                <Link
                  to="/groups"
                  className={`block px-3 py-2 text-sm font-medium rounded-md ${
                    isActive('/groups')
                      ? 'bg-secondary/10 text-secondary font-semibold'
                      : 'text-foreground hover:bg-accent'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Groups
                </Link>
                {isAdmin && (
                  <Link
                    to="/admin"
                    className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Shield className="w-4 h-4 inline mr-2" />
                    Admin Panel
                  </Link>
                )}
                <div className="border-t border-border pt-3 mt-3">
                  <button
                    onClick={() => {
                      handleLogout();
                      setMobileMenuOpen(false);
                    }}
                    className="block w-full text-left px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              // Unauthenticated Mobile Menu
              <>
                <Link
                  to="/"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Home
                </Link>
                <Link
                  to="/browse"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Browse
                </Link>
                <Link
                  to="/today"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Today's Devotional
                </Link>
                <Link
                  to="/about"
                  className="block px-3 py-2 text-sm font-medium text-foreground hover:bg-accent rounded-md"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  About
                </Link>
                <div className="border-t border-border pt-3 mt-3 space-y-2">
                  <Button
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => {
                      navigate('/auth');
                      setMobileMenuOpen(false);
                    }}
                  >
                    Login
                  </Button>
                  <Button
                    className="w-full"
                    onClick={() => {
                      navigate('/auth');
                      setMobileMenuOpen(false);
                    }}
                  >
                    Sign Up
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
