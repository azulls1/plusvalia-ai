// src/app/services/cache.service.ts - Servicio dedicado de cache con localStorage
import { Injectable } from '@angular/core';
import { LoggerService } from './logger.service';

@Injectable({ providedIn: 'root' })
export class CacheService {
  constructor(private logger: LoggerService) {}

  /**
   * Guarda datos en localStorage con expiracion (tiempo en milisegundos).
   * @param key   Clave de cache (se recomienda prefijo 'api_')
   * @param data  Datos a almacenar
   * @param ttl   Tiempo de vida en ms (default: 5 minutos)
   */
  setCache(key: string, data: unknown, ttl: number = 300000): void {
    try {
      const item = {
        data: data,
        timestamp: Date.now(),
        ttl: ttl
      };
      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      this.logger.warn('Error guardando en cache:', error);
      // Si falla (ej: quota exceeded), continuar sin cache
    }
  }

  /**
   * Obtiene datos del cache si no han expirado.
   * @returns Los datos almacenados o null si no existen / expiraron
   */
  getCache<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;

      const cached = JSON.parse(item);
      const now = Date.now();

      // Verificar si el cache ha expirado
      if (now - cached.timestamp > cached.ttl) {
        localStorage.removeItem(key); // Limpiar cache expirado
        return null;
      }

      return cached.data as T;
    } catch (error) {
      this.logger.warn('Error leyendo cache:', error);
      localStorage.removeItem(key);
      return null;
    }
  }

  /**
   * Limpia cache especifico o todo el cache del API.
   * @param pattern Si se proporciona, solo elimina claves que contengan el patron
   */
  clearCache(pattern?: string): void {
    try {
      if (pattern) {
        // Limpia solo las claves que coincidan con el patron
        Object.keys(localStorage).forEach(key => {
          if (key.includes(pattern)) {
            localStorage.removeItem(key);
          }
        });
      } else {
        // Limpia todo el cache del API
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('api_')) {
            localStorage.removeItem(key);
          }
        });
      }
    } catch (error) {
      this.logger.warn('Error limpiando cache:', error);
    }
  }
}
