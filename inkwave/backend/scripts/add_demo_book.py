"""
Add a comprehensive demo book for testing the "Start Listening" feature.

This script creates a book with rich, engaging content that demonstrates
the full InkWave experience with narration and Q&A capabilities.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/kasaai/.env')

from motor.motor_asyncio import AsyncIOMotorClient


# Rich demo book content
DEMO_BOOK = {
    "book_id": "demo_the_power_of_faith",
    "title": "The Power of Faith: A Journey to Spiritual Victory",
    "author": "Dr. Samuel Blessing",
    "isbn": "978-1-234567-89-0",
    "cover_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600&h=900&fit=crop",
    "pdf_url": None,
    "processed": True,
    "processing_status": "ready",
    "metadata": {
        "summary": "An inspiring journey through the transformative power of faith. This book explores how faith can move mountains, change circumstances, and bring victory in every area of life. Through practical examples, biblical teachings, and real-life testimonies, readers will discover how to activate their faith and experience God's supernatural power.",
        "themes": ["Faith", "Victory", "Prayer", "Spiritual Growth", "Breakthrough"],
        "genre": ["Christian Living", "Spiritual Growth", "Inspirational"],
        "page_count": 120,
        "word_count": 35000,
        "estimated_reading_time_minutes": 180,
        "difficulty_level": "intermediate",
        "language": "en"
    },
    "chapters": [
        {
            "title": "Chapter 1: Understanding Faith",
            "start_chunk_id": 0,
            "end_chunk_id": 4,
            "word_count": 2500
        },
        {
            "title": "Chapter 2: Faith That Moves Mountains",
            "start_chunk_id": 5,
            "end_chunk_id": 9,
            "word_count": 2800
        },
        {
            "title": "Chapter 3: Walking in Victory",
            "start_chunk_id": 10,
            "end_chunk_id": 14,
            "word_count": 3000
        }
    ],
    "uploaded_by": "admin",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Rich content chunks for Chapter 1
CHAPTER_1_CHUNKS = [
    {
        "text": """Welcome to this transformative journey into the power of faith. Faith is not just a religious concept; it is the very foundation of our relationship with God and the key to unlocking His supernatural power in our lives.

In Hebrews 11:1, we read: "Now faith is the substance of things hoped for, the evidence of things not seen." This powerful definition reveals that faith is both substance and evidence. It is the tangible reality of what we believe, even when our physical eyes cannot see it.

Many believers struggle with faith because they treat it as a mystical, intangible force. But true biblical faith is concrete, practical, and activatable. It is the currency of heaven, the language God responds to, and the force that moves His hand on our behalf.

Throughout this book, we will explore the multifaceted nature of faith—how to develop it, strengthen it, activate it, and use it to overcome every obstacle in your path. Whether you're facing financial challenges, health issues, relationship problems, or spiritual warfare, faith is your answer.""",
        "chapter_id": 0,
        "word_count": 150
    },
    {
        "text": """The journey of faith begins with understanding its source. Romans 10:17 tells us, "So then faith comes by hearing, and hearing by the word of God." This verse reveals a profound truth: faith is not self-generated. It doesn't come from positive thinking, good intentions, or human willpower. True faith is birthed when we encounter God's Word.

Think of faith as a spiritual muscle. Just as physical muscles grow stronger through exercise, your faith grows stronger through consistent exposure to God's Word. Every time you read the Bible, meditate on Scripture, or hear sound biblical teaching, you are feeding your faith and starving your doubts.

But it's not enough to merely hear the Word—we must receive it with an open heart. The parable of the sower in Matthew 13 illustrates this beautifully. The same seed (God's Word) fell on different types of soil, producing vastly different results. The condition of your heart determines how much faith you can develop. Hard hearts produce no faith. Shallow hearts produce temporary faith. Distracted hearts produce unfruitful faith. But good, receptive hearts produce abundant, multiplying faith that bears fruit in every season.""",
        "chapter_id": 0,
        "word_count": 175
    },
    {
        "text": """One of the greatest misconceptions about faith is that it requires you to ignore reality or deny facts. Nothing could be further from the truth. Biblical faith doesn't deny what exists; it simply refuses to be limited by it. Faith acknowledges the problem but focuses on God's power to solve it.

Consider Abraham, our father of faith. When God promised him a son, Abraham didn't deny that he was old or that Sarah was barren. These were undeniable facts. But Abraham chose to focus not on the impossibility of his circumstances but on the unlimited power of his God. Romans 4:20-21 says, "He did not waver through unbelief regarding the promise of God, but was strengthened in his faith and gave glory to God, being fully persuaded that God had power to do what he had promised."

This is the essence of mature faith: being fully persuaded of God's ability regardless of circumstances. Abraham didn't just hope God might do something; he was fully convinced that what God promised, He would perform. This kind of faith doesn't come overnight. It is cultivated through years of walking with God, seeing His faithfulness, and building a history with Him.""",
        "chapter_id": 0,
        "word_count": 190
    },
    {
        "text": """Faith also requires action. James 2:26 reminds us that "faith without works is dead." This doesn't mean we earn God's favor through our actions, but rather that genuine faith always produces corresponding action. When you truly believe something, you act on it.

Imagine you're sitting in a sturdy chair right now. You have faith in that chair's ability to support your weight. How do you know? Because you sat down! You demonstrated your faith through action. If you truly doubted the chair's strength, you would refuse to sit. Similarly, biblical faith moves us from the place of mere mental agreement to active trust.

Throughout Scripture, we see this pattern repeatedly. Noah's faith led him to build an ark. Abraham's faith led him to leave his homeland. Moses' faith led him to confront Pharaoh. David's faith led him to face Goliath. In each case, faith wasn't passive—it was dynamic, active, and demonstrable.

What action is your faith calling you to take today? Perhaps it's forgiving someone who hurt you, starting that business, applying for that position, or simply obeying God in an area where you've been resistant. Remember: faith acts before it sees results, not after.""",
        "chapter_id": 0,
        "word_count": 200
    },
    {
        "text": """As we conclude this first chapter, I want to emphasize that faith is a journey, not a destination. You will experience seasons where your faith feels strong and unshakeable, and other seasons where doubt and fear try to overwhelm you. This is normal. Even the disciples, who walked with Jesus daily, struggled with faith at times.

The key is not to condemn yourself for moments of doubt but to consistently return to the source of faith: God's Word. Jesus said in Mark 9:24, "I believe; help my unbelief!" This honest prayer acknowledges both our faith and our need for God to strengthen it.

As you continue through this book, you'll discover practical strategies for building unshakeable faith, overcoming obstacles, and experiencing breakthrough in every area of your life. But it all begins here—with a decision to trust God's Word more than your circumstances, His promises more than your problems, and His power more than your limitations.

Take a moment right now to pray: "Father, I choose faith over fear, Your Word over my circumstances, and Your promises over my problems. Increase my faith and help me walk in victory. In Jesus' name, Amen." This is your faith declaration. Believe it, speak it, and watch God move on your behalf.""",
        "chapter_id": 0,
        "word_count": 215
    }
]

# Chapter 2 content
CHAPTER_2_CHUNKS = [
    {
        "text": """Faith that moves mountains—this is not hyperbole or spiritual exaggeration. It is a literal promise from Jesus Himself. In Matthew 17:20, Jesus declared, "Truly I tell you, if you have faith as small as a mustard seed, you can say to this mountain, 'Move from here to there,' and it will move. Nothing will be impossible for you."

Notice that Jesus didn't say we need massive faith to move mountains. He said we need mustard seed faith—one of the smallest seeds known in that region. The size of your faith is less important than the object of your faith. A tiny faith in a great God will accomplish more than great faith in yourself or your circumstances.

But what are these "mountains" Jesus refers to? They represent any obstacle, challenge, or impossibility standing between you and your destiny. It could be a financial mountain, a health mountain, a relationship mountain, or a spiritual mountain. Whatever it is, Jesus promises that faith has the power to move it.

The question is not whether God can move your mountain—He absolutely can. The question is whether you will activate your faith and speak to that mountain with authority and confidence in God's Word.""",
        "chapter_id": 1,
        "word_count": 185
    },
    {
        "text": """Mountain-moving faith requires three essential elements: belief, speech, and persistence. First, you must genuinely believe in your heart that God is able and willing to move your mountain. This isn't mere mental agreement—it's deep, settled conviction that refuses to waver despite contrary evidence.

Second, you must speak to your mountain. Notice in Mark 11:23, Jesus said we should speak TO the mountain, not just ABOUT it. Many believers constantly talk about their problems to everyone who will listen, but they never speak directly to those problems with the authority of God's Word. There is creative power in your words. What you consistently speak, you will eventually experience.

Third, mountain-moving faith requires persistence. Some mountains move instantly; others require sustained faith over time. Don't become discouraged if your mountain doesn't move immediately. Keep believing, keep speaking, keep standing on God's Word. Hebrews 10:35-36 encourages us: "So do not throw away your confidence; it will be richly rewarded. You need to persevere so that when you have done the will of God, you will receive what he has promised."

Your breakthrough is coming. Keep pushing, keep believing, keep declaring. The mountain will move!""",
        "chapter_id": 1,
        "word_count": 210
    },
    {
        "text": """One powerful example of mountain-moving faith is found in the story of Joshua and the Israelites at Jericho. They faced an impossible situation: massive walls protecting a fortified city, with no conventional way to breach them. But God gave them a strategy that required radical faith.

For six days, they marched around the city in silence. Imagine the internal battle: "This seems foolish. Nothing is happening. Maybe we heard God wrong." But they persisted. On the seventh day, they marched seven times, then shouted—and the walls collapsed! Their faith-filled obedience moved their mountain.

Your mountain might not fall on day one, or day two, or even day six. But if you keep marching in faith, keep obeying God's instructions, and keep believing His promises, your seventh day is coming. Your walls will fall. Your breakthrough will manifest.

The enemy wants you to give up one day before your miracle. Don't let him steal your victory! Hold fast to your confession of faith without wavering, for He who promised is faithful. Your mountain-moving moment is closer than you think.""",
        "chapter_id": 1,
        "word_count": 190
    },
    {
        "text": """It's also crucial to understand that moving mountains isn't just about changing your circumstances—it's about transforming you in the process. God uses mountain experiences to strengthen your faith, deepen your dependence on Him, and prepare you for greater assignments.

Think about it: if God removed every obstacle instantly, you would never develop spiritual muscle. You would remain spiritually weak and unable to handle greater responsibilities. The mountain is not your enemy—it's your opportunity. It's the resistance that builds your faith-strength.

Paul understood this principle. In 2 Corinthians 12:9-10, he wrote about his "thorn in the flesh," a persistent challenge God chose not to remove. Through this experience, Paul discovered that God's grace is sufficient and His power is perfected in weakness. Sometimes the greatest miracle isn't the removal of the mountain but the grace and strength to overcome it.

Whether God moves your mountain or gives you the faith to climb it, either way, you win. You emerge stronger, wiser, and more intimate with God. Your faith grows not in the absence of challenges but through the process of overcoming them.""",
        "chapter_id": 1,
        "word_count": 195
    },
    {
        "text": """As we close this chapter, I want to give you a practical exercise. Identify one specific mountain in your life right now. Write it down. Now, find three Scriptures that directly address this issue. Write them down. Every morning and evening for the next 21 days, speak those Scriptures aloud to your mountain with faith and authority.

Don't just read them passively—declare them boldly: "Mountain of [name your challenge], I speak to you in Jesus' name! The Word of God says [quote your Scripture]. I believe it, I receive it, and I declare that you must move!" This practice will revolutionize your faith and your results.

Remember, Jesus never said "hope that mountain moves" or "wish that mountain would move." He said to SPEAK to the mountain. Your words, filled with faith and backed by God's Word, carry supernatural power. Start speaking life, breakthrough, and victory over your situation today.

God is not looking for perfect faith—He's looking for persistent faith. He's not impressed by your strength—He's moved by your trust. So trust Him today, speak to your mountain, and watch what happens when faith meets the impossible. Your victory is inevitable when you refuse to quit believing!""",
        "chapter_id": 1,
        "word_count": 210
    }
]

# Chapter 3 content
CHAPTER_3_CHUNKS = [
    {
        "text": """Walking in victory is not a one-time event—it's a lifestyle. It's the daily practice of applying your faith to every situation, refusing to be defeated by circumstances, and consistently choosing God's truth over temporary feelings. This chapter will teach you how to maintain a victorious mindset regardless of what you face.

First, understand that victory is already yours. Jesus didn't leave you to fight for victory; He left you to fight FROM victory. At the cross, He declared, "It is finished!" The battle is won. The war is over. Every enemy has been defeated. Your job is not to achieve victory but to enforce it, walk in it, and demonstrate it.

1 Corinthians 15:57 proclaims: "But thanks be to God! He gives us the victory through our Lord Jesus Christ." Notice it says "gives"—present tense. Not "will give" in the future. Victory is your present possession, not your future hope. When you grasp this truth, it changes everything. You stop begging God for victory and start thanking Him for the victory you already have.

This is not presumption or arrogance—it's biblical faith. You're not claiming something that isn't yours; you're appropriating what Christ already purchased for you at Calvary.""",
        "chapter_id": 2,
        "word_count": 210
    },
    {
        "text": """Victorious living requires daily spiritual disciplines. Just as a soldier maintains his weapons and a runner trains consistently, you must maintain your spiritual life through prayer, Word study, worship, and fellowship. These aren't religious obligations—they're empowerment tools.

Prayer is your communication line with heaven. Through prayer, you access divine wisdom, receive strategic direction, and tap into supernatural power. Don't just pray when you're in crisis—pray consistently. Develop a prayer rhythm that keeps you connected to God throughout the day.

The Word of God is your spiritual food and your sword of offense. Psalm 119:11 says, "I have hidden your word in my heart that I might not sin against you." Memorize Scripture. Meditate on it. Let it renew your mind and transform your thinking. When the enemy attacks, you need immediate access to God's Word, and that only comes through consistent study and memorization.

Worship shifts your focus from your problems to God's power. When Paul and Silas worshiped in prison, their chains fell off and doors opened. Worship doesn't change God—it changes you. It adjusts your perspective, lifts your spirit, and positions you for breakthrough.""",
        "chapter_id": 2,
        "word_count": 200
    },
    {
        "text": """Another key to victorious living is guarding your mind. Proverbs 4:23 warns: "Above all else, guard your heart, for everything you do flows from it." Your mind is the battlefield where spiritual victories and defeats are determined. If the enemy can control your thoughts, he can control your life.

This is why Paul instructs us in Philippians 4:8 to think on things that are true, noble, right, pure, lovely, admirable, excellent, and praiseworthy. These aren't just nice suggestions—they're strategic spiritual warfare. Every thought you entertain either strengthens or weakens your faith, moves you toward victory or toward defeat.

Practice taking every thought captive to the obedience of Christ (2 Corinthians 10:5). When negative, fearful, or doubtful thoughts arise—and they will—don't just passively accept them. Challenge them with truth. Replace lies with Scripture. Refuse to meditate on anything that contradicts God's Word about you and your situation.

Remember: you can't stop birds from flying over your head, but you can stop them from building nests in your hair. Similarly, you can't prevent negative thoughts from coming, but you can refuse to dwell on them. This discipline is crucial for sustained victory.""",
        "chapter_id": 2,
        "word_count": 215
    },
    {
        "text": """Victorious Christians also understand the power of testimony. Revelation 12:11 says, "They triumphed over him by the blood of the Lamb and by the word of their testimony." Your testimony—the story of what God has done in your life—is a powerful weapon against the enemy and an encouragement to other believers.

Don't wait until your entire journey is complete to share your testimony. Testify in the midst of the battle. Declare what God is doing, even when you don't see the full manifestation yet. This isn't denial—it's prophetic declaration. You're calling those things that are not as though they are, just as Abraham did (Romans 4:17).

Your testimony also strengthens your own faith. When you recount God's faithfulness in past situations, it builds your confidence for current challenges. Create a "faith journal" where you record answered prayers, breakthrough moments, and divine interventions. When doubt tries to creep in, review your journal and remind yourself: "If God did it before, He'll do it again."

Moreover, your testimony gives hope to others who are facing similar battles. When they hear how God brought you through, they believe He can bring them through too. Your victory becomes their encouragement, creating a multiplication effect in the Kingdom.""",
        "chapter_id": 2,
        "word_count": 220
    },
    {
        "text": """As we conclude this final chapter, I want to leave you with this powerful truth: You are more than a conqueror through Christ who loves you (Romans 8:37). Not just a conqueror—more than a conqueror. This means you don't just barely win; you win decisively, overwhelmingly, with margin to spare.

The victorious life isn't about perfection—it's about progression. You won't win every battle on the first attempt. You'll face setbacks, make mistakes, and experience temporary defeats. But remember: a temporary setback is not a permanent defeat. Get back up, dust yourself off, realign with God's Word, and keep moving forward.

Your faith has brought you this far, and it will take you all the way to complete victory. Continue to walk by faith and not by sight. Continue to speak life and not death. Continue to trust God's promises more than your present circumstances. Continue to stand firm in the midst of storms.

The power of faith has changed your life, moved your mountains, and positioned you for victory. Now go forth and walk in the fullness of what Christ has provided. Your best days are not behind you—they're ahead of you. Your greatest victories are not in your past—they're in your future. Believe it, declare it, and walk in it. In Jesus' mighty name, Amen!""",
        "chapter_id": 2,
        "word_count": 230
    }
]


async def add_demo_book():
    """Add comprehensive demo book to database."""

    print("🚀 Adding comprehensive demo book to InkWave...\n")

    # Connect to MongoDB using credentials from .env
    mongo_url = 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin'
    client = AsyncIOMotorClient(mongo_url)
    db = client['inkwave']

    try:
        # Check if demo book already exists
        existing = await db.books.find_one({"book_id": DEMO_BOOK["book_id"]})
        if existing:
            print(f"⚠️  Demo book already exists. Deleting old version...\n")
            await db.books.delete_one({"book_id": DEMO_BOOK["book_id"]})
            await db.book_chunks.delete_many({"book_id": DEMO_BOOK["book_id"]})

        # Insert book
        await db.books.insert_one(DEMO_BOOK)
        print(f"✅ Created book: {DEMO_BOOK['title']}")
        print(f"   Author: {DEMO_BOOK['author']}")
        print(f"   Chapters: {len(DEMO_BOOK['chapters'])}\n")

        # Prepare all chunks
        all_chunks = CHAPTER_1_CHUNKS + CHAPTER_2_CHUNKS + CHAPTER_3_CHUNKS

        # Insert chunks
        chunk_documents = []
        for idx, chunk_data in enumerate(all_chunks):
            chunk_doc = {
                "book_id": DEMO_BOOK["book_id"],
                "chunk_id": f"{DEMO_BOOK['book_id']}_chunk_{idx}",
                "chunk_index": idx,
                "text": chunk_data["text"],
                "text_optimized": None,
                "chapter_id": chunk_data["chapter_id"],
                "vector_id": None,
                "word_count": chunk_data["word_count"],
                "audio_url": None,
                "audio_duration": None,
                "audio_provider": None,
                "audio_voice_id": None,
                "audio_speed": None,
                "audio_language": None,
                "audio_cost": None,
                "audio_generated_at": None,
                "created_at": datetime.utcnow()
            }
            chunk_documents.append(chunk_doc)

        if chunk_documents:
            await db.book_chunks.insert_many(chunk_documents)
            print(f"✅ Created {len(chunk_documents)} content chunks")
            print(f"   Total words: ~{sum(c['word_count'] for c in all_chunks)}")
            print(f"   Estimated listening time: ~15-20 minutes\n")

        # Summary
        print("📚 Demo Book Summary:")
        print(f"   Title: {DEMO_BOOK['title']}")
        print(f"   Status: {DEMO_BOOK['processing_status']}")
        print(f"   Chapters: {len(DEMO_BOOK['chapters'])}")
        print(f"   Chunks: {len(chunk_documents)}")
        print(f"   Theme: Inspirational Christian content about faith and victory")
        print(f"\n✨ Users can now click 'Start Listening' to hear this content!")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(add_demo_book())
