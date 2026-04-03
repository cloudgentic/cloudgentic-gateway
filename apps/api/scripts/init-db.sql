-- Create audit-only role for append-only audit logs
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gateway_audit_writer') THEN
        CREATE ROLE gateway_audit_writer WITH LOGIN PASSWORD 'audit_writer_password';
    END IF;
END
$$;

-- Permissions are granted after tables are created by Alembic migrations
