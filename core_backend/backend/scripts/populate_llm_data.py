#!/usr/bin/env python3
"""Script to populate MongoDB with latest LLM providers and models."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.models import LLMProvider, LLMModel
from backend.services.llm_service import llm_service


async def populate_llm_data():
    """Populate the database with latest LLM providers and models."""
    
    print("🔄 Populating LLM providers and models...")
    
    # Define the latest LLM providers and models based on research
    providers_data = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "description": "Leading AI research company known for GPT models",
            "website": "https://openai.com",
            "api_base_url": "https://api.openai.com/v1",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "embeddings", "vision", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 128000
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic",
            "description": "AI safety-focused company with Claude models",
            "website": "https://anthropic.com",
            "api_base_url": "https://api.anthropic.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "vision", "function_calling", "constitutional_ai"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 200000
        },
        {
            "name": "google",
            "display_name": "Google",
            "description": "Tech giant with Gemini models",
            "website": "https://ai.google.dev",
            "api_base_url": "https://generativelanguage.googleapis.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "vision", "function_calling", "multimodal"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 1000000
        },
        {
            "name": "meta",
            "display_name": "Meta",
            "description": "Social media company with Llama models",
            "website": "https://ai.meta.com",
            "api_base_url": "https://api.meta.ai",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "open_source"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 32768
        },
        {
            "name": "mistral",
            "display_name": "Mistral AI",
            "description": "French AI company with high-performance models",
            "website": "https://mistral.ai",
            "api_base_url": "https://api.mistral.ai",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "embeddings", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 32768
        },
        {
            "name": "deepseek",
            "display_name": "DeepSeek",
            "description": "AI research company with advanced reasoning models",
            "website": "https://deepseek.com",
            "api_base_url": "https://api.deepseek.com",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "reasoning", "coding"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 128000
        },
        {
            "name": "cohere",
            "display_name": "Cohere",
            "description": "Enterprise-focused AI company",
            "website": "https://cohere.com",
            "api_base_url": "https://api.cohere.ai",
            "pricing_model": "per_token",
            "features": ["chat", "completion", "embeddings", "rerank", "classify"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "max_context_length": 32768
        }
    ]
    
    # Create providers
    provider_ids = {}
    for provider_data in providers_data:
        provider = LLMProvider(**provider_data)
        created_provider = await llm_service.create_provider(provider)
        provider_ids[provider.name] = created_provider.id
        print(f"✅ Created provider: {created_provider.display_name}")
    
    # Define models for each provider
    models_data = [
        # OpenAI Models
        {
            "provider_id": provider_ids["openai"],
            "name": "gpt-4o",
            "display_name": "GPT-4o",
            "description": "Latest GPT-4 model with improved performance and lower costs",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.0025,
            "output_cost_per_1k_tokens": 0.01,
            "capabilities": ["chat", "vision", "function_calling", "reasoning"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "excellent", "reasoning": "strong"},
            "is_default": True
        },
        {
            "provider_id": provider_ids["openai"],
            "name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "description": "Faster and more cost-effective version of GPT-4o",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.00015,
            "output_cost_per_1k_tokens": 0.0006,
            "capabilities": ["chat", "function_calling", "reasoning"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "very_fast", "quality": "good", "reasoning": "good"}
        },
        {
            "provider_id": provider_ids["openai"],
            "name": "gpt-4-turbo",
            "display_name": "GPT-4 Turbo",
            "description": "Previous generation GPT-4 model",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.01,
            "output_cost_per_1k_tokens": 0.03,
            "capabilities": ["chat", "vision", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "medium", "quality": "excellent", "reasoning": "strong"}
        },
        
        # Anthropic Models
        {
            "provider_id": provider_ids["anthropic"],
            "name": "claude-3-5-sonnet",
            "display_name": "Claude 3.5 Sonnet",
            "description": "Latest Claude model with excellent reasoning capabilities",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "capabilities": ["chat", "vision", "function_calling", "reasoning", "coding"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "excellent", "reasoning": "excellent"}
        },
        {
            "provider_id": provider_ids["anthropic"],
            "name": "claude-3-opus",
            "display_name": "Claude 3 Opus",
            "description": "Most capable Claude model for complex tasks",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.015,
            "output_cost_per_1k_tokens": 0.075,
            "capabilities": ["chat", "vision", "function_calling", "reasoning", "coding", "analysis"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "medium", "quality": "excellent", "reasoning": "excellent"}
        },
        {
            "provider_id": provider_ids["anthropic"],
            "name": "claude-3-haiku",
            "display_name": "Claude 3 Haiku",
            "description": "Fastest Claude model for simple tasks",
            "model_type": "chat",
            "context_length": 200000,
            "input_cost_per_1k_tokens": 0.00025,
            "output_cost_per_1k_tokens": 0.00125,
            "capabilities": ["chat", "vision", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "very_fast", "quality": "good", "reasoning": "good"}
        },
        
        # Google Models
        {
            "provider_id": provider_ids["google"],
            "name": "gemini-1.5-pro",
            "display_name": "Gemini 1.5 Pro",
            "description": "Latest Gemini model with 1M token context",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.0035,
            "output_cost_per_1k_tokens": 0.0105,
            "capabilities": ["chat", "vision", "function_calling", "multimodal"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "excellent", "reasoning": "strong"}
        },
        {
            "provider_id": provider_ids["google"],
            "name": "gemini-1.5-flash",
            "display_name": "Gemini 1.5 Flash",
            "description": "Faster Gemini model for quick responses",
            "model_type": "chat",
            "context_length": 1000000,
            "input_cost_per_1k_tokens": 0.000075,
            "output_cost_per_1k_tokens": 0.0003,
            "capabilities": ["chat", "vision", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "very_fast", "quality": "good", "reasoning": "good"}
        },
        
        # Meta Models
        {
            "provider_id": provider_ids["meta"],
            "name": "llama-3.1-405b",
            "display_name": "Llama 3.1 405B",
            "description": "Latest large Llama model",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0006,
            "output_cost_per_1k_tokens": 0.0016,
            "capabilities": ["chat", "completion", "coding"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "medium", "quality": "good", "reasoning": "good"}
        },
        {
            "provider_id": provider_ids["meta"],
            "name": "llama-3.1-8b",
            "display_name": "Llama 3.1 8B",
            "description": "Efficient Llama model for fast responses",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0002,
            "output_cost_per_1k_tokens": 0.0002,
            "capabilities": ["chat", "completion"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "very_fast", "quality": "good", "reasoning": "fair"}
        },
        
        # Mistral Models
        {
            "provider_id": provider_ids["mistral"],
            "name": "mistral-large",
            "display_name": "Mistral Large",
            "description": "Most capable Mistral model",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.007,
            "output_cost_per_1k_tokens": 0.024,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "excellent", "reasoning": "strong"}
        },
        {
            "provider_id": provider_ids["mistral"],
            "name": "mistral-medium",
            "display_name": "Mistral Medium",
            "description": "Balanced Mistral model",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0027,
            "output_cost_per_1k_tokens": 0.0081,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "good", "reasoning": "good"}
        },
        {
            "provider_id": provider_ids["mistral"],
            "name": "mistral-small",
            "display_name": "Mistral Small",
            "description": "Fastest Mistral model",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.0014,
            "output_cost_per_1k_tokens": 0.0042,
            "capabilities": ["chat", "completion"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "very_fast", "quality": "good", "reasoning": "fair"}
        },
        
        # DeepSeek Models
        {
            "provider_id": provider_ids["deepseek"],
            "name": "deepseek-coder",
            "display_name": "DeepSeek Coder",
            "description": "Specialized coding model",
            "model_type": "chat",
            "context_length": 128000,
            "input_cost_per_1k_tokens": 0.0014,
            "output_cost_per_1k_tokens": 0.0028,
            "capabilities": ["chat", "completion", "coding", "reasoning"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "excellent", "reasoning": "strong"}
        },
        
        # Cohere Models
        {
            "provider_id": provider_ids["cohere"],
            "name": "command-r-plus",
            "display_name": "Command R+",
            "description": "Latest Cohere model for enterprise use",
            "model_type": "chat",
            "context_length": 32768,
            "input_cost_per_1k_tokens": 0.003,
            "output_cost_per_1k_tokens": 0.015,
            "capabilities": ["chat", "completion", "function_calling"],
            "supported_languages": ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Russian", "Japanese", "Korean", "Chinese", "Arabic", "Hindi", "Twi", "Swahili"],
            "performance_metrics": {"speed": "fast", "quality": "good", "reasoning": "good"}
        }
    ]
    
    # Create models
    for model_data in models_data:
        model = LLMModel(**model_data)
        created_model = await llm_service.create_model(model)
        print(f"✅ Created model: {created_model.display_name} ({created_model.name})")
    
    print(f"\n🎉 Successfully populated database with {len(providers_data)} providers and {len(models_data)} models!")
    print("📊 Default model set to: GPT-4o")


if __name__ == "__main__":
    asyncio.run(populate_llm_data())
