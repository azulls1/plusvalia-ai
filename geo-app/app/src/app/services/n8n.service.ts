// src/app/services/n8n.service.ts - Servicio dedicado para llamadas a webhooks n8n
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { LoggerService } from './logger.service';

@Injectable({ providedIn: 'root' })
export class N8nService {
  private baseUrl = environment.n8nBase;

  constructor(private logger: LoggerService) {}

  /** Sube archivo CSV de comparables a n8n para procesamiento */
  async uploadComparablesCsv(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseUrl}/ingest-csv`, {
        method: 'POST',
        body: formData
        // no incluir Content-Type, el navegador lo configura automaticamente con boundary
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.logger.error('Error subiendo CSV', error);
      throw error;
    }
  }

  /** Dispara extraccion de amenidades OSM via n8n */
  async fetchOsmAmenities(city: string, state: string, types: string[]): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/osm-amenities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city,
          state,
          types: types.join(',')
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.logger.error('Error extrayendo OSM', error);
      throw error;
    }
  }

  /** Dispara reconstruccion de grilla via n8n */
  async rebuildGrid(step?: number): Promise<any> {
    const gridStep = step || environment.gridDegStep;

    try {
      const response = await fetch(`${this.baseUrl}/grid-build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: gridStep })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.logger.error('Error reconstruyendo grilla', error);
      throw error;
    }
  }
}
