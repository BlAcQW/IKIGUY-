"""
Migration: Add Ghana Tourism Board RAG tables with pgvector for semantic search
Created: 2025-10-02

Creates tables for:
- Tourism destinations
- Accommodations
- Practical information (visa, SIM cards, safety, currency)
- Emergency contacts
- Tourism FAQs with vector embeddings for RAG
"""

import asyncio
import json
import os
from datetime import datetime
import asyncpg

# PostgreSQL connection from environment
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB_CORE", "kasaai_core")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"


async def migrate_up():
    """Create Ghana Tourism RAG tables and load data."""

    print("🚀 Creating Ghana Tourism Board RAG tables...")

    # SQL migrations
    migrations = [
        # Enable pgvector extension
        """
        CREATE EXTENSION IF NOT EXISTS vector;
        """,

        # Create tourism_destinations table
        """
        CREATE TABLE IF NOT EXISTS tourism_destinations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            category TEXT[] NOT NULL, -- beach, historical, nature, etc.
            description TEXT NOT NULL,
            highlights TEXT[] NOT NULL,
            best_time_to_visit TEXT,
            entry_fee TEXT,
            activities TEXT[] NOT NULL,
            difficulty TEXT,
            duration_hours TEXT,
            district TEXT,
            neighborhood TEXT,
            coordinates JSONB, -- {lat, lon}
            distance_from_accra_km INTEGER,
            contact JSONB, -- {phone, email, website}
            facilities TEXT[],
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),

            -- Vector embedding for semantic search (1536 dimensions for OpenAI embeddings)
            embedding vector(1536)
        );

        CREATE INDEX IF NOT EXISTS idx_tourism_destinations_region ON tourism_destinations(region);
        CREATE INDEX IF NOT EXISTS idx_tourism_destinations_category ON tourism_destinations USING GIN(category);
        CREATE INDEX IF NOT EXISTS idx_tourism_destinations_embedding ON tourism_destinations USING ivfflat (embedding vector_cosine_ops);
        """,

        # Create tourism_accommodations table
        """
        CREATE TABLE IF NOT EXISTS tourism_accommodations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            city TEXT NOT NULL,
            type TEXT NOT NULL, -- hotel, resort, lodge, guesthouse
            star_rating INTEGER,
            description TEXT NOT NULL,
            amenities TEXT[] NOT NULL,
            room_types JSONB NOT NULL, -- [{type, price_range_ghs}]
            location JSONB NOT NULL, -- {neighborhood, distance_from_airport_km, coordinates}
            contact JSONB NOT NULL, -- {phone, email, website}
            booking_platforms TEXT[] NOT NULL,
            special_notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),

            -- Vector embedding for semantic search
            embedding vector(1536)
        );

        CREATE INDEX IF NOT EXISTS idx_tourism_accommodations_region ON tourism_accommodations(region);
        CREATE INDEX IF NOT EXISTS idx_tourism_accommodations_type ON tourism_accommodations(type);
        CREATE INDEX IF NOT EXISTS idx_tourism_accommodations_star_rating ON tourism_accommodations(star_rating);
        CREATE INDEX IF NOT EXISTS idx_tourism_accommodations_embedding ON tourism_accommodations USING ivfflat (embedding vector_cosine_ops);
        """,

        # Create tourism_practical_info table (visa, SIM, safety, currency)
        """
        CREATE TABLE IF NOT EXISTS tourism_practical_info (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL, -- visa, mobile_sim, currency, safety, weather, culture
            subcategory TEXT,
            title TEXT NOT NULL,
            content JSONB NOT NULL,
            keywords TEXT[] NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),

            -- Vector embedding for semantic search
            embedding vector(1536)
        );

        CREATE INDEX IF NOT EXISTS idx_tourism_practical_info_category ON tourism_practical_info(category);
        CREATE INDEX IF NOT EXISTS idx_tourism_practical_info_keywords ON tourism_practical_info USING GIN(keywords);
        CREATE INDEX IF NOT EXISTS idx_tourism_practical_info_embedding ON tourism_practical_info USING ivfflat (embedding vector_cosine_ops);
        """,

        # Create tourism_faqs table for common questions
        """
        CREATE TABLE IF NOT EXISTS tourism_faqs (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords TEXT[] NOT NULL,
            relevance_score FLOAT DEFAULT 1.0,
            source_data_id TEXT, -- Reference to destination/accommodation/practical_info
            source_table TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),

            -- Vector embedding for semantic question matching
            question_embedding vector(1536),
            answer_embedding vector(1536)
        );

        CREATE INDEX IF NOT EXISTS idx_tourism_faqs_category ON tourism_faqs(category);
        CREATE INDEX IF NOT EXISTS idx_tourism_faqs_keywords ON tourism_faqs USING GIN(keywords);
        CREATE INDEX IF NOT EXISTS idx_tourism_faqs_question_embedding ON tourism_faqs USING ivfflat (question_embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS idx_tourism_faqs_answer_embedding ON tourism_faqs USING ivfflat (answer_embedding vector_cosine_ops);
        """,

        # Create function for similarity search
        """
        CREATE OR REPLACE FUNCTION match_tourism_content(
            query_embedding vector(1536),
            match_threshold float DEFAULT 0.7,
            match_count int DEFAULT 5
        )
        RETURNS TABLE (
            source_type text,
            source_id text,
            title text,
            content text,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY

            -- Search destinations
            SELECT
                'destination'::text as source_type,
                d.id as source_id,
                d.name as title,
                d.description as content,
                1 - (d.embedding <=> query_embedding) as similarity
            FROM tourism_destinations d
            WHERE 1 - (d.embedding <=> query_embedding) > match_threshold

            UNION ALL

            -- Search accommodations
            SELECT
                'accommodation'::text as source_type,
                a.id as source_id,
                a.name as title,
                a.description as content,
                1 - (a.embedding <=> query_embedding) as similarity
            FROM tourism_accommodations a
            WHERE 1 - (a.embedding <=> query_embedding) > match_threshold

            UNION ALL

            -- Search practical info
            SELECT
                'practical_info'::text as source_type,
                p.id as source_id,
                p.title as title,
                p.content::text as content,
                1 - (p.embedding <=> query_embedding) as similarity
            FROM tourism_practical_info p
            WHERE 1 - (p.embedding <=> query_embedding) > match_threshold

            ORDER BY similarity DESC
            LIMIT match_count;
        END;
        $$;
        """,
    ]

    # Connect to PostgreSQL
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Execute migrations
        for i, migration in enumerate(migrations, 1):
            try:
                print(f"   [{i}/{len(migrations)}] Executing migration...")
                await conn.execute(migration)
                print(f"   ✓ Migration {i} completed")
            except Exception as e:
                print(f"   ⚠️ Migration {i} error (may already exist): {e}")
    finally:
        await conn.close()

    print("\n✅ Ghana Tourism RAG tables created successfully!")
    print("\nNext steps:")
    print("1. Load data from JSON files into PostgreSQL")
    print("2. Generate embeddings for all content using OpenAI")
    print("3. Update tools to use RAG for enhanced responses")


async def migrate_down():
    """Drop Ghana Tourism RAG tables."""

    print("🗑️ Dropping Ghana Tourism Board RAG tables...")

    drops = [
        "DROP FUNCTION IF EXISTS match_tourism_content;",
        "DROP TABLE IF EXISTS tourism_faqs;",
        "DROP TABLE IF EXISTS tourism_practical_info;",
        "DROP TABLE IF EXISTS tourism_accommodations;",
        "DROP TABLE IF EXISTS tourism_destinations;",
    ]

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        for drop_sql in drops:
            try:
                await conn.execute(drop_sql)
                print(f"   ✓ Dropped: {drop_sql.split()[4]}")
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
    finally:
        await conn.close()

    print("✅ Ghana Tourism RAG tables dropped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        asyncio.run(migrate_down())
    else:
        asyncio.run(migrate_up())
