import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AddressSearchComponent } from './address-search.component';

describe('AddressSearchComponent', () => {
  let component: AddressSearchComponent;
  let fixture: ComponentFixture<AddressSearchComponent>;
  let fetchSpy: jasmine.Spy;

  const mockSearchResults = [
    {
      display_name: 'Guadalajara, Jalisco, Mexico',
      lat: '20.6597',
      lon: '-103.3496',
      type: 'city',
      address: {
        city: 'Guadalajara',
        state: 'Jalisco',
        country: 'Mexico'
      }
    },
    {
      display_name: 'Colonia Centro, Guadalajara, Jalisco',
      lat: '20.6757',
      lon: '-103.3467',
      type: 'neighbourhood',
      address: {
        suburb: 'Centro',
        city: 'Guadalajara',
        state: 'Jalisco'
      }
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddressSearchComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AddressSearchComponent);
    component = fixture.componentInstance;
    fetchSpy = spyOn(window, 'fetch');
    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty search query', () => {
    expect(component.searchQuery).toBe('');
  });

  it('should initialize with empty results', () => {
    expect(component.searchResults).toEqual([]);
  });

  it('should initialize with isSearching false', () => {
    expect(component.isSearching).toBeFalse();
  });

  it('should initialize with showResults false', () => {
    expect(component.showResults).toBeFalse();
  });

  it('should initialize with empty error message', () => {
    expect(component.errorMessage).toBe('');
  });

  // ==================== Search with Valid Query ====================

  describe('searchAddress - valid query', () => {
    it('should search and populate results', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSearchResults)
      }));

      component.searchQuery = 'Guadalajara';
      await component.searchAddress();

      expect(component.searchResults.length).toBe(2);
      expect(component.showResults).toBeTrue();
      expect(component.errorMessage).toBe('');
    });

    it('should call Nominatim API with correct URL', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      component.searchQuery = 'Monterrey Centro';
      await component.searchAddress();

      const url = fetchSpy.calls.first().args[0] as string;
      expect(url).toContain('nominatim.openstreetmap.org');
      expect(url).toContain('Monterrey%20Centro');
      expect(url).toContain('countrycodes=mx');
      expect(url).toContain('limit=8');
      expect(url).toContain('addressdetails=1');
    });

    it('should include User-Agent header', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      component.searchQuery = 'Test';
      await component.searchAddress();

      const headers = fetchSpy.calls.first().args[1].headers;
      expect(headers['User-Agent']).toBeTruthy();
    });

    it('should set isSearching to true during search', async () => {
      let searchingDuringCall = false;
      fetchSpy.and.callFake(() => {
        searchingDuringCall = component.isSearching;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      });

      component.searchQuery = 'Test query';
      await component.searchAddress();

      expect(searchingDuringCall).toBeTrue();
    });

    it('should set isSearching to false after search', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      component.searchQuery = 'Test query';
      await component.searchAddress();

      expect(component.isSearching).toBeFalse();
    });

    it('should show error when no results found', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      component.searchQuery = 'NonExistentPlace12345';
      await component.searchAddress();

      expect(component.errorMessage).toContain('No se encontraron');
      expect(component.searchResults).toEqual([]);
    });
  });

  // ==================== Search with Short Query ====================

  describe('searchAddress - short query', () => {
    it('should not search with empty query', async () => {
      component.searchQuery = '';
      await component.searchAddress();

      expect(fetchSpy).not.toHaveBeenCalled();
      expect(component.errorMessage).toContain('3 caracteres');
    });

    it('should not search with 1 character', async () => {
      component.searchQuery = 'A';
      await component.searchAddress();

      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('should not search with 2 characters', async () => {
      component.searchQuery = 'AB';
      await component.searchAddress();

      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('should search with exactly 3 characters', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      component.searchQuery = 'ABC';
      await component.searchAddress();

      expect(fetchSpy).toHaveBeenCalled();
    });

    it('should not search with whitespace-only query', async () => {
      component.searchQuery = '   ';
      await component.searchAddress();

      expect(fetchSpy).not.toHaveBeenCalled();
    });
  });

  // ==================== Clear Search ====================

  describe('clearSearch', () => {
    it('should clear search query', () => {
      component.searchQuery = 'Guadalajara';
      component.clearSearch();
      expect(component.searchQuery).toBe('');
    });

    it('should clear search results', () => {
      component.searchResults = mockSearchResults;
      component.clearSearch();
      expect(component.searchResults).toEqual([]);
    });

    it('should hide results', () => {
      component.showResults = true;
      component.clearSearch();
      expect(component.showResults).toBeFalse();
    });

    it('should clear error message', () => {
      component.errorMessage = 'Some error';
      component.clearSearch();
      expect(component.errorMessage).toBe('');
    });
  });

  // ==================== Select Result ====================

  describe('selectResult', () => {
    it('should emit locationSelected event with parsed coordinates', () => {
      spyOn(component.locationSelected, 'emit');

      component.selectResult(mockSearchResults[0]);

      expect(component.locationSelected.emit).toHaveBeenCalledWith({
        lat: 20.6597,
        lon: -103.3496,
        name: 'Guadalajara, Jalisco, Mexico'
      });
    });

    it('should hide results after selection', () => {
      spyOn(component.locationSelected, 'emit');
      component.showResults = true;

      component.selectResult(mockSearchResults[0]);

      expect(component.showResults).toBeFalse();
    });

    it('should update search query with selected name', () => {
      spyOn(component.locationSelected, 'emit');

      component.selectResult(mockSearchResults[0]);

      expect(component.searchQuery).toBe('Guadalajara, Jalisco, Mexico');
    });

    it('should parse lat/lon as numbers', () => {
      spyOn(component.locationSelected, 'emit');

      component.selectResult(mockSearchResults[0]);

      const emittedValue = (component.locationSelected.emit as jasmine.Spy).calls.first().args[0];
      expect(typeof emittedValue.lat).toBe('number');
      expect(typeof emittedValue.lon).toBe('number');
    });
  });

  // ==================== Error Handling ====================

  describe('Error handling', () => {
    it('should display error message on HTTP error', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: false,
        status: 500
      }));

      component.searchQuery = 'Test query';
      await component.searchAddress();

      expect(component.errorMessage).toContain('Error');
    });

    it('should display error message on network failure', async () => {
      fetchSpy.and.returnValue(Promise.reject(new Error('Network error')));

      component.searchQuery = 'Test query';
      await component.searchAddress();

      expect(component.errorMessage).toContain('Error');
      expect(component.isSearching).toBeFalse();
    });
  });

  // ==================== Key Press ====================

  describe('onKeyPress', () => {
    it('should call searchAddress on Enter key', () => {
      spyOn(component, 'searchAddress');
      const event = new KeyboardEvent('keypress', { key: 'Enter' });

      component.onKeyPress(event);

      expect(component.searchAddress).toHaveBeenCalled();
    });

    it('should not call searchAddress on other keys', () => {
      spyOn(component, 'searchAddress');
      const event = new KeyboardEvent('keypress', { key: 'a' });

      component.onKeyPress(event);

      expect(component.searchAddress).not.toHaveBeenCalled();
    });
  });

  // ==================== getResultIcon ====================

  describe('getResultIcon', () => {
    it('should return house icon for "house" type', () => {
      expect(component.getResultIcon('house')).toBe('🏠');
    });

    it('should return default icon for unknown type', () => {
      const icon = component.getResultIcon('unknown_type');
      expect(icon).toBeTruthy();
    });

    it('should return city icon for "city" type', () => {
      const icon = component.getResultIcon('city');
      expect(icon).toBeTruthy();
    });
  });

  // ==================== formatAddress ====================

  describe('formatAddress', () => {
    it('should format address with road, suburb, city, state', () => {
      const result = {
        display_name: 'Full name',
        lat: '20',
        lon: '-103',
        type: 'road',
        address: {
          road: 'Av. Vallarta',
          suburb: 'Americana',
          city: 'Guadalajara',
          state: 'Jalisco'
        }
      };

      const formatted = component.formatAddress(result);
      expect(formatted).toContain('Av. Vallarta');
      expect(formatted).toContain('Americana');
      expect(formatted).toContain('Guadalajara');
      expect(formatted).toContain('Jalisco');
    });

    it('should include house number if available', () => {
      const result = {
        display_name: 'Full name',
        lat: '20',
        lon: '-103',
        type: 'house',
        address: {
          road: 'Calle 5',
          house_number: '42',
          city: 'Guadalajara',
          state: 'Jalisco'
        }
      };

      const formatted = component.formatAddress(result);
      expect(formatted).toContain('#42');
    });

    it('should fallback to display_name when no address parts', () => {
      const result = {
        display_name: 'Fallback Name',
        lat: '20',
        lon: '-103',
        type: 'other',
        address: {}
      };

      const formatted = component.formatAddress(result);
      expect(formatted).toBe('Fallback Name');
    });
  });
});
