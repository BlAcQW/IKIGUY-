import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  Filter,
  Grid3X3,
  List,
  MapPin,
  Bed,
  Bath,
  Square,
  Heart,
  MoreHorizontal,
  MessageSquare,
  Sparkles,
  Loader2,
  Edit,
  Trash2,
  Building2
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { CurrencySelector } from "@/components/CurrencySelector";
import { AddPropertyDialog } from "@/components/AddPropertyDialog";
import { EditPropertyDialog } from "@/components/EditPropertyDialog";
import { PropertyFilters } from "@/components/PropertyFilters";
import { SavePropertyButton } from "@/components/SavePropertyButton";
import { PropertySearchBar } from "@/components/PropertySearchBar";
import { useProperties, useDeleteProperty } from "@/hooks/use-properties";
import { useCurrencies, useExchangeRates } from "@/hooks/use-currencies";
import { convertPrice, formatPrice } from "@/lib/api/currency-api";
import { getStorageUrl } from "@/lib/api-config";
import { useAuth } from "@/contexts/AuthContext";
import type { Property, PropertyFilters as Filters } from "@/lib/types/property";

export default function Properties() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAuthenticated = !!user;
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCurrency, setSelectedCurrency] = useState("GHS");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [filters, setFilters] = useState<Filters>({});
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Property[]>([]);
  const [searchMetadata, setSearchMetadata] = useState<{
    query: string;
    total: number;
    timing?: any;
  } | null>(null);

  // Fetch properties and currencies with filters
  const { data: propertiesData, isLoading: propertiesLoading, error: propertiesError } = useProperties(filters);
  const { data: currencies, isLoading: currenciesLoading } = useCurrencies();
  const { data: exchangeRates, isLoading: ratesLoading } = useExchangeRates();

  // Delete mutation
  const deleteMutation = useDeleteProperty();

  // Use search results if searching, otherwise use regular properties
  const properties = isSearching ? searchResults : (propertiesData?.properties || []);
  const total = isSearching ? searchResults.length : (propertiesData?.total || 0);

  // Handlers
  const handleEdit = (property: Property) => {
    setSelectedProperty(property);
    setShowEditDialog(true);
  };

  const handleDelete = async (property: Property) => {
    if (confirm(`Are you sure you want to delete "${property.name}"?`)) {
      deleteMutation.mutate(property.id);
    }
  };

  const handleClearFilters = () => {
    setFilters({});
  };

  // Helper to format property price in selected currency
  const formatPropertyPrice = (property: Property) => {
    const selectedCurrencyObj = currencies?.find(c => c.code === selectedCurrency);
    if (!selectedCurrencyObj || !exchangeRates) {
      return `$${property.financial.price_usd.toLocaleString()}`;
    }

    if (selectedCurrency === "USD") {
      return formatPrice(property.financial.price_usd, selectedCurrencyObj);
    }

    const convertedPrice = convertPrice(property.financial.price_usd, selectedCurrency, exchangeRates);
    return formatPrice(convertedPrice, selectedCurrencyObj);
  };

  // Helper to get first image or placeholder
  const getPropertyImage = (property: Property) => {
    if (property.images && property.images.length > 0) {
      return getStorageUrl(property.images[0]);
    }
    return "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&h=400&fit=crop";
  };

  // Helper to get full address
  const getPropertyAddress = (property: Property) => {
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

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">
              {isAuthenticated ? "Your Properties" : "Browse Properties"}
            </h1>
            <p className="text-sm md:text-base text-muted-foreground mt-1">
              {isAuthenticated
                ? "Manage your property listings"
                : "Discover your perfect property"}
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <CurrencySelector value={selectedCurrency} onValueChange={setSelectedCurrency} />
            {isAuthenticated && (
              <Button variant="accent" className="gap-2" onClick={() => setShowAddDialog(true)}>
                <Plus className="h-4 w-4" />
                Add Property
              </Button>
            )}
          </div>
        </div>
        {/* AI Search Bar */}
        <PropertySearchBar
          onSearch={(results) => {
            try {
              console.log('Search results received:', results);

              // Update properties list with search results (use property_data, not property)
              const properties = results.matches
                .map((m: any) => m.property_data || m.property) // Fallback for backwards compatibility
                .filter(Boolean); // Remove any undefined values

              setSearchResults(properties);

              // Show search metadata
              setIsSearching(true);
              setSearchMetadata({
                query: results.parsed_query?.original_query || results.query || "Search query",
                total: properties.length,
                timing: results.search_timing
              });
            } catch (error) {
              console.error('Error processing search results:', error);
            }
          }}
          onClear={() => {
            // Reset to default property list
            setIsSearching(false);
            setSearchResults([]);
            setSearchMetadata(null);
          }}
        />

        {/* Search Results Banner */}
        {isSearching && searchMetadata && (
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      AI Search: "{searchMetadata.query}"
                    </p>
                    <p className="text-xs text-primary">
                      Found {searchMetadata.total} {searchMetadata.total === 1 ? 'property' : 'properties'}
                      {searchMetadata.timing && ` in ${searchMetadata.timing.total_ms}ms`}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsSearching(false);
                    setSearchResults([]);
                    setSearchMetadata(null);
                  }}
                >
                  Clear Search
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters and View Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <PropertyFilters
              filters={filters}
              onFiltersChange={setFilters}
              onClear={handleClearFilters}
            />
            <Badge variant="muted">{total} {total === 1 ? 'property' : 'properties'}</Badge>
          </div>
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

        {/* Loading State */}
        {propertiesLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
          </div>
        )}

        {/* Error State */}
        {propertiesError && (
          <Card className="p-6">
            <p className="text-center text-destructive">
              Failed to load properties: {propertiesError.message}
            </p>
          </Card>
        )}

        {/* Empty State */}
        {!propertiesLoading && !propertiesError && properties.length === 0 && (
          <Card className="p-12">
            <div className="text-center space-y-4">
              <Building2 className="h-16 w-16 mx-auto text-muted-foreground/50" />
              <div>
                <h3 className="text-lg font-semibold mb-2">No properties found</h3>
                <p className="text-muted-foreground">
                  {isAuthenticated
                    ? "Get started by adding your first property listing."
                    : "Check back soon for new listings."}
                </p>
                {isAuthenticated && (
                  <Button variant="accent" onClick={() => setShowAddDialog(true)} className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Property
                  </Button>
                )}
              </div>
            </div>
          </Card>
        )}

        {!propertiesLoading && !propertiesError && properties.length > 0 && (
          <div className={`grid gap-6 ${viewMode === "grid"
            ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
            : "grid-cols-1"
            }`}>
            {properties.map((property, index) => (
              <Link key={property.id} to={`/properties/${property.id}`}>
                <Card
                  variant="interactive"
                  className="overflow-hidden group animate-scale-in"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Image Container with Enhanced Gradient */}
                  <div className="relative aspect-[4/3] overflow-hidden">
                    <img
                      src={getPropertyImage(property)}
                      alt={property.name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />

                    {/* Multi-layer gradient overlay for better text readability */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                    {/* Status Badge (top-left) with premium styling */}
                    <Badge
                      variant={
                        property.status === "active" ? "success" :
                          property.status === "pending" ? "warning" : "muted"
                      }
                      className="absolute top-4 left-4 shadow-lg backdrop-blur-sm"
                    >
                      {property.status === "active" ? "Available" : property.status}
                    </Badge>

                    {/* Banners */}
                    <div className="absolute top-4 left-4 mt-8 flex flex-col gap-2">
                      {property.features.newly_built && (
                        <Badge className="bg-blue-600 text-white border-0 shadow-lg">
                          Newly Built
                        </Badge>
                      )}
                      {property.features.renovated && (
                        <Badge className="bg-emerald-600 text-white border-0 shadow-lg">
                          Newly Renovated
                        </Badge>
                      )}
                      {property.financial.discount_percentage && property.financial.discount_percentage > 0 && (
                        <Badge className="bg-red-600 text-white border-0 shadow-lg">
                          {property.financial.discount_percentage}% Off
                        </Badge>
                      )}
                    </div>

                    {/* Favorite Button (top-right) */}
                    <div className="absolute top-4 right-4 flex gap-2" onClick={(e) => e.preventDefault()}>
                      <SavePropertyButton propertyId={property.id} />
                    </div>

                    {/* Price (bottom-left) with enhanced styling */}
                    <div className="absolute bottom-4 left-4">
                      <p className="text-2xl font-bold text-white drop-shadow-lg">
                        {formatPropertyPrice(property)}
                      </p>
                      {selectedCurrency !== "USD" && (
                        <p className="text-sm text-white/90 drop-shadow">
                          ${property.financial.price_usd.toLocaleString()} USD
                        </p>
                      )}
                    </div>

                    {/* Quick Actions (bottom-right, shown on hover) */}
                    <div className="absolute bottom-4 right-4 flex gap-2 opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200">
                      <Button variant="glass" size="sm" className="gap-1.5 shadow-lg">
                        <MessageSquare className="h-4 w-4" />
                        <span className="hidden sm:inline">Ask AI</span>
                      </Button>
                    </div>
                  </div>

                  {/* Property Info */}
                  <CardContent className="p-5 space-y-3">
                    {/* Title and Location */}
                    <div>
                      <h3 className="font-semibold text-lg line-clamp-1 group-hover:text-primary transition-colors">
                        {property.name}
                      </h3>
                      <p className="flex items-center gap-1 text-sm text-muted-foreground line-clamp-1 mt-1">
                        <MapPin className="h-4 w-4 flex-shrink-0" />
                        {getPropertyAddress(property)}
                      </p>
                    </div>

                    {/* Features Grid */}
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1.5">
                        <Bed className="h-4 w-4 text-primary" />
                        <span className="font-medium">{property.features.bedrooms}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Bath className="h-4 w-4 text-primary" />
                        <span className="font-medium">{property.features.bathrooms}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Square className="h-4 w-4 text-primary" />
                        <span className="font-medium">
                          {property.features.sqft?.toLocaleString() || 'N/A'} sqft
                        </span>
                      </div>
                    </div>

                    {/* Feature Badges */}
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="soft" className="text-xs">
                        {property.property_type}
                      </Badge>
                      {property.features.pool && (
                        <Badge variant="soft-success" className="text-xs">Pool</Badge>
                      )}
                      {property.features.garden && (
                        <Badge variant="soft-success" className="text-xs">Garden</Badge>
                      )}
                      {property.features.parking_spaces > 0 && (
                        <Badge variant="soft" className="text-xs">
                          {property.features.parking_spaces} Parking
                        </Badge>
                      )}
                    </div>

                    {/* Actions Row */}
                    <div className="flex items-center gap-2 pt-3 border-t">
                      {isAuthenticated && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={(e) => {
                              e.preventDefault();
                              handleEdit(property);
                            }}
                            className="hover:text-primary"
                            title="Edit property"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={(e) => {
                              e.preventDefault();
                              handleDelete(property);
                            }}
                            className="hover:text-destructive"
                            title="Delete property"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <div className="flex-1" />
                      <Button variant="soft" size="sm" className="gap-1.5">
                        View Details
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Add Property Dialog */}
      <AddPropertyDialog open={showAddDialog} onOpenChange={setShowAddDialog} />

      {/* Edit Property Dialog */}
      <EditPropertyDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        property={selectedProperty}
      />
    </div>
  );
}
