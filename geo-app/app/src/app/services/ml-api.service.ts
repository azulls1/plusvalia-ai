// src/app/services/ml-api.service.ts - Servicio dedicado para llamadas a la API ML (FastAPI)
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { CacheService } from './cache.service';
import { LoggerService } from './logger.service';
import type {
  HeatmapResponse,
  NearbyResponse,
  StatsResponse,
  MLPredictionResponse
} from './api.service';

@Injectable({ providedIn: 'root' })
export class MlApiService {
  private baseUrl = environment.mlApiBase;

  constructor(
    private cache: CacheService,
    private logger: LoggerService
  ) {}

  /** Predice precio y plusvalia de un terreno via API ML */
  async predictPriceML(
    lat: number,
    lon: number,
    area_m2: number,
    city: string,
    state: string
  ): Promise<MLPredictionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lon, area_m2, city, state })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.logger.error('Error en prediccion ML', error);
      throw error;
    }
  }

  /** Obtiene estadisticas de la API ML */
  async getMLStats(): Promise<Record<string, unknown>> {
    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/stats`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    });
  }

  /** Obtiene historial de predicciones */
  async getPredictionsHistory(
    limit: number = 100,
    city?: string,
    state?: string
  ): Promise<Record<string, unknown>[]> {
    return this.retryWithBackoff(async () => {
      let url = `${this.baseUrl}/predictions/history?limit=${limit}`;

      if (city) url += `&city=${encodeURIComponent(city)}`;
      if (state) url += `&state=${encodeURIComponent(state)}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    });
  }

  /** Obtiene datos de heatmap de predicciones (optimizado con cache y retry) */
  async getPredictionsHeatmap(
    city?: string,
    minScore?: number,
    limit: number = 10000
  ): Promise<HeatmapResponse> {
    const cacheKey = `api_heatmap_${city || 'all'}_${minScore || 0}_${limit}`;

    const cached = this.cache.getCache<HeatmapResponse>(cacheKey);
    if (cached) {
      this.logger.success('Heatmap cargado desde cache');
      return cached;
    }

    return this.retryWithBackoff(async () => {
      let url = `${this.baseUrl}/predictions/heatmap?limit=${limit}`;

      if (city) url += `&city=${encodeURIComponent(city)}`;
      if (minScore !== undefined) url += `&min_score=${minScore}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Guardar en cache por 5 minutos (300000 ms)
      this.cache.setCache(cacheKey, data, 300000);

      return data;
    });
  }

  /** Obtiene predicciones cercanas a una ubicacion (con retry) */
  async getPredictionsNearby(
    lat: number,
    lon: number,
    radiusKm: number = 2.0,
    limit: number = 50
  ): Promise<NearbyResponse> {
    // No cachear nearby porque depende de la ubicacion del click (muy variable)
    return this.retryWithBackoff(async () => {
      const url = `${this.baseUrl}/predictions/nearby?lat=${lat}&lon=${lon}&radius_km=${radiusKm}&limit=${limit}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    });
  }

  /** Obtiene stats agregados por estado (para mapa coropletico) */
  async getStatsByState(): Promise<{ states: Record<string, { avg_score: number; count: number; avg_price_m2: number }> }> {
    const cacheKey = 'api_stats_by_state';
    const cached = this.cache.getCache<{ states: Record<string, { avg_score: number; count: number; avg_price_m2: number }> }>(cacheKey);
    if (cached) return cached;

    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/predictions/stats-by-state`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      this.cache.setCache(cacheKey, data, 600000); // cache 10 min
      return data;
    });
  }

  /** Obtiene predicciones en un bounding box (area rectangular) */
  async getPredictionsInBbox(
    minLat: number,
    maxLat: number,
    minLon: number,
    maxLon: number,
    limit: number = 5000
  ): Promise<Record<string, unknown>[]> {
    return this.retryWithBackoff(async () => {
      const url = `${this.baseUrl}/predictions/bbox?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}&limit=${limit}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    });
  }

  /** Obtiene estadisticas de predicciones por ciudad (con cache y retry) */
  async getPredictionsStatsByCity(): Promise<StatsResponse> {
    const cacheKey = 'api_stats_by_city';

    const cached = this.cache.getCache<StatsResponse>(cacheKey);
    if (cached) {
      this.logger.success('Estadisticas cargadas desde cache');
      return cached;
    }

    return this.retryWithBackoff(async () => {
      const response = await fetch(`${this.baseUrl}/predictions/stats-by-city`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Guardar en cache por 10 minutos (600000 ms) - las estadisticas cambian menos
      this.cache.setCache(cacheKey, data, 600000);

      return data;
    });
  }

  // ==================== RETRY LOGIC ====================

  /** Ejecuta una funcion asincrona con reintentos automaticos y backoff exponencial */
  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    initialDelay: number = 1000
  ): Promise<T> {
    let lastError: unknown;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;

        if (attempt < maxRetries) {
          const delay = initialDelay * Math.pow(2, attempt);
          this.logger.warn(`Intento ${attempt + 1} fallo. Reintentando en ${delay}ms...`, error);

          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    this.logger.error(`Fallo despues de ${maxRetries + 1} intentos`, lastError);
    throw lastError;
  }
}
