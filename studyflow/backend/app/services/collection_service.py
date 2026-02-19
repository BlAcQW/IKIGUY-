"""
Collection management service for StudyFlow.

Handles RAG collection lifecycle: creation, listing, statistics, and cleanup.
"""

import logging
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.rag import RAGService, RAGConfig

from app.core.database import mongodb, COLLECTION_MATERIALS
from app.models.material import StudyMaterial
from app.services.tutoring_service import TutoringService
from app.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)


class CollectionInfo:
    """Model for collection information."""

    def __init__(
        self,
        name: str,
        organization_id: str,
        subject: str,
        grade: Optional[int],
        document_count: int = 0,
        material_count: int = 0,
        created_at: Optional[datetime] = None,
        last_updated: Optional[datetime] = None
    ):
        self.name = name
        self.organization_id = organization_id
        self.subject = subject
        self.grade = grade
        self.document_count = document_count
        self.material_count = material_count
        self.created_at = created_at
        self.last_updated = last_updated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "organization_id": self.organization_id,
            "subject": self.subject,
            "grade": self.grade,
            "document_count": self.document_count,
            "material_count": self.material_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class CollectionService:
    """
    Service for managing RAG collections.

    Provides collection lifecycle management for organization-scoped
    knowledge bases.
    """

    _rag_service: Optional[RAGService] = None

    @classmethod
    def get_rag_service(cls) -> RAGService:
        """
        Get or create RAG service instance.

        Returns:
            RAGService instance
        """
        if cls._rag_service is None:
            config = RAGConfig(
                postgres_host=settings.POSTGRES_HOST,
                postgres_port=settings.POSTGRES_PORT,
                postgres_user=settings.POSTGRES_USER,
                postgres_password=settings.POSTGRES_PASSWORD,
                postgres_db=settings.POSTGRES_DB,
                ai_provider=settings.AI_PROVIDER,
                api_key=settings.GEMINI_API_KEY,
                llm_model=settings.GEMINI_MODEL,
                embedding_model=settings.GEMINI_EMBEDDING_MODEL
            )

            cls._rag_service = RAGService(config)
            logger.info("✓ RAG Service initialized for collection management")

        return cls._rag_service

    @staticmethod
    async def list_organization_collections(
        organization_id: str
    ) -> List[CollectionInfo]:
        """
        List all RAG collections for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of collection information
        """
        # Get all materials for this organization
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)
        cursor = materials_collection.find({
            "organization_id": organization_id,
            "status": "completed",
            "embedding_collection": {"$exists": True, "$ne": None}
        })

        # Group by collection name
        collections_map: Dict[str, CollectionInfo] = {}

        async for material_doc in cursor:
            collection_name = material_doc.get("embedding_collection")
            if not collection_name:
                continue

            if collection_name not in collections_map:
                # Parse collection name to extract subject and grade
                # Format: studyflow_{org_id}_{subject}_grade{X} or studyflow_{org_id}_{subject}
                parts = collection_name.split("_")
                subject = "unknown"
                grade = None

                # Try to extract subject and grade from collection name
                if len(parts) >= 3:
                    # studyflow_{org}_{subject}... format
                    if parts[0] == "studyflow":
                        subject_parts = parts[2:]  # Everything after org_id

                        # Check if last part is gradeX
                        if subject_parts and subject_parts[-1].startswith("grade"):
                            try:
                                grade = int(subject_parts[-1].replace("grade", ""))
                                subject = "_".join(subject_parts[:-1])
                            except ValueError:
                                subject = "_".join(subject_parts)
                        else:
                            subject = "_".join(subject_parts)

                collections_map[collection_name] = CollectionInfo(
                    name=collection_name,
                    organization_id=organization_id,
                    subject=subject,
                    grade=grade,
                    material_count=0,
                    document_count=0,
                    created_at=material_doc.get("created_at"),
                    last_updated=material_doc.get("processed_at")
                )

            # Increment counts
            collections_map[collection_name].material_count += 1
            collections_map[collection_name].document_count += material_doc.get("chunks_count", 0)

            # Update last_updated if this material is newer
            material_updated = material_doc.get("processed_at")
            if material_updated:
                current_updated = collections_map[collection_name].last_updated
                if not current_updated or material_updated > current_updated:
                    collections_map[collection_name].last_updated = material_updated

        return list(collections_map.values())

    @staticmethod
    async def get_collection_stats(collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a collection.

        Args:
            collection_name: Collection name

        Returns:
            Collection statistics or None if not found
        """
        # Get materials using this collection
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)
        cursor = materials_collection.find({"embedding_collection": collection_name})

        total_materials = 0
        total_chunks = 0
        total_size = 0
        subjects = set()
        grades = set()
        earliest_created = None
        latest_updated = None

        async for material_doc in cursor:
            total_materials += 1
            total_chunks += material_doc.get("chunks_count", 0)
            total_size += material_doc.get("file_size", 0)

            subject = material_doc.get("subject")
            if subject:
                subjects.add(subject)

            grade = material_doc.get("grade")
            if grade:
                grades.add(grade)

            created = material_doc.get("created_at")
            if created:
                if not earliest_created or created < earliest_created:
                    earliest_created = created

            updated = material_doc.get("processed_at")
            if updated:
                if not latest_updated or updated > latest_updated:
                    latest_updated = updated

        if total_materials == 0:
            return None

        return {
            "collection_name": collection_name,
            "total_materials": total_materials,
            "total_document_chunks": total_chunks,
            "total_file_size_bytes": total_size,
            "subjects": list(subjects),
            "grades": sorted(list(grades)) if grades else [],
            "created_at": earliest_created.isoformat() if earliest_created else None,
            "last_updated": latest_updated.isoformat() if latest_updated else None,
            "avg_chunks_per_material": total_chunks / total_materials if total_materials > 0 else 0
        }

    @staticmethod
    async def delete_collection(
        collection_name: str,
        organization_id: str
    ) -> bool:
        """
        Delete a RAG collection and update associated materials.

        CAUTION: This permanently removes embeddings from the vector database.

        Args:
            collection_name: Collection name to delete
            organization_id: Organization ID for verification

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify collection belongs to organization (security check)
            if organization_id not in collection_name:
                logger.error(
                    f"Collection {collection_name} does not belong to "
                    f"organization {organization_id}"
                )
                return False

            # Get RAG service
            rag = CollectionService.get_rag_service()

            # Delete collection from vector database
            # Note: The shared RAG service may not have a delete_collection method
            # This would need to be added to the shared service or done via raw SQL
            logger.warning(
                f"Collection deletion requested for {collection_name}. "
                "Manual cleanup may be required in pgvector database."
            )

            # Update all materials that used this collection
            materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)
            result = await materials_collection.update_many(
                {
                    "embedding_collection": collection_name,
                    "organization_id": organization_id
                },
                {
                    "$set": {
                        "embedding_collection": None,
                        "status": "pending",  # Mark for reprocessing
                        "chunks_count": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(
                f"Collection {collection_name} cleared from {result.modified_count} materials. "
                "Materials marked for reprocessing."
            )

            return True

        except Exception as e:
            logger.error(f"Collection deletion error: {str(e)}")
            return False

    @staticmethod
    async def reindex_collection(
        collection_name: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Reindex all materials in a collection.

        Useful when:
        - RAG configuration changes
        - Embedding model is upgraded
        - Documents need to be re-chunked

        Args:
            collection_name: Collection to reindex
            organization_id: Organization ID for verification

        Returns:
            Dict with reindexing results
        """
        # Get all materials for this collection
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)
        cursor = materials_collection.find({
            "embedding_collection": collection_name,
            "organization_id": organization_id
        })

        material_ids = []
        async for material_doc in cursor:
            material_ids.append(str(material_doc["_id"]))

        logger.info(f"Reindexing {len(material_ids)} materials in collection {collection_name}")

        # TODO: Trigger batch reprocessing
        # This would use MaterialProcessor.process_materials_batch()
        # For now, just mark materials for reprocessing
        await materials_collection.update_many(
            {
                "embedding_collection": collection_name,
                "organization_id": organization_id
            },
            {
                "$set": {
                    "status": "pending",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {
            "collection_name": collection_name,
            "materials_marked_for_reindex": len(material_ids),
            "material_ids": material_ids
        }

    @staticmethod
    def parse_collection_name(collection_name: str) -> Dict[str, Any]:
        """
        Parse a collection name into its components.

        Args:
            collection_name: Collection name to parse

        Returns:
            Dict with organization_id, subject, grade (if any)
        """
        parts = collection_name.split("_")

        result = {
            "organization_id": None,
            "subject": None,
            "grade": None,
            "is_legacy": False
        }

        if not parts or parts[0] != "studyflow":
            return result

        # Check if it's org-scoped (studyflow_{org}_{subject}...) or legacy (studyflow_{subject}...)
        if len(parts) >= 3:
            # Could be org-scoped
            # Try to determine if parts[1] looks like an org_id
            # For now, assume format: studyflow_{org_id}_{subject}_grade{X}
            result["organization_id"] = parts[1]
            subject_parts = parts[2:]

            # Check for grade suffix
            if subject_parts and subject_parts[-1].startswith("grade"):
                try:
                    result["grade"] = int(subject_parts[-1].replace("grade", ""))
                    result["subject"] = "_".join(subject_parts[:-1])
                except ValueError:
                    result["subject"] = "_".join(subject_parts)
            else:
                result["subject"] = "_".join(subject_parts)
        elif len(parts) == 2:
            # Legacy format: studyflow_{subject}
            result["subject"] = parts[1]
            result["is_legacy"] = True

        return result
