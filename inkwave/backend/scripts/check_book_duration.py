"""
Check book content word count and estimate audio duration.
"""

import PyPDF2
from pathlib import Path


def count_words_in_pdf(pdf_path: str) -> dict:
    """
    Count words in PDF and estimate audio duration.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with word counts and duration estimates
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)

        total_text = ""
        for page in pdf_reader.pages:
            total_text += page.extract_text()

        # Count words
        words = total_text.split()
        word_count = len(words)

        # Estimate duration (150 words per minute for TTS)
        duration_minutes = word_count / 150
        duration_seconds = duration_minutes * 60

        return {
            "pages": num_pages,
            "words": word_count,
            "duration_minutes": round(duration_minutes, 2),
            "duration_seconds": round(duration_seconds, 2),
            "words_per_page": round(word_count / num_pages, 2)
        }


if __name__ == "__main__":
    pdf_path = Path(__file__).parent.parent / "test_books" / "binding_the_strong_man_demo.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        exit(1)

    stats = count_words_in_pdf(str(pdf_path))

    print("\n📊 Book Content Analysis")
    print("=" * 60)
    print(f"PDF File: {pdf_path.name}")
    print(f"Total Pages: {stats['pages']}")
    print(f"Total Words: {stats['words']:,}")
    print(f"Words per Page: {stats['words_per_page']}")
    print(f"\n🎧 Audio Duration Estimate (at 150 words/min):")
    print(f"   {stats['duration_minutes']:.1f} minutes")
    print(f"   {stats['duration_seconds']:.0f} seconds")
    print(f"\n✅ Target: 5+ minutes per chapter")

    if stats['duration_minutes'] >= 20:
        print(f"✅ PASS: Book has enough content for 5+ min/chapter")
    else:
        print(f"⚠️  WARNING: Book may need more content")

    print("=" * 60)
