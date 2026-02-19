/**
 * PropertySearchBar Component
 *
 * AI-powered natural language search for properties.
 */

import { useState, useRef, useEffect } from "react";
import { Search, Sparkles, X, TrendingUp, Loader2 } from "lucide-react";
import { usePropertySearch, usePopularSearches } from "../hooks/use-search";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";

interface PropertySearchBarProps {
  onSearch?: (results: any) => void;
  onClear?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export function PropertySearchBar({
  onSearch,
  onClear,
  placeholder = "Search properties with natural language...",
  autoFocus = false,
}: PropertySearchBarProps) {
  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { searchWithQuery, results, isLoading, error } = usePropertySearch();
  const { data: popularSearches } = usePopularSearches(5);

  // Notify parent when results change
  useEffect(() => {
    if (results) {
      console.log('PropertySearchBar - Search results:', results);
      onSearch?.(results);
    }
  }, [results, onSearch]);

  // Log errors for debugging
  useEffect(() => {
    if (error) {
      console.error('PropertySearchBar - Search error:', error);
    }
  }, [error]);

  const handleSearch = (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;

    searchWithQuery(finalQuery, {
      useSemanticSearch: true,
      currency: "USD",
    });

    setShowSuggestions(false);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    handleSearch(suggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  };

  const clearSearch = () => {
    setQuery("");
    inputRef.current?.focus();
    onClear?.(); // Notify parent that search was cleared
  };

  // Example queries for first-time users
  const exampleQueries = [
    "3 bedroom apartment in Accra with pool under $500k",
    "Pet-friendly house in East Legon",
    "Luxury villa with ocean view",
    "Investment properties with good rental yield",
    "Furnished apartment near airport",
  ];

  return (
    <div className="relative w-full">
      <Popover open={showSuggestions} onOpenChange={setShowSuggestions}>
        <PopoverTrigger asChild>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
              {isLoading ? (
                <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
              ) : (
                <Search className="h-5 w-5 text-gray-400" />
              )}
              <Sparkles className="h-4 w-4 text-purple-500" />
            </div>

            <Input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setShowSuggestions(true)}
              placeholder={placeholder}
              className="pl-16 pr-24 h-12 text-base"
              autoFocus={autoFocus}
              disabled={isLoading}
            />

            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
              {query && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearSearch}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}

              <Button
                onClick={() => handleSearch()}
                disabled={!query.trim() || isLoading}
                className="h-8"
                size="sm"
              >
                {isLoading ? "Searching..." : "Search"}
              </Button>
            </div>
          </div>
        </PopoverTrigger>

        <PopoverContent
          className="w-[600px] p-0"
          align="start"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <div className="p-4 space-y-4">
            {/* Popular Searches */}
            {popularSearches && popularSearches.popular_searches.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">
                    Popular Searches
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {popularSearches.popular_searches.map((search, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer hover:bg-gray-200"
                      onClick={() => handleSuggestionClick(search.query)}
                    >
                      {search.query}
                      <span className="ml-1 text-xs text-gray-500">
                        ({search.count})
                      </span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Example Queries */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-700">
                  Try asking...
                </span>
              </div>
              <div className="space-y-2">
                {exampleQueries.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(example)}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    "{example}"
                  </button>
                ))}
              </div>
            </div>

            {/* AI Note */}
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Powered by AI - Search naturally, like asking a friend
              </p>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Search Results Summary */}
      {results && (
        <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
          <span>
            Found <span className="font-medium">{results.total}</span> properties
          </span>
          <span className="text-gray-400">•</span>
          <span>
            Search took{" "}
            <span className="font-medium">{Math.round(results.search_time_ms)}ms</span>
          </span>
          {results.used_semantic_search && (
            <>
              <span className="text-gray-400">•</span>
              <Badge variant="secondary" className="text-xs">
                <Sparkles className="h-3 w-3 mr-1" />
                AI-powered
              </Badge>
            </>
          )}
        </div>
      )}
    </div>
  );
}
