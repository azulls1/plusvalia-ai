import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MapaComponent } from './mapa.component';
import { ApiService } from '../../services/api.service';

// Mock Leaflet to avoid DOM/canvas errors in tests
const mockMap = {
  setView: jasmine.createSpy('setView').and.callFake(function(this: any) { return this; }),
  addLayer: jasmine.createSpy('addLayer'),
  removeLayer: jasmine.createSpy('removeLayer'),
  on: jasmine.createSpy('on'),
  removeControl: jasmine.createSpy('removeControl')
};

const mockHeatLayer = {
  setLatLngs: jasmine.createSpy('setLatLngs'),
  addTo: jasmine.createSpy('addTo').and.callFake(function(this: any) { return this; })
};

const mockMarkerClusterGroup = {
  clearLayers: jasmine.createSpy('clearLayers'),
  addLayer: jasmine.createSpy('addLayer')
};

const mockMarker = {
  bindPopup: jasmine.createSpy('bindPopup').and.callFake(function(this: any) { return this; }),
  addTo: jasmine.createSpy('addTo').and.callFake(function(this: any) { return this; }),
  openPopup: jasmine.createSpy('openPopup').and.callFake(function(this: any) { return this; })
};

const mockTileLayer = {
  addTo: jasmine.createSpy('addTo')
};

const mockLegendControl = {
  addTo: jasmine.createSpy('addTo'),
  onAdd: null as any
};

const mockPopup = {
  setLatLng: jasmine.createSpy('setLatLng').and.callFake(function(this: any) { return this; }),
  setContent: jasmine.createSpy('setContent').and.callFake(function(this: any) { return this; }),
  openOn: jasmine.createSpy('openOn')
};

// We need to mock the Leaflet module before tests run
// Since Leaflet is imported as * as L, we mock the global usage via the component
describe('MapaComponent', () => {
  let component: MapaComponent;
  let fixture: ComponentFixture<MapaComponent>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiServiceSpy = jasmine.createSpyObj('ApiService', [
      'getTiles',
      'getAmenities',
      'getPredictionsHeatmap',
      'getPredictionsStatsByCity',
      'getPredictionsNearby',
      'clearCache',
      'fetchOsmAmenities',
      'rebuildGrid'
    ]);

    // Setup default resolved promises
    apiServiceSpy.getTiles.and.returnValue(Promise.resolve([]));
    apiServiceSpy.getAmenities.and.returnValue(Promise.resolve([]));
    apiServiceSpy.getPredictionsHeatmap.and.returnValue(Promise.resolve({ points: [], count: 0, filters: {} }));
    apiServiceSpy.getPredictionsStatsByCity.and.returnValue(Promise.resolve({ cities: [], total_predictions: 0, cities_count: 0 }));

    await TestBed.configureTestingModule({
      imports: [MapaComponent],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    // Create a mock #map element in the DOM for Leaflet to attach to
    const mapDiv = document.createElement('div');
    mapDiv.id = 'map';
    mapDiv.style.height = '400px';
    mapDiv.style.width = '600px';
    document.body.appendChild(mapDiv);

    fixture = TestBed.createComponent(MapaComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    // Clean up mock map element
    const mapDiv = document.getElementById('map');
    if (mapDiv) {
      mapDiv.remove();
    }
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty arrays', () => {
    expect(component.tiles).toEqual([]);
    expect(component.amenities).toEqual([]);
    expect(component.predictions).toEqual([]);
    expect(component.filteredPredictions).toEqual([]);
  });

  it('should initialize with loading false', () => {
    expect(component.loading).toBeFalse();
  });

  it('should initialize with predictions view mode', () => {
    expect(component.viewMode).toBe('predictions');
  });

  it('should initialize with empty selectedCity', () => {
    expect(component.selectedCity).toBe('');
  });

  it('should initialize with empty message', () => {
    expect(component.message).toBe('');
  });

  it('should initialize with info message type', () => {
    expect(component.messageType).toBe('info');
  });

  // ==================== loadData ====================

  describe('loadData', () => {
    it('should call all API methods on loadData', async () => {
      // Skip ngOnInit by calling loadData directly
      await component.loadData();

      expect(apiServiceSpy.getTiles).toHaveBeenCalled();
      expect(apiServiceSpy.getAmenities).toHaveBeenCalled();
      expect(apiServiceSpy.getPredictionsHeatmap).toHaveBeenCalled();
      expect(apiServiceSpy.getPredictionsStatsByCity).toHaveBeenCalled();
    });

    it('should set loading to true during data fetch', async () => {
      let loadingDuringFetch = false;
      apiServiceSpy.getTiles.and.callFake(() => {
        loadingDuringFetch = component.loading;
        return Promise.resolve([]);
      });

      await component.loadData();
      expect(loadingDuringFetch).toBeTrue();
    });

    it('should set loading to false after successful load', async () => {
      await component.loadData();
      expect(component.loading).toBeFalse();
    });

    it('should store tiles data', async () => {
      const mockTiles = [
        { id: 1, lat: 20.5, lon: -103.3, price_m2_avg: 15000 }
      ];
      apiServiceSpy.getTiles.and.returnValue(Promise.resolve(mockTiles));

      await component.loadData();
      expect(component.tiles).toEqual(mockTiles);
    });

    it('should store amenities data', async () => {
      const mockAmenities = [{ id: 1, name: 'School', lat: 20.5, lon: -103.3 }];
      apiServiceSpy.getAmenities.and.returnValue(Promise.resolve(mockAmenities));

      await component.loadData();
      expect(component.amenities).toEqual(mockAmenities);
    });

    it('should store predictions data from points field', async () => {
      const mockPoints = [[20.5, -103.3, 0.8], [20.6, -103.4, 0.6]];
      apiServiceSpy.getPredictionsHeatmap.and.returnValue(
        Promise.resolve({ points: mockPoints as [number, number, number][], count: 2, filters: {} })
      );

      await component.loadData();
      expect(component.predictions).toEqual(mockPoints);
    });

    it('should initialize filteredPredictions with all predictions', async () => {
      const mockPoints = [[20.5, -103.3, 0.8]] as [number, number, number][];
      apiServiceSpy.getPredictionsHeatmap.and.returnValue(
        Promise.resolve({ points: mockPoints, count: 1, filters: {} })
      );

      await component.loadData();
      expect(component.filteredPredictions).toEqual(mockPoints);
    });

    it('should store cities stats', async () => {
      const mockStats = {
        cities: [{
          city: 'GDL', state: 'Jalisco', predictions_count: 100,
          avg_price_m2: 10000, min_price_m2: 5000, max_price_m2: 15000,
          avg_plusvalia_score: 70, potential_distribution: { alto: 50, medio: 30, bajo: 20 }
        }],
        total_predictions: 100, cities_count: 1
      };
      apiServiceSpy.getPredictionsStatsByCity.and.returnValue(Promise.resolve(mockStats));

      await component.loadData();
      expect(component.citiesStats).toEqual(mockStats.cities);
    });

    it('should handle API errors gracefully', async () => {
      apiServiceSpy.getTiles.and.returnValue(Promise.reject(new Error('API down')));

      await component.loadData();

      expect(component.loading).toBeFalse();
      expect(component.messageType).toBe('error');
    });

    it('should pass selectedCity to getPredictionsHeatmap', async () => {
      component.selectedCity = 'Guadalajara';
      await component.loadData();

      expect(apiServiceSpy.getPredictionsHeatmap).toHaveBeenCalledWith(
        'Guadalajara', undefined, 15000
      );
    });

    it('should pass undefined when no city is selected', async () => {
      component.selectedCity = '';
      await component.loadData();

      expect(apiServiceSpy.getPredictionsHeatmap).toHaveBeenCalledWith(
        undefined, undefined, 15000
      );
    });
  });

  // ==================== View Mode Switching ====================

  describe('switchViewMode', () => {
    beforeEach(async () => {
      // Initialize the map first
      try {
        fixture.detectChanges();
        await fixture.whenStable();
      } catch (e) {
        // Leaflet might throw in test environment, but component state is still set
      }
    });

    it('should switch viewMode to tiles', () => {
      component.switchViewMode('tiles');
      expect(component.viewMode).toBe('tiles');
    });

    it('should switch viewMode to predictions', () => {
      component.viewMode = 'tiles';
      component.switchViewMode('predictions');
      expect(component.viewMode).toBe('predictions');
    });

    it('should update message when switching mode', () => {
      component.switchViewMode('tiles');
      expect(component.message).toContain('Precios');

      component.switchViewMode('predictions');
      expect(component.message).toContain('Predicciones');
    });
  });

  // ==================== City Filter ====================

  describe('filterByCity', () => {
    it('should set selectedCity', async () => {
      await component.filterByCity('Guadalajara');
      expect(component.selectedCity).toBe('Guadalajara');
    });

    it('should reload data after setting city', async () => {
      await component.filterByCity('Monterrey');
      // loadData is called which calls all API methods again
      expect(apiServiceSpy.getTiles.calls.count()).toBeGreaterThanOrEqual(1);
    });
  });

  // ==================== clearCache ====================

  describe('clearCache', () => {
    it('should call apiService.clearCache', () => {
      component.clearCache();
      expect(apiServiceSpy.clearCache).toHaveBeenCalled();
    });

    it('should set loading to true', () => {
      component.clearCache();
      expect(component.loading).toBeTrue();
    });
  });

  // ==================== Event Handlers ====================

  describe('onFileUploaded', () => {
    it('should show success message', () => {
      component.onFileUploaded({ ok: true, inserted: 5 });
      expect(component.message).toContain('CSV procesado');
      expect(component.messageType).toBe('success');
    });
  });

  describe('onFiltersApplied', () => {
    it('should call getAmenities with filters', () => {
      apiServiceSpy.getAmenities.and.returnValue(Promise.resolve([]));
      const filters = { types: ['school'] };

      component.onFiltersApplied(filters);

      expect(apiServiceSpy.getAmenities).toHaveBeenCalledWith(filters);
    });

    it('should set loading to true during filter application', () => {
      apiServiceSpy.getAmenities.and.returnValue(Promise.resolve([]));

      component.onFiltersApplied({});

      expect(component.loading).toBeTrue();
    });
  });

  describe('onExtractOsm', () => {
    it('should call fetchOsmAmenities with params', () => {
      apiServiceSpy.fetchOsmAmenities.and.returnValue(Promise.resolve({ upserts: 10 }));
      const params = { city: 'GDL', state: 'JAL', types: ['school'] };

      component.onExtractOsm(params);

      expect(apiServiceSpy.fetchOsmAmenities).toHaveBeenCalledWith('GDL', 'JAL', ['school']);
    });

    it('should set loading to true', () => {
      apiServiceSpy.fetchOsmAmenities.and.returnValue(Promise.resolve({ upserts: 0 }));

      component.onExtractOsm({ city: 'GDL', state: 'JAL', types: [] });

      expect(component.loading).toBeTrue();
    });
  });

  describe('onRebuildGrid', () => {
    it('should call rebuildGrid', () => {
      apiServiceSpy.rebuildGrid.and.returnValue(Promise.resolve({ tiles: 100 }));

      component.onRebuildGrid();

      expect(apiServiceSpy.rebuildGrid).toHaveBeenCalled();
    });

    it('should set loading to true', () => {
      apiServiceSpy.rebuildGrid.and.returnValue(Promise.resolve({ tiles: 0 }));

      component.onRebuildGrid();

      expect(component.loading).toBeTrue();
    });
  });

  // ==================== onAdvancedFiltersChanged ====================

  describe('onAdvancedFiltersChanged', () => {
    beforeEach(async () => {
      // Populate predictions
      component.predictions = [
        [20.5, -103.3, 0.85],  // score=85, alto
        [20.6, -103.4, 0.50],  // score=50, medio
        [20.7, -103.5, 0.20],  // score=20, bajo
      ];
    });

    it('should filter predictions by score range', () => {
      const filters = {
        scoreMin: 40,
        scoreMax: 90,
        priceMin: 0,
        priceMax: 200000,
        potentialLevels: ['bajo', 'medio', 'alto'],
        cities: [],
        sortBy: 'score' as const,
        sortOrder: 'desc' as const
      };

      component.onAdvancedFiltersChanged(filters);

      // Should include score=85 and score=50, exclude score=20
      expect(component.filteredPredictions.length).toBe(2);
    });

    it('should filter predictions by potential level', () => {
      const filters = {
        scoreMin: 0,
        scoreMax: 100,
        priceMin: 0,
        priceMax: 200000,
        potentialLevels: ['alto'],
        cities: [],
        sortBy: 'score' as const,
        sortOrder: 'desc' as const
      };

      component.onAdvancedFiltersChanged(filters);

      // Only score=85 is alto (>= 66)
      expect(component.filteredPredictions.length).toBe(1);
    });

    it('should sort predictions by score descending', () => {
      const filters = {
        scoreMin: 0,
        scoreMax: 100,
        priceMin: 0,
        priceMax: 200000,
        potentialLevels: ['bajo', 'medio', 'alto'],
        cities: [],
        sortBy: 'score' as const,
        sortOrder: 'desc' as const
      };

      component.onAdvancedFiltersChanged(filters);

      expect(component.filteredPredictions[0][2]).toBe(0.85);
      expect(component.filteredPredictions[1][2]).toBe(0.50);
      expect(component.filteredPredictions[2][2]).toBe(0.20);
    });

    it('should sort predictions ascending when specified', () => {
      const filters = {
        scoreMin: 0,
        scoreMax: 100,
        priceMin: 0,
        priceMax: 200000,
        potentialLevels: ['bajo', 'medio', 'alto'],
        cities: [],
        sortBy: 'score' as const,
        sortOrder: 'asc' as const
      };

      component.onAdvancedFiltersChanged(filters);

      expect(component.filteredPredictions[0][2]).toBe(0.20);
      expect(component.filteredPredictions[2][2]).toBe(0.85);
    });

    it('should show success message with count', () => {
      const filters = {
        scoreMin: 0,
        scoreMax: 100,
        priceMin: 0,
        priceMax: 200000,
        potentialLevels: ['bajo', 'medio', 'alto'],
        cities: [],
        sortBy: 'score' as const,
        sortOrder: 'desc' as const
      };

      component.onAdvancedFiltersChanged(filters);

      expect(component.messageType).toBe('success');
      expect(component.message).toContain('3');
    });
  });

  // ==================== onLocationSelected ====================

  describe('onLocationSelected', () => {
    it('should show success message', () => {
      // Will fail on Leaflet calls but we test the state changes
      try {
        component.onLocationSelected({ lat: 20.5, lon: -103.3, name: 'Test Location' });
      } catch (e) {
        // Leaflet DOM operations may fail in test
      }
      // Message should be set before Leaflet operations
      expect(component.message).toContain('Test Location');
    });
  });

  // ==================== Loading State ====================

  describe('Loading State', () => {
    it('should start with loading false', () => {
      expect(component.loading).toBeFalse();
    });

    it('should set loading true during loadData', async () => {
      let wasLoading = false;
      apiServiceSpy.getTiles.and.callFake(async () => {
        wasLoading = component.loading;
        return [];
      });

      await component.loadData();
      expect(wasLoading).toBeTrue();
    });

    it('should set loading false after loadData completes', async () => {
      await component.loadData();
      expect(component.loading).toBeFalse();
    });

    it('should set loading false after loadData fails', async () => {
      apiServiceSpy.getTiles.and.returnValue(Promise.reject(new Error('fail')));
      await component.loadData();
      expect(component.loading).toBeFalse();
    });
  });
});
