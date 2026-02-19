# Shared Services Integration Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-24
**Status**: Production Ready

## Overview

This guide shows how to integrate KasaAI shared services into your application. All shared services are production-ready, battle-tested, and follow consistent patterns.

## Table of Contents

1. [Quick Start](#quick-start)
2. [RAG Service Integration](#rag-service-integration)
3. [Document Processor Integration](#document-processor-integration)
4. [Wallet Service Integration](#wallet-service-integration)
5. [Usage Calculator Integration](#usage-calculator-integration)
6. [AI Services Integration](#ai-services-integration)
7. [VoicePipeline Integration](#voicepipeline-integration) ⭐ NEW
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

All shared services are located in `@apps/shared/integration/`:

```python
# Import from shared services
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument
from apps.shared.integration.document_processor import DocumentProcessor
from apps.shared.integration.wallet import WalletService
from apps.shared.integration.usage_calculator import UsageCalculator
from apps.shared.integration.ai_services import AIProviderService, ProviderRegistry
```

### Dependencies

Add to your `requirements.txt`:

```txt
# RAG Service
langchain>=0.1.0
langchain-core>=0.1.0
langchain-openai>=0.0.5
langchain-google-genai>=0.0.5
langchain-postgres>=0.0.5
langchain-text-splitters>=0.0.1
psycopg2-binary>=2.9.0

# Document Processing
PyPDF2>=3.0.0
pdfplumber>=0.10.0
python-docx>=1.0.0
beautifulsoup4>=4.12.0

# Wallet & Usage
pymongo>=4.6.0
stripe>=7.0.0  # Optional
```

---

## RAG Service Integration

### Overview

The RAG (Retrieval-Augmented Generation) service provides semantic search and AI-powered Q&A for any knowledge base.

**Features:**
- Multi-provider support (OpenAI, Gemini, Anthropic)
- Pgvector for efficient semantic search
- Automatic chunking and embedding
- Confidence scoring
- Escalation logic

### Basic Integration

```python
import os
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

# 1. Configure the service
config = RAGConfig(
    postgres_host="localhost",
    postgres_port="5432",
    postgres_user="postgres",
    postgres_password=os.getenv("POSTGRES_PASSWORD"),
    postgres_db="my_app_db",
    ai_provider="openai",  # or "gemini", "anthropic"
    api_key=os.getenv("OPENAI_API_KEY"),
    embedding_model="text-embedding-3-small",
    llm_model="gpt-4o-mini",
    chunk_size=1000,
    chunk_overlap=200,
    retrieval_k=3,
    confidence_threshold=0.7
)

# 2. Initialize the service
rag_service = RAGService(config)

# 3. Create knowledge base
documents = [
    KnowledgeDocument(
        title="Product Features",
        content="Our product includes AI-powered analytics, real-time dashboards, and automated reporting...",
        category="Product",
        source="docs/features.md",
        tags=["features", "analytics"]
    ),
    KnowledgeDocument(
        title="Pricing Plans",
        content="We offer three plans: Starter ($10/mo), Professional ($50/mo), Enterprise (custom)...",
        category="Pricing",
        source="docs/pricing.md",
        tags=["pricing", "plans"]
    )
]

result = await rag_service.initialize_knowledge_base(
    collection_name="product_docs",
    documents=documents
)

print(f"Indexed {result['documents_indexed']} documents, {result['chunks_created']} chunks")

# 4. Query the knowledge base
query_result = await rag_service.query_knowledge_base(
    collection_name="product_docs",
    query="What are the pricing options?",
    filters={"category": "Pricing"}  # Optional: filter by metadata
)

if query_result.success:
    print(f"Answer: {query_result.response}")
    print(f"Confidence: {query_result.confidence_score}")
    print(f"Sources: {query_result.sources_used}")

    if query_result.requires_escalation:
        print(f"Escalation needed: {query_result.escalation_reason}")
```

### Advanced Usage

#### Custom System Prompts

```python
custom_prompt = """
You are a friendly customer support assistant for ACME Corp.
Answer questions based on the knowledge base below.

Context: {context}
Question: {question}

Guidelines:
- Use a friendly, conversational tone
- If unsure, offer to connect them with a human agent
- Always mention relevant product features

Answer:
"""

result = await rag_service.query_knowledge_base(
    collection_name="support_docs",
    query="How do I reset my password?",
    system_prompt_template=custom_prompt
)
```

#### Context-Aware Queries

```python
# Pass conversation context for better responses
context = {
    "user_plan": "Professional",
    "previous_query": "billing",
    "user_location": "US"
}

result = await rag_service.query_knowledge_base(
    collection_name="support_docs",
    query="What payment methods do you accept?",
    context=context
)
```

#### Multi-Provider Support

```python
# OpenAI
openai_config = RAGConfig(
    ai_provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    embedding_model="text-embedding-3-small",
    llm_model="gpt-4o-mini",
    postgres_password=os.getenv("POSTGRES_PASSWORD")
)

# Google Gemini
gemini_config = RAGConfig(
    ai_provider="gemini",
    api_key=os.getenv("GEMINI_API_KEY"),
    embedding_model="embedding-001",
    llm_model="gemini-pro",
    postgres_password=os.getenv("POSTGRES_PASSWORD")
)

# Anthropic Claude (uses OpenAI for embeddings)
anthropic_config = RAGConfig(
    ai_provider="anthropic",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    llm_model="claude-3-sonnet-20240229",
    postgres_password=os.getenv("POSTGRES_PASSWORD")
)
```

### Production Tips

1. **Collection Naming**: Use descriptive, app-specific names
   ```python
   collection_name = f"{app_name}_{environment}_{entity_type}"
   # Example: "bookshop_prod_products"
   ```

2. **Chunking Strategy**: Adjust based on content type
   ```python
   # Technical docs: Larger chunks
   config.chunk_size = 1500
   config.chunk_overlap = 300

   # FAQ/Support: Smaller chunks
   config.chunk_size = 500
   config.chunk_overlap = 100
   ```

3. **Confidence Handling**:
   ```python
   if query_result.confidence_score < 0.5:
       # Low confidence - escalate to human
       await escalate_to_agent(query, query_result)
   elif query_result.confidence_score < 0.7:
       # Medium confidence - provide answer with disclaimer
       response = f"{query_result.response}\n\nNote: If this doesn't fully answer your question, please contact support."
   else:
       # High confidence - use answer directly
       response = query_result.response
   ```

---

## Document Processor Integration

### Overview

The Document Processor handles PDF, DOCX, TXT, and HTML files with automatic text extraction and intelligent chunking.

**Features:**
- Multi-format support (PDF, DOCX, TXT, HTML)
- Multiple PDF extraction strategies
- Smart chunking with overlap
- Metadata preservation
- Batch processing

### Basic Integration

```python
from apps.shared.integration.document_processor import (
    DocumentProcessor,
    DocumentFormat,
    ChunkingStrategy
)

# 1. Initialize processor
processor = DocumentProcessor(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy=ChunkingStrategy.SEMANTIC
)

# 2. Process a single file
result = processor.process_file(
    file_path="/path/to/document.pdf",
    document_format=DocumentFormat.PDF
)

print(f"Extracted {len(result.chunks)} chunks")
print(f"Metadata: {result.metadata}")

# 3. Access chunks
for chunk in result.chunks:
    print(f"Chunk {chunk.index}: {chunk.text[:100]}...")
    print(f"  Position: {chunk.start_char}-{chunk.end_char}")

# 4. Process from bytes (for file uploads)
with open("uploaded_file.pdf", "rb") as f:
    file_bytes = f.read()

result = processor.process_bytes(
    file_bytes=file_bytes,
    document_format=DocumentFormat.PDF,
    filename="uploaded_file.pdf"
)
```

### Advanced Usage

#### Batch Processing

```python
import asyncio
from pathlib import Path

# Process multiple files
files_to_process = [
    {
        "path": "/docs/manual.pdf",
        "format": DocumentFormat.PDF,
        "metadata": {"category": "manuals", "version": "1.0"}
    },
    {
        "path": "/docs/guide.docx",
        "format": DocumentFormat.DOCX,
        "metadata": {"category": "guides", "version": "2.1"}
    }
]

processed_documents = []

def progress_callback(current, total):
    print(f"Processing: {current}/{total} files")

results = await processor.process_batch(
    files=files_to_process,
    progress_callback=progress_callback
)

for result in results:
    if result.success:
        print(f"✅ {result.metadata.filename}: {len(result.chunks)} chunks")
    else:
        print(f"❌ {result.metadata.filename}: {result.error_message}")
```

#### Custom Chunking

```python
# Fixed-size chunking (simple, fast)
processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.FIXED_SIZE,
    chunk_size=500,
    chunk_overlap=50
)

# Semantic chunking (intelligent, preserves meaning)
processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.SEMANTIC,
    chunk_size=1000,
    chunk_overlap=200
)

# Paragraph-based chunking
processor = DocumentProcessor(
    chunking_strategy=ChunkingStrategy.PARAGRAPH,
    chunk_size=1500,
    chunk_overlap=0
)
```

#### PDF Extraction Strategies

```python
from apps.shared.integration.document_processor import PDFExtractionStrategy

# Try multiple strategies for difficult PDFs
strategies = [
    PDFExtractionStrategy.PDFPLUMBER,  # Best for tables
    PDFExtractionStrategy.PYPDF2,      # Fast, reliable
    PDFExtractionStrategy.OCR          # For scanned docs
]

for strategy in strategies:
    try:
        result = processor.process_file(
            file_path="difficult.pdf",
            document_format=DocumentFormat.PDF,
            pdf_strategy=strategy
        )
        if result.chunks:
            print(f"Success with {strategy}")
            break
    except Exception as e:
        print(f"{strategy} failed: {e}")
        continue
```

### Integration with RAG

```python
# Complete pipeline: Document Upload → Processing → RAG Indexing

from apps.shared.integration.document_processor import DocumentProcessor
from apps.shared.integration.rag import RAGService, KnowledgeDocument

async def index_document(file_path: str, category: str):
    # 1. Process document
    processor = DocumentProcessor()
    doc_result = processor.process_file(file_path)

    # 2. Convert to knowledge documents
    knowledge_docs = []
    for chunk in doc_result.chunks:
        knowledge_docs.append(KnowledgeDocument(
            title=doc_result.metadata.filename,
            content=chunk.text,
            category=category,
            source=file_path,
            metadata={
                "chunk_index": chunk.index,
                "page": chunk.page_number,
                "word_count": chunk.word_count
            }
        ))

    # 3. Index in RAG
    result = await rag_service.initialize_knowledge_base(
        collection_name="documents",
        documents=knowledge_docs
    )

    return result

# Use it
result = await index_document("/uploads/manual.pdf", "Documentation")
print(f"Indexed {result['documents_indexed']} documents")
```

---

## Wallet Service Integration

### Overview

The Wallet Service handles payments, credits, and transactions across multiple payment gateways.

**Features:**
- Multi-currency support
- Multiple payment gateways (Paystack, Stripe, MoMo)
- Transaction history
- Credit management
- Automatic conversions

### Basic Integration

```python
from apps.shared.integration.wallet import WalletService, Transaction, PaymentGateway

# 1. Initialize service
wallet_service = WalletService(
    mongodb_url=os.getenv("MONGODB_URL"),
    default_currency="USD"
)

# 2. Create user wallet
wallet = await wallet_service.create_wallet(
    user_id="user_123",
    initial_balance=0.0,
    currency="USD"
)

# 3. Add credits
transaction = await wallet_service.add_credits(
    user_id="user_123",
    amount=50.0,
    description="Plan upgrade - Professional",
    payment_gateway=PaymentGateway.STRIPE,
    transaction_ref="txn_abc123"
)

# 4. Deduct credits for usage
await wallet_service.deduct_credits(
    user_id="user_123",
    amount=5.0,
    description="API usage - 100 requests"
)

# 5. Check balance
balance = await wallet_service.get_balance("user_123")
print(f"Current balance: ${balance:.2f}")

# 6. Get transaction history
transactions = await wallet_service.get_transactions(
    user_id="user_123",
    limit=10
)
```

### Payment Gateway Integration

#### Stripe

```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Create payment intent
payment_intent = stripe.PaymentIntent.create(
    amount=5000,  # $50.00 in cents
    currency="usd",
    metadata={"user_id": "user_123"}
)

# After successful payment
if payment_intent.status == "succeeded":
    await wallet_service.add_credits(
        user_id="user_123",
        amount=50.0,
        description="Credit purchase via Stripe",
        payment_gateway=PaymentGateway.STRIPE,
        transaction_ref=payment_intent.id
    )
```

#### Paystack

```python
import requests

# Initialize Paystack payment
response = requests.post(
    "https://api.paystack.co/transaction/initialize",
    headers={"Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"},
    json={
        "amount": 5000000,  # 50,000.00 NGN in kobo
        "email": "user@example.com",
        "metadata": {"user_id": "user_123"}
    }
)

# Verify payment callback
def verify_paystack_payment(reference):
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"}
    )

    if response.json()["data"]["status"] == "success":
        await wallet_service.add_credits(
            user_id="user_123",
            amount=50.0,
            description="Credit purchase via Paystack",
            payment_gateway=PaymentGateway.PAYSTACK,
            transaction_ref=reference
        )
```

---

## Usage Calculator Integration

### Overview

The Usage Calculator tracks and calculates costs for all service usage.

**Features:**
- Per-endpoint cost tracking
- Multiple pricing tiers
- Automatic cost calculation
- Usage aggregation
- Billing period support

### Basic Integration

```python
from apps.shared.integration.usage_calculator import UsageCalculator, UsageTier

# 1. Initialize calculator
calculator = UsageCalculator()

# 2. Calculate costs for different operations
rag_cost = calculator.calculate_rag_query_cost(
    tokens_used=150,
    tier=UsageTier.PROFESSIONAL
)
print(f"RAG query cost: ${rag_cost:.4f}")

tts_cost = calculator.calculate_tts_cost(
    characters=500,
    voice_type="premium",
    tier=UsageTier.PROFESSIONAL
)
print(f"TTS cost: ${tts_cost:.4f}")

# 3. Track usage
await calculator.track_usage(
    user_id="user_123",
    service="rag",
    operation="query",
    cost=rag_cost,
    metadata={
        "tokens": 150,
        "collection": "support_docs",
        "query": "How do I reset password?"
    }
)

# 4. Get usage summary
summary = await calculator.get_usage_summary(
    user_id="user_123",
    start_date=datetime.now() - timedelta(days=30)
)

print(f"Total cost (30 days): ${summary['total_cost']:.2f}")
print(f"Total requests: {summary['total_requests']}")
print(f"Cost by service: {summary['by_service']}")
```

### Custom Pricing Tiers

```python
# Define custom pricing
custom_pricing = {
    "rag_query": {
        UsageTier.FREE: 0.001,
        UsageTier.STARTER: 0.0008,
        UsageTier.PROFESSIONAL: 0.0005,
        UsageTier.ENTERPRISE: 0.0003
    },
    "tts_character": {
        UsageTier.FREE: 0.00002,
        UsageTier.STARTER: 0.000015,
        UsageTier.PROFESSIONAL: 0.00001,
        UsageTier.ENTERPRISE: 0.000005
    }
}

calculator = UsageCalculator(custom_pricing=custom_pricing)
```

---

## AI Services Integration

### Overview

The AI Services framework provides provider-agnostic access to TTS, ASR, and LLM services with health monitoring and failover.

**Features:**
- Multi-provider support
- Health monitoring
- Automatic failover
- Capability filtering
- Real-time status tracking

### Basic Integration

```python
from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    ProviderType,
    AIProvider,
    ProviderCapabilities
)

# 1. Create provider registry
registry = ProviderRegistry()

# 2. Register TTS providers
coqui_provider = AIProvider(
    id="coqui_xtts",
    name="Coqui XTTS v2",
    provider_type=ProviderType.TTS,
    endpoint="https://coqui.ailabsafrica.com",
    capabilities=ProviderCapabilities(
        voiceCloning=True,
        multiLanguage=True,
        streaming=True
    ),
    languages=10,
    languageList=["en", "es", "fr", "de", "it"]
)
registry.register_provider(coqui_provider)

# 3. Create service
tts_service = AIProviderService(
    provider_type=ProviderType.TTS,
    registry=registry
)

# 4. Get available providers
providers = registry.get_all_providers()
for provider_id, provider in providers.items():
    print(f"{provider.name}: {provider.status}")

# 5. Filter by capability
voice_cloning_providers = registry.get_providers_by_capability("voiceCloning")
print(f"Providers with voice cloning: {len(voice_cloning_providers)}")

# 6. Health check
provider = registry.get_provider("coqui_xtts")
health_result = await tts_service.check_health(provider)
print(f"Health: {health_result['status']}, Response time: {health_result['response_time']}ms")
```

### Health Monitoring

```python
from apps.shared.integration.ai_services import HealthMonitorService

# 1. Create health monitor
health_monitor = HealthMonitorService(
    registry=registry,
    check_interval=60,  # Check every 60 seconds
    timeout=5
)

# 2. Register alert callback
async def on_provider_down(provider_id, result):
    print(f"⚠️ Provider {provider_id} is down!")
    # Send alert to admin
    await send_alert_email(f"Provider {provider_id} health check failed")

health_monitor.register_alert_callback(on_provider_down)

# 3. Start monitoring
await health_monitor.start_monitoring()

# 4. Check all providers manually
results = await health_monitor.check_all_providers()
for result in results:
    print(f"{result.provider_id}: {result.status} ({result.response_time_ms}ms)")

# 5. Get metrics
metrics = health_monitor.get_metrics("coqui_xtts")
print(f"Uptime: {metrics.uptime_percentage:.1f}%")
print(f"Avg response time: {metrics.avg_response_time_ms:.0f}ms")
```

---

## VoicePipeline Integration

### Overview

The VoicePipeline service provides unified voice conversation handling with automatic VAD → STT → LLM → TTS flow. Eliminates manual state machine complexity and provides consistent behavior across multiple transport protocols (WebRTC, WebSocket, PSTN, SIP).

**Features:**
- Unified conversation flow
- Voice Activity Detection (VAD) with Silero v5
- Speech-to-Text with Faster Whisper
- LLM response generation
- Streaming TTS with Parler-TTS
- 10x code reduction vs manual state machines
- Production-ready and tested

**Status:** ✅ Production Ready (Phase 3 Complete)

### Basic Integration

```python
from apps.shared.integration.voice_pipeline import create_voice_pipeline

# 1. Create pipeline for an assistant
pipeline = create_voice_pipeline(
    assistant_id="asst_123abc",
    pause_threshold_ms=1500,  # 1.5s pause triggers turn completion
    sample_rate=16000          # 16kHz audio
)

# 2. Prepare audio stream
async def audio_stream():
    """Yield PCM audio chunks as bytes"""
    for chunk in your_audio_source:
        yield chunk  # bytes of PCM audio

# 3. Process conversation turn
async for message in pipeline.process_turn(audio_stream()):
    # Handle messages based on type
    if message["type"] == "transcription":
        user_text = message["data"]["text"]
        print(f"User said: {user_text}")

    elif message["type"] == "text_response":
        assistant_text = message["data"]
        print(f"Assistant: {assistant_text}")

    elif message["type"] == "audio_chunk":
        audio_base64 = message["data"]
        # Play or send audio chunk to client
        play_audio(audio_base64)

    elif message["type"] == "audio_complete":
        chunks = message["data"]["chunks"]
        print(f"Audio complete: {chunks} chunks")

    elif message["type"] == "error":
        error_msg = message["data"]
        print(f"Error: {error_msg}")

# 4. Reset for new conversation
pipeline.reset()
```

### WebSocket Integration Example

```python
from fastapi import WebSocket
from apps.shared.integration.voice_pipeline import create_voice_pipeline

@app.websocket("/ws/voice/{assistant_id}")
async def voice_chat(websocket: WebSocket, assistant_id: str):
    await websocket.accept()

    # Create pipeline
    pipeline = create_voice_pipeline(assistant_id)

    audio_buffer = []

    while True:
        message = await websocket.receive_json()

        if message["type"] == "pcm_chunk":
            # Collect audio
            audio_buffer.append(message["data"])

        elif message["type"] == "turn_complete":
            # Process turn
            async def audio_stream():
                for pcm_base64 in audio_buffer:
                    yield base64.b64decode(pcm_base64)

            # Stream results back to client
            async for pipeline_msg in pipeline.process_turn(audio_stream()):
                await websocket.send_json(pipeline_msg)

            audio_buffer.clear()
```

### WebRTC Integration Example

```python
from fastrtc import Stream, ReplyOnPause
from apps.shared.integration.voice_pipeline import VoicePipeline
import asyncio

class WebRTCVoiceAgent:
    """WebRTC handler using VoicePipeline"""

    def __init__(self, assistant_id: str):
        self.pipeline = VoicePipeline(assistant_id)

    def __call__(self, audio: tuple[int, np.ndarray]):
        """Handle audio from WebRTC (synchronous)"""
        sample_rate, audio_data = audio

        # Process through pipeline
        response_chunks = asyncio.run(
            self._process_audio(audio_data, sample_rate)
        )

        # Yield response audio
        for chunk in response_chunks:
            yield (sample_rate, chunk)

    async def _process_audio(self, audio_data, sample_rate):
        """Process audio through VoicePipeline"""
        if not self.pipeline:
            self.pipeline = VoicePipeline(
                assistant_id=self.assistant_id,
                sample_rate=sample_rate
            )

        async def audio_stream():
            yield audio_data.tobytes()

        response_chunks = []
        async for message in self.pipeline.process_turn(audio_stream()):
            if message["type"] == "audio_chunk":
                # Extract PCM from base64 WAV
                wav_bytes = base64.b64decode(message["data"])
                pcm_array = np.frombuffer(wav_bytes[44:], dtype=np.int16)
                response_chunks.append(pcm_array)

        return response_chunks

# Create FastRTC Stream
agent = WebRTCVoiceAgent(assistant_id)
stream = Stream(handler=ReplyOnPause(agent), modality="audio")
```

### Message Types Reference

| Type | Direction | Data Structure | Description |
|------|-----------|---------------|-------------|
| `transcription` | Server → Client | `{"text": str, "is_final": bool}` | User's transcribed speech |
| `text_response` | Server → Client | `string` | Assistant's text response |
| `audio_chunk` | Server → Client | `string` (base64 WAV) | Audio chunk to play |
| `audio_complete` | Server → Client | `{"chunks": int, "streaming": bool}` | Audio streaming complete |
| `error` | Server → Client | `string` | Error message |

### Configuration Options

```python
from apps.shared.integration.voice_pipeline import VoicePipeline

pipeline = VoicePipeline(
    assistant_id="asst_123abc",       # Required: MongoDB assistant ID
    pause_threshold_ms=1500,          # Optional: VAD pause threshold (default: 1500ms)
    sample_rate=16000                 # Optional: Audio sample rate (default: 16000Hz)
)
```

**Pause Threshold:**
- Lower values (800-1200ms): More responsive, may cut off speaker
- Higher values (1500-2000ms): More natural, slight delay
- Recommended: 1500ms for general conversations

**Sample Rate:**
- 16000 Hz: Standard for voice conversations (recommended)
- 24000 Hz: Higher quality for music/broadcast
- 8000 Hz: Phone quality (not recommended)

### Advanced: Custom Components

You can extend VoicePipeline by overriding internal methods:

```python
class CustomVoicePipeline(VoicePipeline):
    """Custom pipeline with enhanced features"""

    async def _transcribe(self, audio: np.ndarray) -> str:
        """Custom transcription with language detection"""
        # Your custom STT implementation
        transcription = await super()._transcribe(audio)

        # Post-process
        detected_lang = detect_language(transcription)
        self.detected_language = detected_lang

        return transcription

    async def _generate_response(self, text: str) -> str:
        """Custom response with sentiment analysis"""
        # Analyze sentiment
        sentiment = analyze_sentiment(text)

        # Adjust system prompt based on sentiment
        if sentiment == "negative":
            system_prompt = "Be extra empathetic..."
        else:
            system_prompt = self.assistant.system_prompt

        # Generate response
        return await generate_llm_response(text, system_prompt)
```

### Performance Metrics

**Latency:**
- First audio chunk: <1.5s
- Audio chunk streaming: Incremental (40-60% faster than buffered)
- Total turn time: 2-4s (depends on audio length and LLM)

**Resource Usage:**
- Memory: ~500MB per active pipeline (models loaded once)
- CPU: Minimal (GPU-accelerated for STT/TTS)
- GPU: ~2GB VRAM per active conversation

### Troubleshooting

**Issue: Pipeline hangs during turn processing**
```python
# Solution: Add timeout
import asyncio

try:
    async with asyncio.timeout(30):  # 30 second timeout
        async for message in pipeline.process_turn(audio_stream()):
            await handle_message(message)
except asyncio.TimeoutError:
    logger.error("Pipeline timeout - resetting")
    pipeline.reset()
```

**Issue: Audio quality is poor**
```python
# Solution: Verify audio format
# Ensure PCM audio is:
# - 16-bit signed integer
# - Single channel (mono)
# - Correct sample rate (16000 Hz)

# Convert if needed
import numpy as np
audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
```

**Issue: VAD not detecting speech**
```python
# Solution: Adjust pause threshold
pipeline = create_voice_pipeline(
    assistant_id=assistant_id,
    pause_threshold_ms=800  # Lower threshold for faster detection
)
```

### Dependencies

```txt
# VoicePipeline core
numpy>=1.24.0
torch>=2.0.0

# VAD
silero-vad>=5.0.0

# STT
faster-whisper>=0.10.0

# TTS
parler-tts>=0.1.0

# LLM (choose one)
openai>=1.0.0
anthropic>=0.8.0
google-generativeai>=0.3.0
```

### Production Checklist

- [ ] Assistant configured in MongoDB with system_prompt, voice settings
- [ ] VAD pause threshold tuned for your use case
- [ ] Audio format validated (PCM 16-bit, 16kHz)
- [ ] Error handling implemented for pipeline messages
- [ ] Timeout configured for long conversations
- [ ] Monitoring/logging added for pipeline metrics
- [ ] Load testing performed for concurrent conversations
- [ ] GPU resources allocated if using local STT/TTS

### Real-World Examples

**Example 1: Customer Support Bot**
```python
pipeline = create_voice_pipeline(
    assistant_id="support_bot_123",
    pause_threshold_ms=1200,  # Quick responses
    sample_rate=16000
)
```

**Example 2: Interview Assistant**
```python
pipeline = create_voice_pipeline(
    assistant_id="interview_bot_456",
    pause_threshold_ms=2000,  # Let speaker finish thoughts
    sample_rate=16000
)
```

**Example 3: Language Learning**
```python
pipeline = create_voice_pipeline(
    assistant_id="language_tutor_789",
    pause_threshold_ms=1500,
    sample_rate=16000
)
```

### Related Documentation

- **Architecture:** `/opt/kasaai/apps/architecture/VOICE_PIPELINE_ARCHITECTURE.md`
- **Source Code:** `/opt/kasaai/apps/shared/integration/voice_pipeline.py`
- **WebRTC Handler:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/webrtc_voice.py`
- **WebSocket v2:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_v2.py`

---

## Best Practices

### 1. Environment Configuration

```python
# Use environment variables for all credentials
import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "postgres_password": os.getenv("POSTGRES_PASSWORD"),
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "mongodb_url": os.getenv("MONGODB_URL"),
    "stripe_secret_key": os.getenv("STRIPE_SECRET_KEY")
}

# Never hardcode credentials!
```

### 2. Error Handling

```python
from apps.shared.integration.rag import RAGService

try:
    result = await rag_service.query_knowledge_base(
        collection_name="docs",
        query="What is the refund policy?"
    )

    if not result.success:
        logger.error(f"RAG query failed: {result.error_message}")
        return fallback_response()

    return result.response

except Exception as e:
    logger.exception("Unexpected error in RAG query")
    return error_response("Service temporarily unavailable")
```

### 3. Resource Management

```python
# Use context managers for services with connections
async with WalletService(mongodb_url=os.getenv("MONGODB_URL")) as wallet:
    await wallet.deduct_credits(user_id, amount)

# Or explicit cleanup
wallet_service = WalletService(mongodb_url=os.getenv("MONGODB_URL"))
try:
    result = await wallet_service.add_credits(user_id, amount)
finally:
    await wallet_service.close()
```

### 4. Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log important operations
logger.info(f"RAG query: user={user_id}, query='{query[:50]}...'")
logger.debug(f"Retrieved {len(docs)} documents from vector store")
logger.warning(f"Low confidence ({confidence:.2f}) for query: {query}")
logger.error(f"Failed to process document: {error}")
```

### 5. Caching

```python
from functools import lru_cache
import asyncio

# Cache expensive operations
@lru_cache(maxsize=100)
def get_cached_response(query: str, collection: str):
    # Check cache before querying RAG
    pass

# Or use Redis for distributed caching
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

async def query_with_cache(query: str):
    cache_key = f"rag:{hash(query)}"
    cached = cache.get(cache_key)

    if cached:
        return json.loads(cached)

    result = await rag_service.query_knowledge_base("docs", query)
    cache.setex(cache_key, 3600, json.dumps(result.dict()))  # 1 hour TTL

    return result
```

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'langchain_core'"

**Solution**:
```bash
pip install langchain langchain-core langchain-openai langchain-postgres
```

#### 2. "Connection refused" for PostgreSQL

**Solution**:
```python
# Check connection string format
connection_string = (
    f"postgresql://{user}:{password}@{host}:{port}/{database}"
)

# Ensure PostgreSQL is running
# Ubuntu: sudo systemctl status postgresql
# Docker: docker ps | grep postgres
```

#### 3. "PgVector extension not found"

**Solution**:
```sql
-- Connect to PostgreSQL
psql -U postgres -d your_database

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

#### 4. Low RAG confidence scores

**Solution**:
```python
# 1. Reduce similarity threshold
config.similarity_threshold = 0.2  # Lower = more results

# 2. Increase retrieval results
config.retrieval_k = 5  # Get more context

# 3. Improve document quality
# - Add more relevant documents
# - Ensure proper formatting
# - Include metadata for filtering
```

#### 5. Slow document processing

**Solution**:
```python
# Use batch processing for multiple files
results = await processor.process_batch(
    files=file_list,
    max_workers=4  # Parallel processing
)

# Reduce chunk size for faster processing
processor = DocumentProcessor(chunk_size=500)

# For PDFs, try faster strategy
result = processor.process_file(
    file_path="doc.pdf",
    pdf_strategy=PDFExtractionStrategy.PYPDF2  # Faster than pdfplumber
)
```

---

## Support

For issues or questions:

1. **Documentation**: Check this guide first
2. **Tests**: See `@apps/shared/tests/` for working examples
3. **Issues**: Report at [GitHub Issues](https://github.com/your-org/kasaai/issues)
4. **Team**: Contact the platform team on Slack

---

**Happy Integrating!** 🚀
