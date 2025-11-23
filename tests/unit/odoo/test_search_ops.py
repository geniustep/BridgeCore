"""
Unit tests for Search Operations
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.odoo.search_ops import SearchOperations


@pytest.fixture
def search_service():
    """Create search service instance for testing"""
    return SearchOperations(
        odoo_url="https://demo.odoo.com",
        database="demo",
        username="admin",
        password="admin"
    )


class TestSearchOperations:
    """Tests for SearchOperations class"""

    @pytest.mark.asyncio
    async def test_search_basic(self, search_service):
        """Test basic search operation"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [1, 2, 3, 4, 5]

            result = await search_service.search(
                model='res.partner',
                domain=[['is_company', '=', True]],
                limit=5
            )

            assert result == [1, 2, 3, 4, 5]
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'res.partner'
            assert call_args[1]['method'] == 'search'

    @pytest.mark.asyncio
    async def test_search_empty_domain(self, search_service):
        """Test search with empty domain"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [1, 2, 3]

            result = await search_service.search(
                model='res.partner',
                limit=3
            )

            assert result == [1, 2, 3]
            call_args = mock_execute.call_args
            assert call_args[1]['args'] == [[]]  # Empty domain

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, search_service):
        """Test search with pagination parameters"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = [11, 12, 13, 14, 15]

            result = await search_service.search(
                model='res.partner',
                domain=[],
                limit=5,
                offset=10,
                order='name ASC'
            )

            assert result == [11, 12, 13, 14, 15]
            call_kwargs = mock_execute.call_args[1]['kwargs']
            assert call_kwargs['limit'] == 5
            assert call_kwargs['offset'] == 10
            assert call_kwargs['order'] == 'name ASC'

    @pytest.mark.asyncio
    async def test_search_read_basic(self, search_service):
        """Test basic search_read operation"""
        expected_records = [
            {'id': 1, 'name': 'Partner 1', 'email': 'p1@example.com'},
            {'id': 2, 'name': 'Partner 2', 'email': 'p2@example.com'}
        ]

        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_records

            result = await search_service.search_read(
                model='res.partner',
                domain=[],
                fields=['name', 'email'],
                limit=2
            )

            assert result == expected_records
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_read_with_fields(self, search_service):
        """Test search_read with specific fields"""
        expected_records = [
            {'id': 1, 'name': 'Product A', 'list_price': 100.0}
        ]

        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_records

            result = await search_service.search_read(
                model='product.product',
                domain=[['sale_ok', '=', True]],
                fields=['name', 'list_price']
            )

            assert result == expected_records
            call_kwargs = mock_execute.call_args[1]['kwargs']
            assert call_kwargs['fields'] == ['name', 'list_price']

    @pytest.mark.asyncio
    async def test_search_count(self, search_service):
        """Test search_count operation"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = 42

            result = await search_service.search_count(
                model='res.partner',
                domain=[['is_company', '=', True]]
            )

            assert result == 42

    @pytest.mark.asyncio
    async def test_search_count_empty_result(self, search_service):
        """Test search_count with no matches"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = 0

            result = await search_service.search_count(
                model='res.partner',
                domain=[['id', '=', 999999]]
            )

            assert result == 0

    @pytest.mark.asyncio
    async def test_paginated_search_read(self, search_service):
        """Test paginated_search_read operation"""
        records = [{'id': i, 'name': f'Partner {i}'} for i in range(1, 26)]

        with patch.object(search_service, 'search_count', new_callable=AsyncMock) as mock_count:
            with patch.object(search_service, 'search_read', new_callable=AsyncMock) as mock_search_read:
                mock_count.return_value = 100
                mock_search_read.return_value = records

                result = await search_service.paginated_search_read(
                    model='res.partner',
                    domain=[],
                    fields=['name'],
                    page=1,
                    page_size=25
                )

                assert result['total'] == 100
                assert result['page'] == 1
                assert result['page_size'] == 25
                assert result['pages'] == 4
                assert result['has_next'] is True
                assert result['has_prev'] is False
                assert len(result['records']) == 25

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_none(self, search_service):
        """Test search returns empty list when result is None"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await search_service.search(
                model='res.partner',
                domain=[]
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_search_read_returns_empty_on_none(self, search_service):
        """Test search_read returns empty list when result is None"""
        with patch.object(search_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await search_service.search_read(
                model='res.partner',
                domain=[]
            )

            assert result == []
