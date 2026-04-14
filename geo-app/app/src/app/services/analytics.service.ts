import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * AnalyticsService — Tracking de eventos y metricas de uso.
 *
 * Soporta multiples backends:
 * - Console (desarrollo)
 * - Google Analytics 4 (produccion, si GA_MEASUREMENT_ID configurado)
 * - Custom endpoint (si ANALYTICS_URL configurado)
 *
 * Uso:
 *   this.analytics.trackAction('prediction_requested', 'map', 'CDMX');
 *   this.analytics.trackPageView('/mapa');
 */
@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private enabled: boolean;
  private sessionId: string;
  private sessionStart: Date;
  private eventBuffer: AnalyticsEvent[] = [];
  private flushInterval: ReturnType<typeof setInterval> | null = null;

  constructor() {
    this.enabled = true; // Always track, console in dev, endpoint in prod
    this.sessionId = this.generateSessionId();
    this.sessionStart = new Date();

    if (this.enabled) {
      this.startFlushInterval();
    }
  }

  /** Track a page view. */
  trackPageView(path: string): void {
    this.track({
      type: 'page_view',
      name: path,
      properties: { path },
    });
  }

  /** Track a user action (click, toggle, filter). */
  trackAction(action: string, target: string, value?: string | number): void {
    this.track({
      type: 'action',
      name: action,
      properties: { target, value },
    });
  }

  /** Track performance metric. */
  trackPerformance(metric: string, durationMs: number): void {
    this.track({
      type: 'performance',
      name: metric,
      properties: { duration_ms: durationMs },
    });
  }

  /** Track an error. */
  trackError(error: string, context: Record<string, unknown> = {}): void {
    this.track({
      type: 'error',
      name: error,
      properties: { ...context, severity: 'error' },
    });
  }

  /** Flush buffered events (send to backend). */
  flush(): void {
    if (this.eventBuffer.length === 0) return;

    const events = [...this.eventBuffer];
    this.eventBuffer = [];

    // In development: log to console only (no external calls to avoid CORS)
    if (!environment.production) {
      console.groupCollapsed(`[Analytics] ${events.length} events`);
      events.forEach(e => console.log(`  ${e.type}: ${e.name}`, e.properties));
      console.groupEnd();
      return;
    }

    // In production: send to ML API analytics endpoint (same origin, no CORS)
    const analyticsUrl = `${environment.mlApiBase}/analytics/events`;
    fetch(analyticsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: this.sessionId,
        events,
        timestamp: new Date().toISOString(),
      }),
    }).catch(() => { /* Silent fail in production */ });
  }

  private track(event: Omit<AnalyticsEvent, 'timestamp' | 'sessionId'>): void {
    const fullEvent: AnalyticsEvent = {
      ...event,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
    };

    this.eventBuffer.push(fullEvent);

    if (!environment.production) {
      console.log(`[Analytics] ${event.type}: ${event.name}`, event.properties);
    }

    // Flush si buffer grande
    if (this.eventBuffer.length >= 50) {
      this.flush();
    }
  }

  /** Clean up: clear the flush interval and send remaining events. */
  destroy(): void {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.flush();
  }

  private startFlushInterval(): void {
    // Flush cada 30 segundos
    this.flushInterval = setInterval(() => this.flush(), 30000);
  }

  private generateSessionId(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

interface AnalyticsEvent {
  type: 'page_view' | 'event' | 'action' | 'performance' | 'error';
  name: string;
  properties: Record<string, unknown>;
  timestamp: string;
  sessionId: string;
}
