"""
Moodle Adapter Implementation
Supports Moodle Web Services API (REST)
"""
import httpx
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.adapters.base_adapter import BaseAdapter


class MoodleAdapter(BaseAdapter):
    """
    Complete Moodle adapter using Web Services API

    Features:
    - Token-based authentication
    - REST API support
    - Course management
    - User management
    - Enrolment operations
    - Grade operations
    - Connection retry logic

    Moodle Web Services Documentation:
    https://docs.moodle.org/dev/Web_services
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url").rstrip('/')  # e.g., "https://lms.example.com"
        self.token = config.get("token")  # Web services token
        self.service = config.get("service", "moodle_mobile_app")  # Default service
        self.format = "json"  # Response format

        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0),
            follow_redirects=True
        )

        # Moodle API endpoint
        self.api_endpoint = f"{self.url}/webservice/rest/server.php"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def connect(self) -> bool:
        """
        Test connection to Moodle

        Returns:
            True if connection successful
        """
        try:
            # Test with core_webservice_get_site_info
            result = await self._call_function("core_webservice_get_site_info")
            self.is_connected = "sitename" in result
            return self.is_connected
        except Exception as e:
            logger.error(f"Moodle connection failed: {str(e)}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP client"""
        await self.client.aclose()
        self.is_connected = False
        return True

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Moodle (get token)

        Note: This requires login service to be enabled in Moodle
        Typically, tokens are pre-generated in Moodle admin panel

        Args:
            username: Moodle username
            password: Moodle password

        Returns:
            Authentication result with token
        """
        try:
            login_url = f"{self.url}/login/token.php"
            params = {
                "username": username,
                "password": password,
                "service": self.service
            }

            response = await self.client.post(login_url, data=params)
            result = response.json()

            if "token" in result:
                self.token = result["token"]
                return {
                    "success": True,
                    "token": self.token,
                    "user": result.get("privatetoken")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Authentication failed")
                }
        except Exception as e:
            logger.error(f"Moodle authentication failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _call_function(
        self,
        function_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Call Moodle Web Service function

        Args:
            function_name: Moodle function name (e.g., "core_course_get_courses")
            params: Function parameters

        Returns:
            Function result

        Raises:
            Exception if API call fails
        """
        request_params = {
            "wstoken": self.token,
            "wsfunction": function_name,
            "moodlewsrestformat": self.format
        }

        if params:
            # Flatten nested parameters for Moodle API
            flattened = self._flatten_params(params)
            request_params.update(flattened)

        try:
            response = await self.client.post(self.api_endpoint, data=request_params)
            response.raise_for_status()

            result = response.json()

            # Check for Moodle error response
            if isinstance(result, dict) and "exception" in result:
                raise Exception(f"Moodle API Error: {result.get('message', 'Unknown error')}")

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Moodle API HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Moodle API call failed: {str(e)}")
            raise

    def _flatten_params(self, params: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten nested parameters for Moodle API format

        Example:
            {"criteria": [{"key": "id", "value": 1}]}
            -> {"criteria[0][key]": "id", "criteria[0][value]": 1}
        """
        flattened = {}

        for key, value in params.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(self._flatten_params(value, f"{full_key}["))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(self._flatten_params(item, f"{full_key}[{i}]["))
                    else:
                        flattened[f"{full_key}[{i}]"] = item
            else:
                flattened[full_key] = value

        return flattened

    # ============= BaseAdapter Implementation =============

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
        Search and read records from Moodle

        Args:
            model: Moodle entity (courses, users, etc.)
            domain: Search criteria (simplified)
            fields: Fields to return (not used - Moodle returns all)
            limit: Maximum number of records
            offset: Number of records to skip (not supported)
            order: Sorting (not directly supported)

        Returns:
            List of records
        """
        # Map model names to Moodle functions
        function_map = {
            "courses": "core_course_get_courses",
            "users": "core_user_get_users",
            "categories": "core_course_get_categories",
            "enrolments": "core_enrol_get_enrolled_users"
        }

        if model not in function_map:
            raise ValueError(f"Unsupported Moodle model: {model}")

        function = function_map[model]
        params = {}

        # Handle domain filters
        if domain and model == "users":
            # Convert domain to Moodle criteria format
            criteria = []
            for condition in domain:
                if len(condition) == 3:
                    field, operator, value = condition
                    criteria.append({"key": field, "value": str(value)})
            if criteria:
                params["criteria"] = criteria

        result = await self._call_function(function, params)

        # Apply limit if specified
        if limit and isinstance(result, list):
            result = result[:limit]

        return result if isinstance(result, list) else [result]

    async def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> Any:
        """
        Create a new record in Moodle

        Args:
            model: Moodle entity
            values: Record data

        Returns:
            Created record ID
        """
        function_map = {
            "courses": "core_course_create_courses",
            "users": "core_user_create_users",
            "categories": "core_course_create_categories"
        }

        if model not in function_map:
            raise ValueError(f"Unsupported Moodle model for create: {model}")

        function = function_map[model]

        # Wrap values in array (Moodle expects arrays)
        params = {f"{model}": [values]}

        result = await self._call_function(function, params)

        # Return first created ID
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("id")
        return result

    async def write(
        self,
        model: str,
        record_id: Any,
        values: Dict[str, Any]
    ) -> bool:
        """
        Update an existing record in Moodle

        Args:
            model: Moodle entity
            record_id: Record ID to update
            values: Updated data

        Returns:
            True if successful
        """
        function_map = {
            "courses": "core_course_update_courses",
            "users": "core_user_update_users",
            "categories": "core_course_update_categories"
        }

        if model not in function_map:
            raise ValueError(f"Unsupported Moodle model for write: {model}")

        function = function_map[model]

        # Add ID to values
        values["id"] = record_id

        # Wrap in array
        params = {f"{model}": [values]}

        result = await self._call_function(function, params)

        return True if result else False

    async def unlink(
        self,
        model: str,
        record_ids: List[Any]
    ) -> bool:
        """
        Delete records from Moodle

        Args:
            model: Moodle entity
            record_ids: List of record IDs to delete

        Returns:
            True if successful
        """
        function_map = {
            "courses": "core_course_delete_courses",
            "users": "core_user_delete_users",
            "categories": "core_course_delete_categories"
        }

        if model not in function_map:
            raise ValueError(f"Unsupported Moodle model for delete: {model}")

        function = function_map[model]

        # Moodle expects array of IDs
        params = {f"{model}ids": record_ids}

        result = await self._call_function(function, params)

        return True

    async def call_method(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Call a custom Moodle Web Service function

        Args:
            model: Not used (Moodle doesn't have models)
            method: Moodle function name (e.g., "core_course_get_courses")
            args: Not used
            kwargs: Function parameters

        Returns:
            Method result
        """
        return await self._call_function(method, kwargs)

    async def get_metadata(
        self,
        model: str
    ) -> Dict[str, Any]:
        """
        Get metadata about Moodle site

        Args:
            model: Not used

        Returns:
            Site information
        """
        return await self._call_function("core_webservice_get_site_info")

    async def check_connection(self) -> bool:
        """
        Check if connection is still alive

        Returns:
            True if connection is active
        """
        try:
            await self._call_function("core_webservice_get_site_info")
            return True
        except:
            return False

    # ============= Moodle-Specific Methods =============

    async def get_courses(self, course_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get courses (all or by IDs)"""
        params = {}
        if course_ids:
            params["options"] = {"ids": course_ids}

        return await self._call_function("core_course_get_courses", params)

    async def get_users(self, criteria: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
        """Get users by criteria"""
        params = {}
        if criteria:
            params["criteria"] = criteria

        return await self._call_function("core_user_get_users", params)

    async def get_enrolled_users(self, course_id: int) -> List[Dict[str, Any]]:
        """Get users enrolled in a course"""
        params = {"courseid": course_id}
        return await self._call_function("core_enrol_get_enrolled_users", params)

    async def enrol_user(self, course_id: int, user_id: int, role_id: int = 5) -> bool:
        """
        Enrol user in course

        Args:
            course_id: Course ID
            user_id: User ID
            role_id: Role ID (5 = student by default)
        """
        params = {
            "enrolments": [{
                "roleid": role_id,
                "userid": user_id,
                "courseid": course_id
            }]
        }
        await self._call_function("enrol_manual_enrol_users", params)
        return True

    async def get_grades(self, course_id: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get grades for a course"""
        params = {"courseid": course_id}
        if user_id:
            params["userid"] = user_id

        return await self._call_function("gradereport_user_get_grade_items", params)
