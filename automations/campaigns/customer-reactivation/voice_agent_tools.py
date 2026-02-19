"""
Enhanced Customer Reactivation Voice Agent Tools
AI-powered customer reactivation featuring behavioral analysis, churn prediction,
personalized offers, and comprehensive reactivation analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
import asyncio
import logging
from enum import Enum

# Database and API imports
from pymongo import MongoClient
from bson import ObjectId
import httpx
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerValueTier(str, Enum):
    HIGH_VALUE = "high_value"
    MEDIUM_VALUE = "medium_value"
    STANDARD = "standard"

class ChurnReason(str, Enum):
    PRICE_SENSITIVITY = "price_sensitivity"
    FEATURE_GAPS = "feature_gaps"
    POOR_EXPERIENCE = "poor_experience"
    COMPETITOR_SWITCH = "competitor_switch"
    LACK_OF_ENGAGEMENT = "lack_of_engagement"
    LIFE_CHANGES = "life_changes"

class OfferType(str, Enum):
    DISCOUNT = "discount"
    FREE_TRIAL = "free_trial"
    BONUS_FEATURES = "bonus_features"
    PERSONAL_ONBOARDING = "personal_onboarding"
    ACCOUNT_CREDIT = "account_credit"

class ReactivationType(str, Enum):
    ACCOUNT_RESTORATION = "account_restoration"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SERVICE_RESTART = "service_restart"
    PLAN_UPGRADE = "plan_upgrade"

class FollowUpType(str, Enum):
    PHONE_CALL = "phone_call"
    EMAIL_SEQUENCE = "email_sequence"
    PRODUCT_DEMO = "product_demo"
    CHECK_IN = "check_in"
    OFFER_REMINDER = "offer_reminder"

class CommunicationFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    MINIMAL = "minimal"

class EscalationReason(str, Enum):
    COMPLEX_TECHNICAL_ISSUE = "complex_technical_issue"
    HIGH_VALUE_CUSTOMER = "high_value_customer"
    LEGAL_CONCERNS = "legal_concerns"
    BILLING_DISPUTE = "billing_dispute"
    CUSTOM_SOLUTION_NEEDED = "custom_solution_needed"

class CustomerSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Database connection
mongo_client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"))
db = mongo_client.kasaai_reactivation

class CustomerReactivationTools:
    """Comprehensive customer reactivation voice agent tools."""

    def __init__(self):
        self.freshdesk_api_key = os.getenv("FRESHDESK_API_KEY")
        self.freshdesk_url = os.getenv("FRESHDESK_URL", "https://ailabs-888099064326049059.myfreshworks.com")
        self.kasaai_api_key = os.getenv("KASAAI_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    async def analyze_customer_behavior(
        self,
        customer_id: str,
        include_purchase_history: bool = True,
        analyze_engagement_patterns: bool = True,
        time_period_months: int = 12
    ) -> Dict[str, Any]:
        """
        Analyze customer history, purchase patterns, engagement data, and behavioral signals.

        Args:
            customer_id: Unique customer identifier
            include_purchase_history: Include detailed purchase and transaction history
            analyze_engagement_patterns: Analyze email opens, website visits, app usage, etc.
            time_period_months: Number of months to analyze (default: 12)

        Returns:
            Dict containing comprehensive customer behavior analysis
        """
        try:
            logger.info(f"Analyzing customer behavior for {customer_id}")

            # Get customer data from database
            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            analysis_period = datetime.utcnow() - timedelta(days=time_period_months * 30)

            # Basic customer profile
            behavior_analysis = {
                "customer_id": customer_id,
                "analysis_period_months": time_period_months,
                "customer_since": customer.get("created_date"),
                "last_activity_date": customer.get("last_activity_date"),
                "customer_status": customer.get("status", "inactive"),
                "account_type": customer.get("account_type", "standard")
            }

            if include_purchase_history:
                # Purchase history analysis
                purchases = list(db.purchases.find({
                    "customer_id": customer_id,
                    "purchase_date": {"$gte": analysis_period}
                }).sort("purchase_date", -1))

                total_spent = sum(p.get("amount", 0) for p in purchases)
                avg_order_value = total_spent / len(purchases) if purchases else 0

                behavior_analysis["purchase_history"] = {
                    "total_purchases": len(purchases),
                    "total_spent": total_spent,
                    "average_order_value": avg_order_value,
                    "last_purchase_date": purchases[0].get("purchase_date") if purchases else None,
                    "purchase_frequency": len(purchases) / time_period_months if time_period_months > 0 else 0,
                    "most_purchased_categories": self._get_top_categories(purchases)
                }

            if analyze_engagement_patterns:
                # Engagement pattern analysis
                engagement_data = db.engagement_events.find({
                    "customer_id": customer_id,
                    "event_date": {"$gte": analysis_period}
                })

                engagement_summary = self._analyze_engagement_patterns(list(engagement_data))
                behavior_analysis["engagement_patterns"] = engagement_summary

            # Calculate customer value score
            behavior_analysis["customer_value_score"] = self._calculate_customer_value_score(behavior_analysis)
            behavior_analysis["churn_risk_score"] = self._calculate_churn_risk_score(behavior_analysis)
            behavior_analysis["reactivation_potential"] = self._assess_reactivation_potential(behavior_analysis)

            logger.info(f"Customer behavior analysis completed for {customer_id}")
            return behavior_analysis

        except Exception as e:
            logger.error(f"Error analyzing customer behavior: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def identify_churn_reasons(
        self,
        customer_id: str,
        include_support_history: bool = True,
        analyze_competitor_activity: bool = True
    ) -> Dict[str, Any]:
        """
        Determine likely reasons for customer churn using AI analysis.

        Args:
            customer_id: Customer identifier
            include_support_history: Include support ticket analysis
            analyze_competitor_activity: Check for signs of competitor switching

        Returns:
            Dict containing identified churn reasons and analysis
        """
        try:
            logger.info(f"Identifying churn reasons for {customer_id}")

            churn_analysis = {
                "customer_id": customer_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "identified_reasons": [],
                "confidence_scores": {},
                "risk_factors": []
            }

            # Get customer data
            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            # Analyze inactivity patterns
            last_activity = customer.get("last_activity_date")
            if last_activity:
                days_inactive = (datetime.utcnow() - last_activity).days
                if days_inactive > 90:
                    churn_analysis["identified_reasons"].append("prolonged_inactivity")
                    churn_analysis["confidence_scores"]["prolonged_inactivity"] = min(days_inactive / 180.0, 1.0)

            # Analyze usage decline
            usage_data = list(db.usage_metrics.find({
                "customer_id": customer_id
            }).sort("date", -1).limit(6))

            if len(usage_data) >= 3:
                usage_trend = self._analyze_usage_trend(usage_data)
                if usage_trend["declining"]:
                    churn_analysis["identified_reasons"].append("declining_usage")
                    churn_analysis["confidence_scores"]["declining_usage"] = usage_trend["decline_rate"]

            if include_support_history:
                # Analyze support tickets for frustration indicators
                support_tickets = list(db.support_tickets.find({
                    "customer_id": customer_id,
                    "created_date": {"$gte": datetime.utcnow() - timedelta(days=180)}
                }))

                support_analysis = self._analyze_support_history(support_tickets)
                churn_analysis["support_indicators"] = support_analysis

                if support_analysis["frustration_score"] > 0.6:
                    churn_analysis["identified_reasons"].append("poor_support_experience")
                    churn_analysis["confidence_scores"]["poor_support_experience"] = support_analysis["frustration_score"]

            if analyze_competitor_activity:
                # Check for competitor-related indicators
                competitor_signals = self._detect_competitor_signals(customer_id)
                if competitor_signals["detected"]:
                    churn_analysis["identified_reasons"].append("competitor_switch")
                    churn_analysis["confidence_scores"]["competitor_switch"] = competitor_signals["confidence"]
                    churn_analysis["competitor_indicators"] = competitor_signals["indicators"]

            # Determine primary churn reason
            if churn_analysis["confidence_scores"]:
                primary_reason = max(churn_analysis["confidence_scores"], key=churn_analysis["confidence_scores"].get)
                churn_analysis["primary_churn_reason"] = primary_reason
                churn_analysis["primary_confidence"] = churn_analysis["confidence_scores"][primary_reason]
            else:
                churn_analysis["primary_churn_reason"] = "unknown"
                churn_analysis["primary_confidence"] = 0.0

            # Generate recommendations
            churn_analysis["reactivation_recommendations"] = self._generate_reactivation_recommendations(churn_analysis)

            logger.info(f"Churn analysis completed for {customer_id}")
            return churn_analysis

        except Exception as e:
            logger.error(f"Error identifying churn reasons: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def generate_personalized_offer(
        self,
        customer_id: str,
        customer_value_tier: CustomerValueTier,
        churn_reason: Optional[ChurnReason] = None,
        preferred_offer_type: Optional[OfferType] = None
    ) -> Dict[str, Any]:
        """
        Create customized win-back offers based on customer value and churn reasons.

        Args:
            customer_id: Customer identifier
            customer_value_tier: Customer value classification
            churn_reason: Primary reason for churn
            preferred_offer_type: Type of offer to generate

        Returns:
            Dict containing personalized offer details
        """
        try:
            logger.info(f"Generating personalized offer for {customer_id}")

            offer_data = {
                "customer_id": customer_id,
                "customer_value_tier": customer_value_tier,
                "churn_reason": churn_reason,
                "generated_date": datetime.utcnow().isoformat(),
                "offer_valid_until": (datetime.utcnow() + timedelta(days=14)).isoformat()
            }

            # Get customer preferences and history
            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            # Determine offer parameters based on value tier
            if customer_value_tier == CustomerValueTier.HIGH_VALUE:
                base_discount = 0.30
                offer_duration_days = 30
                include_premium_features = True
                personal_support = True
            elif customer_value_tier == CustomerValueTier.MEDIUM_VALUE:
                base_discount = 0.20
                offer_duration_days = 21
                include_premium_features = False
                personal_support = False
            else:  # STANDARD
                base_discount = 0.15
                offer_duration_days = 14
                include_premium_features = False
                personal_support = False

            # Adjust offer based on churn reason
            if churn_reason == ChurnReason.PRICE_SENSITIVITY:
                base_discount += 0.10
                offer_data["offer_type"] = "discount"
                offer_data["discount_percentage"] = min(base_discount, 0.50)
                offer_data["message"] = f"We understand budget is important. Here's a special {int(offer_data['discount_percentage'] * 100)}% discount to welcome you back!"

            elif churn_reason == ChurnReason.FEATURE_GAPS:
                offer_data["offer_type"] = "feature_access"
                offer_data["discount_percentage"] = base_discount
                offer_data["bonus_features"] = ["advanced_analytics", "priority_support", "custom_integrations"]
                offer_data["message"] = "We've added amazing new features! Try them free for 30 days with your reactivation."

            elif churn_reason == ChurnReason.POOR_EXPERIENCE:
                offer_data["offer_type"] = "service_upgrade"
                offer_data["discount_percentage"] = base_discount
                offer_data["include_personal_onboarding"] = True
                offer_data["dedicated_support"] = True
                offer_data["message"] = "Let us make it right. Enjoy premium support and personal onboarding at no extra cost."

            else:
                # Default offer based on preferred type or value tier
                if preferred_offer_type == OfferType.FREE_TRIAL:
                    offer_data["offer_type"] = "free_trial"
                    offer_data["trial_days"] = offer_duration_days
                    offer_data["message"] = f"Try us again with a free {offer_duration_days}-day trial - no strings attached!"
                else:
                    offer_data["offer_type"] = "discount"
                    offer_data["discount_percentage"] = base_discount
                    offer_data["message"] = f"Welcome back! Enjoy {int(base_discount * 100)}% off your first month."

            # Generate unique offer code
            offer_data["offer_code"] = f"REACTIVATE_{customer_id[:8].upper()}_{datetime.utcnow().strftime('%Y%m')}"

            # Add terms and conditions
            offer_data["terms"] = {
                "valid_until": offer_data["offer_valid_until"],
                "one_time_use": True,
                "requires_minimum_commitment": customer_value_tier != CustomerValueTier.STANDARD,
                "combinable_with_other_offers": False
            }

            # Store offer in database
            db.reactivation_offers.insert_one(offer_data.copy())

            logger.info(f"Personalized offer generated for {customer_id}: {offer_data['offer_code']}")
            return offer_data

        except Exception as e:
            logger.error(f"Error generating personalized offer: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def check_customer_segment(
        self,
        customer_id: str,
        include_clv_calculation: bool = True,
        segment_by_behavior: bool = True
    ) -> Dict[str, Any]:
        """
        Determine customer value tier, lifecycle stage, and segmentation.

        Args:
            customer_id: Customer identifier
            include_clv_calculation: Include Customer Lifetime Value calculation
            segment_by_behavior: Include behavioral segmentation analysis

        Returns:
            Dict containing customer segmentation analysis
        """
        try:
            logger.info(f"Checking customer segment for {customer_id}")

            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            segmentation = {
                "customer_id": customer_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "current_status": customer.get("status", "inactive")
            }

            # Calculate customer metrics
            purchase_history = list(db.purchases.find({"customer_id": customer_id}))
            total_spent = sum(p.get("amount", 0) for p in purchase_history)
            total_orders = len(purchase_history)

            # Determine value tier
            if total_spent >= 10000 or (total_orders >= 20 and total_spent >= 5000):
                value_tier = CustomerValueTier.HIGH_VALUE
            elif total_spent >= 2000 or total_orders >= 10:
                value_tier = CustomerValueTier.MEDIUM_VALUE
            else:
                value_tier = CustomerValueTier.STANDARD

            segmentation["customer_value_tier"] = value_tier
            segmentation["total_spent"] = total_spent
            segmentation["total_orders"] = total_orders
            segmentation["average_order_value"] = total_spent / total_orders if total_orders > 0 else 0

            if include_clv_calculation:
                # Calculate Customer Lifetime Value
                customer_age_days = (datetime.utcnow() - customer.get("created_date", datetime.utcnow())).days
                if customer_age_days > 0:
                    monthly_value = total_spent / (customer_age_days / 30)
                    predicted_lifespan_months = self._predict_customer_lifespan(customer, purchase_history)
                    clv = monthly_value * predicted_lifespan_months
                else:
                    clv = 0

                segmentation["customer_lifetime_value"] = {
                    "calculated_clv": clv,
                    "monthly_value": monthly_value if customer_age_days > 0 else 0,
                    "predicted_lifespan_months": predicted_lifespan_months if customer_age_days > 0 else 0,
                    "customer_age_days": customer_age_days
                }

            if segment_by_behavior:
                # Behavioral segmentation
                engagement_data = list(db.engagement_events.find({"customer_id": customer_id}))
                behavioral_segment = self._determine_behavioral_segment(engagement_data, purchase_history)
                segmentation["behavioral_segment"] = behavioral_segment

            # Lifecycle stage determination
            last_activity = customer.get("last_activity_date", datetime.utcnow())
            days_since_activity = (datetime.utcnow() - last_activity).days

            if days_since_activity <= 7:
                lifecycle_stage = "active"
            elif days_since_activity <= 30:
                lifecycle_stage = "at_risk"
            elif days_since_activity <= 90:
                lifecycle_stage = "dormant"
            else:
                lifecycle_stage = "churned"

            segmentation["lifecycle_stage"] = lifecycle_stage
            segmentation["days_since_last_activity"] = days_since_activity

            # Reactivation priority score
            priority_score = self._calculate_reactivation_priority(segmentation)
            segmentation["reactivation_priority_score"] = priority_score

            logger.info(f"Customer segmentation completed for {customer_id}")
            return segmentation

        except Exception as e:
            logger.error(f"Error checking customer segment: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def schedule_follow_up(
        self,
        customer_id: str,
        follow_up_type: FollowUpType,
        days_from_now: int,
        preferred_time: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule future touchpoints, demos, or check-ins.

        Args:
            customer_id: Customer identifier
            follow_up_type: Type of follow-up to schedule
            days_from_now: Number of days from today to schedule follow-up
            preferred_time: Customer preferred contact time
            notes: Notes about the conversation and next steps

        Returns:
            Dict containing follow-up scheduling confirmation
        """
        try:
            logger.info(f"Scheduling follow-up for {customer_id}")

            follow_up_date = datetime.utcnow() + timedelta(days=days_from_now)

            follow_up_data = {
                "customer_id": customer_id,
                "follow_up_type": follow_up_type,
                "scheduled_date": follow_up_date.isoformat(),
                "preferred_time": preferred_time,
                "notes": notes,
                "status": "scheduled",
                "created_date": datetime.utcnow().isoformat(),
                "priority": self._determine_follow_up_priority(customer_id, follow_up_type)
            }

            # Insert into database
            result = db.follow_ups.insert_one(follow_up_data.copy())
            follow_up_data["follow_up_id"] = str(result.inserted_id)

            # Create calendar event or notification based on type
            if follow_up_type in [FollowUpType.PHONE_CALL, FollowUpType.PRODUCT_DEMO]:
                calendar_result = await self._create_calendar_event(follow_up_data)
                follow_up_data["calendar_event_id"] = calendar_result.get("event_id")

            # Set up automated reminders
            reminder_result = await self._schedule_reminders(follow_up_data)
            follow_up_data["reminders_scheduled"] = reminder_result["scheduled"]

            logger.info(f"Follow-up scheduled for {customer_id}: {follow_up_data['follow_up_id']}")
            return {
                "success": True,
                "follow_up_id": follow_up_data["follow_up_id"],
                "scheduled_date": follow_up_data["scheduled_date"],
                "follow_up_type": follow_up_type,
                "confirmation_message": f"Great! I've scheduled a {follow_up_type.replace('_', ' ')} for {follow_up_date.strftime('%B %d, %Y')}. You'll receive a reminder 24 hours beforehand."
            }

        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def process_reactivation(
        self,
        customer_id: str,
        reactivation_type: ReactivationType,
        offer_code: Optional[str] = None,
        billing_update_required: bool = False,
        immediate_access: bool = True
    ) -> Dict[str, Any]:
        """
        Handle immediate customer reactivation and account restoration.

        Args:
            customer_id: Customer identifier
            reactivation_type: Type of reactivation to process
            offer_code: Promotional offer code to apply
            billing_update_required: Whether billing information needs updating
            immediate_access: Whether to provide immediate access to services

        Returns:
            Dict containing reactivation processing results
        """
        try:
            logger.info(f"Processing reactivation for {customer_id}")

            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            reactivation_data = {
                "customer_id": customer_id,
                "reactivation_type": reactivation_type,
                "offer_code": offer_code,
                "processed_date": datetime.utcnow().isoformat(),
                "billing_update_required": billing_update_required,
                "immediate_access": immediate_access,
                "status": "processing"
            }

            # Validate and apply offer if provided
            if offer_code:
                offer_validation = await self._validate_and_apply_offer(customer_id, offer_code)
                reactivation_data["offer_applied"] = offer_validation["valid"]
                if offer_validation["valid"]:
                    reactivation_data["discount_applied"] = offer_validation["discount"]
                    reactivation_data["offer_details"] = offer_validation["details"]

            # Process reactivation based on type
            if reactivation_type == ReactivationType.ACCOUNT_RESTORATION:
                result = await self._restore_customer_account(customer_id, immediate_access)

            elif reactivation_type == ReactivationType.SUBSCRIPTION_RENEWAL:
                result = await self._renew_customer_subscription(customer_id, offer_code)

            elif reactivation_type == ReactivationType.SERVICE_RESTART:
                result = await self._restart_customer_services(customer_id)

            elif reactivation_type == ReactivationType.PLAN_UPGRADE:
                result = await self._upgrade_customer_plan(customer_id, offer_code)

            else:
                return {"error": "Invalid reactivation type", "customer_id": customer_id}

            reactivation_data.update(result)
            reactivation_data["status"] = "completed" if result["success"] else "failed"

            # Update customer status
            if result["success"]:
                db.customers.update_one(
                    {"customer_id": customer_id},
                    {
                        "$set": {
                            "status": "active",
                            "reactivation_date": datetime.utcnow(),
                            "last_activity_date": datetime.utcnow()
                        }
                    }
                )

            # Store reactivation record
            db.reactivations.insert_one(reactivation_data.copy())

            # Send confirmation communications
            if result["success"]:
                await self._send_reactivation_confirmation(customer_id, reactivation_data)

            logger.info(f"Reactivation processed for {customer_id}: {reactivation_data['status']}")
            return reactivation_data

        except Exception as e:
            logger.error(f"Error processing reactivation: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def update_preferences(
        self,
        customer_id: str,
        communication_frequency: Optional[CommunicationFrequency] = None,
        preferred_channels: Optional[List[str]] = None,
        content_interests: Optional[List[str]] = None,
        opt_out_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update customer communication preferences and settings.

        Args:
            customer_id: Customer identifier
            communication_frequency: Preferred communication frequency
            preferred_channels: Preferred communication channels
            content_interests: Topics and content types of interest
            opt_out_categories: Communication categories to opt out of

        Returns:
            Dict containing preference update confirmation
        """
        try:
            logger.info(f"Updating preferences for {customer_id}")

            customer = db.customers.find_one({"customer_id": customer_id})
            if not customer:
                return {"error": "Customer not found", "customer_id": customer_id}

            # Prepare update data
            preference_updates = {
                "last_updated": datetime.utcnow().isoformat(),
                "updated_by": "voice_agent"
            }

            if communication_frequency:
                preference_updates["communication_frequency"] = communication_frequency

            if preferred_channels:
                preference_updates["preferred_channels"] = preferred_channels

            if content_interests:
                preference_updates["content_interests"] = content_interests

            if opt_out_categories:
                preference_updates["opt_out_categories"] = opt_out_categories

            # Update customer preferences
            result = db.customers.update_one(
                {"customer_id": customer_id},
                {"$set": {"preferences": preference_updates}}
            )

            # Log preference changes
            db.preference_history.insert_one({
                "customer_id": customer_id,
                "changes": preference_updates,
                "change_date": datetime.utcnow().isoformat(),
                "source": "reactivation_call"
            })

            # Update external systems (CRM, email marketing, etc.)
            await self._sync_preferences_to_external_systems(customer_id, preference_updates)

            logger.info(f"Preferences updated for {customer_id}")
            return {
                "success": True,
                "customer_id": customer_id,
                "updated_preferences": preference_updates,
                "confirmation_message": "Perfect! I've updated your communication preferences. You'll only receive the types of updates you're interested in."
            }

        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return {"error": str(e), "customer_id": customer_id}

    async def escalate_to_retention_specialist(
        self,
        customer_id: str,
        escalation_reason: EscalationReason,
        conversation_summary: str,
        customer_sentiment: Optional[CustomerSentiment] = None,
        urgency_level: Optional[UrgencyLevel] = None
    ) -> Dict[str, Any]:
        """
        Transfer complex cases to human retention specialists.

        Args:
            customer_id: Customer identifier
            escalation_reason: Reason for escalation to human agent
            conversation_summary: Summary of conversation and customer concerns
            customer_sentiment: Current customer sentiment
            urgency_level: Urgency level for human follow-up

        Returns:
            Dict containing escalation confirmation and details
        """
        try:
            logger.info(f"Escalating customer {customer_id} to retention specialist")

            escalation_data = {
                "customer_id": customer_id,
                "escalation_reason": escalation_reason,
                "conversation_summary": conversation_summary,
                "customer_sentiment": customer_sentiment or CustomerSentiment.NEUTRAL,
                "urgency_level": urgency_level or UrgencyLevel.MEDIUM,
                "escalated_date": datetime.utcnow().isoformat(),
                "escalated_by": "voice_agent",
                "status": "pending_assignment"
            }

            # Determine specialist assignment based on escalation reason
            specialist_type = self._determine_specialist_type(escalation_reason)
            escalation_data["specialist_type"] = specialist_type

            # Create support ticket in Freshdesk
            ticket_data = await self._create_escalation_ticket(escalation_data)
            escalation_data["support_ticket_id"] = ticket_data["ticket_id"]

            # Store escalation record
            result = db.escalations.insert_one(escalation_data.copy())
            escalation_data["escalation_id"] = str(result.inserted_id)

            # Notify appropriate team
            await self._notify_retention_team(escalation_data)

            # Update customer record
            db.customers.update_one(
                {"customer_id": customer_id},
                {
                    "$set": {
                        "escalation_status": "active",
                        "last_escalation_date": datetime.utcnow(),
                        "assigned_specialist_type": specialist_type
                    }
                }
            )

            logger.info(f"Customer {customer_id} escalated successfully: {escalation_data['escalation_id']}")
            return {
                "success": True,
                "escalation_id": escalation_data["escalation_id"],
                "support_ticket_id": escalation_data["support_ticket_id"],
                "specialist_type": specialist_type,
                "urgency_level": urgency_level,
                "expected_response_time": self._get_expected_response_time(urgency_level),
                "confirmation_message": f"I understand this needs special attention. I've escalated your case to our {specialist_type} team. You can expect to hear from them within {self._get_expected_response_time(urgency_level)}."
            }

        except Exception as e:
            logger.error(f"Error escalating to retention specialist: {e}")
            return {"error": str(e), "customer_id": customer_id}

    # Helper methods

    def _get_top_categories(self, purchases: List[Dict]) -> List[Dict[str, Any]]:
        """Get most purchased product categories."""
        category_counts = {}
        for purchase in purchases:
            category = purchase.get("category", "uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1

        return [{"category": cat, "count": count} for cat, count in
                sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _analyze_engagement_patterns(self, engagement_data: List[Dict]) -> Dict[str, Any]:
        """Analyze customer engagement patterns."""
        if not engagement_data:
            return {"total_events": 0, "engagement_score": 0}

        event_types = {}
        for event in engagement_data:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        total_events = len(engagement_data)
        unique_event_types = len(event_types)

        # Calculate engagement score based on frequency and diversity
        engagement_score = min((total_events * 0.1) + (unique_event_types * 0.2), 1.0)

        return {
            "total_events": total_events,
            "unique_event_types": unique_event_types,
            "event_type_breakdown": event_types,
            "engagement_score": engagement_score,
            "most_common_event": max(event_types, key=event_types.get) if event_types else None
        }

    def _calculate_customer_value_score(self, behavior_analysis: Dict) -> float:
        """Calculate overall customer value score."""
        score = 0.0

        # Purchase history contribution
        if "purchase_history" in behavior_analysis:
            total_spent = behavior_analysis["purchase_history"].get("total_spent", 0)
            score += min(total_spent / 10000, 0.4)  # Max 0.4 for spending

            purchase_frequency = behavior_analysis["purchase_history"].get("purchase_frequency", 0)
            score += min(purchase_frequency / 5, 0.3)  # Max 0.3 for frequency

        # Engagement contribution
        if "engagement_patterns" in behavior_analysis:
            engagement_score = behavior_analysis["engagement_patterns"].get("engagement_score", 0)
            score += engagement_score * 0.3  # Max 0.3 for engagement

        return min(score, 1.0)

    def _calculate_churn_risk_score(self, behavior_analysis: Dict) -> float:
        """Calculate churn risk score."""
        risk_score = 0.0

        # Days since last activity
        last_activity = behavior_analysis.get("last_activity_date")
        if last_activity:
            days_inactive = (datetime.utcnow() - last_activity).days
            risk_score += min(days_inactive / 180, 0.5)  # Max 0.5 for inactivity

        # Declining engagement patterns
        if "engagement_patterns" in behavior_analysis:
            engagement_score = behavior_analysis["engagement_patterns"].get("engagement_score", 0)
            risk_score += (1 - engagement_score) * 0.3

        # Purchase pattern decline
        if "purchase_history" in behavior_analysis:
            purchase_frequency = behavior_analysis["purchase_history"].get("purchase_frequency", 0)
            if purchase_frequency < 0.5:  # Less than once every 2 months
                risk_score += 0.2

        return min(risk_score, 1.0)

    def _assess_reactivation_potential(self, behavior_analysis: Dict) -> Dict[str, Any]:
        """Assess customer's reactivation potential."""
        value_score = behavior_analysis.get("customer_value_score", 0)
        churn_risk = behavior_analysis.get("churn_risk_score", 0)

        # Higher value and recent activity = higher potential
        potential_score = (value_score * 0.7) + ((1 - churn_risk) * 0.3)

        if potential_score >= 0.7:
            potential_level = "high"
        elif potential_score >= 0.4:
            potential_level = "medium"
        else:
            potential_level = "low"

        return {
            "potential_score": potential_score,
            "potential_level": potential_level,
            "recommended_approach": self._get_reactivation_approach(potential_level)
        }

    def _get_reactivation_approach(self, potential_level: str) -> str:
        """Get recommended reactivation approach."""
        approaches = {
            "high": "Aggressive outreach with premium offers and personal attention",
            "medium": "Targeted campaigns with moderate incentives and follow-up",
            "low": "Low-cost automated campaigns with basic offers"
        }
        return approaches.get(potential_level, "Standard approach")

    async def _create_calendar_event(self, follow_up_data: Dict) -> Dict[str, Any]:
        """Create calendar event for follow-up."""
        # Mock implementation - integrate with actual calendar system
        return {"event_id": f"cal_{follow_up_data['customer_id']}_{datetime.utcnow().timestamp()}"}

    async def _schedule_reminders(self, follow_up_data: Dict) -> Dict[str, Any]:
        """Schedule automated reminders."""
        # Mock implementation - integrate with notification system
        return {"scheduled": True, "reminder_count": 2}

# Initialize tools instance
customer_reactivation_tools = CustomerReactivationTools()