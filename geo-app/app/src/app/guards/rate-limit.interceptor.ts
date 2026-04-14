/**
 * rate-limit.interceptor.ts — HTTP Interceptor for Security Hardening
 *
 * Provides:
 *   1. Client-side rate limiting (configurable requests per window)
 *   2. Request deduplication (prevents duplicate in-flight requests)
 *   3. Timeout handling (default 30s, configurable per request)
 *   4. Error sanitization (no stack traces or internal details to UI)
 *
 * Usage in app.config.ts or app.module.ts:
 *   providers: [
 *     { provide: HTTP_INTERCEPTORS, useClass: RateLimitInterceptor, multi: true }
 *   ]
 *
 * OWASP references:
 *   - A04:2021 Insecure Design (rate limiting)
 *   - A09:2021 Security Logging and Monitoring (error sanitization)
 */

import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, Subject, of } from 'rxjs';
import { catchError, timeout, takeUntil, finalize, share } from 'rxjs/operators';

/** Configuration constants */
const RATE_LIMIT_MAX_REQUESTS = 60;       // Max requests per window
const RATE_LIMIT_WINDOW_MS = 60_000;      // Window duration: 60 seconds
const DEFAULT_TIMEOUT_MS = 30_000;        // Default request timeout: 30 seconds
const DEDUP_ENABLED_METHODS = ['GET'];    // Only deduplicate GET requests

/** Sanitized error messages by HTTP status code */
const SAFE_ERROR_MESSAGES: Record<number, string> = {
  0:   'No se pudo conectar al servidor. Verifica tu conexión a internet.',
  400: 'La solicitud contiene datos inválidos. Verifica los campos e intenta de nuevo.',
  401: 'No tienes autorización. Inicia sesión nuevamente.',
  403: 'No tienes permiso para realizar esta acción.',
  404: 'El recurso solicitado no fue encontrado.',
  408: 'La solicitud tardó demasiado. Intenta de nuevo.',
  429: 'Demasiadas solicitudes. Espera un momento antes de intentar de nuevo.',
  500: 'Error interno del servidor. El equipo ha sido notificado.',
  502: 'El servidor no está disponible temporalmente. Intenta más tarde.',
  503: 'El servicio está en mantenimiento. Intenta más tarde.',
  504: 'El servidor tardó demasiado en responder. Intenta más tarde.'
};

@Injectable()
export class RateLimitInterceptor implements HttpInterceptor {
  /** Tracks request timestamps for rate limiting */
  private requestTimestamps: number[] = [];

  /** Tracks in-flight requests for deduplication (key -> observable) */
  private inFlightRequests = new Map<string, Observable<HttpEvent<any>>>();

  /**
   * Intercepts all outgoing HTTP requests.
   */
  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // Step 1: Check rate limit
    if (this.isRateLimited()) {
      console.warn('[Security] Rate limit exceeded. Request blocked:', req.url);
      return throwError(() => new HttpErrorResponse({
        status: 429,
        statusText: 'Too Many Requests',
        error: { message: SAFE_ERROR_MESSAGES[429] },
        url: req.url
      }));
    }

    // Record this request timestamp
    this.recordRequest();

    // Step 2: Deduplicate GET requests
    if (DEDUP_ENABLED_METHODS.includes(req.method)) {
      const dedupKey = this.getRequestKey(req);
      const existing = this.inFlightRequests.get(dedupKey);

      if (existing) {
        console.debug('[Security] Deduplicating request:', req.url);
        return existing;
      }

      // Create shared observable for this request
      const shared$ = this.executeRequest(req, next, dedupKey);
      this.inFlightRequests.set(dedupKey, shared$);
      return shared$;
    }

    // Step 3: Execute non-GET requests normally (with timeout + error sanitization)
    return this.executeRequest(req, next);
  }

  /**
   * Executes the request with timeout and error sanitization.
   * Optionally registers it for deduplication cleanup.
   */
  private executeRequest(
    req: HttpRequest<any>,
    next: HttpHandler,
    dedupKey?: string
  ): Observable<HttpEvent<any>> {
    // Determine timeout: use custom header or default
    const timeoutMs = this.getTimeoutForRequest(req);

    const result$ = next.handle(req).pipe(
      // Apply timeout
      timeout(timeoutMs),

      // Sanitize errors — never expose internal details to the UI
      catchError((error: unknown) => {
        return throwError(() => this.sanitizeError(error, req));
      }),

      // Clean up dedup map when request completes
      finalize(() => {
        if (dedupKey) {
          this.inFlightRequests.delete(dedupKey);
        }
      }),

      // Share the observable for deduplication
      share()
    );

    return result$;
  }

  /**
   * Checks whether the client has exceeded the rate limit.
   * Uses a sliding window approach.
   */
  private isRateLimited(): boolean {
    const now = Date.now();
    const windowStart = now - RATE_LIMIT_WINDOW_MS;

    // Remove timestamps outside the current window
    this.requestTimestamps = this.requestTimestamps.filter(ts => ts > windowStart);

    return this.requestTimestamps.length >= RATE_LIMIT_MAX_REQUESTS;
  }

  /** Records the current timestamp for rate limiting. */
  private recordRequest(): void {
    this.requestTimestamps.push(Date.now());
  }

  /**
   * Generates a unique key for request deduplication.
   * Based on method + URL + sorted query params.
   */
  private getRequestKey(req: HttpRequest<any>): string {
    return `${req.method}:${req.urlWithParams}`;
  }

  /**
   * Gets the timeout value for a request.
   * Supports a custom 'X-Request-Timeout' header to override the default.
   */
  private getTimeoutForRequest(req: HttpRequest<any>): number {
    const customTimeout = req.headers.get('X-Request-Timeout');
    if (customTimeout) {
      const parsed = parseInt(customTimeout, 10);
      if (!isNaN(parsed) && parsed > 0 && parsed <= 120_000) {
        return parsed;
      }
    }
    return DEFAULT_TIMEOUT_MS;
  }

  /**
   * Sanitizes error responses to prevent leaking internal information.
   *
   * OWASP A09: Security Logging and Monitoring
   * - Log the full error server-side / in console (dev only)
   * - Return only a safe, user-friendly message
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- HttpRequest generic requires any
  private sanitizeError(error: unknown, req: HttpRequest<any>): HttpErrorResponse {
    // Log full error in development (console only, never to UI)
    const errObj = error as Record<string, unknown>;
    if (typeof error === 'object' && error !== null) {
      console.error('[Security] Request failed:', {
        url: req.url,
        method: req.method,
        status: errObj['status'] || 'unknown',
        // Only log message, never the full error body in production
        message: errObj['message'] || 'Unknown error'
      });
    }

    // Handle timeout errors from RxJS
    if (errObj?.['name'] === 'TimeoutError') {
      return new HttpErrorResponse({
        status: 408,
        statusText: 'Request Timeout',
        error: { message: SAFE_ERROR_MESSAGES[408] },
        url: req.url
      });
    }

    // Handle HTTP errors
    if (error instanceof HttpErrorResponse) {
      const safeMessage =
        SAFE_ERROR_MESSAGES[error.status] ||
        'Ocurrió un error inesperado. Intenta de nuevo más tarde.';

      return new HttpErrorResponse({
        status: error.status,
        statusText: error.statusText,
        error: { message: safeMessage },
        url: req.url
      });
    }

    // Handle unknown errors
    return new HttpErrorResponse({
      status: 0,
      statusText: 'Unknown Error',
      error: { message: SAFE_ERROR_MESSAGES[0] },
      url: req.url
    });
  }
}
