import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, X, Filter } from 'lucide-react';

interface NotebookFiltersProps {
  filters: {
    query?: string;
    category?: string;
    difficulty?: string;
    language_codes?: string[];
    tags?: string[];
    sort_by?: string;
    sort_order?: string;
  };
  onFiltersChange: (filters: any) => void;
  availableLanguages?: string[];
  availableTags?: string[];
}

const categories = [
  { value: 'data_acquisition', label: 'Data Acquisition' },
  { value: 'data_processing', label: 'Data Processing' },
  { value: 'asr_training', label: 'ASR Training' },
  { value: 'tts_training', label: 'TTS Training' },
  { value: 'llm_training', label: 'LLM Training' },
  { value: 'evaluation', label: 'Evaluation' },
  { value: 'deployment', label: 'Deployment' },
  { value: 'research', label: 'Research' },
  { value: 'tutorial', label: 'Tutorial' },
  { value: 'other', label: 'Other' }
];

const difficulties = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' }
];

const sortOptions = [
  { value: 'updated_at', label: 'Recently Updated' },
  { value: 'created_at', label: 'Recently Created' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'upvotes', label: 'Most Upvoted' },
  { value: 'downloads', label: 'Most Downloaded' }
];

export const NotebookFilters: React.FC<NotebookFiltersProps> = ({
  filters,
  onFiltersChange,
  availableLanguages = [],
  availableTags = []
}) => {
  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value
    });
  };

  const handleLanguageToggle = (language: string) => {
    const currentLanguages = filters.language_codes || [];
    const newLanguages = currentLanguages.includes(language)
      ? currentLanguages.filter(l => l !== language)
      : [...currentLanguages, language];

    handleFilterChange('language_codes', newLanguages);
  };

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag];

    handleFilterChange('tags', newTags);
  };

  const clearFilters = () => {
    onFiltersChange({
      query: '',
      category: '',
      difficulty: '',
      language_codes: [],
      tags: [],
      sort_by: 'updated_at',
      sort_order: 'desc'
    });
  };

  const hasActiveFilters = filters.query || filters.category || filters.difficulty ||
    (filters.language_codes && filters.language_codes.length > 0) ||
    (filters.tags && filters.tags.length > 0);

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
          {hasActiveFilters && (
            <Button variant="outline" size="sm" onClick={clearFilters}>
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Search */}
        <div className="space-y-2">
          <Label htmlFor="search">Search Notebooks</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              id="search"
              placeholder="Search by title, description, or author..."
              value={filters.query || ''}
              onChange={(e) => handleFilterChange('query', e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Category */}
        <div className="space-y-2">
          <Label>Category</Label>
          <Select
            value={filters.category || ''}
            onValueChange={(value) => handleFilterChange('category', value === 'all' ? '' : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {categories.map((category) => (
                <SelectItem key={category.value} value={category.value}>
                  {category.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Difficulty */}
        <div className="space-y-2">
          <Label>Difficulty</Label>
          <Select
            value={filters.difficulty || ''}
            onValueChange={(value) => handleFilterChange('difficulty', value === 'all' ? '' : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All difficulties" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All difficulties</SelectItem>
              {difficulties.map((difficulty) => (
                <SelectItem key={difficulty.value} value={difficulty.value}>
                  {difficulty.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Languages */}
        {availableLanguages.length > 0 && (
          <div className="space-y-2">
            <Label>Languages</Label>
            <div className="flex flex-wrap gap-2">
              {availableLanguages.slice(0, 10).map((language) => (
                <Badge
                  key={language}
                  variant={filters.language_codes?.includes(language) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => handleLanguageToggle(language)}
                >
                  {language.toUpperCase()}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {availableTags.length > 0 && (
          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex flex-wrap gap-2">
              {availableTags.slice(0, 15).map((tag) => (
                <Badge
                  key={tag}
                  variant={filters.tags?.includes(tag) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => handleTagToggle(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Sort */}
        <div className="space-y-2">
          <Label>Sort By</Label>
          <div className="flex gap-2">
            <Select
              value={filters.sort_by || 'updated_at'}
              onValueChange={(value) => handleFilterChange('sort_by', value)}
            >
              <SelectTrigger className="flex-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {sortOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.sort_order || 'desc'}
              onValueChange={(value) => handleFilterChange('sort_order', value)}
            >
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="desc">↓</SelectItem>
                <SelectItem value="asc">↑</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};