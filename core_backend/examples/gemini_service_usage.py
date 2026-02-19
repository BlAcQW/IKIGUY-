"""
Gemini Service Usage Examples

This file demonstrates how to use the centralized Gemini service
for various AI operations throughout the application.
"""

import asyncio
import os
from backend.services.gemini_service import (
    GeminiService,
    get_gemini_service,
    set_gemini_model,
    generate_content_with_gemini
)


async def basic_usage_example():
    """Basic usage of the Gemini service."""
    print("=== Basic Gemini Service Usage ===")

    # Get the global service instance
    gemini_service = get_gemini_service()

    if not gemini_service.is_available():
        print("❌ Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        return

    try:
        # Generate simple content
        prompt = "Write a brief introduction to AI in customer service."
        result = await gemini_service.generate_content(
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=200
        )

        print(f"✅ Generated content ({result['output_length']} chars):")
        print(f"📝 {result['content'][:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")


async def specialized_methods_example():
    """Example using specialized methods for different use cases."""
    print("\n=== Specialized Methods ===")

    gemini_service = get_gemini_service()

    if not gemini_service.is_available():
        print("❌ Gemini service not available")
        return

    try:
        # 1. System prompt generation (optimized for AI agent prompts)
        system_prompt = await gemini_service.generate_system_prompt(
            prompt="Create a system prompt for a customer service AI that helps with product returns.",
            temperature=0.7,
            max_output_tokens=500
        )
        print(f"🤖 System Prompt: {system_prompt[:100]}...")

        # 2. Summary generation (optimized for consistency)
        summary = await gemini_service.generate_summary(
            content="This is a long customer call transcript about a billing issue. The customer called because they were charged twice for the same service. The agent helped resolve the issue by processing a refund for the duplicate charge.",
            temperature=0.3,
            max_output_tokens=100
        )
        print(f"📄 Summary: {summary}")

        # 3. Structured data extraction (optimized for JSON/structured output)
        extraction_prompt = """
        Extract the following information from this text in JSON format:
        Text: "John Smith called about his order #12345. His email is john@example.com and phone is 555-0123."

        Extract: {"name": "", "order_id": "", "email": "", "phone": ""}
        """

        extracted_data = await gemini_service.extract_structured_data(
            prompt=extraction_prompt,
            temperature=0.1,
            max_output_tokens=200
        )
        print(f"🔍 Extracted Data: {extracted_data}")

    except Exception as e:
        print(f"❌ Error in specialized methods: {e}")


async def model_management_example():
    """Example of changing models dynamically."""
    print("\n=== Model Management ===")

    gemini_service = get_gemini_service()
    print(f"📱 Current model: {gemini_service.model}")

    # Change to a different model
    set_gemini_model("gemini-2.5-pro")
    print(f"📱 Updated model: {gemini_service.model}")

    # Change back to Flash
    set_gemini_model("gemini-2.5-flash")
    print(f"📱 Reverted model: {gemini_service.model}")


async def convenience_function_example():
    """Example using the convenience function."""
    print("\n=== Convenience Function ===")

    try:
        # Use the convenience function for quick generation
        content = await generate_content_with_gemini(
            prompt="List 3 benefits of AI customer service.",
            temperature=0.5,
            max_output_tokens=150
        )
        print(f"⚡ Quick generation: {content}")

    except Exception as e:
        print(f"❌ Error with convenience function: {e}")


async def error_handling_example():
    """Example of proper error handling."""
    print("\n=== Error Handling ===")

    # Create a service with invalid API key for testing
    test_service = GeminiService(api_key="invalid-key")

    try:
        await test_service.generate_content("Test prompt")
    except Exception as e:
        print(f"✅ Properly caught error: {e}")

    # Test with no API key
    no_key_service = GeminiService()
    try:
        await no_key_service.generate_content("Test prompt")
    except Exception as e:
        print(f"✅ Properly caught no-key error: {e}")


async def integration_example():
    """Example showing how this integrates with existing AI workflow."""
    print("\n=== Integration with AI Workflow ===")

    gemini_service = get_gemini_service()

    if not gemini_service.is_available():
        print("❌ Gemini not available, would fall back to OpenAI or Anthropic")
        return

    try:
        # This is how you would use it in the AI prompt generator
        website_info = "Company: TechCorp. Business: Software development. Services: Web apps, mobile apps."

        ai_prompt = f"""
        Create a customer service system prompt for this company:
        {website_info}

        The agent should be helpful, professional, and knowledgeable about their services.
        """

        system_prompt = await gemini_service.generate_system_prompt(
            prompt=ai_prompt,
            temperature=0.7,
            max_output_tokens=800
        )

        print(f"🏢 Company-specific system prompt generated: {len(system_prompt)} characters")
        print(f"📝 Preview: {system_prompt[:200]}...")

    except Exception as e:
        print(f"❌ Integration error: {e}")


async def main():
    """Run all examples."""
    print("🚀 Gemini Service Examples\n")

    await basic_usage_example()
    await specialized_methods_example()
    await model_management_example()
    await convenience_function_example()
    await error_handling_example()
    await integration_example()

    print("\n✅ All examples completed!")


if __name__ == "__main__":
    # Set up environment for testing (optional)
    # os.environ["GEMINI_API_KEY"] = "your-api-key-here"

    asyncio.run(main())