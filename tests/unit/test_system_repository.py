"""
Unit tests for System Repositories
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from app.repositories.system_repository import ExternalSystemRepository, TenantSystemRepository
from app.models.external_system import SystemType, SystemStatus


@pytest.fixture
def mock_session():
    """Mock database session"""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_external_system():
    """Sample external system"""
    system = Mock()
    system.id = uuid4()
    system.system_type = SystemType.MOODLE
    system.name = "Moodle LMS"
    system.status = SystemStatus.ACTIVE
    system.is_enabled = True
    return system


@pytest.fixture
def sample_tenant_system():
    """Sample tenant system connection"""
    conn = Mock()
    conn.id = uuid4()
    conn.tenant_id = uuid4()
    conn.system_id = uuid4()
    conn.is_active = True
    conn.is_primary = False
    conn.external_system = Mock()
    conn.external_system.system_type = SystemType.MOODLE
    return conn


@pytest.mark.asyncio
class TestExternalSystemRepository:
    """Test ExternalSystemRepository"""

    async def test_get_by_type(self, mock_session, sample_external_system):
        """Test get_by_type method"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_external_system
        mock_session.execute.return_value = mock_result

        repo = ExternalSystemRepository(mock_session)
        result = await repo.get_by_type(SystemType.MOODLE)

        assert result == sample_external_system
        assert result.system_type == SystemType.MOODLE

    async def test_get_enabled_systems(self, mock_session, sample_external_system):
        """Test get_enabled_systems method"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_external_system]
        mock_session.execute.return_value = mock_result

        repo = ExternalSystemRepository(mock_session)
        result = await repo.get_enabled_systems()

        assert len(result) == 1
        assert result[0].is_enabled is True
        assert result[0].status == SystemStatus.ACTIVE

    async def test_get_all_systems(self, mock_session, sample_external_system):
        """Test get_all_systems method"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_external_system]
        mock_session.execute.return_value = mock_result

        repo = ExternalSystemRepository(mock_session)
        result = await repo.get_all_systems()

        assert len(result) == 1
        assert result[0] == sample_external_system


@pytest.mark.asyncio
class TestTenantSystemRepository:
    """Test TenantSystemRepository"""

    async def test_get_by_tenant_active_only(self, mock_session, sample_tenant_system):
        """Test get_by_tenant with active_only=True"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_tenant_system]
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.get_by_tenant(sample_tenant_system.tenant_id, active_only=True)

        assert len(result) == 1
        assert result[0].is_active is True

    async def test_get_by_tenant_all(self, mock_session, sample_tenant_system):
        """Test get_by_tenant with active_only=False"""
        inactive_conn = Mock()
        inactive_conn.id = uuid4()
        inactive_conn.tenant_id = sample_tenant_system.tenant_id
        inactive_conn.is_active = False

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_tenant_system, inactive_conn]
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.get_by_tenant(sample_tenant_system.tenant_id, active_only=False)

        assert len(result) == 2

    async def test_get_by_tenant_and_type(self, mock_session, sample_tenant_system):
        """Test get_by_tenant_and_type method"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_tenant_system
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.get_by_tenant_and_type(
            sample_tenant_system.tenant_id,
            SystemType.MOODLE
        )

        assert result == sample_tenant_system
        assert result.external_system.system_type == SystemType.MOODLE

    async def test_get_primary_system(self, mock_session, sample_tenant_system):
        """Test get_primary_system method"""
        sample_tenant_system.is_primary = True

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_tenant_system
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.get_primary_system(sample_tenant_system.tenant_id)

        assert result == sample_tenant_system
        assert result.is_primary is True

    async def test_set_primary(self, mock_session, sample_tenant_system):
        """Test set_primary method"""
        # Mock get all connections
        other_conn = Mock()
        other_conn.is_primary = True

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [other_conn, sample_tenant_system]

        # Mock get specific connection
        mock_result2 = Mock()
        mock_result2.scalar_one_or_none.return_value = sample_tenant_system

        mock_session.execute.side_effect = [mock_result, mock_result2]

        repo = TenantSystemRepository(mock_session)
        result = await repo.set_primary(
            sample_tenant_system.tenant_id,
            sample_tenant_system.system_id
        )

        assert result is True
        assert other_conn.is_primary is False
        assert sample_tenant_system.is_primary is True

    async def test_check_exists_true(self, mock_session):
        """Test check_exists returns True"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = Mock()
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.check_exists(uuid4(), uuid4())

        assert result is True

    async def test_check_exists_false(self, mock_session):
        """Test check_exists returns False"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.check_exists(uuid4(), uuid4())

        assert result is False

    async def test_update_connection_status_success(self, mock_session, sample_tenant_system):
        """Test update_connection_status with success"""
        mock_session.commit = AsyncMock()

        with patch.object(TenantSystemRepository, 'get_by_id', return_value=sample_tenant_system):
            repo = TenantSystemRepository(mock_session)
            await repo.update_connection_status(
                sample_tenant_system.id,
                success=True,
                error_message=None
            )

        assert sample_tenant_system.last_successful_connection is not None
        assert sample_tenant_system.connection_error is None

    async def test_update_connection_status_failure(self, mock_session, sample_tenant_system):
        """Test update_connection_status with failure"""
        mock_session.commit = AsyncMock()
        error_msg = "Connection timeout"

        with patch.object(TenantSystemRepository, 'get_by_id', return_value=sample_tenant_system):
            repo = TenantSystemRepository(mock_session)
            await repo.update_connection_status(
                sample_tenant_system.id,
                success=False,
                error_message=error_msg
            )

        assert sample_tenant_system.connection_error == error_msg

    async def test_get_by_system_type(self, mock_session, sample_tenant_system):
        """Test get_by_system_type method"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_tenant_system]
        mock_session.execute.return_value = mock_result

        repo = TenantSystemRepository(mock_session)
        result = await repo.get_by_system_type(SystemType.MOODLE, active_only=True)

        assert len(result) == 1
        assert result[0].external_system.system_type == SystemType.MOODLE
