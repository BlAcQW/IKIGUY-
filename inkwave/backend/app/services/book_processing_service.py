"""
Book Processing Service.

Handles PDF/EPUB processing, chapter extraction, and embedding generation.
Integrates with shared DocumentProcessor for text extraction.

Now uses shared document_processing module for:
- Topic extraction (AI-powered)
- Collection naming (organization-scoped)
- Processing status models

Features detailed logging and progress tracking for frontend display.
"""

import logging
import sys
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

from shared.integration.document_processor import DocumentProcessor
from shared.document_processing import (
    TopicExtractor,
    CollectionNaming,
    ProcessingStatus,
)

from app.core.config import settings
from app.core.database import get_db
from app.models.book import Book, BookChunk, BookMetadata, BookChapter
from app.services.rag_service import get_rag_service
from app.services.embedding_service import get_embedding_service
from app.services.content_classification_service import (
    get_content_classification_service,
    ContentClassificationService,
    NarrationPreferences
)

logger = logging.getLogger(__name__)

# Shared topic extractor for automatic topic generation
_topic_extractor = TopicExtractor()


class BookProcessingService:
    """
    Service for processing book files (PDF, EPUB).

    Handles:
    - Text extraction
    - Chapter detection
    - Chunking
    - Embedding generation
    - Storage in MongoDB

    Provides detailed progress updates for frontend tracking.
    """

    def __init__(self):
        """Initialize book processing service."""
        self.document_processor = None
        self._initialized = False

    async def initialize(self):
        """
        Initialize document processor.

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            self.document_processor = DocumentProcessor(
                chunking_strategy="recursive",
                chunk_size=1000,
                chunk_overlap=200,
                min_chunk_size=100,
                max_chunk_size=2000,
                clean_text=True,
                extract_metadata=True
            )
            self._initialized = True
            logger.info("✅ Book Processing Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize book processing service: {e}")
            raise

    async def _update_progress(
        self,
        book_id: str,
        stage: str,
        progress: int,
        message: str,
        status: str = "processing"
    ):
        """
        Update book processing progress in the database.

        Args:
            book_id: Book identifier
            stage: Current processing stage
            progress: Progress percentage (0-100)
            message: Human-readable status message
            status: Processing status (processing, ready, error)
        """
        db = get_db()
        await db.books.update_one(
            {"book_id": book_id},
            {
                "$set": {
                    "processing_stage": stage,
                    "processing_progress": progress,
                    "processing_message": message,
                    "processing_status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"📊 [{book_id}] {stage}: {progress}% - {message}")

    async def process_book_file(
        self,
        file_path: str,
        book_metadata: Dict[str, Any],
        uploaded_by: str,
        book_id: Optional[str] = None,
        use_ai_chapter_detection: bool = False
    ) -> Book:
        """
        Process a book file (PDF or EPUB).

        Args:
            file_path: Path to book file
            book_metadata: Metadata (title, author, description, etc.)
            uploaded_by: User ID who uploaded
            book_id: Optional pre-generated book ID (for background tasks)
            use_ai_chapter_detection: If True, use Gemini AI for enhanced chapter detection

        Returns:
            Book model with processing status

        Raises:
            Exception: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        # Use provided book_id or generate new one
        if not book_id:
            book_id = f"book_{uuid.uuid4().hex[:12]}"

        db = get_db()

        # Check if book record already exists (created by upload endpoint)
        existing_book = await db.books.find_one({"book_id": book_id})

        if not existing_book:
            # Create initial book record
            book = Book(
                book_id=book_id,
                title=book_metadata["title"],
                author=book_metadata["author"],
                cover_url=book_metadata.get("cover_url"),
                pdf_url=file_path,
                processed=False,
                processing_status="processing",
                processing_stage="initializing",
                processing_progress=0,
                processing_message="Starting book processing...",
                uploaded_by=uploaded_by,
                metadata=BookMetadata()
            )
            await db.books.insert_one(book.model_dump())
            logger.info(f"📚 Created book record: {book_id}")
        else:
            logger.info(f"📚 Using existing book record: {book_id}")

        try:
            # Stage 1: Extract text (10-30%)
            # Start from 10% if book was already created by upload endpoint
            # Otherwise start from 5%
            initial_progress = 10 if existing_book else 5
            await self._update_progress(
                book_id, "extracting", initial_progress,
                "Extracting text from PDF..."
            )

            logger.info(f"📄 [{book_id}] Processing file: {file_path}")
            result = await self.document_processor.process_file(file_path)

            await self._update_progress(
                book_id, "extracting", 20,
                f"Text extracted successfully"
            )

            # Stage 2: Process metadata (20-30%)
            await self._update_progress(
                book_id, "metadata", 25,
                "Processing book metadata..."
            )

            page_count = result.metadata.page_count if hasattr(result, 'metadata') and hasattr(result.metadata, 'page_count') else 0
            word_count = result.metadata.word_count if hasattr(result, 'metadata') and hasattr(result.metadata, 'word_count') else len(result.raw_text.split())
            reading_time = int(word_count / 200)  # 200 words per minute

            logger.info(f"📊 [{book_id}] Metadata: {page_count} pages, {word_count} words, ~{reading_time} min read")

            await self._update_progress(
                book_id, "metadata", 30,
                f"Found {page_count} pages, {word_count} words"
            )

            # Stage 3: Chunking (30-50%)
            await self._update_progress(
                book_id, "chunking", 35,
                "Splitting text into chunks..."
            )

            chunks_data = result.chunks if hasattr(result, 'chunks') else []
            logger.info(f"📦 [{book_id}] Extracted {len(chunks_data)} raw chunks")

            # Initialize content classification service
            classification_service = get_content_classification_service()

            # Create title/author introduction chunk
            intro_chunk = None
            if book_metadata.get('title') and book_metadata.get('author'):
                title = book_metadata['title']
                author = book_metadata['author']
                title_author_text = f"{title} by {author}."
                intro_chunk = {
                    'content': title_author_text,
                    'type': 'intro',
                    'content_type': 'narrative',
                    'narratable': True
                }
                logger.info(f"📝 [{book_id}] Created title/author introduction chunk")

            await self._update_progress(
                book_id, "chunking", 40,
                "Classifying content for professional narration..."
            )

            # Classify all chunks using the professional content classification system
            all_chunks = []
            if intro_chunk:
                all_chunks.append(intro_chunk)

            # Convert raw chunks to dict format for classification
            raw_chunk_list = []
            for idx, chunk_obj in enumerate(chunks_data):
                chunk_text = chunk_obj.content if hasattr(chunk_obj, 'content') else str(chunk_obj)
                raw_chunk_list.append({'text': chunk_text, 'original_index': idx})

            # Classify chunks
            total_chunks = len(raw_chunk_list)
            classifications = classification_service.classify_chunks(
                chunks=raw_chunk_list,
                book_title=book_metadata.get("title", "")
            )

            # Process classifications and build filtered chunk list
            narratable_count = 0
            skipped_count = 0
            content_type_counts = {}

            for idx, (chunk_data, classification) in enumerate(zip(raw_chunk_list, classifications)):
                content_type = classification.content_type.value
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1

                if classification.narratable:
                    narratable_count += 1
                    all_chunks.append({
                        'content': chunk_data['text'],
                        'content_type': content_type,
                        'narratable': True,
                        'narration_text': classification.narration_text,
                        'is_chapter_start': classification.is_chapter_start,
                        'chapter_title_detected': classification.chapter_title,
                        'classification_confidence': classification.confidence
                    })
                else:
                    skipped_count += 1
                    # Still store non-narratable chunks for reference but mark them
                    all_chunks.append({
                        'content': chunk_data['text'],
                        'content_type': content_type,
                        'narratable': False,
                        'skip_reason': classification.skip_reason,
                        'classification_confidence': classification.confidence
                    })
                    logger.debug(
                        f"⏭️ [{book_id}] Chunk {idx} marked non-narratable: "
                        f"{content_type} - {classification.skip_reason}"
                    )

            # Log classification summary
            logger.info(
                f"📊 [{book_id}] Content Classification Summary:\n"
                f"  - Total chunks: {total_chunks}\n"
                f"  - Narratable: {narratable_count}\n"
                f"  - Non-narratable: {skipped_count}\n"
                f"  - Content types: {content_type_counts}"
            )

            # Use all_chunks for further processing (narratable chunks will be filtered during playback)
            filtered_chunks = all_chunks

            await self._update_progress(
                book_id, "chunking", 45,
                f"Classified {total_chunks} chunks: {narratable_count} narratable"
            )

            # Stage 4: Chapter detection (moved before chunk storage)
            if use_ai_chapter_detection:
                await self._update_progress(
                    book_id, "chapters", 45,
                    "Detecting chapters with AI..."
                )
            else:
                await self._update_progress(
                    book_id, "chapters", 45,
                    "Detecting chapters..."
                )

            chapters = await self._detect_chapters(
                filtered_chunks,
                use_ai=use_ai_chapter_detection,
                book_title=book_metadata.get("title", "")
            )
            logger.info(f"📖 [{book_id}] Detected {len(chapters)} chapters (AI={'enabled' if use_ai_chapter_detection else 'disabled'})")

            await self._update_progress(
                book_id, "chapters", 48,
                f"Found {len(chapters)} chapters"
            )

            # Helper to find chapter for a chunk index
            def get_chapter_for_chunk(chunk_idx: int) -> tuple:
                """Return (chapter_id, chapter_title) for a chunk index."""
                for chapter in chapters:
                    if chapter.start_chunk_id <= chunk_idx <= chapter.end_chunk_id:
                        return (chapter.id, chapter.title)
                return (None, None)

            # Store chunks in MongoDB with chapter info and content classification
            chunk_documents = []
            for idx, chunk_obj in enumerate(filtered_chunks):
                # Handle different chunk formats:
                # - Plain dicts with 'content' key (from classification)
                # - Objects with .content attribute (from document processor)
                # - Other objects (convert to string)
                if isinstance(chunk_obj, dict):
                    chunk_text = chunk_obj.get('content', '')
                    content_type = chunk_obj.get('content_type', 'narrative')
                    narratable = chunk_obj.get('narratable', True)
                    narration_text = chunk_obj.get('narration_text')
                    skip_reason = chunk_obj.get('skip_reason')
                    is_chapter_start = chunk_obj.get('is_chapter_start', False)
                    classification_confidence = chunk_obj.get('classification_confidence', 1.0)
                elif hasattr(chunk_obj, 'content'):
                    chunk_text = chunk_obj.content
                    content_type = 'narrative'
                    narratable = True
                    narration_text = None
                    skip_reason = None
                    is_chapter_start = False
                    classification_confidence = 1.0
                else:
                    chunk_text = str(chunk_obj)
                    content_type = 'narrative'
                    narratable = True
                    narration_text = None
                    skip_reason = None
                    is_chapter_start = False
                    classification_confidence = 1.0

                chapter_id, chapter_title = get_chapter_for_chunk(idx)

                chunk = BookChunk(
                    book_id=book_id,
                    chunk_id=f"{book_id}_chunk_{idx}",
                    chunk_index=idx,
                    text=chunk_text,
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    word_count=len(chunk_text.split()),
                    # Content classification fields
                    content_type=content_type,
                    narratable=narratable,
                    narration_text=narration_text,
                    skip_reason=skip_reason,
                    is_chapter_start=is_chapter_start,
                    classification_confidence=classification_confidence
                )
                chunk_documents.append(chunk.model_dump())

            if chunk_documents:
                await db.book_chunks.insert_many(chunk_documents)
                logger.info(f"💾 [{book_id}] Stored {len(chunk_documents)} chunks in MongoDB")

            await self._update_progress(
                book_id, "chunking", 55,
                f"Created {len(chunk_documents)} text chunks with chapter info"
            )

            # Stage 5: Topic extraction (55-65%)
            await self._update_progress(
                book_id, "topics", 58,
                "Extracting topics using AI..."
            )

            topics = []
            try:
                content_sample = "\n\n".join([
                    chunk_obj.content if hasattr(chunk_obj, 'content') else str(chunk_obj)
                    for chunk_obj in chunks_data[:3]
                ])
                topics = await _topic_extractor.extract_from_content(
                    content=content_sample,
                    title=book_metadata["title"],
                    category=book_metadata.get("genre", ""),
                    max_topics=5
                )
                if topics:
                    logger.info(f"🏷️ [{book_id}] Extracted topics: {topics}")
            except Exception as e:
                logger.warning(f"⚠️ [{book_id}] Topic extraction failed (non-critical): {e}")

            await self._update_progress(
                book_id, "topics", 65,
                f"Extracted {len(topics)} topics" if topics else "Topic extraction skipped"
            )

            # Stage 6: Generate embeddings (65-95%)
            await self._update_progress(
                book_id, "embeddings", 68,
                "Generating semantic embeddings..."
            )

            embeddings_generated = False
            total_embedded = 0

            try:
                embedding_service = await get_embedding_service()
                batch_size = 50
                total_batches = (len(chunk_documents) + batch_size - 1) // batch_size

                for batch_idx, batch_start in enumerate(range(0, len(chunk_documents), batch_size)):
                    batch_end = min(batch_start + batch_size, len(chunk_documents))
                    batch_chunks = chunk_documents[batch_start:batch_end]
                    batch_texts = [chunk["text"] for chunk in batch_chunks]

                    # Generate embeddings for this batch
                    embeddings = await embedding_service.generate_embeddings(batch_texts)

                    # Store embeddings in pgvector
                    stored = await embedding_service.store_embeddings(
                        book_id=book_id,
                        chunks=batch_chunks,
                        embeddings=embeddings,
                        uploaded_by=uploaded_by,
                        topics=topics
                    )
                    total_embedded += stored

                    # Calculate progress (65-95% range)
                    batch_progress = 65 + int((batch_idx + 1) / total_batches * 30)
                    await self._update_progress(
                        book_id, "embeddings", batch_progress,
                        f"Generated embeddings: {total_embedded}/{len(chunk_documents)}"
                    )

                    logger.info(f"🧠 [{book_id}] Embedding batch {batch_idx + 1}/{total_batches}: {stored} stored")

                logger.info(f"✅ [{book_id}] Generated {total_embedded} embeddings total")
                embeddings_generated = True

            except Exception as e:
                logger.error(f"❌ [{book_id}] Embedding generation failed: {e}", exc_info=True)
                await self._update_progress(
                    book_id, "embeddings", 70,
                    f"Embedding generation failed: {str(e)[:50]}..."
                )

            # Stage 7: Finalize (95-100%)
            await self._update_progress(
                book_id, "finalizing", 98,
                "Finalizing book processing..."
            )

            # Build warning message if embeddings failed
            summary_note = ""
            if not embeddings_generated or total_embedded == 0:
                summary_note = "\n\n⚠️ Note: Embeddings not generated. Semantic search unavailable."
                logger.warning(f"⚠️ [{book_id}] Processed without embeddings - semantic search unavailable")

            # Update book with all processed data
            update_data = {
                "processed": True,
                "processing_status": "ready",
                "processing_stage": "complete",
                "processing_progress": 100,
                "processing_message": "Book is ready for reading!",
                "chapters": [c.model_dump() for c in chapters],
                "metadata.page_count": page_count,
                "metadata.word_count": word_count,
                "metadata.estimated_reading_time_minutes": reading_time,
                "metadata.topics": topics,
                "updated_at": datetime.utcnow()
            }

            if summary_note:
                update_data["metadata.summary"] = summary_note.strip()

            await db.books.update_one(
                {"book_id": book_id},
                {"$set": update_data}
            )

            logger.info(f"🎉 [{book_id}] Book processing completed successfully!")

            # Stage 8: Trigger audio pre-generation in background
            try:
                from app.services.audio_pregeneration_service import trigger_audio_pregeneration
                from app.services.session_voice_settings_service import (
                    get_session_voice_settings_service
                )

                # Get uploader's global voice settings or use defaults
                voice_settings = None
                try:
                    session_service = await get_session_voice_settings_service()
                    user_settings = await session_service.get_user_settings(uploaded_by, "default")
                    
                    # Extract TTS settings from user settings
                    tts_settings = user_settings.get("tts", {})
                    voice_settings = {
                        "provider_id": tts_settings.get("provider") or tts_settings.get("default_provider") or "kokoro",
                        "voice_id": tts_settings.get("voice") or tts_settings.get("default_voice") or "am_michael",
                        "speed": tts_settings.get("speed", 1.0),
                        "language": "en"
                    }
                    
                    logger.info(
                        f"🎵 [{book_id}] Using user voice settings for pre-generation: "
                        f"provider={voice_settings['provider_id']}, "
                        f"voice={voice_settings['voice_id']}"
                    )
                except Exception as settings_error:
                    logger.warning(
                        f"⚠️ [{book_id}] Failed to get user settings, using defaults: {settings_error}"
                    )
                    # Use defaults: kokoro/am_michael
                    voice_settings = {
                        "provider_id": "kokoro",
                        "voice_id": "am_michael",
                        "speed": 1.0,
                        "language": "en"
                    }

                await trigger_audio_pregeneration(
                    book_id=book_id,
                    user_id=uploaded_by,
                    voice_settings=voice_settings
                )
                logger.info(f"🔊 [{book_id}] Audio pre-generation triggered in background")
            except Exception as e:
                logger.warning(f"⚠️ [{book_id}] Audio pre-generation trigger failed (non-critical): {e}")
                # Don't fail book processing if audio trigger fails

            # Fetch and return updated book
            book_doc = await db.books.find_one({"book_id": book_id})
            return Book(**book_doc)

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"❌ [{book_id}] Book processing failed: {e}", exc_info=True)

            # Update book status to error
            await db.books.update_one(
                {"book_id": book_id},
                {
                    "$set": {
                        "processing_status": "error",
                        "processing_stage": "failed",
                        "processing_progress": 0,
                        "processing_message": f"Processing failed: {error_msg}",
                        "processing_error": error_msg,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            raise

    async def _detect_chapters(
        self,
        chunks: List[Any],
        use_ai: bool = False,
        book_title: str = ""
    ) -> List[BookChapter]:
        """
        Detect chapters in text chunks.

        Uses regex to find chapter headings like "Chapter 1:", "CHAPTER ONE",
        "Part I", etc. Filters out table of contents entries.

        When use_ai=True, uses AI-enhanced detection with Gemini for books
        with non-standard chapter formats.

        Args:
            chunks: List of text chunks
            use_ai: If True, use AI-enhanced chapter detection
            book_title: Book title for AI context

        Returns:
            List of detected chapters with id, order, and chunk ranges
        """
        import re

        # If AI detection is enabled, try the AI service first
        if use_ai:
            try:
                from app.services.ai_chapter_detection_service import (
                    get_ai_chapter_detection_service
                )

                ai_service = await get_ai_chapter_detection_service()
                ai_chapters = await ai_service.detect_chapters_with_fallback(
                    chunks=chunks,
                    book_title=book_title,
                    use_ai=True
                )

                if ai_chapters:
                    # Convert AI detection results to BookChapter objects
                    return self._convert_ai_chapters_to_book_chapters(
                        ai_chapters, chunks
                    )

                logger.info("AI chapter detection returned no results, falling back to regex")

            except Exception as e:
                logger.warning(f"AI chapter detection failed, falling back to regex: {e}")

        # Standard regex-based chapter detection
        chapters = []

        # Regex patterns for chapter detection
        # Match "Chapter 1", "CHAPTER ONE", "Chapter I:", etc.
        chapter_regex = re.compile(
            r'^(chapter|part|section)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|'
            r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
            r'i{1,3}|iv|v|vi{1,3}|ix|x|xi{1,3})\s*[:\-]?\s*(.*)$',
            re.IGNORECASE | re.MULTILINE
        )

        def is_toc_line(line: str) -> bool:
            """Check if a line looks like a table of contents entry."""
            # TOC entries typically have lots of dots and page numbers
            if line.count('.') > 5 and len(line) < 200:
                return True
            # Or have page numbers at the end
            if re.search(r'\.\s*\d+\s*$', line):
                return True
            return False

        def extract_chapter_title(text: str) -> str | None:
            """
            Extract clean chapter title from text.

            Scans ALL lines in the chunk to find chapter headings that may appear
            anywhere in the text, not just at the beginning.
            """
            lines = text.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line or is_toc_line(line):
                    continue

                match = chapter_regex.match(line)
                if match:
                    chapter_type = match.group(1).capitalize()
                    chapter_num = match.group(2)
                    chapter_subtitle = match.group(3).strip() if match.group(3) else ""

                    # Clean up the title
                    if chapter_subtitle:
                        return f"{chapter_type} {chapter_num}: {chapter_subtitle}"[:100]
                    else:
                        return f"{chapter_type} {chapter_num}"[:100]

            return None

        current_chapter = None
        chapter_start_idx = 0
        chapter_order = 0

        for idx, chunk in enumerate(chunks):
            # Extract text from chunk object
            if isinstance(chunk, dict):
                chunk_text = chunk.get('content', str(chunk))
            elif hasattr(chunk, 'content'):
                chunk_text = chunk.content
            else:
                chunk_text = str(chunk)

            # Try to find a chapter title in this chunk
            chapter_title = extract_chapter_title(chunk_text)

            if chapter_title:
                # Save previous chapter
                if current_chapter:
                    current_chapter.end_chunk_id = idx - 1
                    current_chapter.word_count = sum(
                        len((chunks[i].content if hasattr(chunks[i], 'content') else str(chunks[i])).split())
                        for i in range(chapter_start_idx, idx)
                    )
                    chapters.append(current_chapter)

                # Start new chapter
                chapter_order += 1
                current_chapter = BookChapter(
                    id=f"ch_{chapter_order}",
                    title=chapter_title,
                    order=chapter_order,
                    start_chunk_id=idx,
                    end_chunk_id=idx,  # Will be updated
                    word_count=0,  # Will be calculated
                    duration=None,  # Calculated after audio generation
                    start_time=None  # Calculated after audio generation
                )
                chapter_start_idx = idx

        # Save last chapter
        if current_chapter:
            current_chapter.end_chunk_id = len(chunks) - 1
            current_chapter.word_count = sum(
                len((chunks[i].content if hasattr(chunks[i], 'content') else str(chunks[i])).split())
                for i in range(chapter_start_idx, len(chunks))
            )
            chapters.append(current_chapter)

        # If no chapters detected, create a single default chapter
        if not chapters and chunks:
            chapters.append(
                BookChapter(
                    id="ch_1",
                    title="Full Book",
                    order=1,
                    start_chunk_id=0,
                    end_chunk_id=len(chunks) - 1,
                    word_count=sum(
                        len((chunk.content if hasattr(chunk, 'content') else str(chunk)).split())
                        for chunk in chunks
                    ),
                    duration=None,
                    start_time=None
                )
            )

        return chapters

    def _convert_ai_chapters_to_book_chapters(
        self,
        ai_chapters: List[Dict[str, Any]],
        chunks: List[Any]
    ) -> List[BookChapter]:
        """
        Convert AI detection results to BookChapter objects.

        AI detection returns list of dicts with chunk_index, title, confidence.
        This method creates proper BookChapter objects with calculated
        start/end chunk indices and word counts.

        Args:
            ai_chapters: Results from AI chapter detection
            chunks: Original text chunks

        Returns:
            List of BookChapter objects
        """
        book_chapters = []

        for order, ai_chapter in enumerate(ai_chapters, start=1):
            start_idx = ai_chapter["chunk_index"]
            title = ai_chapter["title"]

            # Determine end_chunk_id - either next chapter's start - 1 or end of book
            if order < len(ai_chapters):
                end_idx = ai_chapters[order]["chunk_index"] - 1
            else:
                end_idx = len(chunks) - 1

            # Ensure end_idx is valid
            end_idx = max(start_idx, end_idx)

            # Calculate word count for this chapter
            word_count = 0
            for i in range(start_idx, min(end_idx + 1, len(chunks))):
                chunk = chunks[i]
                if isinstance(chunk, dict):
                    text = chunk.get('content') or chunk.get('text', '')
                elif hasattr(chunk, 'content'):
                    text = chunk.content
                elif hasattr(chunk, 'text'):
                    text = chunk.text
                else:
                    text = str(chunk)
                word_count += len(text.split())

            book_chapters.append(
                BookChapter(
                    id=f"ch_{order}",
                    title=title,
                    order=order,
                    start_chunk_id=start_idx,
                    end_chunk_id=end_idx,
                    word_count=word_count,
                    duration=None,  # Calculated after audio generation
                    start_time=None  # Calculated after audio generation
                )
            )

        # If no chapters were created but we have chunks, create default
        if not book_chapters and chunks:
            word_count = sum(
                len((chunk.content if hasattr(chunk, 'content') else str(chunk)).split())
                for chunk in chunks
            )
            book_chapters.append(
                BookChapter(
                    id="ch_1",
                    title="Full Book",
                    order=1,
                    start_chunk_id=0,
                    end_chunk_id=len(chunks) - 1,
                    word_count=word_count,
                    duration=None,
                    start_time=None
                )
            )

        return book_chapters

    async def get_processing_status(
        self,
        book_id: str
    ) -> Dict[str, Any]:
        """
        Get book processing status.

        Args:
            book_id: Book identifier

        Returns:
            Status information
        """
        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            return {
                "book_id": book_id,
                "status": "not_found",
                "message": "Book not found"
            }

        chunks_count = await db.book_chunks.count_documents({"book_id": book_id})

        return {
            "book_id": book_id,
            "status": book.get("processing_status", "unknown"),
            "stage": book.get("processing_stage", ""),
            "progress": book.get("processing_progress", 0),
            "message": book.get("processing_message", self._get_status_message(book)),
            "chapters_processed": len(book.get("chapters", [])),
            "chunks_generated": chunks_count,
            "error": book.get("processing_error")
        }

    async def reclassify_book_chunks(
        self,
        book_id: str,
        preferences: Optional[NarrationPreferences] = None
    ) -> Dict[str, Any]:
        """
        Re-classify all chunks for an existing book.

        Applies content classification to books that were ingested before
        the classification system was added. Updates chunks in-place with
        narratable flags and content types.

        Args:
            book_id: The book ID to reclassify
            preferences: Optional narration preferences (defaults to strict)

        Returns:
            Dictionary with reclassification statistics
        """
        db = get_db()

        # Get the book
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise ValueError(f"Book not found: {book_id}")

        book_title = book.get("title", "")
        logger.info(f"📚 [{book_id}] Starting reclassification for: {book_title}")

        # Get all chunks for this book
        chunks = await db.book_chunks.find(
            {"book_id": book_id}
        ).sort("chunk_index", 1).to_list(None)

        if not chunks:
            logger.warning(f"⚠️ [{book_id}] No chunks found for reclassification")
            return {"book_id": book_id, "chunks_processed": 0, "error": "No chunks found"}

        total_chunks = len(chunks)
        logger.info(f"📊 [{book_id}] Found {total_chunks} chunks to reclassify")

        # Get classification service
        classification_service = get_content_classification_service()
        prefs = preferences or NarrationPreferences()

        # Statistics
        stats = {
            "total_chunks": total_chunks,
            "narratable": 0,
            "non_narratable": 0,
            "content_types": {}
        }

        # Process each chunk
        for chunk in chunks:
            chunk_index = chunk.get("chunk_index", 0)
            text = chunk.get("text", "")

            # Classify this chunk
            classification = classification_service.classify_chunk(
                text=text,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                book_title=book_title,
                preferences=prefs
            )

            # Update chunk in database
            update_data = {
                "content_type": classification.content_type.value,
                "narratable": classification.narratable,
                "skip_reason": classification.skip_reason,
                "is_chapter_start": classification.is_chapter_start,
                "classification_confidence": classification.confidence
            }

            # Add narration_text if available
            if classification.narration_text:
                update_data["narration_text"] = classification.narration_text

            # Add chapter_title if detected
            if classification.chapter_title:
                update_data["chapter_title"] = classification.chapter_title

            await db.book_chunks.update_one(
                {"_id": chunk["_id"]},
                {"$set": update_data}
            )

            # Update statistics
            content_type = classification.content_type.value
            stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1
            if classification.narratable:
                stats["narratable"] += 1
            else:
                stats["non_narratable"] += 1

        logger.info(
            f"✅ [{book_id}] Reclassification complete: "
            f"{stats['narratable']} narratable, {stats['non_narratable']} non-narratable"
        )
        logger.info(f"📊 [{book_id}] Content types: {stats['content_types']}")

        return {
            "book_id": book_id,
            "book_title": book_title,
            "chunks_processed": total_chunks,
            "stats": stats
        }

    async def reclassify_all_books(
        self,
        preferences: Optional[NarrationPreferences] = None
    ) -> Dict[str, Any]:
        """
        Re-classify all books that don't have classification data.

        Finds books with chunks missing narratable field and applies
        classification to them.

        Returns:
            Dictionary with overall statistics
        """
        db = get_db()

        # Find books with unclassified chunks
        pipeline = [
            {"$match": {"narratable": {"$exists": False}}},
            {"$group": {"_id": "$book_id"}},
            {"$limit": 100}  # Process in batches
        ]
        unclassified = await db.book_chunks.aggregate(pipeline).to_list(None)
        book_ids = [doc["_id"] for doc in unclassified]

        logger.info(f"📚 Found {len(book_ids)} books with unclassified chunks")

        results = []
        for book_id in book_ids:
            try:
                result = await self.reclassify_book_chunks(book_id, preferences)
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Failed to reclassify {book_id}: {e}")
                results.append({"book_id": book_id, "error": str(e)})

        return {
            "books_processed": len(results),
            "results": results
        }

    def _get_status_message(self, book: Dict[str, Any]) -> str:
        """Get human-readable status message."""
        status = book.get("processing_status", "unknown")

        if status == "pending":
            return "Book upload received, waiting to process"
        elif status == "processing":
            return book.get("processing_message", "Processing book...")
        elif status == "ready":
            return "Book is ready for readers"
        elif status == "error":
            return f"Processing failed: {book.get('processing_error', 'Unknown error')}"
        else:
            return f"Unknown status: {status}"


# Global service instance
_book_processing_service: Optional[BookProcessingService] = None


async def get_book_processing_service() -> BookProcessingService:
    """
    Get or create book processing service instance.

    Returns:
        Book processing service instance
    """
    global _book_processing_service

    if _book_processing_service is None:
        _book_processing_service = BookProcessingService()
        await _book_processing_service.initialize()

    return _book_processing_service
