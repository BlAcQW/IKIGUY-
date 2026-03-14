/**
 * My Properties Page.
 *
 * Unified view showing user's favorited properties and properties with booked tours.
 * Features tabbed interface with grid/list view toggle.
 */

import { useState, useEffect } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Heart, Calendar, LayoutGrid, List, Loader2, Home } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { SavePropertyButton } from "@/components/SavePropertyButton";
import { useBookedProperties } from "@/hooks/use-user";
import { getSavedProperties } from "@/lib/api/user-api";

// Helper to get property image
function getPropertyImage(property: any): string {
  if (property.images && property.images.length > 0) {
    return property.images[0];
  }
  return "/placeholder-property.jpg";
}

// Helper to format price
function formatPrice(price?: number, currency?: string): string {
  if (!price) return "Price on request";
  const formatted = new Intl.NumberFormat("en-US").format(price);
  return `${currency || "GHS"} ${formatted}`;
}

export default function MyProperties() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [savedProperties, setSavedProperties] = useState<any[]>([]);
  const [savedLoading, setSavedLoading] = useState(true);
  const [savedError, setSavedError] = useState<string | null>(null);

  // Fetch booked properties using React Query hook
  const {
    data: bookedProperties = [],
    isLoading: bookedLoading,
    error: bookedError,
  } = useBookedProperties({ limit: 100 });

  // Fetch saved properties
  useEffect(() => {
    if (!user) {
      setSavedLoading(false);
      return;
    }

    async function fetchSaved() {
      try {
        setSavedLoading(true);
        const response = await getSavedProperties({
          limit: 100,
          include_property_details: true,
        });
        setSavedProperties(response.saved_properties || []);
      } catch (error: any) {
        console.error("Failed to fetch saved properties:", error);
        setSavedError(error.message || "Failed to load favorites");
      } finally {
        setSavedLoading(false);
      }
    }

    fetchSaved();
  }, [user]);

  // Redirect to signup if not authenticated
  if (!user) {
    return <Navigate to="/signup" replace />;
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold">My Properties</h1>
          <p className="text-muted-foreground mt-1">
            View your favorited properties and booked tours
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setViewMode("grid")}
            title="Grid view"
          >
            <LayoutGrid className="h-4 w-4" />
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

      {/* Tabs */}
      <Tabs defaultValue="favorites" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="favorites" className="flex items-center gap-2">
            <Heart className="h-4 w-4" />
            Favorites ({savedProperties.length})
          </TabsTrigger>
          <TabsTrigger value="booked" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Booked Tours ({bookedProperties.length})
          </TabsTrigger>
        </TabsList>

        {/* Favorites Tab */}
        <TabsContent value="favorites" className="mt-6">
          {/* Loading State */}
          {savedLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Error State */}
          {savedError && !savedLoading && (
            <Card className="p-6">
              <p className="text-center text-destructive">
                Failed to load favorites: {savedError}
              </p>
            </Card>
          )}

          {/* Empty State */}
          {!savedLoading && !savedError && savedProperties.length === 0 && (
            <Card className="p-12">
              <div className="text-center space-y-4">
                <Heart className="h-16 w-16 mx-auto text-muted-foreground/50" />
                <div>
                  <h3 className="text-lg font-semibold mb-2">No Favorites Yet</h3>
                  <p className="text-muted-foreground mb-6">
                    Start exploring properties and save your favorites
                  </p>
                  <Button onClick={() => navigate("/properties")}>
                    <Home className="h-4 w-4 mr-2" />
                    Browse Properties
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Properties Grid/List */}
          {!savedLoading && !savedError && savedProperties.length > 0 && (
            <div
              className={`grid gap-6 ${
                viewMode === "grid"
                  ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                  : "grid-cols-1"
              }`}
            >
              {savedProperties.map((saved) => {
                const property = saved.property_details || saved.property || {};
                return (
                  <Link key={saved.property_id} to={`/properties/${saved.property_id}`}>
                    <Card variant="interactive" className="overflow-hidden group">
                      {/* Image Container */}
                      <div className="relative aspect-[4/3] overflow-hidden">
                        <img
                          src={getPropertyImage(property)}
                          alt={property.name || "Property"}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                        {/* Status Badge */}
                        {property.status && (
                          <Badge
                            variant={
                              property.status === "active"
                                ? "success"
                                : property.status === "pending"
                                ? "warning"
                                : "muted"
                            }
                            className="absolute top-4 left-4 shadow-lg backdrop-blur-sm"
                          >
                            {property.status}
                          </Badge>
                        )}

                        {/* Favorite Button */}
                        <div className="absolute top-4 right-4" onClick={(e) => e.stopPropagation()}>
                          <SavePropertyButton propertyId={saved.property_id} />
                        </div>

                        {/* Price */}
                        <div className="absolute bottom-4 left-4 text-white">
                          <p className="text-2xl font-bold drop-shadow-lg">
                            {formatPrice(property.price, property.currency)}
                          </p>
                        </div>
                      </div>

                      {/* Content */}
                      <CardContent className="p-4">
                        <h3 className="font-semibold text-lg mb-2 line-clamp-1">
                          {property.name || "Unnamed Property"}
                        </h3>
                        {property.location && (
                          <p className="text-sm text-muted-foreground mb-3 line-clamp-1">
                            {property.location}
                          </p>
                        )}
                        {property.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {property.description}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Booked Tours Tab */}
        <TabsContent value="booked" className="mt-6">
          {/* Loading State */}
          {bookedLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Error State */}
          {bookedError && !bookedLoading && (
            <Card className="p-6">
              <p className="text-center text-destructive">
                Failed to load booked properties: {bookedError.message}
              </p>
            </Card>
          )}

          {/* Empty State */}
          {!bookedLoading && !bookedError && bookedProperties.length === 0 && (
            <Card className="p-12">
              <div className="text-center space-y-4">
                <Calendar className="h-16 w-16 mx-auto text-muted-foreground/50" />
                <div>
                  <h3 className="text-lg font-semibold mb-2">No Booked Tours</h3>
                  <p className="text-muted-foreground mb-6">
                    You haven't booked any property tours yet
                  </p>
                  <Button onClick={() => navigate("/properties")}>
                    <Home className="h-4 w-4 mr-2" />
                    Browse Properties
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Properties Grid/List */}
          {!bookedLoading && !bookedError && bookedProperties.length > 0 && (
            <div
              className={`grid gap-6 ${
                viewMode === "grid"
                  ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                  : "grid-cols-1"
              }`}
            >
              {bookedProperties.map((property) => (
                <Link key={property.id} to={`/properties/${property.id}`}>
                  <Card variant="interactive" className="overflow-hidden group">
                    {/* Image Container */}
                    <div className="relative aspect-[4/3] overflow-hidden">
                      <img
                        src={getPropertyImage(property)}
                        alt={property.name || "Property"}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                      {/* Booking Badge */}
                      <Badge className="absolute top-4 left-4 bg-blue-600 text-white shadow-lg backdrop-blur-sm">
                        {property.booking_count} {property.booking_count === 1 ? "booking" : "bookings"}
                      </Badge>

                      {/* Booking Status Badge */}
                      <Badge
                        variant={
                          property.latest_booking_status === "confirmed"
                            ? "success"
                            : property.latest_booking_status === "requested"
                            ? "warning"
                            : "muted"
                        }
                        className="absolute top-4 right-4 shadow-lg backdrop-blur-sm"
                      >
                        {property.latest_booking_status}
                      </Badge>

                      {/* Price */}
                      <div className="absolute bottom-4 left-4 text-white">
                        <p className="text-2xl font-bold drop-shadow-lg">
                          {formatPrice(property.price, property.currency)}
                        </p>
                      </div>
                    </div>

                    {/* Content */}
                    <CardContent className="p-4">
                      <h3 className="font-semibold text-lg mb-2 line-clamp-1">
                        {property.name || "Unnamed Property"}
                      </h3>
                      {property.location && (
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-1">
                          {property.location}
                        </p>
                      )}
                      {property.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                          {property.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <span>
                          Latest: {new Date(property.latest_booking_date).toLocaleDateString()}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
