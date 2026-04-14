import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdvancedFiltersComponent, AdvancedFilters } from './advanced-filters.component';

describe('AdvancedFiltersComponent', () => {
  let component: AdvancedFiltersComponent;
  let fixture: ComponentFixture<AdvancedFiltersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdvancedFiltersComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AdvancedFiltersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default score range 0-100', () => {
    expect(component.scoreMin).toBe(0);
    expect(component.scoreMax).toBe(100);
  });

  it('should initialize with default price range 0-200000', () => {
    expect(component.priceMin).toBe(0);
    expect(component.priceMax).toBe(200000);
  });

  it('should initialize with all potential levels enabled', () => {
    expect(component.potentialLevels.bajo).toBeTrue();
    expect(component.potentialLevels.medio).toBeTrue();
    expect(component.potentialLevels.alto).toBeTrue();
  });

  it('should initialize with 32 mexican states', () => {
    expect(component.mexicanStates.length).toBe(32);
    expect(component.mexicanStates).toContain('Jalisco');
    expect(component.mexicanStates).toContain('Nuevo Leon');
    expect(component.mexicanStates).toContain('Ciudad de Mexico');
  });

  it('should initialize with no selected state', () => {
    expect(component.selectedState).toBe('');
  });

  it('should initialize with score_desc sort option', () => {
    expect(component.sortOption).toBe('score_desc');
  });

  it('should initialize with visibility hidden', () => {
    expect(component.isVisible).toBeFalse();
  });

  it('should initialize with 0 active filters', () => {
    expect(component.activeFiltersCount).toBe(0);
  });

  // ==================== Toggle Visibility ====================

  describe('toggleVisibility', () => {
    it('should toggle from hidden to visible', () => {
      component.toggleVisibility();
      expect(component.isVisible).toBeTrue();
    });

    it('should toggle from visible to hidden', () => {
      component.isVisible = true;
      component.toggleVisibility();
      expect(component.isVisible).toBeFalse();
    });
  });

  // ==================== Score Range ====================

  describe('Score Range Adjustment', () => {
    it('should allow setting custom scoreMin', () => {
      component.scoreMin = 25;
      expect(component.scoreMin).toBe(25);
    });

    it('should allow setting custom scoreMax', () => {
      component.scoreMax = 75;
      expect(component.scoreMax).toBe(75);
    });

    it('should count as active filter when scoreMin > 0', () => {
      component.scoreMin = 10;
      component.applyFilters();
      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should count as active filter when scoreMax < 100', () => {
      component.scoreMax = 90;
      component.applyFilters();
      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });
  });

  // ==================== Price Range ====================

  describe('Price Range Adjustment', () => {
    it('should allow setting custom priceMin', () => {
      component.priceMin = 5000;
      expect(component.priceMin).toBe(5000);
    });

    it('should allow setting custom priceMax', () => {
      component.priceMax = 100000;
      expect(component.priceMax).toBe(100000);
    });

    it('should count as active filter when priceMin > 0', () => {
      component.priceMin = 1000;
      component.applyFilters();
      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should count as active filter when priceMax < 200000', () => {
      component.priceMax = 150000;
      component.applyFilters();
      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });
  });

  // ==================== Potential Level Toggling ====================

  describe('Potential Level Toggling', () => {
    it('should toggle bajo off', () => {
      component.potentialLevels.bajo = false;
      component.applyFilters();

      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should toggle medio off', () => {
      component.potentialLevels.medio = false;
      component.applyFilters();

      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should toggle alto off', () => {
      component.potentialLevels.alto = false;
      component.applyFilters();

      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should include all active levels in emitted filters', () => {
      spyOn(component.filtersChanged, 'emit');
      component.potentialLevels.bajo = false;
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.potentialLevels).toEqual(['medio', 'alto']);
    });

    it('should emit all 3 levels when all are enabled', () => {
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.potentialLevels).toEqual(['bajo', 'medio', 'alto']);
    });
  });

  // ==================== State Selection ====================

  describe('State Selection', () => {
    it('should allow selecting a state', () => {
      component.selectedState = 'Jalisco';
      expect(component.selectedState).toBe('Jalisco');
    });

    it('should count as active filter when a state is selected', () => {
      component.selectedState = 'Nuevo Leon';
      component.applyFilters();
      expect(component.activeFiltersCount).toBeGreaterThanOrEqual(1);
    });

    it('should NOT count as active filter when no state is selected', () => {
      component.selectedState = '';
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(0);
    });

    it('should emit selectedState in filters', () => {
      spyOn(component.filtersChanged, 'emit');
      component.selectedState = 'Queretaro';
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.selectedState).toBe('Queretaro');
    });

    it('should emit empty string when no state is selected', () => {
      spyOn(component.filtersChanged, 'emit');
      component.selectedState = '';
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.selectedState).toBe('');
    });
  });

  // ==================== Sort Options ====================

  describe('Sort Options', () => {
    it('should parse score_desc correctly', () => {
      component.sortOption = 'score_desc';
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.sortBy).toBe('score');
      expect(emitted.sortOrder).toBe('desc');
    });

    it('should parse price_asc correctly', () => {
      component.sortOption = 'price_asc';
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.sortBy).toBe('price');
      expect(emitted.sortOrder).toBe('asc');
    });

    it('should parse city_asc correctly', () => {
      component.sortOption = 'city_asc';
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.sortBy).toBe('city');
      expect(emitted.sortOrder).toBe('asc');
    });
  });

  // ==================== Apply Filters ====================

  describe('applyFilters', () => {
    it('should emit filtersChanged event', () => {
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();
      expect(component.filtersChanged.emit).toHaveBeenCalled();
    });

    it('should emit correct filter object structure', () => {
      spyOn(component.filtersChanged, 'emit');
      component.applyFilters();

      const emitted = (component.filtersChanged.emit as jasmine.Spy).calls.first().args[0] as AdvancedFilters;
      expect(emitted.scoreMin).toBeDefined();
      expect(emitted.scoreMax).toBeDefined();
      expect(emitted.priceMin).toBeDefined();
      expect(emitted.priceMax).toBeDefined();
      expect(emitted.potentialLevels).toBeDefined();
      expect(emitted.selectedState).toBeDefined();
      expect(emitted.sortBy).toBeDefined();
      expect(emitted.sortOrder).toBeDefined();
    });

    it('should calculate active filters count', () => {
      component.scoreMin = 20;
      component.priceMax = 100000;
      component.potentialLevels.bajo = false;

      component.applyFilters();

      expect(component.activeFiltersCount).toBe(3);
    });

    it('should only emit on applyFilters call, not on input change', () => {
      spyOn(component.filtersChanged, 'emit');
      component.scoreMin = 50;
      component.priceMax = 80000;
      component.selectedState = 'Jalisco';
      // No call to applyFilters
      expect(component.filtersChanged.emit).not.toHaveBeenCalled();
    });
  });

  // ==================== Reset Filters ====================

  describe('resetFilters', () => {
    it('should reset scoreMin to 0', () => {
      component.scoreMin = 50;
      component.resetFilters();
      expect(component.scoreMin).toBe(0);
    });

    it('should reset scoreMax to 100', () => {
      component.scoreMax = 80;
      component.resetFilters();
      expect(component.scoreMax).toBe(100);
    });

    it('should reset priceMin to 0', () => {
      component.priceMin = 10000;
      component.resetFilters();
      expect(component.priceMin).toBe(0);
    });

    it('should reset priceMax to 200000', () => {
      component.priceMax = 50000;
      component.resetFilters();
      expect(component.priceMax).toBe(200000);
    });

    it('should reset all potential levels to true', () => {
      component.potentialLevels = { bajo: false, medio: false, alto: false };
      component.resetFilters();
      expect(component.potentialLevels).toEqual({ bajo: true, medio: true, alto: true });
    });

    it('should clear selected state', () => {
      component.selectedState = 'Jalisco';
      component.resetFilters();
      expect(component.selectedState).toBe('');
    });

    it('should reset sortOption to score_desc', () => {
      component.sortOption = 'price_asc';
      component.resetFilters();
      expect(component.sortOption).toBe('score_desc');
    });

    it('should emit filtersChanged after reset', () => {
      spyOn(component.filtersChanged, 'emit');
      component.resetFilters();
      expect(component.filtersChanged.emit).toHaveBeenCalled();
    });
  });

  // ==================== Active Filters Count ====================

  describe('Active Filters Count', () => {
    it('should be 0 with all defaults', () => {
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(0);
    });

    it('should count 1 for score filter only', () => {
      component.scoreMin = 10;
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(1);
    });

    it('should count 1 for price filter only', () => {
      component.priceMax = 100000;
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(1);
    });

    it('should count 1 for potential filter only', () => {
      component.potentialLevels.alto = false;
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(1);
    });

    it('should count 1 for state filter only', () => {
      component.selectedState = 'Sonora';
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(1);
    });

    it('should count 4 when all filters are active', () => {
      component.scoreMin = 10;
      component.priceMax = 100000;
      component.potentialLevels.bajo = false;
      component.selectedState = 'Jalisco';
      component.applyFilters();
      expect(component.activeFiltersCount).toBe(4);
    });
  });

  // ==================== Helper Methods ====================

  describe('formatPrice', () => {
    it('should format millions', () => {
      expect(component.formatPrice(1000000)).toBe('$1.0M');
      expect(component.formatPrice(2500000)).toBe('$2.5M');
    });

    it('should format thousands', () => {
      expect(component.formatPrice(1000)).toBe('$1K');
      expect(component.formatPrice(50000)).toBe('$50K');
    });

    it('should format small values', () => {
      expect(component.formatPrice(500)).toBe('$500');
      expect(component.formatPrice(0)).toBe('$0');
    });
  });
});
