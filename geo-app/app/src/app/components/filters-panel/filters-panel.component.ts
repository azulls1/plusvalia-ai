// src/app/components/filters-panel/filters-panel.component.ts - Componente de panel de filtros
import { Component, EventEmitter, Output, Input } from '@angular/core'; // decoradores de Angular
import { CommonModule } from '@angular/common'; // módulo común
import { FormsModule } from '@angular/forms'; // módulo para formularios (ngModel)

@Component({
    selector: 'app-filters-panel', // componente standalone
    imports: [CommonModule, FormsModule], // importa módulos necesarios
    templateUrl: './filters-panel.component.html', // ruta del template
    styleUrls: ['./filters-panel.component.css'] // ruta de estilos
})
export class FiltersPanelComponent { // clase del componente
  @Output() filtersApplied = new EventEmitter<any>(); // evento cuando se aplican filtros
  @Output() rebuildGrid = new EventEmitter<void>(); // evento cuando se recalcula grilla
  @Input() disabled = false; // propiedad de entrada para deshabilitar

  validationMessage = ''; // mensaje de validación inline

  // Tipos de amenidades disponibles (checkboxes)
  amenityTypes = [ // array de tipos con label y valor
    { label: 'Escuelas', value: 'school', checked: false }, // escuelas
    { label: 'Hospitales', value: 'hospital', checked: false }, // hospitales
    { label: 'Universidades', value: 'university', checked: false }, // universidades
    { label: 'Mercados', value: 'marketplace', checked: false }, // mercados
    { label: 'Paradas de Bus', value: 'bus_station', checked: false }, // paradas de bus
    { label: 'Metro', value: 'subway_entrance', checked: false }, // entradas de metro
    { label: 'Gasolineras', value: 'fuel', checked: false }, // gasolineras
    { label: 'Zonas Industriales', value: 'industrial', checked: false } // zonas industriales
  ];

  constructor() {} // constructor vacío

  // Aplica filtros y emite evento
  applyFilters(): void { // método público para aplicar filtros
    const selectedTypes = this.amenityTypes // filtra tipos seleccionados
      .filter(type => type.checked) // solo los marcados
      .map(type => type.value); // extrae el valor

    const filters = { // objeto de filtros
      types: selectedTypes.length > 0 ? selectedTypes : undefined // tipos (undefined si array vacío)
    };

    this.filtersApplied.emit(filters); // emite evento con filtros
  }

  // Limpia el mensaje de validación
  clearValidation(): void {
    this.validationMessage = '';
  }

  // Recalcula la grilla
  recalculateGrid(): void { // método público para recalcular grilla
    const confirmMsg = '¿Deseas recalcular la grilla? Esto puede tomar varios minutos.'; // mensaje de confirmación
    if (confirm(confirmMsg)) { // muestra confirmación
      this.rebuildGrid.emit(); // emite evento
    }
  }

  // Limpia todos los filtros
  clearFilters(): void { // método público para limpiar filtros
    this.amenityTypes.forEach(type => type.checked = false); // desmarca todos los checkboxes
    this.applyFilters(); // aplica filtros (vacíos = muestra todo)
  }

  // TrackBy function for amenityTypes *ngFor
  trackByAmenityValue(index: number, type: { label: string; value: string; checked: boolean }): string {
    return type.value;
  }

  // Selecciona o deselecciona todos los tipos de amenidad
  toggleAllAmenities(checked: boolean): void { // método con parámetro booleano
    this.amenityTypes.forEach(type => type.checked = checked); // marca o desmarca todos
  }
}

