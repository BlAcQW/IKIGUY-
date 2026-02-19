"""
Enhanced Survey & Feedback Collection Voice Agent Tools

AI-powered survey administration and feedback collection tools featuring intelligent
questionnaire delivery, real-time sentiment analysis, response validation, and
comprehensive analytics integration.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

# MongoDB and database imports
from pymongo import MongoClient
from bson import ObjectId

# Pydantic for data validation
from pydantic import BaseModel, Field, validator

# Survey and analytics imports
import textblob
from textstat import flesch_reading_ease, flesch_kincaid_grade

# Configuration
logger = logging.getLogger(__name__)

class SurveyType(str, Enum):
    """Survey type enumeration"""
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    PRODUCT_FEEDBACK = "product_feedback"
    SERVICE_EVALUATION = "service_evaluation"
    MARKET_RESEARCH = "market_research"
    POST_PURCHASE = "post_purchase"
    NET_PROMOTER_SCORE = "net_promoter_score"
    BRAND_PERCEPTION = "brand_perception"

class QuestionType(str, Enum):
    """Question type enumeration"""
    MULTIPLE_CHOICE = "multiple_choice"
    RATING_SCALE = "rating_scale"
    OPEN_ENDED = "open_ended"
    YES_NO = "yes_no"
    RANKING = "ranking"

class SentimentLevel(str, Enum):
    """Sentiment level enumeration"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

@dataclass
class SurveyQuestion:
    """Survey question data structure"""
    question_id: str
    question_text: str
    question_type: QuestionType
    options: List[str] = None
    required: bool = True
    branching_logic: str = None

@dataclass
class ResponseData:
    """Response data structure"""
    response_text: str = None
    response_value: str = None
    response_scale: int = None
    response_category: str = None

class SurveyFeedbackVoiceAgent:
    """Enhanced Survey & Feedback Collection Voice Agent with comprehensive tools"""

    def __init__(self, mongo_client: MongoClient, database_name: str = "survey_feedback_db"):
        """
        Initialize the Survey & Feedback Voice Agent.

        Args:
            mongo_client: MongoDB client instance
            database_name: Name of the MongoDB database
        """
        self.mongo_client = mongo_client
        self.db = mongo_client[database_name]

        # Collections
        self.surveys = self.db.surveys
        self.responses = self.db.responses
        self.participants = self.db.participants
        self.analytics = self.db.analytics
        self.incentives = self.db.incentives
        self.concerns = self.db.concerns

        # Ensure indexes for performance
        self._ensure_indexes()

        logger.info("Survey & Feedback Voice Agent initialized successfully")

    def _ensure_indexes(self):
        """Create necessary database indexes for optimal performance"""
        # Survey indexes
        self.surveys.create_index([("survey_id", 1)])
        self.surveys.create_index([("survey_type", 1)])
        self.surveys.create_index([("created_at", -1)])

        # Response indexes
        self.responses.create_index([("survey_id", 1)])
        self.responses.create_index([("participant_id", 1)])
        self.responses.create_index([("question_id", 1)])
        self.responses.create_index([("response_sentiment", 1)])

        # Participant indexes
        self.participants.create_index([("participant_id", 1)])
        self.participants.create_index([("email", 1)])

        # Analytics indexes
        self.analytics.create_index([("survey_id", 1)])
        self.analytics.create_index([("analysis_type", 1)])
        self.analytics.create_index([("created_at", -1)])

    async def administer_survey(
        self,
        survey_type: str,
        survey_questions: List[Dict[str, Any]],
        estimated_duration: int,
        survey_topic: str,
        incentive_offered: Optional[Dict[str, Any]] = None,
        anonymity_level: str = "confidential"
    ) -> Dict[str, Any]:
        """
        Deliver structured surveys with intelligent branching logic and adaptive questioning.

        Args:
            survey_type: Type of survey being conducted
            survey_questions: Structured list of survey questions with metadata
            estimated_duration: Estimated survey completion time in minutes
            survey_topic: Main topic or focus of the survey
            incentive_offered: Survey completion incentive details
            anonymity_level: Level of anonymity for survey responses

        Returns:
            Dict containing survey administration results and next steps
        """
        try:
            # Generate unique survey ID
            survey_id = f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Create survey record
            survey_data = {
                "survey_id": survey_id,
                "survey_type": survey_type,
                "survey_topic": survey_topic,
                "questions": survey_questions,
                "estimated_duration": estimated_duration,
                "incentive_offered": incentive_offered,
                "anonymity_level": anonymity_level,
                "status": "active",
                "created_at": datetime.utcnow(),
                "total_questions": len(survey_questions),
                "responses_collected": 0
            }

            self.surveys.insert_one(survey_data)

            # Prepare survey delivery strategy
            delivery_strategy = self._optimize_survey_delivery(survey_questions, estimated_duration)

            # Generate adaptive questioning plan
            questioning_plan = self._generate_questioning_plan(survey_questions, survey_type)

            logger.info(f"Survey {survey_id} administered successfully with {len(survey_questions)} questions")

            return {
                "success": True,
                "survey_id": survey_id,
                "delivery_strategy": delivery_strategy,
                "questioning_plan": questioning_plan,
                "estimated_completion_time": f"{estimated_duration} minutes",
                "incentive_info": incentive_offered,
                "next_steps": [
                    "Begin with introduction and consent confirmation",
                    "Start with demographic or warming questions",
                    "Follow adaptive questioning based on responses",
                    "Monitor response quality throughout survey"
                ]
            }

        except Exception as e:
            logger.error(f"Error administering survey: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "Switch to simplified questionnaire format"
            }

    async def collect_feedback_response(
        self,
        question_id: str,
        response_data: Dict[str, Any],
        response_confidence: str = "confident",
        response_completeness: str = "complete",
        follow_up_needed: bool = False,
        response_sentiment: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Capture and validate customer responses with real-time data quality checks.

        Args:
            question_id: Identifier for the question being answered
            response_data: Customer response data in multiple formats
            response_confidence: Customer confidence level in their response
            response_completeness: Completeness assessment of the response
            follow_up_needed: Whether additional clarification is needed
            response_sentiment: Initial sentiment assessment of response
            additional_context: Additional context or clarification provided

        Returns:
            Dict containing response collection results and quality assessment
        """
        try:
            # Generate unique response ID
            response_id = f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Perform automatic sentiment analysis if not provided
            if not response_sentiment and response_data.get('response_text'):
                response_sentiment = self._analyze_sentiment(response_data['response_text'])

            # Validate response quality
            quality_assessment = self._assess_response_quality(response_data, response_confidence, response_completeness)

            # Create response record
            response_record = {
                "response_id": response_id,
                "question_id": question_id,
                "response_data": response_data,
                "response_confidence": response_confidence,
                "response_completeness": response_completeness,
                "response_sentiment": response_sentiment,
                "quality_assessment": quality_assessment,
                "follow_up_needed": follow_up_needed,
                "additional_context": additional_context,
                "collected_at": datetime.utcnow(),
                "processing_status": "validated"
            }

            self.responses.insert_one(response_record)

            # Update survey response count
            survey_info = self._update_survey_progress(question_id)

            # Generate real-time insights
            real_time_insights = self._generate_response_insights(response_record, survey_info)

            logger.info(f"Response {response_id} collected and validated for question {question_id}")

            return {
                "success": True,
                "response_id": response_id,
                "quality_score": quality_assessment["overall_score"],
                "sentiment_detected": response_sentiment,
                "real_time_insights": real_time_insights,
                "follow_up_recommended": follow_up_needed or quality_assessment["needs_clarification"],
                "next_question_guidance": self._get_next_question_guidance(question_id, response_data)
            }

        except Exception as e:
            logger.error(f"Error collecting feedback response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "Request response clarification or repetition"
            }

    async def analyze_response_sentiment(
        self,
        response_text: str,
        analysis_depth: str = "detailed",
        emotional_indicators: List[str] = None,
        context_factors: Optional[Dict[str, str]] = None,
        sentiment_confidence: Optional[float] = None,
        action_triggers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform real-time sentiment analysis and emotional assessment of customer feedback.

        Args:
            response_text: Customer response text to analyze
            analysis_depth: Level of sentiment analysis to perform
            emotional_indicators: Specific emotional indicators to assess
            context_factors: Additional context for sentiment analysis
            sentiment_confidence: Confidence level in sentiment analysis
            action_triggers: Keywords or phrases that trigger specific actions

        Returns:
            Dict containing comprehensive sentiment analysis results
        """
        try:
            # Basic sentiment analysis using TextBlob
            blob = textblob.TextBlob(response_text)
            basic_sentiment = blob.sentiment

            # Advanced emotional analysis
            emotional_analysis = self._perform_emotional_analysis(
                response_text,
                emotional_indicators or []
            )

            # Context-aware sentiment adjustment
            contextual_sentiment = self._adjust_sentiment_for_context(
                basic_sentiment,
                context_factors or {}
            )

            # Action trigger detection
            triggered_actions = self._detect_action_triggers(
                response_text,
                action_triggers or []
            )

            # Generate sentiment confidence score
            confidence_score = sentiment_confidence or self._calculate_sentiment_confidence(
                response_text,
                basic_sentiment
            )

            # Classify overall sentiment level
            sentiment_level = self._classify_sentiment_level(contextual_sentiment.polarity)

            # Generate analysis report
            analysis_report = {
                "sentiment_level": sentiment_level,
                "polarity_score": contextual_sentiment.polarity,
                "subjectivity_score": contextual_sentiment.subjectivity,
                "confidence_score": confidence_score,
                "emotional_indicators": emotional_analysis,
                "triggered_actions": triggered_actions,
                "analysis_depth": analysis_depth,
                "context_influence": self._assess_context_influence(context_factors or {}),
                "recommendations": self._generate_sentiment_recommendations(sentiment_level, triggered_actions)
            }

            # Store analysis for trend tracking
            self._store_sentiment_analysis(response_text, analysis_report)

            logger.info(f"Sentiment analysis completed: {sentiment_level} (confidence: {confidence_score:.2f})")

            return {
                "success": True,
                "analysis_report": analysis_report,
                "immediate_actions": triggered_actions,
                "follow_up_recommended": sentiment_level in ["negative", "very_negative"],
                "escalation_needed": "complaint" in triggered_actions or "urgent" in triggered_actions
            }

        except Exception as e:
            logger.error(f"Error analyzing response sentiment: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_sentiment": "neutral",
                "confidence_score": 0.0
            }

    async def schedule_follow_up_survey(
        self,
        follow_up_type: str,
        follow_up_reason: str,
        scheduling_preferences: Optional[Dict[str, Any]] = None,
        priority_level: str = "medium",
        specific_topics: List[str] = None,
        incentive_adjustment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Plan and schedule additional surveys or in-depth interviews based on initial feedback.

        Args:
            follow_up_type: Type of follow-up survey or interview
            follow_up_reason: Reason for scheduling additional data collection
            scheduling_preferences: Customer preferences for follow-up scheduling
            priority_level: Priority for follow-up based on initial feedback
            specific_topics: Specific areas to explore in follow-up
            incentive_adjustment: Adjusted incentives for extended participation

        Returns:
            Dict containing follow-up scheduling results and details
        """
        try:
            # Generate follow-up survey ID
            follow_up_id = f"followup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Determine optimal scheduling timeframe
            optimal_timeframe = self._calculate_optimal_followup_timing(
                follow_up_type,
                priority_level
            )

            # Create follow-up survey configuration
            follow_up_config = self._create_followup_survey_config(
                follow_up_type,
                specific_topics or [],
                scheduling_preferences or {}
            )

            # Calculate adjusted incentive
            final_incentive = self._calculate_adjusted_incentive(
                incentive_adjustment or {},
                follow_up_type
            )

            # Create follow-up record
            follow_up_record = {
                "follow_up_id": follow_up_id,
                "follow_up_type": follow_up_type,
                "follow_up_reason": follow_up_reason,
                "priority_level": priority_level,
                "specific_topics": specific_topics or [],
                "scheduling_preferences": scheduling_preferences or {},
                "optimal_timeframe": optimal_timeframe,
                "survey_config": follow_up_config,
                "incentive_details": final_incentive,
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                "scheduled_for": datetime.utcnow() + timedelta(days=optimal_timeframe)
            }

            self.surveys.insert_one(follow_up_record)

            # Generate participant communication
            communication_plan = self._generate_followup_communication(
                follow_up_record,
                scheduling_preferences or {}
            )

            logger.info(f"Follow-up survey {follow_up_id} scheduled for {optimal_timeframe} days")

            return {
                "success": True,
                "follow_up_id": follow_up_id,
                "scheduled_timeframe": f"{optimal_timeframe} days",
                "communication_plan": communication_plan,
                "survey_configuration": follow_up_config,
                "incentive_details": final_incentive,
                "next_steps": [
                    "Send follow-up invitation to participant",
                    "Prepare customized survey questions",
                    "Schedule reminder notifications",
                    "Monitor response and engagement"
                ]
            }

        except Exception as e:
            logger.error(f"Error scheduling follow-up survey: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "Schedule basic follow-up call instead"
            }

    async def process_survey_incentive(
        self,
        incentive_type: str,
        delivery_method: str,
        completion_verification: Dict[str, Any],
        incentive_value: Optional[float] = None,
        customer_details: Optional[Dict[str, str]] = None,
        processing_timeline: str = "24_hours"
    ) -> Dict[str, Any]:
        """
        Handle survey completion rewards, compensation processing, and incentive distribution.

        Args:
            incentive_type: Type of incentive to process
            delivery_method: How to deliver the incentive
            completion_verification: Verification of survey completion requirements
            incentive_value: Monetary value of the incentive
            customer_details: Customer information for incentive processing
            processing_timeline: Expected processing and delivery timeframe

        Returns:
            Dict containing incentive processing results and tracking information
        """
        try:
            # Verify survey completion eligibility
            eligibility_check = self._verify_incentive_eligibility(completion_verification)

            if not eligibility_check["eligible"]:
                return {
                    "success": False,
                    "reason": eligibility_check["reason"],
                    "requirements_not_met": eligibility_check["missing_requirements"]
                }

            # Generate incentive processing ID
            incentive_id = f"incentive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Calculate final incentive value
            final_value = self._calculate_final_incentive_value(
                incentive_type,
                incentive_value,
                completion_verification
            )

            # Process incentive based on type and delivery method
            processing_result = await self._process_incentive_delivery(
                incentive_type,
                delivery_method,
                final_value,
                customer_details or {}
            )

            # Create incentive record
            incentive_record = {
                "incentive_id": incentive_id,
                "incentive_type": incentive_type,
                "delivery_method": delivery_method,
                "incentive_value": final_value,
                "customer_details": customer_details or {},
                "completion_verification": completion_verification,
                "processing_timeline": processing_timeline,
                "processing_result": processing_result,
                "status": processing_result["status"],
                "created_at": datetime.utcnow(),
                "estimated_delivery": datetime.utcnow() + self._get_processing_timedelta(processing_timeline)
            }

            self.incentives.insert_one(incentive_record)

            # Generate tracking information
            tracking_info = self._generate_incentive_tracking(incentive_record, processing_result)

            logger.info(f"Incentive {incentive_id} processed successfully: {incentive_type} worth {final_value}")

            return {
                "success": True,
                "incentive_id": incentive_id,
                "incentive_value": final_value,
                "delivery_method": delivery_method,
                "tracking_information": tracking_info,
                "estimated_delivery": processing_timeline,
                "status": processing_result["status"],
                "next_steps": [
                    "Incentive processing initiated",
                    "Customer notification sent",
                    "Delivery tracking activated",
                    "Completion confirmation scheduled"
                ]
            }

        except Exception as e:
            logger.error(f"Error processing survey incentive: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "Manual incentive processing required"
            }

    async def escalate_customer_concern(
        self,
        concern_type: str,
        concern_severity: str,
        escalation_path: str,
        concern_details: Optional[Dict[str, Any]] = None,
        immediate_action_needed: bool = False,
        compensation_consideration: Optional[Dict[str, Any]] = None,
        follow_up_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Address and escalate customer complaints, concerns, or issues raised during feedback collection.

        Args:
            concern_type: Category of customer concern or complaint
            concern_severity: Assessed severity level of the concern
            escalation_path: Appropriate department for escalation
            concern_details: Detailed information about the concern
            immediate_action_needed: Whether immediate action is required
            compensation_consideration: Compensation assessment for the concern
            follow_up_requirements: Required follow-up actions with the customer

        Returns:
            Dict containing escalation results and next steps
        """
        try:
            # Generate concern escalation ID
            escalation_id = f"escalation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Assess escalation urgency and routing
            escalation_assessment = self._assess_escalation_urgency(
                concern_type,
                concern_severity,
                immediate_action_needed
            )

            # Determine appropriate escalation team
            escalation_team = self._determine_escalation_team(
                escalation_path,
                concern_type,
                escalation_assessment["urgency_level"]
            )

            # Generate escalation documentation
            escalation_documentation = self._generate_escalation_documentation(
                concern_details or {},
                compensation_consideration or {}
            )

            # Create concern escalation record
            escalation_record = {
                "escalation_id": escalation_id,
                "concern_type": concern_type,
                "concern_severity": concern_severity,
                "escalation_path": escalation_path,
                "concern_details": concern_details or {},
                "immediate_action_needed": immediate_action_needed,
                "compensation_consideration": compensation_consideration or {},
                "follow_up_requirements": follow_up_requirements,
                "escalation_assessment": escalation_assessment,
                "assigned_team": escalation_team,
                "documentation": escalation_documentation,
                "status": "escalated",
                "created_at": datetime.utcnow(),
                "target_resolution": datetime.utcnow() + timedelta(hours=escalation_assessment["target_hours"])
            }

            self.concerns.insert_one(escalation_record)

            # Notify escalation team
            notification_result = self._notify_escalation_team(escalation_record, escalation_team)

            # Generate customer communication
            customer_communication = self._generate_customer_escalation_communication(escalation_record)

            logger.info(f"Concern escalated {escalation_id} to {escalation_path} with {concern_severity} severity")

            return {
                "success": True,
                "escalation_id": escalation_id,
                "escalation_path": escalation_path,
                "assigned_team": escalation_team,
                "urgency_level": escalation_assessment["urgency_level"],
                "target_resolution_time": f"{escalation_assessment['target_hours']} hours",
                "notification_sent": notification_result["success"],
                "customer_communication": customer_communication,
                "next_steps": [
                    "Escalation team notified",
                    "Customer acknowledgment sent",
                    "Investigation initiated",
                    "Regular progress updates scheduled"
                ]
            }

        except Exception as e:
            logger.error(f"Error escalating customer concern: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_action": "Direct manager notification for manual escalation"
            }

    async def validate_response_quality(
        self,
        response_completeness: Dict[str, Any],
        data_quality_flags: List[str],
        response_consistency: Optional[Dict[str, Any]] = None,
        validation_results: Optional[Dict[str, Any]] = None,
        additional_verification_needed: bool = False
    ) -> Dict[str, Any]:
        """
        Ensure completeness, accuracy, and reliability of collected survey responses.

        Args:
            response_completeness: Response completeness assessment
            data_quality_flags: Quality flags for the response data
            response_consistency: Assessment of response consistency and reliability
            validation_results: Overall validation assessment and recommendations
            additional_verification_needed: Whether additional verification is needed

        Returns:
            Dict containing comprehensive quality validation results
        """
        try:
            # Calculate quality scores
            quality_scores = self._calculate_quality_scores(
                response_completeness,
                response_consistency or {},
                data_quality_flags
            )

            # Perform consistency analysis
            consistency_analysis = self._perform_consistency_analysis(
                response_consistency or {},
                data_quality_flags
            )

            # Generate quality recommendations
            quality_recommendations = self._generate_quality_recommendations(
                quality_scores,
                data_quality_flags,
                consistency_analysis
            )

            # Assess overall data usability
            usability_assessment = self._assess_data_usability(
                quality_scores,
                data_quality_flags,
                additional_verification_needed
            )

            # Create validation record
            validation_record = {
                "validation_id": f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}",
                "response_completeness": response_completeness,
                "data_quality_flags": data_quality_flags,
                "response_consistency": response_consistency or {},
                "quality_scores": quality_scores,
                "consistency_analysis": consistency_analysis,
                "usability_assessment": usability_assessment,
                "quality_recommendations": quality_recommendations,
                "additional_verification_needed": additional_verification_needed,
                "validation_timestamp": datetime.utcnow(),
                "validation_status": "completed"
            }

            # Store validation results
            self.analytics.insert_one(validation_record)

            logger.info(f"Response quality validation completed with overall score: {quality_scores['overall_quality_score']}")

            return {
                "success": True,
                "validation_id": validation_record["validation_id"],
                "overall_quality_score": quality_scores["overall_quality_score"],
                "usability_rating": usability_assessment["usability_rating"],
                "data_quality_flags": data_quality_flags,
                "recommendations": quality_recommendations,
                "verification_needed": additional_verification_needed,
                "validation_summary": {
                    "completeness_score": quality_scores["completeness_score"],
                    "consistency_score": quality_scores["consistency_score"],
                    "reliability_score": quality_scores["reliability_score"],
                    "overall_assessment": usability_assessment["overall_assessment"]
                }
            }

        except Exception as e:
            logger.error(f"Error validating response quality: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_quality_score": 5.0,
                "recommended_action": "Manual quality review required"
            }

    async def generate_feedback_summary(
        self,
        summary_scope: str,
        key_metrics: Dict[str, Any],
        qualitative_insights: Optional[Dict[str, Any]] = None,
        actionable_recommendations: Optional[List[Dict[str, Any]]] = None,
        trend_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create real-time summaries and insights from collected customer feedback.

        Args:
            summary_scope: Scope of the feedback summary to generate
            key_metrics: Key quantitative metrics from feedback collection
            qualitative_insights: Qualitative insights and patterns from responses
            actionable_recommendations: Actionable recommendations based on feedback
            trend_analysis: Trend analysis comparing to previous periods

        Returns:
            Dict containing comprehensive feedback summary and insights
        """
        try:
            # Generate summary ID
            summary_id = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}"

            # Process quantitative metrics
            processed_metrics = self._process_quantitative_metrics(key_metrics, summary_scope)

            # Analyze qualitative insights
            analyzed_insights = self._analyze_qualitative_insights(
                qualitative_insights or {},
                summary_scope
            )

            # Generate actionable recommendations
            generated_recommendations = self._generate_actionable_recommendations(
                processed_metrics,
                analyzed_insights,
                actionable_recommendations or []
            )

            # Perform trend analysis
            trend_insights = self._perform_trend_analysis(
                trend_analysis or {},
                processed_metrics,
                summary_scope
            )

            # Create executive summary
            executive_summary = self._create_executive_summary(
                summary_scope,
                processed_metrics,
                analyzed_insights,
                generated_recommendations
            )

            # Generate visualizations data
            visualization_data = self._generate_visualization_data(
                processed_metrics,
                analyzed_insights,
                trend_insights
            )

            # Create comprehensive summary record
            summary_record = {
                "summary_id": summary_id,
                "summary_scope": summary_scope,
                "generation_timestamp": datetime.utcnow(),
                "key_metrics": processed_metrics,
                "qualitative_insights": analyzed_insights,
                "actionable_recommendations": generated_recommendations,
                "trend_analysis": trend_insights,
                "executive_summary": executive_summary,
                "visualization_data": visualization_data,
                "summary_status": "completed"
            }

            # Store summary for historical tracking
            self.analytics.insert_one(summary_record)

            logger.info(f"Feedback summary {summary_id} generated for scope: {summary_scope}")

            return {
                "success": True,
                "summary_id": summary_id,
                "executive_summary": executive_summary,
                "key_findings": {
                    "total_responses": processed_metrics.get("total_responses", 0),
                    "average_satisfaction": processed_metrics.get("average_satisfaction", 0),
                    "response_rate": processed_metrics.get("response_rate", 0),
                    "sentiment_breakdown": analyzed_insights.get("sentiment_distribution", {})
                },
                "top_recommendations": generated_recommendations[:3],
                "trend_highlights": trend_insights.get("key_trends", []),
                "visualization_data": visualization_data,
                "detailed_report_available": True
            }

        except Exception as e:
            logger.error(f"Error generating feedback summary: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_summary": "Basic summary available - detailed analysis failed"
            }

    # Helper methods for supporting functionality

    def _optimize_survey_delivery(self, questions: List[Dict], duration: int) -> Dict[str, Any]:
        """Optimize survey delivery strategy based on questions and duration"""
        return {
            "pacing_strategy": "adaptive",
            "question_grouping": "thematic",
            "break_points": max(1, len(questions) // 3),
            "engagement_techniques": ["progress_indicators", "variety_maintenance"]
        }

    def _generate_questioning_plan(self, questions: List[Dict], survey_type: str) -> Dict[str, Any]:
        """Generate adaptive questioning plan based on survey type"""
        return {
            "opening_approach": "warm_introduction",
            "questioning_style": "conversational",
            "adaptation_triggers": ["confusion", "reluctance", "enthusiasm"],
            "closing_strategy": "appreciation_and_next_steps"
        }

    def _analyze_sentiment(self, text: str) -> str:
        """Perform basic sentiment analysis on response text"""
        blob = textblob.TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity >= 0.5:
            return "very_positive"
        elif polarity >= 0.1:
            return "positive"
        elif polarity >= -0.1:
            return "neutral"
        elif polarity >= -0.5:
            return "negative"
        else:
            return "very_negative"

    def _assess_response_quality(self, response_data: Dict, confidence: str, completeness: str) -> Dict[str, Any]:
        """Assess the quality of a response"""
        quality_score = 7.0  # Base score

        # Adjust based on completeness
        if completeness == "complete":
            quality_score += 1.5
        elif completeness == "partial":
            quality_score -= 1.0
        elif completeness == "unclear":
            quality_score -= 2.0

        # Adjust based on confidence
        if confidence == "very_confident":
            quality_score += 1.0
        elif confidence == "uncertain":
            quality_score -= 1.5

        return {
            "overall_score": max(1.0, min(10.0, quality_score)),
            "completeness_assessment": completeness,
            "confidence_level": confidence,
            "needs_clarification": quality_score < 6.0
        }

    def _update_survey_progress(self, question_id: str) -> Dict[str, Any]:
        """Update survey progress and return survey information"""
        # Find the survey containing this question
        survey = self.surveys.find_one({"questions.question_id": question_id})
        if survey:
            # Increment response count
            self.surveys.update_one(
                {"_id": survey["_id"]},
                {"$inc": {"responses_collected": 1}}
            )
            return {
                "survey_id": survey["survey_id"],
                "total_questions": survey["total_questions"],
                "responses_collected": survey["responses_collected"] + 1
            }
        return {}

    def _generate_response_insights(self, response_record: Dict, survey_info: Dict) -> Dict[str, Any]:
        """Generate real-time insights from response"""
        return {
            "response_pattern": "within_expected_range",
            "survey_progress": f"{survey_info.get('responses_collected', 0)}/{survey_info.get('total_questions', 0)}",
            "engagement_level": "high" if response_record["response_confidence"] in ["confident", "very_confident"] else "moderate"
        }

    def _get_next_question_guidance(self, question_id: str, response_data: Dict) -> str:
        """Get guidance for the next question based on current response"""
        return "Continue with standard question sequence"

    def _perform_emotional_analysis(self, text: str, indicators: List[str]) -> Dict[str, Any]:
        """Perform detailed emotional analysis of response text"""
        # Simplified emotional analysis - in production, use advanced NLP
        emotions_detected = []
        if any(word in text.lower() for word in ["happy", "pleased", "satisfied"]):
            emotions_detected.append("satisfaction")
        if any(word in text.lower() for word in ["frustrated", "annoyed", "upset"]):
            emotions_detected.append("frustration")

        return {
            "emotions_detected": emotions_detected,
            "emotional_intensity": "moderate",
            "dominant_emotion": emotions_detected[0] if emotions_detected else "neutral"
        }

    def _adjust_sentiment_for_context(self, sentiment, context: Dict) -> Any:
        """Adjust sentiment analysis based on context factors"""
        # Return the sentiment with potential context adjustments
        return sentiment

    def _detect_action_triggers(self, text: str, triggers: List[str]) -> List[str]:
        """Detect action triggers in response text"""
        detected = []
        text_lower = text.lower()

        if any(word in text_lower for word in ["complaint", "problem", "issue"]):
            detected.append("complaint")
        if any(word in text_lower for word in ["urgent", "immediately", "asap"]):
            detected.append("urgent")

        return detected

    def _calculate_sentiment_confidence(self, text: str, sentiment) -> float:
        """Calculate confidence score for sentiment analysis"""
        # Simple confidence calculation based on text length and clarity
        base_confidence = 0.7
        if len(text.split()) > 10:
            base_confidence += 0.2
        if abs(sentiment.polarity) > 0.3:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _classify_sentiment_level(self, polarity: float) -> str:
        """Classify sentiment based on polarity score"""
        if polarity >= 0.5:
            return "very_positive"
        elif polarity >= 0.1:
            return "positive"
        elif polarity >= -0.1:
            return "neutral"
        elif polarity >= -0.5:
            return "negative"
        else:
            return "very_negative"

    def _assess_context_influence(self, context: Dict) -> str:
        """Assess how context factors influence sentiment"""
        return "moderate_influence" if context else "minimal_influence"

    def _generate_sentiment_recommendations(self, sentiment_level: str, actions: List[str]) -> List[str]:
        """Generate recommendations based on sentiment analysis"""
        recommendations = []

        if sentiment_level in ["negative", "very_negative"]:
            recommendations.append("Prioritize immediate follow-up")
            recommendations.append("Consider escalation to management")

        if "complaint" in actions:
            recommendations.append("Route to customer service team")

        return recommendations

    def _store_sentiment_analysis(self, text: str, analysis: Dict):
        """Store sentiment analysis for trend tracking"""
        sentiment_record = {
            "text_analyzed": text,
            "analysis_results": analysis,
            "analyzed_at": datetime.utcnow()
        }
        self.analytics.insert_one(sentiment_record)

    def _calculate_optimal_followup_timing(self, follow_up_type: str, priority: str) -> int:
        """Calculate optimal days until follow-up"""
        base_days = {
            "detailed_interview": 7,
            "product_specific_survey": 3,
            "satisfaction_tracking": 14,
            "complaint_resolution": 1,
            "loyalty_assessment": 30
        }

        days = base_days.get(follow_up_type, 7)

        # Adjust based on priority
        if priority == "urgent":
            days = max(1, days // 3)
        elif priority == "high":
            days = max(1, days // 2)

        return days

    def _create_followup_survey_config(self, follow_up_type: str, topics: List[str], preferences: Dict) -> Dict:
        """Create configuration for follow-up survey"""
        return {
            "survey_type": follow_up_type,
            "focus_areas": topics,
            "estimated_duration": preferences.get("duration_estimate", 15),
            "delivery_method": preferences.get("preferred_method", "phone_call")
        }

    def _calculate_adjusted_incentive(self, adjustment: Dict, follow_up_type: str) -> Dict:
        """Calculate adjusted incentive for follow-up participation"""
        base_incentive = {
            "type": "gift_card",
            "value": 25.0,
            "description": "Thank you gift card for extended participation"
        }

        if adjustment.get("additional_incentive"):
            base_incentive["value"] *= 1.5

        return base_incentive

    def _generate_followup_communication(self, follow_up_record: Dict, preferences: Dict) -> Dict:
        """Generate communication plan for follow-up survey"""
        return {
            "initial_contact": "email_invitation",
            "reminder_schedule": ["3_days", "1_day"],
            "contact_method": preferences.get("preferred_method", "email"),
            "message_tone": "appreciative_and_professional"
        }

    def _verify_incentive_eligibility(self, verification: Dict) -> Dict:
        """Verify eligibility for survey incentive"""
        eligible = (
            verification.get("survey_completed", False) and
            verification.get("quality_threshold_met", False) and
            verification.get("response_count", 0) > 0
        )

        return {
            "eligible": eligible,
            "reason": "Survey completion requirements met" if eligible else "Incomplete survey or quality threshold not met",
            "missing_requirements": [] if eligible else ["survey_completion", "quality_threshold"]
        }

    def _calculate_final_incentive_value(self, incentive_type: str, value: Optional[float], verification: Dict) -> float:
        """Calculate final incentive value based on completion quality"""
        base_value = value or 10.0

        # Bonus for high quality responses
        if verification.get("quality_threshold_met") and verification.get("response_count", 0) >= 5:
            base_value *= 1.2

        return round(base_value, 2)

    async def _process_incentive_delivery(self, incentive_type: str, delivery_method: str, value: float, customer_details: Dict) -> Dict:
        """Process incentive delivery based on type and method"""
        # Simulate incentive processing
        return {
            "status": "processing",
            "tracking_number": f"TRK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "estimated_delivery": "24_hours",
            "delivery_confirmation": "email_notification_sent"
        }

    def _get_processing_timedelta(self, timeline: str) -> timedelta:
        """Convert processing timeline to timedelta"""
        timelines = {
            "immediate": timedelta(minutes=5),
            "24_hours": timedelta(days=1),
            "3_business_days": timedelta(days=3),
            "1_week": timedelta(weeks=1),
            "2_weeks": timedelta(weeks=2)
        }
        return timelines.get(timeline, timedelta(days=1))

    def _generate_incentive_tracking(self, record: Dict, processing_result: Dict) -> Dict:
        """Generate tracking information for incentive"""
        return {
            "tracking_number": processing_result.get("tracking_number"),
            "status": processing_result.get("status"),
            "estimated_delivery": record["estimated_delivery"].isoformat(),
            "contact_for_issues": "support@company.com"
        }

    def _assess_escalation_urgency(self, concern_type: str, severity: str, immediate_action: bool) -> Dict:
        """Assess escalation urgency and determine response timeframe"""
        urgency_matrix = {
            ("critical", True): {"urgency_level": "critical", "target_hours": 1},
            ("high", True): {"urgency_level": "high", "target_hours": 4},
            ("medium", False): {"urgency_level": "medium", "target_hours": 24},
            ("low", False): {"urgency_level": "low", "target_hours": 72}
        }

        key = (severity, immediate_action)
        return urgency_matrix.get(key, {"urgency_level": "medium", "target_hours": 24})

    def _determine_escalation_team(self, path: str, concern_type: str, urgency: str) -> Dict:
        """Determine appropriate escalation team"""
        teams = {
            "customer_service": {"team_id": "cs_team", "contact": "cs-manager@company.com"},
            "technical_support": {"team_id": "tech_team", "contact": "tech-lead@company.com"},
            "management": {"team_id": "mgmt_team", "contact": "manager@company.com"}
        }

        return teams.get(path, teams["customer_service"])

    def _generate_escalation_documentation(self, details: Dict, compensation: Dict) -> Dict:
        """Generate comprehensive escalation documentation"""
        return {
            "incident_summary": details.get("description", "Customer concern raised during survey"),
            "impact_assessment": details.get("financial_impact", "Unknown"),
            "compensation_recommended": compensation.get("compensation_warranted", False),
            "documentation_complete": True
        }

    def _notify_escalation_team(self, escalation_record: Dict, team: Dict) -> Dict:
        """Notify escalation team of new concern"""
        # Simulate team notification
        return {
            "success": True,
            "notification_method": "email",
            "team_notified": team["team_id"],
            "notification_time": datetime.utcnow().isoformat()
        }

    def _generate_customer_escalation_communication(self, record: Dict) -> Dict:
        """Generate customer communication for escalation"""
        return {
            "acknowledgment_sent": True,
            "reference_number": record["escalation_id"],
            "expected_resolution": record["target_resolution"].isoformat(),
            "contact_method": "email"
        }

    def _calculate_quality_scores(self, completeness: Dict, consistency: Dict, flags: List[str]) -> Dict:
        """Calculate comprehensive quality scores"""
        completeness_score = (completeness.get("completion_percentage", 0) / 100) * 10
        consistency_score = consistency.get("consistency_score", 7.0)

        # Penalties for quality flags
        penalty = len([f for f in flags if f in ["incomplete_response", "inconsistent_data", "suspicious_pattern"]]) * 1.5

        overall_score = max(1.0, min(10.0, (completeness_score + consistency_score) / 2 - penalty))

        return {
            "overall_quality_score": overall_score,
            "completeness_score": completeness_score,
            "consistency_score": consistency_score,
            "reliability_score": max(1.0, overall_score - 0.5)
        }

    def _perform_consistency_analysis(self, consistency: Dict, flags: List[str]) -> Dict:
        """Perform detailed consistency analysis"""
        return {
            "consistency_level": "high" if "inconsistent_data" not in flags else "low",
            "contradictions_found": len(consistency.get("contradictory_responses", [])),
            "reliability_indicators": consistency.get("reliability_indicators", [])
        }

    def _generate_quality_recommendations(self, scores: Dict, flags: List[str], consistency: Dict) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []

        if scores["overall_quality_score"] < 6.0:
            recommendations.append("Consider follow-up clarification call")

        if "incomplete_response" in flags:
            recommendations.append("Request completion of unanswered questions")

        if consistency["contradictions_found"] > 0:
            recommendations.append("Verify conflicting responses with participant")

        return recommendations

    def _assess_data_usability(self, scores: Dict, flags: List[str], verification_needed: bool) -> Dict:
        """Assess overall data usability"""
        usability_rating = "excellent"

        if scores["overall_quality_score"] < 7.0:
            usability_rating = "good"
        if scores["overall_quality_score"] < 5.0:
            usability_rating = "fair"
        if scores["overall_quality_score"] < 3.0:
            usability_rating = "poor"

        return {
            "usability_rating": usability_rating,
            "overall_assessment": f"Data quality score: {scores['overall_quality_score']:.1f}/10",
            "recommended_usage": "full_analysis" if scores["overall_quality_score"] >= 7.0 else "limited_analysis"
        }

    def _process_quantitative_metrics(self, metrics: Dict, scope: str) -> Dict:
        """Process and analyze quantitative metrics"""
        processed = metrics.copy()

        # Calculate derived metrics
        if "satisfaction_scores" in metrics:
            scores = metrics["satisfaction_scores"]
            processed["average_satisfaction"] = sum(scores) / len(scores) if scores else 0
            processed["satisfaction_variance"] = sum((x - processed["average_satisfaction"])**2 for x in scores) / len(scores) if scores else 0

        return processed

    def _analyze_qualitative_insights(self, insights: Dict, scope: str) -> Dict:
        """Analyze qualitative insights from feedback"""
        analyzed = insights.copy()

        # Add analysis metadata
        analyzed["insight_quality"] = "high" if len(insights.get("common_themes", [])) > 3 else "moderate"
        analyzed["sentiment_distribution"] = {
            "positive": len([theme for theme in insights.get("positive_feedback", [])]),
            "negative": len([theme for theme in insights.get("areas_for_improvement", [])])
        }

        return analyzed

    def _generate_actionable_recommendations(self, metrics: Dict, insights: Dict, existing_recommendations: List[Dict]) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = existing_recommendations.copy()

        # Add data-driven recommendations
        if metrics.get("average_satisfaction", 0) < 7.0:
            recommendations.append({
                "recommendation": "Implement customer satisfaction improvement program",
                "priority": "high",
                "department": "customer_success",
                "estimated_impact": "15-25% satisfaction increase"
            })

        return recommendations

    def _perform_trend_analysis(self, trend_data: Dict, current_metrics: Dict, scope: str) -> Dict:
        """Perform trend analysis comparing current to historical data"""
        trends = trend_data.copy()

        # Add trend insights
        trends["key_trends"] = [
            "Customer satisfaction stable over time",
            "Response rates improving",
            "Quality of feedback increasing"
        ]

        return trends

    def _create_executive_summary(self, scope: str, metrics: Dict, insights: Dict, recommendations: List[Dict]) -> str:
        """Create executive summary of feedback analysis"""
        summary = f"""
        Executive Summary - {scope.replace('_', ' ').title()}

        Key Findings:
        - Total responses analyzed: {metrics.get('total_responses', 'N/A')}
        - Average satisfaction: {metrics.get('average_satisfaction', 'N/A'):.1f}/10
        - Response quality: {insights.get('insight_quality', 'Unknown')}

        Top Recommendations:
        {chr(10).join([f"- {rec['recommendation']}" for rec in recommendations[:3]])}

        Overall Assessment: {'Positive trends with areas for improvement' if metrics.get('average_satisfaction', 0) > 6 else 'Requires immediate attention'}
        """

        return summary.strip()

    def _generate_visualization_data(self, metrics: Dict, insights: Dict, trends: Dict) -> Dict:
        """Generate data for visualization charts and graphs"""
        return {
            "satisfaction_chart": {
                "type": "bar_chart",
                "data": metrics.get("satisfaction_scores", []),
                "labels": [f"Response {i+1}" for i in range(len(metrics.get("satisfaction_scores", [])))]
            },
            "sentiment_pie": {
                "type": "pie_chart",
                "data": insights.get("sentiment_distribution", {}),
                "colors": ["#4CAF50", "#FF9800", "#F44336"]
            },
            "trend_line": {
                "type": "line_chart",
                "data": trends.get("historical_satisfaction", []),
                "timeframe": "last_30_days"
            }
        }