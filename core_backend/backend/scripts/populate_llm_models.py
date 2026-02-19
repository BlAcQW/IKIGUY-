#!/usr/bin/env python3
"""Script to populate MongoDB with latest LLM providers and models."""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to the path
backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

from services.llm_service import llm_service
from ..models import LLMProvider, LLMModel


async def populate_llm_data():
    """Populate MongoDB with latest LLM providers and models."""
    
    print("Starting LLM data population...")
    
    # Clear existing data
    print("Clearing existing data...")
    llm_service.clear_all()
    
    # Create providers
    providers_data = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "Leading AI research company known for GPT models",
            "website": "https://openai.com",
            "api_base_url": "https://api.openai.com/v1",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "audio"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 128000,
            "is_active": True
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "AI safety company focused on reliable and interpretable AI systems",
            "website": "https://anthropic.com",
            "api_base_url": "https://api.anthropic.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "tool_use"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 200000,
            "is_active": True
        },
        {
            "name": "google",
            "display_name": "Google",
            "description": "Google's AI division offering Gemini models",
            "website": "https://ai.google.dev",
            "api_base_url": "https://generativelanguage.googleapis.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling", "vision", "audio"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "max_context_length": 1000000,
            "is_active": True
        },
        {
            "name": "mistral",
            "display_name": "Mistral AI",
            "description": "European AI company focused on open and efficient language models",
            "website": "https://mistral.ai",
            "api_base_url": "https://api.mistral.ai/v1",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "max_context_length": 32768,
            "is_active": True
        },
        {
            "name": "cohere",
            "display_name": "Cohere",
            "description": "AI platform for text generation and understanding",
            "website": "https://cohere.ai",
            "api_base_url": "https://api.cohere.ai/v1",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "embedding", "rerank"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "max_context_length": 100000,
            "is_active": True
        },
        {
            "name": "meta",
            "display_name": "Meta",
            "description": "Meta's open source AI models including LLaMA",
            "website": "https://ai.meta.com",
            "api_base_url": "https://api.meta.ai",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "max_context_length": 4096,
            "is_active": True
        }
    ]
    
    # Create providers
    created_providers = {}
    for provider_data in providers_data:
        provider = LLMProvider(**provider_data)
        created_provider = await llm_service.create_provider(provider)
        created_providers[provider_data["name"]] = created_provider.id
        print(f"Created provider: {provider.display_name}")
    
    # Create models for each provider
    models_data = [
        # OpenAI Models
        {
            "provider_id": created_providers["openai"],
            "name": "gpt-4o",
            "display_name": "GPT-4o",
            "description": "Latest GPT-4 model with multimodal capabilities",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.0025,
            "output_cost_per_1k_tokens": 0.01,
            "capabilities": ["text", "vision", "audio", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "fast", "accuracy": "high"},
            "is_active": True,
            "is_default": True
        },
        {
            "provider_id": created_providers["openai"],
            "name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "description": "Faster and more cost-effective version of GPT-4o",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.00015,
            "output_cost_per_1k_tokens": 0.0006,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["openai"],
            "name": "gpt-3.5-turbo",
            "display_name": "GPT-3.5 Turbo",
            "description": "Fast and efficient model for most tasks",
            "model_type": "chat",
            "context_length": 16385,
            "input_cost_per_1k_tokens": 0.0005,
            "output_cost_per_1k_tokens": 0.0015,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        
        # Anthropic Models
        {
            "provider_id": created_providers["anthropic"],
            "name": "claude-3-5-sonnet",
            "display_name": "Claude 3.5 Sonnet",
            "description": "Latest Claude model with enhanced reasoning and coding capabilities",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "capabilities": ["text", "vision", "function_calling", "tool_use"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "fast", "accuracy": "very_high"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["anthropic"],
            "name": "claude-3-opus",
            "display_name": "Claude 3 Opus",
            "description": "Most capable Claude model for complex tasks",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.015,
            "output_cost_per_1k_tokens": 0.075,
            "capabilities": ["text", "vision", "function_calling", "tool_use"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "medium", "accuracy": "highest"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["anthropic"],
            "name": "claude-3-haiku",
            "display_name": "Claude 3 Haiku",
            "description": "Fastest Claude model for simple tasks",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.00025,
            "output_cost_per_1k_tokens": 0.00125,
            "capabilities": ["text", "vision", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        
        # Google Models
        {
            "provider_id": created_providers["google"],
            "name": "gemini-1.5-pro",
            "display_name": "Gemini 1.5 Pro",
            "description": "Advanced multimodal model with long context",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.0035,
            "output_cost_per_1k_tokens": 0.0105,
            "capabilities": ["text", "vision", "audio", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "medium", "accuracy": "high"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["google"],
            "name": "gemini-1.5-flash",
            "display_name": "Gemini 1.5 Flash",
            "description": "Fast and efficient model for most use cases",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.000075,
            "output_cost_per_1k_tokens": 0.0003,
            "capabilities": ["text", "vision", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["google"],
            "name": "gemini-2.0-flash",
            "display_name": "Gemini 2.0 Flash",
            "description": "Latest Gemini model with improved performance",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.000075,
            "output_cost_per_1k_tokens": 0.0003,
            "capabilities": ["text", "vision", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese", "Japanese", "Korean"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "high"},
            "is_active": True,
            "is_default": False
        },
        
        # Mistral Models
        {
            "provider_id": created_providers["mistral"],
            "name": "mistral-large",
            "display_name": "Mistral Large",
            "description": "Most capable Mistral model for complex tasks",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.007,
            "output_cost_per_1k_tokens": 0.024,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "performance_metrics": {"speed": "medium", "accuracy": "high"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["mistral"],
            "name": "mistral-medium",
            "display_name": "Mistral Medium",
            "description": "Balanced model for general use",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0027,
            "output_cost_per_1k_tokens": 0.0081,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "performance_metrics": {"speed": "fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["mistral"],
            "name": "mistral-small",
            "display_name": "Mistral Small",
            "description": "Fast and cost-effective model",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0002,
            "output_cost_per_1k_tokens": 0.0006,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        
        # Cohere Models
        {
            "provider_id": created_providers["cohere"],
            "name": "command-r-plus",
            "display_name": "Command R+",
            "description": "Advanced model for enterprise applications",
            "model_type": "chat",
            "context_length": 100000,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "performance_metrics": {"speed": "fast", "accuracy": "high"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["cohere"],
            "name": "command-r",
            "display_name": "Command R",
            "description": "Balanced model for general use",
            "model_type": "chat",
            "context_length": 100000,
            "input_cost_per_1k_tokens": 0.0005,
            "output_cost_per_1k_tokens": 0.0015,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Chinese"],
            "performance_metrics": {"speed": "fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        
        # Meta Models
        {
            "provider_id": created_providers["meta"],
            "name": "llama-3.1-8b",
            "display_name": "Llama 3.1 8B",
            "description": "Efficient open-source model",
            "model_type": "chat",
            "context_length": 8192,
            "input_cost_per_1k_tokens": 0.0001,
            "output_cost_per_1k_tokens": 0.0002,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "performance_metrics": {"speed": "very_fast", "accuracy": "medium"},
            "is_active": True,
            "is_default": False
        },
        {
            "provider_id": created_providers["meta"],
            "name": "llama-3.1-70b",
            "display_name": "Llama 3.1 70B",
            "description": "High-performance open-source model",
            "model_type": "chat",
            "context_length": 8192,
            "input_cost_per_1k_tokens": 0.0007,
            "output_cost_per_1k_tokens": 0.0008,
            "capabilities": ["text", "function_calling"],
            "supported_languages": ["English", "Twi", "French", "Spanish", "German", "Italian", "Portuguese"],
            "performance_metrics": {"speed": "medium", "accuracy": "high"},
            "is_active": True,
            "is_default": False
        }
    ]
    
    # Create models
    for model_data in models_data:
        model = LLMModel(**model_data)
        created_model = await llm_service.create_model(model)
        print(f"Created model: {model.display_name} ({model.name})")
    
    print(f"\nSuccessfully populated MongoDB with {len(providers_data)} providers and {len(models_data)} models!")
    print("Default model set to: GPT-4o")


if __name__ == "__main__":
    asyncio.run(populate_llm_data())
