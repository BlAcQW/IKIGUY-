# How to Upload Demo Books to InkWave

## Quick Start Guide

### Step 1: Access Admin Panel
1. Navigate to: https://inkwave.ailabsafrica.com/admin/books/upload
2. Or click "Admin Panel" → "Book Creation" from the dashboard

### Step 2: Upload a Demo Book

**Option A: Small Demo Book (Recommended for First Test)**
- File: `/opt/kasaai/apps/inkwave/backend/test_books/binding_the_strong_man_demo.pdf`
- Size: 11 KB
- Pages: 10
- Chapters: 4
- Processing Time: ~30 seconds

**Option B: Large Test Books**
- Power of Forgiveness: 579 KB, 1053 pages, 70 chapters
- Destined to Win: 661 KB, 1203 pages, 80 chapters
- Spiritual Authority: 295 KB, 528 pages, 35 chapters

### Step 3: Fill in Book Metadata

**For "Binding The Strong Man" Demo:**
```
Title: Binding The Strong Man
Author: Archbishop Nicholas Duncan-Williams
Description: A powerful study on spiritual warfare and breaking free from demonic strongholds. Learn to identify the strong man, use spiritual weapons, and walk in victory.
Cover URL: https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&h=600&fit=crop
Duration (optional): 45 minutes
Narrator (optional): Archbishop Duncan-Williams
```

**Alternative Cover Images:**
- Spiritual book: https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=600&fit=crop
- Open Bible: https://images.unsplash.com/photo-1542280756-74b2f55e73ab?w=400&h=600&fit=crop
- Prayer hands: https://images.unsplash.com/photo-1605629921711-2f6b00c6bbf4?w=400&h=600&fit=crop

### Step 4: Monitor Processing
- Watch the upload progress bar
- Processing status will update automatically
- Book will appear in "Recent Uploads" section when complete

### Step 5: View on User Pages
Once uploaded, the book will be visible on:
1. **Homepage** (https://inkwave.ailabsafrica.com)
   - "Continue Listening" shelf (if you started it)
   - "Recommended for You" (if personalization is enabled)
   - "Latest Messages" (newest books)

2. **All Books Page** (https://inkwave.ailabsafrica.com/all-books)
   - Grid view of all books
   - Search and filter functionality
   - Pagination

3. **Browse Page** (https://inkwave.ailabsafrica.com/browse)
   - Browse by category
   - Browse by author

4. **Library Page** (https://inkwave.ailabsafrica.com/library)
   - Your personal library
   - Books you've started or bookmarked

### Step 6: Test Audio Generation
1. Click on the uploaded book to open player
2. Click "Generate Audio Narration" button
3. Wait for TTS generation (~30 seconds for demo book)
4. Test playback controls:
   - Play/Pause (central button)
   - Skip backward 15s (left button)
   - Skip forward 15s (right button)
   - Playback speed (below controls)
   - Progress bar seeking
   - Chapter navigation (table of contents)

### Step 7: Test Large Books UI
Upload one of the large books to test:
- Section grouping in table of contents (70+ chapters)
- Chapter search functionality
- Progress indicators
- Auto-scroll to current chapter
- Jump to current chapter button

## Troubleshooting

### Book Not Appearing on Homepage
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Check "All Books" page - it always shows all uploaded books
- Wait a few seconds for backend processing

### Processing Failed
- Check backend logs: `sudo journalctl -u kasaai-inkwave-backend -f`
- Verify MongoDB is running: `sudo systemctl status mongod`
- Check book processing status in database

### Audio Generation Fails
- Ensure TTS service is configured in provider management
- Check voice settings (/voice-settings)
- Try a different TTS provider
- Check backend logs for errors

## Expected Processing Times

| Book | Pages | Upload | Processing | Audio Gen |
|------|-------|--------|------------|-----------|
| Demo (10p) | 10 | < 5s | ~30s | ~45s |
| Medium (500p) | 528 | < 10s | ~2min | ~5min* |
| Large (1000p) | 1053 | < 15s | ~4min | ~10min* |
| Very Large (1200p) | 1203 | < 20s | ~5min | ~12min* |

*Audio generation time depends on TTS provider and chapter length

## Viewing Test Books as User

### Scenario 1: New User Experience
1. Open incognito/private browser window
2. Navigate to https://inkwave.ailabsafrica.com
3. View hero banner with featured book
4. Scroll to see book shelves
5. Click on a book to open player
6. Test audio generation and playback

### Scenario 2: Browse All Books
1. Navigate to /all-books
2. View grid of all uploaded books
3. Test search: "Binding"
4. Test filter by genre: "Spiritual Warfare"
5. Click pagination if 24+ books

### Scenario 3: Category Browse
1. Navigate to /browse
2. Click on category: "Prayer", "Faith", "Deliverance", etc.
3. View books in that category

## File Locations

```
Test Books:
/opt/kasaai/apps/inkwave/backend/test_books/
├── binding_the_strong_man_demo.pdf (11 KB - Quick Demo)
├── power_of_forgiveness.pdf (579 KB - Large Book Test)
├── spiritual_authority.pdf (295 KB - Medium Book Test)
├── destined_to_win.pdf (661 KB - Very Large Book Test)
└── README.md (Documentation)

Upload Scripts:
/opt/kasaai/apps/inkwave/backend/scripts/
├── generate_demo_book.py (Creates 10-page demo)
└── generate_test_books.py (Creates 1000+ page books)
```

## Demo Book Content

**Binding The Strong Man** includes:
- Chapter 1: Understanding Spiritual Warfare
- Chapter 2: Identifying the Strong Man
- Chapter 3: The Weapons of Our Warfare
- Chapter 4: Breaking Free from Bondage
- Conclusion: Walking in Victory

**Note**: This is original demo content created for testing, NOT the actual copyrighted book.

## Next Steps After Upload

1. ✅ Verify book appears on user pages
2. ✅ Test audio generation
3. ✅ Test player UI with all features
4. ✅ Test chapter navigation
5. ✅ Test progress tracking
6. ✅ Test Voice Q&A feature
7. ✅ Upload additional books for variety

## Verification Scripts

### Quick Verification

After uploading books, verify they're displaying correctly:

```bash
cd /opt/kasaai/apps/inkwave/backend
source ../../venv/bin/activate
python scripts/verify_book_display.py
```

This will check:
- ✅ Books appear in API
- ✅ Search functionality works
- ✅ User page endpoints are accessible
- ✅ Demo book is present

### Check Specific Book

```bash
python scripts/verify_book_display.py <book_id>
```

Example:
```bash
python scripts/verify_book_display.py book_g8v8sja2luh
```

## Current Status

**Books in System**: 4 books including "Binding The Strong Man"
**User Pages**: All working correctly ✅
**Search**: Functioning ✅
**API Endpoints**: Operational ✅

## Support

If you encounter issues:
1. Run verification script: `python scripts/verify_book_display.py`
2. Check browser console for errors (F12)
3. Check backend logs: `sudo journalctl -u kasaai-inkwave-backend -f`
4. Verify database connectivity
5. Review API endpoints in /api/v1/docs
