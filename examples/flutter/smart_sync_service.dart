/// Smart Sync Service for Flutter Apps
///
/// This service handles synchronization with BridgeCore Smart Sync API.
/// It provides:
/// - Background sync every 30 seconds
/// - Manual sync triggers
/// - Sync state management
/// - Error handling and retry logic
/// - WebSocket support for critical events

import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';

// ===== Models =====

class SyncEvent {
  final int id;
  final String model;
  final int recordId;
  final String event;
  final String timestamp;
  final Map<String, dynamic>? payload;

  SyncEvent({
    required this.id,
    required this.model,
    required this.recordId,
    required this.event,
    required this.timestamp,
    this.payload,
  });

  factory SyncEvent.fromJson(Map<String, dynamic> json) {
    return SyncEvent(
      id: json['id'] as int,
      model: json['model'] as String,
      recordId: json['record_id'] as int,
      event: json['event'] as String,
      timestamp: json['timestamp'] as String,
      payload: json['payload'] as Map<String, dynamic>?,
    );
  }
}

class SyncResponse {
  final bool hasUpdates;
  final int newEventsCount;
  final List<SyncEvent> events;
  final String nextSyncToken;
  final String? lastSyncTime;

  SyncResponse({
    required this.hasUpdates,
    required this.newEventsCount,
    required this.events,
    required this.nextSyncToken,
    this.lastSyncTime,
  });

  factory SyncResponse.fromJson(Map<String, dynamic> json) {
    final eventsJson = json['events'] as List<dynamic>;
    final events = eventsJson
        .map((e) => SyncEvent.fromJson(e as Map<String, dynamic>))
        .toList();

    return SyncResponse(
      hasUpdates: json['has_updates'] as bool,
      newEventsCount: json['new_events_count'] as int,
      events: events,
      nextSyncToken: json['next_sync_token'] as String,
      lastSyncTime: json['last_sync_time'] as String?,
    );
  }
}

enum SyncStatus { idle, syncing, success, error }

// ===== Smart Sync Service =====

class SmartSyncService {
  final Dio _dio;
  final String baseUrl;
  final String appType;
  final Function(List<SyncEvent>) onEventsReceived;
  final Function(String)? onError;
  final Function(SyncStatus)? onStatusChanged;

  // WebSocket support
  WebSocketChannel? _wsChannel;
  final Function(SyncEvent)? onCriticalEvent;

  // Background sync timer
  Timer? _syncTimer;
  SyncStatus _currentStatus = SyncStatus.idle;

  // Preferences for storing device ID and sync state
  late SharedPreferences _prefs;

  SmartSyncService({
    required this.baseUrl,
    required this.appType,
    required this.onEventsReceived,
    this.onError,
    this.onStatusChanged,
    this.onCriticalEvent,
  }) : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
        ));

  /// Initialize the service
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();

    // Configure Dio interceptors
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // Add auth token
        final token = _prefs.getString('access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        debugPrint('Sync error: ${error.message}');
        return handler.next(error);
      },
    ));

    debugPrint('SmartSyncService initialized');
  }

  /// Get or generate device ID
  String getDeviceId() {
    var deviceId = _prefs.getString('device_id');
    if (deviceId == null) {
      // Generate unique device ID
      deviceId = 'flutter-${DateTime.now().millisecondsSinceEpoch}';
      _prefs.setString('device_id', deviceId);
    }
    return deviceId;
  }

  /// Get current user ID
  int getUserId() {
    return _prefs.getInt('user_id') ?? 1;
  }

  /// Start background sync
  void startBackgroundSync({Duration interval = const Duration(seconds: 30)}) {
    _syncTimer?.cancel();

    _syncTimer = Timer.periodic(interval, (_) async {
      await backgroundSync();
    });

    debugPrint('Background sync started (interval: ${interval.inSeconds}s)');
  }

  /// Stop background sync
  void stopBackgroundSync() {
    _syncTimer?.cancel();
    debugPrint('Background sync stopped');
  }

  /// Update sync status
  void _updateStatus(SyncStatus status) {
    _currentStatus = status;
    onStatusChanged?.call(status);
  }

  /// Background sync (automatic)
  Future<void> backgroundSync() async {
    if (_currentStatus == SyncStatus.syncing) {
      debugPrint('Sync already in progress, skipping');
      return;
    }

    try {
      _updateStatus(SyncStatus.syncing);
      debugPrint('Starting background sync...');

      final response = await _dio.post(
        '/api/v2/sync/pull',
        data: {
          'user_id': getUserId(),
          'device_id': getDeviceId(),
          'app_type': appType,
          'limit': 100,
        },
      );

      final syncResponse = SyncResponse.fromJson(response.data);

      if (syncResponse.hasUpdates) {
        debugPrint(
            'Received ${syncResponse.newEventsCount} new events');

        // Apply events locally
        await onEventsReceived(syncResponse.events);

        _updateStatus(SyncStatus.success);
      } else {
        debugPrint('No new updates');
        _updateStatus(SyncStatus.idle);
      }
    } on DioException catch (e) {
      _handleSyncError(e);
      _updateStatus(SyncStatus.error);
    } catch (e) {
      debugPrint('Unexpected sync error: $e');
      onError?.call(e.toString());
      _updateStatus(SyncStatus.error);
    }
  }

  /// Manual sync (user triggered)
  Future<bool> manualSync({
    bool showLoading = true,
    List<String>? modelsFilter,
  }) async {
    try {
      if (showLoading) {
        _updateStatus(SyncStatus.syncing);
      }

      debugPrint('Starting manual sync...');

      final response = await _dio.post(
        '/api/v2/sync/pull',
        data: {
          'user_id': getUserId(),
          'device_id': getDeviceId(),
          'app_type': appType,
          'limit': 500, // Higher limit for manual sync
          if (modelsFilter != null) 'models_filter': modelsFilter,
        },
      );

      final syncResponse = SyncResponse.fromJson(response.data);

      if (syncResponse.hasUpdates) {
        debugPrint(
            'Manual sync: ${syncResponse.newEventsCount} events');
        await onEventsReceived(syncResponse.events);
      }

      _updateStatus(SyncStatus.success);
      return syncResponse.hasUpdates;
    } on DioException catch (e) {
      _handleSyncError(e);
      _updateStatus(SyncStatus.error);
      return false;
    }
  }

  /// Force full sync (reset sync state)
  Future<void> forceFullSync() async {
    try {
      debugPrint('Forcing full sync (resetting state)...');

      // Reset sync state
      await _dio.post(
        '/api/v2/sync/reset',
        queryParameters: {
          'user_id': getUserId(),
          'device_id': getDeviceId(),
        },
      );

      // Trigger full sync
      await manualSync();

      debugPrint('Full sync completed');
    } on DioException catch (e) {
      _handleSyncError(e);
      rethrow;
    }
  }

  /// Get sync state
  Future<Map<String, dynamic>> getSyncState() async {
    try {
      final response = await _dio.get(
        '/api/v2/sync/state',
        queryParameters: {
          'user_id': getUserId(),
          'device_id': getDeviceId(),
        },
      );

      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      _handleSyncError(e);
      rethrow;
    }
  }

  /// Check if updates are available (quick check)
  Future<bool> hasUpdates() async {
    try {
      final response = await _dio.get('/api/v1/webhooks/check-updates');
      final data = response.data as Map<String, dynamic>;
      return data['has_update'] as bool;
    } on DioException catch (e) {
      _handleSyncError(e);
      return false;
    }
  }

  /// Handle sync errors
  void _handleSyncError(DioException error) {
    String message;

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        message = 'Connection timeout. Please check your internet connection.';
        break;

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        if (statusCode == 401) {
          message = 'Session expired. Please login again.';
        } else if (statusCode == 404) {
          message = 'Sync state not found. Resetting...';
          // Auto-reset on 404
          forceFullSync().catchError((_) {});
          return;
        } else if (statusCode == 502 || statusCode == 503) {
          message = 'Server temporarily unavailable. Will retry.';
        } else {
          message = 'Sync failed with status: $statusCode';
        }
        break;

      case DioExceptionType.cancel:
        message = 'Sync cancelled';
        break;

      default:
        message = 'Sync error: ${error.message}';
    }

    debugPrint('Sync error: $message');
    onError?.call(message);
  }

  // ===== WebSocket Support =====

  /// Connect to WebSocket for real-time critical events
  void connectWebSocket() {
    final userId = getUserId();
    final wsUrl = baseUrl.replaceFirst('http', 'ws');

    try {
      _wsChannel = WebSocketChannel.connect(
        Uri.parse('$wsUrl/ws/$userId'),
      );

      _wsChannel!.stream.listen(
        (message) {
          _handleWebSocketMessage(message as String);
        },
        onError: (error) {
          debugPrint('WebSocket error: $error');
          // Retry connection after delay
          Future.delayed(const Duration(seconds: 5), connectWebSocket);
        },
        onDone: () {
          debugPrint('WebSocket connection closed');
          // Retry connection
          Future.delayed(const Duration(seconds: 5), connectWebSocket);
        },
      );

      // Subscribe to critical events
      _wsChannel!.sink.add(jsonEncode({
        'type': 'subscribe',
        'channel': 'critical_events',
      }));

      debugPrint('WebSocket connected');
    } catch (e) {
      debugPrint('WebSocket connection failed: $e');
    }
  }

  /// Handle WebSocket messages
  void _handleWebSocketMessage(String message) {
    try {
      final data = jsonDecode(message) as Map<String, dynamic>;
      final type = data['type'] as String;

      if (type == 'critical_event' || type == 'urgent_update') {
        // Critical event received
        final eventData = data['event'] as Map<String, dynamic>;
        final syncEvent = SyncEvent.fromJson(eventData);

        debugPrint(
            'Critical event received: ${syncEvent.model}:${syncEvent.recordId}');

        // Notify callback
        onCriticalEvent?.call(syncEvent);

        // Trigger background sync to get full details
        backgroundSync();
      } else if (type == 'sync_event') {
        // Sync event notification - trigger pull
        debugPrint('Sync event notification received');
        backgroundSync();
      } else if (type == 'pong') {
        // Pong response
      }
    } catch (e) {
      debugPrint('Error handling WebSocket message: $e');
    }
  }

  /// Disconnect WebSocket
  void disconnectWebSocket() {
    _wsChannel?.sink.close();
    _wsChannel = null;
    debugPrint('WebSocket disconnected');
  }

  /// Send ping to keep connection alive
  void sendPing() {
    _wsChannel?.sink.add(jsonEncode({
      'type': 'ping',
      'timestamp': DateTime.now().toIso8601String(),
    }));
  }

  // ===== Cleanup =====

  /// Dispose resources
  void dispose() {
    stopBackgroundSync();
    disconnectWebSocket();
    _dio.close();
    debugPrint('SmartSyncService disposed');
  }
}

// ===== Usage Example =====

void main() async {
  // Example: Initialize and use SmartSyncService

  final syncService = SmartSyncService(
    baseUrl: 'https://bridgecore.geniura.com',
    appType: 'sales_app',
    onEventsReceived: (events) async {
      print('Received ${events.length} events');

      // Apply events to local database
      for (final event in events) {
        await applyEventToDatabase(event);
      }
    },
    onError: (error) {
      print('Sync error: $error');
      // Show error to user
    },
    onStatusChanged: (status) {
      print('Sync status: $status');
      // Update UI
    },
    onCriticalEvent: (event) {
      print('CRITICAL: ${event.model}:${event.recordId}');
      // Show urgent notification
    },
  );

  // Initialize
  await syncService.initialize();

  // Start background sync
  syncService.startBackgroundSync();

  // Connect WebSocket for real-time events
  syncService.connectWebSocket();

  // Manual sync when user pulls to refresh
  final hasUpdates = await syncService.manualSync();
  if (hasUpdates) {
    print('Data refreshed!');
  }

  // Force full sync if needed
  // await syncService.forceFullSync();

  // Check sync state
  final state = await syncService.getSyncState();
  print('Sync state: $state');

  // Cleanup on app exit
  // syncService.dispose();
}

/// Helper: Apply event to local database
Future<void> applyEventToDatabase(SyncEvent event) async {
  // Implement based on your local database (sqflite, hive, etc.)
  print('Applying ${event.event} on ${event.model}:${event.recordId}');

  switch (event.event) {
    case 'create':
      // Insert new record
      break;
    case 'write':
      // Update existing record
      break;
    case 'unlink':
      // Delete record
      break;
  }
}
