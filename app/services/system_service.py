"""
System Service for managing external system operations

This service orchestrates all CRUD operations, field mapping, and version handling
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from app.adapters.base_adapter import BaseAdapter
from app.adapters.odoo_adapter import OdooAdapter
from app.services.field_mapping_service import FieldMappingService
from app.services.version_handler import VersionHandler
from app.services.cache_service import CacheService
from app.services.audit_service import AuditService
import time


class SystemService:
    """
    Comprehensive system service

    Features:
    - CRUD operations with automatic field mapping
    - Version-aware transformations
    - Caching
    - Audit logging
    - Session management
    """

    def __init__(
        self,
        cache_service: CacheService,
        audit_service: AuditService
    ):
        self.cache = cache_service
        self.audit = audit_service
        self.field_mapping = FieldMappingService()
        self.version_handler = VersionHandler()
        self.adapters: Dict[str, BaseAdapter] = {}

    def _get_adapter(
        self,
        system_type: str,
        config: Dict[str, Any]
    ) -> BaseAdapter:
        """
        Get adapter instance for system type

        Args:
            system_type: System type (odoo, sap, etc.)
            config: System configuration

        Returns:
            Adapter instance
        """
        # Create adapter based on type
        if system_type.lower() == "odoo":
            return OdooAdapter(config)
        # Add more adapters here
        # elif system_type.lower() == "sap":
        #     return SAPAdapter(config)
        # elif system_type.lower() == "salesforce":
        #     return SalesforceAdapter(config)
        else:
            raise ValueError(f"Unsupported system type: {system_type}")

    async def connect_system(
        self,
        system_id: str,
        system_type: str,
        config: Dict[str, Any]
    ) -> BaseAdapter:
        """
        Connect to external system

        Args:
            system_id: Unique system identifier
            system_type: System type
            config: Connection configuration

        Returns:
            Connected adapter instance
        """
        adapter = self._get_adapter(system_type, config)
        await adapter.connect()

        # Authenticate if credentials provided
        if "username" in config and "password" in config:
            await adapter.authenticate(config["username"], config["password"])

        # Store adapter
        self.adapters[system_id] = adapter

        logger.info(f"Connected to system: {system_id} ({system_type})")
        return adapter

    async def disconnect_system(self, system_id: str) -> bool:
        """
        Disconnect from external system

        Args:
            system_id: System identifier

        Returns:
            True if successful
        """
        if system_id in self.adapters:
            await self.adapters[system_id].disconnect()
            del self.adapters[system_id]
            logger.info(f"Disconnected from system: {system_id}")
            return True
        return False

    async def create_record(
        self,
        user_id: int,
        system_id: str,
        model: str,
        data: Dict[str, Any],
        use_universal_schema: bool = False,
        system_version: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create record in external system

        Args:
            user_id: User ID for audit
            system_id: System identifier
            model: Model/entity name
            data: Record data (universal or system-specific)
            use_universal_schema: If True, transform from universal schema
            system_version: System version for mapping
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Creation result with record ID
        """
        start_time = time.time()
        adapter = self.adapters.get(system_id)

        if not adapter:
            raise ValueError(f"System not connected: {system_id}")

        try:
            # Transform from universal schema if needed
            if use_universal_schema and system_version:
                data = await self.field_mapping.transform_to_system(
                    data,
                    adapter.config.get("system_type", "odoo"),
                    system_version,
                    model
                )

            # Create record
            record_id = await adapter.create(model, data)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="create",
                model=model,
                record_id=str(record_id),
                request_data=data,
                response_data={"id": record_id},
                status="success",
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "record_id": record_id,
                "message": f"Record created successfully in {model}"
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log error
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="create",
                model=model,
                request_data=data,
                status="error",
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            logger.error(f"Create record error: {str(e)}")
            raise

    async def read_records(
        self,
        user_id: int,
        system_id: str,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
        use_universal_schema: bool = False,
        system_version: Optional[str] = None,
        use_cache: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records from external system

        Args:
            user_id: User ID for audit
            system_id: System identifier
            model: Model/entity name
            domain: Search filters
            fields: Fields to return
            limit: Maximum records
            offset: Records to skip
            order: Sort order
            use_universal_schema: If True, transform to universal schema
            system_version: System version for mapping
            use_cache: Whether to use caching
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            List of records
        """
        start_time = time.time()
        adapter = self.adapters.get(system_id)

        if not adapter:
            raise ValueError(f"System not connected: {system_id}")

        # Check cache
        cache_key = f"read:{system_id}:{model}:{domain}:{fields}:{limit}:{offset}"
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for read: {cache_key}")
                return cached_result

        try:
            # Read records
            records = await adapter.search_read(
                model=model,
                domain=domain,
                fields=fields,
                limit=limit,
                offset=offset,
                order=order
            )

            # Transform to universal schema if needed
            if use_universal_schema and system_version:
                records = [
                    await self.field_mapping.transform_to_universal(
                        record,
                        adapter.config.get("system_type", "odoo"),
                        system_version,
                        model
                    )
                    for record in records
                ]

            # Cache result (5 minutes for read operations)
            if use_cache:
                await self.cache.set(cache_key, records, ttl=300)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="read",
                model=model,
                request_data={"domain": domain, "fields": fields},
                response_data={"count": len(records)},
                status="success",
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            return records

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log error
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="read",
                model=model,
                request_data={"domain": domain},
                status="error",
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            logger.error(f"Read records error: {str(e)}")
            raise

    async def update_record(
        self,
        user_id: int,
        system_id: str,
        model: str,
        record_id: Any,
        data: Dict[str, Any],
        use_universal_schema: bool = False,
        system_version: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update record in external system

        Args:
            user_id: User ID for audit
            system_id: System identifier
            model: Model/entity name
            record_id: Record ID to update
            data: Updated data
            use_universal_schema: If True, transform from universal schema
            system_version: System version for mapping
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Update result
        """
        start_time = time.time()
        adapter = self.adapters.get(system_id)

        if not adapter:
            raise ValueError(f"System not connected: {system_id}")

        try:
            # Transform from universal schema if needed
            if use_universal_schema and system_version:
                data = await self.field_mapping.transform_to_system(
                    data,
                    adapter.config.get("system_type", "odoo"),
                    system_version,
                    model
                )

            # Update record
            success = await adapter.write(model, record_id, data)

            # Invalidate cache
            await self.cache.delete_pattern(f"read:{system_id}:{model}:*")

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="update",
                model=model,
                record_id=str(record_id),
                request_data=data,
                response_data={"success": success},
                status="success",
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            return {
                "success": success,
                "record_id": record_id,
                "message": f"Record updated successfully in {model}"
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log error
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="update",
                model=model,
                record_id=str(record_id),
                request_data=data,
                status="error",
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            logger.error(f"Update record error: {str(e)}")
            raise

    async def delete_record(
        self,
        user_id: int,
        system_id: str,
        model: str,
        record_id: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete record from external system

        Args:
            user_id: User ID for audit
            system_id: System identifier
            model: Model/entity name
            record_id: Record ID to delete
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            Deletion result
        """
        start_time = time.time()
        adapter = self.adapters.get(system_id)

        if not adapter:
            raise ValueError(f"System not connected: {system_id}")

        try:
            # Delete record
            success = await adapter.unlink(model, [record_id])

            # Invalidate cache
            await self.cache.delete_pattern(f"read:{system_id}:{model}:*")

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="delete",
                model=model,
                record_id=str(record_id),
                response_data={"success": success},
                status="success",
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            return {
                "success": success,
                "record_id": record_id,
                "message": f"Record deleted successfully from {model}"
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Audit log error
            await self.audit.log_operation(
                user_id=user_id,
                system_id=self._get_system_db_id(system_id),
                action="delete",
                model=model,
                record_id=str(record_id),
                status="error",
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )

            logger.error(f"Delete record error: {str(e)}")
            raise

    async def get_metadata(
        self,
        system_id: str,
        model: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get model metadata from external system

        Args:
            system_id: System identifier
            model: Model/entity name
            use_cache: Whether to use caching

        Returns:
            Model metadata
        """
        adapter = self.adapters.get(system_id)

        if not adapter:
            raise ValueError(f"System not connected: {system_id}")

        # Check cache (metadata cached for 30 minutes)
        cache_key = f"metadata:{system_id}:{model}"
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for metadata: {cache_key}")
                return cached_result

        try:
            metadata = await adapter.get_metadata(model)

            # Cache metadata
            if use_cache:
                await self.cache.set(cache_key, metadata, ttl=1800)

            return metadata

        except Exception as e:
            logger.error(f"Get metadata error: {str(e)}")
            raise

    def _get_system_db_id(self, system_id: str) -> int:
        """
        Get database ID for system (temporary - should query from DB)

        Args:
            system_id: System identifier

        Returns:
            Database ID
        """
        # TODO: Query from database
        # For now, return dummy ID
        return 1
