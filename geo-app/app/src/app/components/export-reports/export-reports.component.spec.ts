import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ExportReportsComponent } from './export-reports.component';

describe('ExportReportsComponent', () => {
  let component: ExportReportsComponent;
  let fixture: ComponentFixture<ExportReportsComponent>;

  const mockPredictions = [
    [20.5, -103.3, 0.85],
    [20.6, -103.4, 0.72],
    [20.7, -103.5, 0.45],
    [20.8, -103.6, 0.30],
    [20.9, -103.7, 0.92],
    [21.0, -103.8, 0.15],
    [21.1, -103.9, 0.60],
    [21.2, -104.0, 0.55],
    [21.3, -104.1, 0.78],
    [21.4, -104.2, 0.88],
    [21.5, -104.3, 0.25],
    [21.6, -104.4, 0.10],
  ];

  const mockCitiesStats = [
    {
      city: 'Guadalajara',
      predictions_count: 5000,
      avg_price_m2: 15000,
      min_price_m2: 5000,
      max_price_m2: 30000,
      avg_plusvalia_score: 65.5,
      potential_distribution: { alto: 1500, medio: 2000, bajo: 1500 }
    },
    {
      city: 'Monterrey',
      predictions_count: 3000,
      avg_price_m2: 18000,
      min_price_m2: 7000,
      max_price_m2: 35000,
      avg_plusvalia_score: 70.2,
      potential_distribution: { alto: 1200, medio: 1000, bajo: 800 }
    }
  ];

  let downloadFileSpy: jasmine.Spy;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExportReportsComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ExportReportsComponent);
    component = fixture.componentInstance;
    component.predictions = mockPredictions;
    component.citiesStats = mockCitiesStats;

    // Spy on the private downloadFile method to prevent actual file downloads
    downloadFileSpy = spyOn(component as any, 'downloadFile');
    spyOn(window, 'alert');

    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with isVisible false', () => {
    expect(component.isVisible).toBeFalse();
  });

  it('should initialize with isExporting false', () => {
    expect(component.isExporting).toBeFalse();
  });

  // ==================== Toggle Visibility ====================

  describe('toggleVisibility', () => {
    it('should toggle from false to true', () => {
      component.toggleVisibility();
      expect(component.isVisible).toBeTrue();
    });

    it('should toggle from true to false', () => {
      component.isVisible = true;
      component.toggleVisibility();
      expect(component.isVisible).toBeFalse();
    });
  });

  // ==================== Export CSV ====================

  describe('exportToCSV', () => {
    it('should call downloadFile with CSV content', async () => {
      await component.exportToCSV();

      expect(downloadFileSpy).toHaveBeenCalled();
      const args = downloadFileSpy.calls.first().args;
      expect(args[1]).toBe('predicciones-plusvalia.csv');
      expect(args[2]).toBe('text/csv');
    });

    it('should generate CSV with correct headers', async () => {
      await component.exportToCSV();

      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain('ID');
      expect(csvContent).toContain('Latitud');
      expect(csvContent).toContain('Longitud');
      expect(csvContent).toContain('Score Plusvalía');
      expect(csvContent).toContain('Nivel');
      expect(csvContent).toContain('Precio Estimado/m²');
    });

    it('should include all predictions in CSV', async () => {
      await component.exportToCSV();

      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      const lines = csvContent.split('\n');
      // 1 header + 12 data rows
      expect(lines.length).toBe(13);
    });

    it('should set isExporting to false after completion', async () => {
      await component.exportToCSV();
      expect(component.isExporting).toBeFalse();
    });

    it('should show success alert', async () => {
      await component.exportToCSV();
      expect(window.alert).toHaveBeenCalledWith(jasmine.stringContaining('exportado exitosamente'));
    });

    it('should handle errors gracefully', async () => {
      component.predictions = null as any; // Force an error
      await component.exportToCSV();
      expect(component.isExporting).toBeFalse();
      expect(window.alert).toHaveBeenCalledWith(jasmine.stringContaining('Error'));
    });
  });

  // ==================== Export Top 10 ====================

  describe('exportTop10ToCSV', () => {
    it('should export top 10 sorted by score descending', async () => {
      await component.exportTop10ToCSV();

      expect(downloadFileSpy).toHaveBeenCalled();
      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain('TOP 10');
      expect(csvContent).toContain('Ranking');
    });

    it('should include Google Maps links', async () => {
      await component.exportTop10ToCSV();

      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain('https://www.google.com/maps');
    });

    it('should export with correct filename', async () => {
      await component.exportTop10ToCSV();

      const filename = downloadFileSpy.calls.first().args[1];
      expect(filename).toBe('top10-oportunidades.csv');
    });

    it('should include total predictions count in header', async () => {
      await component.exportTop10ToCSV();

      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain(`${mockPredictions.length}`);
    });

    it('should set isExporting to false after completion', async () => {
      await component.exportTop10ToCSV();
      expect(component.isExporting).toBeFalse();
    });
  });

  // ==================== Export Stats CSV ====================

  describe('exportStatsToCSV', () => {
    it('should export city statistics', async () => {
      await component.exportStatsToCSV();

      expect(downloadFileSpy).toHaveBeenCalled();
      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain('Guadalajara');
      expect(csvContent).toContain('Monterrey');
    });

    it('should include correct headers', async () => {
      await component.exportStatsToCSV();

      const csvContent = downloadFileSpy.calls.first().args[0] as string;
      expect(csvContent).toContain('Ciudad');
      expect(csvContent).toContain('Total Predicciones');
      expect(csvContent).toContain('Precio Promedio');
      expect(csvContent).toContain('Score Promedio');
    });

    it('should export with correct filename', async () => {
      await component.exportStatsToCSV();

      const filename = downloadFileSpy.calls.first().args[1];
      expect(filename).toBe('estadisticas-ciudades.csv');
    });

    it('should set isExporting to false after completion', async () => {
      await component.exportStatsToCSV();
      expect(component.isExporting).toBeFalse();
    });

    it('should handle errors if citiesStats is empty', async () => {
      component.citiesStats = [];
      await component.exportStatsToCSV();
      expect(component.isExporting).toBeFalse();
    });
  });

  // ==================== Export Complete Report ====================

  describe('exportCompleteReport', () => {
    it('should generate a text report', async () => {
      await component.exportCompleteReport();

      expect(downloadFileSpy).toHaveBeenCalled();
      const filename = downloadFileSpy.calls.first().args[1];
      expect(filename).toBe('reporte-completo-plusvalia.txt');
      expect(downloadFileSpy.calls.first().args[2]).toBe('text/plain');
    });

    it('should include executive summary', async () => {
      await component.exportCompleteReport();

      const report = downloadFileSpy.calls.first().args[0] as string;
      expect(report).toContain('RESUMEN EJECUTIVO');
      expect(report).toContain('Total de Predicciones');
    });

    it('should include potential distribution', async () => {
      await component.exportCompleteReport();

      const report = downloadFileSpy.calls.first().args[0] as string;
      expect(report).toContain('Alto');
      expect(report).toContain('Medio');
      expect(report).toContain('Bajo');
    });

    it('should include top 10 opportunities', async () => {
      await component.exportCompleteReport();

      const report = downloadFileSpy.calls.first().args[0] as string;
      expect(report).toContain('TOP 10');
      expect(report).toContain('Google Maps');
    });

    it('should include city analysis', async () => {
      await component.exportCompleteReport();

      const report = downloadFileSpy.calls.first().args[0] as string;
      expect(report).toContain('Guadalajara');
      expect(report).toContain('Monterrey');
    });

    it('should set isExporting to false after completion', async () => {
      await component.exportCompleteReport();
      expect(component.isExporting).toBeFalse();
    });
  });

  // ==================== Copy to Clipboard ====================

  describe('copyStatsToClipboard', () => {
    it('should call navigator.clipboard.writeText', async () => {
      const writeTextSpy = spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());

      await component.copyStatsToClipboard();

      expect(writeTextSpy).toHaveBeenCalled();
      const copiedText = writeTextSpy.calls.first().args[0];
      expect(copiedText).toContain('ESTADÍSTICAS');
    });

    it('should include prediction counts in clipboard text', async () => {
      spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());

      await component.copyStatsToClipboard();

      const copiedText = (navigator.clipboard.writeText as jasmine.Spy).calls.first().args[0];
      expect(copiedText).toContain(mockPredictions.length.toLocaleString());
    });

    it('should show success alert after copying', async () => {
      spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());

      await component.copyStatsToClipboard();

      expect(window.alert).toHaveBeenCalledWith(jasmine.stringContaining('copiadas'));
    });

    it('should handle clipboard errors gracefully', async () => {
      spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.reject('Not allowed'));

      await component.copyStatsToClipboard();

      expect(window.alert).toHaveBeenCalledWith(jasmine.stringContaining('Error'));
    });
  });

  // ==================== getPotentialLevel (private) ====================

  describe('getPotentialLevel (private)', () => {
    it('should return Alto for score >= 66', () => {
      expect((component as any).getPotentialLevel(66)).toBe('Alto');
      expect((component as any).getPotentialLevel(100)).toBe('Alto');
      expect((component as any).getPotentialLevel(80)).toBe('Alto');
    });

    it('should return Medio for score >= 33 and < 66', () => {
      expect((component as any).getPotentialLevel(33)).toBe('Medio');
      expect((component as any).getPotentialLevel(50)).toBe('Medio');
      expect((component as any).getPotentialLevel(65.9)).toBe('Medio');
    });

    it('should return Bajo for score < 33', () => {
      expect((component as any).getPotentialLevel(0)).toBe('Bajo');
      expect((component as any).getPotentialLevel(32.9)).toBe('Bajo');
      expect((component as any).getPotentialLevel(10)).toBe('Bajo');
    });
  });
});
