# InkWave Book Creation Guide

**Complete guide for admins and authors to upload and process books on InkWave**

---

## Overview

InkWave provides a streamlined book creation flow that allows administrators and authors to upload PDF books, add cover images, and have them automatically processed for audiobook narration and interactive Q&A.

### What Happens When You Upload a Book

1. **Upload** - PDF and cover image are uploaded
2. **Process** - Text extraction, chapter detection, chunking
3. **Index** - Vector embeddings generated for Q&A
4. **Ready** - Book appears on interface, ready for narration

---

## Step-by-Step Guide

### Step 1: Access the Admin Panel

1. Log in to InkWave with an admin account
2. Navigate to the **Admin Dashboard** (`/admin`)
3. Click on **"Book Creation"** section

### Step 2: Upload Your Book

1. **Select PDF File**
   - Drag and drop your PDF onto the upload area, OR
   - Click the upload area to browse and select a file
   - Supported: PDF files up to 100MB

2. **Add Cover Image** (Optional but Recommended)
   - **Option A: Upload Image File**
     - Click the cover image box
     - Select JPG, PNG, or WebP (max 5MB)
     - Preview appears immediately

   - **Option B: Use Image URL**
     - Paste the URL of an existing cover image
     - Example: `https://example.com/book-cover.jpg`

3. **Fill in Book Details**
   - **Title*** (Required) - The book's title
   - **Author*** (Required) - Author's name
   - **Description*** (Required) - Brief description or summary
   - **Duration** (Optional) - Estimated duration in minutes
   - **Narrator** (Optional) - Voice actor or TTS voice name

4. **Upload**
   - Click **"Upload Book"** button
   - Monitor upload progress
   - Wait for processing to complete

### Step 3: Processing

Once uploaded, the system automatically:

1. **Extracts Text** - Reads all text from the PDF
2. **Detects Chapters** - Identifies chapter boundaries
3. **Creates Chunks** - Breaks text into manageable pieces (1000 chars)
4. **Generates Embeddings** - Creates vector representations for AI Q&A
5. **Stores Data** - Saves everything to the database

**Processing Time**: Typically 30-60 seconds for a 100-page book

### Step 4: Verify Upload

1. Check the **"Recent Uploads"** section on the right
2. Look for your book with status **"READY"**
3. Note the number of chapters detected

### Step 5: Book is Live!

Your book is now available on InkWave:
- Visible in the book library
- Cover image displayed
- Ready for audiobook narration
- Q&A enabled for interactive reading

---

## Technical Details

### File Requirements

**PDF Files**
- Format: PDF
- Max Size: 100 MB
- Must contain extractable text (not scanned images)
- OCR support planned for future release

**Cover Images**
- Formats: JPG, PNG, WebP
- Max Size: 5 MB
- Recommended: 300x400 pixels or larger
- Aspect ratio: 3:4 (portrait)

### What Gets Processed

1. **Text Extraction**
   - All readable text from PDF
   - Formatted and cleaned
   - Special characters handled

2. **Chapter Detection**
   - Looks for patterns: "Chapter N", "Part N", "Section N"
   - Creates chapter navigation
   - Tracks word counts per chapter

3. **Chunking Strategy**
   - Chunk size: 1000 characters
   - Overlap: 200 characters
   - Min size: 100 characters
   - Max size: 2000 characters

4. **Vector Embeddings**
   - Generated for semantic search
   - Enables AI-powered Q&A
   - Stored in pgvector database

### Database Storage

**MongoDB Collections**

1. **books** - Book metadata
   ```json
   {
     "book_id": "book_abc123",
     "title": "Sample Book",
     "author": "John Doe",
     "cover_url": "/static/covers/cover_abc123.jpg",
     "processing_status": "ready",
     "processed": true,
     "metadata": {
       "page_count": 250,
       "word_count": 75000,
       "chapters": 15
     }
   }
   ```

2. **book_chunks** - Text chunks with narration data
   ```json
   {
     "book_id": "book_abc123",
     "chunk_index": 0,
     "text": "Chapter 1: The Beginning...",
     "word_count": 150,
     "audio_url": null,
     "audio_duration": null
   }
   ```

**pgvector (PostgreSQL)** - Vector embeddings for Q&A

---

## Troubleshooting

### Upload Fails

**"Invalid file type"**
- Ensure file is PDF format
- Check file extension is `.pdf`

**"File too large"**
- PDF exceeds 100MB
- Try compressing the PDF
- Split into multiple volumes

**"Invalid cover image format"**
- Use JPG, PNG, or WebP only
- Ensure file is not corrupted

### Processing Errors

**"Processing failed"**
- PDF may be corrupted
- PDF may be password protected
- PDF may be scanned images without text

**"No chapters detected"**
- This is OK! Book will still work
- Chapters are optional
- You can read/narrate the entire book

**"Embedding generation failed"**
- Non-critical error
- Book narration still works
- Q&A may be limited

### Book Not Appearing

1. Check **"Recent Uploads"** for status
2. Verify status is **"READY"** not **"ERROR"**
3. Refresh the book library page
4. Check browser console for errors

---

## API Reference

For developers integrating with the InkWave API:

### Upload Book

```bash
POST /api/v1/books/upload
Content-Type: multipart/form-data

Fields:
- file: PDF file (required)
- title: string (required)
- author: string (required)
- description: string (required)
- cover_image: Image file (optional)
- cover_url: string (optional, if no cover_image)
- duration_minutes: integer (optional)
- narrator: string (optional)

Response:
{
  "book_id": "book_abc123",
  "title": "Sample Book",
  "cover_url": "/static/covers/cover_abc123.jpg",
  "processing_status": "ready",
  "message": "Book uploaded and processing started",
  "chapters_extracted": 15
}
```

### Check Processing Status

```bash
GET /api/v1/books/{book_id}/processing-status

Response:
{
  "book_id": "book_abc123",
  "processing_status": "ready",
  "processed": true,
  "processing_error": null,
  "metadata": {
    "page_count": 250,
    "word_count": 75000,
    "chapters": 15
  }
}
```

### List Books

```bash
GET /api/v1/books?page=1&per_page=20

Response:
{
  "books": [...],
  "total": 50,
  "page": 1,
  "per_page": 20
}
```

---

## Best Practices

### Cover Images
- Use high-quality images (300 DPI or higher)
- Maintain 3:4 aspect ratio
- Keep file size under 2MB for fast loading
- Use descriptive filenames

### PDF Preparation
- Ensure text is selectable (not scanned)
- Remove password protection
- Include table of contents if possible
- Use clear chapter headings

### Metadata
- Write compelling descriptions (200-500 words)
- Include relevant keywords
- Be accurate with author names
- Add genre/category tags

### Chapter Structure
- Use consistent chapter naming ("Chapter 1", "Chapter 2")
- Include chapter titles when possible
- Consider splitting very long books into volumes

---

## Advanced Features

### Automatic Metadata Extraction

InkWave automatically extracts:
- Page count
- Word count
- Estimated reading time
- Chapter structure

### Voice Narration

Once uploaded, books can be narrated using:
- F5-TTS (default, high quality)
- Kokoro TTS
- MeloTTS
- OpenVoice
- And 10+ other TTS providers

### Interactive Q&A

The vector database enables:
- Natural language questions about the book
- Context-aware answers
- Chapter-specific queries
- Character and plot analysis

---

## Support

### Common Questions

**Q: Can I upload ebooks in EPUB format?**
A: Currently only PDF is supported. EPUB support is planned.

**Q: How long does processing take?**
A: Typically 30-60 seconds for a 100-page book.

**Q: Can I edit book details after upload?**
A: Yes, through the admin API (feature in development).

**Q: Can I delete a book?**
A: Yes, contact support or use the admin API.

**Q: Is there a limit to how many books I can upload?**
A: No hard limit. Storage space is the only constraint.

### Getting Help

- Documentation: https://inkwave-api.ailabsafrica.com/api/docs
- Support: support@ailabsafrica.com
- GitHub Issues: [Link to repo]

---

## Future Features (Roadmap)

- [ ] EPUB format support
- [ ] Automatic cover generation
- [ ] OCR for scanned PDFs
- [ ] Batch upload
- [ ] Book editing interface
- [ ] Automatic genre classification
- [ ] Multi-language support
- [ ] Audio pre-generation
- [ ] Chapter navigation UI

---

**Last Updated**: 2025-11-13
**Version**: 1.0
**InkWave Team**
