"""
Unit tests for MoodleAdapter
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.adapters.moodle_adapter import MoodleAdapter


@pytest.fixture
def moodle_config():
    """Moodle configuration fixture"""
    return {
        "url": "https://lms.example.com",
        "token": "test_token_12345",
        "service": "moodle_mobile_app"
    }


@pytest.fixture
def moodle_adapter(moodle_config):
    """MoodleAdapter instance fixture"""
    return MoodleAdapter(moodle_config)


@pytest.mark.asyncio
class TestMoodleAdapter:
    """Test suite for MoodleAdapter"""

    async def test_initialization(self, moodle_adapter, moodle_config):
        """Test adapter initialization"""
        assert moodle_adapter.url == moodle_config["url"]
        assert moodle_adapter.token == moodle_config["token"]
        assert moodle_adapter.service == moodle_config["service"]
        assert moodle_adapter.format == "json"
        assert moodle_adapter.api_endpoint == f"{moodle_config['url']}/webservice/rest/server.php"

    async def test_connect_success(self, moodle_adapter):
        """Test successful connection"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sitename": "Test LMS",
            "username": "test_user"
        }

        with patch.object(moodle_adapter.client, 'post', return_value=mock_response) as mock_post:
            result = await moodle_adapter.connect()
            assert result is True
            assert moodle_adapter.is_connected is True

    async def test_connect_failure(self, moodle_adapter):
        """Test connection failure"""
        with patch.object(moodle_adapter.client, 'post', side_effect=Exception("Connection error")):
            result = await moodle_adapter.connect()
            assert result is False

    async def test_disconnect(self, moodle_adapter):
        """Test disconnection"""
        with patch.object(moodle_adapter.client, 'aclose', return_value=None):
            result = await moodle_adapter.disconnect()
            assert result is True
            assert moodle_adapter.is_connected is False

    async def test_authenticate_success(self, moodle_adapter):
        """Test successful authentication"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "new_token_67890",
            "privatetoken": "private_token"
        }

        with patch.object(moodle_adapter.client, 'post', return_value=mock_response) as mock_post:
            result = await moodle_adapter.authenticate("test_user", "test_password")
            assert result["success"] is True
            assert result["token"] == "new_token_67890"
            assert moodle_adapter.token == "new_token_67890"

    async def test_authenticate_failure(self, moodle_adapter):
        """Test authentication failure"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": "Invalid credentials"
        }

        with patch.object(moodle_adapter.client, 'post', return_value=mock_response):
            result = await moodle_adapter.authenticate("bad_user", "bad_password")
            assert result["success"] is False
            assert "error" in result

    async def test_flatten_params_simple(self, moodle_adapter):
        """Test parameter flattening with simple values"""
        params = {"key1": "value1", "key2": "value2"}
        result = moodle_adapter._flatten_params(params)
        assert result == {"key1": "value1", "key2": "value2"}

    async def test_flatten_params_nested(self, moodle_adapter):
        """Test parameter flattening with nested values"""
        params = {
            "criteria": [
                {"key": "id", "value": 1},
                {"key": "name", "value": "test"}
            ]
        }
        result = moodle_adapter._flatten_params(params)
        assert result["criteria[0][key]"] == "id"
        assert result["criteria[0][value]"] == 1
        assert result["criteria[1][key]"] == "name"
        assert result["criteria[1][value]"] == "test"

    async def test_call_function_success(self, moodle_adapter):
        """Test successful function call"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sitename": "Test LMS"}

        with patch.object(moodle_adapter.client, 'post', return_value=mock_response):
            result = await moodle_adapter._call_function("core_webservice_get_site_info")
            assert result == {"sitename": "Test LMS"}

    async def test_call_function_error(self, moodle_adapter):
        """Test function call with error response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exception": "moodle_exception",
            "message": "Access denied"
        }

        with patch.object(moodle_adapter.client, 'post', return_value=mock_response):
            with pytest.raises(Exception) as exc_info:
                await moodle_adapter._call_function("some_function")
            assert "Access denied" in str(exc_info.value)

    async def test_search_read_courses(self, moodle_adapter):
        """Test search_read for courses"""
        mock_courses = [
            {"id": 1, "fullname": "Course 1"},
            {"id": 2, "fullname": "Course 2"}
        ]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_courses):
            result = await moodle_adapter.search_read("courses")
            assert len(result) == 2
            assert result[0]["id"] == 1

    async def test_search_read_with_limit(self, moodle_adapter):
        """Test search_read with limit"""
        mock_data = [{"id": i} for i in range(10)]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_data):
            result = await moodle_adapter.search_read("courses", limit=5)
            assert len(result) == 5

    async def test_create_course(self, moodle_adapter):
        """Test course creation"""
        course_data = {
            "fullname": "Test Course",
            "shortname": "TEST101",
            "categoryid": 1
        }
        mock_response = [{"id": 5}]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_response):
            result = await moodle_adapter.create("courses", course_data)
            assert result == 5

    async def test_write_course(self, moodle_adapter):
        """Test course update"""
        update_data = {"fullname": "Updated Course"}

        with patch.object(moodle_adapter, '_call_function', return_value=True):
            result = await moodle_adapter.write("courses", 5, update_data)
            assert result is True

    async def test_unlink_course(self, moodle_adapter):
        """Test course deletion"""
        with patch.object(moodle_adapter, '_call_function', return_value=True):
            result = await moodle_adapter.unlink("courses", [1, 2, 3])
            assert result is True

    async def test_get_courses(self, moodle_adapter):
        """Test get_courses method"""
        mock_courses = [{"id": 1}, {"id": 2}]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_courses):
            result = await moodle_adapter.get_courses([1, 2])
            assert len(result) == 2

    async def test_get_users(self, moodle_adapter):
        """Test get_users method"""
        mock_users = [{"id": 1, "username": "user1"}]
        criteria = [{"key": "username", "value": "user1"}]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_users):
            result = await moodle_adapter.get_users(criteria)
            assert len(result) == 1
            assert result[0]["username"] == "user1"

    async def test_get_enrolled_users(self, moodle_adapter):
        """Test get_enrolled_users method"""
        mock_users = [{"id": 1}, {"id": 2}]

        with patch.object(moodle_adapter, '_call_function', return_value=mock_users):
            result = await moodle_adapter.get_enrolled_users(course_id=5)
            assert len(result) == 2

    async def test_enrol_user(self, moodle_adapter):
        """Test enrol_user method"""
        with patch.object(moodle_adapter, '_call_function', return_value=None):
            result = await moodle_adapter.enrol_user(
                course_id=5,
                user_id=10,
                role_id=5
            )
            assert result is True

    async def test_check_connection_success(self, moodle_adapter):
        """Test connection check success"""
        with patch.object(moodle_adapter, '_call_function', return_value={"sitename": "Test"}):
            result = await moodle_adapter.check_connection()
            assert result is True

    async def test_check_connection_failure(self, moodle_adapter):
        """Test connection check failure"""
        with patch.object(moodle_adapter, '_call_function', side_effect=Exception("Error")):
            result = await moodle_adapter.check_connection()
            assert result is False

    async def test_get_metadata(self, moodle_adapter):
        """Test get_metadata method"""
        mock_info = {"sitename": "Test LMS", "version": "4.1"}

        with patch.object(moodle_adapter, '_call_function', return_value=mock_info):
            result = await moodle_adapter.get_metadata("site")
            assert result["sitename"] == "Test LMS"

    async def test_unsupported_model(self, moodle_adapter):
        """Test unsupported model raises error"""
        with pytest.raises(ValueError) as exc_info:
            await moodle_adapter.search_read("unsupported_model")
        assert "Unsupported Moodle model" in str(exc_info.value)
