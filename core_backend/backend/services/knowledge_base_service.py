"""Knowledge Base service for managing files in Supabase with pgvector."""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from supabase import create_client, Client
from pydantic import BaseModel

from ..models import KbSource, KbChunk, KbIngestRequest, KbSearchRequest, KbSearchResult


class SupabaseKnowledgeBaseService:
    """Supabase-based knowledge base service with pgvector support."""

    def __init__(self):
        """Initialize the knowledge base service."""
        self.client: Optional[Client] = None
        self._connect()

    def _connect(self):
        """Connect to Supabase."""
        try:
            supabase_url = os.getenv("DEMO_SUPABASE_URL")
            supabase_key = os.getenv("DEMO_SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                print("Supabase credentials not found in environment variables")
                return
                
            self.client = create_client(supabase_url, supabase_key)
            
            # Initialize tables if they don't exist
            self._init_tables()
            
        except Exception as e:
            print(f"Failed to connect to Supabase: {e}")
            raise

    def _init_tables(self):
        """Initialize database tables for knowledge base."""
        try:
            # Create kb_sources table
            self.client.table("kb_sources").select("id").limit(1).execute()
        except Exception:
            # Table doesn't exist, create it
            self._create_tables()

    def _create_tables(self):
        """Create the necessary tables for knowledge base."""
        try:
            # Create kb_sources table
            self.client.rpc("create_kb_sources_table").execute()
            
            # Create kb_chunks table with pgvector
            self.client.rpc("create_kb_chunks_table").execute()
            
        except Exception as e:
            print(f"Failed to create tables: {e}")
            # For now, we'll work with existing tables if they exist

    async def ingest_file(self, tenant_id: str, file_content: str, file_name: str, file_type: str = "text") -> KbSource:
        """Ingest a file into the knowledge base."""
        try:
            # Create source record
            source_id = str(uuid.uuid4())
            source_data = {
                "id": source_id,
                "tenant_id": tenant_id,
                "type": file_type,
                "uri": file_name,
                "status": "processing",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert source
            result = self.client.table("kb_sources").insert(source_data).execute()
            
            # Process content into chunks
            chunks = self._chunk_text(file_content)
            
            # Create embeddings and store chunks
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_data = {
                    "id": chunk_id,
                    "source_id": source_id,
                    "text": chunk,
                    "chunk_index": i,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # For now, we'll store without embeddings
                # In production, you'd generate embeddings here
                self.client.table("kb_chunks").insert(chunk_data).execute()
            
            # Update source status
            self.client.table("kb_sources").update({
                "status": "ready",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", source_id).execute()
            
            return KbSource(**source_data)
            
        except Exception as e:
            print(f"Failed to ingest file: {e}")
            raise

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks

    async def search(self, tenant_id: str, query: str, top_k: int = 5) -> List[KbSearchResult]:
        """Search the knowledge base for relevant chunks."""
        try:
            # For now, simple text search
            # In production, you'd use vector similarity search
            result = self.client.table("kb_chunks").select(
                "id, text, source_id"
            ).eq("source_id", self.client.table("kb_sources").select("id").eq("tenant_id", tenant_id)).execute()
            
            # Simple keyword matching for now
            # In production, you'd use embeddings and vector similarity
            matches = []
            query_lower = query.lower()
            
            for chunk in result.data:
                if query_lower in chunk["text"].lower():
                    matches.append(KbSearchResult(
                        source_id=chunk["source_id"],
                        text=chunk["text"],
                        score=0.8  # Placeholder score
                    ))
            
            # Sort by score and return top_k
            matches.sort(key=lambda x: x.score, reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            print(f"Failed to search knowledge base: {e}")
            return []

    async def get_sources(self, tenant_id: str) -> List[KbSource]:
        """Get all knowledge base sources for a tenant."""
        try:
            result = self.client.table("kb_sources").select("*").eq("tenant_id", tenant_id).execute()
            
            sources = []
            for source_data in result.data:
                sources.append(KbSource(**source_data))
            
            return sources
            
        except Exception as e:
            print(f"Failed to get sources: {e}")
            return []

    async def delete_source(self, source_id: str) -> bool:
        """Delete a knowledge base source and all its chunks."""
        try:
            # Delete chunks first
            self.client.table("kb_chunks").delete().eq("source_id", source_id).execute()
            
            # Delete source
            result = self.client.table("kb_sources").delete().eq("id", source_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Failed to delete source: {e}")
            return False

    async def get_source_chunks(self, source_id: str) -> List[KbChunk]:
        """Get all chunks for a specific source."""
        try:
            result = self.client.table("kb_chunks").select("*").eq("source_id", source_id).execute()
            
            chunks = []
            for chunk_data in result.data:
                chunks.append(KbChunk(**chunk_data))
            
            return chunks
            
        except Exception as e:
            print(f"Failed to get source chunks: {e}")
            return []


# Global instance
knowledge_base_service = SupabaseKnowledgeBaseService()
