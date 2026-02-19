# InkWave Book URLs - Quick Reference

## Available Books (Updated 2025-11-26)

### 1. The Power of Faith (Demo Book)
**Author**: Dr. Samuel Blessing
**Player URL**: https://inkwave.ailabsafrica.com/player/demo_the_power_of_faith
**Book ID**: `demo_the_power_of_faith`

### 2. Binding the Strongman
**Author**: Archbishop Nicholas Duncan-Williams
**Player URL**: https://inkwave.ailabsafrica.com/player/book_4e7e2cd00a92
**Book ID**: `book_4e7e2cd00a92`

### 3. Enforcing Prophetic Decrees
**Author**: Archbishop Nicholas Duncan-Williams
**Player URL**: https://inkwave.ailabsafrica.com/player/book_b30c7a7e378d
**Book ID**: `book_b30c7a7e378d`

### 4. Turning Pain to Power
**Author**: Archbishop Nicholas Duncan-Williams
**Player URL**: https://inkwave.ailabsafrica.com/player/book_bb72e2ee222e
**Book ID**: `book_bb72e2ee222e`

### 5. Prayer Moves God
**Author**: Archbishop Nicholas Duncan-Williams
**Player URL**: https://inkwave.ailabsafrica.com/player/book_73b23ac59369
**Book ID**: `book_73b23ac59369`

### 6. Powers Behind the Scenes
**Author**: Archbishop Nicholas Duncan-Williams
**Player URL**: https://inkwave.ailabsafrica.com/player/book_12be146ff4f9
**Book ID**: `book_12be146ff4f9`

## Other Pages

- **Homepage**: https://inkwave.ailabsafrica.com/
- **All Books**: https://inkwave.ailabsafrica.com/all-books
- **Browse**: https://inkwave.ailabsafrica.com/browse
- **Library**: https://inkwave.ailabsafrica.com/library
- **Admin Upload**: https://inkwave.ailabsafrica.com/admin/books/upload

## Notes

- Book IDs use the format `book_XXXXXXX` (not simple numbers like 1, 2, 3)
- Accessing an invalid book ID will now show a proper error page with:
  - Clear error message
  - "Browse All Books" button
  - "Go Back" button
- All books are accessible to both authenticated and anonymous users

## Verification

To verify all books are working, run:
```bash
cd /opt/kasaai/apps/inkwave/backend
source ../../venv/bin/activate
python scripts/verify_book_display.py
```

To check a specific book:
```bash
python scripts/verify_book_display.py book_g8v8sja2luh
```

## Demo Book

The 10-page demo book is available for upload at:
`/opt/kasaai/apps/inkwave/backend/test_books/binding_the_strong_man_demo.pdf`

See [UPLOAD_INSTRUCTIONS.md](UPLOAD_INSTRUCTIONS.md) for upload guide.
