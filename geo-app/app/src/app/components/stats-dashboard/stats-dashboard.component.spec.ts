import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StatsDashboardComponent } from './stats-dashboard.component';

describe('StatsDashboardComponent', () => {
  let component: StatsDashboardComponent;
  let fixture: ComponentFixture<StatsDashboardComponent>;

  // Sample predictions data: [lat, lon, normalizedScore]
  const mockPredictions = [
    [20.5, -103.3, 0.85],  // score=85, price=85000
    [20.6, -103.4, 0.72],  // score=72, price=72000
    [20.7, -103.5, 0.45],  // score=45, price=45000
    [20.8, -103.6, 0.30],  // score=30, price=30000
    [20.9, -103.7, 0.92],  // score=92, price=92000
    [21.0, -103.8, 0.15],  // score=15, price=15000
    [21.1, -103.9, 0.60],  // score=60, price=60000
    [21.2, -104.0, 0.55],  // score=55, price=55000
    [21.3, -104.1, 0.78],  // score=78, price=78000
    [21.4, -104.2, 0.88],  // score=88, price=88000
    [21.5, -104.3, 0.25],  // score=25, price=25000
    [21.6, -104.4, 0.10],  // score=10, price=10000
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatsDashboardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(StatsDashboardComponent);
    component = fixture.componentInstance;
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.isVisible).toBeFalse();
    expect(component.totalPredictions).toBe(0);
    expect(component.avgPrice).toBe(0);
    expect(component.avgScore).toBe(0);
    expect(component.topOpportunities).toEqual([]);
    expect(component.priceDistribution).toEqual([]);
    expect(component.potentialDistribution).toEqual([]);
  });

  // ==================== Visibility Toggle ====================

  it('should toggle visibility from false to true', () => {
    expect(component.isVisible).toBeFalse();
    component.toggleVisibility();
    expect(component.isVisible).toBeTrue();
  });

  it('should toggle visibility from true to false', () => {
    component.isVisible = true;
    component.toggleVisibility();
    expect(component.isVisible).toBeFalse();
  });

  it('should toggle visibility multiple times', () => {
    component.toggleVisibility();
    expect(component.isVisible).toBeTrue();
    component.toggleVisibility();
    expect(component.isVisible).toBeFalse();
    component.toggleVisibility();
    expect(component.isVisible).toBeTrue();
  });

  // ==================== Statistics Calculation ====================

  describe('calculateStatistics', () => {
    it('should calculate totalPredictions correctly', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      expect(component.totalPredictions).toBe(12);
    });

    it('should calculate avgPrice correctly', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      // avgPrice = sum of (score * 100000) / count
      const expectedSum = mockPredictions.reduce((s, p) => s + p[2] * 100000, 0);
      const expectedAvg = expectedSum / mockPredictions.length;
      expect(component.avgPrice).toBeCloseTo(expectedAvg, 0);
    });

    it('should calculate avgScore correctly', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const expectedSum = mockPredictions.reduce((s, p) => s + p[2] * 100, 0);
      const expectedAvg = expectedSum / mockPredictions.length;
      expect(component.avgScore).toBeCloseTo(expectedAvg, 0);
    });

    it('should not calculate statistics when predictions is empty', () => {
      component.predictions = [];
      component.ngOnInit();

      expect(component.totalPredictions).toBe(0);
      expect(component.avgPrice).toBe(0);
      expect(component.avgScore).toBe(0);
    });

    it('should not calculate statistics when predictions is null/undefined', () => {
      component.predictions = null as any;
      component.ngOnInit();

      expect(component.totalPredictions).toBe(0);
    });

    it('should recalculate on ngOnChanges', () => {
      component.predictions = mockPredictions;
      component.ngOnChanges();

      expect(component.totalPredictions).toBe(12);
    });
  });

  // ==================== Top 10 Opportunities ====================

  describe('Top 10 Opportunities', () => {
    it('should sort top opportunities by score descending', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      expect(component.topOpportunities.length).toBe(10);
      // Highest score is 0.92 (index 4 in mockPredictions)
      expect(component.topOpportunities[0].score).toBe('92.0');
    });

    it('should have correct rank numbering 1-10', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      component.topOpportunities.forEach((opp, idx) => {
        expect(opp.rank).toBe(idx + 1);
      });
    });

    it('should include lat and lon in top opportunities', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      // First opportunity should be the one with score 0.92 -> lat=20.9, lon=-103.7
      expect(component.topOpportunities[0].lat).toBe(20.9);
      expect(component.topOpportunities[0].lon).toBe(-103.7);
    });

    it('should handle fewer than 10 predictions', () => {
      component.predictions = mockPredictions.slice(0, 3);
      component.ngOnInit();

      expect(component.topOpportunities.length).toBe(3);
    });

    it('should handle exactly 10 predictions', () => {
      component.predictions = mockPredictions.slice(0, 10);
      component.ngOnInit();

      expect(component.topOpportunities.length).toBe(10);
    });

    it('should sort descending - second opportunity score <= first', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const firstScore = parseFloat(component.topOpportunities[0].score);
      const secondScore = parseFloat(component.topOpportunities[1].score);
      expect(firstScore).toBeGreaterThanOrEqual(secondScore);
    });
  });

  // ==================== Price Distribution ====================

  describe('Price Distribution', () => {
    it('should have 6 price ranges', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      expect(component.priceDistribution.length).toBe(6);
    });

    it('should have correct range labels', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const labels = component.priceDistribution.map(d => d.range);
      expect(labels).toEqual([
        '$0 - $20K',
        '$20K - $40K',
        '$40K - $60K',
        '$60K - $80K',
        '$80K - $100K',
        '$100K+'
      ]);
    });

    it('should distribute predictions into correct price ranges', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      // Verify total count across all ranges equals totalPredictions
      const totalDistributed = component.priceDistribution.reduce((s, d) => s + d.count, 0);
      expect(totalDistributed).toBe(component.totalPredictions);
    });

    it('should calculate percentages correctly', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      component.priceDistribution.forEach(dist => {
        const expectedPct = (dist.count / component.totalPredictions) * 100;
        expect(dist.percentage).toBeCloseTo(expectedPct, 5);
      });
    });

    it('should place score=0.15 (price=15000) in $0-$20K range', () => {
      component.predictions = [[20, -103, 0.15]];
      component.ngOnInit();

      expect(component.priceDistribution[0].count).toBe(1); // $0-$20K
    });
  });

  // ==================== Potential Distribution ====================

  describe('Potential Distribution', () => {
    it('should have 3 potential categories', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      expect(component.potentialDistribution.length).toBe(3);
    });

    it('should have Bajo/Medio/Alto labels', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const labels = component.potentialDistribution.map(d => d.label);
      expect(labels).toEqual(['Bajo', 'Medio', 'Alto']);
    });

    it('should assign correct colors', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      expect(component.potentialDistribution[0].color).toBe('#5B7065'); // Bajo = Pine
      expect(component.potentialDistribution[1].color).toBe('#D97706'); // Medio = amber
      expect(component.potentialDistribution[2].color).toBe('#DC2626'); // Alto = red
    });

    it('should categorize scores correctly (Bajo: 0-33, Medio: 33-66, Alto: 66-100)', () => {
      component.predictions = [
        [20, -103, 0.10],  // 10 -> Bajo
        [20, -103, 0.50],  // 50 -> Medio
        [20, -103, 0.80],  // 80 -> Alto
      ];
      component.ngOnInit();

      expect(component.potentialDistribution[0].count).toBe(1); // Bajo
      expect(component.potentialDistribution[1].count).toBe(1); // Medio
      expect(component.potentialDistribution[2].count).toBe(1); // Alto
    });

    it('should sum percentages to 100%', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const totalPct = component.potentialDistribution.reduce((s, d) => s + d.percentage, 0);
      expect(totalPct).toBeCloseTo(100, 0);
    });
  });

  // ==================== getMaxPercentage ====================

  describe('getMaxPercentage', () => {
    it('should return the highest percentage in priceDistribution', () => {
      component.predictions = mockPredictions;
      component.ngOnInit();

      const maxPct = component.getMaxPercentage();
      const expectedMax = Math.max(...component.priceDistribution.map(d => d.percentage));
      expect(maxPct).toBe(expectedMax);
    });
  });

  // ==================== Input Changes ====================

  describe('Input Changes', () => {
    it('should recalculate when predictions input changes', () => {
      component.predictions = [[20, -103, 0.5]];
      component.ngOnInit();
      expect(component.totalPredictions).toBe(1);

      component.predictions = [[20, -103, 0.5], [21, -104, 0.7]];
      component.ngOnChanges();
      expect(component.totalPredictions).toBe(2);
    });
  });
});
