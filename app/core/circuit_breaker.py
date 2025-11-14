"""
CircuitBreaker Pattern Implementation

Prevent cascading failures when external systems are down
"""
from typing import Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import asyncio


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker implementation

    Features:
    - Automatic failure detection
    - Timeout-based recovery
    - Configurable thresholds
    - Fallback support
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails

        Example:
            result = await circuit_breaker.call(
                adapter.search_read,
                model="res.partner",
                domain=[]
            )
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: Attempting reset (HALF_OPEN)")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs)

            # Success - reset if in half-open state
            if self.state == CircuitState.HALF_OPEN:
                self._reset()
                logger.info("Circuit breaker: Service recovered (CLOSED)")

            return result

        except self.expected_exception as e:
            self._record_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _record_failure(self):
        """Record a failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker: OPENED after {self.failure_count} failures"
            )

    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def get_state(self) -> dict:
        """
        Get current circuit breaker state

        Returns:
            State information
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


# Global circuit breakers for each system
system_circuit_breakers = {}


def get_circuit_breaker(system_id: str) -> CircuitBreaker:
    """
    Get or create circuit breaker for system

    Args:
        system_id: System identifier

    Returns:
        CircuitBreaker instance
    """
    if system_id not in system_circuit_breakers:
        system_circuit_breakers[system_id] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    return system_circuit_breakers[system_id]
