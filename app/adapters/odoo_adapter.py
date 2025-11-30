"""
Odoo Adapter Implementation
"""
import httpx
import json
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.adapters.base_adapter import BaseAdapter


class OdooAdapter(BaseAdapter):
    """
    Complete Odoo adapter with session management and smart fallback

    Features:
    - Full CRUD operations
    - Session management with auto-refresh
    - Smart field fallback
    - Connection retry logic
    - Odoo-specific optimizations
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.database = config.get("database")
        self.username = config.get("username")
        self.password = config.get("password")
        self.uid = None
        self.session_id = None
        self.context = config.get("context", {})

        # HTTP client with timeout and cookies support
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0),  # Like gmobile
            follow_redirects=True,
            cookies={}  # Enable cookie storage
        )

        # Smart field fallbacks
        self.field_fallbacks = {
            'phone': ['mobile', 'phone_primary', 'phone_secondary'],
            'name': ['display_name', 'partner_name', 'complete_name'],
            'price': ['list_price', 'standard_price', 'sale_price'],
            'email': ['email_from', 'partner_email'],
            'street': ['street', 'street1'],
            'city': ['city', 'city_id'],
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def connect(self) -> bool:
        """
        Establish connection to Odoo with retry logic

        Returns:
            True if connection successful
        """
        try:
            # Test connection
            response = await self.client.get(f"{self.url}/web/database/list")
            self.is_connected = response.status_code == 200
            return self.is_connected
        except Exception as e:
            logger.error(f"Odoo connection failed: {str(e)}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP client"""
        await self.client.aclose()
        self.is_connected = False
        return True

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Odoo

        Args:
            username: Odoo username
            password: Odoo password

        Returns:
            Authentication result with uid and session info
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": self.database,
                "login": username,
                "password": password
            }
        }

        try:
            # Use URL as-is (Odoo is at root, not /odoo)
            auth_url = self.url.rstrip('/')
            full_auth_url = f"{auth_url}/web/session/authenticate"
            
            # Log detailed request information
            logger.info(f"[ODOO AUTH] Starting authentication request")
            logger.info(f"[ODOO AUTH] Endpoint: {full_auth_url}")
            logger.info(f"[ODOO AUTH] Database: {self.database}")
            logger.info(f"[ODOO AUTH] Username: {username}")
            logger.info(f"[ODOO AUTH] Payload: {json.dumps(payload, indent=2)}")
            logger.info(f"[ODOO AUTH] Headers: Content-Type: application/json")
            
            response = await self.client.post(
                full_auth_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"[ODOO AUTH] Response status: {response.status_code}")
            logger.info(f"[ODOO AUTH] Response headers: {dict(response.headers)}")

            # Check if response is JSON
            try:
                result = response.json()
                logger.info(f"[ODOO AUTH] Response body (first 500 chars): {str(result)[:500]}")
            except Exception as json_error:
                logger.error(f"[ODOO AUTH] Odoo returned non-JSON response: {response.headers.get('content-type', 'unknown')}. Status: {response.status_code}")
                logger.error(f"[ODOO AUTH] Response text (first 500 chars): {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"Invalid response from Odoo: {str(json_error)}"
                }

            if "result" in result and result["result"].get("uid"):
                self.uid = result["result"]["uid"]
                # Get session_id from cookies - httpx automatically stores cookies
                self.session_id = response.cookies.get("session_id") or response.cookies.get("session_id_http")
                self.is_connected = True
                
                # Log cookies for debugging
                logger.info(f"[ODOO AUTH] Session cookies: {dict(response.cookies)}")
                logger.info(f"[ODOO AUTH] Authentication successful - User: {username}, UID: {self.uid}, Session ID: {self.session_id[:20] if self.session_id else 'None'}...")
                logger.info(f"[ODOO AUTH] User context: {result['result'].get('user_context', {})}")

                return {
                    "success": True,
                    "uid": self.uid,
                    "session_id": self.session_id,
                    "user_context": result["result"].get("user_context", {})
                }
            else:
                error_data = result.get("error", {})
                error_msg = error_data.get("message", "Authentication failed") if error_data else "Authentication failed"
                error_details = error_data.get("data", {}) if isinstance(error_data, dict) else {}
                
                logger.error(f"[ODOO AUTH] Authentication failed")
                logger.error(f"[ODOO AUTH] Error message: {error_msg}")
                logger.error(f"[ODOO AUTH] Full error object: {json.dumps(error_data, indent=2) if error_data else 'No error data'}")
                if error_details:
                    logger.error(f"[ODOO AUTH] Error details: {json.dumps(error_details, indent=2)}")
                
                return {
                    "success": False,
                    "error": error_msg
                }

        except Exception as e:
            logger.error(f"Odoo authentication error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records from Odoo

        Args:
            model: Odoo model name (e.g., 'res.partner')
            domain: Search domain (e.g., [['is_company', '=', True]])
            fields: List of fields to return
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order (e.g., 'name ASC')

        Returns:
            List of records with smart field fallback
        """
        params = {
            "model": model,
            "domain": domain or [],
            "fields": fields or [],
            "limit": limit or 80,
            "offset": offset or 0,
            "context": self.context
        }

        if order:
            params["sort"] = order

        start_time = time.time()
        
        try:
            # Use call_kw endpoint for Odoo 18+
            call_params = {
                "model": model,
                "method": "search_read",
                "args": [],
                "kwargs": {
                    "domain": domain or [],
                    "fields": fields or [],
                    "limit": limit or 80,
                    "offset": offset or 0,
                    "order": order or None,
                    "context": self.context
                }
            }
            
            logger.info(
                f"🔍 [SEARCHREAD] Starting search_read operation\n"
                f"   Model: {model}\n"
                f"   Domain: {domain or []}\n"
                f"   Fields: {fields or []}\n"
                f"   Limit: {limit or 80}\n"
                f"   Offset: {offset or 0}\n"
                f"   Order: {order or None}"
            )
            
            result = await self._call_odoo(
                "/web/dataset/call_kw",
                call_params
            )

            # Result is already a list of records from call_kw
            records = result if isinstance(result, list) else result.get("records", [])

            # Apply smart field fallback
            if fields:
                records = self._apply_field_fallback(records, fields)

            duration = (time.time() - start_time) * 1000  # milliseconds
            logger.info(
                f"✅ [SEARCHREAD] Completed successfully\n"
                f"   Model: {model}\n"
                f"   Records found: {len(records)}\n"
                f"   Duration: {duration:.2f}ms"
            )

            return records

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"❌ [SEARCHREAD] Error: {str(e)}\n"
                f"   Model: {model}\n"
                f"   Domain: {domain or []}\n"
                f"   Duration: {duration:.2f}ms",
                exc_info=True
            )
            raise

    async def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> Any:
        """
        Create record in Odoo

        Args:
            model: Odoo model name
            values: Record data

        Returns:
            Created record ID
        """
        params = {
            "model": model,
            "method": "create",
            "args": [values],
            "kwargs": {"context": self.context}
        }

        try:
            result = await self._call_odoo("/web/dataset/call_kw", params)
            logger.info(f"Created {model} record with ID: {result}")
            return result

        except Exception as e:
            logger.error(f"Odoo create error: {str(e)}")
            raise

    async def write(
        self,
        model: str,
        record_id: Any,
        values: Dict[str, Any]
    ) -> bool:
        """
        Update record in Odoo

        Args:
            model: Odoo model name
            record_id: Record ID to update
            values: Updated data

        Returns:
            True if successful
        """
        params = {
            "model": model,
            "method": "write",
            "args": [[record_id], values],
            "kwargs": {"context": self.context}
        }

        try:
            result = await self._call_odoo("/web/dataset/call_kw", params)
            logger.info(f"Updated {model} record ID: {record_id}")
            return bool(result)

        except Exception as e:
            logger.error(f"Odoo write error: {str(e)}")
            raise

    async def unlink(
        self,
        model: str,
        record_ids: List[Any]
    ) -> bool:
        """
        Delete records from Odoo

        Args:
            model: Odoo model name
            record_ids: List of record IDs to delete

        Returns:
            True if successful
        """
        params = {
            "model": model,
            "method": "unlink",
            "args": [record_ids],
            "kwargs": {"context": self.context}
        }

        try:
            result = await self._call_odoo("/web/dataset/call_kw", params)
            logger.info(f"Deleted {model} records: {record_ids}")
            return bool(result)

        except Exception as e:
            logger.error(f"Odoo unlink error: {str(e)}")
            raise

    async def call_method(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Call custom Odoo method

        Args:
            model: Odoo model name
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result
        """
        params = {
            "model": model,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {"context": self.context}
        }

        try:
            result = await self._call_odoo("/web/dataset/call_kw", params)
            return result

        except Exception as e:
            logger.error(f"Odoo call_method error: {str(e)}")
            raise

    async def get_metadata(
        self,
        model: str
    ) -> Dict[str, Any]:
        """
        Get Odoo model metadata

        Args:
            model: Odoo model name

        Returns:
            Model fields information
        """
        try:
            result = await self.call_method(
                model,
                "fields_get",
                kwargs={"context": self.context}
            )

            return result

        except Exception as e:
            logger.error(f"Odoo get_metadata error: {str(e)}")
            raise

    async def check_connection(self) -> bool:
        """
        Check if Odoo session is still valid

        Returns:
            True if session is active
        """
        try:
            response = await self.client.post(
                f"{self.url}/web/session/get_session_info",
                json={"jsonrpc": "2.0", "method": "call", "params": {}}
            )

            result = response.json()

            if "result" in result:
                session_info = result["result"]
                return session_info.get("uid") is not None

            return False

        except Exception as e:
            logger.error(f"Odoo check_connection error: {str(e)}")
            return False

    async def refresh_session(self) -> bool:
        """
        Refresh Odoo session

        Returns:
            True if refresh successful
        """
        if not await self.check_connection():
            # Re-authenticate
            result = await self.authenticate(self.username, self.password)
            return result.get("success", False)

        return True

    async def _call_odoo(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """
        Internal method to call Odoo API

        Args:
            endpoint: Odoo endpoint
            params: Request parameters

        Returns:
            Response result

        Raises:
            Exception: If session expired (code 100) or other errors
        """
        start_time = time.time()
        
        # Extract method info for logging
        method_name = params.get("method", "unknown")
        model_name = params.get("model", "unknown")
        is_call_kw = endpoint == "/web/dataset/call_kw" and method_name != "search_read"
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params
        }

        try:
            # Log call_kw operations (but not search_read, as it's already logged)
            if is_call_kw:
                logger.info(
                    f"🔧 [CALL_KW] Starting call_kw operation\n"
                    f"   Model: {model_name}\n"
                    f"   Method: {method_name}\n"
                    f"   Args: {params.get('args', [])}\n"
                    f"   Kwargs keys: {list(params.get('kwargs', {}).keys())}"
                )
            
            # Add id to payload if not present (required by Odoo JSON-RPC)
            if "id" not in payload:
                payload["id"] = 1
            
            response = await self.client.post(
                f"{self.url}{endpoint}",
                json=payload
            )

            duration = (time.time() - start_time) * 1000

            # Check if response is JSON
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                response_text = response.text[:500]  # First 500 chars
                logger.error(
                    f"❌ [CALL_KW] Odoo returned non-JSON response\n"
                    f"   Endpoint: {endpoint}\n"
                    f"   Model: {model_name}\n"
                    f"   Method: {method_name}\n"
                    f"   Content-Type: {content_type}\n"
                    f"   Status: {response.status_code}\n"
                    f"   Response: {response_text}\n"
                    f"   Duration: {duration:.2f}ms"
                )
                # Try to get more info about the request
                logger.error(f"Request cookies: {dict(self.client.cookies)}")
                raise Exception(f"Odoo returned non-JSON response: {content_type}. Status: {response.status_code}")

            result = response.json()

            # Check for session expiry (code 100)
            if "error" in result:
                error = result["error"]
                if error.get("code") == 100:
                    logger.warning(
                        f"⚠️ [CALL_KW] Odoo session expired, refreshing...\n"
                        f"   Model: {model_name}\n"
                        f"   Method: {method_name}"
                    )
                    await self.refresh_session()
                    # Retry request
                    return await self._call_odoo(endpoint, params)

                logger.error(
                    f"❌ [CALL_KW] Odoo error: {error.get('message', 'Unknown error')}\n"
                    f"   Model: {model_name}\n"
                    f"   Method: {method_name}\n"
                    f"   Error code: {error.get('code')}\n"
                    f"   Duration: {duration:.2f}ms"
                )
                raise Exception(f"Odoo error: {error.get('message', 'Unknown error')}")

            # Log successful call_kw (but not search_read)
            if is_call_kw:
                result_preview = str(result.get("result", ""))[:200] if result.get("result") else "None"
                logger.info(
                    f"✅ [CALL_KW] Completed successfully\n"
                    f"   Model: {model_name}\n"
                    f"   Method: {method_name}\n"
                    f"   Result preview: {result_preview}\n"
                    f"   Duration: {duration:.2f}ms"
                )

            return result.get("result")

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"❌ [CALL_KW] API call error: {str(e)}\n"
                f"   Endpoint: {endpoint}\n"
                f"   Model: {model_name}\n"
                f"   Method: {method_name}\n"
                f"   Duration: {duration:.2f}ms",
                exc_info=True
            )
            raise

    def _apply_field_fallback(
        self,
        records: List[Dict[str, Any]],
        requested_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Apply smart field fallback for missing fields

        Args:
            records: List of records
            requested_fields: Fields that were requested

        Returns:
            Records with fallback fields applied
        """
        for record in records:
            for field in requested_fields:
                if field not in record or record[field] is False:
                    # Try fallback fields
                    if field in self.field_fallbacks:
                        for fallback_field in self.field_fallbacks[field]:
                            if fallback_field in record and record[fallback_field]:
                                record[field] = record[fallback_field]
                                logger.debug(
                                    f"Used fallback: {fallback_field} -> {field}"
                                )
                                break

        return records

    async def execute_kw(
        self,
        model: str,
        method: str,
        args: List,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute Odoo method (alternative to call_method)

        Args:
            model: Odoo model name
            method: Method name
            args: Arguments
            kwargs: Keyword arguments

        Returns:
            Method result
        """
        return await self.call_method(model, method, args, kwargs)

    async def name_search(
        self,
        model: str,
        name: str = "",
        domain: Optional[List] = None,
        limit: int = 10
    ) -> List[tuple]:
        """
        Search for records by name

        Args:
            model: Odoo model name
            name: Name to search for
            domain: Additional filters
            limit: Maximum results

        Returns:
            List of (id, name) tuples
        """
        return await self.call_method(
            model,
            "name_search",
            kwargs={
                "name": name,
                "args": domain or [],
                "limit": limit,
                "context": self.context
            }
        )
