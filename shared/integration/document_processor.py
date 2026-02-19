"""
Document Processor Utility for KasaAI Shared Services

This module provides comprehensive document processing capabilities including:
- PDF text extraction (PyPDF2, pdfplumber)
- DOCX text extraction (python-docx)
- Plain text processing
- Metadata extraction (author, date, page count, etc.)
- Multiple chunking strategies (sentence-aware, paragraph-aware, recursive)
- Text cleaning and normalization
- Batch processing support

Usage:
    from apps.shared.integration.document_processor import DocumentProcessor, ChunkingStrategy

    # Basic usage
    processor = DocumentProcessor()
    result = await processor.process_file("path/to/document.pdf")
    print(f"Extracted {len(result.chunks)} chunks from {result.metadata.page_count} pages")

    # With custom chunking
    processor = DocumentProcessor(
        chunking_strategy=ChunkingStrategy.SENTENCE_AWARE,
        chunk_size=500,
        chunk_overlap=50
    )
    result = await processor.process_file("document.pdf")

    # Batch processing
    results = await processor.process_batch([
        "doc1.pdf",
        "doc2.docx",
        "doc3.txt"
    ])

Dependencies:
    pip install PyPDF2 pdfplumber python-docx beautifulsoup4 nltk

Author: KasaAI Team
Date: 2025-10-24
"""

import asyncio
import io
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator

# Text processing
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# PDF processing
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# DOCX processing
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# HTML processing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class ChunkingStrategy(str, Enum):
    """Chunking strategies for text splitting."""

    RECURSIVE = "recursive"  # Split on multiple delimiters recursively
    SENTENCE_AWARE = "sentence_aware"  # Split by sentences, merge to target size
    PARAGRAPH_AWARE = "paragraph_aware"  # Split by paragraphs, merge to target size
    FIXED_SIZE = "fixed_size"  # Simple fixed-size chunks with overlap
    SEMANTIC = "semantic"  # Split based on semantic boundaries (headers, sections)


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""

    filename: str
    file_size: int  # bytes
    document_type: DocumentType
    page_count: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    language: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    processing_time: Optional[float] = None  # seconds
    extractor_used: Optional[str] = None  # PyPDF2, pdfplumber, etc.

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TextChunk(BaseModel):
    """A chunk of processed text with metadata."""

    content: str
    chunk_index: int
    char_start: int
    char_end: int
    word_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("content")
    def content_not_empty(cls, v):
        """Ensure chunk content is not empty."""
        if not v or not v.strip():
            raise ValueError("Chunk content cannot be empty")
        return v


class ProcessedDocument(BaseModel):
    """Result of document processing."""

    raw_text: str
    chunks: List[TextChunk]
    metadata: DocumentMetadata
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @property
    def total_chunks(self) -> int:
        """Total number of chunks."""
        return len(self.chunks)

    @property
    def average_chunk_size(self) -> float:
        """Average chunk size in characters."""
        if not self.chunks:
            return 0.0
        return sum(len(c.content) for c in self.chunks) / len(self.chunks)


class DocumentProcessor:
    """
    Comprehensive document processor for various file formats.

    Supports PDF, DOCX, TXT, HTML, and Markdown with intelligent
    text extraction, cleaning, and chunking strategies.
    """

    def __init__(
        self,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        clean_text: bool = True,
        extract_metadata: bool = True,
        pdf_extractor: str = "pdfplumber"  # pdfplumber or pypdf2
    ):
        """
        Initialize document processor.

        Args:
            chunking_strategy: Strategy for splitting text into chunks
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (smaller chunks discarded)
            max_chunk_size: Maximum chunk size (larger chunks split)
            clean_text: Whether to clean and normalize text
            extract_metadata: Whether to extract document metadata
            pdf_extractor: PDF extraction library to use (pdfplumber or pypdf2)
        """
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.clean_text = clean_text
        self.extract_metadata = extract_metadata
        self.pdf_extractor = pdf_extractor

        # Initialize NLTK for sentence tokenization if available
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                # Download punkt tokenizer if not available
                try:
                    nltk.download('punkt', quiet=True)
                except Exception:
                    pass  # Fail silently if download fails

    def _detect_document_type(self, file_path: Union[str, Path]) -> DocumentType:
        """
        Detect document type from file extension.

        Args:
            file_path: Path to the document

        Returns:
            DocumentType enum value
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        type_map = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.DOCX,
            '.txt': DocumentType.TXT,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML,
            '.md': DocumentType.MARKDOWN,
            '.markdown': DocumentType.MARKDOWN,
        }

        return type_map.get(suffix, DocumentType.UNKNOWN)

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Fix common OCR/extraction errors first (before any whitespace handling)
        text = text.replace('\ufeff', '')  # Remove BOM
        text = text.replace('\x00', '')  # Remove null bytes

        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

        # Normalize newlines: convert \r\n and \r to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive newlines (keep max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove excessive horizontal whitespace (spaces/tabs) but preserve newlines
        # This replaces multiple spaces/tabs with single space, but keeps \n intact
        text = re.sub(r'[^\S\n]+', ' ', text)

        # Remove spaces at start/end of lines
        text = re.sub(r' *\n *', '\n', text)

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    async def _extract_pdf_pypdf2(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF using PyPDF2.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")

        def extract():
            text = []
            metadata = {}

            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                # Extract metadata
                if reader.metadata:
                    metadata['author'] = reader.metadata.get('/Author')
                    metadata['title'] = reader.metadata.get('/Title')
                    creation_date = reader.metadata.get('/CreationDate')
                    if creation_date:
                        try:
                            # Parse PDF date format: D:YYYYMMDDHHmmSS
                            date_str = creation_date.replace('D:', '').split('+')[0].split('-')[0]
                            metadata['creation_date'] = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                        except Exception:
                            pass

                metadata['page_count'] = len(reader.pages)

                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                    except Exception as e:
                        metadata[f'page_{page_num}_error'] = str(e)

            return '\n\n'.join(text), metadata

        # Run in thread pool to avoid blocking
        return await asyncio.to_thread(extract)

    async def _extract_pdf_pdfplumber(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF using pdfplumber (better OCR quality).

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")

        def extract():
            text = []
            metadata = {}

            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                if pdf.metadata:
                    metadata['author'] = pdf.metadata.get('Author')
                    metadata['title'] = pdf.metadata.get('Title')
                    creation_date = pdf.metadata.get('CreationDate')
                    if creation_date:
                        try:
                            # Parse PDF date format
                            date_str = creation_date.replace('D:', '').split('+')[0].split('-')[0]
                            metadata['creation_date'] = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                        except Exception:
                            pass

                metadata['page_count'] = len(pdf.pages)

                # Extract text from each page
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                    except Exception as e:
                        metadata[f'page_{page_num}_error'] = str(e)

            return '\n\n'.join(text), metadata

        return await asyncio.to_thread(extract)

    async def _extract_docx(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")

        def extract():
            doc = DocxDocument(file_path)

            # Extract text from paragraphs
            text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text.append(para.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text for cell in row.cells)
                    if row_text.strip():
                        text.append(row_text)

            # Extract metadata
            metadata = {}
            if doc.core_properties:
                metadata['author'] = doc.core_properties.author
                metadata['title'] = doc.core_properties.title
                metadata['creation_date'] = doc.core_properties.created
                metadata['modification_date'] = doc.core_properties.modified

            # Count paragraphs as "pages" for consistency
            metadata['page_count'] = len(doc.paragraphs)

            return '\n\n'.join(text), metadata

        return await asyncio.to_thread(extract)

    async def _extract_text(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from plain text file.

        Args:
            file_path: Path to text file

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        def extract():
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

            metadata = {
                'page_count': text.count('\n\n') + 1  # Estimate "pages" by paragraphs
            }

            return text, metadata

        return await asyncio.to_thread(extract)

    async def _extract_html(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from HTML file.

        Args:
            file_path: Path to HTML file

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")

        def extract():
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html = f.read()

            soup = BeautifulSoup(html, 'html.parser')

            # Extract metadata from meta tags
            metadata = {}
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text()

            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                metadata['author'] = author_meta.get('content')

            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n\n')

            return text, metadata

        return await asyncio.to_thread(extract)

    def _chunk_recursive(self, text: str) -> List[str]:
        """
        Split text recursively on multiple delimiters.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        # Reason: Try splitting on increasingly smaller delimiters until chunks are small enough
        separators = ['\n\n', '\n', '. ', ' ', '']

        def split_text(text: str, separators: List[str]) -> List[str]:
            if not separators:
                # Base case: no more separators, return character-split chunks
                return [text[i:i + self.chunk_size]
                       for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

            separator = separators[0]
            splits = text.split(separator) if separator else list(text)

            chunks = []
            current_chunk = []
            current_size = 0

            for split in splits:
                split_size = len(split)

                if split_size > self.max_chunk_size:
                    # Recursively split large pieces
                    if current_chunk:
                        chunks.append(separator.join(current_chunk))
                        current_chunk = []
                        current_size = 0

                    sub_chunks = split_text(split, separators[1:])
                    chunks.extend(sub_chunks)
                    continue

                if current_size + split_size > self.chunk_size and current_chunk:
                    # Current chunk is full - save it
                    chunks.append(separator.join(current_chunk))

                    # Start fresh with new split (no overlap at this level)
                    # Overlap is handled at the character level in base case
                    current_chunk = [split]
                    current_size = split_size
                else:
                    current_chunk.append(split)
                    current_size += split_size

            if current_chunk:
                chunks.append(separator.join(current_chunk))

            return chunks

        return split_text(text, separators)

    def _chunk_sentence_aware(self, text: str) -> List[str]:
        """
        Split text by sentences, merge to target chunk size.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not NLTK_AVAILABLE:
            # Fallback to simple sentence splitting
            sentences = re.split(r'(?<=[.!?])\s+', text)
        else:
            sentences = sent_tokenize(text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Current chunk is full
                chunks.append(' '.join(current_chunk))

                # Keep overlap (last few sentences)
                if self.chunk_overlap > 0:
                    overlap_size = 0
                    overlap_sentences = []
                    for s in reversed(current_chunk):
                        if overlap_size + len(s) <= self.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_size += len(s)
                        else:
                            break
                    current_chunk = overlap_sentences + [sentence]
                    current_size = overlap_size + sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _chunk_paragraph_aware(self, text: str) -> List[str]:
        """
        Split text by paragraphs, merge to target chunk size.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            if para_size > self.max_chunk_size:
                # Split large paragraphs recursively
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                sub_chunks = self._chunk_recursive(para)
                chunks.extend(sub_chunks)
                continue

            if current_size + para_size > self.chunk_size and current_chunk:
                # Current chunk is full
                chunks.append('\n\n'.join(current_chunk))

                # Keep overlap (last paragraph)
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    current_chunk = [overlap_text, para]
                    current_size = len(overlap_text) + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _chunk_fixed_size(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks with overlap.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start += self.chunk_size - self.chunk_overlap

        return chunks

    def _create_chunks(self, text: str) -> List[TextChunk]:
        """
        Create TextChunk objects from raw text.

        Args:
            text: Text to chunk

        Returns:
            List of TextChunk objects
        """
        # Select chunking strategy
        if self.chunking_strategy == ChunkingStrategy.SENTENCE_AWARE:
            raw_chunks = self._chunk_sentence_aware(text)
        elif self.chunking_strategy == ChunkingStrategy.PARAGRAPH_AWARE:
            raw_chunks = self._chunk_paragraph_aware(text)
        elif self.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
            raw_chunks = self._chunk_fixed_size(text)
        else:  # RECURSIVE (default)
            raw_chunks = self._chunk_recursive(text)

        # Create TextChunk objects
        chunks = []
        char_position = 0

        for i, chunk_text in enumerate(raw_chunks):
            # Skip chunks that are too small
            if len(chunk_text) < self.min_chunk_size:
                continue

            # Find chunk position in original text
            chunk_start = text.find(chunk_text, char_position)
            if chunk_start == -1:
                chunk_start = char_position

            chunk_end = chunk_start + len(chunk_text)
            word_count = len(chunk_text.split())

            chunk = TextChunk(
                content=chunk_text,
                chunk_index=i,
                char_start=chunk_start,
                char_end=chunk_end,
                word_count=word_count,
                metadata={}
            )

            chunks.append(chunk)
            char_position = chunk_end

        return chunks

    async def process_file(self, file_path: Union[str, Path]) -> ProcessedDocument:
        """
        Process a single document file.

        Args:
            file_path: Path to document file

        Returns:
            ProcessedDocument with extracted text, chunks, and metadata
        """
        start_time = datetime.now()
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect document type
        doc_type = self._detect_document_type(file_path)

        errors = []
        warnings = []
        raw_text = ""
        metadata_dict = {}

        try:
            # Extract text based on document type
            if doc_type == DocumentType.PDF:
                if self.pdf_extractor == "pdfplumber":
                    raw_text, metadata_dict = await self._extract_pdf_pdfplumber(str(file_path))
                    metadata_dict['extractor_used'] = 'pdfplumber'
                else:
                    raw_text, metadata_dict = await self._extract_pdf_pypdf2(str(file_path))
                    metadata_dict['extractor_used'] = 'pypdf2'
            elif doc_type == DocumentType.DOCX:
                raw_text, metadata_dict = await self._extract_docx(str(file_path))
                metadata_dict['extractor_used'] = 'python-docx'
            elif doc_type == DocumentType.HTML:
                raw_text, metadata_dict = await self._extract_html(str(file_path))
                metadata_dict['extractor_used'] = 'beautifulsoup4'
            elif doc_type in (DocumentType.TXT, DocumentType.MARKDOWN):
                raw_text, metadata_dict = await self._extract_text(str(file_path))
                metadata_dict['extractor_used'] = 'builtin'
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")

            # Clean text if requested
            if self.clean_text:
                raw_text = self._clean_text(raw_text)

            # Create chunks
            chunks = self._create_chunks(raw_text)

            if not chunks:
                warnings.append("No chunks created - document may be empty or too small")

        except Exception as e:
            errors.append(f"Error processing document: {str(e)}")
            chunks = []

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Build metadata
        file_stat = file_path.stat()
        metadata = DocumentMetadata(
            filename=file_path.name,
            file_size=file_stat.st_size,
            document_type=doc_type,
            page_count=metadata_dict.get('page_count'),
            author=metadata_dict.get('author'),
            title=metadata_dict.get('title'),
            creation_date=metadata_dict.get('creation_date'),
            modification_date=metadata_dict.get('modification_date'),
            word_count=len(raw_text.split()) if raw_text else 0,
            character_count=len(raw_text),
            processing_time=processing_time,
            extractor_used=metadata_dict.get('extractor_used')
        )

        return ProcessedDocument(
            raw_text=raw_text,
            chunks=chunks,
            metadata=metadata,
            errors=errors,
            warnings=warnings
        )

    async def process_batch(
        self,
        file_paths: List[Union[str, Path]],
        max_concurrent: int = 5
    ) -> List[ProcessedDocument]:
        """
        Process multiple documents concurrently.

        Args:
            file_paths: List of file paths to process
            max_concurrent: Maximum number of concurrent processing tasks

        Returns:
            List of ProcessedDocument results
        """
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(file_path):
            async with semaphore:
                return await self.process_file(file_path)

        # Process all files concurrently (with limit)
        tasks = [process_with_semaphore(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to ProcessedDocument with errors
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error document
                file_path = Path(file_paths[i])
                processed_results.append(
                    ProcessedDocument(
                        raw_text="",
                        chunks=[],
                        metadata=DocumentMetadata(
                            filename=file_path.name,
                            file_size=0,
                            document_type=DocumentType.UNKNOWN
                        ),
                        errors=[f"Failed to process: {str(result)}"]
                    )
                )
            else:
                processed_results.append(result)

        return processed_results
