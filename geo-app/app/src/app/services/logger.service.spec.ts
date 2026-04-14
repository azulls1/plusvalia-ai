import { TestBed } from '@angular/core/testing';
import { LoggerService } from './logger.service';

describe('LoggerService', () => {
  let service: LoggerService;

  // ==================== Development Mode Tests ====================

  describe('Development Mode (production = false)', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [LoggerService]
      });
      service = TestBed.inject(LoggerService);
      // Force development mode
      (service as any).isProduction = false;
    });

    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    // --- log() ---
    it('should call console.log in development mode', () => {
      spyOn(console, 'log');
      service.log('test message', { extra: 'data' });
      expect(console.log).toHaveBeenCalledWith('test message', { extra: 'data' });
    });

    it('should pass multiple arguments to console.log', () => {
      spyOn(console, 'log');
      service.log('arg1', 'arg2', 'arg3', 42);
      expect(console.log).toHaveBeenCalledWith('arg1', 'arg2', 'arg3', 42);
    });

    // --- warn() ---
    it('should call console.warn in development mode', () => {
      spyOn(console, 'warn');
      service.warn('warning message', { detail: 'something' });
      expect(console.warn).toHaveBeenCalledWith('warning message', { detail: 'something' });
    });

    it('should pass multiple arguments to console.warn', () => {
      spyOn(console, 'warn');
      service.warn('w1', 'w2');
      expect(console.warn).toHaveBeenCalledWith('w1', 'w2');
    });

    // --- error() ---
    it('should call console.error with full details in development mode', () => {
      spyOn(console, 'error');
      const testError = new Error('test error');
      service.error('Something failed', testError);
      expect(console.error).toHaveBeenCalledWith('Something failed', testError);
    });

    it('should call console.error with message only when no error object provided', () => {
      spyOn(console, 'error');
      service.error('Simple error message');
      expect(console.error).toHaveBeenCalledWith('Simple error message', undefined);
    });

    // --- sensitive() ---
    it('should log sensitive data in development mode', () => {
      spyOn(console, 'log');
      const sensitiveData = { apiKey: 'secret-123', password: 'hunter2' };
      service.sensitive('API Config', sensitiveData);
      expect(console.log).toHaveBeenCalledWith('[SENSITIVE] API Config:', sensitiveData);
    });

    it('should format sensitive label correctly', () => {
      spyOn(console, 'log');
      service.sensitive('Supabase Key', 'my-key-12345');
      expect(console.log).toHaveBeenCalledWith('[SENSITIVE] Supabase Key:', 'my-key-12345');
    });

    // --- success() ---
    it('should log success message with checkmark in development mode', () => {
      spyOn(console, 'log');
      service.success('Data loaded successfully');
      expect(console.log).toHaveBeenCalledWith(jasmine.stringContaining('Data loaded successfully'));
    });

    // --- info() ---
    it('should log info message in development mode', () => {
      spyOn(console, 'log');
      service.info('Loading tiles...');
      expect(console.log).toHaveBeenCalledWith(jasmine.stringContaining('Loading tiles...'));
    });
  });

  // ==================== Production Mode Tests ====================

  describe('Production Mode (production = true)', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [LoggerService]
      });
      service = TestBed.inject(LoggerService);
      // Force production mode
      (service as any).isProduction = true;
    });

    // --- log() ---
    it('should NOT call console.log in production mode', () => {
      spyOn(console, 'log');
      service.log('this should be silent');
      expect(console.log).not.toHaveBeenCalled();
    });

    // --- warn() ---
    it('should NOT call console.warn in production mode', () => {
      spyOn(console, 'warn');
      service.warn('this warning should be silent');
      expect(console.warn).not.toHaveBeenCalled();
    });

    // --- error() ---
    it('should call console.error with ONLY the message in production (sanitized)', () => {
      spyOn(console, 'error');
      const sensitiveError = new Error('Database connection failed: password=abc123');
      service.error('Database error', sensitiveError);
      // In production, only the message is logged, NOT the error object
      expect(console.error).toHaveBeenCalledWith('Database error');
      expect(console.error).not.toHaveBeenCalledWith('Database error', sensitiveError);
    });

    it('should still log error messages in production (just sanitized)', () => {
      spyOn(console, 'error');
      service.error('Something went wrong');
      expect(console.error).toHaveBeenCalledTimes(1);
      expect(console.error).toHaveBeenCalledWith('Something went wrong');
    });

    // --- sensitive() ---
    it('should NEVER log sensitive data in production mode', () => {
      spyOn(console, 'log');
      service.sensitive('API Key', 'super-secret-key-12345');
      expect(console.log).not.toHaveBeenCalled();
    });

    it('should not leak sensitive objects in production', () => {
      spyOn(console, 'log');
      spyOn(console, 'warn');
      spyOn(console, 'error');

      const sensitiveObj = { supabaseKey: 'eyJhbG...', dbPassword: 'secret' };
      service.sensitive('Credentials', sensitiveObj);

      // Neither log, warn, nor error should have been called for sensitive
      expect(console.log).not.toHaveBeenCalled();
    });

    // --- success() ---
    it('should NOT log success messages in production mode', () => {
      spyOn(console, 'log');
      service.success('Heatmap loaded from cache');
      expect(console.log).not.toHaveBeenCalled();
    });

    // --- info() ---
    it('should NOT log info messages in production mode', () => {
      spyOn(console, 'log');
      service.info('Processing data...');
      expect(console.log).not.toHaveBeenCalled();
    });
  });

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [LoggerService]
      });
      service = TestBed.inject(LoggerService);
      (service as any).isProduction = false;
    });

    it('should handle null arguments gracefully', () => {
      spyOn(console, 'log');
      expect(() => service.log(null)).not.toThrow();
      expect(console.log).toHaveBeenCalledWith(null);
    });

    it('should handle undefined arguments gracefully', () => {
      spyOn(console, 'log');
      expect(() => service.log(undefined)).not.toThrow();
    });

    it('should handle empty string arguments', () => {
      spyOn(console, 'log');
      service.log('');
      expect(console.log).toHaveBeenCalledWith('');
    });

    it('should handle error() with undefined error object', () => {
      spyOn(console, 'error');
      service.error('Error occurred');
      expect(console.error).toHaveBeenCalledWith('Error occurred', undefined);
    });

    it('should handle sensitive() with null data', () => {
      spyOn(console, 'log');
      service.sensitive('NullTest', null);
      expect(console.log).toHaveBeenCalledWith('[SENSITIVE] NullTest:', null);
    });
  });
});
