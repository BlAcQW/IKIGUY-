# Inkwave - Gemini 2.5 Flash Integration

**Date**: 2025-10-24
**Purpose**: Document how Inkwave uses Gemini 2.5 Flash via shared services

---

## 🎯 Overview

Inkwave uses **Gemini 2.5 Flash** for:
1. **RAG Q&A** - Answering user questions about books
2. **Book metadata generation** - Summaries, themes, difficulty level
3. **Personalized responses** - Adapting to user's reading level

---

## 🚀 Shared Services

### 1. GeminiService (`@apps/shared/integration/gemini_service.py`)

**Purpose**: Direct HTTP-based Gemini API client for content generation

**Configuration**:
```python
from apps.shared.integration.gemini_service import GeminiService

# Initialize service
gemini_service = GeminiService(
    api_key=os.getenv("GEMINI_API_KEY"),  # or None to use env var
    model="gemini-2.5-flash"  # ✅ Default model
)

# Check availability
if not gemini_service.is_available():
    raise Exception("Gemini API key not configured")
```

**Key Features**:
- ✅ Gemini 2.5 Flash support
- ✅ Async HTTP requests (httpx)
- ✅ Proper error handling
- ✅ Timeout management (60s default)
- ✅ Safety filter detection
- ✅ Token limit handling
- ✅ Finish reason logging
- ✅ Auto-truncation for long prompts

**Usage Examples**:

#### Basic Content Generation
```python
# Generate content
result = await gemini_service.generate_content(
    prompt="Explain validated learning in simple terms",
    temperature=0.7,
    max_output_tokens=1000,
    timeout=60.0
)

# Access response
content = result["content"]  # Generated text
model = result["model"]  # "gemini-2.5-flash"
finish_reason = result["finish_reason"]  # "STOP", "MAX_TOKENS", etc.
```

#### Generate Summary
```python
# Optimized for summarization (lower temperature)
summary = await gemini_service.generate_summary(
    content=book_text,
    max_output_tokens=500,
    temperature=0.3  # Lower temp for consistency
)
```

#### Extract Structured Data
```python
# Optimized for extraction (very low temperature)
data = await gemini_service.extract_structured_data(
    prompt=f"""Extract the following from this text:
    - Title
    - Author
    - Main themes (5 max)
    - Difficulty level (beginner/intermediate/advanced)

    Text: {book_excerpt}

    Return as JSON.
    """,
    max_output_tokens=1500,
    temperature=0.1  # Very low for consistency
)
```

#### Generate System Prompt
```python
# For generating AI agent prompts
system_prompt = await gemini_service.generate_system_prompt(
    prompt="Create a system prompt for an AI book companion that explains concepts clearly to beginners",
    max_output_tokens=1000,
    temperature=0.7
)
```

---

### 2. RAGService with Gemini (`@apps/shared/integration/rag.py`)

**Purpose**: RAG (Retrieval-Augmented Generation) with Gemini 2.5 Flash for Q&A

**Configuration for Inkwave**:
```python
from apps.shared.integration.rag import RAGService, RAGConfig

# Configure RAG with Gemini 2.5 Flash
rag_config = RAGConfig(
    # PostgreSQL (pgvector) config
    postgres_host=os.getenv("PGVECTOR_HOST"),
    postgres_password=os.getenv("PGVECTOR_PASSWORD"),
    postgres_db="inkwave_rag",

    # Gemini config
    ai_provider="gemini",  # ✅ Use Gemini
    api_key=os.getenv("GEMINI_API_KEY"),
    embedding_model="text-embedding-004",  # Gemini embeddings
    llm_model="gemini-2.5-flash",  # ✅ Gemini 2.5 Flash for Q&A

    # RAG parameters
    chunk_size=1000,  # Chunk size for book text
    chunk_overlap=200,  # Overlap for context continuity
    retrieval_k=5,  # Top 5 relevant chunks
    similarity_threshold=0.3,  # Min similarity score
    confidence_threshold=0.7,  # Escalate if lower
    temperature=0.1  # Low for consistent answers
)

# Initialize RAG service
rag_service = RAGService(config=rag_config)
```

**Usage in Inkwave**:

#### Index Book Chunks
```python
from apps.shared.integration.rag import KnowledgeDocument

# Index book for Q&A
documents = [
    KnowledgeDocument(
        title=f"{book.title} - Chapter {chunk.chapter_id}, Chunk {i}",
        content=chunk.text,
        category=book.genre,
        metadata={
            "book_id": str(book.id),
            "chunk_index": i,
            "chapter_id": chunk.chapter_id,
            "position": i  # For spoiler prevention
        }
    )
    for i, chunk in enumerate(book_chunks)
]

await rag_service.initialize_knowledge_base(
    collection_name=f"book_{book.id}",
    documents=documents
)
```

#### Q&A with Context
```python
# User asks a question about the book
result = await rag_service.query_knowledge_base(
    collection_name=f"book_{book.id}",
    query=user_question,
    system_prompt=f"""You are a personalized book companion for "{book.title}".

    Answer the user's question clearly and adapt to their reading level: {user.reading_level}.

    Rules:
    - Use passages from the book to support your answer
    - Don't reveal information beyond the user's current position
    - If you're not confident, say so
    - Keep answers concise but complete
    """,
    context_metadata={
        "current_chunk": session.current_chunk_index,
        "reading_level": user.profile.reading_level,
        "user_id": str(user.id),
        "max_spoiler_chunk": session.current_chunk_index  # Prevent spoilers
    }
)

# Check confidence
if result.confidence_score < 0.7:
    # Low confidence - prompt user for clarification
    return {
        "response": result.response,
        "confidence": "low",
        "suggestion": "Could you rephrase your question or be more specific?"
    }

# High confidence - return answer
return {
    "response": result.response,
    "confidence": "high",
    "sources": result.sources_used,
    "requires_escalation": result.requires_escalation
}
```

---

## 📊 Gemini 2.5 Flash vs 2.0 Flash

| Feature | Gemini 2.0 Flash | Gemini 2.5 Flash |
|---------|------------------|------------------|
| Speed | Fast | **Faster** |
| Context Window | 1M tokens | **2M tokens** |
| Cost | $0.075/$0.30 | **$0.075/$0.30** (same) |
| Multilingual | Good | **Better** |
| Reasoning | Good | **Improved** |
| Safety | Good | **Enhanced** |

**Why 2.5 Flash for Inkwave**:
- ✅ **2M token context** - Can process entire chapters at once
- ✅ **Faster responses** - Better for voice Q&A latency
- ✅ **Better reasoning** - More accurate answers
- ✅ **Same cost** - No price increase
- ✅ **Improved multilingual** - Ready for African language expansion

---

## 💰 Cost Analysis (Gemini 2.5 Flash)

### RAG Q&A Cost Breakdown

**Per Voice Q&A**:
1. **Embeddings** (Gemini text-embedding-004):
   - 5 chunk retrievals × ~500 tokens each = ~2,500 tokens
   - Cost: ~$0.0000625 (negligible)

2. **LLM Query** (Gemini 2.5 Flash):
   - Input: User question (50 tokens) + 5 retrieved chunks (2,500 tokens) + system prompt (200 tokens) = ~2,750 tokens
   - Output: AI response (~300 tokens)
   - Cost: (2,750 × $0.075/1M) + (300 × $0.30/1M) = ~$0.00021 + $0.00009 = **$0.0003**

3. **Total RAG cost per Q&A**: ~$0.0003 (~0.03 credits)

**Add Voice Costs**:
- STT (Whisper): ~$0.01 (1 credit)
- TTS (OpenAI tts-1): ~$0.03 (3 credits)
- **Total voice Q&A cost**: ~$0.04 (4 credits)

**Comparison**:
- OpenAI GPT-4o-mini: ~$0.001 per Q&A (5x more expensive)
- Gemini 2.5 Flash: ~$0.0003 per Q&A (best value)

---

## 🛠️ Implementation in Inkwave

### Voice Agent Service (`@apps/inkwave/backend/services/voice_agent.py`)

```python
from apps.shared.integration.rag import RAGService, RAGConfig, QueryResult
from apps.shared.integration.gemini_service import GeminiService
from apps.shared.integration.usage_calculator import UsageCalculator

class VoiceAgentService:
    """
    Orchestrates voice Q&A using Gemini 2.5 Flash RAG.
    """

    def __init__(self):
        # Initialize Gemini RAG
        self.rag_config = RAGConfig(
            postgres_host=os.getenv("PGVECTOR_HOST"),
            postgres_password=os.getenv("PGVECTOR_PASSWORD"),
            ai_provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            embedding_model="text-embedding-004",
            llm_model="gemini-2.5-flash",  # ✅ Use 2.5 Flash
            retrieval_k=5,
            confidence_threshold=0.7,
            temperature=0.1
        )
        self.rag_service = RAGService(config=self.rag_config)

        # Fallback Gemini service (for metadata generation)
        self.gemini_service = GeminiService(model="gemini-2.5-flash")

        # Usage calculator
        self.usage_calculator = UsageCalculator()

    async def answer_question(
        self,
        book_id: str,
        user_question: str,
        current_chunk_index: int,
        reading_level: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Answer user's voice question about the book.

        Args:
            book_id: Book identifier
            user_question: Transcribed question from STT
            current_chunk_index: Current reading position
            reading_level: User's reading level
            user_id: User identifier

        Returns:
            Dict with answer, confidence, cost, etc.
        """
        # Query RAG
        result: QueryResult = await self.rag_service.query_knowledge_base(
            collection_name=f"book_{book_id}",
            query=user_question,
            system_prompt=f"""You are a personalized book companion.

            Answer clearly and adapt to this reading level: {reading_level}.

            Rules:
            - Use book passages to support your answer
            - Keep answers under 100 words (for TTS)
            - No spoilers beyond current position
            - If unsure, admit it
            """,
            context_metadata={
                "current_chunk": current_chunk_index,
                "reading_level": reading_level,
                "user_id": user_id,
                "max_position": current_chunk_index
            }
        )

        # Calculate cost
        rag_cost = self.usage_calculator.calculate_rag_cost(
            input_tokens=2750,  # Estimate
            output_tokens=300,  # Estimate
            num_queries=1
        )

        return {
            "response": result.response,
            "confidence": result.confidence_score,
            "sources": result.sources_used,
            "cost": rag_cost.total_cost,
            "requires_escalation": result.requires_escalation
        }

    async def generate_book_summary(
        self,
        book_text: str
    ) -> str:
        """
        Generate book summary using Gemini 2.5 Flash.

        Args:
            book_text: Full book text or excerpt

        Returns:
            Generated summary (250 words)
        """
        summary = await self.gemini_service.generate_summary(
            content=f"""Summarize this book in 250 words. Focus on:
            - Main premise
            - Key concepts
            - Target audience
            - What readers will learn

            Text: {book_text[:15000]}  # Limit for API
            """,
            max_output_tokens=500,
            temperature=0.3
        )
        return summary
```

---

## 🔧 Environment Variables

```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL (pgvector) for RAG
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=your_password
PGVECTOR_DB=inkwave_rag
```

---

## 📝 Usage Checklist

- [x] GeminiService moved to `@apps/shared/integration/gemini_service.py`
- [x] Updated default model to `gemini-2.5-flash`
- [x] RAGService configured to use Gemini 2.5 Flash
- [x] Environment variables documented
- [x] Cost analysis completed
- [x] Example implementation provided

---

## 🚀 Next Steps

1. **Test Gemini integration**:
   ```bash
   cd /opt/kasaai/apps/inkwave/backend
   pytest tests/test_gemini_service.py
   ```

2. **Index sample book**:
   ```python
   # Run indexing script
   python scripts/index_book.py --book_id=test_book_1
   ```

3. **Test Q&A**:
   ```python
   # Test Q&A endpoint
   curl -X POST https://api.ailabsafrica.com/bookshop/v1/voice/ask \
     -H "Content-Type: application/json" \
     -d '{
       "book_id": "test_book_1",
       "question": "What is validated learning?",
       "current_chunk": 10
     }'
   ```

---

## 📊 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **RAG latency** | < 2 seconds | Gemini 2.5 Flash response time |
| **Confidence threshold** | > 0.7 | Escalate if lower |
| **Cost per Q&A** | < $0.001 | Gemini is ~$0.0003 |
| **Accuracy** | > 90% | Measured via user feedback |

---

**Last Updated**: 2025-10-24
**Model**: Gemini 2.5 Flash (gemini-2.5-flash)
**Status**: Shared service ready in `@apps/shared/integration/`
