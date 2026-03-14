import { useState } from "react";
import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { PropertyCreate } from "@/lib/types/property";

interface FeaturesStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function FeaturesStep({ formData, updateFormData }: FeaturesStepProps) {
  const [customFeatureInput, setCustomFeatureInput] = useState("");

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

            <div className="flex items-center space-x-2">
              <Checkbox
                id="concierge"
                checked={formData.features?.concierge || false}
                onCheckedChange={(checked) => updateFeatures("concierge", checked)}
              />
              <Label htmlFor="concierge" className="cursor-pointer">Concierge</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="newly_built"
                checked={formData.features?.newly_built || false}
                onCheckedChange={(checked) => updateFeatures("newly_built", checked)}
              />
              <Label htmlFor="newly_built" className="cursor-pointer">Newly Built</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="renovated"
                checked={formData.features?.renovated || false}
                onCheckedChange={(checked) => updateFeatures("renovated", checked)}
              />
              <Label htmlFor="renovated" className="cursor-pointer">Newly Renovated</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card variant="elevated">
        <CardContent className="p-6">
          <Label className="text-base font-semibold mb-4 block">Custom Features</Label>
          <p className="text-sm text-muted-foreground mb-3">
            Add unique features not covered above (e.g., "Rooftop terrace", "Wine cellar")
          </p>
          <div className="flex gap-2 mb-3">
            <Input
              placeholder="Type a custom feature..."
              value={customFeatureInput}
              onChange={(e) => setCustomFeatureInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const value = customFeatureInput.trim();
                  const existing = formData.features?.custom_features ?? [];
                  if (value && value.length <= 50 && existing.length < 20 && !existing.includes(value)) {
                    updateFeatures("custom_features", [...existing, value]);
                    setCustomFeatureInput("");
                  }
                }
              }}
              maxLength={50}
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                const value = customFeatureInput.trim();
                const existing = formData.features?.custom_features ?? [];
                if (value && value.length <= 50 && existing.length < 20 && !existing.includes(value)) {
                  updateFeatures("custom_features", [...existing, value]);
                  setCustomFeatureInput("");
                }
              }}
              disabled={!customFeatureInput.trim() || (formData.features?.custom_features?.length ?? 0) >= 20}
            >
              Add
            </Button>
          </div>
          {(formData.features?.custom_features?.length ?? 0) > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.features?.custom_features?.map((feature) => (
                <Badge key={feature} variant="muted" className="gap-1 pr-1">
                  {feature}
                  <button
                    type="button"
                    onClick={() =>
                      updateFeatures(
                        "custom_features",
                        (formData.features?.custom_features ?? []).filter((f) => f !== feature)
                      )
                    }
                    className="ml-1 rounded-full p-0.5 hover:bg-destructive/20 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            {formData.features?.custom_features?.length ?? 0}/20 custom features
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
