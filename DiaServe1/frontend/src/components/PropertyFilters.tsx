/**
 * Property Filters Component
 *
 * Comprehensive filtering UI for properties including price range,
 * property type, bedrooms, bathrooms, and location filters.
 */

import { useState } from "react";
import { X, SlidersHorizontal } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { PropertyType, PropertyStatus } from "@/lib/types/property";
import type { PropertyFilters as Filters } from "@/lib/types/property";

interface PropertyFiltersProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  onClear: () => void;
}

export function PropertyFilters({ filters, onFiltersChange, onClear }: PropertyFiltersProps) {
  const [open, setOpen] = useState(false);

  const handleFilterChange = (key: keyof Filters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  const handlePropertyTypeToggle = (type: PropertyType) => {
    const currentTypes = filters.property_type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];

    handleFilterChange('property_type', newTypes.length > 0 ? newTypes : undefined);
  };

  const handleStatusToggle = (status: PropertyStatus) => {
    const currentStatuses = filters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status];

    handleFilterChange('status', newStatuses.length > 0 ? newStatuses : undefined);
  };

  // Count active filters
  const activeFilterCount = [
    filters.min_price,
    filters.max_price,
    filters.property_type?.length,
    filters.status?.length,
    filters.min_bedrooms,
    filters.max_bedrooms,
    filters.min_bathrooms,
    filters.max_bathrooms,
    filters.location,
  ].filter(Boolean).length;

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" className="gap-2 relative">
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="accent" className="ml-1 px-1.5 py-0 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Filter Properties</SheetTitle>
          <SheetDescription>
            Narrow down your property search with filters
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Price Range */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Price Range (USD)</Label>
              {(filters.min_price || filters.max_price) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    handleFilterChange('min_price', undefined);
                    handleFilterChange('max_price', undefined);
                  }}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="min_price" className="text-xs text-muted-foreground">
                  Minimum
                </Label>
                <Input
                  id="min_price"
                  type="number"
                  placeholder="No min"
                  value={filters.min_price || ''}
                  onChange={(e) => handleFilterChange('min_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                  min="0"
                />
              </div>
              <div>
                <Label htmlFor="max_price" className="text-xs text-muted-foreground">
                  Maximum
                </Label>
                <Input
                  id="max_price"
                  type="number"
                  placeholder="No max"
                  value={filters.max_price || ''}
                  onChange={(e) => handleFilterChange('max_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                  min="0"
                />
              </div>
            </div>
          </div>

          {/* Property Type */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Property Type</Label>
              {filters.property_type && filters.property_type.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFilterChange('property_type', undefined)}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                PropertyType.APARTMENT,
                PropertyType.HOUSE,
                PropertyType.VILLA,
                PropertyType.PENTHOUSE,
                PropertyType.LOFT,
                PropertyType.TOWNHOUSE,
              ].map((type) => (
                <Badge
                  key={type}
                  variant={filters.property_type?.includes(type) ? "default" : "outline"}
                  className="cursor-pointer capitalize"
                  onClick={() => handlePropertyTypeToggle(type)}
                >
                  {type}
                </Badge>
              ))}
            </div>
          </div>

          {/* Status */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Status</Label>
              {filters.status && filters.status.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFilterChange('status', undefined)}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                PropertyStatus.ACTIVE,
                PropertyStatus.PENDING,
                PropertyStatus.SOLD,
                PropertyStatus.RENTED,
              ].map((status) => (
                <Badge
                  key={status}
                  variant={filters.status?.includes(status) ? "default" : "outline"}
                  className="cursor-pointer capitalize"
                  onClick={() => handleStatusToggle(status)}
                >
                  {status}
                </Badge>
              ))}
            </div>
          </div>

          {/* Bedrooms */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Bedrooms</Label>
              {(filters.min_bedrooms || filters.max_bedrooms) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    handleFilterChange('min_bedrooms', undefined);
                    handleFilterChange('max_bedrooms', undefined);
                  }}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="min_bedrooms" className="text-xs text-muted-foreground">
                  Minimum
                </Label>
                <Input
                  id="min_bedrooms"
                  type="number"
                  placeholder="Any"
                  value={filters.min_bedrooms || ''}
                  onChange={(e) => handleFilterChange('min_bedrooms', e.target.value ? parseInt(e.target.value) : undefined)}
                  min="0"
                />
              </div>
              <div>
                <Label htmlFor="max_bedrooms" className="text-xs text-muted-foreground">
                  Maximum
                </Label>
                <Input
                  id="max_bedrooms"
                  type="number"
                  placeholder="Any"
                  value={filters.max_bedrooms || ''}
                  onChange={(e) => handleFilterChange('max_bedrooms', e.target.value ? parseInt(e.target.value) : undefined)}
                  min="0"
                />
              </div>
            </div>
          </div>

          {/* Bathrooms */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Bathrooms</Label>
              {(filters.min_bathrooms || filters.max_bathrooms) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    handleFilterChange('min_bathrooms', undefined);
                    handleFilterChange('max_bathrooms', undefined);
                  }}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="min_bathrooms" className="text-xs text-muted-foreground">
                  Minimum
                </Label>
                <Input
                  id="min_bathrooms"
                  type="number"
                  step="0.5"
                  placeholder="Any"
                  value={filters.min_bathrooms || ''}
                  onChange={(e) => handleFilterChange('min_bathrooms', e.target.value ? parseFloat(e.target.value) : undefined)}
                  min="0"
                />
              </div>
              <div>
                <Label htmlFor="max_bathrooms" className="text-xs text-muted-foreground">
                  Maximum
                </Label>
                <Input
                  id="max_bathrooms"
                  type="number"
                  step="0.5"
                  placeholder="Any"
                  value={filters.max_bathrooms || ''}
                  onChange={(e) => handleFilterChange('max_bathrooms', e.target.value ? parseFloat(e.target.value) : undefined)}
                  min="0"
                />
              </div>
            </div>
          </div>

          {/* Location */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="location">Location</Label>
              {filters.location && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFilterChange('location', undefined)}
                  className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
            <Input
              id="location"
              placeholder="Search city, neighborhood, or address..."
              value={filters.location || ''}
              onChange={(e) => handleFilterChange('location', e.target.value || undefined)}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                onClear();
                setOpen(false);
              }}
            >
              Clear All
            </Button>
            <Button
              variant="accent"
              className="flex-1"
              onClick={() => setOpen(false)}
            >
              Apply Filters
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
