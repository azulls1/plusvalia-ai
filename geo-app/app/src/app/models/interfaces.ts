/**
 * Shared interfaces for the geo-app application.
 * These model the data structures returned by the API and used across components.
 */

/** A single ML prediction point as returned by the heatmap endpoint: [lat, lon, intensity] */
export type HeatmapPoint = [number, number, number];

/** Full prediction record from the iainmobiliaria_predictions table */
export interface Prediction {
  id?: number;
  lat: number;
  lon: number;
  price_m2_predicted: number;
  plusvalia_score: number;
  city: string;
  state: string;
  potential_level: string;
  prediction_date?: string;
}

/** Nearby prediction returned by /predictions/nearby */
export interface NearbyPrediction {
  lat: number;
  lon: number;
  predicted_price_m2: number;
  plusvalia_score: number;
  city: string;
  growth_potential: string;
  distance_km: number;
}

/** City-level statistics returned by /predictions/stats-by-city */
export interface CityStats {
  city: string;
  predictions_count: number;
  avg_price_m2: number;
  avg_plusvalia_score: number;
  min_price_m2: number;
  max_price_m2: number;
  potential_distribution: PotentialDistribution;
}

export interface PotentialDistribution {
  alto: number;
  medio: number;
  bajo: number;
}

/** Grid tile from iainmobiliaria_grid_tiles */
export interface Tile {
  id?: number;
  lat: number;
  lon: number;
  price_m2_avg: number;
  city?: string;
  state?: string;
}

/** Amenity from iainmobiliaria_amenities */
export interface Amenity {
  id?: number;
  name: string;
  amenity_type: string;
  lat: number;
  lon: number;
  city: string;
  state?: string;
}

/** Nominatim geocoding search result */
export interface SearchResult {
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  address: Record<string, string>;
}

/** Chat message used in the AI chatbot component */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/** Amenity type option used in the filters panel */
export interface AmenityTypeOption {
  label: string;
  value: string;
  checked: boolean;
}

/** Filters emitted by the filters panel */
export interface AmenityFilters {
  types?: string[];
  city?: string;
  state?: string;
  priceMin?: number;
  priceMax?: number;
}

/** Advanced filters for predictions */
export interface AdvancedFilters {
  scoreMin: number;
  scoreMax: number;
  priceMin: number;
  priceMax: number;
  potentialLevels: string[];
  selectedState: string;
  sortBy: 'score' | 'price' | 'city';
  sortOrder: 'asc' | 'desc';
}

/** Top opportunity computed from heatmap data */
export interface TopOpportunity {
  rank: number;
  lat: number;
  lon: number;
  score: number;
}

/** Price distribution bucket for the stats dashboard histogram */
export interface PriceDistributionBucket {
  range: string;
  count: number;
  percentage: number;
}

/** Potential distribution category for the stats dashboard */
export interface PotentialDistributionCategory {
  label: string;
  count: number;
  percentage: number;
  color: string;
}
