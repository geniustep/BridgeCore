-- =====================================================
-- BridgeCore PostgreSQL Triggers Setup
-- Universal Change Detection System
-- =====================================================

-- This script sets up PostgreSQL triggers to automatically detect
-- and notify BridgeCore about all changes in critical Odoo tables

-- =====================================================
-- 1. Create notification function
-- =====================================================

CREATE OR REPLACE FUNCTION notify_bridgecore_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    channel TEXT;
    table_priority TEXT;
    changed_fields JSON;
BEGIN
    -- Determine priority based on table name
    CASE
        WHEN TG_TABLE_NAME IN ('sale_order', 'account_move', 'stock_picking', 'res_partner', 'purchase_order') THEN
            table_priority := 'high';
            channel := 'bridgecore_changes_high';
        WHEN TG_TABLE_NAME LIKE 'sale_%' OR TG_TABLE_NAME LIKE 'stock_%' OR TG_TABLE_NAME LIKE 'purchase_%' THEN
            table_priority := 'medium';
            channel := 'bridgecore_changes_medium';
        ELSE
            table_priority := 'low';
            channel := 'bridgecore_changes_low';
    END CASE;

    -- Calculate changed fields for UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        changed_fields := (
            SELECT json_object_agg(key, value)
            FROM json_each(row_to_json(NEW))
            WHERE value IS DISTINCT FROM (row_to_json(OLD) ->> key)::json
        );
    ELSE
        changed_fields := NULL;
    END IF;

    -- Build comprehensive payload
    payload := json_build_object(
        'operation', TG_OP,
        'table', TG_TABLE_NAME,
        'schema', TG_TABLE_SCHEMA,
        'priority', table_priority,
        'timestamp', CURRENT_TIMESTAMP,
        'database_user', current_user,
        'record_id', CASE
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        'old_data', CASE
            WHEN TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN row_to_json(OLD)
            ELSE NULL
        END,
        'new_data', CASE
            WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN row_to_json(NEW)
            ELSE NULL
        END,
        'changed_fields', changed_fields,
        'trigger_name', TG_NAME
    );

    -- Send notification to appropriate channel
    PERFORM pg_notify(channel, payload::text);

    -- Return appropriate value
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        -- Log error but don't fail the transaction
        RAISE WARNING 'Error in bridgecore trigger for table %: %', TG_TABLE_NAME, SQLERRM;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Function to create trigger for a table
-- =====================================================

CREATE OR REPLACE FUNCTION create_bridgecore_trigger(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    -- Check if table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = $1
    ) THEN
        -- Drop existing trigger if exists
        EXECUTE format('DROP TRIGGER IF EXISTS bridgecore_audit_trigger ON %I', table_name);

        -- Create new trigger
        EXECUTE format('
            CREATE TRIGGER bridgecore_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION notify_bridgecore_changes()
        ', table_name);

        RAISE NOTICE 'Created BridgeCore trigger for table: %', table_name;
    ELSE
        RAISE NOTICE 'Table % does not exist, skipping', table_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Apply triggers to critical tables
-- =====================================================

-- Critical business tables (HIGH priority)
DO $$
DECLARE
    critical_tables TEXT[] := ARRAY[
        'sale_order',
        'sale_order_line',
        'purchase_order',
        'purchase_order_line',
        'account_move',
        'account_move_line',
        'stock_picking',
        'stock_move',
        'res_partner'
    ];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY critical_tables
    LOOP
        PERFORM create_bridgecore_trigger(t);
    END LOOP;
END $$;

-- Important tables (MEDIUM priority)
DO $$
DECLARE
    important_tables TEXT[] := ARRAY[
        'product_product',
        'product_template',
        'product_category',
        'res_users',
        'stock_location',
        'stock_quant',
        'hr_employee',
        'hr_expense',
        'project_project',
        'project_task',
        'crm_lead',
        'account_payment'
    ];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY important_tables
    LOOP
        PERFORM create_bridgecore_trigger(t);
    END LOOP;
END $$;

-- Standard tables (LOW priority) - Add as needed
-- DO $$
-- DECLARE
--     standard_tables TEXT[] := ARRAY[
--         'mail_message',
--         'mail_followers'
--     ];
--     t TEXT;
-- BEGIN
--     FOREACH t IN ARRAY standard_tables
--     LOOP
--         PERFORM create_bridgecore_trigger(t);
--     END LOOP;
-- END $$;

-- =====================================================
-- 4. Create indexes for better performance
-- =====================================================

-- Indexes on update.webhook table (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'update_webhook'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_update_webhook_timestamp
            ON update_webhook(timestamp DESC);

        CREATE INDEX IF NOT EXISTS idx_update_webhook_model_timestamp
            ON update_webhook(model, timestamp DESC);

        CREATE INDEX IF NOT EXISTS idx_update_webhook_model_record
            ON update_webhook(model, record_id);

        CREATE INDEX IF NOT EXISTS idx_update_webhook_event
            ON update_webhook(event);

        CREATE INDEX IF NOT EXISTS idx_update_webhook_is_archived
            ON update_webhook(is_archived)
            WHERE is_archived = FALSE;

        RAISE NOTICE 'Created indexes on update_webhook table';
    END IF;
END $$;

-- =====================================================
-- 5. Utility functions for management
-- =====================================================

-- Function to list all BridgeCore triggers
CREATE OR REPLACE FUNCTION list_bridgecore_triggers()
RETURNS TABLE (
    table_name TEXT,
    trigger_name TEXT,
    trigger_function TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.event_object_table::TEXT,
        t.trigger_name::TEXT,
        'notify_bridgecore_changes'::TEXT
    FROM information_schema.triggers t
    WHERE t.trigger_name = 'bridgecore_audit_trigger'
    ORDER BY t.event_object_table;
END;
$$ LANGUAGE plpgsql;

-- Function to remove BridgeCore trigger from a table
CREATE OR REPLACE FUNCTION remove_bridgecore_trigger(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('DROP TRIGGER IF EXISTS bridgecore_audit_trigger ON %I', table_name);
    RAISE NOTICE 'Removed BridgeCore trigger from table: %', table_name;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Could not remove trigger from table %: %', table_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Function to remove all BridgeCore triggers
CREATE OR REPLACE FUNCTION remove_all_bridgecore_triggers()
RETURNS VOID AS $$
DECLARE
    trig RECORD;
BEGIN
    FOR trig IN
        SELECT event_object_table
        FROM information_schema.triggers
        WHERE trigger_name = 'bridgecore_audit_trigger'
    LOOP
        PERFORM remove_bridgecore_trigger(trig.event_object_table);
    END LOOP;
    RAISE NOTICE 'Removed all BridgeCore triggers';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. Test notification function
-- =====================================================

CREATE OR REPLACE FUNCTION test_bridgecore_notification()
RETURNS VOID AS $$
BEGIN
    PERFORM pg_notify('bridgecore_test', json_build_object(
        'message', 'BridgeCore notification system is working',
        'timestamp', CURRENT_TIMESTAMP
    )::text);
    RAISE NOTICE 'Test notification sent to bridgecore_test channel';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Setup Complete
-- =====================================================

-- Show summary
DO $$
DECLARE
    trigger_count INT;
BEGIN
    SELECT COUNT(*)
    INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name = 'bridgecore_audit_trigger';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'BridgeCore Triggers Setup Complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total triggers created: %', trigger_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Notification channels:';
    RAISE NOTICE '  - bridgecore_changes_high (critical tables)';
    RAISE NOTICE '  - bridgecore_changes_medium (important tables)';
    RAISE NOTICE '  - bridgecore_changes_low (standard tables)';
    RAISE NOTICE '';
    RAISE NOTICE 'Management functions available:';
    RAISE NOTICE '  - list_bridgecore_triggers()';
    RAISE NOTICE '  - create_bridgecore_trigger(table_name)';
    RAISE NOTICE '  - remove_bridgecore_trigger(table_name)';
    RAISE NOTICE '  - remove_all_bridgecore_triggers()';
    RAISE NOTICE '  - test_bridgecore_notification()';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage examples:';
    RAISE NOTICE '  SELECT * FROM list_bridgecore_triggers();';
    RAISE NOTICE '  SELECT create_bridgecore_trigger(''custom_table'');';
    RAISE NOTICE '  SELECT test_bridgecore_notification();';
    RAISE NOTICE '========================================';
END $$;
