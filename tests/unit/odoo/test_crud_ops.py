"""
Unit tests for CRUD Operations
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.odoo.crud_ops import CRUDOperations


@pytest.fixture
def crud_service():
    """Create CRUD service instance for testing"""
    return CRUDOperations(
        odoo_url="https://demo.odoo.com",
        database="demo",
        username="admin",
        password="admin"
    )


class TestCRUDOperations:
    """Tests for CRUDOperations class"""

    @pytest.mark.asyncio
    async def test_create_single_record(self, crud_service):
        """Test creating a single record"""
        with patch.object(crud_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = 42

            result = await crud_service.create(
                model='res.partner',
                values={'name': 'Test Partner', 'email': 'test@example.com'}
            )

            assert result == 42
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'res.partner'
            assert call_args[1]['method'] == 'create'

    @pytest.mark.asyncio
    async def test_create_batch_records(self, crud_service):
        """Test creating multiple records in batch"""
        with patch.object(crud_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [42, 43, 44]

            result = await crud_service.create(
                model='res.partner',
                values=[
                    {'name': 'Partner 1'},
                    {'name': 'Partner 2'},
                    {'name': 'Partner 3'}
                ]
            )

            assert result == [42, 43, 44]

    @pytest.mark.asyncio
    async def test_read_records(self, crud_service):
        """Test reading records by ID"""
        expected = [
            {'id': 1, 'name': 'Partner 1', 'email': 'p1@example.com'},
            {'id': 2, 'name': 'Partner 2', 'email': 'p2@example.com'}
        ]

        with patch.object(crud_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected

            result = await crud_service.read(
                model='res.partner',
                ids=[1, 2],
                fields=['name', 'email']
            )

            assert result == expected
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'res.partner'
            assert call_args[1]['method'] == 'read'
            assert call_args[1]['args'] == [[1, 2]]

    @pytest.mark.asyncio
    async def test_read_empty_ids(self, crud_service):
        """Test reading with empty IDs returns empty list"""
        result = await crud_service.read(
            model='res.partner',
            ids=[],
            fields=['name']
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_write_records(self, crud_service):
        """Test updating records"""
        with patch.object(crud_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True

            result = await crud_service.write(
                model='res.partner',
                ids=[1, 2],
                values={'phone': '+1234567890'}
            )

            assert result is True
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'res.partner'
            assert call_args[1]['method'] == 'write'
            assert call_args[1]['args'] == [[1, 2], {'phone': '+1234567890'}]

    @pytest.mark.asyncio
    async def test_write_empty_ids(self, crud_service):
        """Test writing with empty IDs returns False"""
        result = await crud_service.write(
            model='res.partner',
            ids=[],
            values={'name': 'Test'}
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_unlink_records(self, crud_service):
        """Test deleting records"""
        with patch.object(crud_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True

            result = await crud_service.unlink(
                model='res.partner',
                ids=[100, 101, 102]
            )

            assert result is True
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'res.partner'
            assert call_args[1]['method'] == 'unlink'
            assert call_args[1]['args'] == [[100, 101, 102]]

    @pytest.mark.asyncio
    async def test_unlink_empty_ids(self, crud_service):
        """Test deleting with empty IDs returns False"""
        result = await crud_service.unlink(
            model='res.partner',
            ids=[]
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_batch_update(self, crud_service):
        """Test batch update with different values"""
        with patch.object(crud_service, 'write', new_callable=AsyncMock) as mock_write:
            mock_write.return_value = True

            result = await crud_service.batch_update(
                model='res.partner',
                updates=[
                    {'id': 1, 'values': {'name': 'Updated 1'}},
                    {'id': 2, 'values': {'name': 'Updated 2'}},
                    {'id': 3, 'values': {'name': 'Updated 3'}}
                ]
            )

            assert len(result['success']) == 3
            assert result['failed'] == []
            assert mock_write.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_update_missing_id(self, crud_service):
        """Test batch update with missing ID"""
        result = await crud_service.batch_update(
            model='res.partner',
            updates=[
                {'values': {'name': 'No ID'}},  # Missing 'id' key
            ]
        )

        assert result['success'] == []
        assert len(result['failed']) == 1
        assert result['failed'][0]['id'] is None
