"""
Integration Test: Webhook → WebSocket Broadcast

Tests the integration between webhook receive endpoint
and WebSocket broadcast for live tracking.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestWebhookWebSocketIntegration:
    """Test webhook to WebSocket broadcast flow"""

    @pytest.fixture
    def mock_manager(self):
        """Create mock WebSocket manager"""
        manager = MagicMock()
        manager.channel_subscriptions = {
            "live_tracking": {1, 2, 3},  # user_ids subscribed
            "model:shuttle.vehicle.position": {1, 2}
        }
        manager.send_personal_message = AsyncMock()
        manager.broadcast_model_update = AsyncMock()
        return manager

    @pytest.fixture
    def webhook_payload(self):
        """Sample webhook payload from Odoo"""
        return {
            "model": "shuttle.vehicle.position",
            "record_id": 123,
            "event": "create",
            "priority": "high",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": 123,
                "vehicle_id": {"id": 5, "name": "Bus 001"},
                "driver_id": {"id": 10, "name": "Ahmed Driver"},
                "latitude": 31.6295,
                "longitude": -7.9811,
                "speed": 45.5,
                "heading": 180.0,
                "timestamp": datetime.utcnow().isoformat()
            },
            "_webhook_metadata": {
                "event_id": 456,
                "rule_name": "Vehicle Position - Create"
            }
        }

    @pytest.mark.asyncio
    async def test_broadcast_webhook_event(self, mock_manager, webhook_payload):
        """Test that webhook events are broadcast via WebSocket"""
        from app.modules.webhook.service import WebhookService
        from app.services.cache_service import CacheService
        
        # Create service with mocks
        cache_service = MagicMock(spec=CacheService)
        odoo_client = MagicMock()
        service = WebhookService(odoo_client, cache_service)
        
        # Patch the manager import
        with patch('app.api.routes.websocket.manager', mock_manager):
            # Call the broadcast method
            await service._broadcast_webhook_event(
                model=webhook_payload["model"],
                record_id=webhook_payload["record_id"],
                event_type=webhook_payload["event"],
                priority=webhook_payload["priority"],
                data=webhook_payload["data"],
                timestamp=webhook_payload["timestamp"]
            )
        
            # Verify messages were sent to live_tracking subscribers
            assert mock_manager.send_personal_message.called
            
            # Verify broadcast_model_update was called
            mock_manager.broadcast_model_update.assert_called_once_with(
                system_id="odoo",
                model="shuttle.vehicle.position",
                record_id=123,
                operation="create",
                data=webhook_payload["data"]
            )

    @pytest.mark.asyncio
    async def test_high_priority_triggers_broadcast(self, mock_manager, webhook_payload):
        """Test that high priority events trigger WebSocket broadcast"""
        from app.modules.webhook.service import WebhookService
        from app.services.cache_service import CacheService
        
        cache_service = MagicMock(spec=CacheService)
        odoo_client = MagicMock()
        service = WebhookService(odoo_client, cache_service)
        
        # Mock _broadcast_webhook_event
        service._broadcast_webhook_event = AsyncMock()
        
        # Process webhook
        result = await service.receive_webhook(webhook_payload)
        
        # Verify success
        assert result["success"] is True
        assert result["model"] == "shuttle.vehicle.position"
        
        # Verify broadcast was triggered for high priority
        service._broadcast_webhook_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_medium_priority_no_broadcast(self, mock_manager):
        """Test that medium priority events don't trigger broadcast"""
        from app.modules.webhook.service import WebhookService
        from app.services.cache_service import CacheService
        
        payload = {
            "model": "shuttle.trip",
            "record_id": 50,
            "event": "write",
            "priority": "medium",  # Not high
            "data": {}
        }
        
        cache_service = MagicMock(spec=CacheService)
        odoo_client = MagicMock()
        service = WebhookService(odoo_client, cache_service)
        
        # Mock _broadcast_webhook_event
        service._broadcast_webhook_event = AsyncMock()
        
        # Process webhook
        result = await service.receive_webhook(payload)
        
        # Verify success but no broadcast
        assert result["success"] is True
        service._broadcast_webhook_event.assert_not_called()


class TestWebSocketSubscriptions:
    """Test WebSocket subscription handling"""

    def test_live_tracking_channel_subscription(self):
        """Test subscribing to live_tracking channel"""
        from app.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        # Simulate subscription
        asyncio.run(manager.subscribe_to_channel("live_tracking", user_id=1))
        
        # Verify subscription
        assert "live_tracking" in manager.channel_subscriptions
        assert 1 in manager.channel_subscriptions["live_tracking"]

    def test_model_channel_subscription(self):
        """Test subscribing to model-specific channel"""
        from app.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        # Simulate subscription to model channel
        channel = "model:shuttle.vehicle.position"
        asyncio.run(manager.subscribe_to_channel(channel, user_id=2))
        
        # Verify subscription
        assert channel in manager.channel_subscriptions
        assert 2 in manager.channel_subscriptions[channel]


# Sample Flutter code for documentation
FLUTTER_EXAMPLE = '''
// Flutter WebSocket Client for Live Tracking
// ==========================================

import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class LiveTrackingService {
  WebSocketChannel? _channel;
  final String baseUrl;
  final int userId;
  
  LiveTrackingService({required this.baseUrl, required this.userId});
  
  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://$baseUrl/api/v1/ws/$userId')
    );
    
    // Subscribe to live tracking
    _channel!.sink.add(jsonEncode({
      'type': 'subscribe_live_tracking'
    }));
    
    // Listen for updates
    _channel!.stream.listen(
      (message) => _handleMessage(jsonDecode(message)),
      onError: (error) => print('WebSocket error: $error'),
      onDone: () => print('WebSocket closed'),
    );
  }
  
  void _handleMessage(Map<String, dynamic> data) {
    switch (data['type']) {
      case 'webhook_event':
        _handleWebhookEvent(data);
        break;
      case 'model_update':
        _handleModelUpdate(data);
        break;
      case 'status':
        print('Status: ${data['message']}');
        break;
    }
  }
  
  void _handleWebhookEvent(Map<String, dynamic> data) {
    final model = data['model'];
    final eventData = data['data'];
    
    if (model == 'shuttle.vehicle.position') {
      // Update driver marker on map
      final lat = eventData['latitude'];
      final lng = eventData['longitude'];
      final vehicleId = eventData['vehicle_id']['id'];
      
      // Call your map update function
      // updateDriverMarker(vehicleId, lat, lng);
    }
  }
  
  void _handleModelUpdate(Map<String, dynamic> data) {
    // Handle specific record updates
    print('Model update: ${data['model']}:${data['record_id']}');
  }
  
  void disconnect() {
    _channel?.sink.close();
  }
}

// Usage:
// final service = LiveTrackingService(
//   baseUrl: 'bridgecore.example.com',
//   userId: 123
// );
// service.connect();
'''

if __name__ == "__main__":
    print("Run with: pytest tests/integration/test_webhook_websocket.py -v")
    print("\nFlutter Example Code:")
    print(FLUTTER_EXAMPLE)
