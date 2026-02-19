/**
 * Segment Builder Component
 *
 * Visual interface for building contact segment filters.
 * Used in campaign creation and standalone contact filtering.
 */

import { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { useSegmentPreview } from '@/hooks/use-campaigns';
import type { SegmentFilter, CampaignType } from '@/lib/api/campaign-api';

interface SegmentBuilderProps {
  value: SegmentFilter;
  onChange: (filter: SegmentFilter) => void;
  campaignType?: CampaignType;
  showPreview?: boolean;
}

const PROPERTY_TYPES = [
  'apartment',
  'house',
  'villa',
  'penthouse',
  'loft',
  'townhouse',
  'land',
  'commercial',
];

const INTEREST_STATUSES = ['hot', 'warm', 'cold', 'unqualified'];
const LEAD_STATUSES = ['new', 'contacted', 'qualified', 'negotiating', 'converted', 'lost'];

const LOCATIONS = [
  'Accra',
  'Kumasi',
  'Tema',
  'Takoradi',
  'Cape Coast',
  'Tamale',
  'East Legon',
  'Cantonments',
  'Airport Residential',
];

export function SegmentBuilder({
  value,
  onChange,
  campaignType,
  showPreview = true,
}: SegmentBuilderProps) {
  const [localFilter, setLocalFilter] = useState<SegmentFilter>(value);

  // Segment preview
  const { data: segmentPreview, isLoading: isPreviewLoading } = useSegmentPreview(
    localFilter,
    campaignType || 'sms',
    showPreview && !!campaignType
  );

  const updateFilter = (updates: Partial<SegmentFilter>) => {
    const newFilter = { ...localFilter, ...updates };
    setLocalFilter(newFilter);
    onChange(newFilter);
  };

  const toggleArrayItem = (field: keyof SegmentFilter, value: string) => {
    const currentArray = (localFilter[field] as string[]) || [];
    const newArray = currentArray.includes(value)
      ? currentArray.filter((item) => item !== value)
      : [...currentArray, value];
    updateFilter({ [field]: newArray.length > 0 ? newArray : undefined });
  };

  return (
    <div className="space-y-6">
      {/* Preview Card */}
      {showPreview && campaignType && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Segment Preview</CardTitle>
            <CardDescription>
              {isPreviewLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Calculating audience size...
                </div>
              ) : segmentPreview ? (
                <div className="space-y-1">
                  <div>
                    <span className="font-semibold text-lg text-gray-900">
                      {segmentPreview.contact_count}
                    </span>{' '}
                    <span className="text-gray-600">contacts match your criteria</span>
                  </div>
                  <div className="text-sm">
                    Estimated cost:{' '}
                    <span className="font-medium">GHS {segmentPreview.estimated_cost.toFixed(2)}</span>
                  </div>
                </div>
              ) : (
                'Add filters to see audience preview'
              )}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Property Types */}
      <div className="space-y-3">
        <Label>Property Type Preferences</Label>
        <div className="flex flex-wrap gap-2">
          {PROPERTY_TYPES.map((type) => {
            const isSelected = localFilter.property_types?.includes(type);
            return (
              <Badge
                key={type}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer capitalize"
                onClick={() => toggleArrayItem('property_types', type)}
              >
                {type}
              </Badge>
            );
          })}
        </div>
        {localFilter.property_types && localFilter.property_types.length > 0 && (
          <p className="text-xs text-gray-500">
            {localFilter.property_types.length} type(s) selected
          </p>
        )}
      </div>

      {/* Locations */}
      <div className="space-y-3">
        <Label>Location Preferences</Label>
        <div className="flex flex-wrap gap-2">
          {LOCATIONS.map((location) => {
            const isSelected = localFilter.locations?.includes(location);
            return (
              <Badge
                key={location}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleArrayItem('locations', location)}
              >
                {location}
              </Badge>
            );
          })}
        </div>
        {localFilter.locations && localFilter.locations.length > 0 && (
          <p className="text-xs text-gray-500">{localFilter.locations.length} location(s) selected</p>
        )}
      </div>

      {/* Budget Range */}
      <div className="space-y-3">
        <Label>Budget Range (GHS)</Label>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="budget-min" className="text-xs text-gray-500">
              Minimum
            </Label>
            <Input
              id="budget-min"
              type="number"
              placeholder="50,000"
              value={localFilter.budget_min || ''}
              onChange={(e) =>
                updateFilter({
                  budget_min: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="budget-max" className="text-xs text-gray-500">
              Maximum
            </Label>
            <Input
              id="budget-max"
              type="number"
              placeholder="500,000"
              value={localFilter.budget_max || ''}
              onChange={(e) =>
                updateFilter({
                  budget_max: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
            />
          </div>
        </div>
      </div>

      {/* Bedrooms Range */}
      <div className="space-y-3">
        <Label>Bedrooms</Label>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="bedrooms-min" className="text-xs text-gray-500">
              Minimum
            </Label>
            <Input
              id="bedrooms-min"
              type="number"
              min="0"
              placeholder="2"
              value={localFilter.bedrooms_min || ''}
              onChange={(e) =>
                updateFilter({
                  bedrooms_min: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="bedrooms-max" className="text-xs text-gray-500">
              Maximum
            </Label>
            <Input
              id="bedrooms-max"
              type="number"
              min="0"
              placeholder="5"
              value={localFilter.bedrooms_max || ''}
              onChange={(e) =>
                updateFilter({
                  bedrooms_max: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
        </div>
      </div>

      {/* Interest Status */}
      <div className="space-y-3">
        <Label>Interest Level</Label>
        <div className="flex flex-wrap gap-2">
          {INTEREST_STATUSES.map((status) => {
            const isSelected = localFilter.interest_statuses?.includes(status as any);
            return (
              <Badge
                key={status}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer capitalize"
                onClick={() => toggleArrayItem('interest_statuses', status)}
              >
                {status}
              </Badge>
            );
          })}
        </div>
        {localFilter.interest_statuses && localFilter.interest_statuses.length > 0 && (
          <p className="text-xs text-gray-500">
            {localFilter.interest_statuses.length} level(s) selected
          </p>
        )}
      </div>

      {/* Lead Status */}
      <div className="space-y-3">
        <Label>Lead Status</Label>
        <div className="flex flex-wrap gap-2">
          {LEAD_STATUSES.map((status) => {
            const isSelected = localFilter.lead_statuses?.includes(status as any);
            return (
              <Badge
                key={status}
                variant={isSelected ? 'default' : 'outline'}
                className="cursor-pointer capitalize"
                onClick={() => toggleArrayItem('lead_statuses', status)}
              >
                {status}
              </Badge>
            );
          })}
        </div>
        {localFilter.lead_statuses && localFilter.lead_statuses.length > 0 && (
          <p className="text-xs text-gray-500">{localFilter.lead_statuses.length} status(es) selected</p>
        )}
      </div>

      {/* Tags */}
      <div className="space-y-3">
        <Label htmlFor="tags-input">Tags</Label>
        <Input
          id="tags-input"
          placeholder="investor, first-time-buyer (comma-separated)"
          value={localFilter.tags?.join(', ') || ''}
          onChange={(e) => {
            const tags = e.target.value
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean);
            updateFilter({ tags: tags.length > 0 ? tags : undefined });
          }}
        />
        <p className="text-xs text-gray-500">
          Enter tags separated by commas. Contacts must have ALL tags to match.
        </p>
      </div>

      {/* Exclude Opted Out */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="exclude-opted-out"
          checked={localFilter.exclude_opted_out !== false}
          onChange={(e) => updateFilter({ exclude_opted_out: e.target.checked })}
          className="rounded"
        />
        <Label htmlFor="exclude-opted-out" className="cursor-pointer">
          Exclude contacts who opted out of this channel
        </Label>
      </div>
    </div>
  );
}
