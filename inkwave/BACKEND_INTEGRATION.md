# Inkwave - Backend Integration Guide

**Purpose**: This document explains how to integrate the Inkwave frontend with the backend using services from `@apps/shared/`.

**Last Updated**: 2025-10-24

---

## 🎯 Overview

Inkwave leverages shared services for:
- **STT (Speech-to-Text)**: OpenAI Whisper via AI Provider Service
- **RAG (Retrieval Augmented Generation)**: Gemini 2.5 Flash via RAGService & GeminiService
- **TTS (Text-to-Speech)**: OpenAI TTS for Q&A, Coqui XTTS v2 for narration

All these services are available in `@apps/shared/integration/`.

---

## 📁 Shared Services Architecture

```
@apps/shared/integration/
├── gemini_service.py       # Gemini 2.5 Flash LLM integration
├── rag.py                  # RAG pipeline (embeddings + retrieval + generation)
├── ai_services/            # AI provider abstraction layer
│   ├── stt_service.py      # Speech-to-Text (Whisper)
│   └── tts_service.py      # Text-to-Speech (OpenAI TTS, Coqui XTTS)
├── wallet.py               # Wallet & billing (Stripe/Paystack)
├── usage_calculator.py     # Usage tracking & cost calculation
└── document_processor.py   # Book processing & chunking
```

---

## 🔧 Backend Setup

### 1. Import Shared Services

```python
# backend/main.py or backend/app/api/v1/voice.py
import sys
sys.path.append('/opt/kasaai/apps/shared')

from integration.gemini_service import GeminiService
from integration.rag import RAGService, RAGConfig
from integration.ai_services.stt_service import STTService
from integration.ai_services.tts_service import TTSService
from integration.wallet import WalletService
from integration.usage_calculator import UsageCalculator
```

### 2. Configure Services

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini Configuration
gemini_service = GeminiService(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.5-flash"  # 2M token context window
)

# RAG Configuration
rag_config = RAGConfig(
    ai_provider="gemini",
    api_key=os.getenv("GEMINI_API_KEY"),
    embedding_model="text-embedding-004",
    llm_model="gemini-2.5-flash",
    retrieval_k=5,              # Top 5 relevant chunks
    confidence_threshold=0.7,    # Min similarity score
    temperature=0.1              # Low temperature for factual answers
)
rag_service = RAGService(rag_config)

# STT Configuration (Whisper)
stt_service = STTService(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY")
)

# TTS Configuration
tts_service = TTSService(
    provider="openai",          # Use OpenAI for Q&A
    api_key=os.getenv("OPENAI_API_KEY"),
    voice="nova",               # OpenAI voice: alloy, echo, fable, onyx, nova, shimmer
    model="tts-1"               # Fast, good quality
)

# Wallet & Usage
wallet_service = WalletService()
usage_calculator = UsageCalculator()
```

---

## 🎙️ Voice Q&A Pipeline

### Step 1: Speech-to-Text (STT)

**Endpoint**: `POST /api/v1/voice/transcribe`

```python
from fastapi import UploadFile, File
from integration.ai_services.stt_service import STTService

@router.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Convert audio to text using Whisper.

    Cost: ~$0.01 per 15 seconds
    """
    # Save uploaded audio temporarily
    audio_bytes = await audio.read()

    # Transcribe using Whisper
    transcript = await stt_service.transcribe(audio_bytes)

    # Calculate cost (Whisper: $0.006/minute)
    duration_seconds = get_audio_duration(audio_bytes)
    cost_credits = usage_calculator.calculate_stt_cost(duration_seconds)

    # Deduct from wallet
    await wallet_service.deduct_credits(user_id, cost_credits)

    return {
        "transcript": transcript,
        "duration_seconds": duration_seconds,
        "cost_credits": cost_credits
    }
```

### Step 2: RAG Query (Gemini 2.5 Flash)

**Endpoint**: `POST /api/v1/voice/ask`

```python
@router.post("/voice/ask")
async def voice_ask(
    question: str,
    book_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Answer question using RAG with Gemini 2.5 Flash.

    Cost: ~$0.0003 per query
    """
    # Retrieve book context from vector DB
    context = await rag_service.retrieve(
        query=question,
        collection=f"book_{book_id}",
        k=5
    )

    # Generate answer using Gemini 2.5 Flash
    answer = await rag_service.generate(
        query=question,
        context=context,
        book_id=book_id
    )

    # Calculate RAG cost
    # Gemini 2.5 Flash: $0.30 per 1M input tokens, $1.20 per 1M output tokens
    # Average: ~1000 tokens total = ~$0.0003
    cost_credits = usage_calculator.calculate_rag_cost(
        input_tokens=len(context.split()) * 1.3,  # Estimate
        output_tokens=len(answer.split()) * 1.3
    )

    # Deduct from wallet
    await wallet_service.deduct_credits(user_id, cost_credits)

    return {
        "question": question,
        "answer": answer,
        "cost_credits": cost_credits
    }
```

### Step 3: Text-to-Speech (TTS)

**Endpoint**: `POST /api/v1/voice/synthesize`

```python
@router.post("/voice/synthesize")
async def synthesize_answer(
    text: str,
    user_id: str = Depends(get_current_user)
):
    """
    Convert answer text to speech using OpenAI TTS.

    Cost: ~$0.03 per minute (~$0.015 per 1000 characters)
    """
    # Generate speech
    audio_bytes = await tts_service.synthesize(text)

    # Calculate TTS cost
    # OpenAI TTS: $15 per 1M characters
    cost_credits = usage_calculator.calculate_tts_cost(len(text))

    # Deduct from wallet
    await wallet_service.deduct_credits(user_id, cost_credits)

    # Upload to storage and return URL
    audio_url = await upload_to_storage(audio_bytes, user_id)

    return {
        "audio_url": audio_url,
        "cost_credits": cost_credits
    }
```

### Complete Voice Q&A Endpoint

```python
@router.post("/voice/qa")
async def voice_qa(
    audio: UploadFile = File(...),
    book_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Complete voice Q&A pipeline: STT → RAG → TTS

    Total Cost: ~$0.04 per question
    """
    total_cost = 0

    # Step 1: Transcribe audio to text
    audio_bytes = await audio.read()
    transcript = await stt_service.transcribe(audio_bytes)
    duration_seconds = get_audio_duration(audio_bytes)
    stt_cost = usage_calculator.calculate_stt_cost(duration_seconds)
    total_cost += stt_cost

    # Step 2: Get answer from RAG
    context = await rag_service.retrieve(
        query=transcript,
        collection=f"book_{book_id}",
        k=5
    )
    answer = await rag_service.generate(
        query=transcript,
        context=context,
        book_id=book_id
    )
    rag_cost = usage_calculator.calculate_rag_cost(1000, 200)  # Estimate
    total_cost += rag_cost

    # Step 3: Synthesize answer to audio
    audio_bytes = await tts_service.synthesize(answer)
    tts_cost = usage_calculator.calculate_tts_cost(len(answer))
    total_cost += tts_cost

    # Deduct total from wallet
    await wallet_service.deduct_credits(user_id, total_cost)

    # Upload audio to storage
    audio_url = await upload_to_storage(audio_bytes, user_id)

    # Save to conversation history
    await save_conversation(user_id, book_id, transcript, answer)

    return {
        "question": transcript,
        "answer": answer,
        "audio_url": audio_url,
        "costs": {
            "stt": stt_cost,
            "rag": rag_cost,
            "tts": tts_cost,
            "total": total_cost
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📚 Book Indexing for RAG

### Step 1: Process & Chunk Book

```python
from integration.document_processor import DocumentProcessor

processor = DocumentProcessor()

# Process book (PDF, EPUB, etc.)
chunks = await processor.process_book(
    file_path="/path/to/book.pdf",
    chunk_size=1000,        # ~1000 characters per chunk
    overlap=200             # 200 character overlap
)

# chunks = [
#     {"text": "...", "metadata": {"chapter": 1, "page": 5}},
#     ...
# ]
```

### Step 2: Generate Embeddings & Store

```python
# Generate embeddings using Gemini
for chunk in chunks:
    embedding = await gemini_service.generate_embedding(
        text=chunk["text"],
        model="text-embedding-004"  # 768 dimensions
    )

    # Store in pgvector
    await db.execute(
        """
        INSERT INTO book_embeddings (book_id, chunk_text, embedding, metadata)
        VALUES ($1, $2, $3, $4)
        """,
        book_id,
        chunk["text"],
        embedding,
        json.dumps(chunk["metadata"])
    )
```

### Step 3: Query RAG

```python
# User asks question
question = "What is the main theme of the book?"

# Generate question embedding
question_embedding = await gemini_service.generate_embedding(
    text=question,
    model="text-embedding-004"
)

# Retrieve top 5 similar chunks using cosine similarity
chunks = await db.fetch(
    """
    SELECT chunk_text, metadata, 1 - (embedding <=> $1) AS similarity
    FROM book_embeddings
    WHERE book_id = $2
    ORDER BY similarity DESC
    LIMIT 5
    """,
    question_embedding,
    book_id
)

# Generate answer using Gemini 2.5 Flash
context = "\n\n".join([chunk["chunk_text"] for chunk in chunks])
prompt = f"""
Based on the following context from the book, answer the question.

Context:
{context}

Question: {question}

Answer:
"""

answer = await gemini_service.generate_content(
    prompt=prompt,
    temperature=0.1,  # Factual answers
    max_output_tokens=500
)
```

---

## 💰 Cost Tracking

```python
from integration.usage_calculator import UsageCalculator

calculator = UsageCalculator()

# STT (Whisper)
stt_cost = calculator.calculate_stt_cost(duration_seconds=30)
# ~60 credits ($0.60) for 30 seconds

# RAG (Gemini 2.5 Flash)
rag_cost = calculator.calculate_rag_cost(
    input_tokens=1000,   # Context + question
    output_tokens=200    # Answer
)
# ~30 credits ($0.30) per query

# TTS (OpenAI)
tts_cost = calculator.calculate_tts_cost(character_count=500)
# ~750 credits ($7.50) per 500 characters

# Narration (Coqui XTTS v2 - pre-generated)
narration_cost = calculator.calculate_narration_cost(duration_minutes=60)
# 120 credits ($1.20) per hour
```

---

## 🔐 Environment Variables

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Supabase (Auth)
SUPABASE_URL=https://supabase.ailabsafrica.com/project/default
SUPABASE_ANON_KEY=your_supabase_anon_key

# Database
MONGODB_URI=mongodb://localhost:27017/inkwave
POSTGRES_URI=postgresql://user:pass@localhost:5432/inkwave  # pgvector

# Payment Gateways
STRIPE_API_KEY=your_stripe_key
PAYSTACK_API_KEY=your_paystack_key
```

---

## 🧪 Testing

```python
# Test STT
audio_file = open("test_audio.mp3", "rb")
transcript = await stt_service.transcribe(audio_file.read())
print(f"Transcript: {transcript}")

# Test RAG
answer = await rag_service.query(
    question="What is the main theme?",
    book_id="test_book_id"
)
print(f"Answer: {answer}")

# Test TTS
audio = await tts_service.synthesize("Hello, this is a test.")
with open("test_output.mp3", "wb") as f:
    f.write(audio)
```

---

## 📊 Cost Estimates

| Service | Cost per Unit | Credits per Unit |
|---------|---------------|------------------|
| STT (Whisper) | $0.006/minute | 60 credits/min |
| RAG (Gemini) | ~$0.0003/query | ~30 credits/query |
| TTS (OpenAI) | $0.015/1000 chars | ~1.5 credits/1000 chars |
| Narration (Coqui) | $0.02/minute | 2 credits/min |

**Average Voice Q&A**: ~4000 credits ($0.04)

---

## 🚀 Deployment Checklist

- [ ] Set up pgvector extension in PostgreSQL
- [ ] Index all books with embeddings
- [ ] Configure Gemini API key
- [ ] Configure OpenAI API key
- [ ] Set up Stripe/Paystack webhooks
- [ ] Deploy FastAPI backend
- [ ] Test STT → RAG → TTS pipeline
- [ ] Monitor usage and costs
- [ ] Set up rate limiting
- [ ] Implement caching for common questions

---

## 📝 Notes

- **Gemini 2.5 Flash** is used for both embeddings and generation for consistency and cost-effectiveness
- **OpenAI Whisper** is the most accurate STT option available
- **OpenAI TTS** provides natural-sounding voices for Q&A
- **Coqui XTTS v2** is used for pre-generated narration (cost-effective for bulk generation)
- All costs are tracked per-user and deducted from wallet in real-time
- RAG context window: Up to 2M tokens with Gemini 2.5 Flash (entire books can fit!)

---

**Status**: Documentation complete. Backend endpoints ready for implementation.

**Next**: Deploy FastAPI backend and connect to frontend API client at `src/lib/api.ts`.
