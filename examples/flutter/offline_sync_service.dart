/// BridgeCore Offline Sync Service - Flutter Implementation
///
/// Complete offline-first synchronization service for Flutter applications
///
/// Features:
/// - Push local changes to server
/// - Pull server changes
/// - Automatic conflict resolution
/// - Background sync
/// - Offline queue management
/// - Progress tracking
/// - Error handling with retry

import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite/sqflite.dart';

/// Sync action types
enum SyncAction { create, update, delete }

/// Conflict resolution strategies
enum ConflictStrategy {
  serverWins,
  clientWins,
  manual,
  merge,
  newestWins
}

/// Sync status
enum SyncStatus { success, failed, conflict, pending }

/// Local change model
class LocalChange {
  final String localId;
  final SyncAction action;
  final String model;
  final int? recordId;
  final Map<String, dynamic> data;
  final DateTime localTimestamp;
  final int version;
  final int priority;
  final List<String>? dependencies;

  LocalChange({
    required this.localId,
    required this.action,
    required this.model,
    this.recordId,
    required this.data,
    required this.localTimestamp,
    this.version = 1,
    this.priority = 0,
    this.dependencies,
  });

  Map<String, dynamic> toJson() {
    return {
      'local_id': localId,
      'action': action.name,
      'model': model,
      'record_id': recordId,
      'data': data,
      'local_timestamp': localTimestamp.toIso8601String(),
      'version': version,
      'priority': priority,
      'dependencies': dependencies,
    };
  }

  factory LocalChange.fromJson(Map<String, dynamic> json) {
    return LocalChange(
      localId: json['local_id'],
      action: SyncAction.values.firstWhere(
        (e) => e.name == json['action'],
      ),
      model: json['model'],
      recordId: json['record_id'],
      data: json['data'],
      localTimestamp: DateTime.parse(json['local_timestamp']),
      version: json['version'] ?? 1,
      priority: json['priority'] ?? 0,
      dependencies: json['dependencies'] != null
          ? List<String>.from(json['dependencies'])
          : null,
    );
  }
}

/// Server change model
class ServerChange {
  final int eventId;
  final String model;
  final int recordId;
  final String action;
  final DateTime timestamp;
  final Map<String, dynamic>? data;
  final List<String>? changedFields;

  ServerChange({
    required this.eventId,
    required this.model,
    required this.recordId,
    required this.action,
    required this.timestamp,
    this.data,
    this.changedFields,
  });

  factory ServerChange.fromJson(Map<String, dynamic> json) {
    return ServerChange(
      eventId: json['event_id'],
      model: json['model'],
      recordId: json['record_id'],
      action: json['action'],
      timestamp: DateTime.parse(json['timestamp']),
      data: json['data'],
      changedFields: json['changed_fields'] != null
          ? List<String>.from(json['changed_fields'])
          : null,
    );
  }
}

/// Push result
class PushResult {
  final String localId;
  final SyncStatus status;
  final int? serverId;
  final String? error;
  final Map<String, dynamic>? conflictInfo;

  PushResult({
    required this.localId,
    required this.status,
    this.serverId,
    this.error,
    this.conflictInfo,
  });

  factory PushResult.fromJson(Map<String, dynamic> json) {
    return PushResult(
      localId: json['local_id'],
      status: SyncStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => SyncStatus.pending,
      ),
      serverId: json['server_id'],
      error: json['error'],
      conflictInfo: json['conflict_info'],
    );
  }
}

/// Push response
class PushResponse {
  final bool success;
  final int total;
  final int succeeded;
  final int failed;
  final int conflicts;
  final List<PushResult> results;
  final Map<String, int> idMapping;

  PushResponse({
    required this.success,
    required this.total,
    required this.succeeded,
    required this.failed,
    required this.conflicts,
    required this.results,
    required this.idMapping,
  });

  factory PushResponse.fromJson(Map<String, dynamic> json) {
    return PushResponse(
      success: json['success'],
      total: json['total'],
      succeeded: json['succeeded'],
      failed: json['failed'],
      conflicts: json['conflicts'],
      results: (json['results'] as List)
          .map((r) => PushResult.fromJson(r))
          .toList(),
      idMapping: Map<String, int>.from(json['id_mapping'] ?? {}),
    );
  }
}

/// Pull response
class PullResponse {
  final bool success;
  final bool hasUpdates;
  final int newEventsCount;
  final List<ServerChange> events;
  final int lastEventId;

  PullResponse({
    required this.success,
    required this.hasUpdates,
    required this.newEventsCount,
    required this.events,
    required this.lastEventId,
  });

  factory PullResponse.fromJson(Map<String, dynamic> json) {
    return PullResponse(
      success: json['success'],
      hasUpdates: json['has_updates'],
      newEventsCount: json['new_events_count'],
      events: (json['events'] as List)
          .map((e) => ServerChange.fromJson(e))
          .toList(),
      lastEventId: json['last_event_id'],
    );
  }
}

/// Offline Sync Service
class OfflineSyncService {
  final String baseUrl;
  final String deviceId;
  final String appType;
  final Database database;
  final Dio _dio;
  final SharedPreferences _prefs;

  // Progress tracking
  final _syncProgressController = StreamController<double>.broadcast();
  Stream<double> get syncProgress => _syncProgressController.stream;

  // Sync status
  final _syncStatusController = StreamController<String>.broadcast();
  Stream<String> get syncStatus => _syncStatusController.stream;

  // Background sync timer
  Timer? _backgroundSyncTimer;
  bool _isSyncing = false;

  OfflineSyncService({
    required this.baseUrl,
    required this.deviceId,
    required this.appType,
    required this.database,
    required Dio dio,
    required SharedPreferences prefs,
  })  : _dio = dio,
        _prefs = prefs {
    // Configure dio interceptors
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Add auth token
          final token = _prefs.getString('auth_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          options.headers['Content-Type'] = 'application/json';
          return handler.next(options);
        },
        onError: (error, handler) {
          print('Sync API Error: ${error.message}');
          return handler.next(error);
        },
      ),
    );
  }

  /// Initialize service
  Future<void> initialize() async {
    await _createTables();
    print('Offline sync service initialized');
  }

  /// Create database tables
  Future<void> _createTables() async {
    await database.execute('''
      CREATE TABLE IF NOT EXISTS pending_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        local_id TEXT UNIQUE NOT NULL,
        action TEXT NOT NULL,
        model TEXT NOT NULL,
        record_id INTEGER,
        data TEXT NOT NULL,
        local_timestamp TEXT NOT NULL,
        version INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 0,
        sync_status TEXT DEFAULT 'pending',
        error TEXT,
        created_at TEXT NOT NULL
      )
    ''');

    await database.execute('''
      CREATE INDEX IF NOT EXISTS idx_sync_status
      ON pending_changes(sync_status)
    ''');

    await database.execute('''
      CREATE INDEX IF NOT EXISTS idx_local_timestamp
      ON pending_changes(local_timestamp)
    ''');
  }

  // ==================== SAVE OFFLINE CHANGES ====================

  /// Save a change to local database
  Future<String> saveOfflineChange({
    required SyncAction action,
    required String model,
    int? recordId,
    required Map<String, dynamic> data,
    int priority = 0,
  }) async {
    final localId = const Uuid().v4();
    final now = DateTime.now().toIso8601String();

    await database.insert('pending_changes', {
      'local_id': localId,
      'action': action.name,
      'model': model,
      'record_id': recordId,
      'data': jsonEncode(data),
      'local_timestamp': now,
      'priority': priority,
      'sync_status': 'pending',
      'created_at': now,
    });

    print('Saved offline change: $localId ($action $model)');

    // Try to sync immediately if online
    _trySyncIfOnline();

    return localId;
  }

  /// Get pending changes count
  Future<int> getPendingChangesCount() async {
    final result = await database.rawQuery(
      'SELECT COUNT(*) as count FROM pending_changes WHERE sync_status = ?',
      ['pending'],
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  /// Get all pending changes
  Future<List<LocalChange>> _getPendingChanges() async {
    final results = await database.query(
      'pending_changes',
      where: 'sync_status = ?',
      whereArgs: ['pending'],
      orderBy: 'priority DESC, created_at ASC',
    );

    return results.map((row) {
      return LocalChange(
        localId: row['local_id'] as String,
        action: SyncAction.values.firstWhere(
          (e) => e.name == row['action'],
        ),
        model: row['model'] as String,
        recordId: row['record_id'] as int?,
        data: jsonDecode(row['data'] as String),
        localTimestamp: DateTime.parse(row['local_timestamp'] as String),
        version: row['version'] as int? ?? 1,
        priority: row['priority'] as int? ?? 0,
      );
    }).toList();
  }

  // ==================== PUSH (Upload) ====================

  /// Push local changes to server
  Future<PushResponse> push({
    ConflictStrategy conflictStrategy = ConflictStrategy.serverWins,
    bool stopOnError = false,
  }) async {
    if (_isSyncing) {
      print('Sync already in progress');
      throw Exception('Sync already in progress');
    }

    _isSyncing = true;
    _syncStatusController.add('Pushing local changes...');

    try {
      // Get pending changes
      final changes = await _getPendingChanges();

      if (changes.isEmpty) {
        print('No pending changes to push');
        _syncStatusController.add('No changes to sync');
        return PushResponse(
          success: true,
          total: 0,
          succeeded: 0,
          failed: 0,
          conflicts: 0,
          results: [],
          idMapping: {},
        );
      }

      print('Pushing ${changes.length} changes...');
      _syncProgressController.add(0.0);

      // Call API
      final response = await _dio.post(
        '$baseUrl/api/v1/offline-sync/push',
        data: {
          'device_id': deviceId,
          'changes': changes.map((c) => c.toJson()).toList(),
          'conflict_strategy': conflictStrategy.name,
          'stop_on_error': stopOnError,
        },
      );

      final result = PushResponse.fromJson(response.data);

      // Update local database
      await _updateLocalDatabase(result);

      _syncProgressController.add(1.0);
      _syncStatusController.add(
        'Pushed ${result.succeeded}/${result.total} changes',
      );

      print('Push completed: ${result.succeeded}/${result.total} succeeded');

      return result;
    } catch (e) {
      print('Push failed: $e');
      _syncStatusController.add('Push failed: $e');
      rethrow;
    } finally {
      _isSyncing = false;
    }
  }

  /// Update local database after push
  Future<void> _updateLocalDatabase(PushResponse response) async {
    final batch = database.batch();

    for (final result in response.results) {
      if (result.status == SyncStatus.success) {
        // Mark as synced
        batch.update(
          'pending_changes',
          {
            'sync_status': 'synced',
            'record_id': result.serverId,
          },
          where: 'local_id = ?',
          whereArgs: [result.localId],
        );

        // Update ID in actual data tables if needed
        if (result.serverId != null) {
          await _updateLocalIdToServerId(
            result.localId,
            result.serverId!,
          );
        }
      } else if (result.status == SyncStatus.failed) {
        // Mark as failed with error
        batch.update(
          'pending_changes',
          {
            'sync_status': 'failed',
            'error': result.error,
          },
          where: 'local_id = ?',
          whereArgs: [result.localId],
        );
      } else if (result.status == SyncStatus.conflict) {
        // Mark as conflict
        batch.update(
          'pending_changes',
          {
            'sync_status': 'conflict',
            'error': jsonEncode(result.conflictInfo),
          },
          where: 'local_id = ?',
          whereArgs: [result.localId],
        );
      }
    }

    await batch.commit(noResult: true);

    // Clean up old synced changes (keep for 7 days)
    await _cleanupOldChanges();
  }

  /// Update local ID to server ID in data tables
  Future<void> _updateLocalIdToServerId(String localId, int serverId) async {
    // TODO: Implement this based on your data model
    // Example for sale_order table:
    // await database.update(
    //   'sale_order',
    //   {'id': serverId},
    //   where: 'local_id = ?',
    //   whereArgs: [localId],
    // );
  }

  // ==================== PULL (Download) ====================

  /// Pull server changes
  Future<PullResponse> pull({
    List<String>? modelsFilter,
    int limit = 100,
    bool includePayload = true,
  }) async {
    _syncStatusController.add('Pulling server changes...');

    try {
      // Get last event ID
      final lastEventId = await _getLastEventId();

      print('Pulling changes since event $lastEventId...');

      // Call API
      final response = await _dio.post(
        '$baseUrl/api/v1/offline-sync/pull',
        data: {
          'device_id': deviceId,
          'app_type': appType,
          'last_event_id': lastEventId,
          'models_filter': modelsFilter,
          'limit': limit,
          'include_payload': includePayload,
        },
      );

      final result = PullResponse.fromJson(response.data);

      if (result.hasUpdates) {
        print('Pulled ${result.newEventsCount} new events');
        _syncStatusController.add('Pulled ${result.newEventsCount} events');

        // Apply events to local database
        await _applyServerEvents(result.events);

        // Update last event ID
        await _setLastEventId(result.lastEventId);
      } else {
        print('No new updates from server');
        _syncStatusController.add('No new updates');
      }

      return result;
    } catch (e) {
      print('Pull failed: $e');
      _syncStatusController.add('Pull failed: $e');
      rethrow;
    }
  }

  /// Apply server events to local database
  Future<void> _applyServerEvents(List<ServerChange> events) async {
    for (final event in events) {
      try {
        switch (event.action) {
          case 'create':
          case 'write':
            await _applyCreateOrUpdate(event);
            break;
          case 'unlink':
            await _applyDelete(event);
            break;
        }
      } catch (e) {
        print('Error applying event ${event.eventId}: $e');
      }
    }
  }

  /// Apply create/update event
  Future<void> _applyCreateOrUpdate(ServerChange event) async {
    // TODO: Implement based on your data model
    // Example for sale_order:
    // final table = event.model.replaceAll('.', '_');
    // await database.insert(
    //   table,
    //   {
    //     'id': event.recordId,
    //     ...event.data,
    //     'synced_at': DateTime.now().toIso8601String(),
    //   },
    //   conflictAlgorithm: ConflictAlgorithm.replace,
    // );
    print('Applied ${event.action} for ${event.model}:${event.recordId}');
  }

  /// Apply delete event
  Future<void> _applyDelete(ServerChange event) async {
    // TODO: Implement based on your data model
    // Example for sale_order:
    // final table = event.model.replaceAll('.', '_');
    // await database.delete(
    //   table,
    //   where: 'id = ?',
    //   whereArgs: [event.recordId],
    // );
    print('Applied delete for ${event.model}:${event.recordId}');
  }

  // ==================== FULL SYNC ====================

  /// Perform complete sync (push then pull)
  Future<void> syncOnce() async {
    if (_isSyncing) {
      print('Sync already in progress');
      return;
    }

    try {
      _syncStatusController.add('Starting sync...');

      // Push first
      final pushResult = await push();

      // Handle conflicts if any
      if (pushResult.conflicts > 0) {
        print('${pushResult.conflicts} conflicts detected');
        _syncStatusController.add('${pushResult.conflicts} conflicts need resolution');
        // Conflicts should be handled by the UI
      }

      // Then pull
      await pull();

      _syncStatusController.add('Sync completed');
      print('Sync completed successfully');
    } catch (e) {
      print('Sync failed: $e');
      _syncStatusController.add('Sync failed');
      // Don't rethrow, let background sync retry
    }
  }

  // ==================== BACKGROUND SYNC ====================

  /// Start background sync
  void startBackgroundSync({Duration interval = const Duration(seconds: 30)}) {
    _backgroundSyncTimer?.cancel();

    _backgroundSyncTimer = Timer.periodic(interval, (_) {
      _trySyncIfOnline();
    });

    print('Background sync started (every ${interval.inSeconds}s)');
  }

  /// Stop background sync
  void stopBackgroundSync() {
    _backgroundSyncTimer?.cancel();
    _backgroundSyncTimer = null;
    print('Background sync stopped');
  }

  /// Try to sync if online
  Future<void> _trySyncIfOnline() async {
    // TODO: Check connectivity
    // if (await ConnectivityService.isOnline()) {
    //   await syncOnce();
    // }

    // For now, just try to sync (will fail if offline)
    try {
      await syncOnce();
    } catch (e) {
      // Silently fail, will retry next time
    }
  }

  // ==================== SYNC STATE ====================

  /// Get last event ID
  Future<int> _getLastEventId() async {
    return _prefs.getInt('last_event_id_$deviceId') ?? 0;
  }

  /// Set last event ID
  Future<void> _setLastEventId(int eventId) async {
    await _prefs.setInt('last_event_id_$deviceId', eventId);
  }

  /// Reset sync state (force full sync)
  Future<void> resetSyncState() async {
    try {
      await _dio.post(
        '$baseUrl/api/v1/offline-sync/reset',
        queryParameters: {'device_id': deviceId},
      );

      await _prefs.setInt('last_event_id_$deviceId', 0);
      print('Sync state reset');
    } catch (e) {
      print('Reset failed: $e');
      rethrow;
    }
  }

  // ==================== CLEANUP ====================

  /// Clean up old synced changes
  Future<void> _cleanupOldChanges() async {
    final cutoffDate = DateTime.now().subtract(const Duration(days: 7));

    await database.delete(
      'pending_changes',
      where: 'sync_status = ? AND local_timestamp < ?',
      whereArgs: ['synced', cutoffDate.toIso8601String()],
    );
  }

  /// Dispose resources
  void dispose() {
    _backgroundSyncTimer?.cancel();
    _syncProgressController.close();
    _syncStatusController.close();
  }
}
