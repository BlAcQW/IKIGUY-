/**
 * Property Detail Page.
 *
 * Displays detailed information about a property with AI chat widget.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, Home, MapPin, Bed, Bath, Maximize, Banknote, Loader2, Calculator, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CurrencySelector } from "@/components/CurrencySelector";
import { PropertyChatWidget } from "@/components/PropertyChatWidget";
import { PropertyImageCarousel } from "@/components/PropertyImageCarousel";
import { VideoPlayer } from "@/components/VideoPlayer";
import { BookingFormDialog } from "@/components/BookingFormDialog";
import { SavePropertyButton } from "@/components/SavePropertyButton";
import { useProperty } from "@/hooks/use-properties";
import { useCurrencies, useExchangeRates } from "@/hooks/use-currencies";
import { convertPrice, formatPrice } from "@/lib/api/currency-api";
import { saveProperty } from "@/lib/api/user-api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/components/ui/use-toast";
import { LeadForm } from "@/components/LeadForm";

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { toast } = useToast();
  const { data: property, isLoading, error } = useProperty(id || "");
  const [selectedCurrency, setSelectedCurrency] = useState("GHS");
  const [bookingDialogOpen, setBookingDialogOpen] = useState(false);
  const { data: currencies } = useCurrencies();
  const { data: exchangeRates } = useExchangeRates();

  // Handle deferred save action after signup
  useEffect(() => {
    const locationState = location.state as any;
    if (locationState?.deferredAction === "save-property" && locationState?.propertyId && user) {
      // Auto-save the property
      saveProperty(locationState.propertyId)
        .then(() => {
          toast({
            title: "Property Saved",
            description: "This property has been added to your favorites"
          });
          // Clear the state to prevent re-triggering
          navigate(location.pathname, { replace: true, state: {} });
        })
        .catch((error) => {
          console.error("Failed to auto-save property:", error);
          toast({
            title: "Error",
            description: "Failed to save property. Please try again.",
            variant: "destructive"
          });
        });
    }
  }, [location.state, user, navigate, location.pathname, toast]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <Card>
            <CardContent className="p-12 text-center space-y-4">
              <Home className="h-16 w-16 mx-auto text-muted-foreground/50" />
              <div>
                <h2 className="text-xl font-semibold mb-2">Property Not Found</h2>
                <p className="text-muted-foreground">
                  {error?.message || "The property you're looking for doesn't exist or has been removed."}
                </p>
              </div>
              <Button variant="accent" onClick={() => navigate("/properties")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Properties
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Calculate price per square foot
  const pricePerSqft = property.features.sqft
    ? property.financial.price_usd / property.features.sqft
    : undefined;

  // Helper to format price in selected currency
  const formatPropertyPrice = (priceUSD: number | undefined | null) => {
    // Handle undefined/null/NaN values
    if (priceUSD === undefined || priceUSD === null || isNaN(priceUSD)) {
      return "Price not available";
    }

    const selectedCurrencyObj = currencies?.find(c => c.code === selectedCurrency);
    if (!selectedCurrencyObj || !exchangeRates) {
      return `$${priceUSD.toLocaleString()}`;
    }

    if (selectedCurrency === "USD") {
      return formatPrice(priceUSD, selectedCurrencyObj);
    }

    const convertedPrice = convertPrice(priceUSD, selectedCurrency, exchangeRates);
    return formatPrice(convertedPrice, selectedCurrencyObj);
  };

  // Helper to calculate monthly mortgage payment
  const calculateMonthlyPayment = (
    principal: number,
    downPaymentPercent: number,
    interestRate: number,
    years: number = 30
  ) => {
    const loanAmount = principal * (1 - downPaymentPercent / 100);
    const monthlyRate = interestRate / 100 / 12;
    const numberOfPayments = years * 12;

    if (monthlyRate === 0) return loanAmount / numberOfPayments;

    const monthlyPayment =
      loanAmount *
      (monthlyRate * Math.pow(1 + monthlyRate, numberOfPayments)) /
      (Math.pow(1 + monthlyRate, numberOfPayments) - 1);

    return monthlyPayment;
  };

  // Helper to format location string (filters out null values)
  const locationFull = {
    address: property.location.address || "",
    cityStateZip: [property.location.city, property.location.state, property.location.zip_code]
      .filter(p => p && p !== "null")
      .join(", ") || "City not specified",
    country: property.location.country && property.location.country !== "null" ? property.location.country : ""
  };

  return (
    <div className="min-h-screen pb-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6 max-w-7xl">
        {/* Page Header with Back Button */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/properties")}
              className="shrink-0"
              title="Back to properties"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="min-w-0">
              <h1 className="text-xl md:text-2xl font-bold text-foreground truncate">
                {property.name}
              </h1>
              <p className="text-sm text-muted-foreground flex items-center gap-1 truncate">
                <MapPin className="h-3 w-3 shrink-0" />
                {`${property.location.city}, ${property.location.state || property.location.country}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <SavePropertyButton propertyId={property.id} variant="large" showLabel />
            <CurrencySelector value={selectedCurrency} onValueChange={setSelectedCurrency} />
          </div>
        </div>
        {/* Property Image Carousel */}
        <PropertyImageCarousel
          images={property.images || []}
          propertyName={property.name}
          className="w-full"
        />

        {/* Property Video Tour */}
        {property.video_url && (
          <div className="mt-6">
            <VideoPlayer
              videoUrl={property.video_url}
              title={`${property.name} - Video Tour`}
              thumbnail={property.images && property.images.length > 0 ? property.images[0] : undefined}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Price & Status */}
            <Card variant="premium" className="animate-slide-up-fade">
              <CardHeader>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <CardTitle className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-2">
                      {formatPropertyPrice(property.financial.price_usd)}
                    </CardTitle>
                    {selectedCurrency !== "USD" && (
                      <p className="text-xs text-muted-foreground/80">
                        ${property.financial.price_usd.toLocaleString()} USD
                      </p>
                    )}
                    <p className="text-sm text-muted-foreground mt-1">
                      {formatPropertyPrice(pricePerSqft)}/sqft
                    </p>
                  </div>
                  <Badge
                    variant={
                      property.status === "active"
                        ? "success"
                        : property.status === "pending"
                          ? "warning"
                          : "muted"
                    }
                    className="text-base px-4 py-2"
                  >
                    {property.status}
                  </Badge>
                </div>
              </CardHeader>
            </Card>

            {/* Quick Stats */}
            <Card variant="elevated" className="animate-slide-up-fade" style={{ animationDelay: '100ms' }}>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="flex flex-col items-center text-center p-4 rounded-xl bg-gradient-to-br from-primary/10 to-transparent">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 mb-3">
                      <Bed className="h-6 w-6 text-primary" />
                    </div>
                    <p className="text-3xl font-bold mb-1">{property.features.bedrooms}</p>
                    <p className="text-sm text-muted-foreground">Bedrooms</p>
                  </div>
                  <div className="flex flex-col items-center text-center p-4 rounded-xl bg-gradient-to-br from-primary/10 to-transparent">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 mb-3">
                      <Bath className="h-6 w-6 text-primary" />
                    </div>
                    <p className="text-3xl font-bold mb-1">{property.features.bathrooms}</p>
                    <p className="text-sm text-muted-foreground">Bathrooms</p>
                  </div>
                  <div className="flex flex-col items-center text-center p-4 rounded-xl bg-gradient-to-br from-primary/10 to-transparent">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 mb-3">
                      <Maximize className="h-6 w-6 text-primary" />
                    </div>
                    <p className="text-3xl font-bold mb-1">{property.features.sqft.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">Sq Ft</p>
                  </div>
                  <div className="flex flex-col items-center text-center p-4 rounded-xl bg-gradient-to-br from-primary/10 to-transparent">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 mb-3">
                      <Banknote className="h-6 w-6 text-primary" />
                    </div>
                    <p className="text-3xl font-bold mb-1">{formatPropertyPrice(pricePerSqft)}</p>
                    <p className="text-sm text-muted-foreground">Per Sq Ft</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Features */}
            {(() => {
              const featuresList = [
                { key: "pool", label: "Pool" },
                { key: "garden", label: "Garden" },
                { key: "balcony", label: "Balcony" },
                { key: "garage", label: "Garage" },
                { key: "furnished", label: "Furnished" },
                { key: "elevator", label: "Elevator" },
                { key: "air_conditioning", label: "A/C" },
                { key: "heating", label: "Heating" },
                { key: "fireplace", label: "Fireplace" },
                { key: "security_system", label: "Security" },
                { key: "gym", label: "Gym" },
                { key: "storage", label: "Storage" },
                { key: "concierge", label: "Concierge" },
                { key: "newly_built", label: "Newly Built" },
                { key: "renovated", label: "Newly Renovated" },
              ] as const;
              const activeFeatures = featuresList.filter(
                (f) => (property.features as Record<string, unknown>)[f.key]
              );
              const hasParking = property.features.parking_spaces && property.features.parking_spaces > 0;
              const hasCustomFeatures = (property.features.custom_features?.length ?? 0) > 0;
              if (activeFeatures.length === 0 && !hasParking && !hasCustomFeatures) return null;
              return (
                <Card variant="elevated" className="animate-slide-up-fade" style={{ animationDelay: '200ms' }}>
                  <CardHeader>
                    <CardTitle>Features</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-3">
                      {activeFeatures.map((f) => (
                        <Badge
                          key={f.key}
                          variant="muted"
                          className="hover:scale-110 hover:-translate-y-1 hover:shadow-md hover:bg-primary/15 hover:text-primary hover:border-primary/30 cursor-default"
                        >
                          {f.label}
                        </Badge>
                      ))}
                      {hasParking && (
                        <Badge
                          variant="muted"
                          className="hover:scale-110 hover:-translate-y-1 hover:shadow-md hover:bg-primary/15 hover:text-primary hover:border-primary/30 cursor-default"
                        >
                          {property.features.parking_spaces} Parking
                        </Badge>
                      )}
                      {property.features.custom_features?.map((feature) => (
                        <Badge
                          key={feature}
                          variant="muted"
                          className="hover:scale-110 hover:-translate-y-1 hover:shadow-md hover:bg-primary/15 hover:text-primary hover:border-primary/30 cursor-default"
                        >
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Description */}
            <Card>
              <CardHeader>
                <CardTitle>Description</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">{property.description}</p>
              </CardContent>
            </Card>

            {/* Location */}
            <Card>
              <CardHeader>
                <CardTitle>Location</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      {locationFull.address && <p className="font-medium">{locationFull.address}</p>}
                      <p className="text-sm text-muted-foreground">{locationFull.cityStateZip}</p>
                      {locationFull.country && <p className="text-sm text-muted-foreground">{locationFull.country}</p>}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Lead Collection / Schedule Tour */}
            {!user ? (
              <div className="space-y-6">
                <Card variant="elevated" className="bg-gradient-to-br from-primary/5 to-accent/5">
                  <CardHeader>
                    <CardTitle className="text-lg">Schedule a Tour</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Interested in visiting this property? Book a tour at a time that works for you.
                    </p>
                    <Button
                      onClick={() => setBookingDialogOpen(true)}
                      className="w-full"
                      size="lg"
                      variant="default"
                    >
                      <Calendar className="mr-2 h-5 w-5" />
                      Book a Tour
                    </Button>
                  </CardContent>
                </Card>
                <LeadForm propertyId={property.id} propertyName={property.name} />
              </div>
            ) : (
              <Card variant="elevated" className="bg-gradient-to-br from-primary/5 to-accent/5">
                <CardHeader>
                  <CardTitle className="text-lg">Staff Options</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    As staff, you can manage this property or book a tour for a client.
                  </p>
                  <Button
                    onClick={() => setBookingDialogOpen(true)}
                    className="w-full"
                    size="lg"
                    variant="default"
                  >
                    <Calendar className="mr-2 h-5 w-5" />
                    Book for Client
                  </Button>
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-border" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-background px-2 text-muted-foreground">Or</span>
                    </div>
                  </div>
                  <SavePropertyButton propertyId={property.id} variant="large" showLabel className="w-full" />
                </CardContent>
              </Card>
            )}

            {/* Financial Details */}
            <Card>
              <CardHeader>
                <CardTitle>Financial Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Price</span>
                  <span className="font-semibold">{formatPropertyPrice(property.financial.price_usd)}</span>
                </div>
                {selectedCurrency !== "USD" && (
                  <div className="flex justify-between">
                    <span className="text-xs text-muted-foreground/70">Price (USD)</span>
                    <span className="text-xs text-muted-foreground/70">${property.financial.price_usd.toLocaleString()}</span>
                  </div>
                )}
                {property.financial.hoa_fees_monthly && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">HOA Fees</span>
                    <span className="font-semibold">
                      {formatPropertyPrice(property.financial.hoa_fees_monthly)}/mo
                    </span>
                  </div>
                )}
                {property.financial.property_tax_annual && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Property Tax</span>
                    <span className="font-semibold">
                      {formatPropertyPrice(property.financial.property_tax_annual)}/yr
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Financing Options */}
            <Card variant="elevated">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-accent" />
                  <CardTitle>Financing Options</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Estimated Monthly Payments */}
                {[
                  { downPayment: 20, rate: 6.5, label: "20% Down @ 6.5% APR" },
                  { downPayment: 10, rate: 7.0, label: "10% Down @ 7.0% APR" },
                  { downPayment: 5, rate: 7.5, label: "5% Down @ 7.5% APR" },
                ].map((option, index) => {
                  const monthlyPayment = calculateMonthlyPayment(
                    property.financial.price_usd,
                    option.downPayment,
                    option.rate
                  );
                  const downPaymentAmount = property.financial.price_usd * (option.downPayment / 100);

                  return (
                    <div
                      key={index}
                      className="p-4 rounded-lg border bg-muted/30 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{option.label}</span>
                        <Badge variant="soft" className="text-xs">
                          30 years
                        </Badge>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Down Payment</span>
                          <span className="font-semibold">
                            {formatPropertyPrice(downPaymentAmount)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Monthly</span>
                          <span className="text-lg font-bold text-accent">
                            {formatPropertyPrice(monthlyPayment)}/mo
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}

                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground text-center">
                    Estimates based on current market rates. Actual rates may vary.
                  </p>
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>

      {/* AI Chat Widget */}
      <PropertyChatWidget propertyId={property.id} propertyName={property.name} />

      {/* Booking Dialog */}
      <BookingFormDialog
        open={bookingDialogOpen}
        onOpenChange={setBookingDialogOpen}
        propertyId={property.id}
        propertyName={property.name}
        onSuccess={() => {
          setBookingDialogOpen(false);
        }}
      />
    </div>
  );
}
