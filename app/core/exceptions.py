"""
Custom exceptions for BridgeCore API

This module defines custom exception classes for better error handling
and reporting across the application.
"""

from typing import Optional, Dict, Any


# ===== Base Exceptions =====

class BridgeCoreException(Exception):
    """Base exception for all BridgeCore errors"""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details
        }


# ===== Sync-Related Exceptions =====

class SyncException(BridgeCoreException):
    """Base exception for synchronization errors"""
    pass


class SyncStateNotFoundException(SyncException):
    """Raised when sync state is not found"""

    def __init__(self, user_id: int, device_id: str):
        super().__init__(
            f"Sync state not found for user {user_id}, device {device_id}",
            code="SYNC_STATE_NOT_FOUND",
            details={"user_id": user_id, "device_id": device_id}
        )


class SyncStateCreateException(SyncException):
    """Raised when sync state creation fails"""

    def __init__(self, user_id: int, device_id: str, reason: str):
        super().__init__(
            f"Failed to create sync state for user {user_id}, device {device_id}: {reason}",
            code="SYNC_STATE_CREATE_FAILED",
            details={"user_id": user_id, "device_id": device_id, "reason": reason}
        )


class SyncConflictException(SyncException):
    """Raised when sync conflict is detected"""

    def __init__(self, message: str, conflicts: list):
        super().__init__(
            message,
            code="SYNC_CONFLICT",
            details={"conflicts": conflicts}
        )


class InvalidSyncTokenException(SyncException):
    """Raised when sync token is invalid or expired"""

    def __init__(self, token: str):
        super().__init__(
            f"Invalid or expired sync token: {token}",
            code="INVALID_SYNC_TOKEN",
            details={"token": token}
        )


# ===== Odoo Connection Exceptions =====

class OdooConnectionException(BridgeCoreException):
    """Raised when Odoo connection fails"""

    def __init__(self, message: str, *, url: Optional[str] = None, code: Optional[str] = None):
        super().__init__(
            message,
            code=code or "ODOO_CONNECTION_ERROR",
            details={"url": url} if url else {}
        )


class OdooAuthenticationException(OdooConnectionException):
    """Raised when Odoo authentication fails"""

    def __init__(self, username: str):
        super().__init__(
            f"Odoo authentication failed for user: {username}",
            code="ODOO_AUTH_FAILED",
        )
        self.details["username"] = username


class OdooSessionExpiredException(OdooConnectionException):
    """Raised when Odoo session has expired"""

    def __init__(self):
        super().__init__(
            "Odoo session has expired. Please re-authenticate.",
            code="ODOO_SESSION_EXPIRED"
        )


class OdooTimeoutException(OdooConnectionException):
    """Raised when Odoo request times out"""

    def __init__(self, timeout: float, operation: str):
        super().__init__(
            f"Odoo request timed out after {timeout}s: {operation}",
            code="ODOO_TIMEOUT"
        )
        self.details["timeout"] = timeout
        self.details["operation"] = operation


class OdooModelNotFoundException(OdooConnectionException):
    """Raised when Odoo model is not found"""

    def __init__(self, model_name: str):
        super().__init__(
            f"Odoo model not found: {model_name}",
            code="ODOO_MODEL_NOT_FOUND"
        )
        self.details["model_name"] = model_name


class OdooRecordNotFoundException(OdooConnectionException):
    """Raised when Odoo record is not found"""

    def __init__(self, model: str, record_id: int):
        super().__init__(
            f"Odoo record not found: {model}({record_id})",
            code="ODOO_RECORD_NOT_FOUND"
        )
        self.details["model"] = model
        self.details["record_id"] = record_id


class OdooPermissionDeniedException(OdooConnectionException):
    """Raised when Odoo operation is not permitted"""

    def __init__(self, operation: str, model: str):
        super().__init__(
            f"Permission denied for {operation} on {model}",
            code="ODOO_PERMISSION_DENIED"
        )
        self.details["operation"] = operation
        self.details["model"] = model


# ===== Webhook Exceptions =====

class WebhookException(BridgeCoreException):
    """Base exception for webhook errors"""
    pass


class WebhookEventNotFoundException(WebhookException):
    """Raised when webhook event is not found"""

    def __init__(self, event_id: int):
        super().__init__(
            f"Webhook event not found: {event_id}",
            code="WEBHOOK_EVENT_NOT_FOUND",
            details={"event_id": event_id}
        )


class WebhookRetryLimitException(WebhookException):
    """Raised when webhook retry limit is exceeded"""

    def __init__(self, event_id: int, max_retries: int):
        super().__init__(
            f"Webhook event {event_id} exceeded max retries ({max_retries})",
            code="WEBHOOK_RETRY_LIMIT_EXCEEDED",
            details={"event_id": event_id, "max_retries": max_retries}
        )


class WebhookDeliveryException(WebhookException):
    """Raised when webhook delivery fails"""

    def __init__(self, event_id: int, reason: str):
        super().__init__(
            f"Webhook delivery failed for event {event_id}: {reason}",
            code="WEBHOOK_DELIVERY_FAILED",
            details={"event_id": event_id, "reason": reason}
        )


# ===== Cache Exceptions =====

class CacheException(BridgeCoreException):
    """Base exception for cache errors"""
    pass


class CacheConnectionException(CacheException):
    """Raised when Redis connection fails"""

    def __init__(self, redis_url: str):
        super().__init__(
            f"Failed to connect to Redis: {redis_url}",
            code="CACHE_CONNECTION_FAILED",
            details={"redis_url": redis_url}
        )


class CacheOperationException(CacheException):
    """Raised when cache operation fails"""

    def __init__(self, operation: str, key: str, reason: str):
        super().__init__(
            f"Cache {operation} failed for key '{key}': {reason}",
            code="CACHE_OPERATION_FAILED",
            details={"operation": operation, "key": key, "reason": reason}
        )


# ===== Validation Exceptions =====

class ValidationException(BridgeCoreException):
    """Raised when validation fails"""

    def __init__(self, field: str, message: str):
        super().__init__(
            f"Validation error for '{field}': {message}",
            code="VALIDATION_ERROR",
            details={"field": field}
        )


class InvalidAppTypeException(ValidationException):
    """Raised when app type is invalid"""

    def __init__(self, app_type: str, valid_types: list):
        super().__init__(
            "app_type",
            f"Invalid app type '{app_type}'. Valid types: {', '.join(valid_types)}"
        )
        self.details["app_type"] = app_type
        self.details["valid_types"] = valid_types


class InvalidDeviceIdException(ValidationException):
    """Raised when device ID is invalid"""

    def __init__(self, device_id: str, reason: str):
        super().__init__(
            "device_id",
            f"Invalid device ID '{device_id}': {reason}"
        )
        self.details["device_id"] = device_id


# ===== Rate Limiting Exceptions =====

class RateLimitException(BridgeCoreException):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: int):
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window} seconds",
            code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window}
        )


# ===== Configuration Exceptions =====

class ConfigurationException(BridgeCoreException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, config_key: str, message: str):
        super().__init__(
            f"Configuration error for '{config_key}': {message}",
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


# ===== System Exceptions =====

class SystemNotFoundException(BridgeCoreException):
    """Raised when external system is not found"""

    def __init__(self, system_id: str):
        super().__init__(
            f"System not found: {system_id}",
            code="SYSTEM_NOT_FOUND",
            details={"system_id": system_id}
        )


class SystemNotConnectedException(BridgeCoreException):
    """Raised when system is not connected"""

    def __init__(self, system_id: str):
        super().__init__(
            f"System not connected: {system_id}. Please connect first.",
            code="SYSTEM_NOT_CONNECTED",
            details={"system_id": system_id}
        )


# ===== Helper Functions =====

def handle_odoo_error(error: Exception) -> BridgeCoreException:
    """
    Convert generic Odoo errors to specific BridgeCore exceptions

    Args:
        error: Original exception from Odoo

    Returns:
        Appropriate BridgeCoreException subclass
    """
    error_msg = str(error).lower()

    # Check for specific error patterns
    if "session" in error_msg and ("expired" in error_msg or "invalid" in error_msg):
        return OdooSessionExpiredException()

    if "timeout" in error_msg:
        return OdooTimeoutException(timeout=15.0, operation="unknown")

    if "access denied" in error_msg or "permission" in error_msg:
        return OdooPermissionDeniedException(operation="unknown", model="unknown")

    if "not found" in error_msg:
        return OdooConnectionException(str(error))

    # Default to generic Odoo connection error
    return OdooConnectionException(str(error))


def handle_sync_error(error: Exception, user_id: int, device_id: str) -> SyncException:
    """
    Convert generic sync errors to specific exceptions

    Args:
        error: Original exception
        user_id: User ID involved in sync
        device_id: Device ID involved in sync

    Returns:
        Appropriate SyncException subclass
    """
    error_msg = str(error).lower()

    if "not found" in error_msg:
        return SyncStateNotFoundException(user_id, device_id)

    if "conflict" in error_msg:
        return SyncConflictException(str(error), conflicts=[])

    # Default to generic sync exception
    return SyncException(
        str(error),
        code="SYNC_ERROR",
        details={"user_id": user_id, "device_id": device_id}
    )
