"""
Enhanced Survey & Feedback Collection Service

Comprehensive service for managing AI-powered survey administration, response collection,
sentiment analysis, and feedback analytics with VAPI and N8N integration.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio

from fastapi import HTTPException
from pymongo import MongoClient
from bson import ObjectId

# Import the voice agent tools
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../automations/campaigns/survey-feedback'))
from voice_agent_tools import SurveyFeedbackVoiceAgent, SurveyType, QuestionType, SentimentLevel

# Configuration
logger = logging.getLogger(__name__)

class SurveyStatus(str, Enum):
    """Survey status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ResponseStatus(str, Enum):
    """Response status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SurveyRequest:
    """Survey creation request model"""
    survey_type: str
    survey_topic: str
    participant_emails: List[str]
    estimated_duration: int = 10
    incentive_offered: Optional[Dict[str, Any]] = None
    anonymity_level: str = "confidential"
    custom_questions: Optional[List[Dict[str, Any]]] = None

@dataclass
class ParticipantProfile:
    """Participant profile model"""
    participant_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    consent_given: bool = False
    preferred_contact_method: str = "email"
    survey_history: List[Dict[str, Any]] = None

class EnhancedSurveyFeedbackService:
    """Enhanced Survey & Feedback Collection Service with comprehensive automation"""

    def __init__(self, mongo_client: MongoClient, database_name: str = "kasaai_survey_db"):
        """
        Initialize the Enhanced Survey & Feedback Service.

        Args:
            mongo_client: MongoDB client instance
            database_name: Name of the MongoDB database
        """
        self.mongo_client = mongo_client
        self.db = mongo_client[database_name]

        # Initialize voice agent
        self.voice_agent = SurveyFeedbackVoiceAgent(mongo_client, database_name)

        # Collections
        self.surveys = self.db.surveys
        self.participants = self.db.participants
        self.survey_sessions = self.db.survey_sessions
        self.responses = self.db.responses
        self.analytics = self.db.analytics
        self.incentives = self.db.incentives

        # Ensure indexes
        self._ensure_indexes()

        logger.info("Enhanced Survey & Feedback Service initialized successfully")

    def _ensure_indexes(self):
        """Create necessary database indexes for optimal performance"""
        # Survey indexes
        self.surveys.create_index([("survey_id", 1)], unique=True)
        self.surveys.create_index([("status", 1)])
        self.surveys.create_index([("created_at", -1)])

        # Participant indexes
        self.participants.create_index([("email", 1)], unique=True)
        self.participants.create_index([("participant_id", 1)], unique=True)

        # Response indexes
        self.responses.create_index([("survey_id", 1)])
        self.responses.create_index([("participant_id", 1)])
        self.responses.create_index([("created_at", -1)])

    async def create_survey_campaign(
        self,
        survey_request: SurveyRequest,
        user_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Create a comprehensive survey campaign with VAPI and N8N integration.

        Args:
            survey_request: Survey creation request data
            user_id: ID of the user creating the survey
            organization_id: Organization ID

        Returns:
            Dict containing survey campaign creation results
        """
        try:
            # Generate unique survey ID
            survey_id = f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Validate and process participants
            processed_participants = await self._process_participants(
                survey_request.participant_emails,
                organization_id
            )

            # Generate survey configuration using voice agent
            survey_config = await self.voice_agent.administer_survey(
                survey_type=survey_request.survey_type,
                survey_questions=survey_request.custom_questions or self._generate_default_questions(survey_request.survey_type),
                estimated_duration=survey_request.estimated_duration,
                survey_topic=survey_request.survey_topic,
                incentive_offered=survey_request.incentive_offered,
                anonymity_level=survey_request.anonymity_level
            )

            if not survey_config.get("success"):
                raise HTTPException(status_code=400, detail=f"Failed to configure survey: {survey_config.get('error')}")

            # Create survey record
            survey_data = {
                "survey_id": survey_id,
                "organization_id": organization_id,
                "created_by": user_id,
                "survey_type": survey_request.survey_type,
                "survey_topic": survey_request.survey_topic,
                "status": SurveyStatus.DRAFT,
                "configuration": survey_config,
                "participants": processed_participants,
                "estimated_duration": survey_request.estimated_duration,
                "incentive_offered": survey_request.incentive_offered,
                "anonymity_level": survey_request.anonymity_level,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_participants": len(processed_participants),
                "responses_collected": 0,
                "completion_rate": 0.0
            }

            result = self.surveys.insert_one(survey_data)

            # Initialize survey analytics
            await self._initialize_survey_analytics(survey_id, survey_data)

            logger.info(f"Survey campaign {survey_id} created successfully with {len(processed_participants)} participants")

            return {
                "success": True,
                "survey_id": survey_id,
                "survey_configuration": survey_config,
                "participants_processed": len(processed_participants),
                "estimated_completion_time": f"{survey_request.estimated_duration} minutes per participant",
                "next_steps": [
                    "Review survey configuration",
                    "Activate survey to begin participant outreach",
                    "Monitor response collection and analytics"
                ]
            }

        except Exception as e:
            logger.error(f"Error creating survey campaign: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create survey campaign: {str(e)}")

    async def activate_survey_campaign(
        self,
        survey_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Activate a survey campaign and begin participant outreach.

        Args:
            survey_id: Survey ID to activate
            user_id: ID of the user activating the survey

        Returns:
            Dict containing activation results and campaign status
        """
        try:
            # Retrieve survey
            survey = self.surveys.find_one({"survey_id": survey_id})
            if not survey:
                raise HTTPException(status_code=404, detail="Survey not found")

            if survey["status"] != SurveyStatus.DRAFT:
                raise HTTPException(status_code=400, detail=f"Survey is not in draft status. Current status: {survey['status']}")

            # Update survey status
            self.surveys.update_one(
                {"survey_id": survey_id},
                {
                    "$set": {
                        "status": SurveyStatus.ACTIVE,
                        "activated_at": datetime.utcnow(),
                        "activated_by": user_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Initialize participant outreach sessions
            outreach_results = await self._initiate_participant_outreach(survey)

            # Set up monitoring and analytics
            monitoring_setup = await self._setup_survey_monitoring(survey_id)

            logger.info(f"Survey campaign {survey_id} activated successfully")

            return {
                "success": True,
                "survey_id": survey_id,
                "activation_timestamp": datetime.utcnow().isoformat(),
                "outreach_initiated": outreach_results["sessions_created"],
                "monitoring_active": monitoring_setup["success"],
                "expected_completion": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "tracking_dashboard_url": f"/surveys/{survey_id}/dashboard"
            }

        except Exception as e:
            logger.error(f"Error activating survey campaign: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to activate survey: {str(e)}")

    async def process_survey_response(
        self,
        survey_id: str,
        participant_id: str,
        response_data: Dict[str, Any],
        call_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming survey responses from VAPI calls or other channels.

        Args:
            survey_id: Survey ID
            participant_id: Participant ID
            response_data: Response data from the survey
            call_data: Optional call data from VAPI

        Returns:
            Dict containing response processing results
        """
        try:
            # Validate survey and participant
            survey = self.surveys.find_one({"survey_id": survey_id})
            if not survey:
                raise HTTPException(status_code=404, detail="Survey not found")

            participant = self.participants.find_one({"participant_id": participant_id})
            if not participant:
                raise HTTPException(status_code=404, detail="Participant not found")

            # Process each response using voice agent tools
            processed_responses = []
            overall_sentiment = "neutral"
            quality_score = 5.0

            for question_id, response in response_data.items():
                # Use voice agent to collect and validate response
                collection_result = await self.voice_agent.collect_feedback_response(
                    question_id=question_id,
                    response_data=response,
                    response_confidence=response.get("confidence", "confident"),
                    response_completeness=response.get("completeness", "complete"),
                    follow_up_needed=response.get("needs_followup", False),
                    additional_context=response.get("context")
                )

                if collection_result.get("success"):
                    processed_responses.append(collection_result)

                    # Perform sentiment analysis
                    if response.get("text"):
                        sentiment_result = await self.voice_agent.analyze_response_sentiment(
                            response_text=response["text"],
                            analysis_depth="detailed"
                        )

                        if sentiment_result.get("success"):
                            response["sentiment_analysis"] = sentiment_result["analysis_report"]

            # Generate overall quality assessment
            if processed_responses:
                quality_scores = [r.get("quality_score", 5.0) for r in processed_responses]
                quality_score = sum(quality_scores) / len(quality_scores)

            # Create response record
            response_record = {
                "response_id": f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}",
                "survey_id": survey_id,
                "participant_id": participant_id,
                "responses": processed_responses,
                "call_data": call_data,
                "overall_quality_score": quality_score,
                "overall_sentiment": overall_sentiment,
                "completion_status": "completed" if len(processed_responses) > 0 else "partial",
                "created_at": datetime.utcnow(),
                "processing_status": "validated"
            }

            self.responses.insert_one(response_record)

            # Update survey statistics
            await self._update_survey_statistics(survey_id)

            # Check for incentive eligibility
            incentive_result = None
            if survey.get("incentive_offered") and quality_score >= 6.0:
                incentive_result = await self._process_survey_incentive(
                    survey_id,
                    participant_id,
                    quality_score,
                    len(processed_responses)
                )

            # Generate real-time analytics
            analytics_result = await self._generate_response_analytics(
                survey_id,
                response_record
            )

            logger.info(f"Survey response processed for {participant_id} in survey {survey_id}")

            return {
                "success": True,
                "response_id": response_record["response_id"],
                "quality_score": quality_score,
                "overall_sentiment": overall_sentiment,
                "responses_processed": len(processed_responses),
                "incentive_processed": incentive_result,
                "analytics_updated": analytics_result.get("success", False),
                "completion_status": response_record["completion_status"]
            }

        except Exception as e:
            logger.error(f"Error processing survey response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

    async def get_survey_analytics(
        self,
        survey_id: str,
        include_real_time: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics and insights for a survey campaign.

        Args:
            survey_id: Survey ID
            include_real_time: Whether to include real-time analytics

        Returns:
            Dict containing comprehensive survey analytics
        """
        try:
            # Retrieve survey
            survey = self.surveys.find_one({"survey_id": survey_id})
            if not survey:
                raise HTTPException(status_code=404, detail="Survey not found")

            # Get all responses for this survey
            responses = list(self.responses.find({"survey_id": survey_id}))

            # Generate comprehensive analytics using voice agent
            analytics_summary = await self.voice_agent.generate_feedback_summary(
                summary_scope="campaign_overview",
                key_metrics={
                    "total_participants": survey["total_participants"],
                    "responses_collected": len(responses),
                    "response_rate": len(responses) / survey["total_participants"] * 100 if survey["total_participants"] > 0 else 0,
                    "satisfaction_scores": [r.get("overall_quality_score", 0) for r in responses],
                    "completion_times": [r.get("call_data", {}).get("duration", 0) for r in responses if r.get("call_data")]
                },
                qualitative_insights={
                    "common_themes": self._extract_common_themes(responses),
                    "positive_feedback": self._extract_positive_feedback(responses),
                    "areas_for_improvement": self._extract_improvement_areas(responses)
                }
            )

            # Calculate detailed metrics
            sentiment_distribution = self._calculate_sentiment_distribution(responses)
            response_quality_metrics = self._calculate_quality_metrics(responses)
            completion_analytics = self._calculate_completion_analytics(responses, survey)

            # Generate trend analysis if there are multiple data points
            trend_analysis = None
            if len(responses) > 5:
                trend_analysis = self._analyze_response_trends(responses)

            # Compile comprehensive analytics report
            analytics_report = {
                "survey_overview": {
                    "survey_id": survey_id,
                    "survey_type": survey["survey_type"],
                    "status": survey["status"],
                    "created_at": survey["created_at"].isoformat(),
                    "total_participants": survey["total_participants"],
                    "estimated_duration": survey["estimated_duration"]
                },
                "response_metrics": {
                    "total_responses": len(responses),
                    "response_rate": len(responses) / survey["total_participants"] * 100 if survey["total_participants"] > 0 else 0,
                    "completion_rate": completion_analytics["completion_rate"],
                    "average_quality_score": response_quality_metrics["average_quality"],
                    "average_response_time": completion_analytics["average_response_time"]
                },
                "sentiment_analysis": sentiment_distribution,
                "quality_metrics": response_quality_metrics,
                "insights_summary": analytics_summary.get("key_findings", {}) if analytics_summary.get("success") else {},
                "trend_analysis": trend_analysis,
                "recommendations": self._generate_survey_recommendations(responses, survey),
                "generated_at": datetime.utcnow().isoformat()
            }

            # Store analytics for historical tracking
            if include_real_time:
                self.analytics.insert_one({
                    "survey_id": survey_id,
                    "analytics_report": analytics_report,
                    "report_type": "comprehensive",
                    "generated_at": datetime.utcnow()
                })

            logger.info(f"Analytics generated for survey {survey_id}")

            return {
                "success": True,
                "analytics_report": analytics_report
            }

        except Exception as e:
            logger.error(f"Error generating survey analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

    async def get_survey_dashboard(
        self,
        survey_id: str
    ) -> Dict[str, Any]:
        """
        Get real-time dashboard data for survey monitoring.

        Args:
            survey_id: Survey ID

        Returns:
            Dict containing dashboard data and visualizations
        """
        try:
            # Get analytics
            analytics_result = await self.get_survey_analytics(survey_id, include_real_time=False)

            if not analytics_result.get("success"):
                raise HTTPException(status_code=500, detail="Failed to generate analytics")

            analytics = analytics_result["analytics_report"]

            # Generate dashboard-specific data
            dashboard_data = {
                "overview_cards": {
                    "total_participants": analytics["survey_overview"]["total_participants"],
                    "responses_collected": analytics["response_metrics"]["total_responses"],
                    "response_rate": f"{analytics['response_metrics']['response_rate']:.1f}%",
                    "average_satisfaction": f"{analytics['response_metrics']['average_quality_score']:.1f}/10"
                },
                "charts": {
                    "response_rate_chart": {
                        "type": "progress",
                        "value": analytics["response_metrics"]["response_rate"],
                        "target": 70,
                        "label": "Response Rate Progress"
                    },
                    "sentiment_distribution": {
                        "type": "pie",
                        "data": analytics["sentiment_analysis"],
                        "label": "Response Sentiment Distribution"
                    },
                    "quality_scores": {
                        "type": "histogram",
                        "data": analytics["quality_metrics"].get("score_distribution", []),
                        "label": "Response Quality Distribution"
                    }
                },
                "recent_activity": await self._get_recent_survey_activity(survey_id),
                "alerts": self._generate_survey_alerts(analytics),
                "recommendations": analytics["recommendations"][:3],  # Top 3 recommendations
                "last_updated": datetime.utcnow().isoformat()
            }

            return {
                "success": True,
                "dashboard_data": dashboard_data
            }

        except Exception as e:
            logger.error(f"Error generating survey dashboard: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

    # Helper methods

    async def _process_participants(
        self,
        participant_emails: List[str],
        organization_id: str
    ) -> List[Dict[str, Any]]:
        """Process and validate participant list"""
        processed_participants = []

        for email in participant_emails:
            # Check if participant already exists
            existing_participant = self.participants.find_one({"email": email})

            if existing_participant:
                processed_participants.append({
                    "participant_id": existing_participant["participant_id"],
                    "email": email,
                    "status": "existing"
                })
            else:
                # Create new participant
                participant_id = f"participant_{ObjectId()}"
                participant_data = {
                    "participant_id": participant_id,
                    "email": email,
                    "organization_id": organization_id,
                    "consent_given": True,  # Assume consent for now
                    "preferred_contact_method": "phone",
                    "created_at": datetime.utcnow(),
                    "survey_history": []
                }

                self.participants.insert_one(participant_data)
                processed_participants.append({
                    "participant_id": participant_id,
                    "email": email,
                    "status": "new"
                })

        return processed_participants

    def _generate_default_questions(self, survey_type: str) -> List[Dict[str, Any]]:
        """Generate default questions based on survey type"""
        question_templates = {
            "customer_satisfaction": [
                {
                    "question_id": "satisfaction_overall",
                    "question_text": "On a scale of 1-10, how satisfied are you with our service overall?",
                    "question_type": "rating_scale",
                    "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    "required": True
                },
                {
                    "question_id": "recommendation_likelihood",
                    "question_text": "How likely are you to recommend our service to others?",
                    "question_type": "rating_scale",
                    "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    "required": True
                },
                {
                    "question_id": "additional_feedback",
                    "question_text": "Is there anything else you'd like to share about your experience?",
                    "question_type": "open_ended",
                    "required": False
                }
            ],
            "product_feedback": [
                {
                    "question_id": "product_satisfaction",
                    "question_text": "How satisfied are you with our product?",
                    "question_type": "rating_scale",
                    "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    "required": True
                },
                {
                    "question_id": "feature_importance",
                    "question_text": "Which features are most important to you?",
                    "question_type": "multiple_choice",
                    "options": ["Ease of use", "Performance", "Price", "Customer support", "Features"],
                    "required": True
                }
            ]
        }

        return question_templates.get(survey_type, question_templates["customer_satisfaction"])

    async def _initialize_survey_analytics(self, survey_id: str, survey_data: Dict[str, Any]):
        """Initialize analytics tracking for a new survey"""
        analytics_record = {
            "survey_id": survey_id,
            "analytics_type": "initialization",
            "baseline_metrics": {
                "total_participants": survey_data["total_participants"],
                "estimated_duration": survey_data["estimated_duration"],
                "survey_type": survey_data["survey_type"]
            },
            "created_at": datetime.utcnow()
        }

        self.analytics.insert_one(analytics_record)

    async def _initiate_participant_outreach(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate outreach to all survey participants"""
        sessions_created = 0

        for participant in survey["participants"]:
            # Create survey session
            session_data = {
                "session_id": f"session_{ObjectId()}",
                "survey_id": survey["survey_id"],
                "participant_id": participant["participant_id"],
                "status": "scheduled",
                "scheduled_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }

            self.survey_sessions.insert_one(session_data)
            sessions_created += 1

        return {"sessions_created": sessions_created}

    async def _setup_survey_monitoring(self, survey_id: str) -> Dict[str, Any]:
        """Set up monitoring and alerting for the survey"""
        # In a real implementation, this would set up monitoring dashboards,
        # alerts, and automated reporting
        return {"success": True, "monitoring_active": True}

    async def _update_survey_statistics(self, survey_id: str):
        """Update survey completion statistics"""
        response_count = self.responses.count_documents({"survey_id": survey_id})
        survey = self.surveys.find_one({"survey_id": survey_id})

        if survey:
            completion_rate = response_count / survey["total_participants"] * 100 if survey["total_participants"] > 0 else 0

            self.surveys.update_one(
                {"survey_id": survey_id},
                {
                    "$set": {
                        "responses_collected": response_count,
                        "completion_rate": completion_rate,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

    async def _process_survey_incentive(
        self,
        survey_id: str,
        participant_id: str,
        quality_score: float,
        response_count: int
    ) -> Dict[str, Any]:
        """Process incentive for survey completion"""
        completion_verification = {
            "survey_completed": True,
            "quality_threshold_met": quality_score >= 6.0,
            "response_count": response_count
        }

        incentive_result = await self.voice_agent.process_survey_incentive(
            incentive_type="gift_card",
            delivery_method="email",
            completion_verification=completion_verification,
            incentive_value=10.0
        )

        return incentive_result

    async def _generate_response_analytics(
        self,
        survey_id: str,
        response_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate real-time analytics for new response"""
        # Update real-time analytics
        analytics_update = {
            "survey_id": survey_id,
            "response_id": response_record["response_id"],
            "quality_score": response_record["overall_quality_score"],
            "sentiment": response_record["overall_sentiment"],
            "timestamp": datetime.utcnow()
        }

        self.analytics.insert_one(analytics_update)

        return {"success": True, "analytics_updated": True}

    def _extract_common_themes(self, responses: List[Dict]) -> List[str]:
        """Extract common themes from responses"""
        # Simplified theme extraction - in production, use advanced NLP
        themes = ["Service quality", "Product features", "Customer support", "Pricing"]
        return themes[:3]

    def _extract_positive_feedback(self, responses: List[Dict]) -> List[str]:
        """Extract positive feedback items"""
        positive_items = []
        for response in responses:
            if response.get("overall_sentiment") in ["positive", "very_positive"]:
                # Extract text snippets with positive sentiment
                for resp in response.get("responses", []):
                    if resp.get("sentiment_analysis", {}).get("sentiment_level") in ["positive", "very_positive"]:
                        positive_items.append(resp.get("response_text", "")[:100])
        return positive_items[:5]

    def _extract_improvement_areas(self, responses: List[Dict]) -> List[str]:
        """Extract areas for improvement from responses"""
        improvement_areas = []
        for response in responses:
            if response.get("overall_sentiment") in ["negative", "very_negative"]:
                for resp in response.get("responses", []):
                    if resp.get("sentiment_analysis", {}).get("sentiment_level") in ["negative", "very_negative"]:
                        improvement_areas.append(resp.get("response_text", "")[:100])
        return improvement_areas[:5]

    def _calculate_sentiment_distribution(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate sentiment distribution across responses"""
        sentiment_counts = {"very_positive": 0, "positive": 0, "neutral": 0, "negative": 0, "very_negative": 0}

        for response in responses:
            sentiment = response.get("overall_sentiment", "neutral")
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1

        total_responses = len(responses)
        sentiment_percentages = {
            sentiment: (count / total_responses * 100) if total_responses > 0 else 0
            for sentiment, count in sentiment_counts.items()
        }

        return {
            "counts": sentiment_counts,
            "percentages": sentiment_percentages,
            "total_responses": total_responses
        }

    def _calculate_quality_metrics(self, responses: List[Dict]) -> Dict[str, Any]:
        """Calculate response quality metrics"""
        if not responses:
            return {"average_quality": 0, "score_distribution": []}

        quality_scores = [r.get("overall_quality_score", 0) for r in responses]
        average_quality = sum(quality_scores) / len(quality_scores)

        # Create score distribution buckets
        score_distribution = {
            "1-2": len([s for s in quality_scores if 1 <= s < 3]),
            "3-4": len([s for s in quality_scores if 3 <= s < 5]),
            "5-6": len([s for s in quality_scores if 5 <= s < 7]),
            "7-8": len([s for s in quality_scores if 7 <= s < 9]),
            "9-10": len([s for s in quality_scores if 9 <= s <= 10])
        }

        return {
            "average_quality": average_quality,
            "score_distribution": score_distribution,
            "highest_score": max(quality_scores),
            "lowest_score": min(quality_scores)
        }

    def _calculate_completion_analytics(self, responses: List[Dict], survey: Dict) -> Dict[str, Any]:
        """Calculate completion and timing analytics"""
        completed_responses = [r for r in responses if r.get("completion_status") == "completed"]
        completion_rate = len(completed_responses) / survey["total_participants"] * 100 if survey["total_participants"] > 0 else 0

        # Calculate average response time from call data
        response_times = []
        for response in responses:
            call_data = response.get("call_data", {})
            if call_data.get("duration"):
                response_times.append(call_data["duration"])

        average_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "completion_rate": completion_rate,
            "average_response_time": average_response_time,
            "completed_responses": len(completed_responses),
            "partial_responses": len(responses) - len(completed_responses)
        }

    def _analyze_response_trends(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in responses over time"""
        # Sort responses by timestamp
        sorted_responses = sorted(responses, key=lambda x: x.get("created_at", datetime.min))

        # Calculate rolling averages
        quality_trend = []
        sentiment_trend = []

        for i, response in enumerate(sorted_responses):
            # Calculate moving average over last 5 responses
            start_idx = max(0, i - 4)
            recent_responses = sorted_responses[start_idx:i+1]

            avg_quality = sum(r.get("overall_quality_score", 0) for r in recent_responses) / len(recent_responses)
            quality_trend.append(avg_quality)

        return {
            "quality_trend": quality_trend,
            "trend_direction": "improving" if len(quality_trend) > 1 and quality_trend[-1] > quality_trend[0] else "stable",
            "data_points": len(quality_trend)
        }

    def _generate_survey_recommendations(self, responses: List[Dict], survey: Dict) -> List[str]:
        """Generate actionable recommendations based on survey results"""
        recommendations = []

        if not responses:
            recommendations.append("Increase participant outreach to improve response rates")
            return recommendations

        # Analyze response quality
        avg_quality = sum(r.get("overall_quality_score", 0) for r in responses) / len(responses)

        if avg_quality < 6.0:
            recommendations.append("Review survey questions for clarity and relevance")

        # Analyze sentiment
        negative_responses = [r for r in responses if r.get("overall_sentiment") in ["negative", "very_negative"]]
        if len(negative_responses) > len(responses) * 0.3:
            recommendations.append("Immediate follow-up required for negative feedback")

        # Analyze completion rate
        completion_rate = survey.get("completion_rate", 0)
        if completion_rate < 50:
            recommendations.append("Optimize survey length and incentives to improve completion rates")

        return recommendations

    async def _get_recent_survey_activity(self, survey_id: str) -> List[Dict[str, Any]]:
        """Get recent activity for the survey"""
        recent_responses = list(
            self.responses.find({"survey_id": survey_id})
            .sort("created_at", -1)
            .limit(10)
        )

        activity = []
        for response in recent_responses:
            activity.append({
                "timestamp": response["created_at"].isoformat(),
                "activity_type": "response_received",
                "participant_id": response["participant_id"],
                "quality_score": response.get("overall_quality_score", 0),
                "sentiment": response.get("overall_sentiment", "neutral")
            })

        return activity

    def _generate_survey_alerts(self, analytics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate alerts based on survey analytics"""
        alerts = []

        response_rate = analytics["response_metrics"]["response_rate"]
        if response_rate < 30:
            alerts.append({
                "type": "warning",
                "message": f"Low response rate: {response_rate:.1f}%",
                "action": "Consider adjusting outreach strategy"
            })

        avg_quality = analytics["response_metrics"]["average_quality_score"]
        if avg_quality < 5.0:
            alerts.append({
                "type": "critical",
                "message": f"Low average quality score: {avg_quality:.1f}/10",
                "action": "Review survey design and participant experience"
            })

        return alerts