"""
Multi-tenant Manager for Odoo Connections

Manages multiple Odoo instances/databases with connection pooling
"""
from typing import Dict, Optional, Any
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import httpx


@dataclass
class TenantConfig:
    """
    Configuration for an Odoo tenant/system

    Attributes:
        tenant_id: Unique tenant identifier
        odoo_url: Odoo instance URL
        database: Odoo database name
        username: Odoo username
        api_key: Odoo API key (encrypted)
        timeout: Request timeout in seconds
        max_connections: Maximum concurrent connections
        active: Whether tenant is active
        created_at: When tenant was created
        updated_at: When tenant was last updated
    """
    tenant_id: str
    odoo_url: str
    database: str
    username: str = ""
    api_key: str = ""
    timeout: int = 30
    max_connections: int = 10
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConnectionStats:
    """
    Connection statistics for a tenant

    Attributes:
        total_requests: Total number of requests
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        avg_response_time: Average response time in seconds
        last_request_at: Last request timestamp
        active_connections: Number of active connections
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_at: Optional[datetime] = None
    active_connections: int = 0


class OdooConnectionPool:
    """
    Connection pool manager for Odoo instances

    Features:
    - Per-tenant connection pooling
    - Automatic connection lifecycle management
    - Connection statistics tracking
    - Health checking
    """

    def __init__(self):
        # tenant_id -> httpx.AsyncClient
        self.connections: Dict[str, httpx.AsyncClient] = {}

        # tenant_id -> TenantConfig
        self.tenant_configs: Dict[str, TenantConfig] = {}

        # tenant_id -> ConnectionStats
        self.stats: Dict[str, ConnectionStats] = {}

        # Locks for thread-safe operations
        self._locks: Dict[str, asyncio.Lock] = {}

    async def add_tenant(self, config: TenantConfig):
        """
        Add a new tenant configuration

        Args:
            config: Tenant configuration

        Example:
            config = TenantConfig(
                tenant_id="odoo-prod",
                odoo_url="https://app.propanel.ma",
                database="production_db"
            )
            await pool.add_tenant(config)
        """
        self.tenant_configs[config.tenant_id] = config
        self.stats[config.tenant_id] = ConnectionStats()
        self._locks[config.tenant_id] = asyncio.Lock()

        logger.info(f"Added tenant: {config.tenant_id} -> {config.odoo_url}")

    async def remove_tenant(self, tenant_id: str):
        """
        Remove a tenant and close its connections

        Args:
            tenant_id: Tenant identifier
        """
        # Close connection if exists
        if tenant_id in self.connections:
            await self.connections[tenant_id].aclose()
            del self.connections[tenant_id]

        # Remove config and stats
        if tenant_id in self.tenant_configs:
            del self.tenant_configs[tenant_id]
        if tenant_id in self.stats:
            del self.stats[tenant_id]
        if tenant_id in self._locks:
            del self._locks[tenant_id]

        logger.info(f"Removed tenant: {tenant_id}")

    async def get_connection(self, tenant_id: str) -> httpx.AsyncClient:
        """
        Get or create connection for tenant

        Args:
            tenant_id: Tenant identifier

        Returns:
            HTTP client for tenant

        Raises:
            ValueError: If tenant not found or inactive
        """
        # Check if tenant exists
        if tenant_id not in self.tenant_configs:
            raise ValueError(f"Tenant not found: {tenant_id}")

        config = self.tenant_configs[tenant_id]

        # Check if tenant is active
        if not config.active:
            raise ValueError(f"Tenant is inactive: {tenant_id}")

        # Ensure lock exists
        if tenant_id not in self._locks:
            self._locks[tenant_id] = asyncio.Lock()

        # Get or create connection
        async with self._locks[tenant_id]:
            if tenant_id not in self.connections:
                # Create new connection
                client = httpx.AsyncClient(
                    base_url=config.odoo_url,
                    timeout=httpx.Timeout(config.timeout),
                    limits=httpx.Limits(
                        max_connections=config.max_connections,
                        max_keepalive_connections=config.max_connections // 2
                    ),
                    http2=True,  # Enable HTTP/2
                    follow_redirects=True
                )

                self.connections[tenant_id] = client
                logger.debug(f"Created connection for tenant: {tenant_id}")

            return self.connections[tenant_id]

    async def execute_request(
        self,
        tenant_id: str,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """
        Execute HTTP request for tenant

        Args:
            tenant_id: Tenant identifier
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response data

        Example:
            result = await pool.execute_request(
                tenant_id="odoo-prod",
                method="POST",
                endpoint="/jsonrpc",
                json={...}
            )
        """
        start_time = datetime.now()
        stats = self.stats.get(tenant_id, ConnectionStats())

        try:
            # Get connection
            client = await self.get_connection(tenant_id)

            # Update active connections
            stats.active_connections += 1

            # Execute request
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            # Update statistics
            stats.total_requests += 1
            stats.successful_requests += 1
            stats.last_request_at = datetime.now()

            # Update average response time
            duration = (datetime.now() - start_time).total_seconds()
            stats.avg_response_time = (
                (stats.avg_response_time * (stats.total_requests - 1) + duration)
                / stats.total_requests
            )

            logger.debug(
                f"Request successful for {tenant_id}: "
                f"{method} {endpoint} ({duration:.2f}s)"
            )

            return response.json()

        except Exception as e:
            # Update statistics
            stats.total_requests += 1
            stats.failed_requests += 1
            stats.last_request_at = datetime.now()

            logger.error(
                f"Request failed for {tenant_id}: "
                f"{method} {endpoint} - {str(e)}"
            )

            raise

        finally:
            # Decrement active connections
            stats.active_connections = max(0, stats.active_connections - 1)

    async def health_check(self, tenant_id: str) -> bool:
        """
        Check if tenant connection is healthy

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if healthy, False otherwise
        """
        try:
            config = self.tenant_configs.get(tenant_id)
            if not config:
                return False

            client = await self.get_connection(tenant_id)

            # Try a simple request
            response = await client.get("/web/database/list", timeout=5.0)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Health check failed for {tenant_id}: {str(e)}")
            return False

    async def get_stats(self, tenant_id: str) -> Optional[ConnectionStats]:
        """
        Get connection statistics for tenant

        Args:
            tenant_id: Tenant identifier

        Returns:
            Connection statistics or None
        """
        return self.stats.get(tenant_id)

    async def get_all_stats(self) -> Dict[str, ConnectionStats]:
        """
        Get connection statistics for all tenants

        Returns:
            Dictionary of tenant_id -> ConnectionStats
        """
        return self.stats.copy()

    async def close_all(self):
        """Close all tenant connections"""
        for tenant_id, client in self.connections.items():
            try:
                await client.aclose()
                logger.info(f"Closed connection for tenant: {tenant_id}")
            except Exception as e:
                logger.error(
                    f"Error closing connection for {tenant_id}: {str(e)}"
                )

        self.connections.clear()


# Singleton instance
connection_pool = OdooConnectionPool()


async def initialize_default_tenants():
    """
    Initialize default tenant configurations

    This should be called on application startup.
    In production, load tenant configs from database.
    """
    # Example: Add default tenant
    default_config = TenantConfig(
        tenant_id="odoo-default",
        odoo_url="https://app.propanel.ma",
        database="propanel_db",
        timeout=30,
        max_connections=10
    )

    await connection_pool.add_tenant(default_config)

    logger.info("Initialized default tenants")


async def shutdown_tenants():
    """
    Shutdown all tenant connections

    This should be called on application shutdown.
    """
    await connection_pool.close_all()
    logger.info("Shutdown all tenant connections")
