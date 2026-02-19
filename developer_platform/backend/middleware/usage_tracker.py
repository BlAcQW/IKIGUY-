"""
Usage Tracking Middleware for Developer Platform API.

Tracks API usage, costs, and quota enforcement.
Provides usage analytics and billing data.
MongoDB persistence for historical analytics.
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.collection import Collection
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None
    Collection = None

logger = logging.getLogger(__name__)


class UsageRecord(BaseModel):
    """Record of a single API usage event."""
    timestamp: datetime
    api_key: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    tokens_used: int = 1
    cost_credits: float = 0.0
    metadata: Optional[Dict] = None


class QuotaLimit(BaseModel):
    """Quota limits for an API key."""
    api_key: str
    plan: str
    daily_limit: int
    monthly_limit: int
    daily_used: int = 0
    monthly_used: int = 0
    last_reset_daily: datetime
    last_reset_monthly: datetime


class UsageTracker:
    """
    Track API usage and enforce quotas.

    Features:
    - Request counting per API key
    - Usage cost tracking (credits/tokens)
    - Daily and monthly quota enforcement
    - Usage analytics and reporting
    """

    # Cost multipliers for different operations
    ENDPOINT_COSTS = {
        "create_assistant": 1.0,
        "list_assistants": 0.1,
        "get_assistant": 0.1,
        "update_assistant": 0.5,
        "delete_assistant": 0.5,
        "initiate_call": 10.0,  # Calls are expensive
        "list_calls": 0.1,
        "get_call": 0.1,
        "create_workflow": 2.0,
        "list_workflows": 0.1,
        "get_workflow": 0.1,
        "update_workflow": 1.0,
        "delete_workflow": 0.5,
        "execute_workflow": 5.0,  # Executions are expensive
        "list_executions": 0.1,
        "get_execution": 0.1,
    }

    # Quota limits by plan
    PLAN_QUOTAS = {
        "free": {
            "daily_limit": 100,
            "monthly_limit": 1000,
        },
        "starter": {
            "daily_limit": 1000,
            "monthly_limit": 10000,
        },
        "professional": {
            "daily_limit": 10000,
            "monthly_limit": 100000,
        },
        "enterprise": {
            "daily_limit": 100000,
            "monthly_limit": 1000000,
        },
    }

    def __init__(self, mongo_db=None):
        """
        Initialize usage tracker with optional MongoDB persistence.

        Args:
            mongo_db: Optional MongoDB database for persistence
        """
        self.usage_records: Dict[str, List[UsageRecord]] = defaultdict(list)  # In-memory cache
        self.quotas: Dict[str, QuotaLimit] = {}  # In-memory quota cache
        self.last_cleanup = time.time()
        self.mongo_db = mongo_db

        if mongo_db:
            # Create collections
            self.usage_collection = mongo_db.usage_records
            self.quota_collection = mongo_db.usage_quotas

            # Create indexes for performance
            try:
                self.usage_collection.create_index([("api_key", ASCENDING), ("timestamp", DESCENDING)])
                self.usage_collection.create_index([("timestamp", DESCENDING)])
                self.quota_collection.create_index([("api_key", ASCENDING)], unique=True)
                logger.info("✅ Usage tracker initialized with MongoDB persistence")
            except Exception as e:
                logger.error(f"Error creating MongoDB indexes: {e}")
        else:
            self.usage_collection = None
            self.quota_collection = None
            logger.warning("⚠️  Usage tracker running in memory-only mode (no persistence)")

    def _get_or_create_quota(self, api_key: str, plan: str = "free") -> QuotaLimit:
        """
        Get or create quota limit for API key.
        Loads from MongoDB if available, otherwise creates new.

        Args:
            api_key: API key identifier
            plan: Plan tier (free, starter, professional, enterprise)

        Returns:
            QuotaLimit for the API key
        """
        # Check in-memory cache first
        if api_key in self.quotas:
            return self.quotas[api_key]

        # Try to load from MongoDB
        if self.quota_collection is not None:
            try:
                quota_doc = self.quota_collection.find_one({"api_key": api_key})
                if quota_doc:
                    # Convert MongoDB document to QuotaLimit
                    quota = QuotaLimit(
                        api_key=quota_doc["api_key"],
                        plan=quota_doc["plan"],
                        daily_limit=quota_doc["daily_limit"],
                        monthly_limit=quota_doc["monthly_limit"],
                        daily_used=quota_doc["daily_used"],
                        monthly_used=quota_doc["monthly_used"],
                        last_reset_daily=quota_doc["last_reset_daily"],
                        last_reset_monthly=quota_doc["last_reset_monthly"]
                    )
                    self.quotas[api_key] = quota  # Cache in memory
                    return quota
            except Exception as e:
                logger.error(f"Error loading quota from MongoDB: {e}")

        # Create new quota if not found
        limits = self.PLAN_QUOTAS.get(plan, self.PLAN_QUOTAS["free"])
        now = datetime.utcnow()

        quota = QuotaLimit(
            api_key=api_key,
            plan=plan,
            daily_limit=limits["daily_limit"],
            monthly_limit=limits["monthly_limit"],
            daily_used=0,
            monthly_used=0,
            last_reset_daily=now,
            last_reset_monthly=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
        self.quotas[api_key] = quota
        self._save_quota(quota)

        return quota

    def _save_quota(self, quota: QuotaLimit):
        """
        Save quota to MongoDB.

        Args:
            quota: QuotaLimit to save
        """
        if self.quota_collection is None:
            return

        try:
            # Upsert (update or insert) quota document
            self.quota_collection.update_one(
                {"api_key": quota.api_key},
                {"$set": quota.dict()},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving quota to MongoDB: {e}")

    def _reset_quotas_if_needed(self, quota: QuotaLimit):
        """
        Reset daily/monthly quotas if period has elapsed.
        Saves to MongoDB after reset.

        Args:
            quota: QuotaLimit to check and reset
        """
        now = datetime.utcnow()
        reset_occurred = False

        # Reset daily quota if needed
        if (now - quota.last_reset_daily).days >= 1:
            quota.daily_used = 0
            quota.last_reset_daily = now
            reset_occurred = True
            logger.info(f"Reset daily quota for {quota.api_key[:10]}...")

        # Reset monthly quota if needed (new month)
        if now.month != quota.last_reset_monthly.month or now.year != quota.last_reset_monthly.year:
            quota.monthly_used = 0
            quota.last_reset_monthly = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            reset_occurred = True
            logger.info(f"Reset monthly quota for {quota.api_key[:10]}...")

        # Save to MongoDB if reset occurred
        if reset_occurred:
            self._save_quota(quota)

    def check_quota(self, api_key: str, plan: str = "free", tokens: int = 1) -> tuple[bool, Optional[str]]:
        """
        Check if API key has quota available.

        Args:
            api_key: API key identifier
            plan: Plan tier
            tokens: Tokens to consume

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        quota = self._get_or_create_quota(api_key, plan)
        self._reset_quotas_if_needed(quota)

        # Check daily limit
        if quota.daily_used + tokens > quota.daily_limit:
            return False, f"Daily quota exceeded ({quota.daily_limit} requests/day)"

        # Check monthly limit
        if quota.monthly_used + tokens > quota.monthly_limit:
            return False, f"Monthly quota exceeded ({quota.monthly_limit} requests/month)"

        return True, None

    def record_usage(
        self,
        api_key: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        plan: str = "free",
        metadata: Optional[Dict] = None
    ):
        """
        Record API usage event.
        Saves to MongoDB for historical analytics.

        Args:
            api_key: API key identifier
            endpoint: Endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            plan: Plan tier
            metadata: Additional metadata
        """
        # Determine operation cost
        operation = self._extract_operation(endpoint, method)
        cost = self.ENDPOINT_COSTS.get(operation, 1.0)

        # Create usage record
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            tokens_used=1,
            cost_credits=cost,
            metadata=metadata
        )

        # Store in memory cache
        self.usage_records[api_key].append(record)

        # Save to MongoDB for persistence
        if self.usage_collection is not None:
            try:
                self.usage_collection.insert_one(record.dict())
            except Exception as e:
                logger.error(f"Error saving usage record to MongoDB: {e}")

        # Update quota usage
        quota = self._get_or_create_quota(api_key, plan)
        self._reset_quotas_if_needed(quota)
        quota.daily_used += 1
        quota.monthly_used += 1

        # Save updated quota to MongoDB
        self._save_quota(quota)

        # Cleanup old records periodically
        if time.time() - self.last_cleanup > 3600:  # Every hour
            self._cleanup_old_records()

        logger.info(
            f"Usage recorded: {api_key[:10]}... {method} {endpoint} "
            f"[{status_code}] {response_time_ms:.0f}ms cost={cost}"
        )

    def _extract_operation(self, endpoint: str, method: str) -> str:
        """
        Extract operation name from endpoint and method.

        Args:
            endpoint: Endpoint path
            method: HTTP method

        Returns:
            Operation name
        """
        # Map endpoint patterns to operations
        if "/assistants" in endpoint:
            if method == "POST":
                return "create_assistant"
            elif method == "GET":
                if endpoint.endswith("/assistants"):
                    return "list_assistants"
                else:
                    return "get_assistant"
            elif method == "PATCH":
                return "update_assistant"
            elif method == "DELETE":
                return "delete_assistant"

        elif "/calls" in endpoint:
            if method == "POST":
                return "initiate_call"
            elif method == "GET":
                if endpoint.endswith("/calls"):
                    return "list_calls"
                else:
                    return "get_call"

        elif "/workflows" in endpoint:
            if method == "POST":
                if "activate" in endpoint:
                    return "activate_workflow"
                return "create_workflow"
            elif method == "GET":
                if endpoint.endswith("/workflows"):
                    return "list_workflows"
                else:
                    return "get_workflow"
            elif method == "PATCH":
                return "update_workflow"
            elif method == "DELETE":
                return "delete_workflow"

        elif "/executions" in endpoint:
            if method == "POST":
                return "execute_workflow"
            elif method == "GET":
                if endpoint.endswith("/executions"):
                    return "list_executions"
                else:
                    return "get_execution"

        return "unknown_operation"

    def _cleanup_old_records(self):
        """Remove usage records older than 30 days."""
        cutoff = datetime.utcnow() - timedelta(days=30)
        removed_count = 0

        for api_key in list(self.usage_records.keys()):
            original_count = len(self.usage_records[api_key])
            self.usage_records[api_key] = [
                r for r in self.usage_records[api_key]
                if r.timestamp > cutoff
            ]
            removed_count += original_count - len(self.usage_records[api_key])

            # Remove key if no records left
            if not self.usage_records[api_key]:
                del self.usage_records[api_key]

        self.last_cleanup = time.time()
        logger.info(f"Cleaned up {removed_count} old usage records")

    def get_usage_stats(
        self,
        api_key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get usage statistics for an API key.
        Queries MongoDB for accurate historical data.

        Args:
            api_key: API key identifier
            start_date: Start date for stats (default: 30 days ago)
            end_date: End date for stats (default: now)

        Returns:
            Dict with usage statistics
        """
        # Default date range: last 30 days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        records = []

        # Query MongoDB if available (preferred - has all historical data)
        if self.usage_collection is not None:
            try:
                cursor = self.usage_collection.find({
                    "api_key": api_key,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }).sort("timestamp", DESCENDING)

                for doc in cursor:
                    records.append(UsageRecord(**doc))
            except Exception as e:
                logger.error(f"Error querying MongoDB for usage stats: {e}")
                # Fall back to in-memory cache
                if api_key in self.usage_records:
                    records = [
                        r for r in self.usage_records[api_key]
                        if start_date <= r.timestamp <= end_date
                    ]
        else:
            # Use in-memory cache if MongoDB not available
            if api_key in self.usage_records:
                records = [
                    r for r in self.usage_records[api_key]
                    if start_date <= r.timestamp <= end_date
                ]

        if not records:
            return {
                "total_requests": 0,
                "total_cost": 0.0,
                "avg_response_time_ms": 0.0,
                "requests_by_endpoint": {},
                "requests_by_status": {},
                "daily_usage": []
            }

        # Calculate statistics
        total_requests = len(records)
        total_cost = sum(r.cost_credits for r in records)
        avg_response_time = sum(r.response_time_ms for r in records) / total_requests

        # Group by endpoint
        requests_by_endpoint = defaultdict(int)
        for r in records:
            requests_by_endpoint[r.endpoint] += 1

        # Group by status
        requests_by_status = defaultdict(int)
        for r in records:
            requests_by_status[str(r.status_code)] += 1

        # Daily usage breakdown
        daily_usage = defaultdict(lambda: {"requests": 0, "cost": 0.0})
        for r in records:
            day = r.timestamp.date().isoformat()
            daily_usage[day]["requests"] += 1
            daily_usage[day]["cost"] += r.cost_credits

        return {
            "total_requests": total_requests,
            "total_cost": round(total_cost, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "requests_by_endpoint": dict(requests_by_endpoint),
            "requests_by_status": dict(requests_by_status),
            "daily_usage": [
                {"date": k, **v}
                for k, v in sorted(daily_usage.items())
            ]
        }

    def get_quota_status(self, api_key: str, plan: str = "free") -> Dict:
        """
        Get quota status for an API key.

        Args:
            api_key: API key identifier
            plan: Plan tier

        Returns:
            Dict with quota information
        """
        quota = self._get_or_create_quota(api_key, plan)
        self._reset_quotas_if_needed(quota)

        return {
            "plan": quota.plan,
            "daily": {
                "limit": quota.daily_limit,
                "used": quota.daily_used,
                "remaining": quota.daily_limit - quota.daily_used,
                "reset_at": (quota.last_reset_daily + timedelta(days=1)).isoformat()
            },
            "monthly": {
                "limit": quota.monthly_limit,
                "used": quota.monthly_used,
                "remaining": quota.monthly_limit - quota.monthly_used,
                "reset_at": (quota.last_reset_monthly.replace(month=quota.last_reset_monthly.month % 12 + 1)).isoformat()
            }
        }


# Global usage tracker instance (initialized without MongoDB by default)
# MongoDB database should be set via set_mongo_db() after creation
usage_tracker = UsageTracker()


def set_mongo_db(mongo_db):
    """
    Set MongoDB database for usage tracker persistence.
    Call this during app startup after creating MongoDB connection.

    Args:
        mongo_db: MongoDB database instance
    """
    global usage_tracker
    usage_tracker.mongo_db = mongo_db
    usage_tracker.usage_collection = mongo_db.usage_records
    usage_tracker.quota_collection = mongo_db.usage_quotas

    # Create indexes for performance
    try:
        usage_tracker.usage_collection.create_index([("api_key", ASCENDING), ("timestamp", DESCENDING)])
        usage_tracker.usage_collection.create_index([("timestamp", DESCENDING)])
        usage_tracker.quota_collection.create_index([("api_key", ASCENDING)], unique=True)
        logger.info("✅ MongoDB persistence enabled for usage tracker")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")


async def usage_tracking_middleware(request: Request, call_next):
    """
    Usage tracking middleware for FastAPI.

    Tracks all API requests and enforces quotas.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response with usage tracking
    """
    # Skip tracking for health checks and docs
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get API key from header
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

    if not api_key:
        # No API key = use IP address for tracking
        api_key = request.client.host
        plan = "free"
    else:
        # TODO: Get plan from database based on API key
        plan = "free"

    # Check quota before processing
    allowed, error_message = usage_tracker.check_quota(api_key, plan)

    if not allowed:
        logger.warning(f"Quota exceeded for {api_key[:10]}... on {request.url.path}")
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "QUOTA_EXCEEDED",
                    "message": error_message,
                    "field": None
                },
                "request_id": f"req_{int(time.time())}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    # Track request timing
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Record usage
    usage_tracker.record_usage(
        api_key=api_key,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        response_time_ms=response_time_ms,
        plan=plan,
        metadata={
            "user_agent": request.headers.get("user-agent"),
            "ip": request.client.host
        }
    )

    return response
