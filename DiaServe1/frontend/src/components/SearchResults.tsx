/**
 * SearchResults Component
 *
 * Displays property search results with match scoring and reasons.
 */

import { useState } from "react";
import {
  MapPin,
  Bed,
  Bath,
  Square,
  DollarSign,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import type { SearchResponse, PropertyMatch } from "../lib/api/search-api";

interface SearchResultsProps {
  results: SearchResponse;
  onPropertyClick?: (propertyId: string) => void;
}

export function SearchResults({ results, onPropertyClick }: SearchResultsProps) {
  const [selectedProperty, setSelectedProperty] = useState<string | null>(null);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-blue-600";
    if (score >= 0.4) return "text-yellow-600";
    return "text-gray-600";
  };

  const getRelevanceLabel = (score: number) => {
    if (score >= 0.8) return "Excellent Match";
    if (score >= 0.6) return "Good Match";
    if (score >= 0.4) return "Fair Match";
    return "Partial Match";
  };

  const handlePropertyClick = (propertyId: string) => {
    setSelectedProperty(propertyId);
    onPropertyClick?.(propertyId);
  };

  if (!results || results.matches.length === 0) {
    return (
      <Card>
        <CardContent className="pt-12 pb-12 text-center">
          <div className="text-gray-400 mb-4">
            <Sparkles className="h-16 w-16 mx-auto opacity-20" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
          <p className="text-gray-500 mb-6">
            Try adjusting your search criteria or use different keywords
          </p>

          {/* Search Suggestions */}
          {results.suggested_refinements.length > 0 && (
            <div className="max-w-md mx-auto">
              <p className="text-sm font-medium text-gray-700 mb-2">Suggestions:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                {results.suggested_refinements.map((suggestion, index) => (
                  <li key={index}>• {suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Alternative Locations */}
          {results.alternative_locations.length > 0 && (
            <div className="mt-6">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Try searching in these areas:
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {results.alternative_locations.map((location, index) => (
                  <Badge key={index} variant="outline">
                    {location}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Parsed Query Info */}
      {results.parsed_query && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-blue-900 mb-2">
                  AI understood your search as:
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">
                      Intent: {results.parsed_query.intent}
                    </Badge>
                    {results.parsed_query.property_types.length > 0 && (
                      <Badge variant="secondary">
                        Types: {results.parsed_query.property_types.join(", ")}
                      </Badge>
                    )}
                    {results.parsed_query.locations.length > 0 && (
                      <Badge variant="secondary">
                        Locations: {results.parsed_query.locations.join(", ")}
                      </Badge>
                    )}
                    {results.parsed_query.min_bedrooms && (
                      <Badge variant="secondary">
                        {results.parsed_query.min_bedrooms}+ bedrooms
                      </Badge>
                    )}
                    {results.parsed_query.max_price && (
                      <Badge variant="secondary">
                        Under {formatPrice(results.parsed_query.max_price)}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Grid */}
      <div className="grid grid-cols-1 gap-4">
        {results.matches.map((match: PropertyMatch) => {
          const property = match.property_data;
          const isSelected = selectedProperty === match.property_id;

          return (
            <Card
              key={match.property_id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isSelected ? "ring-2 ring-blue-500" : ""
              }`}
              onClick={() => handlePropertyClick(match.property_id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="flex items-center gap-2">
                      {property.name}
                      <Badge variant="outline">{property.property_type}</Badge>
                    </CardTitle>
                    <CardDescription className="flex items-center gap-1 mt-1">
                      <MapPin className="h-3 w-3" />
                      {property.location?.city}, {property.location?.neighborhood}
                    </CardDescription>
                  </div>

                  {/* Relevance Score */}
                  <div className="text-right">
                    <div
                      className={`text-lg font-bold ${getRelevanceColor(
                        match.relevance_score
                      )}`}
                    >
                      {Math.round(match.relevance_score * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {getRelevanceLabel(match.relevance_score)}
                    </div>
                  </div>
                </div>

                {/* Match Progress Bar */}
                <div className="mt-2">
                  <Progress value={match.relevance_score * 100} className="h-2" />
                </div>
              </CardHeader>

              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {/* Property Details */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Bed className="h-4 w-4 text-gray-400" />
                        <span>
                          {property.features?.bedrooms || 0} beds
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Bath className="h-4 w-4 text-gray-400" />
                        <span>
                          {property.features?.bathrooms || 0} baths
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Square className="h-4 w-4 text-gray-400" />
                        <span>
                          {property.features?.sqft?.toLocaleString() || 0} sqft
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-lg font-bold text-blue-600">
                      <DollarSign className="h-5 w-5" />
                      {formatPrice(property.financial?.price_usd || 0)}
                    </div>

                    {property.description && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {property.description}
                      </p>
                    )}
                  </div>

                  {/* Match Information */}
                  <div className="space-y-2">
                    {/* Match Reasons */}
                    {match.match_reasons.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1 text-xs font-medium text-green-700 mb-1">
                          <CheckCircle className="h-3 w-3" />
                          Why this matches:
                        </div>
                        <ul className="text-xs text-gray-600 space-y-0.5">
                          {match.match_reasons.map((reason, index) => (
                            <li key={index}>• {reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Missing Criteria */}
                    {match.missing_criteria.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1 text-xs font-medium text-yellow-700 mb-1">
                          <AlertCircle className="h-3 w-3" />
                          Note:
                        </div>
                        <ul className="text-xs text-gray-600 space-y-0.5">
                          {match.missing_criteria.map((criteria, index) => (
                            <li key={index}>• {criteria}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Semantic Score */}
                    {match.semantic_score !== undefined && (
                      <div className="flex items-center gap-1 text-xs text-purple-600">
                        <TrendingUp className="h-3 w-3" />
                        Semantic match: {Math.round(match.semantic_score * 100)}%
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t">
                  <Button variant="outline" size="sm" className="w-full">
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Pagination Info */}
      {results.total > results.limit && (
        <div className="text-center text-sm text-gray-500">
          Showing {results.matches.length} of {results.total} properties
        </div>
      )}
    </div>
  );
}
