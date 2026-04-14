// src/app/components/advanced-filters/advanced-filters.component.ts
import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

/** 32 Mexican states — shared constant for reuse across components */
export const MEXICAN_STATES: readonly string[] = [
  'Aguascalientes',
  'Baja California',
  'Baja California Sur',
  'Campeche',
  'Chiapas',
  'Chihuahua',
  'Ciudad de Mexico',
  'Coahuila',
  'Colima',
  'Durango',
  'Estado de Mexico',
  'Guanajuato',
  'Guerrero',
  'Hidalgo',
  'Jalisco',
  'Michoacan',
  'Morelos',
  'Nayarit',
  'Nuevo Leon',
  'Oaxaca',
  'Puebla',
  'Queretaro',
  'Quintana Roo',
  'San Luis Potosi',
  'Sinaloa',
  'Sonora',
  'Tabasco',
  'Tamaulipas',
  'Tlaxcala',
  'Veracruz',
  'Yucatan',
  'Zacatecas'
] as const;

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

@Component({
    selector: 'app-advanced-filters',
    imports: [CommonModule, FormsModule],
    templateUrl: './advanced-filters.component.html',
    styleUrls: ['./advanced-filters.component.css']
})
export class AdvancedFiltersComponent {
  @Output() filtersChanged = new EventEmitter<AdvancedFilters>();

  isVisible = false;

  // Score range
  scoreMin = 0;
  scoreMax = 100;

  // Price range
  priceMin = 0;
  priceMax = 200000;

  // Potential toggle states
  potentialLevels = {
    bajo: true,
    medio: true,
    alto: true
  };

  // State filter
  selectedState = '';

  // Sort (combined field + direction)
  sortOption = 'score_desc';

  // Active filters count
  activeFiltersCount = 0;

  // 32 Mexican states (from shared constant)
  mexicanStates: readonly string[] = MEXICAN_STATES;

  toggleVisibility(): void {
    this.isVisible = !this.isVisible;
  }

  applyFilters(): void {
    const [sortBy, sortOrder] = this.parseSortOption();

    const filters: AdvancedFilters = {
      scoreMin: this.scoreMin,
      scoreMax: this.scoreMax,
      priceMin: this.priceMin,
      priceMax: this.priceMax,
      potentialLevels: this.getActivePotentialLevels(),
      selectedState: this.selectedState,
      sortBy,
      sortOrder
    };

    this.calculateActiveFilters();
    this.filtersChanged.emit(filters);
  }

  resetFilters(): void {
    this.scoreMin = 0;
    this.scoreMax = 100;
    this.priceMin = 0;
    this.priceMax = 200000;
    this.potentialLevels = { bajo: true, medio: true, alto: true };
    this.selectedState = '';
    this.sortOption = 'score_desc';

    this.applyFilters();
  }

  formatPrice(value: number): string {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  }

  private parseSortOption(): ['score' | 'price' | 'city', 'asc' | 'desc'] {
    const parts = this.sortOption.split('_');
    const field = parts[0] as 'score' | 'price' | 'city';
    const order = parts[1] as 'asc' | 'desc';
    return [field, order];
  }

  private getActivePotentialLevels(): string[] {
    const levels: string[] = [];
    if (this.potentialLevels.bajo) levels.push('bajo');
    if (this.potentialLevels.medio) levels.push('medio');
    if (this.potentialLevels.alto) levels.push('alto');
    return levels;
  }

  private calculateActiveFilters(): void {
    let count = 0;

    if (this.scoreMin > 0 || this.scoreMax < 100) count++;
    if (this.priceMin > 0 || this.priceMax < 200000) count++;

    const activePotentials = this.getActivePotentialLevels();
    if (activePotentials.length < 3) count++;

    if (this.selectedState !== '') count++;

    this.activeFiltersCount = count;
  }
}
