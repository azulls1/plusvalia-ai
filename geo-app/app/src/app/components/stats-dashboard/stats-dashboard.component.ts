// src/app/components/stats-dashboard/stats-dashboard.component.ts
import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeatmapPoint, CityStats } from '../../models/interfaces';

@Component({
  selector: 'app-stats-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-dashboard.component.html',
  styleUrls: ['./stats-dashboard.component.css']
})
export class StatsDashboardComponent implements OnInit, OnChanges {
  @Input() citiesStats: CityStats[] = [];
  @Input() predictions: HeatmapPoint[] = [];

  isVisible = false; // Control de visibilidad

  // Estadísticas generales (derived from citiesStats)
  totalPredictions = 0;
  avgPrice = 0;
  avgScore = 0;

  // Top 10 ciudades por score
  topOpportunities: { rank: number; city: string; avgPrice: number; avgScore: number; count: number }[] = [];

  // Distribución de precios (para histograma, from citiesStats)
  priceDistribution: { range: string; count: number; percentage: number }[] = [];

  // Distribución de potencial (aggregated from citiesStats)
  potentialDistribution: { label: string; count: number; percentage: number; color: string }[] = [];

  ngOnInit(): void {
    this.calculateStatistics();
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.calculateStatistics();
  }

  toggleVisibility(): void {
    this.isVisible = !this.isVisible;
  }

  private calculateStatistics(): void {
    if (!this.citiesStats || this.citiesStats.length === 0) return;

    // Total predictions from city stats
    this.totalPredictions = this.citiesStats.reduce((sum, c) => sum + c.predictions_count, 0);

    // Weighted averages from real city data
    if (this.totalPredictions > 0) {
      this.avgPrice = this.citiesStats.reduce((sum, c) => sum + c.avg_price_m2 * c.predictions_count, 0) / this.totalPredictions;
      this.avgScore = this.citiesStats.reduce((sum, c) => sum + c.avg_plusvalia_score * c.predictions_count, 0) / this.totalPredictions;
    }

    // Top 10 cities by avg score
    this.calculateTopOpportunities();

    // Price distribution from city averages
    this.calculatePriceDistribution();

    // Potential distribution aggregated from all cities
    this.calculatePotentialDistribution();
  }

  private calculateTopOpportunities(): void {
    // Sort cities by avg_plusvalia_score descending, take top 10
    const sorted = [...this.citiesStats].sort((a, b) => b.avg_plusvalia_score - a.avg_plusvalia_score);

    this.topOpportunities = sorted.slice(0, 10).map((city, index) => ({
      rank: index + 1,
      city: city.city,
      avgPrice: city.avg_price_m2,
      avgScore: Math.round(city.avg_plusvalia_score * 10) / 10,
      count: city.predictions_count
    }));
  }

  private calculatePriceDistribution(): void {
    const ranges = [
      { min: 0, max: 5000, label: '$0 - $5K' },
      { min: 5000, max: 10000, label: '$5K - $10K' },
      { min: 10000, max: 20000, label: '$10K - $20K' },
      { min: 20000, max: 40000, label: '$20K - $40K' },
      { min: 40000, max: 80000, label: '$40K - $80K' },
      { min: 80000, max: Infinity, label: '$80K+' }
    ];

    this.priceDistribution = ranges.map(range => {
      const count = this.citiesStats.filter(c => {
        return c.avg_price_m2 >= range.min && c.avg_price_m2 < range.max;
      }).length;

      const total = this.citiesStats.length;
      return {
        range: range.label,
        count,
        percentage: total > 0 ? (count / total) * 100 : 0
      };
    });
  }

  private calculatePotentialDistribution(): void {
    // Aggregate potential_distribution from all cities
    let alto = 0, medio = 0, bajo = 0;
    this.citiesStats.forEach(city => {
      if (city.potential_distribution) {
        alto += city.potential_distribution.alto || 0;
        medio += city.potential_distribution.medio || 0;
        bajo += city.potential_distribution.bajo || 0;
      }
    });

    const total = alto + medio + bajo;
    this.potentialDistribution = [
      { label: 'Alto', count: alto, percentage: total > 0 ? (alto / total) * 100 : 0, color: '#DC2626' },
      { label: 'Medio', count: medio, percentage: total > 0 ? (medio / total) * 100 : 0, color: '#D97706' },
      { label: 'Bajo', count: bajo, percentage: total > 0 ? (bajo / total) * 100 : 0, color: '#5B7065' }
    ];
  }

  getMaxPercentage(): number {
    const max = Math.max(...this.priceDistribution.map(d => d.percentage));
    return max > 0 ? max : 1;
  }

  // TrackBy functions for *ngFor performance
  trackByRank(_index: number, opp: { rank: number }): number {
    return opp.rank;
  }

  trackByRange(_index: number, dist: { range: string; count: number; percentage: number }): string {
    return dist.range;
  }

  trackByLabel(_index: number, pot: { label: string; count: number; percentage: number; color: string }): string {
    return pot.label;
  }

  trackByCity(_index: number, city: CityStats): string {
    return city.city;
  }

  /** Returns a color based on the plusvalia score, matching the app-wide palette. */
  getColorByScore(score: number): string {
    if (score >= 66) return '#DC2626';
    if (score >= 33) return '#D97706';
    return '#5B7065';
  }
}
