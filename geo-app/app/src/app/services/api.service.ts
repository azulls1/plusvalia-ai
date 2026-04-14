// src/app/services/api.service.ts - Facade que delega a servicios especializados
// Mantiene compatibilidad hacia atras para todos los componentes existentes.
import { Injectable } from '@angular/core';
import { LoggerService } from './logger.service';
import { CacheService } from './cache.service';
import { SupabaseService } from './supabase.service';
import { MlApiService } from './ml-api.service';
import { N8nService } from './n8n.service';
import type { Tile, Amenity, AmenityFilters } from '../models/interfaces';

// Re-export response interfaces so existing consumers keep working
export interface HeatmapResponse {
  points: [number, number, number][];
  count: number;
  filters: { city?: string; min_score?: number };
}

export interface NearbyResponse {
  predictions: {
    id?: number;
    lat: number;
    lon: number;
    city: string;
    state: string;
    predicted_price_m2: number;
    plusvalia_score: number;
    growth_potential: string;
    distance_km?: number;
    created_at?: string;
  }[];
  count: number;
  center: { lat: number; lon: number };
  radius_km: number;
}

export interface CityStats {
  city: string;
  state: string;
  predictions_count: number;
  avg_price_m2: number;
  min_price_m2: number;
  max_price_m2: number;
  avg_plusvalia_score: number;
  potential_distribution: { alto: number; medio: number; bajo: number };
}

export interface StatsResponse {
  cities: CityStats[];
  total_predictions: number;
  cities_count: number;
}

export interface MLPredictionResponse {
  predicted_price_m2: number;
  predicted_total_price: number;
  plusvalia_score: number;
  growth_potential: string;
  confidence: number;
  model_version: string;
  features_used: Record<string, unknown>;
  prediction_id?: number;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // Expose reactive state from SupabaseService for components that need it
  public readonly loading$ = this.supabaseService.loading$;
  public readonly error$ = this.supabaseService.error$;

  constructor(
    private supabaseService: SupabaseService,
    private mlApiService: MlApiService,
    private n8nService: N8nService,
    private cacheService: CacheService,
    private logger: LoggerService
  ) {}

  // ==================== SUPABASE DELEGATES ====================

  getTiles(limit: number = 1000, offset: number = 0): Promise<Tile[]> {
    return this.supabaseService.getTiles(limit, offset);
  }

  getAmenities(filters: AmenityFilters = {}): Promise<Amenity[]> {
    return this.supabaseService.getAmenities(filters);
  }

  // ==================== ML API DELEGATES ====================

  getPredictionsHeatmap(city?: string, minScore?: number, limit?: number): Promise<HeatmapResponse> {
    return this.mlApiService.getPredictionsHeatmap(city, minScore, limit);
  }

  getStatsByState(): Promise<{ states: Record<string, { avg_score: number; count: number; avg_price_m2: number }> }> {
    return this.mlApiService.getStatsByState();
  }

  getPredictionsNearby(
    lat: number, lon: number, radiusKm?: number, limit?: number
  ): Promise<NearbyResponse> {
    return this.mlApiService.getPredictionsNearby(lat, lon, radiusKm, limit);
  }

  getPredictionsStatsByCity(): Promise<StatsResponse> {
    return this.mlApiService.getPredictionsStatsByCity();
  }

  // ==================== N8N DELEGATES ====================

  uploadComparablesCsv(file: File): Promise<Record<string, unknown>> {
    return this.n8nService.uploadComparablesCsv(file);
  }

  fetchOsmAmenities(city: string, state: string, types: string[]): Promise<Record<string, unknown>> {
    return this.n8nService.fetchOsmAmenities(city, state, types);
  }

  rebuildGrid(step?: number): Promise<Record<string, unknown>> {
    return this.n8nService.rebuildGrid(step);
  }

  // ==================== CACHE DELEGATE ====================

  clearCache(pattern?: string): void {
    this.cacheService.clearCache(pattern);
  }
}
