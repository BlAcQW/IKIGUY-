/**
 * VoiceFilters Component
 *
 * Filter controls for voice library browsing.
 * Allows filtering by gender, language, accent, categories, and other attributes.
 *
 * Usage:
 * ```tsx
 * import { VoiceFilters } from '@/components/voice-library/VoiceFilters';
 *
 * <VoiceFilters
 *   filters={currentFilters}
 *   onChange={(newFilters) => setFilters(newFilters)}
 *   showSearch={true}
 * />
 * ```
 */

import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Search, X, Filter, Star } from 'lucide-react';

interface VoiceFiltersData {
  search?: string;
  gender?: string;
  language?: string;
  accent?: string;
  dialect?: string;
  categories?: string[];
  tags?: string[];
  featured?: boolean;
  verified?: boolean;
  visibility?: string;
  minRating?: number;
}

interface VoiceFiltersProps {
  filters: VoiceFiltersData;
  onChange: (filters: VoiceFiltersData) => void;
  showSearch?: boolean;
  showAdvanced?: boolean;
  compact?: boolean;
  className?: string;
}

export const VoiceFilters: React.FC<VoiceFiltersProps> = ({
  filters,
  onChange,
  showSearch = true,
  showAdvanced = false,
  compact = false,
  className = '',
}) => {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(showAdvanced);

  const genderOptions = [
    { value: '', label: 'All Genders' },
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'neutral', label: 'Neutral' },
  ];

  const languageOptions = [
    { value: '', label: 'All Languages' },
    { value: 'en', label: 'English' },
    { value: 'tw', label: 'Twi' },
    { value: 'ak', label: 'Akan' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' },
    { value: 'de', label: 'German' },
  ];

  const accentOptions = [
    { value: '', label: 'All Accents' },
    { value: 'American', label: 'American' },
    { value: 'British', label: 'British' },
    { value: 'Ghanaian', label: 'Ghanaian' },
    { value: 'Nigerian', label: 'Nigerian' },
    { value: 'General', label: 'General' },
  ];

  const categoryOptions = [
    'Narration',
    'Conversational',
    'Professional',
    'Casual',
    'Education',
    'Customer Service',
    'IVR',
    'Audiobook',
  ];

  const handleFilterChange = (key: keyof VoiceFiltersData, value: any) => {
    onChange({
      ...filters,
      [key]: value,
    });
  };

  const handleCategoryToggle = (category: string) => {
    const currentCategories = filters.categories || [];
    const newCategories = currentCategories.includes(category)
      ? currentCategories.filter(c => c !== category)
      : [...currentCategories, category];

    handleFilterChange('categories', newCategories.length > 0 ? newCategories : undefined);
  };

  const clearFilters = () => {
    onChange({});
  };

  const hasActiveFilters = Object.keys(filters).some(
    key => filters[key as keyof VoiceFiltersData] !== undefined && filters[key as keyof VoiceFiltersData] !== ''
  );

  if (compact) {
    return (
      <div className={`flex items-center gap-2 flex-wrap ${className}`}>
        {showSearch && (
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search voices..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-8"
            />
          </div>
        )}

        <Select value={filters.gender || ''} onValueChange={(v) => handleFilterChange('gender', v || undefined)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Gender" />
          </SelectTrigger>
          <SelectContent>
            {genderOptions.map(opt => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filters.language || ''} onValueChange={(v) => handleFilterChange('language', v || undefined)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            {languageOptions.map(opt => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
        >
          <Filter className="h-4 w-4 mr-1" />
          {showAdvancedFilters ? 'Less' : 'More'}
        </Button>
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear All
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {showSearch && (
          <div className="space-y-2">
            <Label htmlFor="search">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search by name or description..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="gender">Gender</Label>
            <Select value={filters.gender || ''} onValueChange={(v) => handleFilterChange('gender', v || undefined)}>
              <SelectTrigger id="gender">
                <SelectValue placeholder="All Genders" />
              </SelectTrigger>
              <SelectContent>
                {genderOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select value={filters.language || ''} onValueChange={(v) => handleFilterChange('language', v || undefined)}>
              <SelectTrigger id="language">
                <SelectValue placeholder="All Languages" />
              </SelectTrigger>
              <SelectContent>
                {languageOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {(showAdvanced || showAdvancedFilters) && (
          <>
            <Separator />

            <div className="space-y-2">
              <Label htmlFor="accent">Accent</Label>
              <Select value={filters.accent || ''} onValueChange={(v) => handleFilterChange('accent', v || undefined)}>
                <SelectTrigger id="accent">
                  <SelectValue placeholder="All Accents" />
                </SelectTrigger>
                <SelectContent>
                  {accentOptions.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Categories</Label>
              <div className="flex flex-wrap gap-2">
                {categoryOptions.map(category => (
                  <Badge
                    key={category}
                    variant={filters.categories?.includes(category) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => handleCategoryToggle(category)}
                  >
                    {category}
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="featured"
                  checked={filters.featured || false}
                  onCheckedChange={(checked) => handleFilterChange('featured', checked || undefined)}
                />
                <Label htmlFor="featured" className="flex items-center gap-1 cursor-pointer">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  Featured voices only
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="verified"
                  checked={filters.verified || false}
                  onCheckedChange={(checked) => handleFilterChange('verified', checked || undefined)}
                />
                <Label htmlFor="verified" className="cursor-pointer">
                  Verified voices only
                </Label>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="visibility">Visibility</Label>
              <Select
                value={filters.visibility || ''}
                onValueChange={(v) => handleFilterChange('visibility', v || undefined)}
              >
                <SelectTrigger id="visibility">
                  <SelectValue placeholder="All Voices" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Voices</SelectItem>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="organization">Organization</SelectItem>
                  <SelectItem value="private">Private</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )}

        {!showAdvanced && !compact && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          >
            {showAdvancedFilters ? 'Show Less Filters' : 'Show More Filters'}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default VoiceFilters;
