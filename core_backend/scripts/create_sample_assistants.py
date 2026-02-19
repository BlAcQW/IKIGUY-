#!/usr/bin/env python3
"""Create sample assistants for testing."""

import sys
import os
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Assistant
from backend.services.assistant_service import assistant_service

def create_sample_assistants():
    """Create sample assistants for testing."""
    
    sample_assistants = [
        {
            "id": str(uuid.uuid4()),
            "name": "Customer Support Agent",
            "description": "A friendly customer support assistant that can help with product inquiries and support tickets",
            "user_id": "user-123",
            "template_id": "template-1",
            "status": "active",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "first_message_mode": "assistant_first",
            "first_message": "Hello! I'm your customer support assistant. How can I help you today?",
            "system_prompt": "You are a helpful customer support agent. Be friendly, professional, and solution-oriented.",
            "tts_provider": "openai",
            "tts_voice": "alloy",
            "language": "en",
            "country": "US",
            "stt_provider": "openai",
            "stt_model": "whisper-1",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Twi Language Assistant",
            "description": "An AI assistant that speaks fluent Twi for Ghanaian users",
            "user_id": "user-123",
            "template_id": "template-2",
            "status": "active",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "first_message_mode": "assistant_first",
            "first_message": "Akwaaba! Me ho yɛ me. Ɛdeɛn na me betumi ayɛ ama wo?",
            "system_prompt": "You are a helpful assistant that speaks Twi (Akan). Always respond in Twi unless the user specifically asks you to use English.",
            "tts_provider": "meta_mms",
            "tts_voice": "mms-tts-aka",
            "language": "twi",
            "country": "Ghana",
            "stt_provider": "meta_mms",
            "stt_model": "mms-1b-all",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sales Assistant",
            "description": "An AI sales assistant to help qualify leads and answer product questions",
            "user_id": "user-123",
            "template_id": "template-3",
            "status": "draft",
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "first_message_mode": "assistant_first",
            "first_message": "Hi there! I'm here to help you learn about our products and services. What brings you here today?",
            "system_prompt": "You are a professional sales assistant. Help qualify leads, answer product questions, and guide customers through the sales process.",
            "tts_provider": "elevenlabs",
            "tts_voice": "rachel",
            "language": "en",
            "country": "US",
            "stt_provider": "openai",
            "stt_model": "whisper-1",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Yoruba Voice Assistant",
            "description": "A voice assistant for Nigerian users speaking Yoruba",
            "user_id": "user-123",
            "template_id": "template-4",
            "status": "active",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "first_message_mode": "assistant_first",
            "first_message": "Ẹ káàbọ̀! Kí ni mo lè ṣe fún yín?",
            "system_prompt": "You are a helpful assistant that speaks Yoruba. Be culturally appropriate and respectful.",
            "tts_provider": "meta_mms",
            "tts_voice": "mms-tts-yor",
            "language": "yoruba",
            "country": "Nigeria",
            "stt_provider": "meta_mms",
            "stt_model": "mms-1b-all",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Technical Support Bot",
            "description": "An AI assistant for technical support and troubleshooting",
            "user_id": "user-123",
            "template_id": "template-5",
            "status": "published",
            "llm_provider": "gemini",
            "llm_model": "gemini-2.5-flash",
            "first_message_mode": "assistant_first",
            "first_message": "Hello! I'm here to help with any technical issues you're experiencing. What seems to be the problem?",
            "system_prompt": "You are a technical support specialist. Help users troubleshoot issues, provide clear instructions, and escalate when necessary.",
            "tts_provider": "openai",
            "tts_voice": "echo",
            "language": "en",
            "country": "US",
            "stt_provider": "openai",
            "stt_model": "whisper-1",
        }
    ]
    
    # Clear existing assistants
    print("Clearing existing assistants...")
    assistant_service.clear_all()
    
    # Create sample assistants
    created_count = 0
    for assistant_data in sample_assistants:
        try:
            assistant = Assistant(**assistant_data)
            assistant.created_at = datetime.utcnow()
            assistant.updated_at = datetime.utcnow()
            
            created_assistant = assistant_service.create_assistant(assistant)
            print(f"Created assistant: {created_assistant.name} (ID: {created_assistant.id})")
            created_count += 1
        except Exception as e:
            print(f"Failed to create assistant {assistant_data['name']}: {e}")
    
    print(f"\nSuccessfully created {created_count} sample assistants!")
    
    # Verify by fetching all assistants
    all_assistants = assistant_service.get_all_assistants()
    print(f"Total assistants in database: {len(all_assistants)}")

if __name__ == "__main__":
    create_sample_assistants()