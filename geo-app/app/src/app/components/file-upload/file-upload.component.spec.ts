import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FileUploadComponent } from './file-upload.component';
import { ApiService } from '../../services/api.service';

describe('FileUploadComponent', () => {
  let component: FileUploadComponent;
  let fixture: ComponentFixture<FileUploadComponent>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiServiceSpy = jasmine.createSpyObj('ApiService', ['uploadComparablesCsv']);

    await TestBed.configureTestingModule({
      imports: [FileUploadComponent],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FileUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with no selected file', () => {
    expect(component.selectedFile).toBeNull();
  });

  it('should initialize with uploading false', () => {
    expect(component.uploading).toBeFalse();
  });

  it('should initialize with empty upload message', () => {
    expect(component.uploadMessage).toBe('');
  });

  it('should initialize with empty upload status', () => {
    expect(component.uploadStatus).toBe('');
  });

  it('should not be disabled by default', () => {
    expect(component.disabled).toBeFalse();
  });

  // ==================== File Selection ====================

  describe('onFileSelected', () => {
    it('should accept CSV file by MIME type', () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      const event = { target: { files: [file] } };

      component.onFileSelected(event);

      expect(component.selectedFile).toBe(file);
      expect(component.uploadMessage).toContain('test.csv');
      expect(component.uploadStatus).toBe('');
    });

    it('should accept CSV file by extension', () => {
      const file = new File(['data'], 'data.csv', { type: '' }); // No MIME type but .csv extension
      const event = { target: { files: [file] } };

      component.onFileSelected(event);

      expect(component.selectedFile).toBe(file);
    });

    it('should reject non-CSV file', () => {
      const file = new File(['data'], 'test.txt', { type: 'text/plain' });
      const event = { target: { files: [file] } };

      component.onFileSelected(event);

      expect(component.selectedFile).toBeNull();
      expect(component.uploadMessage).toContain('CSV');
      expect(component.uploadStatus).toBe('error');
    });

    it('should reject Excel file', () => {
      const file = new File(['data'], 'data.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const event = { target: { files: [file] } };

      component.onFileSelected(event);

      expect(component.selectedFile).toBeNull();
      expect(component.uploadStatus).toBe('error');
    });

    it('should handle empty file selection (no files)', () => {
      const event = { target: { files: [] } };

      component.onFileSelected(event);

      // Should not change state
      expect(component.selectedFile).toBeNull();
    });

    it('should replace previous file selection', () => {
      const file1 = new File(['data1'], 'first.csv', { type: 'text/csv' });
      const file2 = new File(['data2'], 'second.csv', { type: 'text/csv' });

      component.onFileSelected({ target: { files: [file1] } });
      expect(component.selectedFile!.name).toBe('first.csv');

      component.onFileSelected({ target: { files: [file2] } });
      expect(component.selectedFile!.name).toBe('second.csv');
    });

    it('should show file name in upload message', () => {
      const file = new File(['data'], 'my-comparables.csv', { type: 'text/csv' });
      component.onFileSelected({ target: { files: [file] } });

      expect(component.uploadMessage).toContain('my-comparables.csv');
    });
  });

  // ==================== Upload File ====================

  describe('uploadFile', () => {
    it('should show error when no file is selected', async () => {
      component.selectedFile = null;
      await component.uploadFile();

      expect(component.uploadMessage).toContain('selecciona un archivo');
      expect(component.uploadStatus).toBe('error');
      expect(apiServiceSpy.uploadComparablesCsv).not.toHaveBeenCalled();
    });

    it('should call apiService.uploadComparablesCsv with selected file', async () => {
      const file = new File(['col1,col2\nv1,v2'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: true, inserted: 10, rejects: 0 })
      );

      await component.uploadFile();

      expect(apiServiceSpy.uploadComparablesCsv).toHaveBeenCalledWith(file);
    });

    it('should show success message on successful upload', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: true, inserted: 5, rejects: 0 })
      );

      await component.uploadFile();

      expect(component.uploadMessage).toContain('5 registros insertados');
      expect(component.uploadStatus).toBe('success');
    });

    it('should show rejects count in success message', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: true, inserted: 8, rejects: 2 })
      );

      await component.uploadFile();

      expect(component.uploadMessage).toContain('2 rechazados');
    });

    it('should emit fileUploaded event on success', async () => {
      spyOn(component.fileUploaded, 'emit');
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      const result = { ok: true, inserted: 3, rejects: 0 };
      apiServiceSpy.uploadComparablesCsv.and.returnValue(Promise.resolve(result));

      await component.uploadFile();

      expect(component.fileUploaded.emit).toHaveBeenCalledWith(result);
    });

    it('should clear selected file on success', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: true, inserted: 1, rejects: 0 })
      );

      await component.uploadFile();

      expect(component.selectedFile).toBeNull();
    });

    it('should handle non-ok response from API', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: false })
      );

      await component.uploadFile();

      expect(component.uploadMessage).toContain('Error');
      expect(component.uploadStatus).toBe('error');
    });

    it('should handle API error/exception', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.reject(new Error('Server error'))
      );

      await component.uploadFile();

      expect(component.uploadMessage).toContain('Error');
      expect(component.uploadStatus).toBe('error');
    });

    it('should set uploading to true during upload', async () => {
      let uploadingDuringCall = false;
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.callFake(() => {
        uploadingDuringCall = component.uploading;
        return Promise.resolve({ ok: true, inserted: 1, rejects: 0 });
      });

      await component.uploadFile();

      expect(uploadingDuringCall).toBeTrue();
    });

    it('should set uploading to false after upload completes', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.resolve({ ok: true, inserted: 1, rejects: 0 })
      );

      await component.uploadFile();

      expect(component.uploading).toBeFalse();
    });

    it('should set uploading to false even on error', async () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.selectedFile = file;
      apiServiceSpy.uploadComparablesCsv.and.returnValue(
        Promise.reject(new Error('Fail'))
      );

      await component.uploadFile();

      expect(component.uploading).toBeFalse();
    });
  });

  // ==================== Clear Selection ====================

  describe('clearSelection', () => {
    it('should clear selected file', () => {
      component.selectedFile = new File(['data'], 'test.csv', { type: 'text/csv' });
      component.clearSelection();
      expect(component.selectedFile).toBeNull();
    });

    it('should clear upload message', () => {
      component.uploadMessage = 'Some message';
      component.clearSelection();
      expect(component.uploadMessage).toBe('');
    });

    it('should clear upload status', () => {
      component.uploadStatus = 'success';
      component.clearSelection();
      expect(component.uploadStatus).toBe('');
    });
  });

  // ==================== Disabled State ====================

  describe('Disabled State', () => {
    it('should accept disabled input', () => {
      component.disabled = true;
      expect(component.disabled).toBeTrue();
    });

    it('should default to not disabled', () => {
      expect(component.disabled).toBeFalse();
    });
  });
});
