-- Create test database for running tests in isolation
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create test database
CREATE DATABASE learnr_test;

-- Grant all privileges to learnr user on test database
GRANT ALL PRIVILEGES ON DATABASE learnr_test TO learnr;

-- Connect to test database and grant schema permissions
\c learnr_test
GRANT ALL ON SCHEMA public TO learnr;
