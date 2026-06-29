#!/bin/bash
# Script to reset rate limits using docker redis-cli
# This script uses docker exec to access Redis directly, no Python dependencies needed

cd "$(dirname "$0")/.." || exit 1

TENANT_ID="${1}"
RESET_TYPE="${2:-all}"

if [ -z "$TENANT_ID" ]; then
    echo "Usage: $0 <tenant_id> [daily|hourly|all]"
    echo ""
    echo "Examples:"
    echo "  $0 9b230aba-8477-4979-a345-04c9b255cf45 daily"
    echo "  $0 9b230aba-8477-4979-a345-04c9b255cf45 hourly"
    echo "  $0 9b230aba-8477-4979-a345-04c9b255cf45 all"
    exit 1
fi

# Get Redis container name (prefer bridgecore_redis)
REDIS_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "bridgecore_redis" | head -1)
if [ -z "$REDIS_CONTAINER" ]; then
    REDIS_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "redis|bridgecore.*redis" | head -1)
fi

if [ -z "$REDIS_CONTAINER" ]; then
    echo "❌ Error: Redis container not found"
    exit 1
fi

echo "Using Redis container: $REDIS_CONTAINER"

# Get current date/time for keys
NOW=$(date -u +"%Y%m%d")
HOUR=$(date -u +"%Y%m%d%H")

if [ "$RESET_TYPE" = "daily" ]; then
    DAY_KEY="rate_limit:tenant:${TENANT_ID}:day:${NOW}"
    echo "Deleting daily key: $DAY_KEY"
    docker exec $REDIS_CONTAINER redis-cli DEL "$DAY_KEY"
    echo "✅ Daily rate limit reset for tenant $TENANT_ID"
elif [ "$RESET_TYPE" = "hourly" ]; then
    HOUR_KEY="rate_limit:tenant:${TENANT_ID}:hour:${HOUR}"
    echo "Deleting hourly key: $HOUR_KEY"
    docker exec $REDIS_CONTAINER redis-cli DEL "$HOUR_KEY"
    echo "✅ Hourly rate limit reset for tenant $TENANT_ID"
elif [ "$RESET_TYPE" = "all" ]; then
    # Delete all keys for this tenant
    PATTERN="rate_limit:tenant:${TENANT_ID}:*"
    echo "Finding keys matching: $PATTERN"
    KEYS=$(docker exec $REDIS_CONTAINER redis-cli KEYS "$PATTERN" 2>/dev/null)
    if [ -z "$KEYS" ] || [ "$KEYS" = "" ]; then
        echo "ℹ️  No rate limit keys found for tenant $TENANT_ID"
    else
        # Count keys (handle both single line and multi-line)
        KEY_COUNT=$(echo "$KEYS" | grep -c "^" || echo "0")
        if [ "$KEY_COUNT" -eq 0 ]; then
            echo "ℹ️  No rate limit keys found for tenant $TENANT_ID"
        else
            echo "Found $KEY_COUNT key(s), deleting..."
            # Delete all keys at once
            echo "$KEYS" | xargs -I {} docker exec $REDIS_CONTAINER redis-cli DEL "{}" > /dev/null 2>&1
            echo "✅ All rate limits reset for tenant $TENANT_ID ($KEY_COUNT keys deleted)"
        fi
    fi
else
    echo "❌ Invalid reset_type: $RESET_TYPE"
    echo "Use: daily, hourly, or all"
    exit 1
fi
