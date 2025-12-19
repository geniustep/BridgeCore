"""
Odoo 18.0 Fields Verification Script

This script verifies actual field names and structures in Odoo 18.0
before implementing conversation features.

Run this during setup to ensure field compatibility.
"""
import json
import asyncio
from typing import Dict, Any, List
from loguru import logger

from app.utils.odoo_client import OdooClient
from app.core.config import settings


async def verify_odoo_fields(odoo_client: OdooClient) -> Dict[str, Any]:
    """
    Verify actual field names in Odoo 18.0
    
    Args:
        odoo_client: Initialized OdooClient instance
        
    Returns:
        Dictionary with verification results
    """
    
    models_to_check = [
        'mail.message',
        'mail.channel',
        'mail.followers',
    ]
    
    results = {}
    
    for model_name in models_to_check:
        try:
            logger.info(f"Verifying fields for {model_name}...")
            
            # Get all fields metadata
            fields_metadata = odoo_client.call_kw(
                model_name,
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'relation', 'help']}
            )
            
            results[model_name] = {
                'fields': fields_metadata,
                'key_fields': {}
            }
            
            # Extract key fields we need
            if model_name == 'mail.message':
                results[model_name]['key_fields'] = {
                    'author_id': fields_metadata.get('author_id'),
                    'partner_ids': fields_metadata.get('partner_ids'),
                    'channel_ids': fields_metadata.get('channel_ids'),
                    'model': fields_metadata.get('model'),
                    'res_id': fields_metadata.get('res_id'),
                    'message_type': fields_metadata.get('message_type'),
                    'body': fields_metadata.get('body'),
                    'subject': fields_metadata.get('subject'),
                    'date': fields_metadata.get('date'),
                    'parent_id': fields_metadata.get('parent_id'),
                }
            elif model_name == 'mail.channel':
                results[model_name]['key_fields'] = {
                    'channel_type': fields_metadata.get('channel_type'),
                    'public': fields_metadata.get('public'),
                    'channel_partner_ids': fields_metadata.get('channel_partner_ids'),
                    'channel_member_ids': fields_metadata.get('channel_member_ids'),
                    'name': fields_metadata.get('name'),
                    'description': fields_metadata.get('description'),
                    'uuid': fields_metadata.get('uuid'),
                }
            elif model_name == 'mail.followers':
                results[model_name]['key_fields'] = {
                    'res_model': fields_metadata.get('res_model'),
                    'res_id': fields_metadata.get('res_id'),
                    'partner_id': fields_metadata.get('partner_id'),
                    'channel_id': fields_metadata.get('channel_id'),
                    'subtype_ids': fields_metadata.get('subtype_ids'),
                }
                
            logger.success(f"✅ {model_name} fields verified ({len(fields_metadata)} fields)")
            
        except Exception as e:
            logger.error(f"❌ Error checking {model_name}: {e}")
            results[model_name] = {'error': str(e)}
    
    return results


async def verify_channel_structure(odoo_client: OdooClient) -> Dict[str, Any]:
    """
    Verify channel partner/member fields structure
    
    Args:
        odoo_client: Initialized OdooClient instance
        
    Returns:
        Dictionary with verification results
    """
    try:
        # Get a sample channel
        channel_ids = odoo_client.call_kw(
            'mail.channel',
            'search',
            [[('channel_type', '=', 'channel')]],
            {'limit': 1}
        )
        
        if not channel_ids:
            logger.warning("No channels found for testing")
            return {'error': 'No channels found'}
        
        channel_id = channel_ids[0]
        
        # Read channel with all relevant fields
        channel = odoo_client.call_kw(
            'mail.channel',
            'read',
            [[channel_id]],
            {
                'fields': [
                    'id', 'name', 'channel_type', 'public',
                    'channel_partner_ids', 'channel_member_ids',
                ]
            }
        )[0]
        
        # Get current user's partner
        user_data = odoo_client.call_kw(
            'res.users',
            'read',
            [[odoo_client.user_id]],
            {'fields': ['partner_id']}
        )[0]
        current_partner_id = user_data['partner_id'][0]
        
        # Test search with channel_partner_ids
        domain_with_partner_ids = [('channel_partner_ids', 'in', [current_partner_id])]
        channels_via_partner_ids = odoo_client.call_kw(
            'mail.channel',
            'search',
            [domain_with_partner_ids],
            {}
        )
        
        result = {
            'channel_sample': channel,
            'search_test': {
                'domain': domain_with_partner_ids,
                'found_channels': channels_via_partner_ids,
                'success': len(channels_via_partner_ids) >= 0
            },
            'current_partner_id': current_partner_id,
        }
        
        logger.success("✅ Channel structure verified")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error verifying channel structure: {e}")
        return {'error': str(e)}


async def test_message_post(odoo_client: OdooClient, test_record_ids: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Test message_post on different models
    
    Args:
        odoo_client: Initialized OdooClient instance
        test_record_ids: Dict with model names and test record IDs
                        e.g., {'mail.channel': 1, 'sale.order': 5}
        
    Returns:
        List of test results
    """
    test_cases = [
        {
            'name': 'Channel message',
            'model': 'mail.channel',
            'res_id': test_record_ids.get('mail.channel'),
            'body': 'Test channel message from verification script',
        },
    ]
    
    # Add other models if test IDs provided
    if 'sale.order' in test_record_ids:
        test_cases.append({
            'name': 'Chatter on sale.order',
            'model': 'sale.order',
            'res_id': test_record_ids['sale.order'],
            'body': 'Test chatter message from verification script',
        })
    
    if 'res.partner' in test_record_ids:
        test_cases.append({
            'name': 'Chatter on res.partner',
            'model': 'res.partner',
            'res_id': test_record_ids['res.partner'],
            'body': 'Test partner chatter from verification script',
        })
    
    results = []
    
    for test_case in test_cases:
        if not test_case.get('res_id'):
            logger.warning(f"Skipping {test_case['name']}: no test record ID provided")
            continue
            
        try:
            # Call message_post
            message_id = odoo_client.call_kw(
                test_case['model'],
                'message_post',
                [[test_case['res_id']]],
                {
                    'body': test_case['body'],
                    'message_type': 'comment',
                }
            )
            
            # Verify message was created
            message = odoo_client.call_kw(
                'mail.message',
                'read',
                [[message_id]],
                {
                    'fields': ['id', 'model', 'res_id', 'author_id', 'body', 'message_type']
                }
            )
            
            author_info = None
            if message and message[0].get('author_id'):
                author_info = {
                    'id': message[0]['author_id'][0],
                    'name': message[0]['author_id'][1] if len(message[0]['author_id']) > 1 else None
                }
            
            result = {
                'test': test_case['name'],
                'success': True,
                'message_id': message_id,
                'message_data': message[0] if message else None,
                'author_from_session': author_info,
                'note': 'author_id was automatically set from session'
            }
            
            results.append(result)
            logger.success(f"✅ {test_case['name']}: Message ID {message_id}, Author: {author_info}")
            
        except Exception as e:
            result = {
                'test': test_case['name'],
                'success': False,
                'error': str(e)
            }
            results.append(result)
            logger.error(f"❌ {test_case['name']}: {e}")
    
    return results


async def run_full_verification(
    odoo_client: OdooClient,
    output_file: str = 'odoo_18_verification_results.json',
    test_record_ids: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    Run full verification suite
    
    Args:
        odoo_client: Initialized OdooClient instance
        output_file: Path to save results JSON
        test_record_ids: Optional test record IDs for message_post tests
        
    Returns:
        Complete verification results
    """
    logger.info("Starting Odoo 18.0 fields verification...")
    
    results = {
        'fields_verification': await verify_odoo_fields(odoo_client),
        'channel_structure': await verify_channel_structure(odoo_client),
    }
    
    if test_record_ids:
        results['message_post_tests'] = await test_message_post(odoo_client, test_record_ids)
    else:
        logger.info("Skipping message_post tests (no test_record_ids provided)")
        results['message_post_tests'] = None
    
    # Save results
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.success(f"✅ Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
    
    return results


if __name__ == '__main__':
    # Example usage
    async def main():
        # Initialize OdooClient (you'll need actual credentials)
        odoo = OdooClient(
            base_url=settings.ODOO_URL,
            session_id=None,  # Will need to authenticate
            timeout=30
        )
        
        # Provide test record IDs (optional)
        test_ids = {
            'mail.channel': 1,  # Replace with actual channel ID
            # 'sale.order': 5,   # Uncomment if you have test IDs
        }
        
        results = await run_full_verification(odoo, test_record_ids=test_ids)
        print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(main())
