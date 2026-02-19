import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PropertyType, PropertyStatus } from "@/lib/types/property";
import type { PropertyCreate } from "@/lib/types/property";

interface BasicInfoStepProps {
  formData: Partial<PropertyCreate>;
  updateFormData: (data: Partial<PropertyCreate>) => void;
}

export function BasicInfoStep({ formData, updateFormData }: BasicInfoStepProps) {
  return (
    <div className="space-y-6 animate-slide-up-fade">
      <div className="space-y-2">
        <Label htmlFor="name">Property Name *</Label>
        <Input
          id="name"
          placeholder="e.g., Sunset Villa, Downtown Loft"
          value={formData.name || ""}
          onChange={(e) => updateFormData({ name: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="property_type">Property Type *</Label>
          <Select
            value={formData.property_type}
            onValueChange={(value) => updateFormData({ property_type: value as PropertyType })}
          >
            <SelectTrigger id="property_type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={PropertyType.HOUSE}>House</SelectItem>
              <SelectItem value={PropertyType.APARTMENT}>Apartment</SelectItem>
              <SelectItem value={PropertyType.CONDO}>Condo</SelectItem>
              <SelectItem value={PropertyType.VILLA}>Villa</SelectItem>
              <SelectItem value={PropertyType.LAND}>Land</SelectItem>
              <SelectItem value={PropertyType.COMMERCIAL}>Commercial</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="status">Status *</Label>
          <Select
            value={formData.status}
            onValueChange={(value) => updateFormData({ status: value as PropertyStatus })}
          >
            <SelectTrigger id="status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={PropertyStatus.ACTIVE}>Active</SelectItem>
              <SelectItem value={PropertyStatus.PENDING}>Pending</SelectItem>
              <SelectItem value={PropertyStatus.SOLD}>Sold</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description *</Label>
        <Textarea
          id="description"
          placeholder="Describe the property, its features, and what makes it special..."
          rows={6}
          value={formData.description || ""}
          onChange={(e) => updateFormData({ description: e.target.value })}
          required
        />
      </div>
    </div>
  );
}
