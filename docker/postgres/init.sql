CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Read-only user for analytics/reporting
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'citadel_readonly') THEN
        CREATE ROLE citadel_readonly WITH LOGIN PASSWORD 'readonly_changeme';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE citadel_marketing TO citadel_readonly;
GRANT USAGE ON SCHEMA public TO citadel_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO citadel_readonly;
