"""
Base service class for all Odoo operations

This module provides the foundational class that all Odoo operation services inherit from.
It handles authentication, JSON-RPC communication, context management, and error handling.
"""
from abc import ABC
from typing import Any, Dict, List, Optional, Union
import httpx
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    OdooConnectionException,
    OdooAuthenticationException,
    OdooSessionExpiredException,
    OdooTimeoutException,
    OdooPermissionDeniedException,
    OdooModelNotFoundException,
    OdooRecordNotFoundException,
)


class OdooExecutionError(Exception):
    """Exception raised when Odoo operation execution fails"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.data = data or {}


class OdooOperationsService(ABC):
    """
    Base class for all Odoo operations

    This class provides the foundational functionality for communicating with Odoo
    via JSON-RPC API. All operation services inherit from this class.

    Features:
        - Authentication with Odoo (session-based or API key)
        - JSON-RPC execution via call_kw
        - Context injection (lang, tz, company_id, uid)
        - Error handling with specific exceptions
        - Logging for debugging and monitoring
        - Session management with auto-refresh
        - Configurable timeouts
        - Optional caching support

    Attributes:
        odoo_url: Base URL of the Odoo instance
        database: Odoo database name
        username: Odoo username for authentication
        password: Odoo password or API key
        base_context: Default context for all operations

    Example:
        >>> service = OdooOperationsService(
        ...     odoo_url="https://demo.odoo.com",
        ...     database="demo",
        ...     username="admin",
        ...     password="admin123"
        ... )
        >>> await service.authenticate()
        >>> result = await service._execute_kw("res.partner", "search", [[]])
    """

    def __init__(
        self,
        odoo_url: str,
        database: str,
        username: str,
        password: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """
        Initialize Odoo Operations Service

        Args:
            odoo_url: Base URL of Odoo instance (e.g., "https://odoo.example.com")
            database: Odoo database name
            username: Odoo username
            password: Odoo password or API key
            context: Base context to include in all operations
            session_id: Existing session ID (for session reuse)
            timeout: Request timeout in seconds
        """
        self.odoo_url = odoo_url.rstrip('/')
        self.database = database
        self.username = username
        self.password = password
        self.base_context = context or {}
        self._uid: Optional[int] = None
        self._session_id = session_id
        self._timeout = timeout

        # HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
                cookies={} if not self._session_id else {"session_id": self._session_id}
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def uid(self) -> Optional[int]:
        """Get current user ID"""
        return self._uid

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self._session_id

    @property
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self._uid is not None and self._session_id is not None

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Odoo and get UID and session

        Returns:
            Dict containing:
                - success: bool
                - uid: int (user ID)
                - session_id: str
                - user_context: dict

        Raises:
            OdooAuthenticationException: If authentication fails
            OdooConnectionException: If connection fails
        """
        url = f"{self.odoo_url}/web/session/authenticate"

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": self.database,
                "login": self.username,
                "password": self.password
            },
            "id": 1
        }

        try:
            client = await self._get_client()

            logger.debug(
                f"Authenticating with Odoo",
                extra={
                    "url": self.odoo_url,
                    "database": self.database,
                    "username": self.username
                }
            )

            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                error_data = result["error"]
                error_msg = error_data.get("message", "Authentication failed")
                logger.error(f"Odoo authentication error: {error_msg}")
                raise OdooAuthenticationException(self.username)

            if "result" in result and result["result"].get("uid"):
                self._uid = result["result"]["uid"]
                self._session_id = (
                    response.cookies.get("session_id") or
                    response.cookies.get("session_id_http")
                )

                # Update client cookies
                if self._session_id:
                    self._client.cookies.set("session_id", self._session_id)

                user_context = result["result"].get("user_context", {})

                logger.info(
                    f"Authenticated with Odoo",
                    extra={
                        "uid": self._uid,
                        "username": self.username,
                        "database": self.database
                    }
                )

                return {
                    "success": True,
                    "uid": self._uid,
                    "session_id": self._session_id,
                    "user_context": user_context
                }
            else:
                raise OdooAuthenticationException(self.username)

        except httpx.TimeoutException:
            raise OdooTimeoutException(
                timeout=self._timeout,
                operation="authentication"
            )
        except httpx.HTTPStatusError as e:
            raise OdooConnectionException(
                f"HTTP error during authentication: {e.response.status_code}",
                url=self.odoo_url
            )
        except OdooAuthenticationException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise OdooConnectionException(
                f"Unexpected error during authentication: {str(e)}",
                url=self.odoo_url
            )

    async def _ensure_authenticated(self):
        """Ensure service is authenticated before operations"""
        if not self.is_authenticated:
            await self.authenticate()

    async def _execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        retry_on_session_expire: bool = True
    ) -> Any:
        """
        Execute Odoo operation via call_kw

        This is the core method for all Odoo JSON-RPC operations.

        Args:
            model: Model name (e.g., 'res.partner')
            method: Method name (e.g., 'search_read', 'create', 'write')
            args: Positional arguments for the method
            kwargs: Named arguments (fields, limit, offset, context, etc.)
            retry_on_session_expire: Whether to retry on session expiration

        Returns:
            Any: Result from Odoo

        Raises:
            OdooExecutionError: If execution fails
            OdooSessionExpiredException: If session expired and retry failed
            OdooPermissionDeniedException: If operation not permitted
            OdooModelNotFoundException: If model doesn't exist
            OdooRecordNotFoundException: If record not found
        """
        await self._ensure_authenticated()

        # Merge context
        merged_kwargs = kwargs.copy() if kwargs else {}
        if "context" not in merged_kwargs:
            merged_kwargs["context"] = {}
        merged_kwargs["context"].update(self.base_context)

        # Add uid to context if available
        if self._uid and "uid" not in merged_kwargs["context"]:
            merged_kwargs["context"]["uid"] = self._uid

        url = f"{self.odoo_url}/web/dataset/call_kw"

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": merged_kwargs
            },
            "id": 1
        }

        logger.debug(
            f"Executing {model}.{method}",
            extra={
                "model": model,
                "method": method,
                "args_count": len(args) if args else 0,
                "has_context": bool(merged_kwargs.get("context"))
            }
        )

        try:
            client = await self._get_client()
            response = await client.post(url, json=payload)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                raise OdooExecutionError(
                    f"Invalid response type: {content_type}",
                    data={"response_text": response.text[:500]}
                )

            result = response.json()

            if "error" in result:
                error_data = result["error"]
                error_code = error_data.get("code")
                error_msg = error_data.get("message", "Unknown error")
                error_details = error_data.get("data", {})

                # Handle session expiration (code 100)
                if error_code == 100 and retry_on_session_expire:
                    logger.warning("Odoo session expired, re-authenticating...")
                    self._uid = None
                    self._session_id = None
                    await self.authenticate()
                    return await self._execute_kw(
                        model, method, args, kwargs,
                        retry_on_session_expire=False
                    )

                # Parse specific error types
                error_msg_lower = error_msg.lower()

                if "access denied" in error_msg_lower or "permission" in error_msg_lower:
                    raise OdooPermissionDeniedException(
                        operation=method,
                        model=model
                    )

                if "does not exist" in error_msg_lower and "model" in error_msg_lower:
                    raise OdooModelNotFoundException(model)

                if "record does not exist" in error_msg_lower:
                    raise OdooRecordNotFoundException(
                        model=model,
                        record_id=args[0] if args else 0
                    )

                logger.error(
                    f"Odoo error in {model}.{method}: {error_msg}",
                    extra={
                        "model": model,
                        "method": method,
                        "error_code": error_code,
                        "error_data": error_details
                    }
                )
                raise OdooExecutionError(
                    message=error_msg,
                    data=error_details
                )

            logger.debug(f"Successfully executed {model}.{method}")
            return result.get("result")

        except httpx.TimeoutException:
            raise OdooTimeoutException(
                timeout=self._timeout,
                operation=f"{model}.{method}"
            )
        except httpx.HTTPStatusError as e:
            raise OdooConnectionException(
                f"HTTP error during {model}.{method}: {e.response.status_code}",
                url=self.odoo_url
            )
        except (OdooExecutionError, OdooPermissionDeniedException,
                OdooModelNotFoundException, OdooRecordNotFoundException,
                OdooSessionExpiredException, OdooTimeoutException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {model}.{method}: {str(e)}")
            raise OdooExecutionError(
                message=f"Unexpected error: {str(e)}",
                data={"model": model, "method": method}
            )

    async def _execute_with_cache(
        self,
        cache_key: str,
        ttl: int,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute Odoo operation with caching support

        This method checks cache before executing and stores result after.
        Useful for frequently accessed data that doesn't change often.

        Args:
            cache_key: Unique cache key for this operation
            ttl: Time to live in seconds
            model: Model name
            method: Method name
            args: Positional arguments
            kwargs: Named arguments

        Returns:
            Any: Result from cache or fresh execution
        """
        # TODO: Implement caching with Redis when cache_service is available
        # For now, execute directly without caching
        return await self._execute_kw(model, method, args, kwargs)

    async def check_connection(self) -> bool:
        """
        Check if connection to Odoo is valid

        Returns:
            bool: True if connected and authenticated
        """
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.odoo_url}/web/session/get_session_info",
                json={"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}
            )

            result = response.json()

            if "result" in result:
                session_info = result["result"]
                return session_info.get("uid") is not None

            return False

        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False

    async def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information from Odoo

        Returns:
            Dict containing session info (uid, username, company_id, etc.)
        """
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.odoo_url}/web/session/get_session_info",
                json={"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}
            )

            result = response.json()
            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to get session info: {str(e)}")
            return {}

    def set_context(self, context: Dict[str, Any]):
        """
        Set or update the base context

        Args:
            context: Context values to set/update
        """
        self.base_context.update(context)

    def clear_context(self):
        """Clear the base context"""
        self.base_context = {}


def create_odoo_service(
    odoo_url: Optional[str] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
) -> OdooOperationsService:
    """
    Factory function to create Odoo service with defaults from settings

    Args:
        odoo_url: Odoo URL (defaults to settings.ODOO_URL)
        database: Database name
        username: Username
        password: Password
        **kwargs: Additional arguments for OdooOperationsService

    Returns:
        OdooOperationsService instance
    """
    return OdooOperationsService(
        odoo_url=odoo_url or settings.ODOO_URL,
        database=database or "",
        username=username or "",
        password=password or "",
        **kwargs
    )
