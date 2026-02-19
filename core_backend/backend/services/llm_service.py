"""LLM Provider and Model management service using MongoDB."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId

from ..models import LLMProvider, LLMModel


class MongoDBLLMService:
    """MongoDB-based service for managing LLM providers and models."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.providers_collection: Optional[Collection] = None
        self.models_collection: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            # Get MongoDB URL from environment
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")
            
            # Connect to MongoDB
            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            
            # Get collections
            self.providers_collection = self.db["llm_providers"]
            self.models_collection = self.db["llm_models"]
            
            # Create indexes for better performance
            self.providers_collection.create_index("name", unique=True)
            self.models_collection.create_index("name")
            self.models_collection.create_index("provider_id")
            self.models_collection.create_index("is_default")
            
            print(f"Connected to MongoDB: {database_name}")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            # Fallback to in-memory storage
            self._use_in_memory_fallback()

    def _use_in_memory_fallback(self):
        """Fallback to in-memory storage if MongoDB is not available."""
        print("Using in-memory storage as fallback")
        self.providers: Dict[str, LLMProvider] = {}
        self.models: Dict[str, LLMModel] = {}
        self.client = None
        self.db = None
        self.providers_collection = None
        self.models_collection = None

    async def create_provider(self, provider: LLMProvider) -> LLMProvider:
        """Create a new LLM provider.
        
        Args:
            provider: LLM provider data
            
        Returns:
            Created provider with ID
        """
        if self.client is None:
            # In-memory fallback
            provider_dict = provider.model_dump()
            provider_dict["id"] = str(ObjectId())
            provider_dict["created_at"] = datetime.utcnow()
            provider_dict["updated_at"] = datetime.utcnow()
            provider_obj = LLMProvider(**provider_dict)
            self.providers[provider_obj.id] = provider_obj
            return provider_obj
        
        # MongoDB
        provider_dict = provider.model_dump()
        provider_dict["created_at"] = datetime.utcnow()
        provider_dict["updated_at"] = datetime.utcnow()
        
        result = self.providers_collection.insert_one(provider_dict)
        provider_dict["id"] = str(result.inserted_id)
        
        return LLMProvider(**provider_dict)

    async def get_providers(self, active_only: bool = True) -> List[LLMProvider]:
        """Get all LLM providers.
        
        Args:
            active_only: Whether to return only active providers
            
        Returns:
            List of LLM providers
        """
        if self.client is None:
            # In-memory fallback
            providers = list(self.providers.values())
            if active_only:
                providers = [p for p in providers if p.is_active]
            return providers
        
        # MongoDB
        query = {"is_active": True} if active_only else {}
        cursor = self.providers_collection.find(query)
        
        providers = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            providers.append(LLMProvider(**doc))
        
        return providers

    async def get_provider_by_name(self, name: str) -> Optional[LLMProvider]:
        """Get LLM provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            LLM provider or None if not found
        """
        if self.client is None:
            # In-memory fallback
            for provider in self.providers.values():
                if provider.name == name:
                    return provider
            return None
        
        # MongoDB
        provider_dict = self.providers_collection.find_one({"name": name})
        if provider_dict:
            provider_dict["id"] = str(provider_dict["_id"])
            return LLMProvider(**provider_dict)
        return None
    
    async def get_model_by_name(self, name: str) -> Optional[LLMModel]:
        """Get LLM model by name.
        
        Args:
            name: Model name
            
        Returns:
            LLM model or None if not found
        """
        if self.client is None:
            # In-memory fallback
            for model in self.models.values():
                if model.name == name:
                    return model
            return None
        
        # MongoDB
        model_dict = self.models_collection.find_one({"name": name})
        if model_dict:
            model_dict["id"] = str(model_dict["_id"])
            return LLMModel(**model_dict)
        return None

    async def get_provider_by_id(self, provider_id: str) -> Optional[LLMProvider]:
        """Get provider by ID.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider if found, None otherwise
        """
        if self.client is None:
            # In-memory fallback
            return self.providers.get(provider_id)
        
        # MongoDB
        try:
            doc = self.providers_collection.find_one({"_id": ObjectId(provider_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return LLMProvider(**doc)
        except Exception:
            pass
        
        return None

    async def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> Optional[LLMProvider]:
        """Update provider.
        
        Args:
            provider_id: Provider ID
            updates: Fields to update
            
        Returns:
            Updated provider if found, None otherwise
        """
        if self.client is None:
            # In-memory fallback
            if provider_id in self.providers:
                provider = self.providers[provider_id]
                provider_dict = provider.model_dump()
                provider_dict.update(updates)
                provider_dict["updated_at"] = datetime.utcnow()
                updated_provider = LLMProvider(**provider_dict)
                self.providers[provider_id] = updated_provider
                return updated_provider
            return None
        
        # MongoDB
        try:
            updates["updated_at"] = datetime.utcnow()
            result = self.providers_collection.update_one(
                {"_id": ObjectId(provider_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return await self.get_provider_by_id(provider_id)
        except Exception:
            pass
        
        return None

    async def delete_provider(self, provider_id: str) -> bool:
        """Delete provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            True if deleted, False otherwise
        """
        if self.client is None:
            # In-memory fallback
            if provider_id in self.providers:
                del self.providers[provider_id]
                return True
            return False
        
        # MongoDB
        try:
            result = self.providers_collection.delete_one({"_id": ObjectId(provider_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def create_model(self, model: LLMModel) -> LLMModel:
        """Create a new LLM model.
        
        Args:
            model: LLM model data
            
        Returns:
            Created model with ID
        """
        if self.client is None:
            # In-memory fallback
            model_dict = model.model_dump()
            model_dict["id"] = str(ObjectId())
            model_dict["created_at"] = datetime.utcnow()
            model_dict["updated_at"] = datetime.utcnow()
            model_obj = LLMModel(**model_dict)
            self.models[model_obj.id] = model_obj
            return model_obj
        
        # MongoDB
        model_dict = model.model_dump()
        model_dict["created_at"] = datetime.utcnow()
        model_dict["updated_at"] = datetime.utcnow()
        
        result = self.models_collection.insert_one(model_dict)
        model_dict["id"] = str(result.inserted_id)
        
        return LLMModel(**model_dict)

    async def get_models(self, provider_id: Optional[str] = None, active_only: bool = True) -> List[LLMModel]:
        """Get LLM models.
        
        Args:
            provider_id: Optional provider ID to filter by
            active_only: Whether to return only active models
            
        Returns:
            List of LLM models
        """
        if self.client is None:
            # In-memory fallback
            models = list(self.models.values())
            if provider_id:
                models = [m for m in models if m.provider_id == provider_id]
            if active_only:
                models = [m for m in models if m.is_active]
            return models
        
        # MongoDB
        query = {}
        if provider_id:
            query["provider_id"] = provider_id
        if active_only:
            query["is_active"] = True
        
        cursor = self.models_collection.find(query)
        
        models = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            models.append(LLMModel(**doc))
        
        return models

    async def get_model_by_id(self, model_id: str) -> Optional[LLMModel]:
        """Get model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model if found, None otherwise
        """
        if self.client is None:
            # In-memory fallback
            return self.models.get(model_id)
        
        # MongoDB
        try:
            doc = self.models_collection.find_one({"_id": ObjectId(model_id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return LLMModel(**doc)
        except Exception:
            pass
        
        return None

    async def update_model(self, model_id: str, updates: Dict[str, Any]) -> Optional[LLMModel]:
        """Update model.
        
        Args:
            model_id: Model ID
            updates: Fields to update
            
        Returns:
            Updated model if found, None otherwise
        """
        if self.client is None:
            # In-memory fallback
            if model_id in self.models:
                model = self.models[model_id]
                model_dict = model.model_dump()
                model_dict.update(updates)
                model_dict["updated_at"] = datetime.utcnow()
                updated_model = LLMModel(**model_dict)
                self.models[model_id] = updated_model
                return updated_model
            return None
        
        # MongoDB
        try:
            updates["updated_at"] = datetime.utcnow()
            result = self.models_collection.update_one(
                {"_id": ObjectId(model_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return await self.get_model_by_id(model_id)
        except Exception:
            pass
        
        return None

    async def delete_model(self, model_id: str) -> bool:
        """Delete model.
        
        Args:
            model_id: Model ID
            
        Returns:
            True if deleted, False otherwise
        """
        if self.client is None:
            # In-memory fallback
            if model_id in self.models:
                del self.models[model_id]
                return True
            return False
        
        # MongoDB
        try:
            result = self.models_collection.delete_one({"_id": ObjectId(model_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def get_provider_models(self, provider_id: str) -> List[LLMModel]:
        """Get all models for a specific provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List of models for the provider
        """
        return await self.get_models(provider_id=provider_id)

    async def get_default_model(self) -> Optional[LLMModel]:
        """Get the default LLM model.
        
        Returns:
            Default model if found, None otherwise
        """
        if self.client is None:
            # In-memory fallback
            for model in self.models.values():
                if model.is_default:
                    return model
            return None
        
        # MongoDB
        try:
            doc = self.models_collection.find_one({"is_default": True})
            if doc:
                doc["id"] = str(doc.pop("_id"))
                return LLMModel(**doc)
        except Exception:
            pass
        
        return None

    async def set_default_model(self, model_id: str) -> bool:
        """Set a model as the default.
        
        Args:
            model_id: Model ID to set as default
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            # In-memory fallback
            # First, unset all defaults
            for model in self.models.values():
                if model.is_default:
                    model_dict = model.model_dump()
                    model_dict["is_default"] = False
                    model_dict["updated_at"] = datetime.utcnow()
                    self.models[model.id] = LLMModel(**model_dict)
            
            # Set the new default
            if model_id in self.models:
                model = self.models[model_id]
                model_dict = model.model_dump()
                model_dict["is_default"] = True
                model_dict["updated_at"] = datetime.utcnow()
                self.models[model_id] = LLMModel(**model_dict)
                return True
            return False
        
        # MongoDB
        try:
            # First, unset all defaults
            self.models_collection.update_many(
                {"is_default": True},
                {"$set": {"is_default": False, "updated_at": datetime.utcnow()}}
            )
            
            # Set the new default
            result = self.models_collection.update_one(
                {"_id": ObjectId(model_id)},
                {"$set": {"is_default": True, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
        except Exception:
            return False

    def clear_all(self):
        """Clear all data (for testing purposes)."""
        if self.client is None:
            # In-memory fallback
            self.providers.clear()
            self.models.clear()
        else:
            # MongoDB
            self.providers_collection.delete_many({})
            self.models_collection.delete_many({})

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()


# Global instance
llm_service = MongoDBLLMService()
