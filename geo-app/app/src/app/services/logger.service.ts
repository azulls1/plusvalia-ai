// src/app/services/logger.service.ts - Servicio de logging seguro
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LoggerService {
  
  private isProduction = environment.production;

  // Log general - solo en desarrollo
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- variadic log args
  log(...args: unknown[]): void {
    if (!this.isProduction) {
      console.log(...args);
    }
  }

  // Warning - solo en desarrollo
  warn(...args: unknown[]): void {
    if (!this.isProduction) {
      console.warn(...args);
    }
  }

  // Error - siempre se registra pero sanitizado en producción
  error(message: string, error?: unknown): void {
    if (this.isProduction) {
      // En producción: solo mensaje genérico, NO detalles
      console.error(message);
      // Aquí podrías enviar a un servicio de monitoreo como Sentry
      // this.sendToErrorTracking(message, error);
    } else {
      // En desarrollo: todos los detalles
      console.error(message, error);
    }
  }

  // Success - solo en desarrollo
  success(message: string): void {
    if (!this.isProduction) {
      console.log(`✅ ${message}`);
    }
  }

}

