"""
Product Launch Announcement Voice Agent Tools

Enhanced voice agent tools for product launch campaigns with customer segmentation,
personalized messaging, and comprehensive analytics.
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from pymongo import MongoClient

logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    """Product information for launch announcements."""
    product_id: str
    product_name: str
    description: str
    key_features: List[str]
    pricing: Dict[str, Any]
    availability_date: str
    target_audience: List[str]
    competitive_advantages: List[str]

@dataclass
class CustomerSegment:
    """Customer segment information."""
    segment_name: str
    characteristics: List[str]
    messaging_approach: str
    value_proposition: str
    preferred_channels: List[str]

class ProductLaunchVoiceTools:
    """Voice agent tools for product launch announcements."""

    def __init__(self, db_config: Dict[str, str]):
        """Initialize with database configuration."""
        self.db_config = db_config
        self.client = MongoClient(db_config.get('connection_string'))
        self.db = self.client[db_config.get('database_name', 'kasaai_campaigns')]

        # Collections
        self.products = self.db.products
        self.customers = self.db.customers
        self.launch_campaigns = self.db.launch_campaigns
        self.engagement_analytics = self.db.engagement_analytics

        # Product data cache
        self._product_cache = {}

        logger.info("ProductLaunchVoiceTools initialized successfully")

    def get_product_details(
        self,
        product_id: str,
        customer_segment: str = "general",
        detail_level: str = "overview",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive product information and features.

        Args:
            product_id (str): Product identifier
            customer_segment (str): Customer segment for targeted messaging
            detail_level (str): Level of detail (overview, detailed, technical, competitive)
            focus_areas (List[str], optional): Specific areas to focus on

        Returns:
            Dict[str, Any]: Product information tailored to segment and detail level
        """
        try:
            # Check cache first
            cache_key = f"{product_id}_{customer_segment}_{detail_level}"
            if cache_key in self._product_cache:
                return self._product_cache[cache_key]

            # Retrieve product from database
            product = self.products.find_one({"product_id": product_id})
            if not product:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found",
                    "suggested_action": "Please verify the product ID"
                }

            # Tailor information based on customer segment
            segment_messaging = {
                "early_adopters": {
                    "focus": "innovation and cutting-edge features",
                    "tone": "exciting new technology",
                    "highlights": ["latest_features", "innovation_aspects", "early_access_benefits"]
                },
                "loyal_customers": {
                    "focus": "value and relationship",
                    "tone": "exclusive offering for valued customers",
                    "highlights": ["customer_benefits", "loyalty_rewards", "exclusive_access"]
                },
                "tech_enthusiasts": {
                    "focus": "technical specifications and capabilities",
                    "tone": "technical excellence and performance",
                    "highlights": ["technical_specs", "performance_metrics", "integration_capabilities"]
                },
                "price_conscious": {
                    "focus": "value proposition and ROI",
                    "tone": "smart investment and cost-effective solution",
                    "highlights": ["cost_benefits", "roi_analysis", "competitive_pricing"]
                }
            }

            segment_info = segment_messaging.get(customer_segment, segment_messaging["loyal_customers"])

            # Build response based on detail level
            response = {
                "success": True,
                "product_id": product_id,
                "product_name": product["name"],
                "segment_messaging": segment_info,
                "launch_positioning": product.get("launch_positioning", "Revolutionary new offering")
            }

            if detail_level == "overview":
                response.update({
                    "brief_description": product.get("brief_description", ""),
                    "key_benefits": product.get("key_benefits", [])[:3],
                    "availability": product.get("availability", "Available now"),
                    "starting_price": product.get("pricing", {}).get("starting_price", "Contact for pricing")
                })

            elif detail_level == "detailed":
                response.update({
                    "full_description": product.get("full_description", ""),
                    "key_features": product.get("key_features", []),
                    "benefits": product.get("key_benefits", []),
                    "pricing_tiers": product.get("pricing", {}),
                    "availability_timeline": product.get("availability_timeline", {}),
                    "target_use_cases": product.get("target_use_cases", [])
                })

            elif detail_level == "technical":
                response.update({
                    "technical_specifications": product.get("technical_specs", {}),
                    "system_requirements": product.get("system_requirements", {}),
                    "integration_options": product.get("integration_options", []),
                    "api_capabilities": product.get("api_capabilities", []),
                    "security_features": product.get("security_features", [])
                })

            elif detail_level == "competitive":
                response.update({
                    "competitive_advantages": product.get("competitive_advantages", []),
                    "market_positioning": product.get("market_positioning", ""),
                    "differentiation_points": product.get("differentiation_points", []),
                    "comparison_chart": product.get("comparison_chart", {})
                })

            # Apply focus areas filter if specified
            if focus_areas:
                filtered_response = {"success": True, "product_id": product_id}
                for area in focus_areas:
                    if area in response:
                        filtered_response[area] = response[area]
                response = filtered_response

            # Cache the response
            self._product_cache[cache_key] = response

            # Log successful retrieval
            self.engagement_analytics.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "action": "product_details_retrieved",
                "product_id": product_id,
                "customer_segment": customer_segment,
                "detail_level": detail_level,
                "focus_areas": focus_areas
            })

            return response

        except Exception as e:
            logger.error(f"Error retrieving product details: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to retrieve product details: {str(e)}",
                "suggested_action": "Please try again or contact support"
            }

    def assess_customer_interest(
        self,
        interest_indicators: List[str],
        questions: List[str],
        sentiment_score: float,
        purchase_intent: str
    ) -> Dict[str, Any]:
        """
        Assess and score customer interest level in the new product.

        Args:
            interest_indicators (List[str]): Indicators of customer interest
            questions (List[str]): Questions asked by customer
            sentiment_score (float): Sentiment score from 1-10
            purchase_intent (str): Purchase timeline intent

        Returns:
            Dict[str, Any]: Interest assessment and recommendations
        """
        try:
            # Calculate interest score based on multiple factors
            base_score = sentiment_score

            # Adjust based on interest indicators
            indicator_weights = {
                "asked_for_demo": 2.0,
                "requested_pricing": 1.5,
                "technical_questions": 1.3,
                "comparison_questions": 1.2,
                "availability_inquiry": 1.4,
                "integration_questions": 1.6,
                "security_questions": 1.3,
                "roi_questions": 1.5,
                "timeline_questions": 1.7,
                "budget_discussion": 1.8
            }

            indicator_boost = sum(indicator_weights.get(indicator, 0.5) for indicator in interest_indicators)

            # Adjust based on purchase intent
            intent_multipliers = {
                "immediate": 2.0,
                "short_term": 1.5,
                "long_term": 1.0,
                "unlikely": 0.3
            }

            intent_multiplier = intent_multipliers.get(purchase_intent, 1.0)

            # Calculate final interest score
            final_score = min(10.0, (base_score + indicator_boost) * intent_multiplier)

            # Determine interest level
            if final_score >= 8.5:
                interest_level = "very_high"
                recommendation = "Prioritize immediate follow-up with detailed demo"
            elif final_score >= 7.0:
                interest_level = "high"
                recommendation = "Schedule demo within 24-48 hours"
            elif final_score >= 5.5:
                interest_level = "moderate"
                recommendation = "Continue nurturing with targeted content"
            elif final_score >= 3.0:
                interest_level = "low"
                recommendation = "Add to long-term nurture campaign"
            else:
                interest_level = "very_low"
                recommendation = "Focus on other prospects, minimal follow-up"

            # Analyze question patterns for insights
            question_analysis = self._analyze_questions(questions)

            result = {
                "success": True,
                "interest_score": round(final_score, 2),
                "interest_level": interest_level,
                "recommendation": recommendation,
                "interest_indicators": interest_indicators,
                "purchase_intent": purchase_intent,
                "question_analysis": question_analysis,
                "next_actions": self._generate_next_actions(interest_level, question_analysis),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Log interest assessment
            self.engagement_analytics.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "action": "interest_assessed",
                "interest_score": final_score,
                "interest_level": interest_level,
                "purchase_intent": purchase_intent,
                "indicators_count": len(interest_indicators),
                "questions_count": len(questions)
            })

            return result

        except Exception as e:
            logger.error(f"Error assessing customer interest: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to assess interest: {str(e)}"
            }

    def offer_exclusive_access(
        self,
        access_type: str,
        customer_segment: str,
        validity_period: str = "30 days",
        special_terms: str = ""
    ) -> Dict[str, Any]:
        """
        Offer exclusive early access or special launch benefits.

        Args:
            access_type (str): Type of exclusive access
            customer_segment (str): Customer segment
            validity_period (str): How long the offer is valid
            special_terms (str): Any special terms or conditions

        Returns:
            Dict[str, Any]: Exclusive access offer details
        """
        try:
            # Define access types and benefits
            access_benefits = {
                "early_access": {
                    "title": "Exclusive Early Access",
                    "benefits": [
                        "Access 30 days before general availability",
                        "Priority customer support",
                        "Exclusive early adopter badge",
                        "15% discount on first year"
                    ],
                    "urgency": "Limited to first 100 customers"
                },
                "beta_testing": {
                    "title": "Beta Testing Program",
                    "benefits": [
                        "Free access during beta period",
                        "Direct input into product development",
                        "Special recognition as beta tester",
                        "50% discount upon general release"
                    ],
                    "urgency": "Limited beta testing spots available"
                },
                "exclusive_preview": {
                    "title": "VIP Preview Access",
                    "benefits": [
                        "Private demonstration session",
                        "One-on-one product walkthrough",
                        "Custom implementation consultation",
                        "Priority onboarding"
                    ],
                    "urgency": "Available for next 48 hours"
                },
                "early_bird_pricing": {
                    "title": "Early Bird Special Pricing",
                    "benefits": [
                        "20% discount off regular pricing",
                        "Price lock guarantee for 12 months",
                        "Free premium support for 6 months",
                        "Complimentary training sessions"
                    ],
                    "urgency": "Pricing expires in 7 days"
                }
            }

            offer_details = access_benefits.get(access_type, access_benefits["early_access"])

            # Customize based on customer segment
            segment_customizations = {
                "early_adopters": {
                    "additional_benefit": "Exclusive innovation roadmap preview",
                    "personalization": "As an innovation leader"
                },
                "loyal_customers": {
                    "additional_benefit": "Loyalty bonus credits applied",
                    "personalization": "In appreciation of your continued partnership"
                },
                "tech_enthusiasts": {
                    "additional_benefit": "Technical deep-dive session with engineering team",
                    "personalization": "Given your technical expertise"
                },
                "price_conscious": {
                    "additional_benefit": "Extended payment terms available",
                    "personalization": "With flexible investment options"
                }
            }

            customization = segment_customizations.get(customer_segment, segment_customizations["loyal_customers"])

            # Generate unique offer code
            offer_code = f"LAUNCH_{access_type.upper()}_{datetime.now().strftime('%Y%m%d')}"

            result = {
                "success": True,
                "offer_type": access_type,
                "offer_title": offer_details["title"],
                "benefits": offer_details["benefits"] + [customization["additional_benefit"]],
                "urgency_message": offer_details["urgency"],
                "validity_period": validity_period,
                "special_terms": special_terms,
                "personalization": customization["personalization"],
                "offer_code": offer_code,
                "next_steps": f"Use code {offer_code} to claim this exclusive offer",
                "expiration_date": self._calculate_expiration_date(validity_period),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Log offer presentation
            self.engagement_analytics.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "action": "exclusive_offer_presented",
                "access_type": access_type,
                "customer_segment": customer_segment,
                "offer_code": offer_code,
                "validity_period": validity_period
            })

            return result

        except Exception as e:
            logger.error(f"Error offering exclusive access: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate exclusive offer: {str(e)}"
            }

    def schedule_product_demo(
        self,
        demo_type: str,
        preferred_time: str,
        duration: str = "30 minutes",
        specific_focus: Optional[List[str]] = None,
        attendees: int = 1
    ) -> Dict[str, Any]:
        """
        Schedule a personalized product demonstration or presentation.

        Args:
            demo_type (str): Type of demonstration
            preferred_time (str): Customer's preferred time
            duration (str): Demo duration
            specific_focus (List[str], optional): Areas to focus on
            attendees (int): Number of attendees

        Returns:
            Dict[str, Any]: Demo scheduling information
        """
        try:
            # Define demo types and their characteristics
            demo_configurations = {
                "individual_demo": {
                    "title": "Personalized 1-on-1 Product Demo",
                    "format": "Individual video call",
                    "preparation_time": "15 minutes",
                    "recommended_duration": "30-45 minutes"
                },
                "group_webinar": {
                    "title": "Group Product Webinar",
                    "format": "Multi-participant webinar",
                    "preparation_time": "30 minutes",
                    "recommended_duration": "45-60 minutes"
                },
                "technical_deep_dive": {
                    "title": "Technical Deep Dive Session",
                    "format": "Technical presentation with Q&A",
                    "preparation_time": "45 minutes",
                    "recommended_duration": "60-90 minutes"
                },
                "executive_overview": {
                    "title": "Executive Business Overview",
                    "format": "High-level business presentation",
                    "preparation_time": "20 minutes",
                    "recommended_duration": "30 minutes"
                }
            }

            demo_config = demo_configurations.get(demo_type, demo_configurations["individual_demo"])

            # Generate demo agenda based on focus areas
            agenda = self._generate_demo_agenda(demo_type, specific_focus or [])

            # Calculate suggested time slots
            time_slots = self._generate_time_slots(preferred_time)

            # Generate unique demo ID
            demo_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            result = {
                "success": True,
                "demo_id": demo_id,
                "demo_type": demo_type,
                "demo_title": demo_config["title"],
                "format": demo_config["format"],
                "duration": duration,
                "recommended_duration": demo_config["recommended_duration"],
                "attendees": attendees,
                "agenda": agenda,
                "suggested_time_slots": time_slots,
                "preparation_requirements": [
                    "Stable internet connection",
                    "Computer or tablet with camera",
                    "Quiet environment for discussion"
                ],
                "what_to_expect": [
                    "Live product demonstration",
                    "Interactive Q&A session",
                    "Customized use case discussion",
                    "Next steps planning"
                ],
                "booking_instructions": f"Demo booking reference: {demo_id}",
                "calendar_link": f"https://calendar.kasaai.com/demo/{demo_id}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Store demo request
            self.launch_campaigns.insert_one({
                "demo_id": demo_id,
                "demo_type": demo_type,
                "preferred_time": preferred_time,
                "duration": duration,
                "specific_focus": specific_focus,
                "attendees": attendees,
                "status": "scheduled",
                "created_at": datetime.now(timezone.utc)
            })

            # Log demo scheduling
            self.engagement_analytics.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "action": "demo_scheduled",
                "demo_id": demo_id,
                "demo_type": demo_type,
                "attendees": attendees
            })

            return result

        except Exception as e:
            logger.error(f"Error scheduling demo: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to schedule demo: {str(e)}"
            }

    def collect_launch_feedback(
        self,
        feedback_type: str,
        rating: float,
        comments: str = "",
        suggestions: str = "",
        likely_to_recommend: bool = True
    ) -> Dict[str, Any]:
        """
        Collect customer feedback about the product launch and announcement.

        Args:
            feedback_type (str): Type of feedback
            rating (float): Rating from 1-10
            comments (str): Customer comments
            suggestions (str): Customer suggestions
            likely_to_recommend (bool): Whether customer would recommend

        Returns:
            Dict[str, Any]: Feedback collection confirmation
        """
        try:
            # Generate feedback ID
            feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Store feedback
            feedback_data = {
                "feedback_id": feedback_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "comments": comments,
                "suggestions": suggestions,
                "likely_to_recommend": likely_to_recommend,
                "timestamp": datetime.now(timezone.utc),
                "source": "voice_agent"
            }

            self.engagement_analytics.insert_one(feedback_data)

            # Generate response based on rating
            if rating >= 8:
                response_message = "Thank you for the excellent feedback! We're thrilled you're excited about the launch."
                follow_up = "We'll keep you updated on new features and developments."
            elif rating >= 6:
                response_message = "Thank you for your feedback. We appreciate your honest assessment."
                follow_up = "We'll consider your suggestions for future improvements."
            else:
                response_message = "Thank you for your candid feedback. We take all input seriously."
                follow_up = "We'll reach out to discuss how we can better meet your needs."

            result = {
                "success": True,
                "feedback_id": feedback_id,
                "response_message": response_message,
                "follow_up_action": follow_up,
                "rating_category": self._categorize_rating(rating),
                "next_steps": [
                    "Feedback recorded in our system",
                    "Product team will review suggestions",
                    "Follow-up planned based on rating level"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error collecting feedback: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to collect feedback: {str(e)}"
            }

    def capture_lead_information(
        self,
        lead_quality: str,
        timeframe: str,
        budget: str = "unknown",
        decision_maker: bool = False,
        next_steps: str = ""
    ) -> Dict[str, Any]:
        """
        Capture qualified lead information for product follow-up.

        Args:
            lead_quality (str): Quality level of the lead
            timeframe (str): Purchase timeframe
            budget (str): Budget information
            decision_maker (bool): Whether contact is decision maker
            next_steps (str): Agreed next steps

        Returns:
            Dict[str, Any]: Lead capture confirmation and next actions
        """
        try:
            # Generate lead ID
            lead_id = f"LEAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Calculate lead score
            lead_score = self._calculate_lead_score(lead_quality, timeframe, budget, decision_maker)

            # Determine follow-up strategy
            follow_up_strategy = self._determine_follow_up_strategy(lead_quality, timeframe, lead_score)

            # Store lead information
            lead_data = {
                "lead_id": lead_id,
                "lead_quality": lead_quality,
                "timeframe": timeframe,
                "budget": budget,
                "decision_maker": decision_maker,
                "next_steps": next_steps,
                "lead_score": lead_score,
                "follow_up_strategy": follow_up_strategy,
                "timestamp": datetime.now(timezone.utc),
                "source": "product_launch_campaign"
            }

            self.launch_campaigns.insert_one(lead_data)

            result = {
                "success": True,
                "lead_id": lead_id,
                "lead_score": lead_score,
                "lead_quality": lead_quality,
                "follow_up_strategy": follow_up_strategy,
                "priority_level": self._get_priority_level(lead_score),
                "recommended_actions": follow_up_strategy.get("actions", []),
                "timeline": follow_up_strategy.get("timeline", "Within 24 hours"),
                "assigned_team": follow_up_strategy.get("team", "Sales team"),
                "next_contact_method": follow_up_strategy.get("method", "Email"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Log lead capture
            self.engagement_analytics.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "action": "lead_captured",
                "lead_id": lead_id,
                "lead_quality": lead_quality,
                "lead_score": lead_score,
                "timeframe": timeframe
            })

            return result

        except Exception as e:
            logger.error(f"Error capturing lead: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to capture lead information: {str(e)}"
            }

    def _analyze_questions(self, questions: List[str]) -> Dict[str, Any]:
        """Analyze customer questions for insights."""
        if not questions:
            return {"question_count": 0, "categories": [], "insights": []}

        categories = []
        insights = []

        for question in questions:
            question_lower = question.lower()
            if any(word in question_lower for word in ["price", "cost", "expensive", "budget"]):
                categories.append("pricing")
            if any(word in question_lower for word in ["integrate", "api", "connect", "compatibility"]):
                categories.append("integration")
            if any(word in question_lower for word in ["security", "secure", "privacy", "compliance"]):
                categories.append("security")
            if any(word in question_lower for word in ["demo", "trial", "test", "try"]):
                categories.append("trial_interest")
            if any(word in question_lower for word in ["support", "help", "training", "onboarding"]):
                categories.append("support")

        unique_categories = list(set(categories))

        if "pricing" in unique_categories:
            insights.append("Customer is cost-conscious and needs pricing justification")
        if "integration" in unique_categories:
            insights.append("Customer has technical requirements and existing systems")
        if "trial_interest" in unique_categories:
            insights.append("Customer wants hands-on experience before commitment")

        return {
            "question_count": len(questions),
            "categories": unique_categories,
            "insights": insights
        }

    def _generate_next_actions(self, interest_level: str, question_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommended next actions based on interest level and questions."""
        actions = []

        if interest_level == "very_high":
            actions.extend([
                "Schedule immediate demo call",
                "Prepare custom pricing proposal",
                "Assign dedicated sales representative"
            ])
        elif interest_level == "high":
            actions.extend([
                "Schedule demo within 24 hours",
                "Send detailed product information",
                "Follow up with case studies"
            ])
        elif interest_level == "moderate":
            actions.extend([
                "Add to nurture campaign",
                "Send relevant content",
                "Schedule follow-up in 1 week"
            ])
        else:
            actions.extend([
                "Add to long-term nurture",
                "Monitor engagement",
                "Quarterly check-in"
            ])

        # Add actions based on question categories
        categories = question_analysis.get("categories", [])
        if "pricing" in categories:
            actions.append("Prepare ROI analysis")
        if "integration" in categories:
            actions.append("Schedule technical consultation")
        if "trial_interest" in categories:
            actions.append("Set up trial access")

        return actions

    def _calculate_expiration_date(self, validity_period: str) -> str:
        """Calculate expiration date based on validity period."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)

        if "day" in validity_period:
            days = int(''.join(filter(str.isdigit, validity_period)))
            expiration = now + timedelta(days=days)
        elif "week" in validity_period:
            weeks = int(''.join(filter(str.isdigit, validity_period)))
            expiration = now + timedelta(weeks=weeks)
        elif "month" in validity_period:
            months = int(''.join(filter(str.isdigit, validity_period)))
            expiration = now + timedelta(days=months*30)  # Approximate
        else:
            expiration = now + timedelta(days=30)  # Default 30 days

        return expiration.isoformat()

    def _generate_demo_agenda(self, demo_type: str, focus_areas: List[str]) -> List[str]:
        """Generate demo agenda based on type and focus areas."""
        base_agendas = {
            "individual_demo": [
                "Welcome and introductions",
                "Understanding your specific needs",
                "Live product demonstration",
                "Q&A and discussion",
                "Next steps planning"
            ],
            "group_webinar": [
                "Welcome and agenda overview",
                "Product introduction",
                "Key features demonstration",
                "Use case examples",
                "Q&A session",
                "Follow-up information"
            ],
            "technical_deep_dive": [
                "Technical architecture overview",
                "API and integration capabilities",
                "Security and compliance features",
                "Performance metrics",
                "Technical Q&A",
                "Implementation planning"
            ],
            "executive_overview": [
                "Business value proposition",
                "ROI and cost analysis",
                "Strategic benefits",
                "Implementation timeline",
                "Success metrics",
                "Decision framework"
            ]
        }

        agenda = base_agendas.get(demo_type, base_agendas["individual_demo"])

        # Add focus area specific items
        if "security" in focus_areas:
            agenda.insert(-1, "Security and compliance deep dive")
        if "integration" in focus_areas:
            agenda.insert(-1, "Integration scenarios walkthrough")
        if "roi" in focus_areas:
            agenda.insert(-1, "ROI calculation and business case")

        return agenda

    def _generate_time_slots(self, preferred_time: str) -> List[str]:
        """Generate suggested time slots based on preferred time."""
        # This would typically integrate with a calendar system
        return [
            "Tomorrow 10:00 AM - 10:30 AM",
            "Tomorrow 2:00 PM - 2:30 PM",
            "Day after tomorrow 11:00 AM - 11:30 AM",
            "Day after tomorrow 3:00 PM - 3:30 PM"
        ]

    def _categorize_rating(self, rating: float) -> str:
        """Categorize rating into descriptive categories."""
        if rating >= 9:
            return "exceptional"
        elif rating >= 7:
            return "positive"
        elif rating >= 5:
            return "neutral"
        elif rating >= 3:
            return "negative"
        else:
            return "very_negative"

    def _calculate_lead_score(self, quality: str, timeframe: str, budget: str, decision_maker: bool) -> int:
        """Calculate lead score based on various factors."""
        base_scores = {
            "hot": 80,
            "warm": 60,
            "cold": 30,
            "nurture": 20
        }

        timeframe_scores = {
            "immediate": 20,
            "1_month": 15,
            "3_months": 10,
            "6_months": 5,
            "next_year": 2
        }

        budget_scores = {
            "confirmed": 15,
            "estimated": 10,
            "need_approval": 5,
            "unknown": 0
        }

        score = base_scores.get(quality, 30)
        score += timeframe_scores.get(timeframe, 0)
        score += budget_scores.get(budget, 0)
        score += 10 if decision_maker else 0

        return min(100, score)

    def _determine_follow_up_strategy(self, quality: str, timeframe: str, score: int) -> Dict[str, Any]:
        """Determine follow-up strategy based on lead characteristics."""
        if score >= 80:
            return {
                "actions": ["Immediate sales call", "Custom proposal", "Executive involvement"],
                "timeline": "Within 4 hours",
                "team": "Senior sales team",
                "method": "Phone call"
            }
        elif score >= 60:
            return {
                "actions": ["Schedule demo", "Send case studies", "Pricing discussion"],
                "timeline": "Within 24 hours",
                "team": "Sales team",
                "method": "Email + call"
            }
        else:
            return {
                "actions": ["Add to nurture", "Send content", "Regular check-ins"],
                "timeline": "Within 1 week",
                "team": "Marketing team",
                "method": "Email"
            }

    def _get_priority_level(self, score: int) -> str:
        """Get priority level based on lead score."""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "medium"
        else:
            return "low"