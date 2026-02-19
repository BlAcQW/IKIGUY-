import { useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Filter,
  X,
  Check,
  Calendar,
  Star,
  Users,
  Sparkles,
  TrendingUp,
  Shield
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

export interface AdvancedFilters {
  // Content Type Filters
  contentTypes: string[];

  // Language Filters
  languages: string[];
  languageFamilies: string[];

  // Quality Filters
  minQualityScore?: number;
  qualityTiers: string[];  // gold, community, submitted
  verifiedOnly: boolean;

  // Date Filters
  dateFrom?: string;
  dateTo?: string;
  datePreset?: 'today' | 'week' | 'month' | 'year' | 'custom';

  // User/Community Filters
  contributorLevel?: string;  // newcomer, contributor, validator, expert, guardian
  minContributions?: number;
  expertValidatedOnly: boolean;

  // Model/Dataset Specific
  modelTypes?: string[];  // tts, asr, translation
  datasetFormats?: string[];  // audio, text, parallel
  minDownloads?: number;

  // Status Filters
  status?: string[];  // active, completed, pending

  // Sort Options
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface AdvancedFiltersPanelProps {
  filters: AdvancedFilters;
  onFiltersChange: (filters: AdvancedFilters) => void;
  onApply: () => void;
  onReset: () => void;
}

const CONTENT_TYPES = [
  { value: 'audio', label: 'Audio Submissions' },
  { value: 'text', label: 'Text Content' },
  { value: 'model', label: 'ML Models' },
  { value: 'dataset', label: 'Datasets' },
  { value: 'resource', label: 'External Resources' },
  { value: 'user', label: 'Users' }
];

const LANGUAGE_FAMILIES = [
  'Niger-Congo',
  'Afroasiatic',
  'Nilo-Saharan',
  'Khoisan'
];

const QUALITY_TIERS = [
  { value: 'tier-1-validated', label: 'Gold Standard', icon: Star },
  { value: 'tier-2-reviewed', label: 'Community Reviewed', icon: Users },
  { value: 'tier-3-submitted', label: 'Submitted', icon: Sparkles }
];

const CONTRIBUTOR_LEVELS = [
  { value: 'guardian', label: 'Guardian', icon: Shield },
  { value: 'expert', label: 'Expert', icon: Star },
  { value: 'validator', label: 'Validator', icon: Check },
  { value: 'contributor', label: 'Contributor', icon: Users },
  { value: 'newcomer', label: 'Newcomer', icon: Sparkles }
];

const MODEL_TYPES = [
  { value: 'tts', label: 'Text-to-Speech' },
  { value: 'asr', label: 'Speech Recognition' },
  { value: 'translation', label: 'Translation' },
  { value: 'classification', label: 'Classification' }
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'popular', label: 'Most Popular' },
  { value: 'quality', label: 'Highest Quality' },
  { value: 'downloads', label: 'Most Downloads' }
];

export function AdvancedFiltersPanel({
  filters,
  onFiltersChange,
  onApply,
  onReset
}: AdvancedFiltersPanelProps) {
  const [open, setOpen] = useState(false);

  const toggleContentType = (type: string) => {
    const updated = filters.contentTypes.includes(type)
      ? filters.contentTypes.filter(t => t !== type)
      : [...filters.contentTypes, type];
    onFiltersChange({ ...filters, contentTypes: updated });
  };

  const toggleLanguageFamily = (family: string) => {
    const updated = filters.languageFamilies.includes(family)
      ? filters.languageFamilies.filter(f => f !== family)
      : [...filters.languageFamilies, family];
    onFiltersChange({ ...filters, languageFamilies: updated });
  };

  const toggleQualityTier = (tier: string) => {
    const updated = filters.qualityTiers.includes(tier)
      ? filters.qualityTiers.filter(t => t !== tier)
      : [...filters.qualityTiers, tier];
    onFiltersChange({ ...filters, qualityTiers: updated });
  };

  const toggleModelType = (type: string) => {
    const current = filters.modelTypes || [];
    const updated = current.includes(type)
      ? current.filter(t => t !== type)
      : [...current, type];
    onFiltersChange({ ...filters, modelTypes: updated });
  };

  const activeFiltersCount = [
    filters.contentTypes.length > 0,
    filters.languageFamilies.length > 0,
    filters.qualityTiers.length > 0,
    filters.minQualityScore !== undefined,
    filters.verifiedOnly,
    filters.dateFrom || filters.dateTo,
    filters.contributorLevel,
    filters.expertValidatedOnly,
    (filters.modelTypes?.length || 0) > 0,
    filters.minDownloads !== undefined
  ].filter(Boolean).length;

  const handleApply = () => {
    onApply();
    setOpen(false);
  };

  const handleReset = () => {
    onReset();
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" />
          Advanced Filters
          {activeFiltersCount > 0 && (
            <Badge variant="secondary" className="ml-1 h-5 w-5 rounded-full p-0 flex items-center justify-center">
              {activeFiltersCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-xl">
        <SheetHeader>
          <SheetTitle>Advanced Filters</SheetTitle>
          <SheetDescription>
            Refine your search with detailed filtering options
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-180px)] pr-4">
          <div className="space-y-6 py-6">
            {/* Content Type Filter */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Content Type</Label>
              <div className="grid grid-cols-2 gap-2">
                {CONTENT_TYPES.map(({ value, label }) => (
                  <div key={value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`type-${value}`}
                      checked={filters.contentTypes.includes(value)}
                      onCheckedChange={() => toggleContentType(value)}
                    />
                    <Label
                      htmlFor={`type-${value}`}
                      className="text-sm font-normal cursor-pointer"
                    >
                      {label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Language Family Filter */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Language Family</Label>
              <div className="space-y-2">
                {LANGUAGE_FAMILIES.map(family => (
                  <div key={family} className="flex items-center space-x-2">
                    <Checkbox
                      id={`family-${family}`}
                      checked={filters.languageFamilies.includes(family)}
                      onCheckedChange={() => toggleLanguageFamily(family)}
                    />
                    <Label
                      htmlFor={`family-${family}`}
                      className="text-sm font-normal cursor-pointer"
                    >
                      {family}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Quality Filters */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Quality & Validation</Label>

              <div className="space-y-3">
                {/* Quality Tiers */}
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Quality Tiers</Label>
                  {QUALITY_TIERS.map(({ value, label, icon: Icon }) => (
                    <div key={value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`tier-${value}`}
                        checked={filters.qualityTiers.includes(value)}
                        onCheckedChange={() => toggleQualityTier(value)}
                      />
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      <Label
                        htmlFor={`tier-${value}`}
                        className="text-sm font-normal cursor-pointer flex-1"
                      >
                        {label}
                      </Label>
                    </div>
                  ))}
                </div>

                {/* Min Quality Score */}
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">
                    Minimum Quality Score: {filters.minQualityScore || 0}/10
                  </Label>
                  <Slider
                    value={[filters.minQualityScore || 0]}
                    onValueChange={([value]) =>
                      onFiltersChange({ ...filters, minQualityScore: value })
                    }
                    max={10}
                    step={0.5}
                    className="w-full"
                  />
                </div>

                {/* Verified Only */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="verified-only"
                    checked={filters.verifiedOnly}
                    onCheckedChange={(checked) =>
                      onFiltersChange({ ...filters, verifiedOnly: checked as boolean })
                    }
                  />
                  <Label htmlFor="verified-only" className="text-sm font-normal cursor-pointer">
                    Verified content only
                  </Label>
                </div>

                {/* Expert Validated Only */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="expert-validated"
                    checked={filters.expertValidatedOnly}
                    onCheckedChange={(checked) =>
                      onFiltersChange({ ...filters, expertValidatedOnly: checked as boolean })
                    }
                  />
                  <Label htmlFor="expert-validated" className="text-sm font-normal cursor-pointer">
                    Expert validated only
                  </Label>
                </div>
              </div>
            </div>

            <Separator />

            {/* Date Filters */}
            <div className="space-y-3">
              <Label className="text-base font-semibold flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Date Range
              </Label>

              <Select
                value={filters.datePreset}
                onValueChange={(value) =>
                  onFiltersChange({ ...filters, datePreset: value as any })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select date range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">Past Week</SelectItem>
                  <SelectItem value="month">Past Month</SelectItem>
                  <SelectItem value="year">Past Year</SelectItem>
                  <SelectItem value="custom">Custom Range</SelectItem>
                </SelectContent>
              </Select>

              {filters.datePreset === 'custom' && (
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">From</Label>
                    <Input
                      type="date"
                      value={filters.dateFrom || ''}
                      onChange={(e) =>
                        onFiltersChange({ ...filters, dateFrom: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">To</Label>
                    <Input
                      type="date"
                      value={filters.dateTo || ''}
                      onChange={(e) =>
                        onFiltersChange({ ...filters, dateTo: e.target.value })
                      }
                    />
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Contributor Level Filter */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Contributor Level</Label>
              <Select
                value={filters.contributorLevel}
                onValueChange={(value) =>
                  onFiltersChange({ ...filters, contributorLevel: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any Level</SelectItem>
                  {CONTRIBUTOR_LEVELS.map(({ value, label, icon: Icon }) => (
                    <SelectItem key={value} value={value}>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4" />
                        {label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">
                  Minimum Contributions: {filters.minContributions || 0}
                </Label>
                <Slider
                  value={[filters.minContributions || 0]}
                  onValueChange={([value]) =>
                    onFiltersChange({ ...filters, minContributions: value })
                  }
                  max={100}
                  step={5}
                  className="w-full"
                />
              </div>
            </div>

            <Separator />

            {/* Model/Dataset Specific Filters */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Model Types</Label>
              <div className="grid grid-cols-2 gap-2">
                {MODEL_TYPES.map(({ value, label }) => (
                  <div key={value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`model-${value}`}
                      checked={(filters.modelTypes || []).includes(value)}
                      onCheckedChange={() => toggleModelType(value)}
                    />
                    <Label
                      htmlFor={`model-${value}`}
                      className="text-sm font-normal cursor-pointer"
                    >
                      {label}
                    </Label>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">
                  Minimum Downloads: {filters.minDownloads || 0}
                </Label>
                <Slider
                  value={[filters.minDownloads || 0]}
                  onValueChange={([value]) =>
                    onFiltersChange({ ...filters, minDownloads: value })
                  }
                  max={1000}
                  step={50}
                  className="w-full"
                />
              </div>
            </div>

            <Separator />

            {/* Sort Options */}
            <div className="space-y-3">
              <Label className="text-base font-semibold flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Sort Results
              </Label>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">Sort By</Label>
                  <Select
                    value={filters.sortBy}
                    onValueChange={(value) =>
                      onFiltersChange({ ...filters, sortBy: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SORT_OPTIONS.map(({ value, label }) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Order</Label>
                  <Select
                    value={filters.sortOrder}
                    onValueChange={(value: any) =>
                      onFiltersChange({ ...filters, sortOrder: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="desc">Descending</SelectItem>
                      <SelectItem value="asc">Ascending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        <div className="absolute bottom-0 left-0 right-0 border-t bg-background p-4 space-y-2">
          <div className="flex gap-2">
            <Button onClick={handleApply} className="flex-1">
              <Check className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
            <Button onClick={handleReset} variant="outline">
              <X className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </div>
          {activeFiltersCount > 0 && (
            <p className="text-xs text-center text-muted-foreground">
              {activeFiltersCount} filter{activeFiltersCount > 1 ? 's' : ''} active
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
