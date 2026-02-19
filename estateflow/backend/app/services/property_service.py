"""
Property service for EstateFlow.

Provides business logic for property CRUD operations, filtering, search,
and organization-scoped data access.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.property import (
    Property,
    PropertyCreate,
    PropertyUpdate,
    PropertyFilter,
    PropertyStatus,
    PropertyType,
)


logger = logging.getLogger(__name__)


class PropertyService:
    """
    Service for property operations.

    Provides CRUD operations, filtering, search, and organization scoping.
    All operations are scoped to the user's organization for multi-tenancy.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize property service.

        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database["properties"]

    async def create_property(
        self,
        property_data: PropertyCreate,
        organization_id: str
    ) -> Property:
        """
        Create a new property listing.

        Args:
            property_data: Property creation data
            organization_id: Organization ID (from auth context)

        Returns:
            Property: Created property with generated ID

        Raises:
            ValueError: If validation fails
        """
        # Reason: Ensure organization_id matches auth context for security
        if property_data.organization_id != organization_id:
            raise ValueError("Organization ID mismatch")

        now = datetime.utcnow()

        # Convert to dict and add timestamps
        property_dict = property_data.model_dump()
        property_dict["created_at"] = now
        property_dict["updated_at"] = now

        # Insert into database
        result = await self.collection.insert_one(property_dict)

        # Return created property with ID
        property_dict["id"] = str(result.inserted_id)
        property_dict["_id"] = result.inserted_id

        logger.info(
            f"Created property {result.inserted_id} "
            f"for organization {organization_id}"
        )

        return Property(**self._convert_object_id(property_dict))

    async def get_property(
        self,
        property_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[Property]:
        """
        Get property by ID.

        Args:
            property_id: Property ID (MongoDB ObjectId string)
            organization_id: Optional organization ID for access control.
                           If None, returns any property (public access).
                           If provided, only returns properties from that organization.

        Returns:
            Optional[Property]: Property if found and accessible, None otherwise

        Raises:
            ValueError: If property_id is invalid ObjectId format
        """
        try:
            object_id = ObjectId(property_id)
        except Exception:
            raise ValueError(f"Invalid property ID format: {property_id}")

        # Build query
        query = {"_id": object_id}

        # Reason: Filter by organization_id if provided for data isolation
        if organization_id:
            query["organization_id"] = organization_id

        doc = await self.collection.find_one(query)

        if not doc:
            return None

        return Property(**self._convert_object_id(doc))

    async def list_properties(
        self,
        filters: PropertyFilter,
        organization_id: Optional[str] = None
    ) -> Tuple[List[Property], int]:
        """
        List properties with filtering, sorting, and pagination.

        Args:
            filters: Filter criteria
            organization_id: Optional organization ID for access control.
                           If None, returns all properties (public access).
                           If provided, only returns properties from that organization.

        Returns:
            Tuple[List[Property], int]: (properties, total_count)
        """
        # Build MongoDB query
        query = self._build_filter_query(filters, organization_id)

        # Build sort criteria
        sort_field = filters.sort_by
        sort_direction = 1 if filters.sort_order == "asc" else -1

        # Map sort fields to database fields
        sort_mapping = {
            "price": "financial.price_usd",
            "created_at": "created_at",
            "sqft": "features.sqft",
        }
        db_sort_field = sort_mapping.get(sort_field, "created_at")

        # Get total count (for pagination)
        total_count = await self.collection.count_documents(query)

        # Get paginated results
        cursor = self.collection.find(query).sort(
            db_sort_field, sort_direction
        ).skip(filters.offset).limit(filters.limit)

        properties = []
        async for doc in cursor:
            properties.append(Property(**self._convert_object_id(doc)))

        logger.info(
            f"Listed {len(properties)} properties "
            f"(total: {total_count}, filters: {filters.model_dump()})"
        )

        return properties, total_count

    async def update_property(
        self,
        property_id: str,
        updates: PropertyUpdate,
        organization_id: str
    ) -> Optional[Property]:
        """
        Update property.

        Args:
            property_id: Property ID
            updates: Update data (partial updates supported)
            organization_id: Organization ID for access control

        Returns:
            Optional[Property]: Updated property or None if not found

        Raises:
            ValueError: If property_id is invalid
        """
        try:
            object_id = ObjectId(property_id)
        except Exception:
            raise ValueError(f"Invalid property ID format: {property_id}")

        # Get only fields that were actually set in the update
        update_dict = updates.model_dump(exclude_unset=True)

        if not update_dict:
            # No fields to update
            return await self.get_property(property_id, organization_id)

        # Add updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow()

        # Update document
        result = await self.collection.find_one_and_update(
            {
                "_id": object_id,
                "organization_id": organization_id
            },
            {"$set": update_dict},
            return_document=True  # Return updated document
        )

        if not result:
            return None

        logger.info(
            f"Updated property {property_id} "
            f"(fields: {list(update_dict.keys())})"
        )

        return Property(**self._convert_object_id(result))

    async def delete_property(
        self,
        property_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete property (soft delete by setting status to INACTIVE).

        Args:
            property_id: Property ID
            organization_id: Organization ID for access control

        Returns:
            bool: True if deleted, False if not found

        Raises:
            ValueError: If property_id is invalid
        """
        try:
            object_id = ObjectId(property_id)
        except Exception:
            raise ValueError(f"Invalid property ID format: {property_id}")

        # Reason: Soft delete instead of hard delete to preserve data
        result = await self.collection.update_one(
            {
                "_id": object_id,
                "organization_id": organization_id
            },
            {
                "$set": {
                    "status": PropertyStatus.INACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Deleted (soft) property {property_id}")
            return True

        return False

    async def search_properties(
        self,
        query: str,
        filters: PropertyFilter,
        organization_id: Optional[str] = None
    ) -> Tuple[List[Property], int]:
        """
        Search properties using full-text search.

        Searches in property name and description fields.

        Args:
            query: Search query string
            filters: Additional filters to apply
            organization_id: Optional organization ID for access control.
                           If None, searches all properties (public access).
                           If provided, only searches properties from that organization.

        Returns:
            Tuple[List[Property], int]: (matching properties, total count)
        """
        # Build base filter query
        base_query = self._build_filter_query(filters, organization_id)

        # Add text search
        # Reason: Use MongoDB text index for efficient full-text search
        base_query["$text"] = {"$search": query}

        # Get total count
        total_count = await self.collection.count_documents(base_query)

        # Get results with text score sorting
        cursor = self.collection.find(
            base_query,
            {"score": {"$meta": "textScore"}}
        ).sort(
            [("score", {"$meta": "textScore"})]  # Sort by relevance
        ).skip(filters.offset).limit(filters.limit)

        properties = []
        async for doc in cursor:
            properties.append(Property(**self._convert_object_id(doc)))

        logger.info(
            f"Search '{query}' returned {len(properties)} results "
            f"(total: {total_count})"
        )

        return properties, total_count

    def _build_filter_query(
        self,
        filters: PropertyFilter,
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Build MongoDB query from filter criteria.

        Args:
            filters: Filter parameters
            organization_id: Optional organization ID.
                           If None, no organization filter is applied (public access).
                           If provided, only properties from that organization are returned.

        Returns:
            dict: MongoDB query document
        """
        query = {}

        # Add organization filter if provided
        if organization_id:
            query["organization_id"] = organization_id

        # Property type filter
        if filters.property_type:
            query["property_type"] = {
                "$in": [pt.value for pt in filters.property_type]
            }

        # Status filter
        if filters.status:
            query["status"] = {
                "$in": [s.value for s in filters.status]
            }

        # Price range filter
        if filters.min_price is not None or filters.max_price is not None:
            price_query = {}
            if filters.min_price is not None:
                price_query["$gte"] = filters.min_price
            if filters.max_price is not None:
                price_query["$lte"] = filters.max_price
            if price_query:
                query["financial.price_usd"] = price_query

        # Bedroom filter
        if filters.min_bedrooms is not None or filters.max_bedrooms is not None:
            bedroom_query = {}
            if filters.min_bedrooms is not None:
                bedroom_query["$gte"] = filters.min_bedrooms
            if filters.max_bedrooms is not None:
                bedroom_query["$lte"] = filters.max_bedrooms
            if bedroom_query:
                query["features.bedrooms"] = bedroom_query

        # Bathroom filter
        if filters.min_bathrooms is not None or filters.max_bathrooms is not None:
            bathroom_query = {}
            if filters.min_bathrooms is not None:
                bathroom_query["$gte"] = filters.min_bathrooms
            if filters.max_bathrooms is not None:
                bathroom_query["$lte"] = filters.max_bathrooms
            if bathroom_query:
                query["features.bathrooms"] = bathroom_query

        # City filter (case-insensitive)
        if filters.city:
            query["location.city"] = {"$regex": filters.city, "$options": "i"}

        # Neighborhood filter (case-insensitive)
        if filters.neighborhood:
            query["location.neighborhood"] = {
                "$regex": filters.neighborhood,
                "$options": "i"
            }

        # General location search (searches across city, neighborhood, address, state, and country)
        if filters.location:
            query["$or"] = [
                {"location.city": {"$regex": filters.location, "$options": "i"}},
                {"location.neighborhood": {"$regex": filters.location, "$options": "i"}},
                {"location.address": {"$regex": filters.location, "$options": "i"}},
                {"location.state": {"$regex": filters.location, "$options": "i"}},
                {"location.country": {"$regex": filters.location, "$options": "i"}},
            ]

        # Pet policy filter
        if filters.pet_policy:
            query["features.pet_policy"] = {
                "$in": [pp.value for pp in filters.pet_policy]
            }

        # Boolean feature filters
        if filters.has_pool is not None:
            query["features.pool"] = filters.has_pool

        if filters.has_garden is not None:
            query["features.garden"] = filters.has_garden

        if filters.furnished is not None:
            query["features.furnished"] = filters.furnished

        return query

    def _convert_object_id(self, doc: Dict) -> Dict:
        """
        Convert MongoDB ObjectId to string for Pydantic models.

        Args:
            doc: MongoDB document

        Returns:
            dict: Document with _id converted to string id field
        """
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            # Remove _id to avoid Pydantic validation issues
            # Keep it for internal use but Pydantic model uses 'id'

        return doc

    async def get_property_count(self, organization_id: str) -> Dict[str, int]:
        """
        Get property counts by status.

        Args:
            organization_id: Organization ID

        Returns:
            dict: Status counts (active, pending, sold, rented, inactive, total)
        """
        pipeline = [
            {"$match": {"organization_id": organization_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]

        counts = {
            "active": 0,
            "pending": 0,
            "sold": 0,
            "rented": 0,
            "inactive": 0,
            "total": 0
        }

        async for doc in self.collection.aggregate(pipeline):
            status = doc["_id"]
            count = doc["count"]
            counts[status] = count
            counts["total"] += count

        return counts
