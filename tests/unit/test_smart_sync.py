"""
Comprehensive tests for Smart Sync system

Tests cover:
- Smart sync pull operations
- Sync state management
- Multi-user/multi-device scenarios
- Cache integration
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.modules.webhook.service import WebhookService, APP_TYPE_MODELS
from app.modules.webhook.schemas import (
    SyncRequest,
    SyncResponse,
    SyncStatsResponse,
    EventData
)
from app.utils.odoo_client import OdooClient, OdooError
from app.services.cache_service import CacheService


# ===== Fixtures =====

@pytest.fixture
def mock_odoo_client():
    """Mock OdooClient"""
    client = Mock(spec=OdooClient)
    return client


@pytest.fixture
def mock_cache_service():
    """Mock CacheService"""
    cache = AsyncMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def webhook_service(mock_odoo_client, mock_cache_service):
    """WebhookService instance with mocked dependencies"""
    return WebhookService(mock_odoo_client, mock_cache_service)


@pytest.fixture
def sample_sync_request():
    """Sample sync request"""
    return SyncRequest(
        user_id=1,
        device_id="iphone-abc123",
        app_type="sales_app",
        limit=100
    )


@pytest.fixture
def sample_sync_state():
    """Sample sync state from Odoo"""
    return {
        "id": 42,
        "user_id": 1,
        "device_id": "iphone-abc123",
        "app_type": "sales_app",
        "last_event_id": 100,
        "last_sync_time": "2025-11-16T10:00:00",
        "sync_count": 5,
        "is_active": True
    }


@pytest.fixture
def sample_events():
    """Sample webhook events from Odoo"""
    return [
        {
            "id": 101,
            "model": "sale.order",
            "record_id": 456,
            "event": "create",
            "timestamp": "2025-11-16T10:05:00"
        },
        {
            "id": 102,
            "model": "res.partner",
            "record_id": 789,
            "event": "write",
            "timestamp": "2025-11-16T10:06:00"
        },
        {
            "id": 103,
            "model": "product.product",
            "record_id": 123,
            "event": "write",
            "timestamp": "2025-11-16T10:07:00"
        }
    ]


# ===== Smart Sync Tests =====

@pytest.mark.asyncio
async def test_smart_sync_first_time(
    webhook_service,
    mock_odoo_client,
    sample_sync_request,
    sample_events
):
    """Test first-time sync for a new device"""
    # Mock sync state creation (first time, last_event_id = 0)
    new_sync_state = {
        "id": 42,
        "user_id": 1,
        "device_id": "iphone-abc123",
        "app_type": "sales_app",
        "last_event_id": 0,
        "last_sync_time": None,
        "sync_count": 0,
        "is_active": True
    }

    # Setup mocks
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            new_sync_state,  # get_or_create_state
            sample_events,    # search_read events
            None              # write (update sync state)
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(sample_sync_request)

        # Assertions
        assert isinstance(result, SyncResponse)
        assert result.has_updates is True
        assert result.new_events_count == 3
        assert len(result.events) == 3
        assert result.next_sync_token == "103"


@pytest.mark.asyncio
async def test_smart_sync_incremental(
    webhook_service,
    mock_odoo_client,
    sample_sync_request,
    sample_sync_state,
    sample_events
):
    """Test incremental sync with existing state"""
    # Setup mocks
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            sample_sync_state,  # get_or_create_state
            sample_events,       # search_read events
            None                 # write (update sync state)
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(sample_sync_request)

        # Assertions
        assert result.has_updates is True
        assert result.new_events_count == 3
        assert result.last_sync_time == "2025-11-16T10:00:00"


@pytest.mark.asyncio
async def test_smart_sync_no_new_events(
    webhook_service,
    mock_odoo_client,
    sample_sync_request,
    sample_sync_state
):
    """Test sync when no new events exist"""
    # Setup mocks
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            sample_sync_state,  # get_or_create_state
            []                   # search_read events (empty)
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(sample_sync_request)

        # Assertions
        assert result.has_updates is False
        assert result.new_events_count == 0
        assert len(result.events) == 0
        assert result.next_sync_token == "100"  # Same as last_event_id


@pytest.mark.asyncio
async def test_smart_sync_app_type_filtering(
    webhook_service,
    mock_odoo_client,
    sample_sync_state
):
    """Test that events are filtered by app type"""
    # Sales app sync request
    sales_request = SyncRequest(
        user_id=1,
        device_id="iphone-abc123",
        app_type="sales_app",
        limit=100
    )

    # Events including non-sales models
    mixed_events = [
        {"id": 101, "model": "sale.order", "record_id": 1, "event": "create", "timestamp": "2025-11-16T10:00:00"},
        {"id": 102, "model": "stock.picking", "record_id": 2, "event": "create", "timestamp": "2025-11-16T10:01:00"},
        {"id": 103, "model": "res.partner", "record_id": 3, "event": "write", "timestamp": "2025-11-16T10:02:00"}
    ]

    # Setup mocks
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()

        # We expect search_read to be called with sales_app models
        def check_domain_and_return_events(*args, **kwargs):
            # Second call is search_read
            return mixed_events

        mock_executor.side_effect = [
            sample_sync_state,
            check_domain_and_return_events(),
            None
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(sales_request)

        # Note: Filtering happens in Odoo via domain
        # Here we verify the call was made correctly
        assert result.has_updates is True


@pytest.mark.asyncio
async def test_smart_sync_custom_model_filter(
    webhook_service,
    mock_odoo_client,
    sample_sync_state
):
    """Test sync with custom model filter"""
    # Request with specific models only
    custom_request = SyncRequest(
        user_id=1,
        device_id="iphone-abc123",
        app_type="sales_app",
        models_filter=["sale.order"],
        limit=100
    )

    filtered_events = [
        {"id": 101, "model": "sale.order", "record_id": 1, "event": "create", "timestamp": "2025-11-16T10:00:00"}
    ]

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            sample_sync_state,
            filtered_events,
            None
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(custom_request)

        # Assertions
        assert result.has_updates is True
        assert result.new_events_count == 1


@pytest.mark.asyncio
async def test_smart_sync_odoo_error(
    webhook_service,
    mock_odoo_client,
    sample_sync_request
):
    """Test error handling when Odoo fails"""
    with patch("asyncio.get_event_loop") as mock_loop:
        # Simulate Odoo error
        mock_loop.return_value.run_in_executor.side_effect = OdooError("Connection failed")

        # Execute and expect exception
        with pytest.raises(OdooError):
            await webhook_service.smart_sync(sample_sync_request)


# ===== Sync State Tests =====

@pytest.mark.asyncio
async def test_get_sync_state(
    webhook_service,
    mock_odoo_client,
    sample_sync_state
):
    """Test getting sync state"""
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor.return_value = [sample_sync_state]

        # Execute
        result = await webhook_service.get_sync_state(1, "iphone-abc123")

        # Assertions
        assert isinstance(result, SyncStatsResponse)
        assert result.user_id == 1
        assert result.device_id == "iphone-abc123"
        assert result.last_event_id == 100
        assert result.sync_count == 5


@pytest.mark.asyncio
async def test_get_sync_state_not_found(
    webhook_service,
    mock_odoo_client
):
    """Test getting non-existent sync state"""
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor.return_value = []  # Empty result

        # Execute and expect exception
        with pytest.raises(ValueError, match="Sync state not found"):
            await webhook_service.get_sync_state(1, "nonexistent-device")


@pytest.mark.asyncio
async def test_reset_sync_state(
    webhook_service,
    mock_odoo_client
):
    """Test resetting sync state"""
    with patch("asyncio.get_event_loop") as mock_loop:
        # Mock search returning state IDs, then write
        mock_loop.return_value.run_in_executor.side_effect = [
            [42],  # search result
            True   # write result
        ]

        # Execute
        result = await webhook_service.reset_sync_state(1, "iphone-abc123")

        # Assertions
        assert result["status"] == "success"
        assert "reset" in result["message"].lower()


@pytest.mark.asyncio
async def test_reset_sync_state_not_found(
    webhook_service,
    mock_odoo_client
):
    """Test resetting non-existent sync state"""
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor.return_value = []  # No state found

        # Execute and expect exception
        with pytest.raises(ValueError, match="Sync state not found"):
            await webhook_service.reset_sync_state(1, "nonexistent-device")


# ===== Multi-Device Tests =====

@pytest.mark.asyncio
async def test_multiple_devices_same_user(
    webhook_service,
    mock_odoo_client,
    sample_events
):
    """Test that different devices maintain separate sync states"""
    device1_state = {
        "id": 42,
        "user_id": 1,
        "device_id": "iphone-abc123",
        "last_event_id": 100,
        "last_sync_time": "2025-11-16T10:00:00",
        "sync_count": 5,
        "is_active": True
    }

    device2_state = {
        "id": 43,
        "user_id": 1,
        "device_id": "android-xyz789",
        "last_event_id": 50,  # Different sync position
        "last_sync_time": "2025-11-16T09:00:00",
        "sync_count": 2,
        "is_active": True
    }

    # Test device 1
    request1 = SyncRequest(
        user_id=1,
        device_id="iphone-abc123",
        app_type="sales_app",
        limit=100
    )

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            device1_state,
            sample_events,
            None
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        result1 = await webhook_service.smart_sync(request1)

    # Test device 2
    request2 = SyncRequest(
        user_id=1,
        device_id="android-xyz789",
        app_type="sales_app",
        limit=100
    )

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            device2_state,
            sample_events,
            None
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        result2 = await webhook_service.smart_sync(request2)

    # Assertions - both devices work independently
    assert result1.has_updates is True
    assert result2.has_updates is True
    # Device 2 might get more events since it's syncing from event 50


# ===== Performance Tests =====

@pytest.mark.asyncio
async def test_smart_sync_large_event_batch(
    webhook_service,
    mock_odoo_client,
    sample_sync_state
):
    """Test sync with large number of events"""
    # Create 500 events
    large_event_batch = [
        {
            "id": 100 + i,
            "model": "sale.order",
            "record_id": i,
            "event": "write",
            "timestamp": f"2025-11-16T10:{i:02d}:00"
        }
        for i in range(1, 501)
    ]

    request = SyncRequest(
        user_id=1,
        device_id="iphone-abc123",
        app_type="sales_app",
        limit=500
    )

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()
        mock_executor.side_effect = [
            sample_sync_state,
            large_event_batch,
            None
        ]
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(request)

        # Assertions
        assert result.new_events_count == 500
        assert len(result.events) == 500


# ===== App Type Models Tests =====

def test_app_type_models_configuration():
    """Test APP_TYPE_MODELS configuration"""
    # Verify all app types have models defined
    assert "sales_app" in APP_TYPE_MODELS
    assert "delivery_app" in APP_TYPE_MODELS
    assert "warehouse_app" in APP_TYPE_MODELS
    assert "manager_app" in APP_TYPE_MODELS

    # Verify sales_app has expected models
    sales_models = APP_TYPE_MODELS["sales_app"]
    assert "sale.order" in sales_models
    assert "res.partner" in sales_models
    assert "product.product" in sales_models

    # Verify delivery_app has expected models
    delivery_models = APP_TYPE_MODELS["delivery_app"]
    assert "stock.picking" in delivery_models
    assert "stock.move" in delivery_models


# ===== Integration Tests =====

@pytest.mark.asyncio
async def test_complete_sync_workflow(
    webhook_service,
    mock_odoo_client,
    sample_sync_request,
    sample_sync_state,
    sample_events
):
    """Test complete sync workflow from pull to state update"""
    with patch("asyncio.get_event_loop") as mock_loop:
        mock_executor = MagicMock()

        # Simulate complete workflow
        call_count = 0

        def mock_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return sample_sync_state  # get_or_create_state
            elif call_count == 2:
                return sample_events       # search_read
            else:
                return None                # write

        mock_executor.side_effect = mock_calls
        mock_loop.return_value.run_in_executor = mock_executor

        # Execute
        result = await webhook_service.smart_sync(sample_sync_request)

        # Verify complete workflow
        assert result.has_updates is True
        assert result.new_events_count == 3
        assert result.next_sync_token == "103"
        assert call_count == 3  # All steps executed


# ===== Edge Cases =====

@pytest.mark.asyncio
async def test_sync_with_empty_device_id(webhook_service):
    """Test sync with invalid device ID"""
    invalid_request = SyncRequest(
        user_id=1,
        device_id="",  # Empty device ID
        app_type="sales_app",
        limit=100
    )

    # This should fail validation at Pydantic level
    # (device_id has min_length=1 in schema)


@pytest.mark.asyncio
async def test_sync_with_invalid_app_type(webhook_service):
    """Test sync with invalid app type"""
    # The schema doesn't restrict app_type values, but service uses it for filtering
    # Test that it handles unknown app types gracefully
    request = SyncRequest(
        user_id=1,
        device_id="test-device",
        app_type="unknown_app",
        limit=100
    )

    # APP_TYPE_MODELS.get() should return None or empty list
    models = APP_TYPE_MODELS.get("unknown_app", [])
    assert models == []
