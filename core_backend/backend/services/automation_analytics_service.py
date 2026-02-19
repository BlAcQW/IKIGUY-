"""
Automation Analytics Service

Handles analytics aggregation and storage for automation configurations.
Fetches call data from VAPI and computes metrics for display.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

import sys
sys.path.append('/opt/kasaai/apps/shared')
from integration.vapi import vapi_service
from ai.ai_powered_features import (
    AIPoweredFeatures,
    CallSummary,
    CallOutcome,
    ConversationSentiment
)

logger = logging.getLogger(__name__)


class AutomationAnalyticsService:
    """
    Service for managing automation analytics.

    Aggregates call data from VAPI, stores snapshots in MongoDB,
    and provides analytics for frontend display.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.analytics_collection = db.automation_analytics
        self.calls_collection = db.automation_calls
        self.vapi_calls_collection = db.vapi_calls  # Enhanced calls with AI analysis
        self.configs_collection = db.automation_configs
        self.vapi_service = vapi_service

        # Cache for analytics (5 minute TTL)
        self._cache = {}
        self._cache_ttl = 300  # seconds

        # Settings collection for database-stored cost rates
        self.settings_collection = db.automation_settings

        # Initialize AI features for call analysis
        ai_config = {
            'sentiment_threshold': 0.6,
            'engagement_threshold': 0.5,
            'objection_confidence_threshold': 0.7,
        }
        self.ai_features = AIPoweredFeatures(ai_config)
        logger.info("Automation Analytics Service initialized with AI features")

    async def initialize(self):
        """Initialize indexes for analytics collections."""
        try:
            # Create indexes for automation_analytics
            await self.analytics_collection.create_index([
                ("automation_id", 1),
                ("period_start", -1)
            ])

            # Create indexes for automation_calls
            await self.calls_collection.create_index([
                ("automation_id", 1),
                ("started_at", -1)
            ])
            await self.calls_collection.create_index("call_id", unique=True)

            logger.info("Analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")

    def _get_assistant_id_from_config(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Extract VAPI assistant ID from automation config.

        Checks multiple possible locations in order of preference:
        1. deployment_info.vapi_assistant_id (new format)
        2. vapi_agent.assistant_id (snake_case format)
        3. vapiAgent.assistantId (camelCase format)
        4. assistant_id (top-level field)

        Args:
            config: Automation configuration document

        Returns:
            VAPI assistant ID if found, None otherwise
        """
        # Check deployment_info
        deployment_info = config.get("deployment_info", {})
        if deployment_info and deployment_info.get("vapi_assistant_id"):
            return deployment_info.get("vapi_assistant_id")

        # Check vapi_agent (snake_case)
        vapi_agent = config.get("vapi_agent", {})
        if vapi_agent and vapi_agent.get("assistant_id"):
            return vapi_agent.get("assistant_id")

        # Check vapiAgent (camelCase)
        vapi_agent_camel = config.get("vapiAgent", {})
        if vapi_agent_camel and vapi_agent_camel.get("assistantId"):
            return vapi_agent_camel.get("assistantId")

        # Check top-level field
        if config.get("assistant_id"):
            return config.get("assistant_id")

        return None

    async def _get_custom_cost_rate(
        self,
        config_id: str,
        assistant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get custom cost rate from database for an automation.

        Args:
            config_id: Automation configuration ID
            assistant_id: Optional VAPI assistant ID

        Returns:
            Cost settings dict or None if not configured
        """
        try:
            # First try to find by automation_id
            settings = await self.settings_collection.find_one({
                "automation_id": config_id
            })

            if settings and settings.get("cost_settings"):
                return settings["cost_settings"]

            # Fallback: try to find by assistant_id
            if assistant_id:
                settings = await self.settings_collection.find_one({
                    "assistant_id": assistant_id
                })
                if settings and settings.get("cost_settings"):
                    return settings["cost_settings"]

            return None

        except Exception as e:
            logger.error(f"Error fetching custom cost rate: {e}")
            return None

    async def get_automation_analytics(
        self,
        config_id: str,
        time_range: str = "30d",
        force_refresh: bool = False,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for an automation.

        Uses VAPI Analytics API for accurate aggregate totals (total calls, duration, cost)
        that are not limited by API pagination limits.

        Args:
            config_id: Automation configuration ID
            time_range: Time range for analytics (7d, 30d, 90d, all)
            force_refresh: Force refresh from VAPI instead of using cache
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Analytics data with metrics, trends, and recent calls
        """
        try:
            # Check cache first (unless force refresh)
            cache_key = f"{config_id}:{time_range}:{organization_id}"
            if not force_refresh and cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if (datetime.now(timezone.utc) - cached_time).total_seconds() < self._cache_ttl:
                    logger.debug(f"Returning cached analytics for {config_id}, organization={organization_id}")
                    return cached_data

            # Get automation configuration with organization validation
            query_filter = {"_id": ObjectId(config_id)}
            if organization_id:
                query_filter["organization_id"] = organization_id

            config = await self.configs_collection.find_one(query_filter)
            if not config:
                return {"error": "Configuration not found"}

            # Get VAPI assistant ID from config (checks multiple possible locations)
            assistant_id = self._get_assistant_id_from_config(config)
            if not assistant_id:
                return {
                    "automation_id": config_id,
                    "assistant_id": None,
                    "error": "No VAPI assistant deployed",
                    "metrics": self._get_empty_metrics()
                }

            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(time_range, end_date)

            # === STEP 1: Get aggregate totals from VAPI Analytics API ===
            # Reason: This provides accurate totals without pagination limits
            vapi_analytics = await self.vapi_service.get_assistant_analytics(
                assistant_id=assistant_id,
                start_date=start_date,
                end_date=end_date
            )

            # === STEP 2: Fetch recent calls for detailed metrics and display ===
            # This is limited to 1000 calls but provides detailed call data
            calls = await self._fetch_vapi_calls(assistant_id, start_date, end_date)

            # Aggregate metrics from recent calls (for breakdown, sentiment, etc.)
            metrics = self._aggregate_call_metrics(calls)

            # === STEP 3: Override totals with accurate VAPI Analytics data ===
            if vapi_analytics.get("success"):
                # Use accurate totals from Analytics API
                metrics["total_calls"] = vapi_analytics.get("total_calls", metrics["total_calls"])
                metrics["total_duration"] = vapi_analytics.get("total_duration_seconds", metrics["total_duration"])
                metrics["total_duration_minutes"] = vapi_analytics.get("total_duration_minutes", metrics["total_duration"] / 60)
                metrics["avg_duration"] = vapi_analytics.get("avg_duration_seconds", metrics["avg_duration"])
                metrics["min_duration"] = vapi_analytics.get("min_duration_minutes", 0) * 60
                metrics["max_duration"] = vapi_analytics.get("max_duration_minutes", 0) * 60

                # VAPI cost breakdown
                vapi_cost_breakdown = vapi_analytics.get("cost_breakdown", {})
                metrics["vapi_cost_breakdown"] = {
                    "llm": vapi_cost_breakdown.get("llm", 0),
                    "stt": vapi_cost_breakdown.get("stt", 0),
                    "tts": vapi_cost_breakdown.get("tts", 0),
                    "vapi": vapi_cost_breakdown.get("vapi", 0),
                    "transport": vapi_cost_breakdown.get("transport", 0),
                    "total": vapi_cost_breakdown.get("total", 0)
                }

                # Usage metrics (tokens, characters)
                usage = vapi_analytics.get("usage", {})
                metrics["usage"] = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "tts_characters": usage.get("tts_characters", 0)
                }

                # Calculate success rate based on actual totals
                # Reason: We can't get exact success count from Analytics API,
                # so we use the ratio from sampled calls
                if len(calls) > 0 and metrics["total_calls"] > 0:
                    sampled_success_rate = metrics["successful_calls"] / len(calls)
                    metrics["successful_calls"] = int(metrics["total_calls"] * sampled_success_rate)
                    metrics["success_rate"] = round(sampled_success_rate * 100, 1)

            # === STEP 4: Apply custom cost rate from database if configured ===
            custom_rate = await self._get_custom_cost_rate(config_id, assistant_id)
            if custom_rate and custom_rate.get("rate_per_call"):
                # Cost per call calculation
                custom_cost = metrics["total_calls"] * custom_rate["rate_per_call"]
                metrics["total_cost"] = round(custom_cost, 2)
                metrics["avg_cost_per_call"] = custom_rate["rate_per_call"]
                metrics["cost_currency"] = custom_rate.get("currency", "GHS")
                metrics["cost_currency_symbol"] = custom_rate.get("currency_symbol", "GH₵")
                metrics["cost_rate_per_call"] = custom_rate["rate_per_call"]
                metrics["cost_breakdown"] = {
                    "custom_cost": round(custom_cost, 2),
                    "rate_per_call": custom_rate["rate_per_call"],
                    "currency": custom_rate.get("currency", "GHS"),
                    "total_calls": metrics["total_calls"]
                }
                logger.info(f"Applied custom cost rate for {config_id}: {custom_rate['rate_per_call']} {custom_rate.get('currency', 'GHS')}/call = {custom_cost:.2f}")

            # Get trend data
            trend_data = self._calculate_trend_data(calls, time_range)

            # Get recent calls
            recent_calls = sorted(
                calls,
                key=lambda x: x.get("started_at", x.get("createdAt", "")),
                reverse=True
            )[:10]

            # Store snapshot in database
            await self._store_analytics_snapshot(
                config_id,
                assistant_id,
                start_date,
                end_date,
                metrics,
                trend_data
            )

            # Prepare response
            analytics_data = {
                "automation_id": config_id,
                "automation_name": config.get("automation_name", "Unknown"),
                "assistant_id": assistant_id,
                "time_range": time_range,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "metrics": metrics,
                "trend_data": trend_data,
                "recent_calls": recent_calls,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            # Update cache
            self._cache[cache_key] = (analytics_data, datetime.now(timezone.utc))

            logger.info(f"Retrieved analytics for automation {config_id}, organization={organization_id}: {metrics['total_calls']} calls, {metrics['total_duration']/60:.2f} min")
            return analytics_data

        except Exception as e:
            logger.error(f"Error getting automation analytics for {config_id}, organization={organization_id}: {e}")
            return {
                "automation_id": config_id,
                "error": str(e),
                "metrics": self._get_empty_metrics()
            }

    async def get_automation_calls(
        self,
        config_id: str,
        page: int = 1,
        limit: int = 20,
        status_filter: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated call history for an automation.

        Args:
            config_id: Automation configuration ID
            page: Page number (1-indexed)
            limit: Number of calls per page
            status_filter: Optional status filter (answered, ended, failed)
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Paginated call history with metadata
        """
        try:
            query = {"automation_id": config_id}
            if status_filter:
                query["status"] = status_filter
            if organization_id:
                query["organization_id"] = organization_id

            # Get total count
            total_count = await self.calls_collection.count_documents(query)

            # Calculate pagination
            skip = (page - 1) * limit

            # Get calls
            cursor = self.calls_collection.find(query).sort("started_at", -1).skip(skip).limit(limit)
            calls = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for call in calls:
                call["id"] = str(call["_id"])
                del call["_id"]

            logger.info(f"Retrieved {len(calls)} calls for automation {config_id}, organization={organization_id}")
            return {
                "calls": calls,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            }

        except Exception as e:
            logger.error(f"Error getting automation calls for {config_id}, organization={organization_id}: {e}")
            return {
                "calls": [],
                "pagination": {"page": 1, "limit": limit, "total": 0, "pages": 0},
                "error": str(e)
            }

    async def sync_automation_calls(
        self,
        config_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync calls from VAPI to local database for an automation.

        Args:
            config_id: Automation configuration ID
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Sync result with counts
        """
        try:
            # Get automation configuration with organization validation
            query_filter = {"_id": ObjectId(config_id)}
            if organization_id:
                query_filter["organization_id"] = organization_id

            config = await self.configs_collection.find_one(query_filter)
            if not config:
                return {"success": False, "error": "Configuration not found"}

            # Get VAPI assistant ID from config (checks multiple possible locations)
            assistant_id = self._get_assistant_id_from_config(config)
            if not assistant_id:
                return {"success": False, "error": "No VAPI assistant deployed"}

            # Fetch all calls from VAPI (last 90 days)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=90)

            calls = await self._fetch_vapi_calls(assistant_id, start_date, end_date)

            # Store calls in database
            new_count = 0
            updated_count = 0

            for call in calls:
                call_doc = {
                    "automation_id": config_id,
                    "call_id": call["id"],
                    "assistant_id": assistant_id,
                    "customer_number": call.get("customer", {}).get("number"),
                    "status": call.get("status"),
                    "duration": call.get("duration"),
                    "ended_reason": call.get("endedReason"),
                    "transcript": call.get("transcript_full", call.get("transcript")),
                    "recording_url": call.get("recordingUrl"),
                    "metadata": call.get("metadata", {}),
                    "started_at": datetime.fromisoformat(call["createdAt"].replace("Z", "+00:00")) if call.get("createdAt") else None,
                    "ended_at": datetime.fromisoformat(call["endedAt"].replace("Z", "+00:00")) if call.get("endedAt") else None,
                    "synced_at": datetime.now(timezone.utc),
                    # AI-enriched fields
                    "ai_summary": call.get("ai_summary"),
                    "sentiment": call.get("sentiment"),
                    # Cost tracking
                    "vapi_cost": float(call.get("cost", 0)) if call.get("cost") else 0.0,  # AI service costs
                    "vonage_cost": call.get("vonage_cost"),  # Telephony costs
                    "ai_enriched": call.get("ai_enriched", False)
                }

                # Upsert call record
                result = await self.calls_collection.update_one(
                    {"call_id": call["id"]},
                    {"$set": call_doc},
                    upsert=True
                )

                if result.upserted_id:
                    new_count += 1
                elif result.modified_count > 0:
                    updated_count += 1

            logger.info(f"Synced {new_count} new, {updated_count} updated calls for automation {config_id}, organization={organization_id}")
            return {
                "success": True,
                "automation_id": config_id,
                "total_calls": len(calls),
                "new_calls": new_count,
                "updated_calls": updated_count,
                "synced_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error syncing automation calls for {config_id}, organization={organization_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _fetch_vapi_calls(
        self,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch calls from VAPI API and enrich with AI analysis from vapi_calls collection.

        Args:
            assistant_id: VAPI assistant ID
            start_date: Start date for call filter
            end_date: End date for call filter

        Returns:
            List of enriched call records with AI summaries and transcripts
        """
        try:
            # === STEP 1: Get calls from VAPI API ===
            result = await self.vapi_service.get_calls()

            if not result.get("success"):
                logger.error(f"Failed to fetch calls from VAPI: {result.get('error')}")
                return []

            all_calls = result.get("data", [])

            # Filter calls by assistant_id and date range
            filtered_calls = []
            for call in all_calls:
                # Check assistant ID
                if call.get("assistantId") != assistant_id:
                    continue

                # Check date range
                created_at_str = call.get("createdAt")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if start_date <= created_at <= end_date:
                            filtered_calls.append(call)
                    except Exception:
                        continue

            logger.info(f"Fetched {len(filtered_calls)} calls from VAPI for assistant {assistant_id}")

            # === STEP 2: Enrich with AI analysis from vapi_calls collection ===
            enriched_calls = []
            for call in filtered_calls:
                call_id = call.get("id")

                # Query vapi_calls collection for AI-enriched data
                vapi_call_doc = await self.vapi_calls_collection.find_one({"call_id": call_id})

                if vapi_call_doc:
                    # Merge VAPI data with AI-enriched data
                    call["ai_summary"] = vapi_call_doc.get("summary")
                    call["transcript_full"] = vapi_call_doc.get("transcript")
                    call["transcript_preview"] = (
                        vapi_call_doc.get("transcript", "")[:300]
                        if vapi_call_doc.get("transcript") else None
                    )
                    call["sentiment"] = vapi_call_doc.get("metadata", {}).get("sentiment")
                    call["vonage_cost"] = vapi_call_doc.get("vonage_cost")
                    call["ai_enriched"] = True
                    logger.debug(f"Enriched call {call_id} with AI data")
                else:
                    # Generate AI analysis if not available
                    call["ai_enriched"] = False
                    logger.debug(f"No AI enrichment found for call {call_id}")

                # Extract VAPI cost from API response (AI service costs: GPT-4, voice synthesis, etc.)
                vapi_api_cost = call.get("cost", 0)
                call["vapi_cost"] = float(vapi_api_cost) if vapi_api_cost else 0.0

                enriched_calls.append(call)

            logger.info(f"Enriched {len(enriched_calls)} calls with AI analysis")
            return enriched_calls

        except Exception as e:
            logger.error(f"Error fetching and enriching VAPI calls: {e}")
            return []

    def _aggregate_call_metrics(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate metrics from call data including AI-powered sentiment analysis.

        Args:
            calls: List of enriched call records from VAPI

        Returns:
            Aggregated metrics dictionary with AI insights
        """
        if not calls:
            return self._get_empty_metrics()

        total_calls = len(calls)
        successful_calls = 0
        failed_calls = 0
        voicemail_calls = 0
        no_answer_calls = 0
        total_duration = 0
        durations = []
        ai_enriched_count = 0
        total_cost = 0.0
        total_vapi_cost = 0.0  # AI service costs (GPT-4, ElevenLabs, Deepgram)
        total_vonage_cost = 0.0  # Telephony costs (phone minutes)

        call_breakdown = {
            "answered": 0,
            "ended": 0,
            "failed": 0,
            "voicemail": 0,
            "no_answer": 0,
            "other": 0
        }

        # AI sentiment tracking
        sentiment_counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "mixed": 0
        }

        for call in calls:
            status = call.get("status", "").lower()
            ended_reason = call.get("endedReason", "").lower() if call.get("endedReason") else ""
            duration = call.get("duration", 0) or 0

            # Count by status
            if status == "ended" and duration > 0:
                successful_calls += 1
                call_breakdown["ended"] += 1
            elif "voicemail" in ended_reason:
                voicemail_calls += 1
                call_breakdown["voicemail"] += 1
            elif "no-answer" in ended_reason or "no_answer" in ended_reason:
                no_answer_calls += 1
                call_breakdown["no_answer"] += 1
            elif status == "failed":
                failed_calls += 1
                call_breakdown["failed"] += 1
            else:
                call_breakdown["other"] += 1

            # Track duration
            if duration > 0:
                total_duration += duration
                durations.append(duration)

            # Track AI enrichment
            if call.get("ai_enriched"):
                ai_enriched_count += 1

                # Track sentiment if available
                sentiment = call.get("sentiment")
                if sentiment:
                    sentiment_lower = sentiment.lower()
                    if sentiment_lower in sentiment_counts:
                        sentiment_counts[sentiment_lower] += 1

            # Track costs
            # VAPI costs (AI service: GPT-4, ElevenLabs, Deepgram)
            vapi_cost = call.get("vapi_cost") or call.get("cost", 0)
            if vapi_cost:
                total_vapi_cost += float(vapi_cost)

            # Vonage costs (telephony: phone minutes)
            vonage_cost = call.get("vonage_cost")
            if vonage_cost:
                total_vonage_cost += float(vonage_cost)

            # Total cost is sum of both
            total_cost = total_vapi_cost + total_vonage_cost

        # Calculate metrics
        avg_duration = total_duration / len(durations) if durations else 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        connect_rate = ((successful_calls + voicemail_calls) / total_calls * 100) if total_calls > 0 else 0

        # Calculate AI enrichment rate
        ai_enrichment_rate = (ai_enriched_count / total_calls * 100) if total_calls > 0 else 0

        # Determine dominant sentiment
        dominant_sentiment = "neutral"
        if sentiment_counts:
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "voicemail_calls": voicemail_calls,
            "no_answer_calls": no_answer_calls,
            "avg_duration": round(avg_duration, 1),
            "total_duration": total_duration,
            "success_rate": round(success_rate, 1),
            "connect_rate": round(connect_rate, 1),
            "call_breakdown": call_breakdown,
            # AI-powered metrics
            "ai_enriched_count": ai_enriched_count,
            "ai_enrichment_rate": round(ai_enrichment_rate, 1),
            "sentiment_breakdown": sentiment_counts,
            "dominant_sentiment": dominant_sentiment,
            "total_cost": round(total_cost, 4),
            "avg_cost_per_call": round(total_cost / total_calls, 4) if total_calls > 0 else 0,
            # Cost breakdown by type
            "cost_breakdown": {
                "vapi_cost": round(total_vapi_cost, 4),  # AI service costs (GPT-4, voice, transcription)
                "vonage_cost": round(total_vonage_cost, 4),  # Telephony costs (phone minutes)
                "total_cost": round(total_cost, 4)
            }
        }

    def _calculate_trend_data(
        self,
        calls: List[Dict[str, Any]],
        time_range: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate trend data for charts.

        Args:
            calls: List of call records
            time_range: Time range for grouping (7d, 30d, 90d, all)

        Returns:
            List of daily aggregates for trend visualization
        """
        if not calls:
            return []

        # Group calls by date
        daily_data = {}

        for call in calls:
            created_at_str = call.get("createdAt")
            if not created_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                date_key = created_at.strftime("%Y-%m-%d")

                if date_key not in daily_data:
                    daily_data[date_key] = {
                        "date": date_key,
                        "calls": 0,
                        "successful": 0,
                        "duration": 0
                    }

                daily_data[date_key]["calls"] += 1

                if call.get("status") == "ended" and (call.get("duration") or 0) > 0:
                    daily_data[date_key]["successful"] += 1

                daily_data[date_key]["duration"] += call.get("duration", 0) or 0

            except Exception as e:
                logger.debug(f"Error parsing date for trend: {e}")
                continue

        # Convert to list and sort by date
        trend_list = sorted(daily_data.values(), key=lambda x: x["date"])

        return trend_list

    async def _store_analytics_snapshot(
        self,
        config_id: str,
        assistant_id: str,
        start_date: datetime,
        end_date: datetime,
        metrics: Dict[str, Any],
        trend_data: List[Dict[str, Any]]
    ) -> None:
        """
        Store analytics snapshot in database.

        Args:
            config_id: Automation configuration ID
            assistant_id: VAPI assistant ID
            start_date: Period start date
            end_date: Period end date
            metrics: Aggregated metrics
            trend_data: Trend data for charts
        """
        try:
            snapshot_doc = {
                "automation_id": config_id,
                "assistant_id": assistant_id,
                "period_start": start_date,
                "period_end": end_date,
                "metrics": metrics,
                "trend_data": trend_data,
                "last_synced": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc)
            }

            # Upsert snapshot
            await self.analytics_collection.update_one(
                {
                    "automation_id": config_id,
                    "period_start": start_date,
                    "period_end": end_date
                },
                {"$set": snapshot_doc},
                upsert=True
            )

            logger.debug(f"Stored analytics snapshot for {config_id}")

        except Exception as e:
            logger.error(f"Error storing analytics snapshot: {e}")

    def _get_start_date(self, time_range: str, end_date: datetime) -> datetime:
        """Get start date based on time range."""
        if time_range == "7d":
            return end_date - timedelta(days=7)
        elif time_range == "30d":
            return end_date - timedelta(days=30)
        elif time_range == "90d":
            return end_date - timedelta(days=90)
        elif time_range == "all":
            return end_date - timedelta(days=365)  # Max 1 year
        else:
            return end_date - timedelta(days=30)  # Default to 30 days

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Get empty metrics structure with AI fields."""
        return {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "voicemail_calls": 0,
            "no_answer_calls": 0,
            "avg_duration": 0,
            "total_duration": 0,
            "success_rate": 0,
            "connect_rate": 0,
            "call_breakdown": {
                "answered": 0,
                "ended": 0,
                "failed": 0,
                "voicemail": 0,
                "no_answer": 0,
                "other": 0
            },
            # AI-powered metrics
            "ai_enriched_count": 0,
            "ai_enrichment_rate": 0,
            "sentiment_breakdown": {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "mixed": 0
            },
            "dominant_sentiment": "neutral",
            "total_cost": 0,
            "avg_cost_per_call": 0,
            # Cost breakdown by type
            "cost_breakdown": {
                "vapi_cost": 0,  # AI service costs
                "vonage_cost": 0,  # Telephony costs
                "total_cost": 0
            }
        }


# Global service instance
_analytics_service: Optional[AutomationAnalyticsService] = None


async def get_analytics_service(db: AsyncIOMotorDatabase) -> AutomationAnalyticsService:
    """Get or create the global analytics service instance."""
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = AutomationAnalyticsService(db)
        await _analytics_service.initialize()

    return _analytics_service
