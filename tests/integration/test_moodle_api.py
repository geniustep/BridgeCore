"""
Integration tests for Moodle API endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from app.main import app


@pytest.fixture
async def async_client():
    """Async HTTP client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_tenant_user():
    """Mock tenant user fixture"""
    user = Mock()
    user.id = "test-user-id"
    user.tenant_id = "test-tenant-id"
    user.is_active = True
    user.tenant = Mock()
    user.tenant.id = "test-tenant-id"
    return user


@pytest.fixture
def mock_moodle_adapter():
    """Mock Moodle adapter fixture"""
    adapter = AsyncMock()
    adapter.connect = AsyncMock(return_value=True)
    adapter.disconnect = AsyncMock(return_value=True)
    return adapter


@pytest.mark.asyncio
class TestMoodleCourseAPI:
    """Test Moodle course API endpoints"""

    async def test_get_courses(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/courses"""
        mock_courses = [
            {"id": 1, "fullname": "Course 1", "shortname": "C1"},
            {"id": 2, "fullname": "Course 2", "shortname": "C2"}
        ]
        mock_moodle_adapter.get_courses = AsyncMock(return_value=mock_courses)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/courses",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["fullname"] == "Course 1"

    async def test_get_course_by_id(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/courses/{id}"""
        mock_course = [{"id": 1, "fullname": "Test Course"}]
        mock_moodle_adapter.get_courses = AsyncMock(return_value=mock_course)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/courses/1",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    async def test_create_course(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test POST /api/v1/moodle/courses"""
        course_data = {
            "fullname": "New Course",
            "shortname": "NEW101",
            "categoryid": 1,
            "summary": "Test course"
        }
        mock_moodle_adapter.create = AsyncMock(return_value=5)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.post(
                    "/api/v1/moodle/courses",
                    json=course_data,
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["id"] == 5

    async def test_update_course(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test PUT /api/v1/moodle/courses/{id}"""
        update_data = {
            "id": 1,
            "fullname": "Updated Course"
        }
        mock_moodle_adapter.write = AsyncMock(return_value=True)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.put(
                    "/api/v1/moodle/courses/1",
                    json=update_data,
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_course(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test DELETE /api/v1/moodle/courses/{id}"""
        mock_moodle_adapter.unlink = AsyncMock(return_value=True)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.delete(
                    "/api/v1/moodle/courses/1",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_get_enrolled_users(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/courses/{id}/users"""
        mock_users = [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"}
        ]
        mock_moodle_adapter.get_enrolled_users = AsyncMock(return_value=mock_users)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/courses/1/users",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_enrol_user(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test POST /api/v1/moodle/courses/{id}/enrol"""
        mock_moodle_adapter.enrol_user = AsyncMock(return_value=True)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.post(
                    "/api/v1/moodle/courses/1/enrol?user_id=10&role_id=5",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
class TestMoodleUserAPI:
    """Test Moodle user API endpoints"""

    async def test_get_users(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/users"""
        mock_users = [
            {"id": 1, "username": "user1", "email": "user1@test.com"}
        ]
        mock_moodle_adapter.get_users = AsyncMock(return_value=mock_users)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/users?username=user1",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_create_user(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test POST /api/v1/moodle/users"""
        user_data = {
            "username": "newuser",
            "password": "SecurePass123!",
            "firstname": "John",
            "lastname": "Doe",
            "email": "john@test.com"
        }
        mock_moodle_adapter.create = AsyncMock(return_value=15)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.post(
                    "/api/v1/moodle/users",
                    json=user_data,
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["id"] == 15


@pytest.mark.asyncio
class TestMoodleSystemAPI:
    """Test Moodle system API endpoints"""

    async def test_get_site_info(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/site-info"""
        mock_info = {
            "sitename": "Test LMS",
            "version": "4.1.5",
            "userid": 2
        }
        mock_moodle_adapter.get_metadata = AsyncMock(return_value=mock_info)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/site-info",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["sitename"] == "Test LMS"

    async def test_check_health(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test GET /api/v1/moodle/health"""
        mock_moodle_adapter.check_connection = AsyncMock(return_value=True)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.get(
                    "/api/v1/moodle/health",
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert "latency_ms" in data

    async def test_call_function(self, async_client, mock_tenant_user, mock_moodle_adapter):
        """Test POST /api/v1/moodle/call"""
        mock_result = [{"id": 1, "name": "Category 1"}]
        mock_moodle_adapter.call_method = AsyncMock(return_value=mock_result)

        with patch('app.core.dependencies.get_current_tenant_user', return_value=mock_tenant_user):
            with patch('app.core.dependencies.get_moodle_adapter', return_value=mock_moodle_adapter):
                response = await async_client.post(
                    "/api/v1/moodle/call",
                    json={
                        "function_name": "core_course_get_categories",
                        "params": {}
                    },
                    headers={"Authorization": "Bearer test_token"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == mock_result
