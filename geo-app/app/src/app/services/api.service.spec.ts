import { TestBed } from '@angular/core/testing';
import { ApiService } from './api.service';
import { LoggerService } from './logger.service';

// Mock environment
const mockEnvironment = {
  supabaseUrl: 'https://mock-supabase.example.com',
  supabaseAnonKey: 'mock-anon-key',
  n8nBase: 'https://mock-n8n.example.com',
  mlApiBase: 'http://mock-ml-api.example.com',
  gridDegStep: 0.005,
  production: false
};

// Mock Supabase query builder
function createMockQueryBuilder(mockData: any = [], mockError: any = null) {
  const builder: any = {
    select: jasmine.createSpy('select').and.callFake(() => builder),
    from: jasmine.createSpy('from').and.callFake(() => builder),
    eq: jasmine.createSpy('eq').and.callFake(() => builder),
    gte: jasmine.createSpy('gte').and.callFake(() => builder),
    in: jasmine.createSpy('in').and.callFake(() => builder),
    range: jasmine.createSpy('range').and.callFake(() => builder),
    order: jasmine.createSpy('order').and.callFake(() => builder),
    limit: jasmine.createSpy('limit').and.callFake(() => builder),
    then: undefined as any
  };
  // Make it thenable (Promise-like) so await resolves it
  const result = { data: mockData, error: mockError };
  builder.then = (resolve: any, reject: any) => {
    return Promise.resolve(result).then(resolve, reject);
  };
  return builder;
}

describe('ApiService', () => {
  let service: ApiService;
  let loggerSpy: jasmine.SpyObj<LoggerService>;
  let mockSupabaseFrom: jasmine.Spy;

  beforeEach(() => {
    loggerSpy = jasmine.createSpyObj('LoggerService', [
      'log', 'warn', 'error', 'info', 'success', 'sensitive'
    ]);

    TestBed.configureTestingModule({
      providers: [
        ApiService,
        { provide: LoggerService, useValue: loggerSpy }
      ]
    });

    service = TestBed.inject(ApiService);

    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  // ==================== Initialization ====================

  describe('Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should have a supabase client initialized', () => {
      // The service constructor calls initSupabase which creates a SupabaseClient
      expect((service as any).supabase).toBeTruthy();
    });
  });

  // ==================== Cache Helpers ====================

  describe('Cache - setCache / getCache', () => {
    it('should store and retrieve data from cache', () => {
      const testData = { items: [1, 2, 3], name: 'test' };
      (service as any).setCache('test_key', testData, 300000);

      const cached = (service as any).getCache('test_key');
      expect(cached).toEqual(testData);
    });

    it('should return null for non-existent cache key', () => {
      const cached = (service as any).getCache('nonexistent_key');
      expect(cached).toBeNull();
    });

    it('should return null for expired cache', () => {
      const testData = { value: 42 };
      // Manually set an expired cache item
      const expiredItem = {
        data: testData,
        timestamp: Date.now() - 600000, // 10 minutes ago
        ttl: 300000 // 5 minute TTL
      };
      localStorage.setItem('expired_key', JSON.stringify(expiredItem));

      const cached = (service as any).getCache('expired_key');
      expect(cached).toBeNull();
    });

    it('should remove expired cache items from localStorage', () => {
      const expiredItem = {
        data: 'old_data',
        timestamp: Date.now() - 600000,
        ttl: 300000
      };
      localStorage.setItem('expired_key', JSON.stringify(expiredItem));

      (service as any).getCache('expired_key');
      expect(localStorage.getItem('expired_key')).toBeNull();
    });

    it('should handle localStorage errors gracefully in setCache', () => {
      // Spy on localStorage.setItem to throw
      spyOn(localStorage, 'setItem').and.throwError('QuotaExceededError');

      expect(() => {
        (service as any).setCache('key', { big: 'data' });
      }).not.toThrow();
      expect(loggerSpy.warn).toHaveBeenCalled();
    });

    it('should handle corrupted localStorage data gracefully', () => {
      localStorage.setItem('corrupted_key', 'not-valid-json{{{');

      const result = (service as any).getCache('corrupted_key');
      expect(result).toBeNull();
      expect(loggerSpy.warn).toHaveBeenCalled();
    });

    it('should use default TTL of 300000ms', () => {
      (service as any).setCache('default_ttl_key', 'data');

      const stored = JSON.parse(localStorage.getItem('default_ttl_key')!);
      expect(stored.ttl).toBe(300000);
    });

    it('should use custom TTL when provided', () => {
      (service as any).setCache('custom_ttl_key', 'data', 60000);

      const stored = JSON.parse(localStorage.getItem('custom_ttl_key')!);
      expect(stored.ttl).toBe(60000);
    });
  });

  // ==================== clearCache ====================

  describe('clearCache', () => {
    it('should clear all api_ prefixed keys from localStorage', () => {
      localStorage.setItem('api_heatmap_all', JSON.stringify({ data: 1 }));
      localStorage.setItem('api_stats_by_city', JSON.stringify({ data: 2 }));
      localStorage.setItem('other_key', 'keep_me');

      service.clearCache();

      expect(localStorage.getItem('api_heatmap_all')).toBeNull();
      expect(localStorage.getItem('api_stats_by_city')).toBeNull();
      expect(localStorage.getItem('other_key')).toBe('keep_me');
    });

    it('should clear only matching pattern when provided', () => {
      localStorage.setItem('api_heatmap_cdmx', JSON.stringify({ data: 1 }));
      localStorage.setItem('api_heatmap_gdl', JSON.stringify({ data: 2 }));
      localStorage.setItem('api_stats_by_city', JSON.stringify({ data: 3 }));

      service.clearCache('heatmap');

      expect(localStorage.getItem('api_heatmap_cdmx')).toBeNull();
      expect(localStorage.getItem('api_heatmap_gdl')).toBeNull();
      expect(localStorage.getItem('api_stats_by_city')).not.toBeNull();
    });

    it('should handle localStorage errors in clearCache gracefully', () => {
      spyOn(Object, 'keys').and.throwError('localStorage error');

      expect(() => service.clearCache()).not.toThrow();
      expect(loggerSpy.warn).toHaveBeenCalled();
    });
  });

  // ==================== Retry Logic ====================

  describe('retryWithBackoff', () => {
    it('should return result on first successful attempt', async () => {
      const fn = jasmine.createSpy('fn').and.returnValue(Promise.resolve('success'));

      const result = await (service as any).retryWithBackoff(fn, 3, 10);
      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should retry on failure and succeed eventually', async () => {
      let callCount = 0;
      const fn = jasmine.createSpy('fn').and.callFake(() => {
        callCount++;
        if (callCount < 3) {
          return Promise.reject(new Error('temporary failure'));
        }
        return Promise.resolve('success after retries');
      });

      const result = await (service as any).retryWithBackoff(fn, 3, 10);
      expect(result).toBe('success after retries');
      expect(fn).toHaveBeenCalledTimes(3);
    });

    it('should throw after all retries are exhausted', async () => {
      const fn = jasmine.createSpy('fn').and.returnValue(
        Promise.reject(new Error('persistent failure'))
      );

      try {
        await (service as any).retryWithBackoff(fn, 2, 10);
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('persistent failure');
      }
      // 1 initial + 2 retries = 3 total
      expect(fn).toHaveBeenCalledTimes(3);
    });

    it('should log warnings on intermediate failures', async () => {
      let callCount = 0;
      const fn = jasmine.createSpy('fn').and.callFake(() => {
        callCount++;
        if (callCount < 2) {
          return Promise.reject(new Error('fail'));
        }
        return Promise.resolve('ok');
      });

      await (service as any).retryWithBackoff(fn, 2, 10);
      expect(loggerSpy.warn).toHaveBeenCalled();
    });

    it('should log error when all attempts fail', async () => {
      const fn = jasmine.createSpy('fn').and.returnValue(
        Promise.reject(new Error('always fails'))
      );

      try {
        await (service as any).retryWithBackoff(fn, 1, 10);
      } catch (e) {
        // expected
      }
      expect(loggerSpy.error).toHaveBeenCalled();
    });
  });

  // ==================== getTiles ====================

  describe('getTiles', () => {
    it('should call supabase from iainmobiliaria_grid_tiles', async () => {
      const mockData = [
        { id: 1, lat: 20.5, lon: -103.3, price_m2_avg: 15000 },
        { id: 2, lat: 20.6, lon: -103.4, price_m2_avg: 18000 }
      ];
      const mockBuilder = createMockQueryBuilder(mockData);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      const result = await service.getTiles(100, 0);

      expect((service as any).supabase.from).toHaveBeenCalledWith('iainmobiliaria_grid_tiles');
      expect(mockBuilder.select).toHaveBeenCalledWith('*');
      expect(result).toEqual(mockData);
    });

    it('should use default limit of 1000 and offset of 0', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getTiles();
      expect(mockBuilder.range).toHaveBeenCalledWith(0, 999);
    });

    it('should throw and log error when supabase returns error', async () => {
      const mockError = { message: 'Database error', code: '500' };
      const mockBuilder = createMockQueryBuilder(null, mockError);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      try {
        await service.getTiles();
        fail('Should have thrown');
      } catch (error) {
        expect(error).toEqual(mockError);
      }
      expect(loggerSpy.error).toHaveBeenCalledWith('Error obteniendo tiles', mockError);
    });

    it('should return empty array when data is null', async () => {
      const mockBuilder = createMockQueryBuilder(null, null);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      const result = await service.getTiles();
      expect(result).toEqual([]);
    });
  });

  // ==================== getAmenities ====================

  describe('getAmenities', () => {
    it('should fetch all amenities with no filters', async () => {
      const mockData = [{ id: 1, name: 'School', amenity_type: 'school' }];
      const mockBuilder = createMockQueryBuilder(mockData);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      const result = await service.getAmenities({});

      expect((service as any).supabase.from).toHaveBeenCalledWith('iainmobiliaria_amenities');
      expect(result).toEqual(mockData);
    });

    it('should apply city filter', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getAmenities({ city: 'Guadalajara' });
      expect(mockBuilder.eq).toHaveBeenCalledWith('city', 'Guadalajara');
    });

    it('should apply state filter', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getAmenities({ state: 'Jalisco' });
      expect(mockBuilder.eq).toHaveBeenCalledWith('state', 'Jalisco');
    });

    it('should apply types filter with IN clause', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getAmenities({ types: ['school', 'hospital'] });
      expect(mockBuilder.in).toHaveBeenCalledWith('amenity_type', ['school', 'hospital']);
    });

    it('should NOT apply types filter when array is empty', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getAmenities({ types: [] });
      expect(mockBuilder.in).not.toHaveBeenCalled();
    });

    it('should apply multiple filters simultaneously', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getAmenities({
        city: 'Monterrey',
        state: 'Nuevo Leon',
        types: ['hospital']
      });

      expect(mockBuilder.eq).toHaveBeenCalledWith('city', 'Monterrey');
      expect(mockBuilder.eq).toHaveBeenCalledWith('state', 'Nuevo Leon');
      expect(mockBuilder.in).toHaveBeenCalledWith('amenity_type', ['hospital']);
    });

    it('should throw on supabase error', async () => {
      const mockError = { message: 'Query failed' };
      const mockBuilder = createMockQueryBuilder(null, mockError);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      try {
        await service.getAmenities({});
        fail('Should have thrown');
      } catch (error) {
        expect(error).toEqual(mockError);
      }
    });
  });

  // ==================== uploadComparablesCsv ====================

  describe('uploadComparablesCsv', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
    });

    it('should POST file as FormData', async () => {
      const mockFile = new File(['col1,col2\nval1,val2'], 'test.csv', { type: 'text/csv' });
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ ok: true, inserted: 5, rejects: 0 })
      };
      fetchSpy.and.returnValue(Promise.resolve(mockResponse));

      const result = await service.uploadComparablesCsv(mockFile);

      expect(fetchSpy).toHaveBeenCalled();
      const fetchArgs = fetchSpy.calls.first().args;
      expect(fetchArgs[0]).toContain('/ingest-csv');
      expect(fetchArgs[1].method).toBe('POST');
      expect(fetchArgs[1].body instanceof FormData).toBeTrue();
      expect(result).toEqual({ ok: true, inserted: 5, rejects: 0 });
    });

    it('should throw on HTTP error response', async () => {
      const mockFile = new File(['data'], 'test.csv', { type: 'text/csv' });
      fetchSpy.and.returnValue(Promise.resolve({
        ok: false,
        status: 500
      }));

      try {
        await service.uploadComparablesCsv(mockFile);
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toContain('500');
      }
      expect(loggerSpy.error).toHaveBeenCalled();
    });

    it('should throw on network error', async () => {
      const mockFile = new File(['data'], 'test.csv', { type: 'text/csv' });
      fetchSpy.and.returnValue(Promise.reject(new Error('Network error')));

      try {
        await service.uploadComparablesCsv(mockFile);
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Network error');
      }
      expect(loggerSpy.error).toHaveBeenCalledWith('Error subiendo CSV', jasmine.any(Error));
    });
  });

  // ==================== predictPriceML ====================

  describe('predictPriceML', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
    });

    it('should POST prediction params and return result', async () => {
      const mockResult = {
        predicted_price_m2: 15000,
        predicted_total_price: 3000000,
        plusvalia_score: 75.5,
        growth_potential: 'alto',
        confidence: 85.0,
        model_version: '1.0',
        features_used: { area_m2: 200 },
        timestamp: '2026-03-23T00:00:00Z'
      };
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResult)
      }));

      const result = await service.predictPriceML(20.5, -103.3, 200, 'Guadalajara', 'Jalisco');

      expect(fetchSpy).toHaveBeenCalled();
      const args = fetchSpy.calls.first().args;
      expect(args[0]).toContain('/predict');
      const body = JSON.parse(args[1].body);
      expect(body.lat).toBe(20.5);
      expect(body.lon).toBe(-103.3);
      expect(body.area_m2).toBe(200);
      expect(body.city).toBe('Guadalajara');
      expect(body.state).toBe('Jalisco');
      expect(result).toEqual(mockResult);
    });

    it('should throw on HTTP error', async () => {
      fetchSpy.and.returnValue(Promise.resolve({ ok: false, status: 422 }));

      try {
        await service.predictPriceML(0, 0, 100, 'Test', 'Test');
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toContain('422');
      }
    });

    it('should log error and rethrow on failure', async () => {
      fetchSpy.and.returnValue(Promise.reject(new Error('ML API down')));

      try {
        await service.predictPriceML(20, -103, 100, 'GDL', 'JAL');
      } catch (e) {
        // expected
      }
      expect(loggerSpy.error).toHaveBeenCalledWith('Error en predicción ML', jasmine.any(Error));
    });
  });

  // ==================== getPredictionsHeatmap ====================

  describe('getPredictionsHeatmap', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
      localStorage.clear();
    });

    it('should return cached data if available', async () => {
      const cachedData = { points: [[20, -103, 0.8]] as [number, number, number][], count: 1, filters: {} };
      const cacheItem = {
        data: cachedData,
        timestamp: Date.now(),
        ttl: 300000
      };
      localStorage.setItem('api_heatmap_all_0_10000', JSON.stringify(cacheItem));

      const result = await service.getPredictionsHeatmap();

      expect(fetchSpy).not.toHaveBeenCalled();
      expect(result).toEqual(cachedData);
      expect(loggerSpy.success).toHaveBeenCalledWith('Heatmap cargado desde cache');
    });

    it('should fetch from API when cache misses', async () => {
      const mockData = { points: [[20.5, -103.3, 0.9]] as [number, number, number][], count: 1, filters: {} };
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockData)
      }));

      const result = await service.getPredictionsHeatmap('CDMX', 50, 5000);

      expect(fetchSpy).toHaveBeenCalled();
      const url = fetchSpy.calls.first().args[0];
      expect(url).toContain('/predictions/heatmap');
      expect(url).toContain('city=CDMX');
      expect(url).toContain('min_score=50');
      expect(url).toContain('limit=5000');
      expect(result).toEqual(mockData);
    });

    it('should cache the fetched data', async () => {
      const mockData = { points: [] as [number, number, number][], count: 0, filters: {} };
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockData)
      }));

      await service.getPredictionsHeatmap();

      // Check that something was stored in localStorage with api_heatmap prefix
      const keys = Object.keys(localStorage);
      const heatmapKey = keys.find(k => k.startsWith('api_heatmap'));
      expect(heatmapKey).toBeTruthy();
    });

    it('should use retry logic on failure', async () => {
      let callCount = 0;
      fetchSpy.and.callFake(() => {
        callCount++;
        if (callCount < 2) {
          return Promise.reject(new Error('timeout'));
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ points: [], count: 0 })
        });
      });

      const result = await service.getPredictionsHeatmap();
      expect(callCount).toBeGreaterThanOrEqual(2);
      expect(result).toBeTruthy();
    });
  });

  // ==================== getPredictionsInBbox ====================

  describe('getPredictionsInBbox', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
    });

    it('should pass bounding box parameters in URL', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ predictions: [], count: 0, bbox: {} })
      }));

      await service.getPredictionsInBbox(19.0, 20.0, -104.0, -103.0, 1000);

      const url = fetchSpy.calls.first().args[0];
      expect(url).toContain('min_lat=19');
      expect(url).toContain('max_lat=20');
      expect(url).toContain('min_lon=-104');
      expect(url).toContain('max_lon=-103');
      expect(url).toContain('limit=1000');
    });

    it('should return predictions data', async () => {
      const mockData = {
        predictions: [{ lat: 19.5, lon: -103.5, score: 80 }],
        count: 1,
        bbox: { min_lat: 19, max_lat: 20, min_lon: -104, max_lon: -103 }
      };
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockData)
      }));

      const result = await service.getPredictionsInBbox(19, 20, -104, -103);
      expect(result).toEqual(mockData);
    });

    it('should throw and log on error', async () => {
      fetchSpy.and.returnValue(Promise.resolve({ ok: false, status: 500 }));

      try {
        await service.getPredictionsInBbox(19, 20, -104, -103);
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toContain('500');
      }
      expect(loggerSpy.error).toHaveBeenCalledWith(
        'Error obteniendo predicciones en bbox',
        jasmine.any(Error)
      );
    });
  });

  // ==================== getPredictions (Supabase) ====================

  describe('getPredictions', () => {
    it('should query with city filter', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getPredictions({ city: 'Monterrey' });
      expect(mockBuilder.eq).toHaveBeenCalledWith('city', 'Monterrey');
    });

    it('should query with minScore filter (gte)', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getPredictions({ minScore: 50 });
      expect(mockBuilder.gte).toHaveBeenCalledWith('plusvalia_score', 50);
    });

    it('should use default limit of 100', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getPredictions({});
      expect(mockBuilder.limit).toHaveBeenCalledWith(100);
    });

    it('should use provided limit', async () => {
      const mockBuilder = createMockQueryBuilder([]);
      spyOn((service as any).supabase, 'from').and.returnValue(mockBuilder);

      await service.getPredictions({ limit: 50 });
      expect(mockBuilder.limit).toHaveBeenCalledWith(50);
    });
  });

  // ==================== getMLStats ====================

  describe('getMLStats', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
    });

    it('should fetch stats from ML API', async () => {
      const mockStats = { total_predictions: 5000, model_accuracy: 0.85 };
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockStats)
      }));

      const result = await service.getMLStats();
      expect(result).toEqual(mockStats);
      expect(fetchSpy.calls.first().args[0]).toContain('/stats');
    });

    it('should throw on HTTP error', async () => {
      fetchSpy.and.returnValue(Promise.resolve({ ok: false, status: 503 }));

      try {
        await service.getMLStats();
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toContain('503');
      }
    });
  });

  // ==================== getPredictionsHistory ====================

  describe('getPredictionsHistory', () => {
    let fetchSpy: jasmine.Spy;

    beforeEach(() => {
      fetchSpy = spyOn(window, 'fetch');
    });

    it('should include limit, city, and state in URL', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      await service.getPredictionsHistory(50, 'Guadalajara', 'Jalisco');

      const url = fetchSpy.calls.first().args[0];
      expect(url).toContain('limit=50');
      expect(url).toContain('city=Guadalajara');
      expect(url).toContain('state=Jalisco');
    });

    it('should use default limit of 100', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      await service.getPredictionsHistory();

      const url = fetchSpy.calls.first().args[0];
      expect(url).toContain('limit=100');
    });

    it('should omit optional city and state when not provided', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      }));

      await service.getPredictionsHistory(100);

      const url = fetchSpy.calls.first().args[0];
      expect(url).not.toContain('city=');
      expect(url).not.toContain('state=');
    });
  });
});
