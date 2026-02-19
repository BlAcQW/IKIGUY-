import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import type { PropertyCreate } from "@/lib/types/property";

interface FeaturesStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function FeaturesStep({ formData, updateFormData }: FeaturesStepProps) {
  const updateFeatures = (field: string, value: any) => {
    updateFormData({
      features: {
        ...formData.features,
        [field]: value,
      },
    });
  };

  return (
    <div className="space-y-6 animate-slide-up-fade">
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="bedrooms">Bedrooms *</Label>
          <Input
            id="bedrooms"
            type="number"
            min="0"
            placeholder="3"
            value={formData.features?.bedrooms || ""}
            onChange={(e) => updateFeatures("bedrooms", parseInt(e.target.value) || 0)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="bathrooms">Bathrooms *</Label>
          <Input
            id="bathrooms"
            type="number"
            min="0"
            placeholder="2"
            value={formData.features?.bathrooms || ""}
            onChange={(e) => updateFeatures("bathrooms", parseInt(e.target.value) || 0)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="parking_spaces">Parking</Label>
          <Input
            id="parking_spaces"
            type="number"
            min="0"
            placeholder="2"
            value={formData.features?.parking_spaces || ""}
            onChange={(e) => updateFeatures("parking_spaces", parseInt(e.target.value) || 0)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="sqft">Square Feet *</Label>
          <Input
            id="sqft"
            type="number"
            min="0"
            placeholder="2500"
            value={formData.features?.sqft || ""}
            onChange={(e) => updateFeatures("sqft", parseInt(e.target.value) || 0)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="lot_size">Lot Size (sqft)</Label>
          <Input
            id="lot_size"
            type="number"
            min="0"
            placeholder="5000"
            value={formData.features?.lot_size || ""}
            onChange={(e) => updateFeatures("lot_size", parseInt(e.target.value) || 0)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="year_built">Year Built</Label>
        <Input
          id="year_built"
          type="number"
          min="1800"
          max={new Date().getFullYear()}
          placeholder="2020"
          value={formData.features?.year_built || ""}
          onChange={(e) => updateFeatures("year_built", parseInt(e.target.value) || 0)}
        />
      </div>

      <Card variant="elevated">
        <CardContent className="p-6">
          <Label className="text-base font-semibold mb-4 block">Amenities</Label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="pool"
                checked={formData.features?.pool || false}
                onCheckedChange={(checked) => updateFeatures("pool", checked)}
              />
              <Label htmlFor="pool" className="cursor-pointer">Pool</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="garden"
                checked={formData.features?.garden || false}
                onCheckedChange={(checked) => updateFeatures("garden", checked)}
              />
              <Label htmlFor="garden" className="cursor-pointer">Garden</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="balcony"
                checked={formData.features?.balcony || false}
                onCheckedChange={(checked) => updateFeatures("balcony", checked)}
              />
              <Label htmlFor="balcony" className="cursor-pointer">Balcony</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="garage"
                checked={formData.features?.garage || false}
                onCheckedChange={(checked) => updateFeatures("garage", checked)}
              />
              <Label htmlFor="garage" className="cursor-pointer">Garage</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="furnished"
                checked={formData.features?.furnished || false}
                onCheckedChange={(checked) => updateFeatures("furnished", checked)}
              />
              <Label htmlFor="furnished" className="cursor-pointer">Furnished</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="elevator"
                checked={formData.features?.elevator || false}
                onCheckedChange={(checked) => updateFeatures("elevator", checked)}
              />
              <Label htmlFor="elevator" className="cursor-pointer">Elevator</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="air_conditioning"
                checked={formData.features?.air_conditioning || false}
                onCheckedChange={(checked) => updateFeatures("air_conditioning", checked)}
              />
              <Label htmlFor="air_conditioning" className="cursor-pointer">A/C</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="security_system"
                checked={formData.features?.security_system || false}
                onCheckedChange={(checked) => updateFeatures("security_system", checked)}
              />
              <Label htmlFor="security_system" className="cursor-pointer">Security</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="gym"
                checked={formData.features?.gym || false}
                onCheckedChange={(checked) => updateFeatures("gym", checked)}
              />
              <Label htmlFor="gym" className="cursor-pointer">Gym</Label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
