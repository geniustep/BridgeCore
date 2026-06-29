-- Migration: Add alerts and IP blocks tables
-- Run this in your PostgreSQL database

-- Create enum types
DO $$ BEGIN
    CREATE TYPE alerttype AS ENUM (
        'rate_limit_warning', 'rate_limit_exceeded', 'high_error_rate',
        'slow_response', 'suspicious_ip', 'tenant_suspended',
        'connection_failed', 'security_threat'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alertseverity AS ENUM ('info', 'warning', 'error', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alertstatus AS ENUM ('active', 'acknowledged', 'resolved', 'dismissed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE blockreason AS ENUM (
        'rate_limit_abuse', 'brute_force', 'suspicious_activity',
        'security_threat', 'manual_block', 'spam'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    
    -- Alert details
    alert_type alerttype NOT NULL,
    severity alertseverity DEFAULT 'warning' NOT NULL,
    status alertstatus DEFAULT 'active' NOT NULL,
    
    -- Content
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    
    -- Thresholds
    threshold_value INTEGER,
    current_value INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    acknowledged_at TIMESTAMP,
    acknowledged_by UUID REFERENCES admins(id),
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES admins(id),
    
    -- Auto-dismiss
    auto_resolve BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS ix_alerts_id ON alerts(id);
CREATE INDEX IF NOT EXISTS ix_alerts_tenant_id ON alerts(tenant_id);
CREATE INDEX IF NOT EXISTS ix_alerts_alert_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS ix_alerts_tenant_type ON alerts(tenant_id, alert_type);
CREATE INDEX IF NOT EXISTS ix_alerts_status_severity ON alerts(status, severity);
CREATE INDEX IF NOT EXISTS ix_alerts_active ON alerts(status, created_at);

-- Create IP blocks table
CREATE TABLE IF NOT EXISTS ip_blocks (
    id BIGSERIAL PRIMARY KEY,
    
    -- IP Information
    ip_address VARCHAR(45) NOT NULL,
    ip_range VARCHAR(50),
    
    -- Block details
    reason blockreason NOT NULL,
    description TEXT,
    
    -- Associated tenant
    tenant_id UUID REFERENCES tenants(id),
    
    -- Block settings
    is_permanent BOOLEAN DEFAULT FALSE,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    
    -- Violation tracking
    violation_count INTEGER DEFAULT 1,
    last_violation_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Admin info
    blocked_by UUID REFERENCES admins(id),
    
    -- Unblock info
    is_active BOOLEAN DEFAULT TRUE,
    unblocked_at TIMESTAMP,
    unblocked_by UUID REFERENCES admins(id),
    unblock_reason TEXT,
    
    -- Context
    user_agent VARCHAR(500),
    request_details JSONB
);

-- Create indexes for ip_blocks
CREATE INDEX IF NOT EXISTS ix_ip_blocks_id ON ip_blocks(id);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_ip_address ON ip_blocks(ip_address);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_reason ON ip_blocks(reason);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_tenant_id ON ip_blocks(tenant_id);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_blocked_at ON ip_blocks(blocked_at);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_expires_at ON ip_blocks(expires_at);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_is_active ON ip_blocks(is_active);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_active_ip ON ip_blocks(is_active, ip_address);
CREATE INDEX IF NOT EXISTS ix_ip_blocks_expires ON ip_blocks(is_active, expires_at);

-- Verify tables created
SELECT 'alerts table created' AS status WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alerts');
SELECT 'ip_blocks table created' AS status WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ip_blocks');

