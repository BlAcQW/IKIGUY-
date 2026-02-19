"""
Gamification points calculation service.

Defines point rules for all actions and calculates level progression.
Ensures fair and balanced point distribution to prevent pay-to-win dynamics.
"""

from typing import Dict, Any, Tuple
from datetime import datetime
import math


# ============================================================================
# POINT RULES CONFIGURATION
# ============================================================================

POINT_RULES = {
    # ========================================
    # ATTENDANCE POINTS
    # ========================================
    "attend_service": 10,  # Regular Sunday service
    "attend_midweek": 15,  # Midweek service (bonus for extra commitment)
    "attend_conference": 25,  # Special conference/event
    "perfect_month": 50,  # Attended every service in a calendar month
    "birthday_attendance": 20,  # Attended on birthday (special recognition)
    "anniversary_attendance": 25,  # Attended on church anniversary

    # ========================================
    # VOLUNTEERING POINTS
    # ========================================
    "volunteer_hour": 20,  # Per hour of volunteer work
    "volunteer_event": 30,  # One-time event volunteering

    # ========================================
    # ENGAGEMENT POINTS
    # ========================================
    "bring_visitor": 50,  # First-time visitor invited
    "visitor_returns": 25,  # Invited visitor comes back
    "join_cell_group": 50,  # Joined a cell group
    "complete_spiritual_stage": 100,  # Completed discipleship stage

    # ========================================
    # GIVING POINTS (CAPPED)
    # ========================================
    # IMPORTANT: Donation points are capped at 50 to prevent pay-to-win
    # Formula: min(amount * 0.1, 50)
    # Examples:
    #   $10 donation = 1 point
    #   $100 donation = 10 points
    #   $500 donation = 50 points (capped)
    #   $1000 donation = 50 points (capped)
    "donation_base_multiplier": 0.1,  # 1 point per $10
    "donation_max_points": 50,  # Hard cap to prevent pay-to-win

    # ========================================
    # STREAK MILESTONE POINTS
    # ========================================
    "streak_milestone_4w": 40,  # 4-week streak (1 month)
    "streak_milestone_8w": 80,  # 8-week streak (2 months)
    "streak_milestone_13w": 130,  # 13-week streak (quarter)
    "streak_milestone_26w": 260,  # 26-week streak (half year)
    "streak_milestone_52w": 520,  # 52-week streak (full year!)
}


# ============================================================================
# LEVEL TIER CONFIGURATION
# ============================================================================

LEVEL_TIERS = {
    "bronze": {
        "min_level": 1,
        "max_level": 10,
        "points_per_level": 100,  # 100 points to level up
        "emoji": "🥉",
        "color": "#CD7F32"
    },
    "silver": {
        "min_level": 11,
        "max_level": 20,
        "points_per_level": 200,  # 200 points per level
        "emoji": "🥈",
        "color": "#C0C0C0"
    },
    "gold": {
        "min_level": 21,
        "max_level": 30,
        "points_per_level": 500,  # 500 points per level
        "emoji": "🥇",
        "color": "#FFD700"
    },
    "platinum": {
        "min_level": 31,
        "max_level": 50,
        "points_per_level": 1000,  # 1000 points per level
        "emoji": "💎",
        "color": "#E5E4E2"
    }
}


# ============================================================================
# POINTS CALCULATION SERVICE
# ============================================================================

class GamificationPointsService:
    """
    Service for calculating points and levels.

    Provides methods to:
    - Calculate points for various actions
    - Calculate level progression
    - Determine level tier
    - Check for level ups
    """

    @staticmethod
    def calculate_points_for_action(action: str, metadata: Dict[str, Any] = None) -> int:
        """
        Calculate points for a specific action.

        Args:
            action: Action type (attend_service, volunteer_hour, etc.)
            metadata: Additional context (e.g., donation amount, hours volunteered)

        Returns:
            Points awarded for the action

        Example:
            >>> calculate_points_for_action("attend_service")
            10
            >>> calculate_points_for_action("donation_made", {"amount": 100})
            10
            >>> calculate_points_for_action("donation_made", {"amount": 1000})
            50  # capped
        """
        if metadata is None:
            metadata = {}

        # Special handling for donations (with cap)
        if action == "donation_made":
            amount = metadata.get("amount", 0)
            multiplier = POINT_RULES["donation_base_multiplier"]
            max_points = POINT_RULES["donation_max_points"]
            points = min(amount * multiplier, max_points)
            return int(points)

        # Standard point lookup
        return POINT_RULES.get(action, 0)

    @staticmethod
    def calculate_volunteer_points(hours: float) -> int:
        """
        Calculate points for volunteer work.

        Args:
            hours: Number of hours volunteered

        Returns:
            Points awarded (hours * points_per_hour)

        Example:
            >>> calculate_volunteer_points(2.5)
            50  # 2.5 hours * 20 points/hour
        """
        points_per_hour = POINT_RULES["volunteer_hour"]
        return int(hours * points_per_hour)

    @staticmethod
    def get_level_tier(level: int) -> str:
        """
        Get the tier for a specific level.

        Args:
            level: Current level (1-50)

        Returns:
            Tier name (bronze, silver, gold, platinum)

        Example:
            >>> get_level_tier(5)
            'bronze'
            >>> get_level_tier(15)
            'silver'
            >>> get_level_tier(25)
            'gold'
            >>> get_level_tier(45)
            'platinum'
        """
        for tier_name, tier_config in LEVEL_TIERS.items():
            if tier_config["min_level"] <= level <= tier_config["max_level"]:
                return tier_name
        return "bronze"  # Fallback

    @staticmethod
    def calculate_level_from_points(total_points: int) -> Tuple[int, str, int]:
        """
        Calculate level, tier, and points to next level from total points.

        Args:
            total_points: Total lifetime points accumulated

        Returns:
            Tuple of (level, tier, points_to_next_level)

        Example:
            >>> calculate_level_from_points(0)
            (1, 'bronze', 100)
            >>> calculate_level_from_points(150)
            (2, 'bronze', 50)  # 150 - 100 = level 2, need 50 more for level 3
            >>> calculate_level_from_points(1000)
            (10, 'bronze', 100)
            >>> calculate_level_from_points(1100)
            (11, 'silver', 100)  # Entered silver tier
        """
        current_level = 1
        remaining_points = total_points

        # Iterate through tiers in order
        for tier_name in ["bronze", "silver", "gold", "platinum"]:
            tier = LEVEL_TIERS[tier_name]
            min_level = tier["min_level"]
            max_level = tier["max_level"]
            points_per_level = tier["points_per_level"]

            levels_in_tier = max_level - min_level + 1

            # Calculate how many levels can be completed in this tier
            levels_completable = remaining_points // points_per_level
            levels_to_add = min(levels_completable, levels_in_tier)

            if levels_to_add > 0:
                current_level += levels_to_add
                remaining_points -= levels_to_add * points_per_level

            # If we haven't completed all levels in this tier, we're done
            if levels_to_add < levels_in_tier:
                tier_name = GamificationPointsService.get_level_tier(current_level)
                points_to_next = LEVEL_TIERS[tier_name]["points_per_level"] - remaining_points
                return (current_level, tier_name, points_to_next)

        # Maxed out at level 50
        return (50, "platinum", 0)

    @staticmethod
    def check_level_up(
        old_points: int,
        new_points: int
    ) -> Tuple[bool, int, int]:
        """
        Check if adding points causes a level up.

        Args:
            old_points: Points before adding new points
            new_points: Points after adding new points

        Returns:
            Tuple of (level_up_occurred, old_level, new_level)

        Example:
            >>> check_level_up(90, 110)
            (True, 1, 2)  # Crossed 100-point threshold
            >>> check_level_up(50, 70)
            (False, 1, 1)  # Still in level 1
        """
        old_level, _, _ = GamificationPointsService.calculate_level_from_points(old_points)
        new_level, _, _ = GamificationPointsService.calculate_level_from_points(new_points)

        level_up = new_level > old_level
        return (level_up, old_level, new_level)

    @staticmethod
    def calculate_points_distribution_stats(
        points_list: list[int]
    ) -> Dict[str, Any]:
        """
        Calculate statistics about point distribution.

        Useful for admin analytics to understand point economy.

        Args:
            points_list: List of total points from all members

        Returns:
            Dictionary with statistics (mean, median, percentiles, etc.)
        """
        if not points_list:
            return {
                "count": 0,
                "mean": 0,
                "median": 0,
                "min": 0,
                "max": 0,
                "percentile_25": 0,
                "percentile_50": 0,
                "percentile_75": 0,
                "percentile_90": 0,
                "percentile_95": 0,
                "percentile_99": 0
            }

        sorted_points = sorted(points_list)
        count = len(sorted_points)

        def percentile(data, p):
            """Calculate percentile."""
            k = (count - 1) * (p / 100)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[int(k)]
            d0 = data[int(f)] * (c - k)
            d1 = data[int(c)] * (k - f)
            return d0 + d1

        return {
            "count": count,
            "mean": sum(sorted_points) / count,
            "median": percentile(sorted_points, 50),
            "min": sorted_points[0],
            "max": sorted_points[-1],
            "percentile_25": percentile(sorted_points, 25),
            "percentile_50": percentile(sorted_points, 50),
            "percentile_75": percentile(sorted_points, 75),
            "percentile_90": percentile(sorted_points, 90),
            "percentile_95": percentile(sorted_points, 95),
            "percentile_99": percentile(sorted_points, 99)
        }

    @staticmethod
    def get_tier_info(tier_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tier.

        Args:
            tier_name: Tier name (bronze, silver, gold, platinum)

        Returns:
            Tier configuration dictionary
        """
        return LEVEL_TIERS.get(tier_name, LEVEL_TIERS["bronze"])

    @staticmethod
    def get_all_point_rules() -> Dict[str, Any]:
        """
        Get all point rules for display/configuration.

        Returns:
            Copy of POINT_RULES dictionary
        """
        return POINT_RULES.copy()

    @staticmethod
    def validate_point_value(points: int, action: str) -> bool:
        """
        Validate that a point value matches the configured rule.

        Args:
            points: Points being awarded
            action: Action type

        Returns:
            True if valid, False otherwise

        Example:
            >>> validate_point_value(10, "attend_service")
            True
            >>> validate_point_value(100, "attend_service")
            False
        """
        expected_points = POINT_RULES.get(action)
        if expected_points is None:
            return False

        # For donation, allow any value up to max
        if action == "donation_made":
            return 0 <= points <= POINT_RULES["donation_max_points"]

        return points == expected_points


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_points(points: int) -> str:
    """
    Format points for display with thousands separator.

    Args:
        points: Points value

    Returns:
        Formatted string (e.g., "1,234")

    Example:
        >>> format_points(1234)
        '1,234'
        >>> format_points(50)
        '50'
    """
    return f"{points:,}"


def get_tier_emoji(tier: str) -> str:
    """
    Get emoji for a tier.

    Args:
        tier: Tier name

    Returns:
        Emoji string

    Example:
        >>> get_tier_emoji("bronze")
        '🥉'
        >>> get_tier_emoji("platinum")
        '💎'
    """
    return LEVEL_TIERS.get(tier, {}).get("emoji", "⭐")


def get_tier_color(tier: str) -> str:
    """
    Get hex color for a tier.

    Args:
        tier: Tier name

    Returns:
        Hex color string

    Example:
        >>> get_tier_color("gold")
        '#FFD700'
    """
    return LEVEL_TIERS.get(tier, {}).get("color", "#CD7F32")


# ============================================================================
# STANDALONE FUNCTION WRAPPERS
# ============================================================================
# These wrappers allow importing functions directly without the class

def calculate_level_from_points(total_points: int) -> int:
    """
    Calculate level from total points.

    Args:
        total_points: Total lifetime points

    Returns:
        Current level (1-50)
    """
    level, _, _ = GamificationPointsService.calculate_level_from_points(total_points)
    return level


def calculate_points_to_next_level(total_points: int) -> int:
    """
    Calculate points needed to reach next level.

    Args:
        total_points: Total lifetime points

    Returns:
        Points needed for next level
    """
    _, _, points_to_next = GamificationPointsService.calculate_level_from_points(total_points)
    return points_to_next


def get_level_tier(level: int) -> str:
    """
    Get tier for a specific level.

    Args:
        level: Current level

    Returns:
        Tier name (bronze, silver, gold, platinum)
    """
    return GamificationPointsService.get_level_tier(level)
