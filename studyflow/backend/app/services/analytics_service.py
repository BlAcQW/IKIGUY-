"""
Admin analytics service for StudyFlow.

Provides comprehensive analytics for system monitoring, user metrics,
and business intelligence.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import mongodb, COLLECTION_USERS, COLLECTION_SESSIONS, \
    COLLECTION_QUESTIONS, COLLECTION_MATERIALS, COLLECTION_PROGRESS
from app.models.user import UserRole
from bson import ObjectId

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for admin analytics and system monitoring.

    Provides comprehensive metrics for dashboard, user analytics,
    content performance, and system health monitoring.
    """

    @staticmethod
    async def get_dashboard_stats(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics.

        Args:
            start_date: Start date for time-based metrics (optional)
            end_date: End date for time-based metrics (optional)

        Returns:
            Dictionary with dashboard statistics
        """
        # Default to last 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Build date query
        date_query = {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        # Get user counts
        users_collection = mongodb.get_collection(COLLECTION_USERS)
        total_users = await users_collection.count_documents({})
        new_users = await users_collection.count_documents(date_query)

        # Count by role
        users_by_role = {}
        for role in UserRole:
            count = await users_collection.count_documents({"role": role.value})
            users_by_role[role.value] = count

        # Get session stats
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)
        total_sessions = await sessions_collection.count_documents({})
        sessions_in_period = await sessions_collection.count_documents(date_query)

        # Average session duration
        pipeline = [
            {"$match": {"duration_minutes": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "avg_duration": {"$avg": "$duration_minutes"},
                    "total_duration": {"$sum": "$duration_minutes"}
                }
            }
        ]
        session_stats = await sessions_collection.aggregate(pipeline).to_list(length=1)
        avg_session_duration = session_stats[0]["avg_duration"] if session_stats else 0
        total_learning_time = session_stats[0]["total_duration"] if session_stats else 0

        # Get question stats
        questions_collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        total_questions = await questions_collection.count_documents({})
        questions_in_period = await questions_collection.count_documents(date_query)

        # Average confidence score
        pipeline = [
            {"$match": {"confidence_score": {"$exists": True}}},
            {
                "$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$confidence_score"}
                }
            }
        ]
        confidence_stats = await questions_collection.aggregate(pipeline).to_list(length=1)
        avg_confidence = confidence_stats[0]["avg_confidence"] if confidence_stats else 0

        # Get materials stats
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)
        total_materials = await materials_collection.count_documents({})
        new_materials = await materials_collection.count_documents(date_query)

        # Materials by subject
        pipeline = [
            {
                "$group": {
                    "_id": "$subject",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]
        materials_by_subject = await materials_collection.aggregate(pipeline).to_list(length=100)

        return {
            "users": {
                "total": total_users,
                "new_in_period": new_users,
                "by_role": users_by_role
            },
            "sessions": {
                "total": total_sessions,
                "in_period": sessions_in_period,
                "avg_duration_minutes": round(avg_session_duration, 2),
                "total_learning_time_hours": round(total_learning_time / 60, 2)
            },
            "questions": {
                "total": total_questions,
                "in_period": questions_in_period,
                "avg_confidence_score": round(avg_confidence, 3)
            },
            "materials": {
                "total": total_materials,
                "new_in_period": new_materials,
                "by_subject": [
                    {"subject": item["_id"], "count": item["count"]}
                    for item in materials_by_subject
                ]
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            }
        }

    @staticmethod
    async def get_user_metrics(
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user engagement and retention metrics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with user metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        users_collection = mongodb.get_collection(COLLECTION_USERS)
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)

        # New users over time (daily)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        new_users_daily = await users_collection.aggregate(pipeline).to_list(length=365)

        # Active users (users who created sessions in period)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "session_count": {"$sum": 1},
                    "total_questions": {"$sum": "$questions_asked"},
                    "last_session": {"$max": "$created_at"}
                }
            }
        ]
        active_users_data = await sessions_collection.aggregate(pipeline).to_list(length=10000)

        active_users_count = len(active_users_data)

        # Engagement levels
        engagement_levels = {
            "highly_engaged": 0,  # 10+ sessions
            "moderately_engaged": 0,  # 5-9 sessions
            "lightly_engaged": 0,  # 1-4 sessions
        }

        for user_data in active_users_data:
            session_count = user_data["session_count"]
            if session_count >= 10:
                engagement_levels["highly_engaged"] += 1
            elif session_count >= 5:
                engagement_levels["moderately_engaged"] += 1
            else:
                engagement_levels["lightly_engaged"] += 1

        # Calculate total users for activity rate
        total_users = await users_collection.count_documents({"role": UserRole.STUDENT.value})
        activity_rate = (active_users_count / total_users * 100) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "active_users": active_users_count,
            "activity_rate_percent": round(activity_rate, 2),
            "engagement_levels": engagement_levels,
            "new_users_daily": [
                {"date": item["_id"], "count": item["count"]}
                for item in new_users_daily
            ],
            "period_days": days
        }

    @staticmethod
    async def get_content_analytics(
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get content usage and performance analytics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with content analytics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        questions_collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)

        # Popular subjects (by question count)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$subject",
                    "question_count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "avg_response_time_ms": {"$avg": "$response_time_ms"}
                }
            },
            {"$sort": {"question_count": -1}}
        ]
        subject_stats = await questions_collection.aggregate(pipeline).to_list(length=100)

        # Popular topics within subjects
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "topic": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "subject": "$subject",
                        "topic": "$topic"
                    },
                    "question_count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"}
                }
            },
            {"$sort": {"question_count": -1}},
            {"$limit": 50}
        ]
        topic_stats = await questions_collection.aggregate(pipeline).to_list(length=50)

        # Low confidence questions (need content improvement)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "confidence_score": {"$lt": 0.7}
                }
            },
            {
                "$group": {
                    "_id": "$subject",
                    "low_confidence_count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"}
                }
            },
            {"$sort": {"low_confidence_count": -1}}
        ]
        low_confidence_areas = await questions_collection.aggregate(pipeline).to_list(length=100)

        # Material upload trends
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        material_uploads = await materials_collection.aggregate(pipeline).to_list(length=365)

        return {
            "popular_subjects": [
                {
                    "subject": item["_id"],
                    "question_count": item["question_count"],
                    "avg_confidence": round(item.get("avg_confidence", 0), 3),
                    "avg_response_time_ms": round(item.get("avg_response_time_ms", 0), 2)
                }
                for item in subject_stats
            ],
            "popular_topics": [
                {
                    "subject": item["_id"]["subject"],
                    "topic": item["_id"]["topic"],
                    "question_count": item["question_count"],
                    "avg_confidence": round(item.get("avg_confidence", 0), 3)
                }
                for item in topic_stats
            ],
            "low_confidence_areas": [
                {
                    "subject": item["_id"],
                    "low_confidence_count": item["low_confidence_count"],
                    "avg_confidence": round(item.get("avg_confidence", 0), 3)
                }
                for item in low_confidence_areas
            ],
            "material_uploads_daily": [
                {"date": item["_id"], "count": item["count"]}
                for item in material_uploads
            ],
            "period_days": days
        }

    @staticmethod
    async def get_system_health() -> Dict[str, Any]:
        """
        Get system health and performance metrics.

        Returns:
            Dictionary with system health metrics
        """
        # Database collection stats
        users_collection = mongodb.get_collection(COLLECTION_USERS)
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)
        questions_collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        materials_collection = mongodb.get_collection(COLLECTION_MATERIALS)

        # Get collection counts
        db_stats = {
            "users_count": await users_collection.count_documents({}),
            "sessions_count": await sessions_collection.count_documents({}),
            "questions_count": await questions_collection.count_documents({}),
            "materials_count": await materials_collection.count_documents({})
        }

        # Recent activity (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_activity = {
            "sessions_24h": await sessions_collection.count_documents(
                {"created_at": {"$gte": last_24h}}
            ),
            "questions_24h": await questions_collection.count_documents(
                {"created_at": {"$gte": last_24h}}
            ),
            "materials_24h": await materials_collection.count_documents(
                {"created_at": {"$gte": last_24h}}
            )
        }

        # API performance metrics (based on question response times)
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": last_24h},
                    "response_time_ms": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_response_time": {"$avg": "$response_time_ms"},
                    "min_response_time": {"$min": "$response_time_ms"},
                    "max_response_time": {"$max": "$response_time_ms"}
                }
            }
        ]
        performance_stats = await questions_collection.aggregate(pipeline).to_list(length=1)

        api_performance = {
            "avg_response_time_ms": round(performance_stats[0]["avg_response_time"], 2) if performance_stats else 0,
            "min_response_time_ms": performance_stats[0]["min_response_time"] if performance_stats else 0,
            "max_response_time_ms": performance_stats[0]["max_response_time"] if performance_stats else 0
        }

        # Error rate (low confidence as proxy for errors)
        total_questions_24h = recent_activity["questions_24h"]
        low_confidence_24h = await questions_collection.count_documents({
            "created_at": {"$gte": last_24h},
            "confidence_score": {"$lt": 0.5}
        })
        error_rate = (low_confidence_24h / total_questions_24h * 100) if total_questions_24h > 0 else 0

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_stats,
            "recent_activity_24h": recent_activity,
            "api_performance": api_performance,
            "error_indicators": {
                "low_confidence_questions_24h": low_confidence_24h,
                "error_rate_percent": round(error_rate, 2)
            }
        }

    @staticmethod
    async def get_financial_analytics(
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get financial analytics (usage costs, wallet balances).

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with financial analytics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        # Get wallet data
        wallets_collection = mongodb.get_collection("wallets")
        transactions_collection = mongodb.get_collection("transactions")

        # Total wallet balance across all users
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_balance": {"$sum": "$balance"},
                    "avg_balance": {"$avg": "$balance"},
                    "wallet_count": {"$sum": 1}
                }
            }
        ]
        wallet_stats = await wallets_collection.aggregate(pipeline).to_list(length=1)

        # Transaction stats
        date_query = {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }

        total_transactions = await transactions_collection.count_documents(date_query)

        # Transactions by type
        pipeline = [
            {"$match": date_query},
            {
                "$group": {
                    "_id": "$transaction_type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"}
                }
            }
        ]
        transactions_by_type = await transactions_collection.aggregate(pipeline).to_list(length=100)

        # Daily transaction volume
        pipeline = [
            {"$match": date_query},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_transactions = await transactions_collection.aggregate(pipeline).to_list(length=365)

        return {
            "wallet_stats": {
                "total_balance": float(wallet_stats[0]["total_balance"]) if wallet_stats else 0,
                "avg_balance": float(wallet_stats[0]["avg_balance"]) if wallet_stats else 0,
                "wallet_count": wallet_stats[0]["wallet_count"] if wallet_stats else 0
            },
            "transactions": {
                "total_count": total_transactions,
                "by_type": [
                    {
                        "type": item["_id"],
                        "count": item["count"],
                        "total_amount": float(item["total_amount"])
                    }
                    for item in transactions_by_type
                ],
                "daily": [
                    {
                        "date": item["_id"],
                        "count": item["count"],
                        "total_amount": float(item["total_amount"])
                    }
                    for item in daily_transactions
                ]
            },
            "period_days": days
        }

    @staticmethod
    async def get_top_users(
        metric: str = "questions",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top users by various metrics.

        Args:
            metric: Metric to rank by (questions, sessions, learning_time)
            limit: Number of top users to return

        Returns:
            List of top users with their metrics
        """
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)
        questions_collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        users_collection = mongodb.get_collection(COLLECTION_USERS)

        if metric == "questions":
            # Top users by question count
            pipeline = [
                {
                    "$group": {
                        "_id": "$student_id",
                        "question_count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence_score"}
                    }
                },
                {"$sort": {"question_count": -1}},
                {"$limit": limit}
            ]
            top_users_data = await questions_collection.aggregate(pipeline).to_list(length=limit)

        elif metric == "sessions":
            # Top users by session count
            pipeline = [
                {
                    "$group": {
                        "_id": "$student_id",
                        "session_count": {"$sum": 1},
                        "total_questions": {"$sum": "$questions_asked"}
                    }
                },
                {"$sort": {"session_count": -1}},
                {"$limit": limit}
            ]
            top_users_data = await sessions_collection.aggregate(pipeline).to_list(length=limit)

        elif metric == "learning_time":
            # Top users by learning time
            pipeline = [
                {
                    "$match": {"duration_minutes": {"$exists": True}}
                },
                {
                    "$group": {
                        "_id": "$student_id",
                        "total_learning_time": {"$sum": "$duration_minutes"},
                        "session_count": {"$sum": 1}
                    }
                },
                {"$sort": {"total_learning_time": -1}},
                {"$limit": limit}
            ]
            top_users_data = await sessions_collection.aggregate(pipeline).to_list(length=limit)

        else:
            return []

        # Enrich with user details
        result = []
        for user_data in top_users_data:
            user_id = user_data["_id"]
            user = await users_collection.find_one({"supabase_user_id": user_id})

            result.append({
                "user_id": user_id,
                "name": user.get("full_name", "Unknown") if user else "Unknown",
                "email": user.get("email", "Unknown") if user else "Unknown",
                **{k: v for k, v in user_data.items() if k != "_id"}
            })

        return result
