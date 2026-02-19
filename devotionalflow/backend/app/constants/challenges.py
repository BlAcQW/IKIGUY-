"""
Daily challenge definitions for Fresh Manna gamification.
Challenges refresh daily and offer bonus rewards.
"""

from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel


# ===== CHALLENGE TEMPLATE MODELS =====

class ChallengeTemplate(BaseModel):
    """Template for generating daily/weekly challenges."""
    id: str
    name: str
    description: str
    type: str  # 'daily' or 'weekly'
    requirement_type: str  # 'read_count', 'comment_count', etc.
    requirement_target: int
    points_reward: int
    coins_reward: int
    active_days: List[int]  # Days of week (0=Mon, 6=Sun) when this challenge is active


# ===== DAILY CHALLENGE TEMPLATES =====

DAILY_CHALLENGE_TEMPLATES: List[ChallengeTemplate] = [
    # Reading Challenges
    ChallengeTemplate(
        id="daily_read_one",
        name="Daily Devotion",
        description="Read one devotional today",
        type="daily",
        requirement_type="read_count",
        requirement_target=1,
        points_reward=20,
        coins_reward=5,
        active_days=[0, 1, 2, 3, 4, 5, 6],  # All days
    ),

    ChallengeTemplate(
        id="daily_read_three",
        name="Triple Blessing",
        description="Read three devotionals today",
        type="daily",
        requirement_type="read_count",
        requirement_target=3,
        points_reward=50,
        coins_reward=15,
        active_days=[0, 6],  # Sunday and Monday
    ),

    ChallengeTemplate(
        id="daily_early_bird",
        name="Morning Glory",
        description="Read a devotional before 8 AM",
        type="daily",
        requirement_type="early_morning_read",
        requirement_target=1,
        points_reward=30,
        coins_reward=10,
        active_days=[1, 3, 5],  # Mon, Wed, Fri
    ),

    ChallengeTemplate(
        id="daily_comment",
        name="Share Your Thoughts",
        description="Leave 3 meaningful comments today",
        type="daily",
        requirement_type="comment_count",
        requirement_target=3,
        points_reward=25,
        coins_reward=8,
        active_days=[2, 4],  # Tue, Thu
    ),

    ChallengeTemplate(
        id="daily_share",
        name="Spread the Word",
        description="Share 2 devotionals today",
        type="daily",
        requirement_type="share_count",
        requirement_target=2,
        points_reward=30,
        coins_reward=10,
        active_days=[0, 3, 6],  # Sun, Wed, Sat
    ),

    ChallengeTemplate(
        id="daily_engagement",
        name="Active Community Member",
        description="Like 10 devotionals or comments today",
        type="daily",
        requirement_type="likes_given",
        requirement_target=10,
        points_reward=20,
        coins_reward=5,
        active_days=[1, 4],  # Mon, Thu
    ),

    ChallengeTemplate(
        id="daily_reflection",
        name="Deep Dive",
        description="Spend at least 15 minutes reading today",
        type="daily",
        requirement_type="reading_time_minutes",
        requirement_target=15,
        points_reward=35,
        coins_reward=12,
        active_days=[2, 5],  # Tue, Fri
    ),
]


# ===== WEEKLY CHALLENGE TEMPLATES =====

WEEKLY_CHALLENGE_TEMPLATES: List[ChallengeTemplate] = [
    ChallengeTemplate(
        id="weekly_consistent",
        name="Consistency is Key",
        description="Read devotionals on 5 different days this week",
        type="weekly",
        requirement_type="days_active",
        requirement_target=5,
        points_reward=100,
        coins_reward=30,
        active_days=[0, 1, 2, 3, 4, 5, 6],
    ),

    ChallengeTemplate(
        id="weekly_explorer",
        name="Category Explorer",
        description="Read devotionals from 3 different categories this week",
        type="weekly",
        requirement_type="categories_explored",
        requirement_target=3,
        points_reward=80,
        coins_reward=25,
        active_days=[0, 1, 2, 3, 4, 5, 6],
    ),

    ChallengeTemplate(
        id="weekly_community",
        name="Community Builder",
        description="Leave 15 comments this week",
        type="weekly",
        requirement_type="comment_count",
        requirement_target=15,
        points_reward=120,
        coins_reward=35,
        active_days=[0, 1, 2, 3, 4, 5, 6],
    ),
]


# ===== CHALLENGE UTILITIES =====

def get_daily_templates_for_day(day_of_week: int) -> List[ChallengeTemplate]:
    """
    Get all daily challenge templates active for a specific day of the week.

    Args:
        day_of_week: 0 (Monday) to 6 (Sunday)

    Returns:
        List of active challenge templates for that day
    """
    return [
        template for template in DAILY_CHALLENGE_TEMPLATES
        if day_of_week in template.active_days
    ]


def get_active_templates(include_weekly: bool = True) -> List[ChallengeTemplate]:
    """
    Get all challenge templates active today.

    Args:
        include_weekly: Whether to include weekly challenges

    Returns:
        List of active challenge templates
    """
    today = datetime.utcnow().weekday()  # 0 = Monday, 6 = Sunday

    templates = get_daily_templates_for_day(today)

    if include_weekly:
        templates.extend(WEEKLY_CHALLENGE_TEMPLATES)

    return templates


def get_template_by_id(template_id: str) -> ChallengeTemplate:
    """Get challenge template by ID."""
    all_templates = DAILY_CHALLENGE_TEMPLATES + WEEKLY_CHALLENGE_TEMPLATES

    for template in all_templates:
        if template.id == template_id:
            return template

    return None


# Create lookup dictionaries
ALL_TEMPLATES = DAILY_CHALLENGE_TEMPLATES + WEEKLY_CHALLENGE_TEMPLATES
TEMPLATES_DICT = {template.id: template for template in ALL_TEMPLATES}
