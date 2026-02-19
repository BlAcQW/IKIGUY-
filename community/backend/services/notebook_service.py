"""
Notebook sharing service for the African Language Community Platform
Handles notebook CRUD operations, voting, and analytics
"""

import json
import base64
import hashlib
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import HTTPException, status
import nbformat
from nbformat.v4 import new_notebook

from models.notebook import (
    NotebookInDB, NotebookCreate, NotebookUpdate, NotebookVersionCreate,
    NotebookVote, NotebookComment, NotebookResponse, NotebookListResponse,
    NotebookSearchQuery, NotebookVoteInDB, NotebookCommentInDB,
    NotebookBookmarkInDB, NotebookDownloadInDB, NotebookViewInDB,
    NotebookCategory, NotebookDifficulty, NotebookStatus, VoteType,
    NotebookMetadata, NotebookVersion, NotebookUsageStats
)
from core.config import get_settings

class NotebookService:
    """Service for managing notebook sharing functionality"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.settings = get_settings()
        self.notebooks_collection = db.notebooks
        self.votes_collection = db.notebook_votes
        self.comments_collection = db.notebook_comments
        self.bookmarks_collection = db.notebook_bookmarks
        self.downloads_collection = db.notebook_downloads
        self.views_collection = db.notebook_views

    async def create_notebook(
        self,
        notebook_data: NotebookCreate,
        author_id: str,
        author_name: str,
        author_email: str
    ) -> NotebookInDB:
        """Create a new notebook"""

        # Decode and validate notebook content
        try:
            notebook_content = base64.b64decode(notebook_data.file_content).decode('utf-8')
            nb = nbformat.reads(notebook_content, as_version=4)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notebook format: {str(e)}"
            )

        # Generate file metadata
        file_size = len(notebook_content.encode('utf-8'))
        checksum = hashlib.sha256(notebook_content.encode('utf-8')).hexdigest()

        # Extract notebook metadata
        metadata = await self._extract_notebook_metadata(nb)

        # Generate file path
        notebook_id = str(ObjectId())
        file_path = f"notebooks/{author_id}/{notebook_id}/v1.0.0.ipynb"

        # Create initial version
        initial_version = NotebookVersion(
            version="1.0.0",
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            upload_date=datetime.utcnow(),
            is_current=True
        )

        # Create notebook document
        notebook_doc = NotebookInDB(
            id=notebook_id,
            title=notebook_data.title,
            description=notebook_data.description,
            category=notebook_data.category,
            difficulty=notebook_data.difficulty,
            language_codes=notebook_data.language_codes,
            tags=notebook_data.tags,
            is_public=notebook_data.is_public,
            license=notebook_data.license,
            author_id=author_id,
            author_name=author_name,
            author_email=author_email,
            status=NotebookStatus.DRAFT,
            current_version="1.0.0",
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            metadata=metadata,
            versions=[initial_version],
            usage_stats=NotebookUsageStats()
        )

        # Save to database
        notebook_dict = notebook_doc.dict(by_alias=True)
        notebook_dict["_id"] = notebook_id
        await self.notebooks_collection.insert_one(notebook_dict)

        # Save file content (in production, this would go to file storage)
        await self._save_notebook_file(file_path, notebook_content)

        return notebook_doc

    async def get_notebook(self, notebook_id: str, user_id: Optional[str] = None) -> NotebookResponse:
        """Get a notebook by ID"""

        # Find notebook
        notebook_doc = await self.notebooks_collection.find_one({"_id": notebook_id})
        if not notebook_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found"
            )

        notebook = NotebookInDB(**notebook_doc)

        # Check visibility
        if not notebook.is_public and notebook.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private notebook"
            )

        # Record view
        if user_id:
            await self._record_view(notebook_id, user_id)

        # Get user-specific data
        user_vote = None
        is_bookmarked = False
        is_owner = False

        if user_id:
            user_vote_doc = await self.votes_collection.find_one({
                "notebook_id": notebook_id,
                "user_id": user_id
            })
            if user_vote_doc:
                user_vote = user_vote_doc["vote_type"]

            bookmark_doc = await self.bookmarks_collection.find_one({
                "notebook_id": notebook_id,
                "user_id": user_id
            })
            is_bookmarked = bookmark_doc is not None
            is_owner = notebook.author_id == user_id

        return NotebookResponse(
            id=notebook.id,
            title=notebook.title,
            description=notebook.description,
            category=notebook.category,
            difficulty=notebook.difficulty,
            language_codes=notebook.language_codes,
            tags=notebook.tags,
            is_public=notebook.is_public,
            license=notebook.license,
            author_name=notebook.author_name,
            current_version=notebook.current_version,
            file_size=notebook.file_size,
            upvotes=notebook.upvotes,
            downvotes=notebook.downvotes,
            rating=notebook.rating,
            comment_count=notebook.comment_count,
            usage_stats=notebook.usage_stats,
            created_at=notebook.created_at,
            updated_at=notebook.updated_at,
            published_at=notebook.published_at,
            user_vote=user_vote,
            is_bookmarked=is_bookmarked,
            is_owner=is_owner
        )

    async def search_notebooks(
        self,
        search_query: NotebookSearchQuery,
        user_id: Optional[str] = None
    ) -> NotebookListResponse:
        """Search notebooks with filters and pagination"""

        # Build MongoDB query
        query = {"status": NotebookStatus.PUBLISHED}

        # Text search
        if search_query.query:
            query["$text"] = {"$search": search_query.query}

        # Category filter
        if search_query.category:
            query["category"] = search_query.category

        # Difficulty filter
        if search_query.difficulty:
            query["difficulty"] = search_query.difficulty

        # Language codes filter
        if search_query.language_codes:
            query["language_codes"] = {"$in": search_query.language_codes}

        # Tags filter
        if search_query.tags:
            query["tags"] = {"$in": search_query.tags}

        # Author filter
        if search_query.author_id:
            query["author_id"] = search_query.author_id

        # Rating filter
        if search_query.min_rating:
            query["rating"] = {"$gte": search_query.min_rating}

        # Count total results
        total = await self.notebooks_collection.count_documents(query)

        # Build sort criteria
        sort_criteria = []
        sort_direction = 1 if search_query.sort_order == "asc" else -1

        if search_query.sort_by == "rating":
            sort_criteria.append(("rating", sort_direction))
        elif search_query.sort_by == "upvotes":
            sort_criteria.append(("upvotes", sort_direction))
        elif search_query.sort_by == "downloads":
            sort_criteria.append(("usage_stats.downloads", sort_direction))
        elif search_query.sort_by == "created_at":
            sort_criteria.append(("created_at", sort_direction))
        else:  # default to updated_at
            sort_criteria.append(("updated_at", sort_direction))

        # Calculate pagination
        skip = (search_query.page - 1) * search_query.page_size
        total_pages = (total + search_query.page_size - 1) // search_query.page_size

        # Execute query
        cursor = self.notebooks_collection.find(query).sort(sort_criteria).skip(skip).limit(search_query.page_size)
        notebook_docs = await cursor.to_list(length=search_query.page_size)

        # Convert to response models
        notebooks = []
        for doc in notebook_docs:
            notebook = NotebookInDB(**doc)

            # Get user-specific data
            user_vote = None
            is_bookmarked = False
            is_owner = False

            if user_id:
                user_vote_doc = await self.votes_collection.find_one({
                    "notebook_id": notebook.id,
                    "user_id": user_id
                })
                if user_vote_doc:
                    user_vote = user_vote_doc["vote_type"]

                bookmark_doc = await self.bookmarks_collection.find_one({
                    "notebook_id": notebook.id,
                    "user_id": user_id
                })
                is_bookmarked = bookmark_doc is not None
                is_owner = notebook.author_id == user_id

            response = NotebookResponse(
                id=notebook.id,
                title=notebook.title,
                description=notebook.description,
                category=notebook.category,
                difficulty=notebook.difficulty,
                language_codes=notebook.language_codes,
                tags=notebook.tags,
                is_public=notebook.is_public,
                license=notebook.license,
                author_name=notebook.author_name,
                current_version=notebook.current_version,
                file_size=notebook.file_size,
                upvotes=notebook.upvotes,
                downvotes=notebook.downvotes,
                rating=notebook.rating,
                comment_count=notebook.comment_count,
                usage_stats=notebook.usage_stats,
                created_at=notebook.created_at,
                updated_at=notebook.updated_at,
                published_at=notebook.published_at,
                user_vote=user_vote,
                is_bookmarked=is_bookmarked,
                is_owner=is_owner
            )
            notebooks.append(response)

        return NotebookListResponse(
            notebooks=notebooks,
            total=total,
            page=search_query.page,
            page_size=search_query.page_size,
            total_pages=total_pages
        )

    async def vote_notebook(
        self,
        notebook_id: str,
        user_id: str,
        vote_data: NotebookVote
    ) -> Dict[str, Any]:
        """Vote on a notebook"""

        # Check if notebook exists
        notebook_doc = await self.notebooks_collection.find_one({"_id": notebook_id})
        if not notebook_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found"
            )

        # Check existing vote
        existing_vote = await self.votes_collection.find_one({
            "notebook_id": notebook_id,
            "user_id": user_id
        })

        old_vote_type = None
        if existing_vote:
            old_vote_type = existing_vote["vote_type"]

            # Update existing vote
            await self.votes_collection.update_one(
                {"_id": existing_vote["_id"]},
                {
                    "$set": {
                        "vote_type": vote_data.vote_type,
                        "comment": vote_data.comment,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            # Create new vote
            vote_doc = NotebookVoteInDB(
                id=str(ObjectId()),
                notebook_id=notebook_id,
                user_id=user_id,
                vote_type=vote_data.vote_type,
                comment=vote_data.comment
            )
            await self.votes_collection.insert_one(vote_doc.dict(by_alias=True))

        # Update notebook vote counts
        await self._update_notebook_votes(notebook_id, old_vote_type, vote_data.vote_type)

        return {"message": "Vote recorded successfully"}

    async def download_notebook(self, notebook_id: str, user_id: Optional[str] = None) -> str:
        """Download notebook file content"""

        # Get notebook
        notebook_doc = await self.notebooks_collection.find_one({"_id": notebook_id})
        if not notebook_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found"
            )

        notebook = NotebookInDB(**notebook_doc)

        # Check visibility
        if not notebook.is_public and notebook.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private notebook"
            )

        # Record download
        await self._record_download(notebook_id, user_id)

        # Get file content
        file_content = await self._load_notebook_file(notebook.file_path)
        return base64.b64encode(file_content.encode('utf-8')).decode('utf-8')

    async def publish_notebook(self, notebook_id: str, user_id: str) -> Dict[str, Any]:
        """Publish a notebook"""

        # Check ownership
        notebook_doc = await self.notebooks_collection.find_one({
            "_id": notebook_id,
            "author_id": user_id
        })
        if not notebook_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )

        # Update status
        await self.notebooks_collection.update_one(
            {"_id": notebook_id},
            {
                "$set": {
                    "status": NotebookStatus.PUBLISHED,
                    "published_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {"message": "Notebook published successfully"}

    async def _extract_notebook_metadata(self, nb: nbformat.NotebookNode) -> NotebookMetadata:
        """Extract metadata from notebook"""

        # Get kernel info
        kernel_name = None
        language = None
        if 'kernelspec' in nb.metadata:
            kernel_name = nb.metadata['kernelspec'].get('name')
            language = nb.metadata['kernelspec'].get('language')

        # Count cells
        cell_count = len(nb.cells)

        # Extract dependencies (simplified - could be more sophisticated)
        dependencies = []
        for cell in nb.cells:
            if cell.cell_type == 'code':
                source = cell.source
                # Look for imports
                lines = source.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        dependencies.append(line)

        # Remove duplicates
        dependencies = list(set(dependencies))

        return NotebookMetadata(
            kernel_name=kernel_name,
            language=language,
            cell_count=cell_count,
            dependencies=dependencies
        )

    async def _update_notebook_votes(
        self,
        notebook_id: str,
        old_vote_type: Optional[str],
        new_vote_type: str
    ):
        """Update notebook vote counts"""

        update_doc = {"updated_at": datetime.utcnow()}

        # Handle vote changes
        if old_vote_type == VoteType.UPVOTE and new_vote_type == VoteType.DOWNVOTE:
            update_doc["$inc"] = {"upvotes": -1, "downvotes": 1}
        elif old_vote_type == VoteType.DOWNVOTE and new_vote_type == VoteType.UPVOTE:
            update_doc["$inc"] = {"upvotes": 1, "downvotes": -1}
        elif old_vote_type is None:
            if new_vote_type == VoteType.UPVOTE:
                update_doc["$inc"] = {"upvotes": 1}
            else:
                update_doc["$inc"] = {"downvotes": 1}

        await self.notebooks_collection.update_one(
            {"_id": notebook_id},
            update_doc
        )

        # Update rating
        await self._update_notebook_rating(notebook_id)

    async def _update_notebook_rating(self, notebook_id: str):
        """Update notebook rating based on votes"""

        notebook_doc = await self.notebooks_collection.find_one({"_id": notebook_id})
        if not notebook_doc:
            return

        upvotes = notebook_doc.get("upvotes", 0)
        downvotes = notebook_doc.get("downvotes", 0)
        total_votes = upvotes + downvotes

        if total_votes > 0:
            # Wilson score confidence interval for rating
            rating = (upvotes + 1.9208) / (total_votes + 3.8416) - \
                    1.96 * ((upvotes * downvotes) / total_votes + 0.9604) ** 0.5 / (total_votes + 3.8416)
            rating = max(0, min(1, rating)) * 5  # Scale to 0-5
        else:
            rating = 0.0

        await self.notebooks_collection.update_one(
            {"_id": notebook_id},
            {"$set": {"rating": rating}}
        )

    async def _record_view(self, notebook_id: str, user_id: str):
        """Record notebook view"""

        # Check if user already viewed recently (within last hour)
        recent_view = await self.views_collection.find_one({
            "notebook_id": notebook_id,
            "user_id": user_id,
            "viewed_at": {"$gte": datetime.utcnow().replace(minute=0, second=0, microsecond=0)}
        })

        if not recent_view:
            view_doc = NotebookViewInDB(
                id=str(ObjectId()),
                notebook_id=notebook_id,
                user_id=user_id,
                ip_address="",  # Would be filled from request
                user_agent=""   # Would be filled from request
            )
            await self.views_collection.insert_one(view_doc.dict(by_alias=True))

            # Update notebook view count
            await self.notebooks_collection.update_one(
                {"_id": notebook_id},
                {"$inc": {"usage_stats.views": 1}}
            )

    async def _record_download(self, notebook_id: str, user_id: Optional[str]):
        """Record notebook download"""

        download_doc = NotebookDownloadInDB(
            id=str(ObjectId()),
            notebook_id=notebook_id,
            user_id=user_id,
            ip_address="",  # Would be filled from request
            user_agent=""   # Would be filled from request
        )
        await self.downloads_collection.insert_one(download_doc.dict(by_alias=True))

        # Update notebook download count
        await self.notebooks_collection.update_one(
            {"_id": notebook_id},
            {"$inc": {"usage_stats.downloads": 1}}
        )

    async def _save_notebook_file(self, file_path: str, content: str):
        """Save notebook file (simplified - in production would use proper file storage)"""
        # This is a simplified implementation
        # In production, you'd save to cloud storage (S3, GCS, etc.)
        pass

    async def _load_notebook_file(self, file_path: str) -> str:
        """Load notebook file content"""
        # This is a simplified implementation
        # In production, you'd load from cloud storage
        # For now, return a sample notebook
        return json.dumps({
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        })