"""
Enhanced Lead Nurturing Voice Agent Tools
AI-powered lead nurturing featuring behavioral scoring, qualification assessment,
personalized outreach, and comprehensive sales funnel analytics.
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

class BudgetRange(str, Enum):
    UNDER_1K = "under_1k"
    K_1_10 = "1k_10k"
    K_10_50 = "10k_50k"
    K_50_PLUS = "50k_plus"
    UNKNOWN = "unknown"

class DecisionAuthority(str, Enum):
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    END_USER = "end_user"
    GATEKEEPER = "gatekeeper"
    UNKNOWN = "unknown"

class BusinessNeed(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCLEAR = "unclear"

class PurchaseTimeline(str, Enum):
    IMMEDIATE = "immediate"
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    MONTHS_6 = "6_months"
    NO_TIMELINE = "no_timeline"

class InteractionType(str, Enum):
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    DEMO = "demo"
    MEETING = "meeting"
    FOLLOW_UP = "follow_up"

class LeadSentiment(str, Enum):
    VERY_INTERESTED = "very_interested"
    INTERESTED = "interested"
    NEUTRAL = "neutral"
    SKEPTICAL = "skeptical"
    NOT_INTERESTED = "not_interested"

class LeadTemperature(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

class FollowUpType(str, Enum):
    PRODUCT_DEMO = "product_demo"
    DISCOVERY_CALL = "discovery_call"
    PROPOSAL_MEETING = "proposal_meeting"
    CHECK_IN = "check_in"
    DECISION_CALL = "decision_call"

class ContentType(str, Enum):
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"
    PRODUCT_DEMO = "product_demo"
    PRICING_INFO = "pricing_info"
    ROI_CALCULATOR = "roi_calculator"
    COMPARISON_GUIDE = "comparison_guide"

class DeliveryMethod(str, Enum):
    EMAIL = "email"
    PORTAL_ACCESS = "portal_access"
    CALENDAR_INVITE = "calendar_invite"
    DIRECT_LINK = "direct_link"

class SalesStage(str, Enum):
    NEW_LEAD = "new_lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class TaskType(str, Enum):
    FOLLOW_UP_CALL = "follow_up_call"
    SEND_PROPOSAL = "send_proposal"
    SCHEDULE_DEMO = "schedule_demo"
    SEND_CONTRACT = "send_contract"
    CHECK_DECISION_STATUS = "check_decision_status"

class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class UrgencyLevel(str, Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"

# Database connection
mongo_client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"))
db = mongo_client.kasaai_lead_nurturing

class LeadNurturingTools:
    """Comprehensive lead nurturing voice agent tools."""

    def __init__(self):
        self.freshdesk_api_key = os.getenv("FRESHDESK_API_KEY")
        self.freshdesk_url = os.getenv("FRESHDESK_URL", "https://ailabs-888099064326049059.myfreshworks.com")
        self.kasaai_api_key = os.getenv("KASAAI_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.hubspot_api_key = os.getenv("HUBSPOT_API_KEY")

    async def score_lead_behavior(
        self,
        lead_id: str,
        include_website_activity: bool = True,
        include_email_engagement: bool = True,
        include_social_signals: bool = True,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze lead engagement patterns and behavioral signals to calculate lead score.

        Args:
            lead_id: Unique lead identifier
            include_website_activity: Include website visit tracking and page views
            include_email_engagement: Include email opens, clicks, and response patterns
            include_social_signals: Include social media engagement and company signals
            time_period_days: Number of days to analyze (default: 30)

        Returns:
            Dict containing behavioral analysis and lead score
        """
        try:
            logger.info(f"Scoring lead behavior for {lead_id}")

            # Get lead data from database
            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            analysis_period = datetime.utcnow() - timedelta(days=time_period_days)

            behavior_score = {
                "lead_id": lead_id,
                "analysis_period_days": time_period_days,
                "lead_created": lead.get("created_date"),
                "lead_source": lead.get("source"),
                "company_name": lead.get("company_name"),
                "total_score": 0,
                "score_breakdown": {}
            }

            if include_website_activity:
                # Website activity analysis
                website_activities = list(db.website_activity.find({
                    "lead_id": lead_id,
                    "timestamp": {"$gte": analysis_period}
                }))

                website_score = self._calculate_website_score(website_activities)
                behavior_score["score_breakdown"]["website_activity"] = website_score
                behavior_score["total_score"] += website_score["score"]

            if include_email_engagement:
                # Email engagement analysis
                email_activities = list(db.email_activity.find({
                    "lead_id": lead_id,
                    "timestamp": {"$gte": analysis_period}
                }))

                email_score = self._calculate_email_score(email_activities)
                behavior_score["score_breakdown"]["email_engagement"] = email_score
                behavior_score["total_score"] += email_score["score"]

            if include_social_signals:
                # Social signals analysis
                social_activities = list(db.social_activity.find({
                    "lead_id": lead_id,
                    "timestamp": {"$gte": analysis_period}
                }))

                social_score = self._calculate_social_score(social_activities, lead.get("company_name"))
                behavior_score["score_breakdown"]["social_signals"] = social_score
                behavior_score["total_score"] += social_score["score"]

            # Normalize total score to 0-100 scale
            behavior_score["total_score"] = min(behavior_score["total_score"], 100)

            # Determine lead grade
            behavior_score["lead_grade"] = self._determine_lead_grade(behavior_score["total_score"])
            behavior_score["buying_intent"] = self._assess_buying_intent(behavior_score)
            behavior_score["engagement_trend"] = self._calculate_engagement_trend(lead_id, time_period_days)

            # Store scoring results
            db.lead_scores.update_one(
                {"lead_id": lead_id},
                {"$set": behavior_score.copy()},
                upsert=True
            )

            logger.info(f"Lead behavior scoring completed for {lead_id}: {behavior_score['total_score']}")
            return behavior_score

        except Exception as e:
            logger.error(f"Error scoring lead behavior: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def assess_lead_qualification(
        self,
        lead_id: str,
        budget_range: Optional[BudgetRange] = None,
        decision_authority: Optional[DecisionAuthority] = None,
        business_need: Optional[BusinessNeed] = None,
        purchase_timeline: Optional[PurchaseTimeline] = None,
        pain_points: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate lead qualification using BANT criteria and sales readiness scoring.

        Args:
            lead_id: Lead identifier
            budget_range: Estimated budget range for solution
            decision_authority: Level of decision-making authority
            business_need: Urgency and clarity of business need
            purchase_timeline: Expected purchase or decision timeline
            pain_points: Identified business pain points and challenges

        Returns:
            Dict containing qualification assessment and BANT score
        """
        try:
            logger.info(f"Assessing lead qualification for {lead_id}")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            qualification = {
                "lead_id": lead_id,
                "assessment_date": datetime.utcnow().isoformat(),
                "bant_scores": {},
                "overall_qualification": "unknown",
                "qualification_confidence": 0.0
            }

            # Budget Assessment (0-25 points)
            budget_score = self._assess_budget(budget_range, lead.get("company_size"))
            qualification["bant_scores"]["budget"] = budget_score

            # Authority Assessment (0-25 points)
            authority_score = self._assess_authority(decision_authority, lead.get("job_title"))
            qualification["bant_scores"]["authority"] = authority_score

            # Need Assessment (0-25 points)
            need_score = self._assess_need(business_need, pain_points)
            qualification["bant_scores"]["need"] = need_score

            # Timeline Assessment (0-25 points)
            timeline_score = self._assess_timeline(purchase_timeline)
            qualification["bant_scores"]["timeline"] = timeline_score

            # Calculate total BANT score
            total_bant_score = sum(qualification["bant_scores"].values())
            qualification["total_bant_score"] = total_bant_score

            # Determine qualification level
            if total_bant_score >= 80:
                qualification["overall_qualification"] = "highly_qualified"
                qualification["qualification_confidence"] = 0.9
            elif total_bant_score >= 60:
                qualification["overall_qualification"] = "qualified"
                qualification["qualification_confidence"] = 0.7
            elif total_bant_score >= 40:
                qualification["overall_qualification"] = "partially_qualified"
                qualification["qualification_confidence"] = 0.5
            else:
                qualification["overall_qualification"] = "not_qualified"
                qualification["qualification_confidence"] = 0.3

            # Add specific insights
            qualification["qualification_insights"] = self._generate_qualification_insights(qualification)
            qualification["recommended_actions"] = self._get_qualification_recommendations(qualification)

            # Update lead record
            db.leads.update_one(
                {"lead_id": lead_id},
                {
                    "$set": {
                        "qualification_status": qualification["overall_qualification"],
                        "bant_score": total_bant_score,
                        "qualification_date": datetime.utcnow(),
                        "budget_range": budget_range,
                        "decision_authority": decision_authority,
                        "business_need": business_need,
                        "purchase_timeline": purchase_timeline,
                        "pain_points": pain_points or []
                    }
                }
            )

            logger.info(f"Lead qualification completed for {lead_id}: {qualification['overall_qualification']}")
            return qualification

        except Exception as e:
            logger.error(f"Error assessing lead qualification: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def track_lead_interaction(
        self,
        lead_id: str,
        interaction_type: InteractionType,
        conversation_summary: str,
        lead_sentiment: Optional[LeadSentiment] = None,
        objections_raised: Optional[List[str]] = None,
        next_steps_discussed: Optional[str] = None,
        lead_temperature: Optional[LeadTemperature] = None
    ) -> Dict[str, Any]:
        """
        Log conversation details and outcomes for CRM and follow-up purposes.

        Args:
            lead_id: Lead identifier
            interaction_type: Type of interaction
            conversation_summary: Summary of conversation topics and outcomes
            lead_sentiment: Lead interest level and sentiment
            objections_raised: Any objections or concerns mentioned
            next_steps_discussed: Agreed upon next steps or actions
            lead_temperature: Overall lead temperature assessment

        Returns:
            Dict containing interaction tracking confirmation
        """
        try:
            logger.info(f"Tracking lead interaction for {lead_id}")

            interaction_data = {
                "lead_id": lead_id,
                "interaction_type": interaction_type,
                "interaction_date": datetime.utcnow().isoformat(),
                "conversation_summary": conversation_summary,
                "lead_sentiment": lead_sentiment or LeadSentiment.NEUTRAL,
                "objections_raised": objections_raised or [],
                "next_steps_discussed": next_steps_discussed,
                "lead_temperature": lead_temperature or LeadTemperature.WARM,
                "logged_by": "voice_agent"
            }

            # Calculate interaction quality score
            interaction_data["interaction_quality"] = self._calculate_interaction_quality(interaction_data)

            # Store interaction record
            result = db.lead_interactions.insert_one(interaction_data.copy())
            interaction_data["interaction_id"] = str(result.inserted_id)

            # Update lead's latest interaction data
            lead_updates = {
                "last_interaction_date": datetime.utcnow(),
                "last_interaction_type": interaction_type,
                "current_sentiment": lead_sentiment,
                "current_temperature": lead_temperature,
                "latest_objections": objections_raised or []
            }

            # Update lead temperature history
            if lead_temperature:
                await self._update_lead_temperature_history(lead_id, lead_temperature)

            db.leads.update_one(
                {"lead_id": lead_id},
                {"$set": lead_updates}
            )

            # Create follow-up tasks if needed
            if next_steps_discussed:
                await self._create_automatic_follow_up_tasks(lead_id, next_steps_discussed)

            logger.info(f"Lead interaction tracked for {lead_id}: {interaction_data['interaction_id']}")
            return {
                "success": True,
                "interaction_id": interaction_data["interaction_id"],
                "interaction_quality": interaction_data["interaction_quality"],
                "confirmation_message": "Great! I've logged all the details from our conversation and set up the appropriate follow-up actions."
            }

        except Exception as e:
            logger.error(f"Error tracking lead interaction: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def schedule_follow_up(
        self,
        lead_id: str,
        follow_up_type: FollowUpType,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        duration_minutes: int = 30,
        meeting_objectives: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Schedule demos, meetings, or follow-up conversations.

        Args:
            lead_id: Lead identifier
            follow_up_type: Type of follow-up to schedule
            preferred_date: Lead preferred date for follow-up
            preferred_time: Lead preferred time of day
            duration_minutes: Expected duration of follow-up (default: 30)
            meeting_objectives: Goals and objectives for the follow-up meeting
            attendees: Additional attendees from lead side

        Returns:
            Dict containing follow-up scheduling confirmation
        """
        try:
            logger.info(f"Scheduling follow-up for {lead_id}")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            # Parse preferred date or suggest next available
            if preferred_date:
                try:
                    follow_up_date = datetime.fromisoformat(preferred_date)
                except:
                    follow_up_date = datetime.utcnow() + timedelta(days=3)
            else:
                follow_up_date = datetime.utcnow() + timedelta(days=3)

            follow_up_data = {
                "lead_id": lead_id,
                "follow_up_type": follow_up_type,
                "scheduled_date": follow_up_date.isoformat(),
                "preferred_time": preferred_time,
                "duration_minutes": duration_minutes,
                "meeting_objectives": meeting_objectives,
                "attendees": attendees or [],
                "status": "scheduled",
                "created_date": datetime.utcnow().isoformat(),
                "priority": self._determine_follow_up_priority(lead_id, follow_up_type)
            }

            # Store follow-up record
            result = db.follow_ups.insert_one(follow_up_data.copy())
            follow_up_data["follow_up_id"] = str(result.inserted_id)

            # Create calendar event
            calendar_result = await self._create_calendar_event(follow_up_data, lead)
            follow_up_data["calendar_event_id"] = calendar_result.get("event_id")

            # Update lead status
            await self._update_lead_stage_for_follow_up(lead_id, follow_up_type)

            # Send calendar invitation
            await self._send_calendar_invitation(follow_up_data, lead)

            logger.info(f"Follow-up scheduled for {lead_id}: {follow_up_data['follow_up_id']}")
            return {
                "success": True,
                "follow_up_id": follow_up_data["follow_up_id"],
                "scheduled_date": follow_up_data["scheduled_date"],
                "calendar_event_id": follow_up_data["calendar_event_id"],
                "confirmation_message": f"Perfect! I've scheduled a {follow_up_type.replace('_', ' ')} for {follow_up_date.strftime('%B %d, %Y')} at {preferred_time or 'a convenient time'}. You'll receive a calendar invitation shortly."
            }

        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def send_lead_content(
        self,
        lead_id: str,
        content_type: ContentType,
        industry_specific: bool = False,
        use_case_focus: Optional[str] = None,
        delivery_method: DeliveryMethod = DeliveryMethod.EMAIL,
        personalized_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share relevant resources and materials based on lead interests.

        Args:
            lead_id: Lead identifier
            content_type: Type of content to send
            industry_specific: Send industry-specific content if available
            use_case_focus: Specific use case or business challenge to focus on
            delivery_method: How to deliver the content
            personalized_message: Personalized message to accompany the content

        Returns:
            Dict containing content delivery confirmation
        """
        try:
            logger.info(f"Sending content to lead {lead_id}")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            # Find appropriate content
            content_item = await self._find_relevant_content(
                content_type,
                lead.get("industry"),
                use_case_focus,
                industry_specific
            )

            if not content_item:
                return {"error": "No relevant content found", "content_type": content_type}

            content_delivery = {
                "lead_id": lead_id,
                "content_type": content_type,
                "content_item": content_item,
                "delivery_method": delivery_method,
                "personalized_message": personalized_message,
                "sent_date": datetime.utcnow().isoformat(),
                "industry_specific": industry_specific,
                "use_case_focus": use_case_focus
            }

            # Deliver content based on method
            if delivery_method == DeliveryMethod.EMAIL:
                delivery_result = await self._send_content_via_email(lead, content_delivery)
            elif delivery_method == DeliveryMethod.PORTAL_ACCESS:
                delivery_result = await self._provide_portal_access(lead, content_delivery)
            else:
                delivery_result = await self._send_direct_link(lead, content_delivery)

            content_delivery.update(delivery_result)

            # Store content delivery record
            result = db.content_deliveries.insert_one(content_delivery.copy())
            content_delivery["delivery_id"] = str(result.inserted_id)

            # Track engagement
            await self._setup_content_engagement_tracking(content_delivery)

            logger.info(f"Content sent to lead {lead_id}: {content_delivery['delivery_id']}")
            return {
                "success": True,
                "delivery_id": content_delivery["delivery_id"],
                "content_title": content_item["title"],
                "delivery_method": delivery_method,
                "confirmation_message": f"I've sent you our {content_type.replace('_', ' ')} - '{content_item['title']}'. This should provide valuable insights for {use_case_focus or 'your business needs'}."
            }

        except Exception as e:
            logger.error(f"Error sending lead content: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def update_lead_status(
        self,
        lead_id: str,
        new_stage: SalesStage,
        stage_reason: Optional[str] = None,
        lead_score_update: Optional[int] = None,
        priority_level: Optional[PriorityLevel] = None,
        sales_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Progress leads through sales stages and update CRM status.

        Args:
            lead_id: Lead identifier
            new_stage: New sales stage for the lead
            stage_reason: Reason for stage change
            lead_score_update: Updated lead score (0-100)
            priority_level: Priority level for follow-up
            sales_notes: Additional notes for sales team

        Returns:
            Dict containing status update confirmation
        """
        try:
            logger.info(f"Updating lead status for {lead_id}")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            previous_stage = lead.get("sales_stage", "new_lead")

            # Prepare status update
            status_update = {
                "sales_stage": new_stage,
                "stage_updated_date": datetime.utcnow(),
                "stage_reason": stage_reason,
                "priority_level": priority_level,
                "sales_notes": sales_notes,
                "updated_by": "voice_agent"
            }

            if lead_score_update is not None:
                status_update["lead_score"] = lead_score_update

            # Update lead record
            db.leads.update_one(
                {"lead_id": lead_id},
                {"$set": status_update}
            )

            # Log stage transition
            stage_history = {
                "lead_id": lead_id,
                "previous_stage": previous_stage,
                "new_stage": new_stage,
                "transition_date": datetime.utcnow().isoformat(),
                "reason": stage_reason,
                "automated": True
            }

            db.stage_history.insert_one(stage_history)

            # Update external CRM systems
            await self._sync_lead_status_to_crm(lead_id, status_update)

            # Trigger stage-specific automations
            await self._trigger_stage_automations(lead_id, new_stage, previous_stage)

            logger.info(f"Lead status updated for {lead_id}: {previous_stage} -> {new_stage}")
            return {
                "success": True,
                "previous_stage": previous_stage,
                "new_stage": new_stage,
                "lead_score": lead_score_update,
                "priority_level": priority_level,
                "confirmation_message": f"Lead status updated to {new_stage.replace('_', ' ')}. The sales team has been notified of this progression."
            }

        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def create_lead_task(
        self,
        lead_id: str,
        task_type: TaskType,
        task_description: str,
        assigned_to: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        related_opportunity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create tasks and reminders for sales team follow-up.

        Args:
            lead_id: Lead identifier
            task_type: Type of task to create
            task_description: Detailed task description and context
            assigned_to: Sales team member to assign task to
            due_date: Task due date
            priority: Task priority level
            related_opportunity: Related opportunity or deal ID

        Returns:
            Dict containing task creation confirmation
        """
        try:
            logger.info(f"Creating lead task for {lead_id}")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            # Parse due date or set default
            if due_date:
                try:
                    task_due_date = datetime.fromisoformat(due_date)
                except:
                    task_due_date = datetime.utcnow() + timedelta(days=1)
            else:
                task_due_date = datetime.utcnow() + timedelta(days=1)

            # Auto-assign if not specified
            if not assigned_to:
                assigned_to = await self._get_assigned_sales_rep(lead_id)

            task_data = {
                "lead_id": lead_id,
                "task_type": task_type,
                "task_description": task_description,
                "assigned_to": assigned_to,
                "due_date": task_due_date.isoformat(),
                "priority": priority,
                "related_opportunity": related_opportunity,
                "status": "pending",
                "created_date": datetime.utcnow().isoformat(),
                "created_by": "voice_agent"
            }

            # Store task
            result = db.lead_tasks.insert_one(task_data.copy())
            task_data["task_id"] = str(result.inserted_id)

            # Create CRM task
            crm_task_result = await self._create_crm_task(task_data, lead)
            task_data["crm_task_id"] = crm_task_result.get("task_id")

            # Send notification to assigned rep
            await self._notify_sales_rep(task_data, lead)

            logger.info(f"Lead task created for {lead_id}: {task_data['task_id']}")
            return {
                "success": True,
                "task_id": task_data["task_id"],
                "assigned_to": assigned_to,
                "due_date": task_data["due_date"],
                "priority": priority,
                "confirmation_message": f"I've created a {task_type.replace('_', ' ')} task for {assigned_to}. They'll be notified and can follow up accordingly."
            }

        except Exception as e:
            logger.error(f"Error creating lead task: {e}")
            return {"error": str(e), "lead_id": lead_id}

    async def escalate_to_sales(
        self,
        lead_id: str,
        qualification_summary: str,
        sales_rep_id: Optional[str] = None,
        deal_size_estimate: Optional[float] = None,
        close_probability: Optional[float] = None,
        key_stakeholders: Optional[List[str]] = None,
        recommended_next_steps: Optional[str] = None,
        urgency_level: UrgencyLevel = UrgencyLevel.NORMAL
    ) -> Dict[str, Any]:
        """
        Transfer qualified leads to account executives with complete context.

        Args:
            lead_id: Lead identifier
            qualification_summary: Summary of lead qualification and readiness
            sales_rep_id: Assigned sales representative ID
            deal_size_estimate: Estimated deal size or annual contract value
            close_probability: Estimated probability of closing (0-100%)
            key_stakeholders: Key decision makers and influencers identified
            recommended_next_steps: Recommended approach and next steps for AE
            urgency_level: Urgency for sales follow-up

        Returns:
            Dict containing escalation confirmation and details
        """
        try:
            logger.info(f"Escalating lead {lead_id} to sales team")

            lead = db.leads.find_one({"lead_id": lead_id})
            if not lead:
                return {"error": "Lead not found", "lead_id": lead_id}

            # Auto-assign sales rep if not specified
            if not sales_rep_id:
                sales_rep_id = await self._assign_sales_rep(lead_id, deal_size_estimate)

            escalation_data = {
                "lead_id": lead_id,
                "sales_rep_id": sales_rep_id,
                "qualification_summary": qualification_summary,
                "deal_size_estimate": deal_size_estimate,
                "close_probability": close_probability,
                "key_stakeholders": key_stakeholders or [],
                "recommended_next_steps": recommended_next_steps,
                "urgency_level": urgency_level,
                "escalated_date": datetime.utcnow().isoformat(),
                "escalated_by": "voice_agent"
            }

            # Store escalation record
            result = db.lead_escalations.insert_one(escalation_data.copy())
            escalation_data["escalation_id"] = str(result.inserted_id)

            # Update lead status
            await self.update_lead_status(
                lead_id,
                SalesStage.QUALIFIED,
                "Escalated to sales team after qualification",
                priority_level=PriorityLevel.HIGH
            )

            # Create opportunity in CRM
            opportunity_result = await self._create_sales_opportunity(escalation_data, lead)
            escalation_data["opportunity_id"] = opportunity_result.get("opportunity_id")

            # Notify sales team
            await self._notify_sales_team_escalation(escalation_data, lead)

            # Create handoff tasks
            await self._create_sales_handoff_tasks(escalation_data)

            logger.info(f"Lead {lead_id} escalated to sales: {escalation_data['escalation_id']}")
            return {
                "success": True,
                "escalation_id": escalation_data["escalation_id"],
                "sales_rep_id": sales_rep_id,
                "opportunity_id": escalation_data["opportunity_id"],
                "urgency_level": urgency_level,
                "expected_contact_time": self._get_expected_contact_time(urgency_level),
                "confirmation_message": f"Excellent! I've escalated your information to our sales team. {await self._get_sales_rep_name(sales_rep_id)} will be in touch within {self._get_expected_contact_time(urgency_level)} to discuss next steps."
            }

        except Exception as e:
            logger.error(f"Error escalating to sales: {e}")
            return {"error": str(e), "lead_id": lead_id}

    # Helper methods for scoring and analysis

    def _calculate_website_score(self, activities: List[Dict]) -> Dict[str, Any]:
        """Calculate website engagement score."""
        if not activities:
            return {"score": 0, "page_views": 0, "time_on_site": 0}

        page_views = len(activities)
        unique_pages = len(set(a.get("page_url", "") for a in activities))
        total_time = sum(a.get("time_on_page", 0) for a in activities)

        # Score calculation: page views (40%) + unique pages (30%) + time (30%)
        score = min((page_views * 2) + (unique_pages * 3) + (total_time / 60 * 2), 30)

        return {
            "score": score,
            "page_views": page_views,
            "unique_pages": unique_pages,
            "total_time_minutes": total_time / 60,
            "high_value_pages": [a.get("page_url") for a in activities if a.get("high_value", False)]
        }

    def _calculate_email_score(self, activities: List[Dict]) -> Dict[str, Any]:
        """Calculate email engagement score."""
        if not activities:
            return {"score": 0, "opens": 0, "clicks": 0}

        opens = len([a for a in activities if a.get("action") == "open"])
        clicks = len([a for a in activities if a.get("action") == "click"])
        replies = len([a for a in activities if a.get("action") == "reply"])

        # Score calculation: opens (20%) + clicks (40%) + replies (40%)
        score = min((opens * 1) + (clicks * 3) + (replies * 5), 25)

        return {
            "score": score,
            "opens": opens,
            "clicks": clicks,
            "replies": replies,
            "engagement_rate": (clicks + replies) / max(opens, 1)
        }

    def _calculate_social_score(self, activities: List[Dict], company_name: Optional[str]) -> Dict[str, Any]:
        """Calculate social media engagement score."""
        if not activities:
            return {"score": 0, "mentions": 0, "follows": 0}

        mentions = len([a for a in activities if a.get("action") == "mention"])
        follows = len([a for a in activities if a.get("action") == "follow"])
        shares = len([a for a in activities if a.get("action") == "share"])

        # Score calculation: follows (30%) + mentions (40%) + shares (30%)
        score = min((follows * 3) + (mentions * 4) + (shares * 3), 15)

        return {
            "score": score,
            "mentions": mentions,
            "follows": follows,
            "shares": shares,
            "platforms": list(set(a.get("platform", "") for a in activities))
        }

# Initialize tools instance
lead_nurturing_tools = LeadNurturingTools()