/**
 * Saved Properties Page
 *
 * Shows user's favorited/saved properties.
 * Requires authentication.
 */

import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Heart, Lock, Loader2, MapPin, Bed, Bath, Square, Grid3X3, List } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { getSavedProperties, type SavedProperty } from "@/lib/api/user-api";
import { SavePropertyButton } from "@/components/SavePropertyButton";
import { CurrencySelector } from "@/components/CurrencySelector";
import { useCurrencies, useExchangeRates } from "@/hooks/use-currencies";
import { convertPrice, formatPrice } from "@/lib/api/currency-api";
import { getStorageUrl } from "@/lib/api-config";

export default function Saved() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedCurrency, setSelectedCurrency] = useState("GHS");

  const { data: currencies } = useCurrencies();
  const { data: exchangeRates } = useExchangeRates();

  // Fetch saved properties
  useEffect(() => {
    if (user) {
      fetchSavedProperties();
    }
  }, [user]);

  const fetchSavedProperties = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getSavedProperties({
        limit: 100,
        include_property_details: true,
      });
      setSavedProperties(response.saved_properties);
    } catch (err: any) {
      console.error("Error fetching saved properties:", err);
      setError(err.message || "Failed to load saved properties");
      toast({
        title: "Error",
        description: "Failed to load your saved properties. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to format property price in selected currency
  const formatPropertyPrice = (property: any) => {
    const selectedCurrencyObj = currencies?.find(c => c.code === selectedCurrency);
    if (!selectedCurrencyObj || !exchangeRates || !property?.financial) {
      return `$${property?.financial?.price_usd?.toLocaleString() || "N/A"}`;
    }

    if (selectedCurrency === "USD") {
      return formatPrice(property.financial.price_usd, selectedCurrencyObj);
    }

    const convertedPrice = convertPrice(property.financial.price_usd, selectedCurrency, exchangeRates);
    return formatPrice(convertedPrice, selectedCurrencyObj);
  };

  // Helper to get first image or placeholder
  const getPropertyImage = (property: any) => {
    if (property?.images && property.images.length > 0) {
      return getStorageUrl(property.images[0]);
    }
    return "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&h=400&fit=crop";
  };

  // Helper to get full address
  const getPropertyAddress = (property: any) => {
    if (!property?.location) return "Address not available";
    const { location } = property;

    // Build address parts, filtering out null/empty values
    const parts = [
      location.city,
      location.state,
      location.country
    ].filter(part => part && part !== "null" && part !== "");

    // If no parts, try address
    if (parts.length === 0 && location.address) {
      return location.address;
    }

    return parts.length > 0 ? parts.join(", ") : "Location not specified";
  };

  // Unauthenticated view - Login required
  if (!user) {
    return (
      <div className="min-h-screen bg-background pb-20 md:pb-0">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          {/* Mobile Header */}
          <div className="md:hidden mb-4">
            <h1 className="text-xl font-bold">Saved Properties</h1>
            <p className="text-sm text-muted-foreground">
              Sign in to save your favorites
            </p>
          </div>

          {/* Login Required Card */}
          <Card className="max-w-2xl mx-auto">
            <CardContent className="p-12 text-center space-y-6">
              <div className="flex justify-center">
                <div className="relative">
                  <div className="p-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20">
                    <Heart className="h-16 w-16 text-primary" />
                  </div>
                  <div className="absolute -bottom-1 -right-1 p-2 rounded-full bg-background border-2 border-border">
                    <Lock className="h-5 w-5 text-muted-foreground" />
                  </div>
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">Save Your Favorite Properties</h2>
                <p className="text-muted-foreground">
                  Sign in to save properties, compare them, and get instant updates on price changes.
                </p>
              </div>
              <ul className="text-left max-w-md mx-auto space-y-2 text-sm text-muted-foreground">
                <li>• Save unlimited properties</li>
                <li>• Get price drop alerts</li>
                <li>• Compare side-by-side</li>
                <li>• Share lists with family</li>
                <li>• Track viewing history</li>
                <li>• Sync across all devices</li>
              </ul>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  onClick={() => navigate("/signup", { state: { from: "/saved" } })}
                  size="lg"
                >
                  Create Account
                </Button>
                <Button
                  onClick={() => navigate("/properties")}
                  variant="outline"
                  size="lg"
                >
                  Browse Properties
                </Button>
              </div>
              <p className="text-sm text-muted-foreground text-center mt-4">
                Already have an account?{" "}
                <button
                  onClick={() => navigate("/login", { state: { from: "/saved" } })}
                  className="text-primary hover:underline font-medium"
                >
                  Sign in
                </button>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Authenticated user view
  return (
    <div className="min-h-screen bg-background pb-20 md:pb-0">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">Saved Properties</h1>
            <p className="text-sm md:text-base text-muted-foreground mt-1">
              Your favorite properties in one place
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <CurrencySelector value={selectedCurrency} onValueChange={setSelectedCurrency} />
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => setViewMode("grid")}
                title="Grid view"
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => setViewMode("list")}
                title="List view"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Total count */}
        <div className="flex items-center gap-3">
          <Badge variant="muted">
            {savedProperties.length} {savedProperties.length === 1 ? 'property' : 'properties'} saved
          </Badge>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <Card className="p-6">
            <p className="text-center text-destructive">
              {error}
            </p>
            <div className="flex justify-center mt-4">
              <Button onClick={fetchSavedProperties} variant="outline">
                Try Again
              </Button>
            </div>
          </Card>
        )}

        {/* Empty State */}
        {!isLoading && !error && savedProperties.length === 0 && (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="p-12 text-center space-y-6">
              <div className="flex justify-center">
                <div className="p-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20">
                  <Heart className="h-16 w-16 text-primary" />
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">No Saved Properties Yet</h2>
                <p className="text-muted-foreground">
                  Start exploring and save properties you love. Click the heart icon on any property to add it here.
                </p>
              </div>
              <Button
                onClick={() => navigate("/properties")}
                size="lg"
              >
                Browse Properties
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Properties Grid */}
        {!isLoading && !error && savedProperties.length > 0 && (
          <div className={`grid gap-6 ${
            viewMode === "grid"
              ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
              : "grid-cols-1"
          }`}>
            {savedProperties.map((savedItem, index) => {
              const property = savedItem.property;
              if (!property) return null;

              return (
                <Link key={savedItem.id} to={`/properties/${property.id}`}>
                  <Card
                    variant="interactive"
                    className="overflow-hidden group animate-scale-in"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    {/* Image Container */}
                    <div className="relative aspect-[4/3] overflow-hidden">
                      <img
                        src={getPropertyImage(property)}
                        alt={property.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                      {/* Status Badge */}
                      <Badge
                        variant={property.status === "active" ? "success" : "default"}
                        className="absolute top-3 left-3"
                      >
                        {property.status}
                      </Badge>

                      {/* Save Button */}
                      <div className="absolute top-3 right-3" onClick={(e) => e.preventDefault()}>
                        <SavePropertyButton propertyId={property.id} />
                      </div>

                      {/* Price Tag */}
                      <div className="absolute bottom-3 left-3">
                        <div className="bg-background/95 backdrop-blur-sm px-3 py-2 rounded-lg">
                          <p className="text-lg font-bold text-foreground">
                            {formatPropertyPrice(property)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Property Details */}
                    <CardContent className="p-4 space-y-3">
                      <div>
                        <h3 className="font-semibold text-lg text-foreground line-clamp-1 group-hover:text-accent transition-colors">
                          {property.name}
                        </h3>
                        <div className="flex items-start gap-1 mt-1">
                          <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {getPropertyAddress(property)}
                          </p>
                        </div>
                      </div>

                      {/* Features */}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        {property.bedrooms && (
                          <div className="flex items-center gap-1">
                            <Bed className="h-4 w-4" />
                            <span>{property.bedrooms}</span>
                          </div>
                        )}
                        {property.bathrooms && (
                          <div className="flex items-center gap-1">
                            <Bath className="h-4 w-4" />
                            <span>{property.bathrooms}</span>
                          </div>
                        )}
                        {property.area_sqft && (
                          <div className="flex items-center gap-1">
                            <Square className="h-4 w-4" />
                            <span>{property.area_sqft.toLocaleString()} sqft</span>
                          </div>
                        )}
                      </div>

                      {/* Property Type */}
                      {property.property_type && (
                        <Badge variant="muted" className="w-fit">
                          {property.property_type}
                        </Badge>
                      )}
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
