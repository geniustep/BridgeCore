"""
Unit tests for Advanced Operations
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.odoo.advanced_ops import AdvancedOperations


@pytest.fixture
def advanced_service():
    """Create advanced service instance for testing"""
    return AdvancedOperations(
        odoo_url="https://demo.odoo.com",
        database="demo",
        username="admin",
        password="admin"
    )


class TestAdvancedOperations:
    """Tests for AdvancedOperations class"""

    @pytest.mark.asyncio
    async def test_onchange_basic(self, advanced_service):
        """Test basic onchange operation"""
        expected_result = {
            'value': {
                'price_unit': 150.0,
                'discount': 10.0,
                'name': 'Product Description'
            },
            'warning': None,
            'domain': None
        }

        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_result

            result = await advanced_service.onchange(
                model='sale.order.line',
                ids=[],
                values={'order_id': 1, 'product_id': 50, 'product_uom_qty': 5.0},
                field_name='product_id',
                field_onchange={'product_id': '1', 'price_unit': '1', 'discount': '1'}
            )

            assert result['value']['price_unit'] == 150.0
            assert result['value']['discount'] == 10.0

    @pytest.mark.asyncio
    async def test_onchange_with_warning(self, advanced_service):
        """Test onchange that returns a warning"""
        expected_result = {
            'value': {},
            'warning': {
                'title': 'Warning',
                'message': 'Product out of stock'
            },
            'domain': None
        }

        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_result

            result = await advanced_service.onchange(
                model='sale.order.line',
                ids=[],
                values={'product_id': 999},
                field_name='product_id',
                field_onchange={'product_id': '1'}
            )

            assert result['warning'] is not None
            assert result['warning']['title'] == 'Warning'

    @pytest.mark.asyncio
    async def test_read_group_basic(self, advanced_service):
        """Test basic read_group operation"""
        expected_groups = [
            {
                'partner_id': [1, 'Customer A'],
                'amount_total': 5000.0,
                '__domain': [['partner_id', '=', 1]],
                '__count': 10
            },
            {
                'partner_id': [2, 'Customer B'],
                'amount_total': 3000.0,
                '__domain': [['partner_id', '=', 2]],
                '__count': 5
            }
        ]

        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_groups

            result = await advanced_service.read_group(
                model='sale.order',
                domain=[['state', '=', 'sale']],
                fields=['amount_total:sum'],
                groupby=['partner_id'],
                orderby='amount_total desc'
            )

            assert len(result) == 2
            assert result[0]['partner_id'][1] == 'Customer A'
            assert result[0]['amount_total'] == 5000.0

    @pytest.mark.asyncio
    async def test_read_group_empty(self, advanced_service):
        """Test read_group with no results"""
        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = []

            result = await advanced_service.read_group(
                model='sale.order',
                domain=[['state', '=', 'nonexistent']],
                fields=['amount_total:sum'],
                groupby=['partner_id']
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_default_get(self, advanced_service):
        """Test default_get operation"""
        expected_defaults = {
            'date_order': '2024-11-23',
            'pricelist_id': 1,
            'warehouse_id': 1
        }

        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = expected_defaults

            result = await advanced_service.default_get(
                model='sale.order',
                fields=['date_order', 'pricelist_id', 'warehouse_id']
            )

            assert result['date_order'] == '2024-11-23'
            assert result['pricelist_id'] == 1

    @pytest.mark.asyncio
    async def test_default_get_empty(self, advanced_service):
        """Test default_get with no defaults"""
        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {}

            result = await advanced_service.default_get(
                model='res.partner',
                fields=['custom_field']
            )

            assert result == {}

    @pytest.mark.asyncio
    async def test_copy(self, advanced_service):
        """Test copy operation"""
        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = 101

            result = await advanced_service.copy(
                model='sale.order',
                record_id=100,
                default={'date_order': '2024-12-01'}
            )

            assert result == 101
            call_args = mock_execute.call_args
            assert call_args[1]['model'] == 'sale.order'
            assert call_args[1]['method'] == 'copy'
            assert call_args[1]['args'] == [100, {'date_order': '2024-12-01'}]

    @pytest.mark.asyncio
    async def test_copy_without_default(self, advanced_service):
        """Test copy without override values"""
        with patch.object(advanced_service, '_execute_kw', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = 102

            result = await advanced_service.copy(
                model='product.template',
                record_id=50
            )

            assert result == 102
            call_args = mock_execute.call_args
            assert call_args[1]['args'] == [50, {}]  # Empty default dict
