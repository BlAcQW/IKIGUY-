"""Assistant service for managing assistants in MongoDB."""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from ..models import Assistant
from .knowledge_base_service import knowledge_base_service
from .voice_parameter_optimizer import voice_parameter_optimizer


class MongoDBAssistantService:
    """MongoDB-based assistant service."""

    def __init__(self):
        """Initialize the assistant service."""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB."""
        try:
            # Use the same MongoDB connection as other services
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            database_name = os.getenv("MONGO_CORE_DATABASE", "kasaai_core")
            
            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.collection = self.db["assistants"]
            
            # Create indexes
            try:
                self.collection.create_index("user_id")
                self.collection.create_index("status")
                self.collection.create_index("name")
                self.collection.create_index([("user_id", 1), ("name", 1)], unique=True)
            except Exception as e:
                # Index might already exist
                pass
                
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def apply_optimized_voice_parameters(
        self,
        assistant_dict: Dict[str, Any],
        use_case: str = "conversational"
    ) -> Dict[str, Any]:
        """
        Apply optimized voice parameters to an assistant configuration.

        Args:
            assistant_dict: Assistant configuration dictionary
            use_case: Use case category (customer_service, sales, conversational, etc.)

        Returns:
            Updated assistant dictionary with optimized parameters
        """
        tts_provider = assistant_dict.get("tts_provider", "openai")
        language = assistant_dict.get("language", "en")

        # Get optimized parameters
        optimized_params = voice_parameter_optimizer.get_optimized_parameters(
            tts_provider=tts_provider,
            use_case=use_case,
            language=language
        )

        # Update assistant config with optimized parameters
        assistant_dict.update(optimized_params)

        return assistant_dict

    def get_default_twi_config(self) -> Dict[str, Any]:
        """Get default configuration for Twi voice agent with optimized parameters."""
        # Get optimized voice parameters for Meta MMS + Twi
        voice_params = voice_parameter_optimizer.get_optimized_parameters(
            tts_provider="meta_mms",
            use_case="conversational",
            language="twi"
        )

        return {
            # LLM Configuration - OpenAI GPT-4 Mini
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",

            # Voice Configuration - Meta MMS for Twi
            "tts_provider": "meta_mms",
            "tts_model": "meta_mms",  # Default to multilingual Meta MMS
            "tts_voice": "mms-tts-aka",  # Akan (Twi) voice

            # Transcriber Configuration - Meta MMS for Twi
            "stt_provider": "meta_mms",
            "stt_model": "mms-1b-all",

            # Language Configuration
            "language": "twi",
            "country": "Ghana",

            # Voice Parameters - OPTIMIZED for natural speech and low latency
            "background_sound": "default",
            "background_sound_url": "",
            "input_min_characters": 30,
            "punctuation_boundaries": "",
            **voice_params,  # Apply optimized parameters

            # Transcriber Parameters
            "background_denoising": False,
            "confidence_threshold": 0.4,
            "use_numerals": False,

            # System Prompt for Twi
            "system_prompt": "You are a helpful assistant that speaks Twi (Akan). Always respond in Twi unless the user specifically asks you to use English. Be polite, respectful, and culturally appropriate for Ghanaian users.",

            # First Message
            "first_message_mode": "assistant_first",
            "first_message": "Akwaaba! Me ho yɛ me. Ɛdeɛn na me betumi ayɛ ama wo?",
        }

    def create_assistant(self, assistant: Assistant) -> Assistant:
        """Create a new assistant."""
        try:
            # Set timestamps
            assistant.created_at = datetime.utcnow()
            assistant.updated_at = datetime.utcnow()
            
            # If no configuration is provided, use default Twi config
            if not assistant.llm_provider:
                default_config = self.get_default_twi_config()
                for key, value in default_config.items():
                    if hasattr(assistant, key) and not getattr(assistant, key):
                        setattr(assistant, key, value)
            
            # Convert to dict and insert
            assistant_dict = assistant.model_dump()
            result = self.collection.insert_one(assistant_dict)
            
            # Set the ID from the inserted document
            assistant.id = str(result.inserted_id)
            return assistant
            
        except Exception as e:
            print(f"Failed to create assistant: {e}")
            raise

    def get_assistant(self, assistant_id: str) -> Optional[Assistant]:
        """Get an assistant by ID."""
        try:
            assistant_dict = self.collection.find_one({"id": assistant_id})
            if assistant_dict:
                return Assistant(**assistant_dict)
            return None
        except Exception as e:
            print(f"Failed to get assistant: {e}")
            return None

    def get_assistants_by_user(self, user_id: str) -> List[Assistant]:
        """Get all assistants for a user."""
        try:
            assistants = []
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
            for assistant_dict in cursor:
                assistants.append(Assistant(**assistant_dict))
            return assistants
        except Exception as e:
            print(f"Failed to get assistants for user: {e}")
            return []

    def get_all_assistants(self) -> List[Assistant]:
        """Get all assistants from the database."""
        try:
            assistants = []
            cursor = self.collection.find({}).sort("created_at", -1)
            for assistant_dict in cursor:
                assistants.append(Assistant(**assistant_dict))
            return assistants
        except Exception as e:
            print(f"Failed to get all assistants: {e}")
            return []

    def update_assistant(self, assistant_id: str, updates: Dict[str, Any]) -> Optional[Assistant]:
        """Update an assistant."""
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"id": assistant_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return self.get_assistant(assistant_id)
            return None
            
        except Exception as e:
            print(f"Failed to update assistant: {e}")
            return None

    def publish_assistant(self, assistant_id: str, configuration: Dict[str, Any]) -> Optional[Assistant]:
        """Publish an assistant with updated configuration."""
        try:
            # Add status and configuration updates
            updates = {
                "status": "published",
                "updated_at": datetime.utcnow(),
                **configuration
            }
            
            return self.update_assistant(assistant_id, updates)
            
        except Exception as e:
            print(f"Failed to publish assistant: {e}")
            return None

    def delete_assistant(self, assistant_id: str) -> bool:
        """Delete an assistant."""
        try:
            result = self.collection.delete_one({"id": assistant_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Failed to delete assistant: {e}")
            return False
    
    def activate_assistant(self, assistant_id: str) -> bool:
        """Activate an assistant."""
        try:
            result = self.collection.update_one(
                {"id": assistant_id},
                {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Failed to activate assistant: {e}")
            return False
    
    def deactivate_assistant(self, assistant_id: str) -> bool:
        """Deactivate an assistant."""
        try:
            result = self.collection.update_one(
                {"id": assistant_id},
                {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Failed to deactivate assistant: {e}")
            return False

    def get_published_assistants(self, user_id: str) -> List[Assistant]:
        """Get all published assistants for a user."""
        try:
            assistants = []
            cursor = self.collection.find({
                "user_id": user_id,
                "status": "published"
            }).sort("updated_at", -1)
            
            for assistant_dict in cursor:
                assistants.append(Assistant(**assistant_dict))
            return assistants
            
        except Exception as e:
            print(f"Failed to get published assistants: {e}")
            return []

    async def add_knowledge_base_file(self, assistant_id: str, file_content: str, file_name: str, user_id: str) -> bool:
        """Add a knowledge base file to an assistant."""
        try:
            # Ingest file into Supabase knowledge base
            source = await knowledge_base_service.ingest_file(
                tenant_id=user_id,
                file_content=file_content,
                file_name=file_name
            )
            
            # Update assistant with knowledge base file ID
            assistant = self.get_assistant(assistant_id)
            if assistant:
                knowledge_base_files = assistant.knowledge_base_files.copy()
                knowledge_base_files.append(source.id)
                
                self.update_assistant(assistant_id, {
                    "knowledge_base_files": knowledge_base_files
                })
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to add knowledge base file: {e}")
            return False

    async def search_knowledge_base(self, assistant_id: str, query: str, user_id: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for an assistant."""
        try:
            assistant = self.get_assistant(assistant_id)
            if not assistant or not assistant.knowledge_base_files:
                return []
            
            # Search in Supabase knowledge base
            results = await knowledge_base_service.search(
                tenant_id=user_id,
                query=query,
                top_k=5
            )
            
            return [result.model_dump() for result in results]
            
        except Exception as e:
            print(f"Failed to search knowledge base: {e}")
            return []

    def clear_all(self):
        """Clear all assistants (for testing)."""
        try:
            self.collection.delete_many({})
        except Exception as e:
            print(f"Failed to clear assistants: {e}")


# Global instance
assistant_service = MongoDBAssistantService()
