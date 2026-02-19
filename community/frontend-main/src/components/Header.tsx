import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Menu, User, Search, X, LogOut, Settings, Crown } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { AuthModal } from "./AuthModal";
import SearchModal from "./SearchModal";
import RealTimeNotifications from "./RealTimeNotifications";

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const navigate = useNavigate();
  const { user, profile, signOut, loading } = useAuth();


  const handleSearchToggle = () => {
    setIsSearchModalOpen(true);
  };

  const handleMobileMenuToggle = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleUserProfile = () => {
    if (user) {
      navigate('/profile');
    } else {
      setIsAuthModalOpen(true);
    }
  };

  const handleJoinCommunity = () => {
    if (user) {
      navigate('/submit');
    } else {
      setIsAuthModalOpen(true);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const getUserInitials = () => {
    if (profile?.full_name) {
      return profile.full_name.split(' ').map(n => n[0]).join('').toUpperCase();
    }
    if (profile?.username) {
      return profile.username.slice(0, 2).toUpperCase();
    }
    if (user?.email) {
      return user.email.slice(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo and Navigation */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center text-primary-foreground font-bold text-sm">
              AL
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-bold text-foreground">AfriLang</h1>
              <p className="text-xs text-muted-foreground -mt-1">Community</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6">
            <a href="/dashboard" className="text-sm font-medium hover:text-primary transition-colors">
              Dashboard
            </a>
            <a href="/languages" className="text-sm font-medium hover:text-primary transition-colors">
              Languages
            </a>
            <a href="/submit" className="text-sm font-medium hover:text-primary transition-colors">
              Contribute
            </a>
            <a href="/validate" className="text-sm font-medium hover:text-primary transition-colors">
              Validate
            </a>
            <a href="/community" className="text-sm font-medium hover:text-primary transition-colors">
              Community
            </a>
            <a href="/datasets" className="text-sm font-medium hover:text-primary transition-colors">
              Datasets
            </a>
            <a href="/mlops" className="text-sm font-medium hover:text-primary transition-colors">
              MLOps
            </a>
          </nav>
        </div>


        {/* User Actions */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="relative" onClick={handleSearchToggle}>
            <Search className="h-4 w-4" />
          </Button>

          <RealTimeNotifications showConnectionStatus={true} />

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={profile?.avatar_url || undefined} alt={profile?.full_name || profile?.username || 'User'} />
                    <AvatarFallback className="text-xs">
                      {getUserInitials()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="flex items-center gap-2 p-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={profile?.avatar_url || undefined} />
                    <AvatarFallback className="text-xs">
                      {getUserInitials()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{profile?.full_name || profile?.username}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/dashboard')}>
                  <User className="mr-2 h-4 w-4" />
                  Dashboard
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/submit')}>
                  <Crown className="mr-2 h-4 w-4" />
                  Contribute
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="ghost" size="icon" className="relative" onClick={() => setIsAuthModalOpen(true)}>
              <User className="h-4 w-4" />
            </Button>
          )}

          <Button
            variant="hero"
            size="sm"
            className="hidden sm:flex"
            onClick={handleJoinCommunity}
          >
            {user ? 'Contribute' : 'Join Community'}
          </Button>

          <Button variant="ghost" size="icon" className="md:hidden" onClick={handleMobileMenuToggle}>
            <Menu className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-border/40 bg-background/95 backdrop-blur">
          <nav className="container mx-auto px-4 py-4 space-y-2">
            <a href="/dashboard" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Dashboard
            </a>
            <a href="/languages" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Languages
            </a>
            <a href="/submit" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Contribute
            </a>
            <a href="/validate" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Validate
            </a>
            <a href="/community" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Community
            </a>
            <a href="/datasets" className="block py-2 text-sm font-medium hover:text-primary transition-colors">
              Datasets
            </a>
            <div className="pt-2 border-t border-border/40">
              <Button variant="hero" size="sm" className="w-full" onClick={handleJoinCommunity}>
                {user ? 'Contribute' : 'Join Community'}
              </Button>
            </div>
          </nav>
        </div>
      )}

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />

      <SearchModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
      />
    </header>
  );
};

export default Header;