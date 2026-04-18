-- ============================================================
-- PostgreSQL initialisation script
-- Runs automatically when the container starts for the first time.
-- ============================================================

-- Create the student table
CREATE TABLE IF NOT EXISTS student (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- REPLICA IDENTITY FULL lets Debezium capture the full "before" row
-- image on UPDATE / DELETE (not just the primary key).
ALTER TABLE student REPLICA IDENTITY FULL;

-- Seed a couple of rows so there is something to see immediately.
INSERT INTO student (name) VALUES ('Alice'), ('Bob');
