"""Voice service for managing voice providers and voices."""

from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import os
from datetime import datetime

from ..models import VoiceProvider, Voice


class MongoDBVoiceService:
    """MongoDB-based voice service for managing voice providers and voices."""
    
    def __init__(self):
        """Initialize the voice service with MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.providers_collection: Optional[Collection] = None
        self.voices_collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB."""
        try:
            # Get MongoDB URL from environment (same as LLM service)
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")
            
            # Connect to MongoDB
            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            
            # Get collections
            self.providers_collection = self.db["voice_providers"]
            self.voices_collection = self.db["voices"]
            
            # Create indexes for better performance
            try:
                self.providers_collection.create_index("name", unique=True)
                self.voices_collection.create_index("provider_id")
                self.voices_collection.create_index("language")
                self.voices_collection.create_index("voice_type")
            except Exception as index_error:
                print(f"Warning: Could not create indexes (may already exist): {index_error}")
            
            print(f"Connected to MongoDB for voice service: {database_name}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
    
    async def create_provider(self, provider: VoiceProvider) -> VoiceProvider:
        """Create a new voice provider.
        
        Args:
            provider: Voice provider data
            
        Returns:
            Created voice provider
        """
        try:
            provider_dict = provider.model_dump()
            provider_dict["created_at"] = datetime.utcnow()
            provider_dict["updated_at"] = datetime.utcnow()
            
            result = self.providers_collection.insert_one(provider_dict)
            provider_dict["id"] = str(result.inserted_id)
            
            return VoiceProvider(**provider_dict)
        except Exception as e:
            print(f"Error creating voice provider: {e}")
            raise
    
    async def create_voice(self, voice: Voice) -> Voice:
        """Create a new voice.
        
        Args:
            voice: Voice data
            
        Returns:
            Created voice
        """
        try:
            voice_dict = voice.model_dump()
            voice_dict["created_at"] = datetime.utcnow()
            voice_dict["updated_at"] = datetime.utcnow()
            
            result = self.voices_collection.insert_one(voice_dict)
            voice_dict["id"] = str(result.inserted_id)
            
            return Voice(**voice_dict)
        except Exception as e:
            print(f"Error creating voice: {e}")
            raise
    
    async def get_providers(self, active_only: bool = True, provider_type: Optional[str] = None) -> List[VoiceProvider]:
        """Get all voice providers.
        
        Args:
            active_only: Whether to return only active providers
            provider_type: Filter by provider type (STT, TTS, or both)
            
        Returns:
            List of voice providers
        """
        try:
            filter_query = {}
            if active_only:
                filter_query["is_active"] = True
            if provider_type:
                filter_query["provider_type"] = provider_type
            
            providers = []
            cursor = self.providers_collection.find(filter_query)
            
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                providers.append(VoiceProvider(**doc))
            
            return providers
        except Exception as e:
            print(f"Error getting voice providers: {e}")
            raise
    
    async def get_provider_by_name(self, name: str) -> Optional[VoiceProvider]:
        """Get voice provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Voice provider or None if not found
        """
        try:
            provider_dict = self.providers_collection.find_one({"name": name})
            if provider_dict:
                provider_dict["id"] = str(provider_dict["_id"])
                return VoiceProvider(**provider_dict)
            return None
        except Exception as e:
            print(f"Error getting voice provider by name: {e}")
            return None
    
    async def get_voice_by_name(self, name: str) -> Optional[Voice]:
        """Get voice by name.
        
        Args:
            name: Voice name
            
        Returns:
            Voice or None if not found
        """
        try:
            voice_dict = self.voices_collection.find_one({"name": name})
            if voice_dict:
                voice_dict["id"] = str(voice_dict["_id"])
                return Voice(**voice_dict)
            return None
        except Exception as e:
            print(f"Error getting voice by name: {e}")
            return None
    
    async def get_voices(self, 
                        provider_id: Optional[str] = None,
                        language: Optional[str] = None,
                        voice_type: Optional[str] = None,
                        active_only: bool = True) -> List[Voice]:
        """Get all voices with optional filtering.
        
        Args:
            provider_id: Filter by provider ID
            language: Filter by language code
            voice_type: Filter by voice type
            active_only: Whether to return only active voices
            
        Returns:
            List of voices
        """
        try:
            filter_query = {}
            if provider_id:
                filter_query["provider_id"] = provider_id
            if language:
                filter_query["language"] = language
            if voice_type:
                filter_query["voice_type"] = voice_type
            if active_only:
                filter_query["is_active"] = True
            
            voices = []
            cursor = self.voices_collection.find(filter_query)
            
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                voices.append(Voice(**doc))
            
            return voices
        except Exception as e:
            print(f"Error getting voices: {e}")
            raise
    
    async def get_default_provider(self, provider_type: str) -> Optional[VoiceProvider]:
        """Get the default provider for a specific type.
        
        Args:
            provider_type: Provider type (STT, TTS, or both)
            
        Returns:
            Default provider or None
        """
        try:
            doc = self.providers_collection.find_one({
                "provider_type": provider_type,
                "is_default": True,
                "is_active": True
            })
            
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return VoiceProvider(**doc)
            
            return None
        except Exception as e:
            print(f"Error getting default provider: {e}")
            raise
    
    async def get_default_voice(self, provider_id: str, language: str) -> Optional[Voice]:
        """Get the default voice for a provider and language.
        
        Args:
            provider_id: Provider ID
            language: Language code
            
        Returns:
            Default voice or None
        """
        try:
            doc = self.voices_collection.find_one({
                "provider_id": provider_id,
                "language": language,
                "is_default": True,
                "is_active": True
            })
            
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return Voice(**doc)
            
            return None
        except Exception as e:
            print(f"Error getting default voice: {e}")
            raise
    
    async def clear_all(self):
        """Clear all voice providers and voices from the database."""
        try:
            self.providers_collection.delete_many({})
            self.voices_collection.delete_many({})
        except Exception as e:
            print(f"Error clearing voice data: {e}")
            raise


# Global instance
voice_service = MongoDBVoiceService()
