# InkWave Test Books

This directory contains test books generated for development and testing purposes.

## Generated Books

### 1. The Power of Forgiveness
- **Author**: Archbishop Nicholas Duncan-Williams
- **Pages**: 1,053
- **Chapters**: 70
- **File Size**: 0.57 MB
- **File**: `power_of_forgiveness.pdf`

**Purpose**: Test large book processing (1000+ pages)
- Text extraction performance
- Chapter detection with 70 chapters
- TTS generation for long content
- UI/UX with extensive table of contents

### 2. Walking in Spiritual Authority
- **Author**: Archbishop Nicholas Duncan-Williams
- **Pages**: 528
- **Chapters**: 35
- **File Size**: 0.29 MB
- **File**: `spiritual_authority.pdf`

**Purpose**: Test medium-sized book processing
- Moderate chapter count
- Balanced content volume
- Performance benchmarking

### 3. Destined to Win
- **Author**: Archbishop Nicholas Duncan-Williams
- **Pages**: 1,203
- **Chapters**: 80
- **File Size**: 0.64 MB
- **File**: `destined_to_win.pdf`

**Purpose**: Test very large book processing
- Maximum chapter count (80 chapters)
- Largest page count
- Stress test for all systems

## Content Details

All books contain:
- Professional title page
- Copyright page
- Table of contents
- 70-80 chapters with realistic spiritual/religious content
- Section headings within chapters
- Consistent formatting

### Sample Chapter Titles
- The Foundation of Faith
- Understanding Divine Purpose
- Walking in Spiritual Authority
- The Power of Prayer and Fasting
- Overcoming Life's Challenges
- Building Strong Relationships
- Financial Stewardship and Prosperity
- Healing and Restoration
- The Gift of Forgiveness
- Living a Life of Worship

## Testing Scenarios

### 1. Book Upload & Processing
```bash
# Upload via admin panel
- Navigate to /admin/books/upload
- Upload power_of_forgiveness.pdf
- Add cover image
- Submit and monitor processing
```

### 2. Chapter Detection
- Verify all 70/80 chapters are detected correctly
- Check chapter titles and durations
- Validate start times

### 3. Text Extraction
- Confirm all 1000+ pages are extracted
- Verify text quality and formatting
- Check for missing content

### 4. Audio Generation
- Generate TTS for selected chapters
- Test with different voice providers
- Measure generation time for long content

### 5. UI/UX Testing
- Test table of contents with 70+ chapters
- Verify chapter search functionality
- Test section grouping (10 chapters per section)
- Validate progress indicators
- Check performance with large chapter lists

### 6. Memory & Performance
- Monitor memory usage during processing
- Check database query performance
- Validate chunk generation efficiency
- Test frontend rendering with large data

## Usage

### Regenerate Books
```bash
cd /opt/kasaai/apps/inkwave/backend
source /opt/kasaai/apps/venv/bin/activate
python scripts/generate_test_books.py
```

### Upload Books
1. Login to InkWave admin panel
2. Navigate to Book Creation
3. Upload PDF files from this directory
4. Add cover images (optional)
5. Monitor processing status

### Test Audio Generation
```bash
# Via API
curl -X POST https://inkwave-api.ailabsafrica.com/api/v1/books/{book_id}/generate-audio \
  -H "Authorization: Bearer {token}" \
  -d '{"provider_id": "f5tts", "voice_id": "archbishop_1"}'
```

## Performance Benchmarks

Target metrics for large books:

| Metric | Target | Notes |
|--------|--------|-------|
| Upload | < 5s | For 0.6MB PDF |
| Text Extraction | < 30s | For 1200 pages |
| Chapter Detection | < 10s | For 80 chapters |
| Chunking | < 20s | 500-word chunks |
| Embedding Generation | < 2min | With batch processing |
| TTS (per chapter) | < 30s | Depends on provider |
| Frontend Load | < 2s | Initial page render |
| TOC Render | < 500ms | With 80 chapters |

## Known Limitations

1. **TTS Generation**: Very long books may require batch processing
2. **Memory**: Processing 1200+ pages requires sufficient RAM
3. **Storage**: Embeddings for large books can be substantial
4. **UI**: Very long chapter lists benefit from virtual scrolling

## Next Steps

After uploading and testing these books:

1. ✅ Verify all chapters detected correctly
2. ✅ Test audio generation for sample chapters
3. ✅ Validate UI/UX with large chapter lists
4. ✅ Monitor performance and memory usage
5. ✅ Test search and navigation features
6. ✅ Validate progress tracking
7. ✅ Check mobile responsiveness

## Generated
- Date: 2025-11-13
- Generator: `generate_test_books.py`
- Version: 1.0
