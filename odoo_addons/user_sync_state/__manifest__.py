# -*- coding: utf-8 -*-
{
    'name': 'User Sync State',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Track synchronization state for BridgeCore multi-user sync',
    'description': """
User Sync State Module
=======================

This module provides:
- User/device sync state tracking
- Multi-device support per user
- App-type based synchronization
- Integration with BridgeCore Smart Sync

Features:
- Track last synced event ID per user/device
- Support multiple app types (sales_app, delivery_app, etc.)
- Sync statistics and monitoring
- Automatic state management

Compatible with BridgeCore v2 Smart Sync API
    """,
    'author': 'BridgeCore Team',
    'website': 'https://github.com/geniustep/BridgeCore',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/user_sync_state_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
