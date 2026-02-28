-- SchemaSense Database Restoration Script
-- This script recreates the Chinook dataset and custom tables in your new Supabase project.
-- Run this in the Supabase SQL Editor.

-- 1. Create Tables
CREATE TABLE IF NOT EXISTS artists (
    "ArtistId" SERIAL PRIMARY KEY,
    "Name" TEXT
);

CREATE TABLE IF NOT EXISTS albums (
    "AlbumId" SERIAL PRIMARY KEY,
    "Title" TEXT,
    "ArtistId" INTEGER REFERENCES artists("ArtistId")
);

CREATE TABLE IF NOT EXISTS tracks (
    "TrackId" SERIAL PRIMARY KEY,
    "Name" TEXT,
    "AlbumId" INTEGER REFERENCES albums("AlbumId"),
    "Milliseconds" INTEGER,
    "UnitPrice" NUMERIC(10,2),
    "Composer" TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    "DepartmentId" SERIAL PRIMARY KEY,
    "Name" TEXT
);

CREATE TABLE IF NOT EXISTS employees (
    "EmployeeId" SERIAL PRIMARY KEY,
    "Name" TEXT,
    "Salary" NUMERIC(12,2),
    "DepartmentId" INTEGER REFERENCES departments("DepartmentId")
);

-- 2. Seed Data
INSERT INTO artists ("ArtistId", "Name") VALUES
(1, 'The 1975'),
(2, 'Ricky Montgomery'),
(3, 'Ravyn Lenae'),
(4, 'Alanis Morissette'),
(5, 'Alice In Chains')
ON CONFLICT ("ArtistId") DO NOTHING;

INSERT INTO albums ("AlbumId", "Title", "ArtistId") VALUES
(1, 'Being Funny in a Foreign Language (2022)', 1),
(2, 'Montgomery Ricky (2016)', 2),
(3, 'Hypnos', 2),
(4, 'Let There Be Rock', 1),
(5, 'Big Ones', 3)
ON CONFLICT ("AlbumId") DO NOTHING;

INSERT INTO tracks ("TrackId", "Name", "AlbumId", "Milliseconds", "UnitPrice", "Composer") VALUES
(1, 'About You', 1, 343719, 0.99, 'Matthew Healy'),
(2, 'Line Without a Hook', 2, 342562, 0.99, 'Ricky Montgomery'),
(3, 'Love Me Not', 3, 230619, 0.99, 'Ravyn Lenae'),
(4, 'Restless and Wild', 3, 252051, 0.99, 'Unknown'),
(5, 'Princess of the Dawn', 3, 375418, 0.99, 'Unknown')
ON CONFLICT ("TrackId") DO NOTHING;

INSERT INTO departments ("DepartmentId", "Name") VALUES
(1, 'IT'),
(2, 'HR')
ON CONFLICT ("DepartmentId") DO NOTHING;

INSERT INTO employees ("EmployeeId", "Name", "Salary", "DepartmentId") VALUES
(1, 'John Doe', 80000.0, 1),
(2, 'Jane Smith', 90000.0, 1)
ON CONFLICT ("EmployeeId") DO NOTHING;

-- 3. Create Helper Function for API Access
-- SchemaSense uses this RPC to execute read-only queries from the backend
CREATE OR REPLACE FUNCTION execute_readonly_query(query_text TEXT)
RETURNS SETOF JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY EXECUTE query_text;
END;
$$;
