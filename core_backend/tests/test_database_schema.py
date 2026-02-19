"""
Test script to validate Core Backend database schema.

This script tests the database schema creation and ensures all tables
are properly created with the correct structure.
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

from backend.database import engine, get_session
from backend.models import Assistant, Campaign, KbSource, KbChunk, ServiceAccount, EventRecord


class TestDatabaseSchema:
    """Test database schema creation and structure."""
    
    def test_database_connection(self):
        """Test that we can connect to the database."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_tables_exist(self):
        """Test that all required tables exist."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'assistant',
            'campaign', 
            'kbsource',
            'kbchunk',
            'serviceaccount',
            'eventrecord'
        ]
        
        for table in required_tables:
            assert table in tables, f"Table {table} does not exist"
    
    def test_assistant_table_structure(self):
        """Test assistant table structure."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('assistant')}
        
        # Check required columns
        assert 'id' in columns
        assert columns['id']['type'].__class__.__name__ == 'UUID'
        assert columns['id']['primary_key'] is True
        
        assert 'tenant_id' in columns
        assert columns['tenant_id']['type'].__class__.__name__ == 'UUID'
        assert columns['tenant_id']['nullable'] is False
        
        assert 'name' in columns
        assert columns['name']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['name']['nullable'] is False
        
        assert 'template' in columns
        assert columns['template']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['template']['default'] == "'default'"
        
        assert 'channel' in columns
        assert columns['channel']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['channel']['nullable'] is False
        
        assert 'voice' in columns
        assert columns['voice']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['voice']['nullable'] is False
        
        assert 'language' in columns
        assert columns['language']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['language']['nullable'] is False
        
        assert 'prompt' in columns
        assert columns['prompt']['type'].__class__.__name__ == 'TEXT'
        assert columns['prompt']['nullable'] is False
        
        assert 'guardrails' in columns
        assert columns['guardrails']['type'].__class__.__name__ == 'TEXT'
        assert columns['guardrails']['nullable'] is True
        
        assert 'created_at' in columns
        assert columns['created_at']['type'].__class__.__name__ == 'TIMESTAMP'
        
        assert 'updated_at' in columns
        assert columns['updated_at']['type'].__class__.__name__ == 'TIMESTAMP'
    
    def test_campaign_table_structure(self):
        """Test campaign table structure."""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('campaign')}
        
        # Check required columns
        assert 'id' in columns
        assert columns['id']['type'].__class__.__name__ == 'UUID'
        assert columns['id']['primary_key'] is True
        
        assert 'tenant_id' in columns
        assert columns['tenant_id']['type'].__class__.__name__ == 'UUID'
        assert columns['tenant_id']['nullable'] is False
        
        assert 'name' in columns
        assert columns['name']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['name']['nullable'] is False
        
        assert 'assistant_id' in columns
        assert columns['assistant_id']['type'].__class__.__name__ == 'UUID'
        assert columns['assistant_id']['nullable'] is True
        
        assert 'audience_id' in columns
        assert columns['audience_id']['type'].__class__.__name__ == 'UUID'
        assert columns['audience_id']['nullable'] is True
        
        assert 'status' in columns
        assert columns['status']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['status']['default'] == "'draft'"
        
        assert 'cron' in columns
        assert columns['cron']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['cron']['nullable'] is False
        
        assert 'pacing_per_minute' in columns
        assert columns['pacing_per_minute']['type'].__class__.__name__ == 'INTEGER'
        assert columns['pacing_per_minute']['default'] == 1
        
        assert 'max_attempts' in columns
        assert columns['max_attempts']['type'].__class__.__name__ == 'INTEGER'
        assert columns['max_attempts']['default'] == 1
        
        assert 'backoff_minutes' in columns
        assert columns['backoff_minutes']['type'].__class__.__name__ == 'INTEGER'
        assert columns['backoff_minutes']['default'] == 0
    
    def test_indexes_exist(self):
        """Test that required indexes exist."""
        inspector = inspect(engine)
        
        # Check assistant indexes
        assistant_indexes = inspector.get_indexes('assistant')
        index_names = [idx['name'] for idx in assistant_indexes]
        
        assert 'idx_assistant_tenant_id' in index_names
        assert 'idx_assistant_name' in index_names
        assert 'idx_assistant_template' in index_names
        
        # Check campaign indexes
        campaign_indexes = inspector.get_indexes('campaign')
        index_names = [idx['name'] for idx in campaign_indexes]
        
        assert 'idx_campaign_tenant_id' in index_names
        assert 'idx_campaign_name' in index_names
        assert 'idx_campaign_status' in index_names
        assert 'idx_campaign_assistant_id' in index_names
    
    def test_rls_policies_exist(self):
        """Test that RLS policies exist."""
        with engine.connect() as conn:
            # Check if RLS is enabled
            result = conn.execute(text(
                "SELECT schemaname, tablename, rowsecurity FROM pg_tables "
                "WHERE tablename IN ('assistant', 'campaign', 'kbsource', 'kbchunk', 'eventrecord')"
            ))
            
            for row in result:
                assert row[2] is True, f"RLS not enabled on table {row[1]}"
            
            # Check if policies exist
            result = conn.execute(text(
                "SELECT tablename, policyname FROM pg_policies "
                "WHERE tablename IN ('assistant', 'campaign', 'kbsource', 'kbchunk', 'eventrecord')"
            ))
            
            policies = [(row[0], row[1]) for row in result]
            
            expected_policies = [
                ('assistant', 'assistant_tenant_isolation'),
                ('campaign', 'campaign_tenant_isolation'),
                ('kbsource', 'kbsource_tenant_isolation'),
                ('kbchunk', 'kbchunk_tenant_isolation'),
                ('eventrecord', 'eventrecord_tenant_isolation')
            ]
            
            for expected in expected_policies:
                assert expected in policies, f"Policy {expected[1]} not found on table {expected[0]}"
    
    def test_triggers_exist(self):
        """Test that triggers exist."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT trigger_name FROM information_schema.triggers "
                "WHERE trigger_name IN ('update_assistant_updated_at', 'update_campaign_updated_at')"
            ))
            
            triggers = [row[0] for row in result]
            
            assert 'update_assistant_updated_at' in triggers
            assert 'update_campaign_updated_at' in triggers
    
    def test_sample_data_exists(self):
        """Test that sample data exists."""
        with get_session() as session:
            # Check assistants
            assistants = session.query(Assistant).all()
            assert len(assistants) >= 2
            
            assistant_names = [a.name for a in assistants]
            assert 'Customer Support Assistant' in assistant_names
            assert 'Sales Assistant' in assistant_names
            
            # Check campaigns
            campaigns = session.query(Campaign).all()
            assert len(campaigns) >= 2
            
            campaign_names = [c.name for c in campaigns]
            assert 'Q4 Sales Campaign' in campaign_names
            assert 'Customer Follow-up' in campaign_names
    
    def test_model_operations(self):
        """Test basic model operations."""
        with get_session() as session:
            # Test creating a new assistant
            new_assistant = Assistant(
                tenant_id="550e8400-e29b-41d4-a716-446655440000",
                name="Test Assistant",
                template="test",
                channel="voice",
                voice="en-US-Neural2-F",
                language="en",
                prompt="Test prompt"
            )
            
            session.add(new_assistant)
            session.commit()
            
            # Test retrieving the assistant
            retrieved = session.query(Assistant).filter_by(name="Test Assistant").first()
            assert retrieved is not None
            assert retrieved.name == "Test Assistant"
            assert retrieved.template == "test"
            
            # Test updating the assistant
            retrieved.template = "updated"
            session.commit()
            
            updated = session.query(Assistant).filter_by(name="Test Assistant").first()
            assert updated.template == "updated"
            
            # Test deleting the assistant
            session.delete(updated)
            session.commit()
            
            deleted = session.query(Assistant).filter_by(name="Test Assistant").first()
            assert deleted is None


if __name__ == "__main__":
    pytest.main([__file__])
