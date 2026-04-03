-- Create audit-only role for append-only audit logs
-- Password is set via AUDIT_WRITER_PASSWORD env var in docker-compose
-- Default: 'changeme_audit_writer' — MUST be changed in production
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gateway_audit_writer') THEN
        EXECUTE format('CREATE ROLE gateway_audit_writer WITH LOGIN PASSWORD %L',
            coalesce(current_setting('app.audit_writer_password', true), 'changeme_audit_writer'));
    END IF;
END
$$;

-- Permissions are granted after tables are created by Alembic migrations
