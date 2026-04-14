import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class MapStateService {
  /**
   * Returns a color hex string based on the plusvalia score.
   */
  getColorByScore(score: number): string {
    if (score >= 66) return '#DC2626';
    if (score >= 33) return '#D97706';
    return '#5B7065';
  }

  /**
   * Returns a color hex string based on the growth potential category.
   */
  getColorByPotential(potential: string): string {
    const p = potential.toLowerCase();
    if (p === 'alto' || p === 'muy_alto') return '#DC2626';
    if (p === 'medio') return '#D97706';
    return '#5B7065';
  }

  /**
   * Returns the city coordinates and zoom level for centering the map.
   */
  getCityCoordinates(city: string): [number, number, number] | null {
    const cityCoords: Record<string, [number, number, number]> = {
      'Aguascalientes': [21.88, -102.29, 12],
      'Mexicali': [32.62, -115.45, 12],
      'La Paz': [24.14, -110.31, 12],
      'Campeche': [19.83, -90.53, 12],
      'Tuxtla Gutiérrez': [16.75, -93.12, 12],
      'Chihuahua': [28.64, -106.09, 12],
      'Ciudad de México': [19.43, -99.13, 12],
      'Saltillo': [25.42, -100.99, 12],
      'Colima': [19.24, -103.72, 12],
      'Durango': [24.02, -104.67, 12],
      'Toluca': [19.29, -99.66, 12],
      'Guanajuato': [21.02, -101.26, 12],
      'Chilpancingo': [17.55, -99.50, 12],
      'Pachuca': [20.12, -98.73, 12],
      'Guadalajara': [20.67, -103.35, 12],
      'Morelia': [19.70, -101.19, 12],
      'Cuernavaca': [18.92, -99.23, 12],
      'Tepic': [21.50, -104.90, 12],
      'Monterrey': [25.67, -100.31, 12],
      'Oaxaca': [17.07, -96.72, 12],
      'Puebla': [19.04, -98.20, 12],
      'Querétaro': [20.59, -100.39, 12],
      'Chetumal': [18.50, -88.30, 12],
      'San Luis Potosí': [22.15, -100.98, 12],
      'Culiacán': [24.81, -107.39, 12],
      'Hermosillo': [29.07, -110.96, 12],
      'Villahermosa': [17.99, -92.93, 12],
      'Ciudad Victoria': [23.74, -99.15, 12],
      'Tlaxcala': [19.32, -98.24, 12],
      'Xalapa': [19.54, -96.93, 12],
      'Mérida': [20.97, -89.62, 12],
      'Zacatecas': [22.77, -102.58, 12],
      'Zapopan': [20.72, -103.39, 12],
    };
    return cityCoords[city] || null;
  }
}
