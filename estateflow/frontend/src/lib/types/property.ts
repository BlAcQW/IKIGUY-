/**
 * Property type definitions matching backend models.
 */

export enum PropertyType {
  APARTMENT = "apartment",
  HOUSE = "house",
  VILLA = "villa",
  PENTHOUSE = "penthouse",
  LOFT = "loft",
  TOWNHOUSE = "townhouse",
  LAND = "land",
  COMMERCIAL = "commercial",
}

export enum PropertyStatus {
  ACTIVE = "active",
  PENDING = "pending",
  SOLD = "sold",
  RENTED = "rented",
  INACTIVE = "inactive",
}

export enum PetPolicy {
  ALLOWED = "allowed",
  NOT_ALLOWED = "not_allowed",
  CONDITIONAL = "conditional",
}

export interface Location {
  address: string;
  city: string;
  state?: string;
  zip_code?: string;
  country: string;
  latitude?: number;
  longitude?: number;
  neighborhood?: string;
}

export interface School {
  name: string;
  type: string;
  distance_km: number;
  rating?: number;
}

export interface Amenity {
  name: string;
  category: string;
  distance_km: number;
}

export interface NeighborhoodData {
  schools: School[];
  amenities: Amenity[];
  safety_rating?: number;
  walkability_score?: number;
  transit_score?: number;
}

export interface PropertyFeatures {
  bedrooms: number;
  bathrooms: number;
  sqft?: number;
  lot_size?: number;
  year_built?: number;
  parking_spaces: number;
  pool: boolean;
  garden: boolean;
  balcony: boolean;
  pet_policy: PetPolicy;
  pet_deposit?: number;
  furnished: boolean;
  elevator: boolean;
  air_conditioning: boolean;
  heating: boolean;
  fireplace: boolean;
  security_system: boolean;
  gym: boolean;
  storage: boolean;
}

export interface FinancialInfo {
  price_usd: number;
  base_currency: string;
  hoa_fees_monthly?: number;
  property_tax_annual?: number;
  insurance_estimate?: number;
}

export interface Property {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  property_type: PropertyType;
  status: PropertyStatus;
  location: Location;
  neighborhood_data: NeighborhoodData;
  features: PropertyFeatures;
  financial: FinancialInfo;
  images: string[];
  video_url?: string;
  virtual_tour_url?: string;
  agent_id?: string;
  agent_name?: string;
  created_at: string;
  updated_at: string;
  // Optional fields from currency conversion
  converted_price?: number;
  conversion_currency?: string;
  exchange_rate?: number;
}

export interface PropertyCreate {
  organization_id?: string;  // Optional - auto-filled from authenticated user
  name: string;
  description: string;
  property_type: PropertyType;
  status: PropertyStatus;
  location: Location;
  neighborhood_data: NeighborhoodData;
  features: PropertyFeatures;
  financial: FinancialInfo;
  images: string[];
  video_url?: string;
  virtual_tour_url?: string;
  agent_id?: string;
  agent_name?: string;
}

export interface PropertyUpdate {
  name?: string;
  description?: string;
  property_type?: PropertyType;
  status?: PropertyStatus;
  location?: Location;
  neighborhood_data?: NeighborhoodData;
  features?: PropertyFeatures;
  financial?: FinancialInfo;
  images?: string[];
  video_url?: string;
  virtual_tour_url?: string;
  agent_id?: string;
  agent_name?: string;
}

export interface PropertyListResponse {
  properties: Property[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PropertyFilters {
  property_type?: PropertyType[];
  status?: PropertyStatus[];
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  max_bathrooms?: number;
  city?: string;
  neighborhood?: string;
  location?: string;
  pet_policy?: PetPolicy[];
  has_pool?: boolean;
  has_garden?: boolean;
  furnished?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  currency?: string;
}

export interface PropertyStats {
  active: number;
  pending: number;
  sold: number;
  rented: number;
  inactive: number;
  total: number;
}

export interface Currency {
  code: string;
  name: string;
  symbol: string;
}

export interface ExchangeRates {
  base_currency: string;
  rates: Record<string, number>;
  last_updated: string;
  source: string;
}
