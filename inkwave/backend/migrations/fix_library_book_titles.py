#!/usr/bin/env python3
"""
Migration script to fix missing book_title fields in library_books.

This script:
1. Finds all users with library_books missing book_title
2. Looks up book details from the books collection
3. Updates the user documents with the correct book_title

Date: 2025-12-18
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment
load_dotenv("/opt/kasaai/.env")

def fix_library_book_titles():
    """Fix missing book_title fields in user library_books."""

    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["inkwave"]

    print("=" * 60)
    print("MIGRATION: Fix Missing book_title in library_books")
    print("=" * 60)

    # Find users with library_books
    users = list(db.users.find(
        {"library_books": {"$exists": True, "$ne": []}},
        {"user_id": 1, "email": 1, "library_books": 1}
    ))

    print(f"\nTotal users with library books: {len(users)}")

    # Track statistics
    users_fixed = 0
    books_fixed = 0
    errors = []

    # Check each user
    for user in users:
        user_updated = False
        library_books = user.get("library_books", [])

        for idx, book in enumerate(library_books):
            # Check if book_title is missing or None
            if "book_title" not in book or book.get("book_title") is None:
                book_id = book.get("book_id")

                if not book_id:
                    error_msg = f"User {user['email']}: library_books[{idx}] has no book_id"
                    print(f"  ⚠️  {error_msg}")
                    errors.append(error_msg)
                    continue

                # Look up book details
                book_doc = db.books.find_one({"book_id": book_id}, {"title": 1, "cover_url": 1, "author": 1})

                if not book_doc:
                    error_msg = f"User {user['email']}: Book {book_id} not found in books collection"
                    print(f"  ⚠️  {error_msg}")
                    errors.append(error_msg)
                    continue

                # Update the book entry
                library_books[idx]["book_title"] = book_doc.get("title", "Unknown Title")

                # Also update other fields if missing
                if "book_cover_url" not in library_books[idx]:
                    library_books[idx]["book_cover_url"] = book_doc.get("cover_url")
                if "book_author" not in library_books[idx]:
                    library_books[idx]["book_author"] = book_doc.get("author")

                user_updated = True
                books_fixed += 1
                print(f"  ✓ Fixed: {user['email']} - {book_doc.get('title')} ({book_id})")

        # Update user document if changes were made
        if user_updated:
            result = db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {"library_books": library_books}}
            )

            if result.modified_count > 0:
                users_fixed += 1
            else:
                error_msg = f"Failed to update user {user['email']}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Users fixed: {users_fixed}")
    print(f"Book entries fixed: {books_fixed}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")

    print("\n✅ Migration completed successfully!")

    client.close()
    return users_fixed, books_fixed, len(errors)


if __name__ == "__main__":
    try:
        users_fixed, books_fixed, error_count = fix_library_book_titles()
        sys.exit(0 if error_count == 0 else 1)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
