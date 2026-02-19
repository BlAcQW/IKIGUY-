import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PropertyCreate } from "@/lib/types/property";

interface LocationStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function LocationStep({ formData, updateFormData }: LocationStepProps) {
  const updateLocation = (field: string, value: string) => {
    updateFormData({
      location: {
        ...formData.location,
        [field]: value,
      },
    });
  };

  return (
    <div className="space-y-6 animate-slide-up-fade">
      <div className="space-y-2">
        <Label htmlFor="address">Street Address *</Label>
        <Input
          id="address"
          placeholder="123 Main Street"
          value={formData.location?.address || ""}
          onChange={(e) => updateLocation("address", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City *</Label>
          <Input
            id="city"
            placeholder="Accra"
            value={formData.location?.city || ""}
            onChange={(e) => updateLocation("city", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="state">State/Region *</Label>
          <Input
            id="state"
            placeholder="Greater Accra"
            value={formData.location?.state || ""}
            onChange={(e) => updateLocation("state", e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="zip_code">Zip Code</Label>
          <Input
            id="zip_code"
            placeholder="00233"
            value={formData.location?.zip_code || ""}
            onChange={(e) => updateLocation("zip_code", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="country">Country *</Label>
          <Input
            id="country"
            placeholder="Ghana"
            value={formData.location?.country || "Ghana"}
            onChange={(e) => updateLocation("country", e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="neighborhood">Neighborhood</Label>
          <Input
            id="neighborhood"
            placeholder="e.g., East Legon, Airport Residential"
            value={formData.location?.neighborhood || ""}
            onChange={(e) => updateLocation("neighborhood", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="digital_address">Digital Address (Ghana Post GPS)</Label>
          <Input
            id="digital_address"
            placeholder="e.g., GD-123-4567"
            value={formData.location?.digital_address || ""}
            onChange={(e) => updateLocation("digital_address", e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="latitude">Latitude (optional)</Label>
          <Input
            id="latitude"
            type="number"
            step="0.000001"
            placeholder="5.6037"
            value={formData.location?.latitude || ""}
            onChange={(e) => updateLocation("latitude", e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="longitude">Longitude (optional)</Label>
          <Input
            id="longitude"
            type="number"
            step="0.000001"
            placeholder="-0.1870"
            value={formData.location?.longitude || ""}
            onChange={(e) => updateLocation("longitude", e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
