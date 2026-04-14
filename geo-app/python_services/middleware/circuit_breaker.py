"""
Circuit Breaker pattern for Python backend services.
Protects external service calls (Supabase, ML model) from cascading failures.
"""
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Optional
from loguru import logger

T = TypeVar('T')

class BreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreaker:
    """Circuit breaker for protecting external service calls."""
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2

    _state: BreakerState = field(default=BreakerState.CLOSED, init=False)
    _failures: int = field(default=0, init=False)
    _successes: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0, init=False)

    @property
    def state(self) -> BreakerState:
        if self._state == BreakerState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = BreakerState.HALF_OPEN
                self._successes = 0
                logger.info(f"Circuit breaker '{self.name}' → HALF_OPEN")
        return self._state

    def record_success(self):
        """Record a successful call."""
        self._successes += 1
        if self._state == BreakerState.HALF_OPEN and self._successes >= self.success_threshold:
            self._state = BreakerState.CLOSED
            self._failures = 0
            logger.info(f"Circuit breaker '{self.name}' → CLOSED")
        elif self._state == BreakerState.CLOSED:
            self._failures = 0

    def record_failure(self):
        """Record a failed call."""
        self._failures += 1
        self._last_failure_time = time.time()
        if self._state == BreakerState.CLOSED and self._failures >= self.failure_threshold:
            self._state = BreakerState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' → OPEN after {self._failures} failures")
        elif self._state == BreakerState.HALF_OPEN:
            self._state = BreakerState.OPEN
            self._successes = 0
            logger.warning(f"Circuit breaker '{self.name}' → OPEN (half-open test failed)")

    def can_execute(self) -> bool:
        """Check if a call is allowed."""
        return self.state != BreakerState.OPEN

    async def execute(self, fn: Callable, fallback: Optional[Callable] = None):
        """Execute a function with circuit breaker protection."""
        if not self.can_execute():
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, using fallback")
            if fallback:
                return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await fn() if asyncio.iscoroutinefunction(fn) else fn()
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if fallback:
                return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
            raise

    def get_status(self) -> dict:
        """Get current breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self._failures,
            "successes": self._successes,
        }


class CircuitBreakerRegistry:
    """Global registry of circuit breakers."""
    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, name: str, **kwargs) -> CircuitBreaker:
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return cls._breakers[name]

    @classmethod
    def get_all_status(cls) -> dict:
        return {name: cb.get_status() for name, cb in cls._breakers.items()}
