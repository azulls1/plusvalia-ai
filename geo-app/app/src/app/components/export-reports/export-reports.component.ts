// src/app/components/export-reports/export-reports.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeatmapPoint, CityStats } from '../../models/interfaces';

@Component({
  selector: 'app-export-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './export-reports.component.html',
  styleUrls: ['./export-reports.component.css']
})
export class ExportReportsComponent {
  @Input() predictions: HeatmapPoint[] = [];
  @Input() citiesStats: CityStats[] = [];

  isVisible = false;
  isExporting = false;
  statusMessage = '';

  toggleVisibility(): void {
    this.isVisible = !this.isVisible;
  }

  /** Escape a CSV field: wrap in quotes if it contains comma, quote, or newline */
  private escapeCsvField(value: string | number): string {
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  }

  /** Build CSV string from array of row objects */
  private buildCsv(rows: Record<string, string | number>[]): string {
    if (rows.length === 0) return '';
    const headers = Object.keys(rows[0]);
    const headerLine = headers.map(h => this.escapeCsvField(h)).join(',');
    const dataLines = rows.map(row =>
      headers.map(h => this.escapeCsvField(row[h])).join(',')
    );
    return [headerLine, ...dataLines].join('\n');
  }

  // Exportar predicciones a CSV usando citiesStats for real data
  async exportToCSV(): Promise<void> {
    this.isExporting = true;
    this.statusMessage = '';

    try {
      if (this.citiesStats.length === 0) {
        this.statusMessage = 'No hay datos de ciudades disponibles para exportar.';
        return;
      }

      // Export city-level data (real prices from citiesStats)
      const csvData = this.citiesStats.map((city, index) => ({
        'ID': index + 1,
        'Ciudad': city.city,
        'Predicciones': city.predictions_count,
        'Precio Promedio/m2': `$${city.avg_price_m2.toFixed(0)}`,
        'Precio Min/m2': `$${city.min_price_m2.toFixed(0)}`,
        'Precio Max/m2': `$${city.max_price_m2.toFixed(0)}`,
        'Score Plusvalia': city.avg_plusvalia_score.toFixed(2),
        'Nivel': this.getPotentialLevel(city.avg_plusvalia_score),
        'Potencial Alto': city.potential_distribution?.alto || 0,
        'Potencial Medio': city.potential_distribution?.medio || 0,
        'Potencial Bajo': city.potential_distribution?.bajo || 0
      }));

      const csvContent = this.buildCsv(csvData);
      this.downloadFile(csvContent, 'predicciones-plusvalia.csv', 'text/csv');
      this.statusMessage = 'Archivo CSV exportado exitosamente.';
    } catch (error) {
      console.error('Error exportando CSV:', error);
      this.statusMessage = 'Error al exportar CSV.';
    } finally {
      this.isExporting = false;
    }
  }

  // Exportar estadísticas por ciudad a CSV
  async exportStatsToCSV(): Promise<void> {
    this.isExporting = true;
    this.statusMessage = '';

    try {
      if (this.citiesStats.length === 0) {
        this.statusMessage = 'No hay estadísticas de ciudades disponibles.';
        return;
      }

      const csvData = this.citiesStats.map(city => ({
        'Ciudad': city.city,
        'Total Predicciones': city.predictions_count,
        'Precio Promedio/m2': `$${city.avg_price_m2.toFixed(0)}`,
        'Precio Minimo/m2': `$${city.min_price_m2.toFixed(0)}`,
        'Precio Maximo/m2': `$${city.max_price_m2.toFixed(0)}`,
        'Score Promedio': city.avg_plusvalia_score.toFixed(2),
        'Potencial Alto': city.potential_distribution?.alto || 0,
        'Potencial Medio': city.potential_distribution?.medio || 0,
        'Potencial Bajo': city.potential_distribution?.bajo || 0
      }));

      const csvContent = this.buildCsv(csvData);
      this.downloadFile(csvContent, 'estadisticas-ciudades.csv', 'text/csv');
      this.statusMessage = 'Estadisticas exportadas exitosamente.';
    } catch (error) {
      console.error('Error exportando estadísticas:', error);
      this.statusMessage = 'Error al exportar estadisticas.';
    } finally {
      this.isExporting = false;
    }
  }

  // Exportar Top 10 ciudades por score
  async exportTop10ToCSV(): Promise<void> {
    this.isExporting = true;
    this.statusMessage = '';

    try {
      if (this.citiesStats.length === 0) {
        this.statusMessage = 'No hay datos de ciudades disponibles.';
        return;
      }

      // Sort cities by score and take top 10
      const sorted = [...this.citiesStats].sort((a, b) => b.avg_plusvalia_score - a.avg_plusvalia_score);
      const top10 = sorted.slice(0, 10);

      const csvData = top10.map((city, index) => ({
        'Ranking': index + 1,
        'Ciudad': city.city,
        'Predicciones': city.predictions_count,
        'Score Plusvalia': city.avg_plusvalia_score.toFixed(2),
        'Nivel': this.getPotentialLevel(city.avg_plusvalia_score),
        'Precio Promedio/m2': `$${city.avg_price_m2.toFixed(0)}`,
        'Precio Min/m2': `$${city.min_price_m2.toFixed(0)}`,
        'Precio Max/m2': `$${city.max_price_m2.toFixed(0)}`
      }));

      const totalPredictions = this.citiesStats.reduce((sum, c) => sum + c.predictions_count, 0);
      const headerRows = [
        'TOP 10 MEJORES CIUDADES PARA INVERSION\n',
        `Generado: ${new Date().toLocaleString('es-MX')}\n`,
        `Total de predicciones analizadas: ${totalPredictions}\n\n`
      ].join('\n');

      const csvContent = headerRows + this.buildCsv(csvData);
      this.downloadFile(csvContent, 'top10-oportunidades.csv', 'text/csv');
      this.statusMessage = 'Top 10 exportado exitosamente.';
    } catch (error) {
      console.error('Error exportando Top 10:', error);
      this.statusMessage = 'Error al exportar Top 10.';
    } finally {
      this.isExporting = false;
    }
  }

  // Exportar reporte completo en formato texto
  async exportCompleteReport(): Promise<void> {
    this.isExporting = true;
    this.statusMessage = '';

    try {
      // Calculate real statistics from citiesStats
      const totalPredictions = this.citiesStats.reduce((sum, c) => sum + c.predictions_count, 0);
      const avgScore = totalPredictions > 0
        ? this.citiesStats.reduce((sum, c) => sum + c.avg_plusvalia_score * c.predictions_count, 0) / totalPredictions
        : 0;
      const avgPrice = totalPredictions > 0
        ? this.citiesStats.reduce((sum, c) => sum + c.avg_price_m2 * c.predictions_count, 0) / totalPredictions
        : 0;

      // Aggregate potential distribution from citiesStats
      let alto = 0, medio = 0, bajo = 0;
      this.citiesStats.forEach(city => {
        if (city.potential_distribution) {
          alto += city.potential_distribution.alto || 0;
          medio += city.potential_distribution.medio || 0;
          bajo += city.potential_distribution.bajo || 0;
        }
      });
      const totalDist = alto + medio + bajo;

      // Top 10 cities
      const sorted = [...this.citiesStats].sort((a, b) => b.avg_plusvalia_score - a.avg_plusvalia_score);
      const top10 = sorted.slice(0, 10);

      // Generar reporte
      const report = `
═══════════════════════════════════════════════════════════════
  REPORTE COMPLETO DE ANALISIS DE PLUSVALIA INMOBILIARIA
═══════════════════════════════════════════════════════════════

Fecha de generacion: ${new Date().toLocaleString('es-MX')}
Sistema: GeoAnalysis ML - Prediccion de Plusvalia

───────────────────────────────────────────────────────────────
RESUMEN EJECUTIVO
───────────────────────────────────────────────────────────────

Total de Predicciones: ${totalPredictions.toLocaleString()}
Score Promedio: ${avgScore.toFixed(2)}/100
Precio Promedio/m2: $${avgPrice.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}

Ciudades Analizadas: ${this.citiesStats.length}
${this.citiesStats.map(c => `  - ${c.city}: ${c.predictions_count.toLocaleString()} predicciones`).join('\n')}

───────────────────────────────────────────────────────────────
DISTRIBUCION DE POTENCIAL
───────────────────────────────────────────────────────────────

Alto (66-100):   ${alto.toLocaleString()} (${totalDist > 0 ? ((alto / totalDist) * 100).toFixed(1) : '0.0'}%)
Medio (33-66):   ${medio.toLocaleString()} (${totalDist > 0 ? ((medio / totalDist) * 100).toFixed(1) : '0.0'}%)
Bajo (0-33):     ${bajo.toLocaleString()} (${totalDist > 0 ? ((bajo / totalDist) * 100).toFixed(1) : '0.0'}%)

───────────────────────────────────────────────────────────────
TOP 10 MEJORES CIUDADES
───────────────────────────────────────────────────────────────

${top10.map((city, i) => `
${i + 1}. ${city.city} - Score: ${city.avg_plusvalia_score.toFixed(2)}/100 - ${this.getPotentialLevel(city.avg_plusvalia_score)}
   Precio Promedio: $${city.avg_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} /m2
   Rango: $${city.min_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} - $${city.max_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} /m2
   Predicciones: ${city.predictions_count.toLocaleString()}
`).join('')}

───────────────────────────────────────────────────────────────
ANALISIS POR CIUDAD
───────────────────────────────────────────────────────────────

${this.citiesStats.map(city => `
${city.city}
   - Total Predicciones: ${city.predictions_count.toLocaleString()}
   - Score Promedio: ${city.avg_plusvalia_score.toFixed(2)}/100
   - Precio Promedio: $${city.avg_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} /m2
   - Rango de Precios: $${city.min_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} - $${city.max_price_m2.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
   - Distribucion: Alto ${city.potential_distribution?.alto || 0} | Medio ${city.potential_distribution?.medio || 0} | Bajo ${city.potential_distribution?.bajo || 0}
`).join('')}

───────────────────────────────────────────────────────────────
NOTAS Y RECOMENDACIONES
───────────────────────────────────────────────────────────────

- Los scores de plusvalia se calculan con ML (Random Forest)
- Los datos incluyen amenidades, demografia INEGI y precios SHF
- Se recomienda validar oportunidades con analisis de mercado local
- Los precios son datos reales agregados por ciudad
- Para mas detalles, consultar el dashboard interactivo

═══════════════════════════════════════════════════════════════
  Fin del Reporte - GeoAnalysis ML
═══════════════════════════════════════════════════════════════
`;

      this.downloadFile(report, 'reporte-completo-plusvalia.txt', 'text/plain');
      this.statusMessage = 'Reporte completo exportado exitosamente.';
    } catch (error) {
      console.error('Error exportando reporte:', error);
      this.statusMessage = 'Error al exportar reporte.';
    } finally {
      this.isExporting = false;
    }
  }

  // Método auxiliar para descargar archivos
  private downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  // Método auxiliar para obtener nivel de potencial
  private getPotentialLevel(score: number): string {
    if (score >= 66) return 'Alto';
    if (score >= 33) return 'Medio';
    return 'Bajo';
  }

  // Copiar estadísticas al portapapeles
  async copyStatsToClipboard(): Promise<void> {
    this.statusMessage = '';
    try {
      const totalPredictions = this.citiesStats.reduce((sum, c) => sum + c.predictions_count, 0);
      const stats = `ESTADISTICAS DE PLUSVALIA

Total Predicciones: ${totalPredictions.toLocaleString()}
Ciudades: ${this.citiesStats.length}

${this.citiesStats.map(c => `${c.city}: ${c.predictions_count} pred., Score: ${c.avg_plusvalia_score.toFixed(1)}, Precio: $${c.avg_price_m2.toFixed(0)}/m2`).join('\n')}
      `;

      await navigator.clipboard.writeText(stats);
      this.statusMessage = 'Estadisticas copiadas al portapapeles.';
    } catch (error) {
      console.error('Error copiando al portapapeles:', error);
      this.statusMessage = 'Error al copiar al portapapeles.';
    }
  }
}
