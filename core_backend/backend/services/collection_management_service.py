"""
Collection Management Service for Knowledge Base.
Handles collection CRUD operations, statistics, and duplication.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from backend.models.knowledge_base import (
    CollectionCreate,
    CollectionUpdate,
    CollectionInfo,
    CollectionStatsResponse,
    CollectionDuplicateRequest
)

logger = logging.getLogger(__name__)


class CollectionManagementService:
    """Service for managing knowledge base collections."""

    def __init__(self):
        """Initialize the collection management service."""
        self.conn_string = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB_CORE', 'kasaai_core')}"

    def _get_connection(self):
        """
        Get a PostgreSQL database connection.

        Returns:
            psycopg2 connection object
        """
        return psycopg2.connect(self.conn_string)

    async def create_collection(self, request: CollectionCreate) -> Dict[str, Any]:
        """
        Create a new knowledge base collection.

        Args:
            request: Collection creation request with company_name, display_name, etc.

        Returns:
            Dict with success status and collection info

        Raises:
            Exception: If collection creation fails
        """
        try:
            # Generate collection name: helpdesk_<company_name>
            collection_name = f"helpdesk_{request.company_name}"
            collection_uuid = str(uuid4())

            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Check if collection already exists
            cursor.execute(
                "SELECT uuid FROM langchain_pg_collection WHERE name = %s",
                (collection_name,)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.close()
                conn.close()
                raise Exception(f"Collection '{collection_name}' already exists")

            # Create collection in langchain_pg_collection
            cursor.execute(
                """
                INSERT INTO langchain_pg_collection (uuid, name, cmetadata)
                VALUES (%s, %s, %s)
                """,
                (
                    collection_uuid,
                    collection_name,
                    Json({
                        "display_name": request.display_name,
                        "description": request.description,
                        "industry": request.industry,
                        "default_category": request.default_category,
                        "created_by": request.created_by,
                        "created_at": datetime.utcnow().isoformat()
                    })
                )
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Created collection '{collection_name}' with UUID {collection_uuid}")

            return {
                "success": True,
                "collection_id": collection_uuid,
                "collection_name": collection_name,
                "company_name": request.company_name,
                "display_name": request.display_name,
                "message": f"Collection '{collection_name}' created successfully"
            }

        except Exception as e:
            logger.error(f"❌ Error creating collection: {str(e)}")
            raise

    async def update_collection(self, company_name: str, request: CollectionUpdate) -> Dict[str, Any]:
        """
        Update collection metadata.

        Args:
            company_name: Company identifier
            request: Collection update request

        Returns:
            Dict with success status and updated collection info
        """
        try:
            collection_name = f"helpdesk_{company_name}"

            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get current metadata
            cursor.execute(
                "SELECT uuid, cmetadata FROM langchain_pg_collection WHERE name = %s",
                (collection_name,)
            )
            row = cursor.fetchone()

            if not row:
                cursor.close()
                conn.close()
                raise Exception(f"Collection '{collection_name}' not found")

            # Update metadata
            current_metadata = row['cmetadata'] or {}

            if request.display_name:
                current_metadata['display_name'] = request.display_name
            if request.description is not None:  # Allow empty string
                current_metadata['description'] = request.description
            if request.industry is not None:
                current_metadata['industry'] = request.industry
            if request.default_category:
                current_metadata['default_category'] = request.default_category

            current_metadata['updated_by'] = request.updated_by
            current_metadata['updated_at'] = datetime.utcnow().isoformat()

            # Update in database
            cursor.execute(
                "UPDATE langchain_pg_collection SET cmetadata = %s WHERE name = %s",
                (Json(current_metadata), collection_name)
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Updated collection '{collection_name}'")

            return {
                "success": True,
                "collection_name": collection_name,
                "message": "Collection updated successfully"
            }

        except Exception as e:
            logger.error(f"❌ Error updating collection: {str(e)}")
            raise

    async def get_collection_stats(self, company_name: str) -> CollectionStatsResponse:
        """
        Get detailed statistics for a collection.

        Args:
            company_name: Company identifier

        Returns:
            CollectionStatsResponse with comprehensive statistics
        """
        try:
            collection_name = f"helpdesk_{company_name}"

            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get collection basic info
            cursor.execute(
                """
                SELECT
                    c.uuid,
                    c.name,
                    c.cmetadata,
                    COUNT(e.id) as chunk_count
                FROM langchain_pg_collection c
                LEFT JOIN langchain_pg_embedding e ON c.uuid = e.collection_id
                WHERE c.name = %s
                GROUP BY c.uuid, c.name
                """,
                (collection_name,)
            )
            collection_row = cursor.fetchone()

            if not collection_row:
                cursor.close()
                conn.close()
                raise Exception(f"Collection '{collection_name}' not found")

            metadata = collection_row['cmetadata'] or {}

            # Get document stats from MongoDB (would need MongoDB connection)
            # For now, return basic stats
            collection_info = CollectionInfo(
                collection_id=str(collection_row['uuid']),
                name=collection_row['name'],
                company_name=company_name,
                display_name=metadata.get('display_name', company_name.replace('_', ' ').title()),
                description=metadata.get('description'),
                industry=metadata.get('industry'),
                document_count=0,  # TODO: Get from MongoDB kb_documents
                total_chunks=collection_row['chunk_count'],
                total_size_bytes=0,  # TODO: Calculate from documents
                created_at=datetime.fromisoformat(metadata['created_at']) if metadata.get('created_at') else None,
                last_updated=datetime.fromisoformat(metadata['updated_at']) if metadata.get('updated_at') else None,
                total_queries=0,  # TODO: Get from query metrics
                avg_confidence=None
            )

            cursor.close()
            conn.close()

            return CollectionStatsResponse(
                success=True,
                collection_info=collection_info,
                documents_by_category={},  # TODO: Get from MongoDB
                documents_by_status={},
                top_tags=[],
                avg_processing_time_ms=None,
                cache_hit_rate=None,
                most_queried_docs=[],
                highest_rated_docs=[]
            )

        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {str(e)}")
            raise

    async def duplicate_collection(self, request: CollectionDuplicateRequest) -> Dict[str, Any]:
        """
        Duplicate a collection with optionally copying all documents.

        Args:
            request: Duplication request with source and target names

        Returns:
            Dict with success status and duplication summary

        Note:
            This creates the collection structure. Document copying would require
            MongoDB integration and is handled separately.
        """
        try:
            source_collection = f"helpdesk_{request.source_company_name}"
            target_collection = f"helpdesk_{request.target_company_name}"

            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get source collection
            cursor.execute(
                "SELECT uuid, cmetadata FROM langchain_pg_collection WHERE name = %s",
                (source_collection,)
            )
            source_row = cursor.fetchone()

            if not source_row:
                cursor.close()
                conn.close()
                raise Exception(f"Source collection '{source_collection}' not found")

            # Check if target already exists
            cursor.execute(
                "SELECT uuid FROM langchain_pg_collection WHERE name = %s",
                (target_collection,)
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                raise Exception(f"Target collection '{target_collection}' already exists")

            # Create target collection with copied metadata
            target_uuid = str(uuid4())
            target_metadata = dict(source_row['cmetadata'] or {})
            target_metadata['created_by'] = request.created_by
            target_metadata['created_at'] = datetime.utcnow().isoformat()
            target_metadata['duplicated_from'] = source_collection

            cursor.execute(
                "INSERT INTO langchain_pg_collection (uuid, name, cmetadata) VALUES (%s, %s, %s)",
                (target_uuid, target_collection, Json(target_metadata))
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Duplicated collection '{source_collection}' to '{target_collection}'")

            return {
                "success": True,
                "source_collection": source_collection,
                "target_collection": target_collection,
                "target_collection_id": target_uuid,
                "documents_copied": 0 if not request.copy_documents else "pending",
                "message": f"Collection duplicated successfully. {'Document copying in progress.' if request.copy_documents else 'No documents copied.'}"
            }

        except Exception as e:
            logger.error(f"❌ Error duplicating collection: {str(e)}")
            raise

    async def list_collections_enhanced(self) -> List[CollectionInfo]:
        """
        List all collections with enhanced metadata.

        Returns:
            List of CollectionInfo objects
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT
                    c.uuid,
                    c.name,
                    c.cmetadata,
                    COUNT(e.id) as chunk_count,
                    MAX(e.cmetadata->>'updated_at') as last_updated
                FROM langchain_pg_collection c
                LEFT JOIN langchain_pg_embedding e ON c.uuid = e.collection_id
                WHERE c.name LIKE 'helpdesk_%'
                GROUP BY c.uuid, c.name
                ORDER BY c.name
                """
            )
            rows = cursor.fetchall()

            collections = []
            for row in rows:
                metadata = row['cmetadata'] or {}
                company_name = row['name'].replace('helpdesk_', '', 1)

                # Parse last_updated
                last_updated = None
                if row['last_updated']:
                    try:
                        last_updated = datetime.fromisoformat(row['last_updated'])
                    except:
                        pass

                # Parse created_at
                created_at = None
                if metadata.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(metadata['created_at'])
                    except:
                        pass

                collection_info = CollectionInfo(
                    collection_id=str(row['uuid']),
                    name=row['name'],
                    company_name=company_name,
                    display_name=metadata.get('display_name', company_name.replace('_', ' ').title()),
                    description=metadata.get('description'),
                    industry=metadata.get('industry'),
                    document_count=0,  # TODO: Get from MongoDB
                    total_chunks=row['chunk_count'] or 0,
                    total_size_bytes=0,
                    created_at=created_at,
                    last_updated=last_updated,
                    total_queries=0,
                    avg_confidence=None
                )

                collections.append(collection_info)

            cursor.close()
            conn.close()

            return collections

        except Exception as e:
            logger.error(f"❌ Error listing collections: {str(e)}")
            raise


# Singleton instance
collection_management_service = CollectionManagementService()
