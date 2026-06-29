#!/usr/bin/env python3
"""
Script to check and reset tenant rate limits in Redis

This script can work in two modes:
1. If redis module is available: Direct Redis connection
2. If redis module is not available: Falls back to docker exec method
"""
import asyncio
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

USE_DOCKER = False
try:
    import redis.asyncio as redis
except ImportError:
    USE_DOCKER = True

from datetime import datetime, timezone

if not USE_DOCKER:
    from app.core.config import settings


async def check_rate_limits(tenant_id: str = None):
    """Check current rate limit counters"""
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    now = datetime.now(timezone.utc)
    
    if tenant_id:
        # Check specific tenant
        hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
        day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"
        
        hourly_count = await redis_client.get(hour_key)
        daily_count = await redis_client.get(day_key)
        
        print(f"Tenant: {tenant_id}")
        print(f"Hourly count: {hourly_count or 0} (limit: {settings.DEFAULT_TENANT_RATE_LIMIT_PER_HOUR})")
        print(f"Daily count: {daily_count or 0} (limit: {settings.DEFAULT_TENANT_RATE_LIMIT_PER_DAY})")
    else:
        # List all rate limit keys
        pattern = "rate_limit:tenant:*"
        keys = await redis_client.keys(pattern)
        
        print(f"Found {len(keys)} rate limit keys:")
        for key in sorted(keys):
            count = await redis_client.get(key)
            print(f"  {key}: {count or 0}")
    
    await redis_client.close()


def reset_rate_limits_docker(tenant_id: str, reset_type: str):
    """Reset rate limits using docker exec (fallback method)"""
    import subprocess
    
    # Get Redis container
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    containers = result.stdout.strip().split('\n')
    redis_container = None
    for container in containers:
        if 'bridgecore_redis' in container:
            redis_container = container
            break
        elif 'redis' in container.lower() and 'bridgecore' in container.lower():
            redis_container = container
            break
    
    if not redis_container:
        for container in containers:
            if 'redis' in container.lower():
                redis_container = container
                break
    
    if not redis_container:
        print("❌ Error: Redis container not found")
        return False
    
    now = datetime.now(timezone.utc)
    
    if reset_type == "daily":
        day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"
        subprocess.run(["docker", "exec", redis_container, "redis-cli", "DEL", day_key])
        print(f"✅ Reset daily limit for tenant {tenant_id}")
        return True
    elif reset_type == "hourly":
        hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
        subprocess.run(["docker", "exec", redis_container, "redis-cli", "DEL", hour_key])
        print(f"✅ Reset hourly limit for tenant {tenant_id}")
        return True
    elif reset_type == "all":
        pattern = f"rate_limit:tenant:{tenant_id}:*"
        result = subprocess.run(
            ["docker", "exec", redis_container, "redis-cli", "KEYS", pattern],
            capture_output=True,
            text=True
        )
        keys = [k for k in result.stdout.strip().split('\n') if k]
        if keys:
            for key in keys:
                subprocess.run(["docker", "exec", redis_container, "redis-cli", "DEL", key], 
                             capture_output=True)
            print(f"✅ Reset all limits for tenant {tenant_id} ({len(keys)} keys)")
        else:
            print(f"ℹ️  No rate limit keys found for tenant {tenant_id}")
        return True
    return False


async def reset_rate_limits(tenant_id: str = None, reset_type: str = "daily"):
    """Reset rate limit counters"""
    if USE_DOCKER:
        return reset_rate_limits_docker(tenant_id, reset_type)
    
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    now = datetime.now(timezone.utc)
    
    if tenant_id:
        if reset_type == "daily":
            day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"
            await redis_client.delete(day_key)
            print(f"✅ Reset daily limit for tenant {tenant_id}")
        elif reset_type == "hourly":
            hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
            await redis_client.delete(hour_key)
            print(f"✅ Reset hourly limit for tenant {tenant_id}")
        elif reset_type == "all":
            # Delete all keys for this tenant
            pattern = f"rate_limit:tenant:{tenant_id}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                print(f"✅ Reset all limits for tenant {tenant_id} ({len(keys)} keys)")
            else:
                print(f"ℹ️  No rate limit keys found for tenant {tenant_id}")
        else:
            print(f"❌ Invalid reset_type: {reset_type}. Use 'daily', 'hourly', or 'all'")
    else:
        # Reset all rate limits
        pattern = "rate_limit:tenant:*"
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            print(f"✅ Reset all rate limits ({len(keys)} keys)")
        else:
            print("ℹ️  No rate limit keys found")
    
    await redis_client.close()


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python reset_rate_limit.py check [tenant_id]")
        print("  python reset_rate_limit.py reset <tenant_id> [daily|hourly|all]")
        print("  python reset_rate_limit.py reset-all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        tenant_id = sys.argv[2] if len(sys.argv) > 2 else None
        await check_rate_limits(tenant_id)
    
    elif command == "reset":
        if len(sys.argv) < 3:
            print("❌ Error: tenant_id required")
            sys.exit(1)
        tenant_id = sys.argv[2]
        reset_type = sys.argv[3] if len(sys.argv) > 3 else "daily"
        if USE_DOCKER:
            reset_rate_limits_docker(tenant_id, reset_type)
        else:
            await reset_rate_limits(tenant_id, reset_type)
    
    elif command == "reset-all":
        confirm = input("⚠️  Are you sure you want to reset ALL rate limits? (yes/no): ")
        if confirm.lower() == "yes":
            await reset_rate_limits()
        else:
            print("❌ Cancelled")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
