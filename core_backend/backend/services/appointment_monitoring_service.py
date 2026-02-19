"""
Specialized Appointment Monitoring Service

Extends the automation monitoring service with healthcare-specific
appointment analytics, no-show prediction, and HIPAA-compliant tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import httpx
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field

from .automation_monitoring_service import AutomationMonitoringService
from ..mongo import get_collection

logger = logging.getLogger(__name__)


class AppointmentMetrics(BaseModel):
    """Appointment-specific metrics model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    automation_id: str
    campaign_id: Optional[str] = None
    organization_id: str

    # Appointment details
    appointment_id: str
    patient_id: str
    exam_type: str
    scheduled_date: datetime
    appointment_status: str = Field(..., pattern="^(scheduled|confirmed|completed|cancelled|no_show|rescheduled)$")

    # Scheduling metrics
    booking_channel: str  # vapi, web, phone, etc.
    time_to_book: Optional[float] = None  # seconds from first contact to booking
    reschedule_count: int = Field(default=0, ge=0)

    # Performance metrics
    provider_location: Optional[str] = None
    mobile_exam: bool = False
    exam_duration: Optional[float] = None  # actual exam duration in minutes
    prep_compliance: Optional[float] = None  # percentage of prep instructions followed

    # Prediction metrics
    no_show_risk_score: Optional[float] = Field(None, ge=0, le=1)
    booking_confidence: Optional[float] = Field(None, ge=0, le=1)
    patient_satisfaction: Optional[int] = Field(None, ge=1, le=10)

    # HIPAA compliance
    hipaa_compliant: bool = True
    data_encrypted: bool = True
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NoShowPrediction(BaseModel):
    """No-show prediction model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    appointment_id: str
    patient_id: str
    risk_score: float = Field(ge=0, le=1)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    confidence: float = Field(ge=0, le=1)

    # Prediction factors
    historical_no_show_rate: Optional[float] = Field(None, ge=0, le=1)
    advance_booking_days: Optional[int] = None
    day_of_week: Optional[str] = None
    time_of_day: Optional[str] = None
    weather_impact: Optional[str] = None

    # Recommended actions
    recommended_actions: List[str] = Field(default_factory=list)
    reminder_strategy: Optional[str] = None

    # Tracking
    prediction_accuracy: Optional[bool] = None  # Set after appointment date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AppointmentAnalytics(BaseModel):
    """Aggregated appointment analytics model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    period_start: datetime
    period_end: datetime

    # Scheduling metrics
    total_appointments: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0
    no_show_appointments: int = 0
    rescheduled_appointments: int = 0

    # Performance metrics
    completion_rate: float = Field(ge=0, le=1)
    no_show_rate: float = Field(ge=0, le=1)
    average_booking_time: float = 0.0  # hours
    average_exam_duration: float = 0.0  # minutes

    # Prediction accuracy
    no_show_prediction_accuracy: Optional[float] = Field(None, ge=0, le=1)
    booking_conversion_rate: float = Field(ge=0, le=1)

    # Channel performance
    channel_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Provider metrics
    provider_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AppointmentMonitoringService(AutomationMonitoringService):
    """Specialized monitoring service for medical appointment scheduling."""

    def __init__(self):
        super().__init__()
        self.collection_name = "appointment_metrics"
        self.analytics_collection_name = "appointment_analytics"

    async def record_appointment_metrics(self, appointment_data: Dict[str, Any]) -> str:
        """Record appointment-specific metrics with HIPAA compliance."""
        try:
            # Flatten nested data structure if needed
            flattened_data = self._flatten_appointment_data(appointment_data)

            # Calculate derived metrics
            flattened_data = self._calculate_appointment_metrics(flattened_data)

            # Ensure HIPAA compliance
            flattened_data = self._ensure_hipaa_compliance(flattened_data)

            # Create appointment metrics record
            appointment_metrics = AppointmentMetrics(**flattened_data)

            # Store in database
            collection = get_collection(self.collection_name)
            result = await collection.insert_one(appointment_metrics.model_dump())

            # Update real-time analytics
            await self._update_appointment_analytics(appointment_metrics)

            logger.info(f"Recorded appointment metrics: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error recording appointment metrics: {str(e)}")
            raise

    def _calculate_appointment_metrics(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived appointment metrics."""
        # Calculate time to book if available
        if appointment_data.get("first_contact_time") and appointment_data.get("booking_time"):
            first_contact = datetime.fromisoformat(appointment_data["first_contact_time"])
            booking_time = datetime.fromisoformat(appointment_data["booking_time"])
            appointment_data["time_to_book"] = (booking_time - first_contact).total_seconds()

        # Calculate no-show risk score based on historical data
        appointment_data["no_show_risk_score"] = self._calculate_no_show_risk(appointment_data)

        # Calculate booking confidence
        appointment_data["booking_confidence"] = self._calculate_booking_confidence(appointment_data)

        return appointment_data

    def _calculate_no_show_risk(self, appointment_data: Dict[str, Any]) -> float:
        """Calculate no-show risk score using ML-like factors."""
        risk_score = 0.0

        # Patient history factor (most important)
        no_show_count = appointment_data.get("patient_no_show_count", 0)
        history_count = appointment_data.get("patient_appointment_history_count", 1)
        if history_count > 0:
            no_show_rate = no_show_count / history_count
            risk_score += no_show_rate * 0.6  # Weight heavily

        # Age factor (younger patients higher risk)
        patient_age = appointment_data.get("patient_age", 50)
        if patient_age < 30:
            risk_score += 0.2
        elif patient_age < 50:
            risk_score += 0.1

        # Reschedule history factor
        reschedule_count = appointment_data.get("reschedule_count", 0)
        risk_score += min(reschedule_count * 0.15, 0.3)

        # Exam type factor (more invasive exams higher risk)
        exam_type = appointment_data.get("exam_type", "basic_physical")
        if exam_type in ["stress_test", "full_medical"]:
            risk_score += 0.15
        elif exam_type in ["comprehensive_physical"]:
            risk_score += 0.1

        # Time to appointment factor
        scheduled_date = appointment_data.get("scheduled_date")
        if scheduled_date:
            if isinstance(scheduled_date, str):
                scheduled_dt = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            else:
                scheduled_dt = scheduled_date
            days_ahead = (scheduled_dt - datetime.utcnow()).days
            if days_ahead > 14:
                risk_score += 0.1
            elif days_ahead < 2:
                risk_score += 0.2

        # Booking channel factor
        booking_channel = appointment_data.get("booking_channel", "web")
        if booking_channel == "vapi":
            risk_score -= 0.1  # Voice bookings tend to be more committed

        return min(max(risk_score, 0.0), 1.0)

    def _calculate_booking_confidence(self, appointment_data: Dict[str, Any]) -> float:
        """Calculate confidence score for successful booking completion."""
        confidence = 0.5  # Base confidence

        # VAPI interaction quality
        if appointment_data.get("booking_channel") == "vapi":
            sentiment_score = appointment_data.get("call_sentiment", 0.5)
            confidence += (sentiment_score - 0.5) * 0.4

            call_duration = appointment_data.get("call_duration", 0)
            if call_duration > 300:  # > 5 minutes suggests thorough discussion
                confidence += 0.1

        # Patient verification
        if appointment_data.get("patient_verified"):
            confidence += 0.2

        # Exam type complexity
        exam_type = appointment_data.get("exam_type", "basic_physical")
        if exam_type == "basic_physical":
            confidence += 0.1

        # Mobile vs office exam
        if appointment_data.get("mobile_exam"):
            confidence += 0.15  # Mobile exams have higher completion rates

        return min(max(confidence, 0.0), 1.0)

    def _ensure_hipaa_compliance(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure appointment data is HIPAA compliant."""
        # Remove or hash PII
        if "patient_ssn" in appointment_data:
            del appointment_data["patient_ssn"]

        if "patient_phone" in appointment_data:
            # Keep only last 4 digits for analytics
            phone = appointment_data["patient_phone"]
            appointment_data["patient_phone_masked"] = "***-***-" + phone[-4:] if len(phone) >= 4 else "***-***-****"
            del appointment_data["patient_phone"]

        # Ensure encryption flags
        appointment_data["hipaa_compliant"] = True
        appointment_data["data_encrypted"] = True

        # Add audit trail entry
        audit_entry = {
            "action": "metrics_recorded",
            "timestamp": datetime.utcnow().isoformat(),
            "user": "automation_system",
            "hipaa_compliant": True
        }
        if "audit_trail" not in appointment_data:
            appointment_data["audit_trail"] = []
        appointment_data["audit_trail"].append(audit_entry)

        return appointment_data

    async def _update_appointment_analytics(self, appointment_metrics: AppointmentMetrics):
        """Update real-time appointment analytics."""
        try:
            collection = get_collection(self.analytics_collection_name)

            # Get current period analytics
            today = datetime.utcnow().date()
            period_start = datetime.combine(today, datetime.min.time())
            period_end = datetime.combine(today, datetime.max.time())

            # Update or create analytics record
            await collection.update_one(
                {
                    "organization_id": appointment_metrics.organization_id,
                    "period_start": {"$gte": period_start},
                    "period_end": {"$lte": period_end}
                },
                {
                    "$inc": {
                        "total_appointments": 1,
                        f"{appointment_metrics.appointment_status}_appointments": 1
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error updating appointment analytics: {str(e)}")

    async def get_appointment_metrics(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime,
        appointment_id: Optional[str] = None,
        exam_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AppointmentMetrics]:
        """Retrieve appointment metrics with filtering."""
        try:
            collection = get_collection(self.collection_name)

            # Build query
            query = {
                "organization_id": organization_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if appointment_id:
                query["appointment_id"] = appointment_id

            if exam_type:
                query["exam_type"] = exam_type

            # Execute query
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            results = await cursor.to_list(length=limit)

            return [AppointmentMetrics(**result) for result in results]

        except Exception as e:
            logger.error(f"Error retrieving appointment metrics: {str(e)}")
            return []

    async def get_appointment_analytics(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[AppointmentAnalytics]:
        """Get aggregated appointment analytics for a period."""
        try:
            # Get appointment metrics for the period
            metrics = await self.get_appointment_metrics(organization_id, start_date, end_date, limit=10000)

            if not metrics:
                return None

            # Calculate analytics
            total_appointments = len(metrics)
            completed = len([m for m in metrics if m.appointment_status == "completed"])
            cancelled = len([m for m in metrics if m.appointment_status == "cancelled"])
            no_shows = len([m for m in metrics if m.appointment_status == "no_show"])
            rescheduled = len([m for m in metrics if m.appointment_status == "rescheduled"])

            # Calculate rates
            completion_rate = completed / total_appointments if total_appointments > 0 else 0
            no_show_rate = no_shows / total_appointments if total_appointments > 0 else 0

            # Calculate averages
            booking_times = [m.time_to_book for m in metrics if m.time_to_book]
            avg_booking_time = sum(booking_times) / len(booking_times) / 3600 if booking_times else 0  # Convert to hours

            exam_durations = [m.exam_duration for m in metrics if m.exam_duration]
            avg_exam_duration = sum(exam_durations) / len(exam_durations) if exam_durations else 0

            # Channel performance
            channel_performance = {}
            channels = set(m.booking_channel for m in metrics)
            for channel in channels:
                channel_metrics = [m for m in metrics if m.booking_channel == channel]
                channel_completed = len([m for m in channel_metrics if m.appointment_status == "completed"])
                channel_performance[channel] = {
                    "total": len(channel_metrics),
                    "completed": channel_completed,
                    "completion_rate": channel_completed / len(channel_metrics) if channel_metrics else 0
                }

            analytics = AppointmentAnalytics(
                organization_id=organization_id,
                period_start=start_date,
                period_end=end_date,
                total_appointments=total_appointments,
                completed_appointments=completed,
                cancelled_appointments=cancelled,
                no_show_appointments=no_shows,
                rescheduled_appointments=rescheduled,
                completion_rate=completion_rate,
                no_show_rate=no_show_rate,
                average_booking_time=avg_booking_time,
                average_exam_duration=avg_exam_duration,
                booking_conversion_rate=completion_rate,  # Simplified for now
                channel_performance=channel_performance
            )

            return analytics

        except Exception as e:
            logger.error(f"Error calculating appointment analytics: {str(e)}")
            return None

    async def predict_no_shows(
        self,
        organization_id: str,
        look_ahead_days: int = 7
    ) -> List[Dict[str, Any]]:
        """Predict potential no-shows for upcoming appointments."""
        try:
            # Get upcoming appointments
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=look_ahead_days)

            collection = get_collection(self.collection_name)
            query = {
                "organization_id": organization_id,
                "scheduled_date": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "appointment_status": {"$in": ["scheduled", "confirmed"]}
            }

            cursor = collection.find(query).sort("no_show_risk_score", -1)
            results = await cursor.to_list(length=100)

            # Return high-risk appointments
            high_risk_appointments = []
            for appointment in results:
                if appointment.get("no_show_risk_score", 0) > 0.6:
                    high_risk_appointments.append({
                        "appointment_id": appointment["appointment_id"],
                        "patient_id": appointment["patient_id"],
                        "scheduled_date": appointment["scheduled_date"],
                        "risk_score": appointment["no_show_risk_score"],
                        "exam_type": appointment["exam_type"],
                        "recommended_action": self._get_risk_mitigation_action(appointment["no_show_risk_score"])
                    })

            return high_risk_appointments

        except Exception as e:
            logger.error(f"Error predicting no-shows: {str(e)}")
            return []

    def _get_risk_mitigation_action(self, risk_score: float) -> str:
        """Get recommended action based on risk score."""
        if risk_score > 0.8:
            return "Call patient to confirm and offer mobile exam option"
        elif risk_score > 0.7:
            return "Send personalized reminder with prep instructions"
        elif risk_score > 0.6:
            return "Schedule automated reminder call 24 hours before"
        else:
            return "Standard reminder sequence"

    async def generate_appointment_report(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate comprehensive appointment performance report."""
        try:
            analytics = await self.get_appointment_analytics(organization_id, start_date, end_date)
            no_show_predictions = await self.predict_no_shows(organization_id)

            if not analytics:
                return {"error": "No data available for the specified period"}

            report = {
                "report_type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_appointments": analytics.total_appointments,
                    "completion_rate": f"{analytics.completion_rate * 100:.1f}%",
                    "no_show_rate": f"{analytics.no_show_rate * 100:.1f}%",
                    "average_booking_time": f"{analytics.average_booking_time:.1f} hours",
                    "average_exam_duration": f"{analytics.average_exam_duration:.0f} minutes"
                },
                "channel_performance": analytics.channel_performance,
                "upcoming_risks": {
                    "high_risk_appointments": len(no_show_predictions),
                    "predictions": no_show_predictions[:10]  # Top 10 risks
                },
                "recommendations": self._generate_recommendations(analytics, no_show_predictions),
                "generated_at": datetime.utcnow().isoformat()
            }

            return report

        except Exception as e:
            logger.error(f"Error generating appointment report: {str(e)}")
            return {"error": f"Failed to generate report: {str(e)}"}

    def _generate_recommendations(
        self,
        analytics: AppointmentAnalytics,
        no_show_predictions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []

        # No-show rate recommendations
        if analytics.no_show_rate > 0.15:
            recommendations.append("Consider implementing proactive reminder calls for high-risk patients")
            recommendations.append("Evaluate mobile exam options to reduce no-show rates")

        # Booking time recommendations
        if analytics.average_booking_time > 24:
            recommendations.append("Optimize VAPI conversation flow to reduce booking time")
            recommendations.append("Consider offering more immediate scheduling options")

        # Channel performance recommendations
        best_channel = max(analytics.channel_performance.items(),
                          key=lambda x: x[1].get("completion_rate", 0),
                          default=(None, {}))
        if best_channel[0]:
            recommendations.append(f"Focus marketing efforts on {best_channel[0]} channel (highest completion rate)")

        # High-risk predictions
        if len(no_show_predictions) > 5:
            recommendations.append("Implement immediate intervention for high-risk appointments")
            recommendations.append("Consider scheduling buffer appointments to account for predicted no-shows")

        return recommendations

    def _flatten_appointment_data(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested appointment data structure to match AppointmentMetrics model."""
        flattened = {}

        # Extract appointment details
        if "appointment" in appointment_data:
            apt = appointment_data["appointment"]
            flattened["appointment_id"] = apt.get("id")
            flattened["exam_type"] = apt.get("type")
            if apt.get("scheduled_date"):
                # Convert string to datetime if needed
                scheduled_date = apt.get("scheduled_date")
                if isinstance(scheduled_date, str):
                    flattened["scheduled_date"] = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
                else:
                    flattened["scheduled_date"] = scheduled_date
            flattened["appointment_status"] = "scheduled"  # Default status
            if apt.get("duration_minutes"):
                flattened["exam_duration"] = apt.get("duration_minutes")

        # Extract patient details (anonymized)
        if "patient" in appointment_data:
            patient = appointment_data["patient"]
            flattened["patient_id"] = patient.get("id")
            if patient.get("age_group"):
                flattened["patient_age_group"] = patient.get("age_group")
            # Add patient history for risk calculation
            flattened["patient_no_show_count"] = patient.get("no_show_count", 0)
            flattened["patient_appointment_history_count"] = patient.get("appointment_history_count", 0)

        # Extract call details
        if "call" in appointment_data:
            call = appointment_data["call"]
            flattened["booking_confidence"] = call.get("booking_confidence")
            flattened["booking_channel"] = "vapi"  # Since it's from VAPI
            if call.get("duration_seconds"):
                flattened["time_to_book"] = call.get("duration_seconds")

        # Extract metadata
        if "metadata" in appointment_data:
            meta = appointment_data["metadata"]
            # Support both organizationId (new) and tenantId (legacy)
            flattened["organization_id"] = meta.get("organizationId") or meta.get("tenantId")
            flattened["automation_id"] = meta.get("automationId")
            flattened["campaign_id"] = meta.get("campaignId")

        # Copy any already flat fields
        for key, value in appointment_data.items():
            if key not in ["appointment", "patient", "call", "metadata"] and key not in flattened:
                flattened[key] = value

        return flattened

    def _predict_no_show(self, risk_score: float) -> NoShowPrediction:
        """Create a no-show prediction object based on risk score."""
        if risk_score < 0.3:
            risk_level = "low"
            actions = ["Standard reminder sequence", "Send appointment confirmation"]
        elif risk_score < 0.7:
            risk_level = "medium"
            actions = ["Call patient 24 hours before", "Send prep instructions", "Offer rescheduling if needed"]
        else:
            risk_level = "high"
            actions = ["Immediate confirmation call", "Offer mobile exam option", "Schedule backup appointment"]

        return NoShowPrediction(
            appointment_id="",  # Will be set by caller
            patient_id="",      # Will be set by caller
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.85,    # Default confidence
            recommended_actions=actions
        )

    def _anonymize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize patient data for HIPAA compliance."""
        anonymized = {}

        # Keep only safe fields
        safe_fields = ["patient_id", "age", "appointment_history_count", "no_show_count"]
        for field in safe_fields:
            if field in patient_data:
                if field == "age" and isinstance(patient_data[field], int):
                    # Convert age to age group
                    age = patient_data[field]
                    if age < 18:
                        anonymized["age_group"] = "minor"
                    elif age < 65:
                        anonymized["age_group"] = "adult"
                    else:
                        anonymized["age_group"] = "senior"
                else:
                    anonymized[field] = patient_data[field]

        return anonymized

    async def _create_audit_trail(
        self,
        action: str,
        patient_id: str,
        user_id: str,
        details: str
    ) -> str:
        """Create HIPAA audit trail entry."""
        try:
            audit_collection = get_collection("hipaa_audit_trail")

            audit_entry = {
                "action": action,
                "patient_id": patient_id,
                "user_id": user_id,
                "details": details,
                "timestamp": datetime.utcnow(),
                "ip_address": "system",  # Could be enhanced to capture real IP
                "system_component": "appointment_monitoring_service"
            }

            result = await audit_collection.insert_one(audit_entry)
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error creating audit trail: {str(e)}")
            raise

    async def get_no_show_predictions(
        self,
        organization_id: str,
        risk_threshold: float = 0.5
    ) -> List[NoShowPrediction]:
        """Get no-show predictions above risk threshold."""
        try:
            collection = get_collection(self.collection_name)

            query = {
                "organization_id": organization_id,
                "no_show_risk_score": {"$gte": risk_threshold},
                "appointment_status": {"$in": ["scheduled", "confirmed"]}
            }

            cursor = collection.find(query).sort("no_show_risk_score", -1)
            results = await cursor.to_list(length=100)

            predictions = []
            for result in results:
                prediction = self._predict_no_show(result.get("no_show_risk_score", 0))
                prediction.appointment_id = result.get("appointment_id", "")
                prediction.patient_id = result.get("patient_id", "")
                predictions.append(prediction)

            return predictions

        except Exception as e:
            logger.error(f"Error getting no-show predictions: {str(e)}")
            return []

    async def _calculate_booking_success_rate(
        self,
        organization_id: str,
        days_back: int = 30
    ) -> float:
        """Calculate booking success rate over specified period."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            collection = get_collection(self.collection_name)
            query = {
                "organization_id": organization_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            cursor = collection.find(query)
            results = await cursor.to_list(length=1000)

            if not results:
                return 0.0

            successful = len([r for r in results if r.get("completion_status") == "completed"])
            total = len(results)

            return (successful / total) * 100 if total > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating booking success rate: {str(e)}")
            return 0.0

    async def _analyze_appointment_patterns(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Analyze appointment patterns for optimization."""
        try:
            collection = get_collection(self.collection_name)

            # Get recent appointment data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)

            query = {
                "organization_id": organization_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            cursor = collection.find(query)
            results = await cursor.to_list(length=1000)

            patterns = {
                "optimal_days": [],
                "optimal_times": [],
                "success_patterns": {}
            }

            # Analyze day patterns
            day_success = {}
            for result in results:
                if "day_of_week" in result:
                    day = result["day_of_week"]
                    success = result.get("success", False)

                    if day not in day_success:
                        day_success[day] = {"total": 0, "successful": 0}

                    day_success[day]["total"] += 1
                    if success:
                        day_success[day]["successful"] += 1

            # Find optimal days (success rate > 80%)
            for day, stats in day_success.items():
                if stats["total"] > 5:  # Minimum sample size
                    success_rate = stats["successful"] / stats["total"]
                    if success_rate > 0.8:
                        patterns["optimal_days"].append(day)

            patterns["success_patterns"] = day_success

            return patterns

        except Exception as e:
            logger.error(f"Error analyzing appointment patterns: {str(e)}")
            return {"optimal_days": [], "optimal_times": [], "success_patterns": {}}