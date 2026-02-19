/**
 * Edit Property Dialog Component
 *
 * Dialog for editing existing property listings with all fields.
 */

import { useState, useEffect } from "react";
import { X, Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpdateProperty } from "@/hooks/use-properties";
import { PropertyType, PropertyStatus } from "@/lib/types/property";
import type { Property, PropertyUpdate } from "@/lib/types/property";

interface EditPropertyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  property: Property | null;
}

export function EditPropertyDialog({ open, onOpenChange, property }: EditPropertyDialogProps) {
  const updateMutation = useUpdateProperty({
    onSuccess: () => {
      onOpenChange(false);
    },
  });

  // Basic info
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [propertyType, setPropertyType] = useState<PropertyType>(PropertyType.HOUSE);
  const [status, setStatus] = useState<PropertyStatus>(PropertyStatus.ACTIVE);

  // Location
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [country, setCountry] = useState("Ghana");
  const [neighborhood, setNeighborhood] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  // Features
  const [bedrooms, setBedrooms] = useState("");
  const [bathrooms, setBathrooms] = useState("");
  const [sqft, setSqft] = useState("");
  const [lotSize, setLotSize] = useState("");
  const [yearBuilt, setYearBuilt] = useState("");
  const [parkingSpaces, setParkingSpaces] = useState("");
  const [pool, setPool] = useState(false);
  const [garden, setGarden] = useState(false);
  const [balcony, setBalcony] = useState(false);
  const [petPolicy, setPetPolicy] = useState("not_allowed");
  const [petDeposit, setPetDeposit] = useState("");
  const [furnished, setFurnished] = useState(false);
  const [elevator, setElevator] = useState(false);
  const [airConditioning, setAirConditioning] = useState(false);
  const [securitySystem, setSecuritySystem] = useState(false);
  const [gym, setGym] = useState(false);
  const [storage, setStorage] = useState(false);

  // Financial
  const [priceUSD, setPriceUSD] = useState("");
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [hoaFees, setHoaFees] = useState("");
  const [propertyTax, setPropertyTax] = useState("");
  const [insurance, setInsurance] = useState("");

  // Media
  const [images, setImages] = useState<string[]>([]);
  const [videoUrl, setVideoUrl] = useState("");
  const [virtualTourUrl, setVirtualTourUrl] = useState("");

  // Agent
  const [agentName, setAgentName] = useState("");

  // Neighborhood data
  const [safetyRating, setSafetyRating] = useState("");
  const [walkabilityScore, setWalkabilityScore] = useState("");
  const [transitScore, setTransitScore] = useState("");

  // Populate form when property changes
  useEffect(() => {
    if (property) {
      setName(property.name);
      setDescription(property.description);
      setPropertyType(property.property_type);
      setStatus(property.status);

      setAddress(property.location.address);
      setCity(property.location.city);
      setState(property.location.state);
      setZipCode(property.location.zip_code);
      setCountry(property.location.country);
      setNeighborhood(property.location.neighborhood || "");
      setLatitude(property.location.latitude?.toString() || "");
      setLongitude(property.location.longitude?.toString() || "");

      setBedrooms(property.features.bedrooms.toString());
      setBathrooms(property.features.bathrooms.toString());
      setSqft(property.features.sqft.toString());
      setLotSize(property.features.lot_size?.toString() || "");
      setYearBuilt(property.features.year_built?.toString() || "");
      setParkingSpaces(property.features.parking_spaces?.toString() || "");
      setPool(property.features.pool);
      setGarden(property.features.garden);
      setBalcony(property.features.balcony);
      setPetPolicy(property.features.pet_policy);
      setPetDeposit(property.features.pet_deposit?.toString() || "");
      setFurnished(property.features.furnished);
      setElevator(property.features.elevator);
      setAirConditioning(property.features.air_conditioning);
      setSecuritySystem(property.features.security_system);
      setGym(property.features.gym);
      setStorage(property.features.storage);

      setPriceUSD(property.financial.price_usd.toString());
      setBaseCurrency(property.financial.base_currency);
      setHoaFees(property.financial.hoa_fees_monthly?.toString() || "");
      setPropertyTax(property.financial.property_tax_annual?.toString() || "");
      setInsurance(property.financial.insurance_estimate?.toString() || "");

      setImages(property.images || []);
      setVideoUrl(property.video_url || "");
      setVirtualTourUrl(property.virtual_tour_url || "");
      setAgentName(property.agent_name || "");

      setSafetyRating(property.neighborhood_data?.safety_rating?.toString() || "");
      setWalkabilityScore(property.neighborhood_data?.walkability_score?.toString() || "");
      setTransitScore(property.neighborhood_data?.transit_score?.toString() || "");
    }
  }, [property]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!property) return;

    const propertyData: PropertyUpdate = {
      name,
      description,
      property_type: propertyType,
      status,
      location: {
        address,
        city,
        state,
        zip_code: zipCode,
        country,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
        neighborhood,
      },
      neighborhood_data: {
        schools: property.neighborhood_data?.schools || [],
        amenities: property.neighborhood_data?.amenities || [],
        safety_rating: safetyRating ? parseFloat(safetyRating) : undefined,
        walkability_score: walkabilityScore ? parseInt(walkabilityScore) : undefined,
        transit_score: transitScore ? parseInt(transitScore) : undefined,
      },
      features: {
        bedrooms: parseInt(bedrooms),
        bathrooms: parseFloat(bathrooms),
        sqft: parseFloat(sqft),
        lot_size: lotSize ? parseFloat(lotSize) : undefined,
        year_built: yearBuilt ? parseInt(yearBuilt) : undefined,
        parking_spaces: parkingSpaces ? parseInt(parkingSpaces) : undefined,
        pool,
        garden,
        balcony,
        pet_policy: petPolicy,
        pet_deposit: petDeposit ? parseFloat(petDeposit) : undefined,
        furnished,
        elevator,
        air_conditioning: airConditioning,
        heating: false,
        fireplace: false,
        security_system: securitySystem,
        gym,
        storage,
      },
      financial: {
        price_usd: parseFloat(priceUSD),
        base_currency: baseCurrency,
        hoa_fees_monthly: hoaFees ? parseFloat(hoaFees) : undefined,
        property_tax_annual: propertyTax ? parseFloat(propertyTax) : undefined,
        insurance_estimate: insurance ? parseFloat(insurance) : undefined,
      },
      images,
      video_url: videoUrl || undefined,
      virtual_tour_url: virtualTourUrl || undefined,
      agent_name: agentName || undefined,
    };

    updateMutation.mutate({ id: property.id, updates: propertyData });
  };

  const addImage = () => {
    const url = prompt("Enter image URL:");
    if (url) {
      setImages([...images, url]);
    }
  };

  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Property</DialogTitle>
          <DialogDescription>
            Update property listing details
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Basic Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="name">Property Name *</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="propertyType">Property Type *</Label>
                <Select value={propertyType} onValueChange={(v) => setPropertyType(v as PropertyType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={PropertyType.APARTMENT}>Apartment</SelectItem>
                    <SelectItem value={PropertyType.HOUSE}>House</SelectItem>
                    <SelectItem value={PropertyType.VILLA}>Villa</SelectItem>
                    <SelectItem value={PropertyType.PENTHOUSE}>Penthouse</SelectItem>
                    <SelectItem value={PropertyType.LOFT}>Loft</SelectItem>
                    <SelectItem value={PropertyType.TOWNHOUSE}>Townhouse</SelectItem>
                    <SelectItem value={PropertyType.LAND}>Land</SelectItem>
                    <SelectItem value={PropertyType.COMMERCIAL}>Commercial</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="status">Status *</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as PropertyStatus)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={PropertyStatus.ACTIVE}>Active</SelectItem>
                    <SelectItem value={PropertyStatus.PENDING}>Pending</SelectItem>
                    <SelectItem value={PropertyStatus.SOLD}>Sold</SelectItem>
                    <SelectItem value={PropertyStatus.RENTED}>Rented</SelectItem>
                    <SelectItem value={PropertyStatus.INACTIVE}>Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Location - Simplified for brevity, same as Add dialog */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Location</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="address">Address *</Label>
                <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="city">City *</Label>
                <Input id="city" value={city} onChange={(e) => setCity(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="state">State/Region *</Label>
                <Input id="state" value={state} onChange={(e) => setState(e.target.value)} required />
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Property Features</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="bedrooms">Bedrooms *</Label>
                <Input id="bedrooms" type="number" value={bedrooms} onChange={(e) => setBedrooms(e.target.value)} required min="0" />
              </div>
              <div>
                <Label htmlFor="bathrooms">Bathrooms *</Label>
                <Input id="bathrooms" type="number" step="0.5" value={bathrooms} onChange={(e) => setBathrooms(e.target.value)} required min="0" />
              </div>
              <div>
                <Label htmlFor="sqft">Square Feet *</Label>
                <Input id="sqft" type="number" value={sqft} onChange={(e) => setSqft(e.target.value)} required min="0" />
              </div>
            </div>
          </div>

          {/* Financial */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Financial Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="priceUSD">Price (USD) *</Label>
                <Input id="priceUSD" type="number" value={priceUSD} onChange={(e) => setPriceUSD(e.target.value)} required min="0" />
              </div>
              <div>
                <Label htmlFor="baseCurrency">Base Currency</Label>
                <Select value={baseCurrency} onValueChange={setBaseCurrency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                    <SelectItem value="GHS">GHS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Media */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Media</h3>
            <div className="space-y-4">
              <div>
                <Label>Images</Label>
                <div className="space-y-2">
                  {images.map((img, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input value={img} readOnly className="flex-1" />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => removeImage(idx)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button type="button" variant="outline" onClick={addImage} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Image URL
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" variant="accent" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Updating..." : "Update Property"}
            </Button>
          </div>

          {updateMutation.isError && (
            <p className="text-sm text-destructive">
              Error: {updateMutation.error?.message || "Failed to update property"}
            </p>
          )}
        </form>
      </DialogContent>
    </Dialog>
  );
}
