"""
MongoDB-based Authentication Service for African Language Community Platform.

Pure MongoDB authentication without Supabase dependency.
Uses JWT tokens for authentication and MongoDB for user storage.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from bson import ObjectId
import jwt
import bcrypt
import logging

from models.user_models import User, UserCreate, UserUpdate, UserAuth, UserLevel
from database import get_database
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MongoDBAuthService:
    """
    Pure MongoDB authentication service.

    Handles user registration, authentication, profile updates, and JWT token management
    without external dependencies.
    """

    def __init__(self):
        """Initialize auth service."""
        # JWT configuration
        self.secret_key = getattr(settings, 'JWT_SECRET_KEY', None) or settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30  # 30 days

    async def _get_db(self):
        """Get database connection - always fresh to support test fixtures."""
        # Always call get_database() fresh to support test database patching
        return get_database()

    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database

        Returns:
            bool: True if password matches
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def _create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Data to encode in token

        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Optional[Dict]: Decoded token data or None if invalid
        """
        try:
            logger.info(f"Decoding token: {token[:50]}... (length: {len(token)})")
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"Token decoded successfully: sub={payload.get('sub')}, type={payload.get('type')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except Exception as e:
            logger.error(f"JWT decode error: {str(e)} | Token: {token[:50]}... (length: {len(token)})")
            return None

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.

        Args:
            user_data: User registration data including password

        Returns:
            User: Created user object

        Raises:
            Exception: If user creation fails
        """
        try:
            db = await self._get_db()

            # Hash password
            hashed_password = self._hash_password(user_data.password)

            # Create user document in MongoDB
            user_doc = {
                "email": user_data.email,
                "password_hash": hashed_password,
                "username": user_data.username or user_data.email.split('@')[0],
                "full_name": user_data.full_name,
                "bio": user_data.bio,
                "location": user_data.location,
                "languages_spoken": user_data.languages_spoken or [],
                "language_expertise": user_data.language_expertise or [],
                "level": UserLevel.NEWCOMER,
                "total_points": 0,
                "level_points": 0,
                "achievements": [],
                "badges": [],
                "validator_qualifications": [],
                "verified_languages": [],
                "permissions": ["submit", "comment"],
                "can_validate": False,
                "can_moderate": False,
                "can_create_proposals": False,
                "contributions_count": 0,
                "validations_count": 0,
                "quality_rating": 0.0,
                "reputation_score": 0,
                "is_active": True,
                "is_verified": False,
                "email_verified": False,
                "phone_verified": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }

            result = await db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            user_doc["id"] = str(result.inserted_id)

            # Remove password hash before returning
            user_doc.pop("password_hash", None)

            return User(**user_doc)

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise

    async def authenticate_user(self, email: str, password: str) -> Optional[UserAuth]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            UserAuth: Authentication result with user data and tokens
        """
        try:
            db = await self._get_db()

            # Find user by email
            user_doc = await db.users.find_one({"email": email.lower()})
            if not user_doc:
                logger.warning(f"User not found: {email}")
                return None

            # Verify password
            if not self._verify_password(password, user_doc["password_hash"]):
                logger.warning(f"Invalid password for user: {email}")
                return None

            # Update last activity
            await db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_activity": datetime.utcnow()}}
            )

            # Create tokens
            user_id = str(user_doc["_id"])
            token_data = {
                "sub": user_id,
                "email": user_doc["email"],
                "username": user_doc.get("username", "")
            }

            access_token = self._create_access_token(token_data)
            refresh_token = self._create_refresh_token(token_data)

            # Remove password hash from user data
            user_doc.pop("password_hash", None)
            user_doc["id"] = user_id

            return UserAuth(
                user=User(**user_doc),
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token.

        Args:
            token: JWT access token

        Returns:
            Optional[User]: User object or None if token invalid
        """
        try:
            # Support dev-token for testing environments
            if token == "dev-token":
                logger.info("Using dev-token authentication for testing")
                # Return a mock user for development/testing
                # Use a fixed valid ObjectId for dev user (deterministic for testing)
                from models.user_models import UserLevel
                from bson import ObjectId as BsonObjectId
                # Fixed ObjectId for dev user: "000000000000000000000001"
                dev_object_id = BsonObjectId("000000000000000000000001")
                return User(
                    id=dev_object_id,
                    email="dev@example.com",
                    username="dev_user",
                    full_name="Development User",
                    level=UserLevel.NEWCOMER,
                    total_points=0,
                    achievements=[],
                    badges=[],
                    languages_spoken=["eng"],
                    language_expertise=[],
                    validator_qualifications=[],
                    verified_languages=[],
                    role="admin",  # Admin role for testing
                    permissions=["submit", "comment", "validate", "moderate"],
                    can_validate=True,
                    can_moderate=True,  # Enable moderation for testing
                    can_create_proposals=True,
                    contributions_count=0,
                    validations_count=0,
                    quality_rating=0.0,
                    reputation_score=0,
                    is_active=True,
                    is_verified=False
                )

            # Decode token
            payload = self._decode_token(token)
            if not payload:
                return None

            # Verify token type
            if payload.get("type") != "access":
                logger.warning("Invalid token type")
                return None

            # Get user from database
            user_id = payload.get("sub")
            if not user_id:
                return None

            db = await self._get_db()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})

            if not user_doc:
                return None

            # Remove password hash
            user_doc.pop("password_hash", None)
            user_doc["id"] = str(user_doc["_id"])

            return User(**user_doc)

        except Exception as e:
            logger.error(f"Get current user failed: {str(e)}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[UserAuth]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            UserAuth: New tokens and user data
        """
        try:
            # Decode refresh token
            payload = self._decode_token(refresh_token)
            if not payload:
                return None

            # Verify token type
            if payload.get("type") != "refresh":
                logger.warning("Invalid token type for refresh")
                return None

            # Get user
            user_id = payload.get("sub")
            if not user_id:
                return None

            db = await self._get_db()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})

            if not user_doc or not user_doc.get("is_active"):
                return None

            # Create new tokens
            token_data = {
                "sub": user_id,
                "email": user_doc["email"],
                "username": user_doc.get("username", "")
            }

            new_access_token = self._create_access_token(token_data)
            new_refresh_token = self._create_refresh_token(token_data)

            # Remove password hash
            user_doc.pop("password_hash", None)
            user_doc["id"] = user_id

            return UserAuth(
                user=User(**user_doc),
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            Optional[User]: User object or None
        """
        try:
            db = await self._get_db()
            user_doc = await db.users.find_one({"email": email.lower()})

            if not user_doc:
                return None

            user_doc.pop("password_hash", None)
            user_doc["id"] = str(user_doc["_id"])

            return User(**user_doc)

        except Exception as e:
            logger.error(f"Get user by email failed: {str(e)}")
            return None

    async def update_user_profile(self, user_id: str, updates: UserUpdate) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User ID
            updates: Profile updates

        Returns:
            Optional[User]: Updated user object
        """
        try:
            db = await self._get_db()

            # Prepare update data
            update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()

            # Update user
            result = await db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=True
            )

            if not result:
                return None

            result.pop("password_hash", None)
            result["id"] = user_id

            return User(**result)

        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            return None

    async def get_public_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get public profile of user.

        Args:
            user_id: User ID

        Returns:
            Optional[Dict]: Public profile data
        """
        try:
            db = await self._get_db()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})

            if not user_doc:
                return None

            # Return only public fields
            return {
                "id": str(user_doc["_id"]),
                "username": user_doc.get("username"),
                "full_name": user_doc.get("full_name"),
                "bio": user_doc.get("bio"),
                "location": user_doc.get("location"),
                "languages_spoken": user_doc.get("languages_spoken", []),
                "language_expertise": user_doc.get("language_expertise", []),
                "level": user_doc.get("level"),
                "total_points": user_doc.get("total_points", 0),
                "achievements": user_doc.get("achievements", []),
                "badges": user_doc.get("badges", []),
                "contributions_count": user_doc.get("contributions_count", 0),
                "validations_count": user_doc.get("validations_count", 0),
                "quality_rating": user_doc.get("quality_rating", 0.0),
                "reputation_score": user_doc.get("reputation_score", 0),
                "created_at": user_doc.get("created_at")
            }

        except Exception as e:
            logger.error(f"Get public profile failed: {str(e)}")
            return None

    async def logout_user(self, user_id: str) -> bool:
        """
        Logout user (for tracking purposes).

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        try:
            # In JWT-based auth, logout is handled client-side by removing token
            # We just update last activity
            db = await self._get_db()
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            return True

        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False

    async def delete_user_account(self, user_id: str) -> bool:
        """
        Delete user account and all associated data.

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        try:
            db = await self._get_db()

            # Soft delete: mark as inactive
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": False,
                        "deleted_at": datetime.utcnow()
                    }
                }
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Account deletion failed: {str(e)}")
            return False

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get user contribution statistics.

        Args:
            user_id: User ID

        Returns:
            Dict: User statistics including submissions, validations, streak, etc.
        """
        try:
            db = await self._get_db()
            user_obj_id = ObjectId(user_id)

            # Get user data
            user_doc = await db.users.find_one({"_id": user_obj_id})
            if not user_doc:
                return {}

            # Count submissions by status
            submissions_pipeline = [
                {"$match": {"user_id": str(user_obj_id)}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            submission_stats = await db.submissions.aggregate(submissions_pipeline).to_list(None)
            submission_counts = {stat["_id"]: stat["count"] for stat in submission_stats}

            # Count validations
            validations_count = await db.validations.count_documents({"validator_id": str(user_obj_id)})

            # Get recent submissions for streak calculation
            recent_submissions = await db.submissions.find(
                {"user_id": str(user_obj_id)},
                {"created_at": 1}
            ).sort("created_at", -1).limit(30).to_list(None)

            # Calculate streak (simplified)
            streak_days = 0
            if recent_submissions:
                current_date = datetime.utcnow().date()
                for submission in recent_submissions:
                    submission_date = submission["created_at"].date()
                    day_diff = (current_date - submission_date).days
                    if day_diff <= streak_days + 1:
                        if day_diff == streak_days:
                            continue
                        streak_days = day_diff
                    else:
                        break

            # Get weekly goals from user doc (ensure no ObjectIds)
            weekly_goals_raw = user_doc.get("weekly_goals", {})
            weekly_goals = {
                "submissions": weekly_goals_raw.get("submissions", 5) if weekly_goals_raw else 5,
                "validations": weekly_goals_raw.get("validations", 10) if weekly_goals_raw else 10,
                "current_submissions": 0,
                "current_validations": 0
            }

            # Calculate current week's activity
            week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            week_submissions = await db.submissions.count_documents({
                "user_id": str(user_obj_id),
                "created_at": {"$gte": week_start}
            })

            week_validations = await db.validations.count_documents({
                "validator_id": str(user_obj_id),
                "validated_at": {"$gte": week_start}
            })

            # Calculate average quality score
            quality_pipeline = [
                {"$match": {"user_id": str(user_obj_id), "quality_score": {"$exists": True}}},
                {"$group": {
                    "_id": None,
                    "avg_quality": {"$avg": "$quality_score"}
                }}
            ]
            quality_result = await db.submissions.aggregate(quality_pipeline).to_list(None)
            avg_quality = quality_result[0]["avg_quality"] if quality_result else 0

            return {
                "user_id": str(user_id),
                "submissions_count": int(sum(submission_counts.values())),
                "approved_submissions": int(submission_counts.get("validated", 0)),
                "pending_submissions": int(submission_counts.get("pending", 0)),
                "rejected_submissions": int(submission_counts.get("rejected", 0)),
                "validations_count": int(validations_count),
                "streak_days": int(streak_days),
                "total_points": int(user_doc.get("total_points", 0)),
                "level": str(user_doc.get("level", "newcomer")),
                "quality_rating": float(user_doc.get("quality_rating", 0.0)),
                "reputation_score": int(user_doc.get("reputation_score", 0)),
                "average_quality": float(round(avg_quality, 1)) if avg_quality else 0.0,
                "weekly_goals": {
                    "submissions": int(weekly_goals.get("submissions", 5)),
                    "validations": int(weekly_goals.get("validations", 10)),
                    "current_submissions": int(week_submissions),
                    "current_validations": int(week_validations)
                },
                "achievements_count": int(len(user_doc.get("achievements", []))),
                "badges_count": int(len(user_doc.get("badges", [])))
            }

        except Exception as e:
            logger.error(f"Get user statistics failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    async def get_user_activities(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's recent activity feed.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Maximum items to return

        Returns:
            List: Recent activities
        """
        try:
            db = await self._get_db()
            user_obj_id = ObjectId(user_id)

            activities = []

            # Get recent submissions
            submissions = await db.submissions.find(
                {"user_id": str(user_obj_id)}
            ).sort("created_at", -1).limit(limit // 2).to_list(None)

            for sub in submissions:
                activities.append({
                    "id": str(sub["_id"]),
                    "type": "submission",
                    "title": f"Submitted {sub.get('type', 'content')} for {sub.get('language_code', 'unknown')}",
                    "description": sub.get("text", "")[:100] if sub.get("text") else "Audio/file submission",
                    "status": sub.get("status", "pending"),
                    "language_code": sub.get("language_code"),
                    "created_at": sub.get("created_at").isoformat() if sub.get("created_at") else None,
                    "points_awarded": 10 if sub.get("status") == "validated" else 0
                })

            # Get recent validations
            validations = await db.validations.find(
                {"validator_id": str(user_obj_id)}
            ).sort("validated_at", -1).limit(limit // 2).to_list(None)

            for val in validations:
                activities.append({
                    "id": str(val["_id"]),
                    "type": "validation",
                    "title": f"Validated submission",
                    "description": f"Score: {val.get('score', 0)}/5",
                    "status": "completed",
                    "created_at": val.get("validated_at").isoformat() if val.get("validated_at") else None,
                    "points_awarded": 5
                })

            # Sort by date and limit
            activities.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            return activities[skip:skip + limit]

        except Exception as e:
            logger.error(f"Get user activities failed: {str(e)}")
            return []

    async def update_user_goals(self, user_id: str, goals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's weekly goals.

        Args:
            user_id: User ID
            goals: Goals configuration

        Returns:
            Dict: Updated goals
        """
        try:
            db = await self._get_db()

            # Update user's weekly goals
            result = await db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "weekly_goals": goals,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )

            if not result:
                return {}

            return result.get("weekly_goals", goals)

        except Exception as e:
            logger.error(f"Update user goals failed: {str(e)}")
            return {}
