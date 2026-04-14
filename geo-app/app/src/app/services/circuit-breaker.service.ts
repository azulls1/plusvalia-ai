import { Injectable } from '@angular/core';

/**
 * CircuitBreakerService — Protege llamadas a servicios externos.
 *
 * Estados:
 * - CLOSED: Funcionamiento normal, requests pasan
 * - OPEN: Circuito abierto, requests se rechazan inmediatamente
 * - HALF_OPEN: Permite un request de prueba para verificar recovery
 *
 * Uso:
 *   const result = await this.circuitBreaker.execute(
 *     'ml-api',
 *     () => apiCall(),
 *     () => fallbackValue
 *   );
 */
@Injectable({ providedIn: 'root' })
export class CircuitBreakerService {
  private breakers = new Map<string, CircuitBreaker>();

  /**
   * Obtiene o crea un circuit breaker para un servicio.
   */
  private getBreaker(name: string, options?: Partial<BreakerOptions>): CircuitBreaker {
    if (!this.breakers.has(name)) {
      this.breakers.set(name, new CircuitBreaker(name, options));
    }
    return this.breakers.get(name)!;
  }

  /**
   * Ejecuta una funcion protegida por circuit breaker.
   */
  async execute<T>(
    name: string,
    fn: () => Promise<T>,
    fallback?: () => T | Promise<T>,
    options?: Partial<BreakerOptions>
  ): Promise<T> {
    const breaker = this.getBreaker(name, options);

    if (!breaker.canExecute()) {
      if (fallback) {
        return await fallback();
      }
      throw new Error(`Circuit breaker '${name}' is OPEN. Service unavailable.`);
    }

    try {
      const result = await fn();
      breaker.onSuccess();
      return result;
    } catch (error) {
      breaker.onFailure();
      if (fallback) {
        return await fallback();
      }
      throw error;
    }
  }

}

type BreakerState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface BreakerOptions {
  failureThreshold: number;    // Fallos antes de abrir (default: 5)
  recoveryTimeout: number;     // Ms antes de intentar half-open (default: 30000)
  successThreshold: number;    // Exitos en half-open para cerrar (default: 2)
}

interface BreakerStatus {
  name: string;
  state: BreakerState;
  failures: number;
  successes: number;
  lastFailure: string | null;
  lastSuccess: string | null;
}

class CircuitBreaker {
  private state: BreakerState = 'CLOSED';
  private failures = 0;
  private successes = 0;
  private lastFailureTime: Date | null = null;
  private lastSuccessTime: Date | null = null;
  private options: BreakerOptions;

  constructor(
    private name: string,
    options?: Partial<BreakerOptions>
  ) {
    this.options = {
      failureThreshold: options?.failureThreshold ?? 5,
      recoveryTimeout: options?.recoveryTimeout ?? 30000,
      successThreshold: options?.successThreshold ?? 2,
    };
  }

  canExecute(): boolean {
    switch (this.state) {
      case 'CLOSED':
        return true;

      case 'OPEN': {
        const now = Date.now();
        const elapsed = this.lastFailureTime
          ? now - this.lastFailureTime.getTime()
          : Infinity;

        if (elapsed >= this.options.recoveryTimeout) {
          this.state = 'HALF_OPEN';
          this.successes = 0;
          return true;
        }
        return false;
      }

      case 'HALF_OPEN':
        return true;

      default:
        return true;
    }
  }

  onSuccess(): void {
    this.lastSuccessTime = new Date();
    this.successes++;

    switch (this.state) {
      case 'HALF_OPEN':
        if (this.successes >= this.options.successThreshold) {
          this.state = 'CLOSED';
          this.failures = 0;
        }
        break;

      case 'CLOSED':
        this.failures = 0;
        break;
    }
  }

  onFailure(): void {
    this.lastFailureTime = new Date();
    this.failures++;

    switch (this.state) {
      case 'CLOSED':
        if (this.failures >= this.options.failureThreshold) {
          this.state = 'OPEN';
        }
        break;

      case 'HALF_OPEN':
        this.state = 'OPEN';
        this.successes = 0;
        break;
    }
  }

  getStatus(): BreakerStatus {
    return {
      name: this.name,
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      lastFailure: this.lastFailureTime?.toISOString() ?? null,
      lastSuccess: this.lastSuccessTime?.toISOString() ?? null,
    };
  }

  reset(): void {
    this.state = 'CLOSED';
    this.failures = 0;
    this.successes = 0;
  }
}
