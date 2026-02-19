"""
Achievement definitions for Fresh Manna gamification.
Initial set of 20 achievements for Phase 1 launch.
"""

from app.models.gamification import Achievement, AchievementRequirement

# ===== READING ACHIEVEMENTS =====

ACHIEVEMENTS = [
    # First Steps
    Achievement(
        id="first_steps",
        name="First Steps",
        description="Read your first devotional",
        category="reading",
        rarity="common",
        icon_name="📖",
        points_reward=10,
        coins_reward=5,
        requirement=AchievementRequirement(
            type="read_count",
            target=1
        )
    ),

    # Reading Milestones
    Achievement(
        id="dedicated_reader",
        name="Dedicated Reader",
        description="Read 10 devotionals",
        category="reading",
        rarity="common",
        icon_name="📚",
        points_reward=25,
        coins_reward=10,
        requirement=AchievementRequirement(
            type="read_count",
            target=10
        )
    ),

    Achievement(
        id="bookworm",
        name="Bookworm",
        description="Read 50 devotionals",
        category="reading",
        rarity="rare",
        icon_name="🎓",
        points_reward=100,
        coins_reward=25,
        requirement=AchievementRequirement(
            type="read_count",
            target=50
        )
    ),

    Achievement(
        id="scholar",
        name="Scholar",
        description="Read 100 devotionals",
        category="reading",
        rarity="epic",
        icon_name="🏛️",
        points_reward=250,
        coins_reward=50,
        requirement=AchievementRequirement(
            type="read_count",
            target=100
        )
    ),

    # Streak Achievements
    Achievement(
        id="ignited",
        name="Ignited",
        description="Maintain a 3-day reading streak",
        category="reading",
        rarity="common",
        icon_name="🔥",
        points_reward=15,
        coins_reward=5,
        requirement=AchievementRequirement(
            type="streak_days",
            target=3
        )
    ),

    Achievement(
        id="steadfast",
        name="Steadfast",
        description="Maintain a 7-day reading streak",
        category="reading",
        rarity="rare",
        icon_name="⭐",
        points_reward=50,
        coins_reward=15,
        requirement=AchievementRequirement(
            type="streak_days",
            target=7
        )
    ),

    Achievement(
        id="devoted",
        name="Devoted",
        description="Maintain a 30-day reading streak",
        category="reading",
        rarity="epic",
        icon_name="💎",
        points_reward=200,
        coins_reward=50,
        requirement=AchievementRequirement(
            type="streak_days",
            target=30
        )
    ),

    Achievement(
        id="faithful_warrior",
        name="Faithful Warrior",
        description="Maintain a 90-day reading streak",
        category="reading",
        rarity="legendary",
        icon_name="👑",
        points_reward=500,
        coins_reward=100,
        requirement=AchievementRequirement(
            type="streak_days",
            target=90
        )
    ),

    # Time-based
    Achievement(
        id="early_bird",
        name="Early Bird",
        description="Read before 6 AM (5 times)",
        category="reading",
        rarity="rare",
        icon_name="🌅",
        points_reward=50,
        coins_reward=15,
        requirement=AchievementRequirement(
            type="early_morning_reads",
            target=5
        )
    ),

    Achievement(
        id="night_owl",
        name="Night Owl",
        description="Read after 10 PM (5 times)",
        category="reading",
        rarity="rare",
        icon_name="🌙",
        points_reward=50,
        coins_reward=15,
        requirement=AchievementRequirement(
            type="late_night_reads",
            target=5
        )
    ),

    # ===== ENGAGEMENT ACHIEVEMENTS =====

    Achievement(
        id="conversationalist",
        name="Conversationalist",
        description="Leave 10 comments",
        category="engagement",
        rarity="common",
        icon_name="💬",
        points_reward=30,
        coins_reward=10,
        requirement=AchievementRequirement(
            type="comment_count",
            target=10
        )
    ),

    Achievement(
        id="thoughtful_commenter",
        name="Thoughtful Commenter",
        description="Leave 50 comments",
        category="engagement",
        rarity="rare",
        icon_name="🗣️",
        points_reward=100,
        coins_reward=25,
        requirement=AchievementRequirement(
            type="comment_count",
            target=50
        )
    ),

    Achievement(
        id="encourager",
        name="Encourager",
        description="Like 100 devotionals",
        category="engagement",
        rarity="common",
        icon_name="❤️",
        points_reward=50,
        coins_reward=15,
        requirement=AchievementRequirement(
            type="likes_given",
            target=100
        )
    ),

    Achievement(
        id="collector",
        name="Collector",
        description="Bookmark 25 devotionals",
        category="engagement",
        rarity="common",
        icon_name="🔖",
        points_reward=40,
        coins_reward=10,
        requirement=AchievementRequirement(
            type="bookmark_count",
            target=25
        )
    ),

    # ===== SOCIAL ACHIEVEMENTS =====

    Achievement(
        id="evangelist",
        name="Evangelist",
        description="Share 20 devotionals",
        category="social",
        rarity="rare",
        icon_name="🔗",
        points_reward=100,
        coins_reward=25,
        requirement=AchievementRequirement(
            type="share_count",
            target=20
        )
    ),

    Achievement(
        id="fellowship_starter",
        name="Fellowship Starter",
        description="Invite 3 friends",
        category="social",
        rarity="rare",
        icon_name="👥",
        points_reward=150,
        coins_reward=30,
        requirement=AchievementRequirement(
            type="friends_invited",
            target=3
        )
    ),

    # ===== SPIRITUAL GROWTH ACHIEVEMENTS =====

    Achievement(
        id="prayer_warrior",
        name="Prayer Warrior",
        description="Complete 30 prayer prompts",
        category="spiritual",
        rarity="epic",
        icon_name="🙏",
        points_reward=200,
        coins_reward=50,
        requirement=AchievementRequirement(
            type="prayers_completed",
            target=30
        )
    ),

    Achievement(
        id="reflector",
        name="Reflector",
        description="Complete 50 reflection questions",
        category="spiritual",
        rarity="epic",
        icon_name="📝",
        points_reward=250,
        coins_reward=50,
        requirement=AchievementRequirement(
            type="reflections_completed",
            target=50
        )
    ),

    # ===== SPECIAL ACHIEVEMENTS =====

    Achievement(
        id="profile_complete",
        name="Profile Complete",
        description="Complete your profile information",
        category="special",
        rarity="common",
        icon_name="✨",
        points_reward=20,
        coins_reward=10,
        requirement=AchievementRequirement(
            type="profile_completed",
            target=1
        )
    ),

    Achievement(
        id="first_day",
        name="Welcome to Fresh Manna",
        description="Join the Fresh Manna community",
        category="special",
        rarity="common",
        icon_name="🎉",
        points_reward=10,
        coins_reward=5,
        requirement=AchievementRequirement(
            type="account_created",
            target=1
        )
    ),
]

# Create achievement lookup dictionary
ACHIEVEMENTS_DICT = {achievement.id: achievement for achievement in ACHIEVEMENTS}


def get_achievement(achievement_id: str) -> Achievement:
    """Get achievement by ID."""
    return ACHIEVEMENTS_DICT.get(achievement_id)


def get_all_achievements() -> list[Achievement]:
    """Get all achievements."""
    return ACHIEVEMENTS


def get_achievements_by_category(category: str) -> list[Achievement]:
    """Get achievements by category."""
    return [a for a in ACHIEVEMENTS if a.category == category]


def get_achievements_by_rarity(rarity: str) -> list[Achievement]:
    """Get achievements by rarity."""
    return [a for a in ACHIEVEMENTS if a.rarity == rarity]
