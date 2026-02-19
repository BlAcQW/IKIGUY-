# Inkwave - Shared Services Usage

**Date**: 2025-10-24
**Purpose**: Document how Inkwave maximizes reuse of KasaAI shared services

---

## ✅ Shared Services We're Using (from @apps/shared/integration/)

### 1. RAGService (`rag.py`)

**Purpose**: Semantic search for intelligent Q&A about book content

**What it provides**:
- Document indexing with vector embeddings
- Semantic search and retrieval (pgvector)
- LLM-powered Q&A with context
- Multiple AI provider support (OpenAI, Gemini, Anthropic)
- Confidence scoring and escalation logic
- LangChain integration

**How Inkwave uses it**:
```python
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

# Initialize RAG service for bookshop
rag_config = RAGConfig(
    postgres_host=os.getenv("PGVECTOR_HOST"),
    postgres_password=os.getenv("PGVECTOR_PASSWORD"),
    ai_provider="openai",  # or "gemini", "anthropic"
    api_key=os.getenv("OPENAI_API_KEY"),
    embedding_model="text-embedding-3-small",
    llm_model="gpt-4o-mini",
    retrieval_k=5,  # Top 5 relevant chunks
    confidence_threshold=0.7,  # Escalate if lower
    similarity_threshold=0.3
)

rag_service = RAGService(config=rag_config)

# Index book chunks
documents = [
    KnowledgeDocument(
        title=f"{book.title} - Chunk {i}",
        content=chunk.text,
        category=book.genre,
        metadata={
            "book_id": str(book.id),
            "chunk_index": i,
            "chapter_id": chunk.chapter_id,
            "no_spoilers_after": i  # Prevent spoilers
        }
    )
    for i, chunk in enumerate(book_chunks)
]

await rag_service.initialize_knowledge_base(
    collection_name=f"book_{book.id}",
    documents=documents
)

# Query for Q&A
result = await rag_service.query_knowledge_base(
    collection_name=f"book_{book.id}",
    query=user_question,
    system_prompt="""You are a personalized book companion.
    Answer questions about the book with context-aware explanations.
    Adapt to the user's reading level.""",
    context_metadata={
        "current_chunk": session.current_chunk_index,
        "reading_level": user.profile.reading_level,
        "user_id": user.id
    }
)

# Use confidence score
if result.confidence_score < 0.7:
    # Prompt user for clarification
    return {
        "response": "I'm not fully confident in my answer. Could you rephrase your question?",
        "confidence": result.confidence_score
    }
```

**Benefits**:
- ✅ No need to build RAG from scratch
- ✅ Provider-agnostic (switch between OpenAI/Gemini/Anthropic)
- ✅ Built-in confidence scoring
- ✅ Optimized chunking and retrieval
- ✅ Tested and production-ready

---

### 2. WalletService (`wallet.py`)

**Purpose**: Credit-based payment and billing management

**What it provides**:
- Wallet creation and balance management
- Transaction recording (credit/debit/refund)
- Payment gateway integration (Stripe, Paystack, MoMo)
- Top-up functionality
- Transaction history and auditing
- Multi-currency support (GHS, USD, EUR, NGN, KES, ZAR)
- Idempotency for transaction safety
- Low-balance detection

**How Inkwave uses it**:
```python
from apps.shared.integration.wallet import (
    WalletService,
    PaymentGateway,
    Currency
)

# Initialize wallet service
wallet_service = await WalletService.create(
    mongodb_uri=os.getenv("MONGODB_URI"),
    database_name="inkwave_wallets"
)

# Configure payment gateways
wallet_service.configure_stripe(
    secret_key=os.getenv("STRIPE_SECRET_KEY"),
    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
)

wallet_service.configure_paystack(
    secret_key=os.getenv("PAYSTACK_SECRET_KEY"),
    webhook_secret=os.getenv("PAYSTACK_WEBHOOK_SECRET")
)

# Create wallet on user signup
wallet = await wallet_service.create_wallet(
    user_id=user.id,
    currency=Currency.USD,
    initial_balance=2.0  # $2 free trial
)

# Debit for Q&A interaction
transaction = await wallet_service.debit(
    wallet_id=wallet.id,
    amount=0.15,  # $0.15 for question
    description=f"Q&A: {book.title}",
    idempotency_key=f"interaction-{interaction_id}",  # Prevent duplicates
    metadata={
        "book_id": str(book.id),
        "session_id": str(session.id),
        "service": "rag_qa",
        "tokens_used": result.tokens_used
    }
)

# Top-up with Stripe (international)
stripe_result = await wallet_service.initiate_stripe_topup(
    wallet_id=wallet.id,
    amount=10.0,
    success_url="https://inkwave.ailabsafrica.com/wallet/success",
    cancel_url="https://inkwave.ailabsafrica.com/wallet/cancel",
    metadata={"user_email": user.email}
)

# Top-up with Paystack (Africa)
paystack_result = await wallet_service.initiate_paystack_topup(
    wallet_id=wallet.id,
    amount=10.0,
    email=user.email,
    callback_url="https://inkwave.ailabsafrica.com/wallet/callback"
)

# Check balance before operations
wallet = await wallet_service.get_wallet_by_user(user.id)
if wallet.balance < 0.10:
    return {"error": "Insufficient balance. Please top up.", "balance": wallet.balance}

# Low balance warning
if wallet.is_low_balance:  # Property: balance < $1
    send_notification(user, "Your balance is low. Top up to continue reading.")

# Get transaction history
transactions = await wallet_service.get_transactions(
    wallet_id=wallet.id,
    limit=20,
    transaction_type=TransactionType.DEBIT  # Filter by type
)
```

**Benefits**:
- ✅ No need to build payment handling from scratch
- ✅ PCI-compliant payment processing (Stripe/Paystack SDKs)
- ✅ Idempotency prevents duplicate charges
- ✅ Multi-currency support (important for African users)
- ✅ Full audit trail with transaction history
- ✅ Webhook handling for payment verification

---

### 3. UsageCalculator (`usage_calculator.py`)

**Purpose**: Cost calculation and usage tracking

**What it provides**:
- Real-time cost calculation for RAG queries, TTS, STT, document processing
- Multiple pricing tiers (Free, Basic, Premium, Enterprise)
- Detailed cost breakdowns
- Per-service cost tracking
- Configurable pricing

**How Inkwave uses it**:
```python
from apps.shared.integration.usage_calculator import (
    UsageCalculator,
    PricingTier,
    ServiceType
)

# Initialize calculator with user's tier
usage_calculator = UsageCalculator(
    tier=user.pricing_tier  # PricingTier.BASIC by default
)

# Calculate RAG query cost
rag_cost = usage_calculator.calculate_rag_cost(
    input_tokens=user_question_tokens,  # e.g., 50
    output_tokens=ai_response_tokens,   # e.g., 250
    num_queries=1,
    retrieval_chunks=5
)
print(f"RAG cost: ${rag_cost.total_cost:.4f}")  # $0.0125

# Calculate TTS cost for narration
tts_cost = usage_calculator.calculate_tts_cost(
    num_characters=len(chunk.text),  # e.g., 500 characters
    provider="openai",  # or "elevenlabs"
    voice_id="alloy"
)
print(f"TTS cost: ${tts_cost.total_cost:.4f}")  # $0.0075

# Calculate document processing cost (one-time)
doc_cost = usage_calculator.calculate_document_processing_cost(
    num_pages=book_pdf.page_count,  # e.g., 200 pages
    file_size_mb=book_pdf.size_mb    # e.g., 5 MB
)
print(f"Processing cost: ${doc_cost.total_cost:.4f}")  # $2.00

# Get total cost breakdown
breakdown = usage_calculator.get_cost_breakdown()
print(breakdown)
# Output:
# {
#   "rag": {"queries": 10, "cost": 0.125},
#   "tts": {"characters": 5000, "cost": 0.075},
#   "total": 0.20
# }

# Show cost estimate to user BEFORE operation
estimated_cost = usage_calculator.calculate_rag_cost(
    input_tokens=estimated_tokens,
    output_tokens=estimated_tokens * 3,  # Rough estimate
    num_queries=1
)

return {
    "message": "Ready to answer your question",
    "estimated_cost": f"${estimated_cost.total_cost:.2f}",
    "will_charge": True
}
```

**Benefits**:
- ✅ Consistent cost calculation across platform
- ✅ Supports multiple pricing tiers
- ✅ Detailed cost breakdown for transparency
- ✅ Easy to update pricing without changing code
- ✅ Per-service tracking for analytics

---

### 4. DocumentProcessor (`document_processor.py`)

**Purpose**: Book processing, chunking, and metadata extraction

**What it provides**:
- Multi-format support (PDF, DOCX, TXT, Markdown)
- 4 intelligent chunking strategies:
  - Recursive character splitting
  - Sentence-aware splitting
  - Paragraph-aware splitting
  - Fixed-size splitting
- Automatic metadata extraction (page count, word count, author)
- Content cleanup and normalization
- Async batch processing with concurrency control

**How Inkwave uses it**:
```python
from apps.shared.integration.document_processor import (
    DocumentProcessor,
    ChunkingStrategy,
    DocumentType
)

# Initialize processor
doc_processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.PARAGRAPH_AWARE,  # Best for books
    chunk_size=1000,  # ~1000 chars per chunk
    chunk_overlap=200,  # Overlap to maintain context
    enable_ocr=True  # For scanned PDFs
)

# Process uploaded PDF
book_pdf_path = f"/tmp/uploads/{book_id}.pdf"
result = await doc_processor.process_file(
    file_path=book_pdf_path,
    document_type=DocumentType.PDF,
    metadata={
        "book_id": str(book_id),
        "uploaded_by": user.id,
        "title": book.title,
        "author": book.author
    }
)

# Extract processed content
book.metadata.page_count = result.metadata["page_count"]
book.metadata.word_count = result.metadata["word_count"]
book.metadata.estimated_reading_time = result.metadata["word_count"] / 200  # 200 wpm

# Store chunks in MongoDB
for i, chunk in enumerate(result.chunks):
    book_chunk = BookChunk(
        book_id=book.id,
        chunk_index=i,
        text=chunk.content,
        text_optimized=optimize_for_tts(chunk.content),  # Custom SSML
        word_count=chunk.metadata.get("word_count", 0),
        chapter_id=detect_chapter(chunk.content)  # Custom logic
    )
    await db.book_chunks.insert_one(book_chunk.dict())

# Batch processing (multiple books)
results = await doc_processor.process_batch(
    file_paths=[f"/tmp/books/{book}.pdf" for book in book_list],
    max_concurrency=3  # Process 3 at a time
)
```

**Benefits**:
- ✅ No need to build PDF extraction from scratch
- ✅ OCR support for scanned documents
- ✅ Smart chunking preserves context
- ✅ Automatic metadata extraction
- ✅ Handles edge cases (malformed PDFs, images)
- ✅ Async batch processing for efficiency

---

## ❌ Shared Services We're NOT Using (and Why)

### VAPIService (`vapi.py`)

**What it provides**:
- Voice AI agent for phone calls
- Inbound/outbound call handling
- Real-time conversation with function calling
- Call recording and transcription
- Webhook events (call.started, call.ended, etc.)

**Why Inkwave doesn't use it**:
- ❌ Inkwave is **not** a phone-based voice agent
- ❌ We use **direct TTS** (OpenAI TTS) for narration, not phone calls
- ❌ MVP is **text-based Q&A** (Phase 1)
- ❌ Voice Q&A (Phase 2) will be **in-app voice**, not phone calls

**When we might use it**:
- 📞 **Phase 3**: If we add phone-based audiobook playback
- 📞 **Future**: "Call to listen" feature (user calls a number to hear their book)

---

## 🔧 Custom Services We're Building (Inkwave-Specific)

These are **not** in shared services because they're specific to the audiobook use case:

### 1. BookService (`app/services/book_service.py`)
- Book CRUD operations
- Search and filtering
- Book detail retrieval
- **Reason**: App-specific business logic

### 2. ReadingService (`app/services/reading_service.py`)
- Reading session management
- Progress tracking
- Bookmark handling
- **Reason**: Specific to audiobook reading experience

### 3. VoiceAgentService (`app/services/voice_agent.py`)
- Orchestrates RAG + LLM for Q&A
- Builds custom prompts for book companion
- Filters results to prevent spoilers
- **Reason**: Specific orchestration logic, but USES shared RAGService under the hood

### 4. TTSService (`app/services/tts_service.py`)
- TTS audio generation wrapper
- Audio caching in S3/CDN
- SSML optimization for book narration
- **Reason**: App-specific caching and optimization

---

## 📊 Summary: Shared vs. Custom

| Service | Source | Purpose |
|---------|--------|---------|
| **RAGService** | ✅ Shared | Semantic search for Q&A |
| **WalletService** | ✅ Shared | Payments and billing |
| **UsageCalculator** | ✅ Shared | Cost calculation |
| **DocumentProcessor** | ✅ Shared | Book processing |
| BookService | ❌ Custom | Book management |
| ReadingService | ❌ Custom | Session tracking |
| VoiceAgentService | ❌ Custom (uses RAG) | Q&A orchestration |
| TTSService | ❌ Custom | Audio generation |

---

## 🎯 Key Principle

**"Share infrastructure, customize experience"**

- ✅ **Shared Services**: Core functionality (RAG, payments, processing)
- ❌ **Custom Services**: App-specific business logic and UX

This approach gives us:
1. **Fast development** - Don't rebuild what exists
2. **Consistency** - Same payment/RAG logic across platform
3. **Flexibility** - Customize UX without changing shared code
4. **Maintainability** - Update shared services benefits all apps

---

## 📝 Next Steps

1. **Test shared services integration** (see TASK.md Sprint 0)
2. **Build custom services** that orchestrate shared services
3. **Document any gaps** in shared services (feature requests)

---

**Last Updated**: 2025-10-24
