import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FiltersPanelComponent } from './filters-panel.component';

describe('FiltersPanelComponent', () => {
  let component: FiltersPanelComponent;
  let fixture: ComponentFixture<FiltersPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FiltersPanelComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(FiltersPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have default city and state from environment', () => {
    expect(component.city).toBeTruthy();
    expect(component.state).toBeTruthy();
  });

  it('should have 8 amenity types', () => {
    expect(component.amenityTypes.length).toBe(8);
  });

  it('should initialize all amenity types as unchecked', () => {
    component.amenityTypes.forEach(type => {
      expect(type.checked).toBeFalse();
    });
  });

  it('should have correct amenity type values', () => {
    const values = component.amenityTypes.map(t => t.value);
    expect(values).toContain('school');
    expect(values).toContain('hospital');
    expect(values).toContain('university');
    expect(values).toContain('marketplace');
    expect(values).toContain('bus_station');
    expect(values).toContain('subway_entrance');
    expect(values).toContain('fuel');
    expect(values).toContain('industrial');
  });

  it('should not be disabled by default', () => {
    expect(component.disabled).toBeFalse();
  });

  // ==================== Amenity Type Toggling ====================

  describe('Amenity Type Toggling', () => {
    it('should toggle a specific amenity type', () => {
      const school = component.amenityTypes.find(t => t.value === 'school')!;
      expect(school.checked).toBeFalse();

      school.checked = true;
      expect(school.checked).toBeTrue();
    });

    it('should allow multiple amenity types to be checked', () => {
      component.amenityTypes[0].checked = true; // school
      component.amenityTypes[1].checked = true; // hospital

      const selectedCount = component.amenityTypes.filter(t => t.checked).length;
      expect(selectedCount).toBe(2);
    });
  });

  // ==================== Toggle All/None ====================

  describe('toggleAllAmenities', () => {
    it('should check all amenity types when called with true', () => {
      component.toggleAllAmenities(true);

      component.amenityTypes.forEach(type => {
        expect(type.checked).toBeTrue();
      });
    });

    it('should uncheck all amenity types when called with false', () => {
      // First check all
      component.toggleAllAmenities(true);
      // Then uncheck all
      component.toggleAllAmenities(false);

      component.amenityTypes.forEach(type => {
        expect(type.checked).toBeFalse();
      });
    });

    it('should set all 8 amenity types to true', () => {
      component.toggleAllAmenities(true);
      const checkedCount = component.amenityTypes.filter(t => t.checked).length;
      expect(checkedCount).toBe(8);
    });
  });

  // ==================== Apply Filters ====================

  describe('applyFilters', () => {
    it('should emit filtersApplied event', () => {
      spyOn(component.filtersApplied, 'emit');
      component.applyFilters();
      expect(component.filtersApplied.emit).toHaveBeenCalled();
    });

    it('should emit selected amenity types', () => {
      spyOn(component.filtersApplied, 'emit');
      component.amenityTypes[0].checked = true; // school
      component.amenityTypes[2].checked = true; // university

      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.types).toEqual(['school', 'university']);
    });

    it('should emit undefined types when none are selected', () => {
      spyOn(component.filtersApplied, 'emit');
      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.types).toBeUndefined();
    });

    it('should emit priceMin when set', () => {
      spyOn(component.filtersApplied, 'emit');
      component.priceMin = 5000;
      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.priceMin).toBe(5000);
    });

    it('should emit undefined priceMin when null', () => {
      spyOn(component.filtersApplied, 'emit');
      component.priceMin = null;
      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.priceMin).toBeUndefined();
    });

    it('should emit priceMax when set', () => {
      spyOn(component.filtersApplied, 'emit');
      component.priceMax = 50000;
      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.priceMax).toBe(50000);
    });

    it('should emit combined filters', () => {
      spyOn(component.filtersApplied, 'emit');
      component.amenityTypes[0].checked = true;
      component.priceMin = 1000;
      component.priceMax = 100000;

      component.applyFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.types).toEqual(['school']);
      expect(emittedFilters.priceMin).toBe(1000);
      expect(emittedFilters.priceMax).toBe(100000);
    });
  });

  // ==================== Recalculate Grid ====================

  describe('recalculateGrid', () => {
    it('should emit rebuildGrid event when user confirms', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      spyOn(component.rebuildGrid, 'emit');

      component.recalculateGrid();

      expect(window.confirm).toHaveBeenCalled();
      expect(component.rebuildGrid.emit).toHaveBeenCalled();
    });

    it('should NOT emit rebuildGrid event when user cancels', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      spyOn(component.rebuildGrid, 'emit');

      component.recalculateGrid();

      expect(component.rebuildGrid.emit).not.toHaveBeenCalled();
    });
  });

  // ==================== Extract from OSM ====================

  describe('extractFromOsm', () => {
    it('should alert when no amenity types are selected', () => {
      spyOn(window, 'alert');
      spyOn(component.extractOsm, 'emit');

      component.extractFromOsm();

      expect(window.alert).toHaveBeenCalledWith(
        'Por favor selecciona al menos un tipo de amenidad'
      );
      expect(component.extractOsm.emit).not.toHaveBeenCalled();
    });

    it('should alert when city is empty', () => {
      spyOn(window, 'alert');
      spyOn(component.extractOsm, 'emit');
      component.amenityTypes[0].checked = true;
      component.city = '';

      component.extractFromOsm();

      expect(window.alert).toHaveBeenCalledWith('Por favor ingresa ciudad y estado');
      expect(component.extractOsm.emit).not.toHaveBeenCalled();
    });

    it('should alert when state is empty', () => {
      spyOn(window, 'alert');
      spyOn(component.extractOsm, 'emit');
      component.amenityTypes[0].checked = true;
      component.city = 'Test';
      component.state = '';

      component.extractFromOsm();

      expect(window.alert).toHaveBeenCalledWith('Por favor ingresa ciudad y estado');
    });

    it('should emit extractOsm with correct params when valid', () => {
      spyOn(component.extractOsm, 'emit');
      component.amenityTypes[0].checked = true; // school
      component.amenityTypes[1].checked = true; // hospital
      component.city = 'Guadalajara';
      component.state = 'Jalisco';

      component.extractFromOsm();

      expect(component.extractOsm.emit).toHaveBeenCalledWith({
        city: 'Guadalajara',
        state: 'Jalisco',
        types: ['school', 'hospital']
      });
    });
  });

  // ==================== Clear Filters ====================

  describe('clearFilters', () => {
    it('should uncheck all amenity types', () => {
      component.toggleAllAmenities(true);
      component.clearFilters();

      component.amenityTypes.forEach(type => {
        expect(type.checked).toBeFalse();
      });
    });

    it('should emit filtersApplied after clearing', () => {
      spyOn(component.filtersApplied, 'emit');
      component.clearFilters();
      expect(component.filtersApplied.emit).toHaveBeenCalled();
    });

    it('should emit empty types after clearing', () => {
      spyOn(component.filtersApplied, 'emit');
      component.toggleAllAmenities(true);
      component.clearFilters();

      const emittedFilters = (component.filtersApplied.emit as jasmine.Spy).calls.first().args[0];
      expect(emittedFilters.types).toBeUndefined();
    });
  });
});
