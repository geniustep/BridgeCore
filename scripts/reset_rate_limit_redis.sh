#!/bin/bash
# Simple script to reset rate limits using redis-cli

TENANT_ID="${1}"
RESET_TYPE="${2:-all}"

if [ -z "$TENANT_ID" ]; then
    echo "Usage: $0 <tenant_id> [daily|hourly|all]"
    echo ""
    echo "Examples:"
    echo "  $0 9b230aba-8477-4979-a345-04c9b255cf45 daily"
    echo "  $0 9b230aba-8477-4979-a345-04c9b255cf45 all"
    exit 1
fi

# Get Redis URL from environment or use default
if [ -f ".env" ]; then
    export $(grep REDIS_URL .env | xargs)
fi
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

# Extract host, port, and db from REDIS_URL
if [[ $REDIS_URL == redis://* ]]; then
    REDIS_HOST_PORT=$(echo $REDIS_URL | sed 's|redis://||' | cut -d'/' -f1)
    REDIS_DB=$(echo $REDIS_URL | sed 's|redis://.*/||')
    REDIS_HOST=$(echo $REDIS_HOST_PORT | cut -d':' -f1)
    REDIS_PORT=$(echo $REDIS_HOST_PORT | cut -d':' -f2)
else
    REDIS_HOST="localhost"
    REDIS_PORT="6379"
    REDIS_DB="0"
fi

# Build redis-cli command
REDIS_CMD="redis-cli"
if [ -n "$REDIS_HOST" ] && [ "$REDIS_HOST" != "localhost" ]; then
    REDIS_CMD="$REDIS_CMD -h $REDIS_HOST"
fi
if [ -n "$REDIS_PORT" ] && [ "$REDIS_PORT" != "6379" ]; then
    REDIS_CMD="$REDIS_CMD -p $REDIS_PORT"
fi
if [ -n "$REDIS_DB" ] && [ "$REDIS_DB" != "0" ]; then
    REDIS_CMD="$REDIS_CMD -n $REDIS_DB"
fi

# Get current date/time for keys
NOW=$(date -u +"%Y%m%d")
HOUR=$(date -u +"%Y%m%d%H")

if [ "$RESET_TYPE" = "daily" ]; then
    DAY_KEY="rate_limit:tenant:${TENANT_ID}:day:${NOW}"
    echo "Deleting daily key: $DAY_KEY"
    $REDIS_CMD DEL "$DAY_KEY"
    echo "✅ Daily rate limit reset for tenant $TENANT_ID"
elif [ "$RESET_TYPE" = "hourly" ]; then
    HOUR_KEY="rate_limit:tenant:${TENANT_ID}:hour:${HOUR}"
    echo "Deleting hourly key: $HOUR_KEY"
    $REDIS_CMD DEL "$HOUR_KEY"
    echo "✅ Hourly rate limit reset for tenant $TENANT_ID"
elif [ "$RESET_TYPE" = "all" ]; then
    # Delete all keys for this tenant
    PATTERN="rate_limit:tenant:${TENANT_ID}:*"
    echo "Finding keys matching: $PATTERN"
    KEYS=$($REDIS_CMD KEYS "$PATTERN")
    if [ -z "$KEYS" ]; then
        echo "ℹ️  No rate limit keys found for tenant $TENANT_ID"
    else
        KEY_COUNT=$(echo "$KEYS" | wc -l)
        echo "Found $KEY_COUNT key(s), deleting..."
        echo "$KEYS" | xargs $REDIS_CMD DEL
        echo "✅ All rate limits reset for tenant $TENANT_ID ($KEY_COUNT keys deleted)"
    fi
else
    echo "❌ Invalid reset_type: $RESET_TYPE"
    echo "Use: daily, hourly, or all"
    exit 1
fi
