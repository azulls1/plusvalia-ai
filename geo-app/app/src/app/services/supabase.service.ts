// src/app/services/supabase.service.ts - Servicio dedicado para consultas a Supabase
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { environment } from '../../environments/environment';
import { CacheService } from './cache.service';
import { LoggerService } from './logger.service';
import type { Tile, Amenity, AmenityFilters } from '../models/interfaces';

@Injectable({ providedIn: 'root' })
export class SupabaseService {
  private supabase: SupabaseClient;

  // Estado reactivo compartido
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();

  private errorSubject = new BehaviorSubject<string | null>(null);
  public error$ = this.errorSubject.asObservable();

  constructor(
    private cache: CacheService,
    private logger: LoggerService
  ) {
    this.supabase = createClient(
      environment.supabaseUrl,
      environment.supabaseAnonKey,
      {
        auth: {
          persistSession: false,
          detectSessionInUrl: false,
          autoRefreshToken: false,
          flowType: 'implicit'
        }
      }
    );
  }

  /** Obtiene tiles de la grilla desde Supabase */
  async getTiles(limit: number = 1000, offset: number = 0): Promise<any> {
    this.setLoading(true);
    try {
      const { data, error } = await this.supabase
        .from('iainmobiliaria_grid_tiles')
        .select('*')
        .range(offset, offset + limit - 1)
        .order('price_m2_avg', { ascending: false });

      if (error) {
        this.logger.error('Error obteniendo tiles', error);
        this.setError('Error obteniendo tiles');
        throw error;
      }
      this.clearError();
      return data || [];
    } finally {
      this.setLoading(false);
    }
  }

  /** Obtiene amenidades desde Supabase con filtros opcionales */
  async getAmenities(filters: AmenityFilters = {}): Promise<Amenity[]> {
    this.setLoading(true);
    try {
      let query = this.supabase
        .from('iainmobiliaria_amenities')
        .select('*');

      if (filters.city) {
        query = query.eq('city', filters.city);
      }
      if (filters.state) {
        query = query.eq('state', filters.state);
      }
      if (filters.types && filters.types.length > 0) {
        query = query.in('amenity_type', filters.types);
      }

      const { data, error } = await query;

      if (error) {
        this.logger.error('Error obteniendo amenidades', error);
        this.setError('Error obteniendo amenidades');
        throw error;
      }
      this.clearError();
      return data || [];
    } finally {
      this.setLoading(false);
    }
  }

  /** Obtiene predicciones desde Supabase (tabla iainmobiliaria_predictions) */
  async getPredictions(filters: { city?: string; state?: string; minScore?: number; limit?: number } = {}): Promise<Record<string, unknown>[]> {
    this.setLoading(true);
    try {
      let query = this.supabase
        .from('iainmobiliaria_predictions')
        .select('*');

      if (filters.city) {
        query = query.eq('city', filters.city);
      }
      if (filters.state) {
        query = query.eq('state', filters.state);
      }
      if (filters.minScore) {
        query = query.gte('plusvalia_score', filters.minScore);
      }

      query = query.order('prediction_date', { ascending: false }).limit(filters.limit || 100);

      const { data, error } = await query;

      if (error) {
        this.logger.error('Error obteniendo predicciones', error);
        this.setError('Error obteniendo predicciones');
        throw error;
      }
      this.clearError();
      return data || [];
    } finally {
      this.setLoading(false);
    }
  }

  /** Obtiene historico de precios */
  async getPriceHistory(city: string, state: string, months: number = 12): Promise<Record<string, unknown>[]> {
    this.setLoading(true);
    try {
      const { data, error } = await this.supabase
        .from('iainmobiliaria_price_history')
        .select('*')
        .eq('city', city)
        .eq('state', state)
        .order('collection_date', { ascending: true })
        .limit(months);

      if (error) {
        this.logger.error('Error obteniendo historico', error);
        this.setError('Error obteniendo historico');
        throw error;
      }
      this.clearError();
      return data || [];
    } finally {
      this.setLoading(false);
    }
  }

  // -- helpers de estado reactivo --

  private setLoading(value: boolean): void {
    this.loadingSubject.next(value);
  }

  private setError(message: string): void {
    this.errorSubject.next(message);
  }

  private clearError(): void {
    this.errorSubject.next(null);
  }
}
