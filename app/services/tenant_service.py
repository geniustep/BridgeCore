"""
Tenant service for tenant business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import httpx

from app.repositories.tenant_repository import TenantRepository
from app.repositories.plan_repository import PlanRepository
from app.models.tenant import Tenant, TenantStatus
from app.core.encryption import encryption_service
from fastapi import HTTPException, status


class TenantService:
    """Service for tenant operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)
        self.plan_repo = PlanRepository(session)

    async def create_tenant(
        self,
        name: str,
        slug: str,
        contact_email: str,
        odoo_url: str,
        odoo_database: str,
        odoo_username: str,
        odoo_password: str,
        plan_id: UUID,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> Tenant:
        """
        Create a new tenant

        Args:
            name: Tenant name
            slug: Unique slug
            contact_email: Contact email
            odoo_url: Odoo instance URL
            odoo_database: Odoo database name
            odoo_username: Odoo username
            odoo_password: Odoo password (will be encrypted)
            plan_id: Subscription plan ID
            created_by: Admin ID who created the tenant
            **kwargs: Additional optional fields

        Returns:
            Created tenant instance

        Raises:
            HTTPException: If slug is taken or plan doesn't exist
        """
        # Check if slug is taken
        if await self.tenant_repo.is_slug_taken(slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already taken"
            )

        # Verify plan exists
        plan = await self.plan_repo.get_by_id_uuid(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )

        # Create tenant
        # Encrypt password for storage (can be decrypted when needed for Odoo)
        encrypted_password = encryption_service.encrypt_value(odoo_password)
        
        tenant = Tenant(
            name=name,
            slug=slug,
            contact_email=contact_email,
            odoo_url=odoo_url,
            odoo_database=odoo_database,
            odoo_username=odoo_username,
            odoo_password=encrypted_password,  # Encrypted for storage
            plan_id=plan_id,
            status=TenantStatus.TRIAL,
            created_by=created_by,
            **kwargs
        )

        return await self.tenant_repo.create(tenant)

    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """
        Get tenant by ID

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant instance or None
        """
        return await self.tenant_repo.get_by_id_uuid(tenant_id)

    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug

        Args:
            slug: Tenant slug

        Returns:
            Tenant instance or None
        """
        return await self.tenant_repo.get_by_slug(slug)

    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenantStatus] = None
    ) -> List[Tenant]:
        """
        List tenants with pagination and optional status filter

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of tenants
        """
        filters = {"status": status} if status else None
        return await self.tenant_repo.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="-created_at"
        )

    async def update_tenant(
        self,
        tenant_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[Tenant]:
        """
        Update tenant

        Args:
            tenant_id: Tenant UUID
            data: Dictionary of fields to update

        Returns:
            Updated tenant instance or None

        Raises:
            HTTPException: If slug is already taken by another tenant
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return None

        # Check slug uniqueness if updating slug
        if "slug" in data and data["slug"] != tenant.slug:
            if await self.tenant_repo.is_slug_taken(data["slug"], exclude_id=tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slug already taken"
                )

        # Encrypt password if updating
        if "odoo_password" in data:
            data["odoo_password"] = encryption_service.encrypt_value(data["odoo_password"])

        # Update fields
        for key, value in data.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def suspend_tenant(self, tenant_id: UUID) -> bool:
        """
        Suspend tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if suspended, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.SUSPENDED
        await self.session.commit()
        return True

    async def activate_tenant(self, tenant_id: UUID) -> bool:
        """
        Activate tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if activated, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.ACTIVE
        await self.session.commit()
        return True

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        """
        Soft delete tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if deleted, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED
        tenant.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def test_odoo_connection(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Test Odoo connection for a tenant with full authentication and database verification

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dictionary with detailed connection test results including:
            - success: Boolean indicating if connection is successful
            - message: Human-readable message
            - url: Odoo URL tested
            - database: Database name
            - version: Odoo version (if available)
            - user_info: User information (if authentication successful)
            - details: Additional connection details

        Raises:
            HTTPException: If tenant not found
        """
        from loguru import logger
        from app.adapters.odoo_adapter import OdooAdapter
        
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        result = {
            "success": False,
            "message": "",
            "url": tenant.odoo_url,
            "database": tenant.odoo_database,
            "version": None,
            "user_info": None,
            "details": {}
        }

        try:
            # Use OdooAdapter for proper authentication (same as /api/v1/auth/login)
            # Decrypt password for Odoo authentication
            try:
                decrypted_password = encryption_service.decrypt_value(tenant.odoo_password)
                logger.info(f"[TEST CONNECTION] Password decrypted successfully")
            except Exception as decrypt_error:
                # If decryption fails, try using as-is (might be plain text from old records or hash)
                logger.warning(f"[TEST CONNECTION] Password decryption failed, using as-is: {str(decrypt_error)}")
                decrypted_password = tenant.odoo_password
            
            odoo_config = {
                "url": tenant.odoo_url,
                "database": tenant.odoo_database,
                "username": tenant.odoo_username,
                "password": decrypted_password  # Use decrypted password
            }
            
            adapter = OdooAdapter(odoo_config)
            
            # Step 1: Test basic connection first
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    # Try to reach Odoo
                    test_url = f"{tenant.odoo_url.rstrip('/')}/web"
                    try:
                        test_response = await client.get(test_url, timeout=10.0)
                        if test_response.status_code in [200, 301, 302, 303, 307, 308]:
                            result["details"]["connection_reachable"] = True
                            logger.info(f"Odoo instance is reachable: {tenant.odoo_url}")
                        else:
                            result["details"]["connection_reachable"] = False
                            logger.warning(f"Odoo returned status {test_response.status_code}")
                    except httpx.TimeoutException:
                        result["details"]["connection_reachable"] = False
                        result["success"] = False
                        result["message"] = "Connection test failed: Timeout - Odoo server is not responding. Please check the URL and network connectivity."
                        result["details"]["timeout"] = True
                        return result
                    except httpx.RequestError as e:
                        result["details"]["connection_reachable"] = False
                        result["success"] = False
                        result["message"] = f"Connection test failed: Cannot reach Odoo instance - {str(e)}. Please check the URL: {tenant.odoo_url}"
                        result["details"]["connection_error"] = str(e)
                        return result
            except Exception as conn_error:
                logger.warning(f"Connection test warning: {str(conn_error)}")
                # Continue anyway - authentication will reveal the real issue
            
            # Step 2: Authenticate
            try:
                logger.info(f"[TEST CONNECTION] Starting authentication process")
                logger.info(f"[TEST CONNECTION] Odoo URL: {tenant.odoo_url}")
                logger.info(f"[TEST CONNECTION] Database: {tenant.odoo_database}")
                logger.info(f"[TEST CONNECTION] Username: {tenant.odoo_username}")
                logger.info(f"[TEST CONNECTION] Password: {'*' * len(decrypted_password) if decrypted_password else 'None'}")
                
                auth_result = await adapter.authenticate(tenant.odoo_username, decrypted_password)
                
                logger.info(f"[TEST CONNECTION] Authentication result: success={auth_result.get('success')}, has_uid={bool(auth_result.get('uid'))}")
                
                if not auth_result.get("success"):
                    error_msg = auth_result.get("error", "Authentication failed")
                    logger.error(f"Odoo authentication error: {error_msg}")
                    
                    result["success"] = False
                    result["message"] = f"Connection test failed: {error_msg}"
                    result["details"]["authentication_failed"] = True
                    result["details"]["connection_reachable"] = True  # Connection worked, auth failed
                    result["details"]["auth_error"] = {
                        "message": error_msg,
                        "detailed_message": error_msg
                    }
                    try:
                        await adapter.disconnect()
                    except:
                        pass
                    return result
                
                # Authentication successful!
                uid = auth_result.get("uid")
                session_id = auth_result.get("session_id")
                user_context = auth_result.get("user_context", {})
                
                logger.info(f"Authentication successful - uid: {uid}, session_id: {session_id[:20] if session_id else 'None'}...")
                
                # Step 3: Get user information from Odoo
                try:
                    user_data = await adapter.search_read(
                        model="res.users",
                        domain=[["id", "=", uid]],
                        fields=["name", "login", "email", "company_id", "partner_id"]
                    )
                    
                    if user_data and len(user_data) > 0:
                        user_info_data = user_data[0]
                        result["user_info"] = {
                            "uid": uid,
                            "username": user_info_data.get("login", tenant.odoo_username),
                            "name": user_info_data.get("name", ""),
                            "email": user_info_data.get("email", ""),
                            "company_id": user_info_data.get("company_id"),
                            "partner_id": user_info_data.get("partner_id"),
                            "session_id": session_id
                        }
                        result["details"]["user_data"] = user_info_data
                        result["details"]["database_query_success"] = True
                    else:
                        # Fallback to basic info
                        result["user_info"] = {
                            "uid": uid,
                            "username": tenant.odoo_username,
                            "name": user_context.get("name", tenant.odoo_username),
                            "company_id": user_context.get("company_id"),
                            "partner_id": user_context.get("partner_id"),
                            "session_id": session_id
                        }
                except Exception as query_error:
                    logger.warning(f"Failed to query user data: {str(query_error)}")
                    # Use basic info from auth result
                    result["user_info"] = {
                        "uid": uid,
                        "username": tenant.odoo_username,
                        "name": user_context.get("name", tenant.odoo_username),
                        "company_id": user_context.get("company_id"),
                        "partner_id": user_context.get("partner_id"),
                        "session_id": session_id
                    }
                    result["details"]["query_error"] = str(query_error)

                # Step 4: Try to get Odoo version
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        version_url = f"{tenant.odoo_url.rstrip('/')}/web/webclient/version_info"
                        version_response = await client.get(version_url)
                        if version_response.status_code == 200:
                            version_data = version_response.json()
                            result["version"] = version_data.get("server_version", "Unknown")
                            result["details"]["server_serie"] = version_data.get("server_serie")
                except Exception as version_error:
                    logger.debug(f"Could not get version info: {str(version_error)}")
                    # Version info is optional

                # Success!
                result["success"] = True
                result["message"] = f"Connection successful - Authenticated as {result['user_info'].get('name', result['user_info'].get('username'))} in database '{tenant.odoo_database}'"
                result["details"]["authenticated"] = True
                result["details"]["uid"] = uid
                
                await adapter.disconnect()
                return result

            except Exception as auth_error:
                logger.error(f"Authentication error: {str(auth_error)}")
                result["success"] = False
                result["message"] = f"Connection test failed: Authentication error - {str(auth_error)}"
                result["details"]["authentication_failed"] = True
                result["details"]["auth_error"] = {
                    "message": str(auth_error),
                    "detailed_message": str(auth_error)
                }
                try:
                    await adapter.disconnect()
                except:
                    pass
                return result

        except httpx.TimeoutException:
            result["success"] = False
            result["message"] = "Connection test failed: Connection timeout - Odoo server is not responding"
            result["details"]["timeout"] = True
            return result
        except httpx.RequestError as e:
            result["success"] = False
            result["message"] = f"Connection test failed: Connection error - {str(e)}"
            result["details"]["connection_error"] = str(e)
            return result
        except Exception as e:
            logger.error(f"Unexpected error in test_odoo_connection: {str(e)}")
            result["success"] = False
            result["message"] = f"Connection test failed: Unexpected error - {str(e)}"
            result["details"]["unexpected_error"] = str(e)
            return result

    async def get_tenant_statistics(self) -> Dict[str, Any]:
        """
        Get overall tenant statistics

        Returns:
            Dictionary with tenant statistics
        """
        total = await self.tenant_repo.count()
        active = await self.tenant_repo.count_by_status(TenantStatus.ACTIVE)
        suspended = await self.tenant_repo.count_by_status(TenantStatus.SUSPENDED)
        trial = await self.tenant_repo.count_by_status(TenantStatus.TRIAL)
        deleted = await self.tenant_repo.count_by_status(TenantStatus.DELETED)

        return {
            "total": total,
            "active": active,
            "suspended": suspended,
            "trial": trial,
            "deleted": deleted
        }
