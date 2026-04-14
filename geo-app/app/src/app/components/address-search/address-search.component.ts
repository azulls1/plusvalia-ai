// src/app/components/address-search/address-search.component.ts
import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface SearchResult {
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  address: Record<string, string>;
}

@Component({
    selector: 'app-address-search',
    imports: [CommonModule, FormsModule],
    templateUrl: './address-search.component.html',
    styleUrls: ['./address-search.component.css']
})
export class AddressSearchComponent {
  @Output() locationSelected = new EventEmitter<{lat: number, lon: number, name: string}>();
  
  searchQuery = '';
  searchResults: SearchResult[] = [];
  isSearching = false;
  showResults = false;
  errorMessage = '';

  async searchAddress(): Promise<void> {
    if (!this.searchQuery.trim() || this.searchQuery.trim().length < 3) {
      this.errorMessage = 'Ingresa al menos 3 caracteres';
      return;
    }

    this.isSearching = true;
    this.errorMessage = '';
    this.searchResults = [];

    try {
      // Usar Nominatim de OpenStreetMap para geocoding
      const query = encodeURIComponent(this.searchQuery.trim());
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${query}&countrycodes=mx&limit=8&addressdetails=1`;
      
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'GeoAnalysis-App/1.0' // Nominatim requiere User-Agent
        }
      });

      if (!response.ok) {
        throw new Error('Error al buscar dirección');
      }

      const data: SearchResult[] = await response.json();
      
      if (data.length === 0) {
        this.errorMessage = 'No se encontraron resultados. Intenta con otra búsqueda.';
      } else {
        this.searchResults = data;
        this.showResults = true;
      }

    } catch (error) {
      console.error('Error en búsqueda de dirección:', error);
      this.errorMessage = 'Error al buscar. Intenta nuevamente.';
    } finally {
      this.isSearching = false;
    }
  }

  selectResult(result: SearchResult): void {
    const lat = parseFloat(result.lat);
    const lon = parseFloat(result.lon);
    const name = result.display_name;

    // Emitir evento con ubicación seleccionada
    this.locationSelected.emit({ lat, lon, name });

    // Limpiar búsqueda
    this.showResults = false;
    this.searchQuery = name; // Mostrar nombre seleccionado en el input
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.searchResults = [];
    this.showResults = false;
    this.errorMessage = '';
  }

  // Cerrar resultados al hacer click fuera
  closeResults(): void {
    setTimeout(() => {
      this.showResults = false;
    }, 200);
  }

  // Manejar Enter para buscar
  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.searchAddress();
    }
  }

  // Formatear tipo de resultado
  getResultIcon(type: string): string {
    const icons: {[key: string]: string} = {
      'house': '🏠',
      'residential': '🏘️',
      'commercial': '🏢',
      'industrial': '🏭',
      'retail': '🛒',
      'neighbourhood': '🏘️',
      'suburb': '🏘️',
      'city': '🏙️',
      'town': '🏘️',
      'village': '🏘️',
      'municipality': '🏛️',
      'state': '📍',
      'road': '🛣️',
      'street': '🛣️',
      'amenity': '📌',
      'building': '🏢'
    };
    
    return icons[type] || '📍';
  }

  // Formatear dirección para mostrar
  formatAddress(result: SearchResult): string {
    const addr = result.address;
    const parts: string[] = [];

    if (addr['road'] || addr['street']) parts.push(addr['road'] || addr['street']);
    if (addr['house_number']) parts.push(`#${addr['house_number']}`);
    if (addr['suburb'] || addr['neighbourhood']) parts.push(addr['suburb'] || addr['neighbourhood']);
    if (addr['city'] || addr['town'] || addr['village']) parts.push(addr['city'] || addr['town'] || addr['village']);
    if (addr['state']) parts.push(addr['state']);

    return parts.length > 0 ? parts.join(', ') : result.display_name;
  }
}

