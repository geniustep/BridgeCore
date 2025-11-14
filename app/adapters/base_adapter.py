"""
Base Adapter Interface for External Systems
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAdapter(ABC):
    """
    Base adapter interface that all system adapters must implement

    This ensures consistency across different ERP/CRM systems
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration

        Args:
            config: Dictionary containing connection details
                   (url, database, username, password, etc.)
        """
        self.config = config
        self.session = None
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to external system

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to external system

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with external system

        Args:
            username: User's username
            password: User's password

        Returns:
            Authentication result with session/token info
        """
        pass

    @abstractmethod
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
        Search and read records from external system

        Args:
            model: Model/entity name
            domain: Search filters
            fields: Fields to return
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sorting specification

        Returns:
            List of records
        """
        pass

    @abstractmethod
    async def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> Any:
        """
        Create a new record in external system

        Args:
            model: Model/entity name
            values: Record data

        Returns:
            Created record ID
        """
        pass

    @abstractmethod
    async def write(
        self,
        model: str,
        record_id: Any,
        values: Dict[str, Any]
    ) -> bool:
        """
        Update an existing record in external system

        Args:
            model: Model/entity name
            record_id: Record ID to update
            values: Updated data

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def unlink(
        self,
        model: str,
        record_ids: List[Any]
    ) -> bool:
        """
        Delete records from external system

        Args:
            model: Model/entity name
            record_ids: List of record IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def call_method(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Call a custom method on external system

        Args:
            model: Model/entity name
            method: Method name to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result
        """
        pass

    @abstractmethod
    async def get_metadata(
        self,
        model: str
    ) -> Dict[str, Any]:
        """
        Get metadata/schema information for a model

        Args:
            model: Model/entity name

        Returns:
            Model metadata (fields, types, relations, etc.)
        """
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Check if connection is still alive

        Returns:
            True if connection is active
        """
        pass

    async def refresh_session(self) -> bool:
        """
        Refresh session/token if needed

        Returns:
            True if refresh successful
        """
        # Default implementation - can be overridden
        return await self.check_connection()
