"""
Generate Small Demo Book for Testing

Creates a 10-page demo book for quick testing of:
- Book upload workflow
- Text extraction
- Chapter detection
- Audio generation
- Player UI
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime


def create_demo_book(output_path: str):
    """
    Create a small 10-page demo book with original spiritual content.

    Args:
        output_path: Path to save the PDF
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
        fontSize=28,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor='gray',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    chapter_title_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor='darkblue',
        spaceAfter=20,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_JUSTIFY,
        spaceAfter=14,
        leading=16,
        fontName='Helvetica'
    )

    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Binding The Strong Man", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("A Demo Study on Spiritual Warfare", author_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("by Archbishop Nicholas Duncan-Williams", author_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Demo Edition • {datetime.now().strftime('%B %Y')}", author_style))
    story.append(PageBreak())

    # Copyright page
    copyright_text = """
    Demo Edition - For Testing Purposes Only<br/>
    <br/>
    This is original demo content created for testing InkWave's audiobook functionality.
    This is NOT the actual copyrighted book by Archbishop Nicholas Duncan-Williams.<br/>
    <br/>
    Content © 2025 InkWave Test Content Generator<br/>
    <br/>
    This demo book is designed to test:<br/>
    - PDF text extraction<br/>
    - Chapter detection<br/>
    - TTS audio generation<br/>
    - Audiobook player UI/UX<br/>
    """
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(copyright_text, body_style))
    story.append(PageBreak())

    # Chapter 1
    story.append(Paragraph("Chapter 1: Understanding Spiritual Warfare", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    chapter1_content = [
        "In our walk with God, we must recognize that we are engaged in a spiritual battle. The apostle Paul reminds us in Ephesians 6:12 that we do not wrestle against flesh and blood, but against principalities, against powers, against the rulers of the darkness of this age, against spiritual hosts of wickedness in the heavenly places. This profound revelation changes everything about how we approach our Christian journey. When we understand that our real enemies are not the people we see, but the spiritual forces working behind the scenes, we can redirect our prayers, our warfare, and our spiritual strategies appropriately. Too many believers waste their energy fighting against flesh and blood, when their real battle is in the spiritual realm.",

        "Understanding the nature of this warfare is crucial for every believer. Many Christians go through life unaware that they are in a battle, and as a result, they become casualties of war. The enemy is real, his tactics are strategic, and his goal is to steal, kill, and destroy everything God has planned for your life. Satan is not some mythical figure with a red suit and pitchfork. He is a fallen angel who once held a high position in heaven, and he understands spiritual authority and protocol. He knows the Word of God, he understands legal rights and spiritual jurisdiction, and he has had thousands of years to study human behavior and perfect his tactics of deception, temptation, and destruction. When you underestimate your enemy, you make yourself vulnerable to his attacks.",

        "The enemy operates through well-organized hierarchies and systems. Ephesians chapter six reveals that there are different ranks in the demonic kingdom - principalities, powers, rulers of darkness, and spiritual wickedness in high places. Each of these represents different levels of authority and different spheres of operation in the kingdom of darkness. Principalities rule over territories and regions. Powers enforce the will of these principalities. Rulers of darkness maintain systems of ignorance and spiritual blindness. And spiritual wickedness in high places operates in the heavenly realms, influencing governments, institutions, and cultural systems. Understanding this structure helps us know how to pray strategically and how to engage the enemy effectively.",

        "However, we serve a God who has already won the victory. Through Jesus Christ, we have been given authority over all the power of the enemy. The question is not whether we have the power to win, but whether we will exercise that authority and stand firm in the battle. Jesus declared in Luke 10:19, 'Behold, I give you the authority to trample on serpents and scorpions, and over all the power of the enemy, and nothing shall by any means hurt you.' This is not a promise for the future - this is a present reality. You have been given authority right now. The power has been delegated to you. But like any authority, it must be exercised. A police officer has authority, but if he never shows up to work, criminals will run rampant. Your authority is only effective when you use it.",

        "This chapter will equip you with foundational truths about spiritual warfare. We will examine the enemy's strategies, understand our position in Christ, and learn how to effectively engage in the battle. Remember, knowledge is power, but applied knowledge is victory. You can know all the right Bible verses, understand all the principles of spiritual warfare, and still be defeated if you never apply what you know. James 4:7 tells us to resist the devil and he will flee from us. But resistance requires action. It requires you to stand up, speak out, and enforce the victory that Jesus has already won. In the pages that follow, you will learn not just theory, but practical strategies that you can implement immediately to see breakthrough in your life. Get ready for transformation, because your understanding of spiritual warfare is about to shift dramatically.",
    ]

    for para in chapter1_content:
        story.append(Paragraph(para, body_style))

    story.append(PageBreak())

    # Chapter 2
    story.append(Paragraph("Chapter 2: Identifying the Strong Man", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    chapter2_content = [
        "Jesus spoke of binding the strong man in Matthew 12:29: 'Or how can one enter a strong man's house and plunder his goods, unless he first binds the strong man? And then he will plunder his house.' This passage reveals a powerful spiritual principle that every believer must understand. Jesus was not speaking in parables here - He was giving us a precise military strategy for spiritual warfare. When you want to invade enemy territory and take back what belongs to you, you cannot just walk in casually. You must first deal with the strongman who is guarding that territory. This is the key to breakthrough in areas where you have experienced stubborn resistance and persistent attacks.",

        "The 'strong man' represents the ruling demonic force that has been assigned against your life, your family, your ministry, or your destiny. These are not ordinary demons, but principalities that have been strategically positioned to hinder the purposes of God in your life. Think of it like a military operation. In any army, there are generals and there are foot soldiers. The foot soldiers follow orders, but the generals give the orders. When you bind the general, the foot soldiers become disorganized and ineffective. Similarly, in the spiritual realm, there are ruling spirits - strong men - who coordinate attacks against specific areas of your life. When you identify and bind that strong man, all the lesser demons under his command lose their coordination and power.",

        "Identifying the strong man requires spiritual discernment. You must be able to recognize the patterns of attack in your life. Is it always the same area? Does the same problem keep recurring despite your prayers and efforts? Do you see generational patterns of failure, sickness, poverty, or broken relationships? These are indicators that there may be a strong man at work. For example, if every business you start fails, there may be a strong man of poverty operating against you. If every relationship ends in betrayal and hurt, there may be a strong man of rejection assigned to your life. If you constantly battle with the same sin no matter how hard you try to break free, there is likely a strong man maintaining that bondage. The recurring nature of the problem is the fingerprint of the strong man.",

        "The strategy of the strong man is to establish strongholds - fortified places of resistance in your life. Second Corinthians 10:4 talks about pulling down strongholds. These strongholds are mental fortresses, belief systems, and thought patterns that have been constructed by the enemy to keep you in bondage. The strong man builds these strongholds over time through repeated attacks, trauma, generational curses, and agreements we make with lies. For instance, if you were repeatedly told as a child that you would never amount to anything, that lie can become a stronghold. The strong man of failure then has a legal right to operate in your life based on that belief system. Breaking the stronghold requires renewing your mind with the truth of God's Word and verbally breaking agreement with every lie you have believed.",

        "The good news is that once you identify the strong man, you can bind him through prayer, fasting, and the authority of God's Word. Jesus has given us the keys to the kingdom, and whatever we bind on earth is bound in heaven. This is not just theoretical theology - this is practical spiritual warfare that produces real results. When you bind the strong man in prayer, you are exercising your delegated authority as a believer. You are enforcing the victory that Jesus won on the cross. The enemy has no legal authority over your life unless you give it to him through sin, disobedience, or agreement with his lies. But when you stand on the Word of God, repent of every open door, and exercise your authority in Christ, you can bind any strong man and render him powerless. Then, and only then, can you plunder his house and take back everything he has stolen from you - your health, your finances, your relationships, your peace, your joy, and your destiny.",
    ]

    for para in chapter2_content:
        story.append(Paragraph(para, body_style))

    story.append(PageBreak())

    # Chapter 3
    story.append(Paragraph("Chapter 3: The Weapons of Our Warfare", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    chapter3_content = [
        "Second Corinthians 10:4 declares that 'the weapons of our warfare are not carnal but mighty in God for pulling down strongholds.' We cannot fight a spiritual battle with natural weapons. We need supernatural weapons that are divinely powerful to demolish the enemy's fortresses. This is a critical truth that many believers miss. They try to fight spiritual battles with natural solutions - therapy when deliverance is needed, medication when healing is available, or financial schemes when God wants to break the spirit of poverty. While these natural tools have their place, they cannot address the root spiritual issue. Only spiritual weapons can demolish spiritual strongholds. God has provided us with an arsenal of weapons that are backed by His divine power, and when we learn to use them effectively, no enemy can stand against us.",

        "The Word of God is our primary weapon. It is described as the sword of the Spirit, sharp and powerful, able to divide soul and spirit, joints and marrow. When Jesus was tempted in the wilderness, He defeated Satan with the simple phrase, 'It is written.' The Word of God in your mouth becomes a weapon in your hand. But notice that Jesus did not just know the Word - He spoke it out loud. There is power in verbally declaring the Word of God. Hebrews 4:12 tells us that the Word is living and active. It is not dead information on a page. When you speak it, it becomes a spiritual force that cuts through demonic resistance. Every promise in the Bible is a weapon you can use against the enemy. When he tells you that you are sick, you can declare, 'By His stripes I am healed.' When he tells you that you are broke, you can declare, 'My God shall supply all my needs according to His riches in glory.' The Word of God never fails, and when you stand on it and speak it, the enemy must bow.",

        "Prayer is another mighty weapon in our arsenal. Not just casual prayer, but fervent, persistent, faith-filled prayer that moves heaven and changes circumstances on earth. James 5:16 tells us that the effective, fervent prayer of a righteous person avails much. When we pray in alignment with God's will, we release divine power into our situations. The key to effective prayer is understanding both your authority and God's will. You do not beg God for things He has already promised. You stand on His promises and declare them in prayer. You bind the works of the enemy and loose the blessings of God. You take your position as a co-laborer with Christ and enforce the victory of the cross. This kind of prayer changes things. It shifts atmospheres. It breaks chains. It opens doors that no man can shut. And it closes doors that no man can open. When you pray with authority, heaven responds and earth conforms.",

        "Fasting amplifies our spiritual sensitivity and breaks the power of stubborn strongholds. When combined with prayer, fasting creates a spiritual breakthrough that releases God's power in unprecedented ways. Jesus Himself said that some demons come out only by prayer and fasting. Fasting is not about earning God's favor or manipulating Him into answering your prayers. Rather, fasting is about denying your flesh to strengthen your spirit. It is about humbling yourself before God and demonstrating that you are serious about breakthrough. When you fast, you sharpen your spiritual discernment, increase your sensitivity to the Holy Spirit, and create an environment where God can work powerfully. Throughout scripture, we see that fasting preceded major breakthroughs - deliverance from enemies, healing from diseases, provision in times of famine, and victory in spiritual battles. If you are facing a stubborn stronghold that will not break despite your prayers, add fasting to your spiritual arsenal and watch God move.",

        "Finally, praise and worship are weapons of warfare. When Paul and Silas praised God in prison, their chains fell off and the prison doors opened. Praise confuses the enemy and releases the power of God's presence. When we worship, we create an atmosphere where God moves mightily. The enemy cannot stand in an atmosphere of genuine worship. Praise shifts the spiritual climate. It lifts your focus from your problems to God's power. It reminds you of who God is and what He has done. And it invites the presence of God into your situation. Second Chronicles 20 gives us a powerful example of this. When the armies of Moab and Ammon came against Judah, King Jehoshaphat sent the worshippers out ahead of the army. As they began to sing and praise, God set ambushes against their enemies and they destroyed themselves. You do not worship because you feel like it. You worship as an act of warfare. You praise God in the midst of the storm. You declare His goodness even when circumstances look bad. And as you do, you will see the enemy retreat and God's power manifest in your life.",
    ]

    for para in chapter3_content:
        story.append(Paragraph(para, body_style))

    story.append(PageBreak())

    # Chapter 4
    story.append(Paragraph("Chapter 4: Breaking Free from Bondage", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    chapter4_content = [
        "Freedom is your birthright as a child of God. Galatians 5:1 declares, 'Stand fast therefore in the liberty by which Christ has made us free, and do not be entangled again with a yoke of bondage.' Jesus came to set the captives free, and that includes you. This is not just a nice theological concept - this is your legal right as a believer. When Jesus died on the cross and rose from the dead, He broke every chain and cancelled every debt. The enemy no longer has any legal claim on your life. The only way he can keep you in bondage is through deception and your agreement with his lies. But when you understand who you are in Christ and what He has done for you, you can walk in total freedom. Jesus said in John 8:36, 'If the Son makes you free, you shall be free indeed.' Not partially free, not occasionally free, but totally and completely free. This is God's will for your life, and it is time to appropriate that freedom.",

        "Many believers struggle with various forms of bondage - addictions, fear, anger, unforgiveness, sexual immorality, and other destructive patterns. These are not just bad habits; they are often strongholds that the enemy has established in your life. But thank God, there is deliverance available through Jesus Christ. Bondage comes in many forms. Some people are bound by substance addictions - alcohol, drugs, prescription medications. Others are bound by behavioral addictions - pornography, gambling, shopping, social media. Still others are bound by emotional strongholds - depression, anxiety, fear, rejection, bitterness. And many carry generational bondages that have been passed down through family lines - poverty, sickness, divorce, premature death. Whatever form your bondage takes, it is robbing you of the abundant life that Jesus died to give you. But here is the good news - no bondage is too strong for the power of God. No addiction is too entrenched. No generational curse is too old. Jesus is the bondage breaker, and He specializes in setting captives free.",

        "The first step to freedom is acknowledgment. You cannot be free from what you deny exists. Be honest with God and yourself about the areas where you are bound. Confession brings these things into the light, and where there is light, darkness cannot remain. Many people remain in bondage because of shame and secrecy. They hide their struggles, pretend everything is fine, and suffer in silence. But James 5:16 says, 'Confess your trespasses to one another, and pray for one another, that you may be healed.' There is power in confession. When you bring your bondage into the light, you break the power of shame. Satan loves secrecy because it keeps you isolated and powerless. But when you confess your bondage to God and to trusted spiritual leaders, you activate the power of God's grace. First John 1:9 promises that if we confess our sins, He is faithful and just to forgive us and cleanse us from all unrighteousness. Acknowledgment is the beginning of breakthrough.",

        "Repentance is the next crucial step. True repentance is not just feeling sorry for sin, but turning away from it completely. It involves a change of mind, heart, and behavior. When you genuinely repent, you close the door to the enemy's access in your life. The Greek word for repentance is 'metanoia,' which means to change your mind or to think differently. Repentance is not about religious emotion or working up tears. It is about a fundamental shift in your thinking that leads to a change in your behavior. You stop making excuses for your sin. You stop blaming others or your circumstances. You take full responsibility and make a decision to turn away from that sin and toward God. When you repent, you are essentially saying to the enemy, 'You no longer have permission to operate in this area of my life. I close this door in Jesus' name.' And you are saying to God, 'I submit this area to Your lordship. I choose Your way instead of my way.' This act of repentance is a powerful weapon that breaks the legal right of the enemy to afflict you.",

        "Renunciation means verbally breaking every agreement you've made with the enemy, whether knowingly or unknowingly. Speak out loud and renounce every demonic covenant, every curse, every ungodly soul tie. Use your authority in Christ to cancel the enemy's claims on your life. Sometimes we enter into agreements with the enemy without even realizing it. When you harbor unforgiveness, you give the enemy a foothold. When you participate in occult practices - even seemingly innocent things like horoscopes, tarot cards, or certain video games - you open demonic doors. When you engage in sexual immorality, you create soul ties that give demons access to your life. These agreements must be verbally renounced. The enemy operates on legal grounds, and when you speak out loud and break these agreements, you revoke his permission to operate in your life. This is not a formula or a magic incantation. It is you exercising your God-given authority as a believer and declaring that the enemy no longer has any claim on you because of the blood of Jesus Christ.",

        "Finally, receive your deliverance by faith. Believe that when you pray, God hears and answers. Stand firm on His promises and do not doubt. The same power that raised Jesus from the dead is available to deliver you from every bondage. Walk in your freedom and do not return to captivity. Deliverance is received by faith, not by feelings. You may not feel different immediately. The temptation may not disappear instantly. But when you have confessed, repented, and renounced, you must believe that God has heard your prayer and that you are free. Stand on the Word of God. When the enemy tries to bring that temptation back, resist him with scripture. When condemnation tries to creep back in, remind yourself that there is no condemnation for those who are in Christ Jesus. Walk in your freedom like it is already yours - because it is. God has done His part. Jesus has paid the price. The Holy Spirit is empowering you. Now you must do your part - believe, stand firm, and refuse to go back to the bondage that Christ has delivered you from. You are free. Walk like it. Talk like it. Live like it. Your bondage is broken in Jesus' name.",
    ]

    for para in chapter4_content:
        story.append(Paragraph(para, body_style))

    story.append(PageBreak())

    # Conclusion
    story.append(Paragraph("Conclusion: Walking in Victory", chapter_title_style))
    story.append(Spacer(1, 0.3*inch))

    conclusion_content = [
        "As we conclude this powerful study on binding the strong man, remember that you are more than a conqueror through Christ who loves you. The victory has already been won at Calvary. Your responsibility is to enforce that victory in your life through prayer, faith, and obedience to God's Word. Romans 8:37 tells us that in all these things we are more than conquerors through Him who loved us. Notice that it does not say we will be conquerors someday - it says we ARE conquerors right now. This is your present reality. You are not trying to become victorious. You already are victorious in Christ. The battle was won two thousand years ago when Jesus rose from the dead with all power in His hands. Now you must simply enforce that victory in every area of your life. When the enemy attacks, remind him of his defeat. When strongholds try to resist, tear them down with the weapons God has given you. Your victory is not in question - it is already secured in Christ.",

        "Do not be intimidated by the enemy. Greater is He that is in you than he that is in the world. You have been given authority to trample on serpents and scorpions and over all the power of the enemy. Nothing shall by any means hurt you. First John 4:4 declares this powerful truth - the One who lives in you is greater than any force in this world. The Holy Spirit dwelling in you is more powerful than any demon, any principality, any stronghold, or any curse. The enemy may roar like a lion, but he is a defeated foe. He has no real power over you unless you give it to him through fear, doubt, or disobedience. Stand tall in your authority. You represent the Kingdom of God on earth. You carry the name of Jesus. You are filled with the Holy Spirit. You are a son or daughter of the Most High God. The enemy should be afraid of you, not the other way around. When you understand your true identity and authority in Christ, you will walk with boldness and the enemy will flee from you.",

        "Stay vigilant. The enemy is always looking for an opportunity to attack. Maintain your spiritual disciplines - daily prayer, regular fasting, consistent Bible study, and active fellowship with other believers. These practices keep you strong and alert in the spirit. First Peter 5:8 warns us to be sober and vigilant because our adversary the devil walks about like a roaring lion, seeking whom he may devour. The key word here is 'may.' The devil does not have unlimited power. He can only devour those who give him an opportunity. Vigilance means staying spiritually alert. It means maintaining your relationship with God. It means not getting comfortable or complacent. The moment you drop your guard is the moment the enemy will strike. But when you stay close to God, when you keep your armor on, when you maintain your spiritual disciplines, you create a hedge of protection around your life that the enemy cannot penetrate. Make prayer a lifestyle, not just a religious duty. Study the Word daily. Fast regularly. Surround yourself with other believers who will strengthen your faith and hold you accountable. These practices are not legalistic requirements - they are weapons that keep you strong in the battle.",

        "Most importantly, remember that this battle belongs to the Lord. You are not fighting for victory; you are fighting from victory. Stand on the finished work of Jesus Christ, and watch as God brings down every stronghold in your life. Second Chronicles 20:15 says, 'Do not be afraid nor dismayed because of this great multitude, for the battle is not yours, but God's.' This changes everything. You do not have to figure out how to defeat the enemy in your own strength. You do not have to manufacture breakthrough through human effort. God is fighting for you. Your job is to stand firm, trust Him, and obey His instructions. When you fight from a place of victory rather than fighting for victory, you operate in rest instead of striving. You know that the outcome is already determined. You know that no weapon formed against you can prosper. You know that all things are working together for your good. This is the secret to sustained victory - recognizing that Jesus has already won the war, and you are simply enforcing His victory in your daily life through faith, obedience, and the power of the Holy Spirit.",

        "Go forth in the power of the Holy Spirit. Bind the strong man in your life, plunder his goods, and walk in the fullness of everything God has prepared for you. Your breakthrough is here. Your deliverance is now. Your victory is assured. This is not wishful thinking or positive confession - this is the truth of God's Word. Everything Jesus died to give you is available right now. Healing is yours. Freedom is yours. Prosperity is yours. Peace is yours. Joy is yours. Purpose is yours. The strong man has been identified. His tactics have been exposed. You have been equipped with mighty weapons. You have been given authority over all the power of the enemy. Now it is time to take action. Rise up in faith. Speak to that mountain. Command that stronghold to come down. Break those chains in Jesus' name. Declare your freedom. Walk in your authority. And watch as the strong man falls and everything he has stolen from you is restored. In Jesus' mighty name, your breakthrough is here, your victory is now, and your destiny is secured. Amen and amen!",
    ]

    for para in conclusion_content:
        story.append(Paragraph(para, body_style))

    # Build PDF
    print("Building demo PDF...")
    doc.build(story)
    print(f"✅ Demo PDF created: {output_path}")

    # Get file size
    file_size = os.path.getsize(output_path)
    file_size_kb = file_size / 1024

    print(f"   Total pages: 10")
    print(f"   File size: {file_size_kb:.2f} KB")
    print(f"   Chapters: 4 + Introduction & Conclusion")


def main():
    """Generate demo book."""

    # Create output directory
    output_dir = Path(__file__).parent.parent / "test_books"
    output_dir.mkdir(exist_ok=True)

    print("🎯 InkWave Demo Book Generator")
    print("=" * 60)
    print("\n📚 Creating: Binding The Strong Man (Demo - 10 pages)")

    create_demo_book(
        output_path=str(output_dir / "binding_the_strong_man_demo.pdf")
    )

    print("\n" + "=" * 60)
    print("✅ Demo book generated successfully!")
    print(f"📁 Location: {output_dir}")
    print("\nNext steps:")
    print("1. Navigate to InkWave admin panel: /admin/books/upload")
    print("2. Upload binding_the_strong_man_demo.pdf")
    print("3. Add book metadata and cover image")
    print("4. Test audio generation and playback")
    print("\nNote: This is original demo content, NOT the actual copyrighted book.")


if __name__ == "__main__":
    main()
