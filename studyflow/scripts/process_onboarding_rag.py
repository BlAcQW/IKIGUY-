"""
Process Onboarding Modules through RAG Pipeline.

Vectorizes all 10 onboarding modules for voice Q&A and assessment
question generation.

Usage:
    PYTHONPATH=/opt/kasaai:/opt/kasaai/apps/studyflow/backend:/opt/kasaai/apps \
    POSTGRES_PASSWORD="aawwER444444" \
    GEMINI_API_KEY="AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4" \
    /opt/kasaai/apps/venv/bin/python3 process_onboarding_rag.py

Author: KasaAI
Created: 2025-11-07
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add paths
sys.path.insert(0, "/opt/kasaai")
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.integration.rag import RAGConfig, RAGService

# Configuration
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")

MODULES_DIR = "/opt/kasaai/apps/studyflow/storage/onboarding_modules"
COLLECTION_NAME = "ai_labs_org_001_developer_onboarding"
ORGANIZATION_ID = "ai_labs_org_001"

# RAG Configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


class OnboardingRAGProcessor:
    """Process onboarding modules through RAG pipeline."""

    def __init__(self):
        """Initialize RAG processor."""
        self.rag_config = RAGConfig(
            postgres_host="localhost",
            postgres_port="5432",
            postgres_user="postgres",
            postgres_password=POSTGRES_PASSWORD,
            postgres_db="kasaai_core",
            ai_provider="gemini",
            api_key=GEMINI_API_KEY,
            llm_model="gemini-2.0-flash-exp",
            embedding_model="models/text-embedding-004"
        )
        self.rag_service = RAGService(self.rag_config)
        print("✓ RAG service initialized")

    async def process_all_modules(self) -> Dict[str, Any]:
        """
        Process all 10 onboarding modules.

        Returns:
            Processing statistics
        """
        modules_dir = Path(MODULES_DIR)
        module_files = sorted(modules_dir.glob("module_*.md"))

        if not module_files:
            raise FileNotFoundError(f"No module files found in {MODULES_DIR}")

        print(f"\n📚 Found {len(module_files)} modules to process")
        print("=" * 70)

        total_chunks = 0
        total_chars = 0
        processed_modules = []

        for module_file in module_files:
            print(f"\n📄 Processing: {module_file.name}")

            # Read module content
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract module metadata
            module_metadata = self._extract_module_metadata(module_file.name, content)

            # Add document to RAG
            result = await self._process_module(
                content=content,
                metadata=module_metadata
            )

            total_chunks += result['chunks']
            total_chars += result['chars']
            processed_modules.append(result)

            print(f"  ✓ Processed: {result['chunks']} chunks, {result['chars']} characters")

        print("\n" + "=" * 70)
        print("✅ ALL MODULES PROCESSED")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   - Modules processed: {len(processed_modules)}")
        print(f"   - Total chunks: {total_chunks}")
        print(f"   - Total characters: {total_chars}")
        print(f"   - Collection: {COLLECTION_NAME}")
        print(f"   - Organization: {ORGANIZATION_ID}")

        # Test queries
        await self._test_rag_queries()

        return {
            "modules_processed": len(processed_modules),
            "total_chunks": total_chunks,
            "total_chars": total_chars,
            "collection_name": COLLECTION_NAME
        }

    def _extract_module_metadata(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Extract metadata from module filename and content.

        Args:
            filename: Module filename
            content: Module content

        Returns:
            Metadata dictionary
        """
        # Extract module number from filename (e.g., "module_01_...")
        import re
        match = re.search(r'module_(\d+)', filename)
        module_number = int(match.group(1)) if match else 0

        # Extract title from first heading
        title_match = re.search(r'^# Module \d+: (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Module {module_number}"

        # Extract topics from content
        topics_match = re.search(r'\*\*Topics Covered:\*\* (.+)$', content, re.MULTILINE)
        topics = []
        if topics_match:
            topics = [t.strip() for t in topics_match.group(1).split(',')]

        return {
            "module_number": module_number,
            "module_title": title,
            "topics": topics,
            "organization_id": ORGANIZATION_ID,
            "source": "developer_onboarding",
            "content_type": "markdown"
        }

    async def _process_module(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single module through RAG.

        Args:
            content: Module content
            metadata: Module metadata

        Returns:
            Processing result
        """
        # Add document to RAG collection
        await self.rag_service.add_document(
            collection_name=COLLECTION_NAME,
            content=content,
            metadata=metadata,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        # Calculate chunks (approximate)
        estimated_chunks = len(content) // (CHUNK_SIZE * 4) + 1  # Rough estimate

        return {
            "module_number": metadata["module_number"],
            "module_title": metadata["module_title"],
            "chunks": estimated_chunks,
            "chars": len(content),
            "metadata": metadata
        }

    async def _test_rag_queries(self):
        """Test RAG with sample queries."""
        print("\n" + "=" * 70)
        print("🧪 TESTING RAG QUERIES")
        print("=" * 70)

        test_queries = [
            ("What is KasaAI's mission?", "Module 1"),
            ("Explain the monorepo architecture", "Module 2"),
            ("What is the core backend?", "Module 3"),
            ("What apps does KasaAI have?", "Module 4-5"),
            ("What is Voice Lab?", "Module 6"),
            ("How do I set up my dev environment?", "Module 7"),
            ("What should I do in week 1?", "Module 8"),
            ("What are the coding standards?", "Module 9"),
            ("Where can I get help?", "Module 10")
        ]

        passed = 0
        failed = 0

        for query, expected_module in test_queries:
            print(f"\n❓ Query: \"{query}\"")
            print(f"   Expected from: {expected_module}")

            try:
                result = await self.rag_service.query_with_context(
                    query=query,
                    collection_name=COLLECTION_NAME,
                    top_k=3,
                    filters={"organization_id": ORGANIZATION_ID}
                )

                # Check if results are relevant
                if result and result.get("documents"):
                    context_preview = result["context"][:200] + "..."
                    confidence = result.get("confidence", 0)

                    print(f"   ✓ Retrieved {len(result['documents'])} chunks")
                    print(f"   ✓ Confidence: {confidence:.2%}")
                    print(f"   ✓ Context preview: {context_preview}")

                    if confidence > 0.7:
                        passed += 1
                        print(f"   ✅ PASS (confidence > 70%)")
                    else:
                        failed += 1
                        print(f"   ⚠️  WARN (confidence < 70%)")
                else:
                    failed += 1
                    print(f"   ❌ FAIL (no results)")

            except Exception as e:
                failed += 1
                print(f"   ❌ ERROR: {str(e)}")

        print("\n" + "=" * 70)
        print(f"Test Results: {passed} passed, {failed} failed")
        print("=" * 70)

        if passed >= 7:  # At least 70% should pass
            print("✅ RAG pipeline is working well!")
        else:
            print("⚠️  RAG pipeline needs optimization")


async def main():
    """Main entry point."""
    print("=" * 70)
    print("🚀 ONBOARDING MODULES RAG PROCESSING")
    print("=" * 70)

    processor = OnboardingRAGProcessor()

    try:
        result = await processor.process_all_modules()
        print(f"\n✅ Processing complete!")
        print(f"\n🎯 Next steps:")
        print(f"   1. Test voice Q&A on module content")
        print(f"   2. Generate assessment questions from RAG")
        print(f"   3. Configure voice settings for AI Labs org")

        return result

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
