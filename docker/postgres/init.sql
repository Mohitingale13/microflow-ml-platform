-- MicroFlow Database Initialization
-- This script runs once when the PostgreSQL container is first created.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The database itself is created by the POSTGRES_DB env var in docker-compose.
-- This script installs extensions used across all future migrations.
