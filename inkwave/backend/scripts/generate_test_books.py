"""
Generate Test Books for InkWave Development

Creates realistic PDF books with 1000+ pages for testing:
- Text extraction performance
- Chapter detection accuracy
- TTS generation with long content
- UI/UX with large books
- Memory management
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime


def generate_spiritual_content(chapter_num: int, pages_per_chapter: int = 15) -> list:
    """
    Generate realistic spiritual/religious content for a chapter.

    Args:
        chapter_num: Chapter number
        pages_per_chapter: Number of pages per chapter

    Returns:
        List of paragraphs for the chapter
    """

    # Sample spiritual content templates
    chapter_titles = [
        "The Foundation of Faith",
        "Understanding Divine Purpose",
        "Walking in Spiritual Authority",
        "The Power of Prayer and Fasting",
        "Overcoming Life's Challenges",
        "Building Strong Relationships",
        "Financial Stewardship and Prosperity",
        "Healing and Restoration",
        "The Gift of Forgiveness",
        "Living a Life of Worship",
        "Developing Spiritual Discipline",
        "The Ministry of Reconciliation",
        "Breaking Free from Bondage",
        "Embracing Your Destiny",
        "The Fruit of the Spirit",
        "Leadership and Servanthood",
        "Cultivating a Prayer Life",
        "Understanding Spiritual Warfare",
        "The Importance of Community",
        "Walking in Love and Grace"
    ]

    sample_paragraphs = [
        "In our journey of faith, we must understand that spiritual growth is not an event but a process. It requires dedication, commitment, and a genuine desire to know God more intimately. As we press forward in our spiritual walk, we discover that each challenge we face is an opportunity for growth and transformation.",

        "The scriptures teach us that faith without works is dead. This means that our belief must be accompanied by action. We cannot simply profess faith while living lives that contradict our profession. True faith manifests itself in how we treat others, how we conduct our business, and how we respond to life's challenges.",

        "Prayer is the foundation of our relationship with God. It is through prayer that we communicate with our Creator, express our needs, and receive divine guidance. A consistent prayer life is essential for anyone who desires to walk in spiritual maturity and understand God's will for their life.",

        "Forgiveness is one of the most powerful spiritual principles we can practice. When we forgive others, we release ourselves from the burden of bitterness and resentment. Forgiveness opens the door to healing, restoration, and the manifestation of God's blessings in our lives.",

        "God has called each of us to a specific purpose. This purpose is unique to our individual gifts, talents, and circumstances. Discovering and walking in our divine purpose brings fulfillment, joy, and a sense of meaning that transcends our temporary circumstances.",

        "Spiritual warfare is a reality that every believer must understand and prepare for. We wrestle not against flesh and blood, but against spiritual forces of darkness. Understanding our spiritual authority and the weapons of our warfare is essential for victory in our spiritual battles.",

        "The fruit of the Spirit - love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, and self-control - are evidence of God's transforming work in our lives. As we yield to the Holy Spirit, these qualities naturally develop and manifest in our character.",

        "Financial stewardship is a spiritual responsibility. God has entrusted us with resources, and we must be faithful managers of what He has given us. This includes tithing, giving, saving, and making wise financial decisions that honor God and bless others.",

        "Healing and restoration are part of God's redemptive plan for humanity. Whether physical, emotional, or spiritual, God desires to make us whole. Through faith, prayer, and obedience to His word, we can experience the healing power of God in every area of our lives.",

        "Building strong, healthy relationships is crucial for our spiritual and emotional wellbeing. The quality of our relationships reflects our spiritual maturity and our capacity to love as God loves. We must intentionally cultivate relationships that honor God and edify one another."
    ]

    story_elements = [
        "Consider the story of a young believer who faced tremendous adversity. Through unwavering faith and persistent prayer, they witnessed God's miraculous intervention in their circumstances. This testimony reminds us that God is faithful even in our darkest moments.",

        "Throughout history, men and women of faith have demonstrated extraordinary courage in the face of persecution and opposition. Their examples inspire us to stand firm in our convictions and trust God regardless of our circumstances.",

        "In practical application, this principle transforms how we approach daily challenges. Instead of responding in fear or anxiety, we learn to rest in God's promises and trust His timing. This shift in perspective brings peace and confidence in every situation.",

        "The early church provides powerful examples of community and fellowship. Believers shared their resources, prayed together, and supported one another through trials. This model of Christian community remains relevant for us today.",

        "When we examine the lives of biblical characters, we see a pattern of God using ordinary people to accomplish extraordinary things. This encourages us that God can use anyone who is willing and available to Him."
    ]

    content = []

    # Chapter title
    title_idx = (chapter_num - 1) % len(chapter_titles)
    chapter_title = f"Chapter {chapter_num}: {chapter_titles[title_idx]}"

    # Add content for each page
    for page in range(pages_per_chapter):
        # Section heading every few pages
        if page % 5 == 0 and page > 0:
            section_num = (page // 5)
            content.append(("heading", f"Section {section_num}: Key Principles"))

        # Add 2-3 paragraphs per page
        num_paragraphs = 3 if page % 2 == 0 else 2
        for _ in range(num_paragraphs):
            para_text = sample_paragraphs[hash(f"{chapter_num}{page}{_}") % len(sample_paragraphs)]
            content.append(("paragraph", para_text))

        # Occasionally add story elements
        if page % 7 == 0:
            story_text = story_elements[hash(f"story{chapter_num}{page}") % len(story_elements)]
            content.append(("story", story_text))

    return chapter_title, content


def create_large_pdf_book(
    output_path: str,
    title: str,
    author: str,
    num_chapters: int = 70,
    pages_per_chapter: int = 15
):
    """
    Create a large PDF book with realistic content.

    Args:
        output_path: Path to save the PDF
        title: Book title
        author: Book author
        num_chapters: Number of chapters (default 70 = ~1050 pages)
        pages_per_chapter: Pages per chapter
    """

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Container for the 'Flowable' objects
    story = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor='gray',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    chapter_title_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor='darkblue',
        spaceAfter=20,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='darkblue',
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=14,
        fontName='Helvetica'
    )

    story_style = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        spaceBefore=6,
        leftIndent=20,
        rightIndent=20,
        fontName='Helvetica-Oblique',
        textColor='darkgray'
    )

    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"by {author}", author_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %Y')}", author_style))
    story.append(PageBreak())

    # Copyright page
    copyright_text = f"""
    Copyright © {datetime.now().year} {author}<br/>
    <br/>
    All rights reserved. This book is a test document generated for development purposes.<br/>
    <br/>
    Generated by InkWave Test Book Generator<br/>
    <br/>
    This is sample content created for testing audiobook functionality,
    including text extraction, chapter detection, and TTS generation.
    """
    story.append(Paragraph(copyright_text, body_style))
    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("Table of Contents", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    for i in range(1, num_chapters + 1):
        title_idx = (i - 1) % 20
        chapter_titles = [
            "The Foundation of Faith", "Understanding Divine Purpose",
            "Walking in Spiritual Authority", "The Power of Prayer and Fasting",
            "Overcoming Life's Challenges", "Building Strong Relationships",
            "Financial Stewardship and Prosperity", "Healing and Restoration",
            "The Gift of Forgiveness", "Living a Life of Worship",
            "Developing Spiritual Discipline", "The Ministry of Reconciliation",
            "Breaking Free from Bondage", "Embracing Your Destiny",
            "The Fruit of the Spirit", "Leadership and Servanthood",
            "Cultivating a Prayer Life", "Understanding Spiritual Warfare",
            "The Importance of Community", "Walking in Love and Grace"
        ]
        toc_entry = f"Chapter {i}: {chapter_titles[title_idx]}"
        story.append(Paragraph(toc_entry, body_style))

    story.append(PageBreak())

    # Generate chapters
    print(f"Generating {num_chapters} chapters...")
    for chapter_num in range(1, num_chapters + 1):
        print(f"  Chapter {chapter_num}/{num_chapters}...")

        chapter_title, content = generate_spiritual_content(chapter_num, pages_per_chapter)

        # Chapter title
        story.append(Paragraph(chapter_title, chapter_title_style))
        story.append(Spacer(1, 0.3*inch))

        # Chapter content
        for content_type, text in content:
            if content_type == "heading":
                story.append(Paragraph(text, heading_style))
            elif content_type == "paragraph":
                story.append(Paragraph(text, body_style))
            elif content_type == "story":
                story.append(Paragraph(text, story_style))

        # Chapter break
        story.append(PageBreak())

    # Build PDF
    print("Building PDF...")
    doc.build(story)
    print(f"✅ PDF created: {output_path}")

    # Get file size
    file_size = os.path.getsize(output_path)
    file_size_mb = file_size / (1024 * 1024)
    total_pages = num_chapters * pages_per_chapter + 3  # +3 for title, copyright, TOC

    print(f"   Total pages: {total_pages}")
    print(f"   File size: {file_size_mb:.2f} MB")


def main():
    """Generate multiple test books."""

    # Create output directory
    output_dir = Path(__file__).parent.parent / "test_books"
    output_dir.mkdir(exist_ok=True)

    print("🎯 InkWave Test Book Generator")
    print("=" * 60)

    # Book 1: Large spiritual book (1000+ pages)
    print("\n📚 Book 1: The Power of Forgiveness (1000+ pages)")
    create_large_pdf_book(
        output_path=str(output_dir / "power_of_forgiveness.pdf"),
        title="The Power of Forgiveness",
        author="Archbishop Nicholas Duncan-Williams",
        num_chapters=70,  # 70 chapters × 15 pages = 1050 pages
        pages_per_chapter=15
    )

    # Book 2: Medium book (500 pages)
    print("\n📚 Book 2: Walking in Spiritual Authority (500+ pages)")
    create_large_pdf_book(
        output_path=str(output_dir / "spiritual_authority.pdf"),
        title="Walking in Spiritual Authority",
        author="Archbishop Nicholas Duncan-Williams",
        num_chapters=35,  # 35 chapters × 15 pages = 525 pages
        pages_per_chapter=15
    )

    # Book 3: Another large book (1200+ pages)
    print("\n📚 Book 3: Destined to Win (1200+ pages)")
    create_large_pdf_book(
        output_path=str(output_dir / "destined_to_win.pdf"),
        title="Destined to Win",
        author="Archbishop Nicholas Duncan-Williams",
        num_chapters=80,  # 80 chapters × 15 pages = 1200 pages
        pages_per_chapter=15
    )

    print("\n" + "=" * 60)
    print(f"✅ All test books generated successfully!")
    print(f"📁 Location: {output_dir}")
    print("\nNext steps:")
    print("1. Upload these books via the InkWave admin panel")
    print("2. Test book processing and chapter detection")
    print("3. Generate audio and test playback performance")
    print("4. Evaluate UI/UX with large books")


if __name__ == "__main__":
    main()
