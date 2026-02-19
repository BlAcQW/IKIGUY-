"""
Real integration tests for PostgreSQL RAG system.
Tests against actual PostgreSQL database with pgvector, no mocks.
"""
import pytest
import pytest_asyncio
import asyncpg
import os

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

DATABASE_URL = f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD', 'aawwER444444')}@localhost:5432/kasaai_core"


@pytest_asyncio.fixture(scope="function")
async def db_conn():
    """Create database connection for tests."""
    conn = await asyncpg.connect(DATABASE_URL)
    yield conn
    await conn.close()


class TestDatabaseSchema:
    """Test that database schema is correctly created."""

    @pytest.mark.asyncio
    async def test_pgvector_extension_exists(self, db_conn):
        """Test that pgvector extension is installed."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        assert result is True, "pgvector extension should be installed"

    @pytest.mark.asyncio
    async def test_tourism_destinations_table_exists(self, db_conn):
        """Test that tourism_destinations table exists."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'tourism_destinations'
            );
        """)
        assert result is True

    @pytest.mark.asyncio
    async def test_tourism_accommodations_table_exists(self, db_conn):
        """Test that tourism_accommodations table exists."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'tourism_accommodations'
            );
        """)
        assert result is True

    @pytest.mark.asyncio
    async def test_tourism_practical_info_table_exists(self, db_conn):
        """Test that tourism_practical_info table exists."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'tourism_practical_info'
            );
        """)
        assert result is True

    @pytest.mark.asyncio
    async def test_destinations_has_vector_column(self, db_conn):
        """Test that destinations table has embedding column."""
        result = await db_conn.fetchval("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'tourism_destinations' AND column_name = 'embedding';
        """)
        assert result == "USER-DEFINED", "embedding column should be vector type"


class TestDataLoading:
    """Test that data is loaded correctly."""

    @pytest.mark.asyncio
    async def test_destinations_data_loaded(self, db_conn):
        """Test that destination data is loaded."""
        count = await db_conn.fetchval(
            "SELECT COUNT(*) FROM tourism_destinations;"
        )
        assert count == 10, "Should have 10 destinations loaded"

    @pytest.mark.asyncio
    async def test_accommodations_data_loaded(self, db_conn):
        """Test that accommodation data is loaded."""
        count = await db_conn.fetchval(
            "SELECT COUNT(*) FROM tourism_accommodations;"
        )
        assert count == 10, "Should have 10 accommodations loaded"

    @pytest.mark.asyncio
    async def test_practical_info_data_loaded(self, db_conn):
        """Test that practical info is loaded."""
        count = await db_conn.fetchval(
            "SELECT COUNT(*) FROM tourism_practical_info;"
        )
        assert count >= 6, "Should have at least 6 practical info records"

    @pytest.mark.asyncio
    async def test_all_destinations_have_embeddings(self, db_conn):
        """Test that all destinations have embeddings."""
        count = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_destinations
            WHERE embedding IS NOT NULL;
        """)
        assert count == 10, "All 10 destinations should have embeddings"

    @pytest.mark.asyncio
    async def test_all_accommodations_have_embeddings(self, db_conn):
        """Test that all accommodations have embeddings."""
        count = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_accommodations
            WHERE embedding IS NOT NULL;
        """)
        assert count == 10, "All 10 accommodations should have embeddings"

    @pytest.mark.asyncio
    async def test_embedding_dimensions(self, db_conn):
        """Test that embeddings have correct dimensions."""
        # Check a destination embedding
        embedding = await db_conn.fetchval("""
            SELECT embedding FROM tourism_destinations LIMIT 1;
        """)

        # pgvector returns embeddings as strings in format [v1,v2,...]
        # Count commas + 1 to get dimension count
        dimensions = str(embedding).count(',') + 1
        assert dimensions == 1536, "Embeddings should be 1536 dimensions"


class TestDestinationData:
    """Test destination data integrity."""

    @pytest.mark.asyncio
    async def test_kakum_national_park_exists(self, db_conn):
        """Test that Kakum National Park is in database."""
        result = await db_conn.fetchrow("""
            SELECT * FROM tourism_destinations
            WHERE name = 'Kakum National Park';
        """)

        assert result is not None
        assert result["region"] == "Central"
        assert "canopy" in result["description"].lower()
        assert "nature" in result["category"]

    @pytest.mark.asyncio
    async def test_cape_coast_castle_exists(self, db_conn):
        """Test that Cape Coast Castle is in database."""
        result = await db_conn.fetchrow("""
            SELECT * FROM tourism_destinations
            WHERE name = 'Cape Coast Castle';
        """)

        assert result is not None
        assert result["region"] == "Central"
        assert "historical" in result["category"]

    @pytest.mark.asyncio
    async def test_destinations_have_activities(self, db_conn):
        """Test that destinations have activities."""
        result = await db_conn.fetch("""
            SELECT name, activities FROM tourism_destinations;
        """)

        for row in result:
            assert len(row["activities"]) > 0, \
                f"{row['name']} should have activities"

    @pytest.mark.asyncio
    async def test_destinations_have_highlights(self, db_conn):
        """Test that destinations have highlights."""
        result = await db_conn.fetch("""
            SELECT name, highlights FROM tourism_destinations;
        """)

        for row in result:
            assert len(row["highlights"]) > 0, \
                f"{row['name']} should have highlights"


class TestAccommodationData:
    """Test accommodation data integrity."""

    @pytest.mark.asyncio
    async def test_kempinski_hotel_exists(self, db_conn):
        """Test that Kempinski Hotel is in database."""
        result = await db_conn.fetchrow("""
            SELECT * FROM tourism_accommodations
            WHERE name = 'Kempinski Hotel Gold Coast City';
        """)

        assert result is not None
        assert result["star_rating"] == 5
        assert result["type"] == "hotel"
        assert result["city"] == "Accra"

    @pytest.mark.asyncio
    async def test_accommodations_have_room_types(self, db_conn):
        """Test that accommodations have room types with prices."""
        result = await db_conn.fetch("""
            SELECT name, room_types FROM tourism_accommodations;
        """)

        for row in result:
            room_types = row["room_types"]
            assert len(room_types) > 0, f"{row['name']} should have room types"

            # Check each room type has required fields
            # asyncpg returns JSON arrays as lists of dicts
            import json
            if isinstance(room_types, str):
                room_types = json.loads(room_types)

            for room in room_types:
                assert "type" in room
                assert "price_range_ghs" in room

    @pytest.mark.asyncio
    async def test_accommodations_have_amenities(self, db_conn):
        """Test that accommodations have amenities."""
        result = await db_conn.fetch("""
            SELECT name, amenities FROM tourism_accommodations;
        """)

        for row in result:
            assert len(row["amenities"]) > 0, \
                f"{row['name']} should have amenities"


class TestPracticalInfoData:
    """Test practical information data integrity."""

    @pytest.mark.asyncio
    async def test_visa_info_exists(self, db_conn):
        """Test that visa information exists."""
        result = await db_conn.fetchrow("""
            SELECT * FROM tourism_practical_info
            WHERE category = 'visa';
        """)

        assert result is not None
        assert "visa" in result["keywords"]

    @pytest.mark.asyncio
    async def test_sim_card_info_exists(self, db_conn):
        """Test that SIM card information exists."""
        result = await db_conn.fetchrow("""
            SELECT * FROM tourism_practical_info
            WHERE category = 'mobile_sim';
        """)

        assert result is not None

    @pytest.mark.asyncio
    async def test_all_practical_categories_exist(self, db_conn):
        """Test that all expected practical info categories exist."""
        expected_categories = ['visa', 'mobile_sim', 'currency', 'safety', 'weather', 'culture']

        for category in expected_categories:
            count = await db_conn.fetchval("""
                SELECT COUNT(*) FROM tourism_practical_info
                WHERE category = $1;
            """, category)
            assert count > 0, f"Should have {category} information"


class TestVectorSearch:
    """Test vector similarity search functionality."""

    @pytest.mark.asyncio
    async def test_can_perform_cosine_similarity_search(self, db_conn):
        """Test that cosine similarity operator works."""
        # Get an embedding from database
        sample_embedding = await db_conn.fetchval("""
            SELECT embedding FROM tourism_destinations LIMIT 1;
        """)

        # Check if embeddings are properly loaded (not all zeros)
        # Convert embedding string to check if it's all zeros
        embedding_str = str(sample_embedding)
        is_all_zeros = all(x == '0' for x in embedding_str.replace('[', '').replace(']', '').replace(',', '').replace(' ', ''))

        if is_all_zeros:
            pytest.skip("Embeddings not properly loaded - all zeros. Run load_data_simple.py with OpenAI API key.")

        # Perform similarity search
        results = await db_conn.fetch("""
            SELECT name, (embedding <=> $1::vector) as distance
            FROM tourism_destinations
            ORDER BY distance
            LIMIT 3;
        """, sample_embedding)

        assert len(results) > 0
        # First result should be same item (distance ~0)
        assert results[0]["distance"] < 0.01

    @pytest.mark.asyncio
    async def test_search_similar_destinations(self, db_conn):
        """Test searching for similar destinations."""
        # Get Kakum's embedding
        kakum_embedding = await db_conn.fetchval("""
            SELECT embedding FROM tourism_destinations
            WHERE name = 'Kakum National Park';
        """)

        # Check if embeddings are properly loaded
        embedding_str = str(kakum_embedding)
        is_all_zeros = all(x == '0' for x in embedding_str.replace('[', '').replace(']', '').replace(',', '').replace(' ', ''))

        if is_all_zeros:
            pytest.skip("Embeddings not properly loaded - all zeros. Run load_data_simple.py with OpenAI API key.")

        # Find similar destinations
        results = await db_conn.fetch("""
            SELECT name, region, category,
                   (embedding <=> $1::vector) as distance
            FROM tourism_destinations
            WHERE name != 'Kakum National Park'
            ORDER BY distance
            LIMIT 3;
        """, kakum_embedding)

        assert len(results) > 0
        # Should find nature/adventure destinations
        for row in results:
            print(f"Similar to Kakum: {row['name']} (distance: {row['distance']:.4f})")

    @pytest.mark.asyncio
    async def test_search_similar_accommodations(self, db_conn):
        """Test searching for similar accommodations."""
        # Get Kempinski's embedding
        kempinski_embedding = await db_conn.fetchval("""
            SELECT embedding FROM tourism_accommodations
            WHERE name = 'Kempinski Hotel Gold Coast City';
        """)

        # Check if embeddings are properly loaded
        embedding_str = str(kempinski_embedding)
        is_all_zeros = all(x == '0' for x in embedding_str.replace('[', '').replace(']', '').replace(',', '').replace(' ', ''))

        if is_all_zeros:
            pytest.skip("Embeddings not properly loaded - all zeros. Run load_data_simple.py with OpenAI API key.")

        # Find similar accommodations
        results = await db_conn.fetch("""
            SELECT name, star_rating, type,
                   (embedding <=> $1::vector) as distance
            FROM tourism_accommodations
            WHERE name != 'Kempinski Hotel Gold Coast City'
            ORDER BY distance
            LIMIT 3;
        """, kempinski_embedding)

        assert len(results) > 0
        # Should find other luxury hotels
        print("Similar to Kempinski:")
        for row in results:
            print(f"  - {row['name']} ({row['star_rating']}-star, distance: {row['distance']:.4f})")


class TestIndexPerformance:
    """Test that indexes are working correctly."""

    @pytest.mark.asyncio
    async def test_ivfflat_index_exists_on_destinations(self, db_conn):
        """Test that vector index exists on destinations."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'tourism_destinations'
                AND indexname LIKE '%embedding%'
            );
        """)
        assert result is True, "Should have embedding index on destinations"

    @pytest.mark.asyncio
    async def test_ivfflat_index_exists_on_accommodations(self, db_conn):
        """Test that vector index exists on accommodations."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'tourism_accommodations'
                AND indexname LIKE '%embedding%'
            );
        """)
        assert result is True, "Should have embedding index on accommodations"

    @pytest.mark.asyncio
    async def test_region_index_exists(self, db_conn):
        """Test that region index exists for fast filtering."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'tourism_destinations'
                AND indexname LIKE '%region%'
            );
        """)
        assert result is True

    @pytest.mark.asyncio
    async def test_category_gin_index_exists(self, db_conn):
        """Test that GIN index exists for category array searches."""
        result = await db_conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'tourism_destinations'
                AND indexname LIKE '%category%'
            );
        """)
        assert result is True


class TestQueryPerformance:
    """Test query performance."""

    @pytest.mark.asyncio
    async def test_vector_search_is_fast(self, db_conn):
        """Test that vector search completes quickly."""
        import time

        # Get a sample embedding
        sample_embedding = await db_conn.fetchval("""
            SELECT embedding FROM tourism_destinations LIMIT 1;
        """)

        # Measure query time
        start = time.time()
        await db_conn.fetch("""
            SELECT name, (embedding <=> $1::vector) as distance
            FROM tourism_destinations
            ORDER BY distance
            LIMIT 5;
        """, sample_embedding)
        elapsed = time.time() - start

        # Should complete in under 100ms
        assert elapsed < 0.1, f"Vector search took {elapsed:.3f}s, should be < 0.1s"

    @pytest.mark.asyncio
    async def test_filtered_search_is_fast(self, db_conn):
        """Test that filtered searches are fast."""
        import time

        start = time.time()
        await db_conn.fetch("""
            SELECT * FROM tourism_destinations
            WHERE region = 'Greater Accra'
            AND 'beach' = ANY(category);
        """)
        elapsed = time.time() - start

        # Should complete in under 50ms
        assert elapsed < 0.05, f"Filtered search took {elapsed:.3f}s, should be < 0.05s"


class TestDataConsistency:
    """Test data consistency across tables."""

    @pytest.mark.asyncio
    async def test_no_null_names(self, db_conn):
        """Test that no records have null names."""
        destinations_null = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_destinations WHERE name IS NULL;
        """)
        accommodations_null = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_accommodations WHERE name IS NULL;
        """)

        assert destinations_null == 0
        assert accommodations_null == 0

    @pytest.mark.asyncio
    async def test_no_null_descriptions(self, db_conn):
        """Test that no records have null descriptions."""
        destinations_null = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_destinations WHERE description IS NULL;
        """)
        accommodations_null = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_accommodations WHERE description IS NULL;
        """)

        assert destinations_null == 0
        assert accommodations_null == 0

    @pytest.mark.asyncio
    async def test_all_ids_are_unique(self, db_conn):
        """Test that all IDs are unique."""
        dest_count = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_destinations;
        """)
        dest_unique = await db_conn.fetchval("""
            SELECT COUNT(DISTINCT id) FROM tourism_destinations;
        """)

        assert dest_count == dest_unique, "All destination IDs should be unique"

        acc_count = await db_conn.fetchval("""
            SELECT COUNT(*) FROM tourism_accommodations;
        """)
        acc_unique = await db_conn.fetchval("""
            SELECT COUNT(DISTINCT id) FROM tourism_accommodations;
        """)

        assert acc_count == acc_unique, "All accommodation IDs should be unique"
