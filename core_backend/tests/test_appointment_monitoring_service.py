"""
Unit tests for the AppointmentMonitoringService.

This module tests the specialized appointment monitoring service
functionality including HIPAA-compliant data handling, no-show prediction,
and healthcare-specific analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from backend.services.appointment_monitoring_service import (
    AppointmentMonitoringService,
    AppointmentMetrics,
    NoShowPrediction
)


@pytest.fixture
def appointment_service():
    """Create an appointment monitoring service instance for testing."""
    return AppointmentMonitoringService()


@pytest.fixture
def sample_appointment_data():
    """Sample appointment data for testing (HIPAA-compliant format)."""
    return {
        "appointment": {
            "id": "appt_12345",
            "type": "medical_exam",
            "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "duration_minutes": 30,
            "priority": "routine"
        },
        "patient": {
            "id": "patient_789",
            "age_group": "adult",
            "appointment_history_count": 5,
            "no_show_count": 1
        },
        "call": {
            "id": "call_456",
            "duration_seconds": 240,
            "completion_status": "completed",
            "booking_confidence": 0.85
        },
        "metadata": {
            "tenantId": "healthcare_tenant",
            "automationId": "medical_exam_automation",
            "campaignId": "exam_scheduling_campaign"
        },
        "scheduling_details": {
            "preferred_time": "morning",
            "special_requirements": ["fasting_required"],
            "insurance_verified": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_no_show_data():
    """Sample data for no-show prediction testing."""
    return {
        "patient_history": {
            "total_appointments": 10,
            "no_shows": 2,
            "cancellations": 1,
            "avg_advance_booking_days": 5
        },
        "appointment_factors": {
            "day_of_week": "monday",
            "time_of_day": "morning",
            "weather_forecast": "clear",
            "advance_booking_days": 7
        },
        "demographic_factors": {
            "age_group": "adult",
            "insurance_type": "commercial"
        }
    }


class TestAppointmentMetrics:
    """Test appointment metrics functionality."""

    @pytest.mark.asyncio
    async def test_record_appointment_metrics_success(self, appointment_service, sample_appointment_data):
        """Test successful recording of appointment metrics."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="appointment_metric_123")

            result = await appointment_service.record_appointment_metrics(sample_appointment_data)

            assert result == "appointment_metric_123"
            mock_collection.insert_one.assert_called_once()

            call_args = mock_collection.insert_one.call_args[0][0]
            assert call_args["appointment_id"] == "appt_12345"
            assert call_args["exam_type"] == "medical_exam"
            assert "created_at" in call_args

    @pytest.mark.asyncio
    async def test_record_appointment_metrics_with_no_show_prediction(self, appointment_service, sample_appointment_data):
        """Test recording appointment metrics with no-show prediction."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="appointment_metric_123")

            result = await appointment_service.record_appointment_metrics(sample_appointment_data)

            call_args = mock_collection.insert_one.call_args[0][0]
            assert "no_show_risk_score" in call_args
            assert isinstance(call_args["no_show_risk_score"], float)
            assert 0 <= call_args["no_show_risk_score"] <= 1

    @pytest.mark.asyncio
    async def test_get_appointment_metrics(self, appointment_service):
        """Test retrieving appointment metrics."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            mock_metrics_data = [
                {
                    "id": "metric_1",
                    "automation_id": "test_automation_123",
                    "tenant_id": "healthcare_tenant",
                    "appointment_id": "appt_12345",
                    "patient_id": "patient_789",
                    "exam_type": "medical_exam",
                    "scheduled_date": datetime.utcnow(),
                    "appointment_status": "scheduled",
                    "booking_channel": "vapi",
                    "no_show_risk_score": 0.25,
                    "booking_confidence": 0.85,
                    "created_at": datetime.utcnow()
                }
            ]
            # Mock the full cursor chain
            mock_limit = AsyncMock()
            mock_limit.to_list = AsyncMock(return_value=mock_metrics_data)
            mock_sort = Mock()
            mock_sort.limit = Mock(return_value=mock_limit)
            mock_find = Mock()
            mock_find.sort = Mock(return_value=mock_sort)
            mock_collection.find = Mock(return_value=mock_find)

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            result = await appointment_service.get_appointment_metrics(
                tenant_id="healthcare_tenant",
                start_date=start_date,
                end_date=end_date,
                limit=10
            )

            assert len(result) == 1
            assert isinstance(result[0], AppointmentMetrics)
            assert result[0].appointment_id == "appt_12345"
            assert result[0].exam_type == "medical_exam"


class TestNoShowPrediction:
    """Test no-show prediction functionality."""

    def test_calculate_no_show_risk_low_risk(self, appointment_service, sample_no_show_data):
        """Test no-show risk calculation for low-risk patient."""
        # Low risk: good history, optimal timing
        sample_no_show_data["patient_history"]["no_shows"] = 0
        sample_no_show_data["appointment_factors"]["advance_booking_days"] = 3

        risk_score = appointment_service._calculate_no_show_risk(sample_no_show_data)

        assert 0 <= risk_score <= 1
        assert risk_score < 0.3  # Should be low risk

    def test_calculate_no_show_risk_high_risk(self, appointment_service, sample_no_show_data):
        """Test no-show risk calculation for high-risk patient."""
        # High risk: poor history, short notice
        sample_no_show_data["patient_history"]["no_shows"] = 5
        sample_no_show_data["appointment_factors"]["advance_booking_days"] = 1

        risk_score = appointment_service._calculate_no_show_risk(sample_no_show_data)

        assert 0 <= risk_score <= 1
        assert risk_score > 0.7  # Should be high risk

    def test_predict_no_show_recommendation(self, appointment_service):
        """Test no-show prediction recommendations."""
        # Test low risk
        low_risk_prediction = appointment_service._predict_no_show(0.2)
        assert low_risk_prediction.risk_level == "low"
        assert "standard" in low_risk_prediction.recommended_actions[0].lower()

        # Test high risk
        high_risk_prediction = appointment_service._predict_no_show(0.8)
        assert high_risk_prediction.risk_level == "high"
        assert any("confirmation" in action.lower() for action in high_risk_prediction.recommended_actions)

    @pytest.mark.asyncio
    async def test_get_no_show_predictions(self, appointment_service):
        """Test retrieving no-show predictions."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            mock_prediction_data = [
                {
                    "id": "prediction_1",
                    "appointment_id": "appt_12345",
                    "risk_score": 0.75,
                    "risk_level": "high",
                    "recommended_actions": ["Send confirmation call", "Schedule reminder"],
                    "created_at": datetime.utcnow()
                }
            ]
            mock_collection.find.return_value.sort.return_value.to_list.return_value = mock_prediction_data

            result = await appointment_service.get_no_show_predictions(
                tenant_id="healthcare_tenant",
                risk_threshold=0.5
            )

            assert len(result) == 1
            assert isinstance(result[0], NoShowPrediction)
            assert result[0].risk_level == "high"


class TestHIPAACompliance:
    """Test HIPAA compliance features."""

    @pytest.mark.asyncio
    async def test_hipaa_compliant_data_storage(self, appointment_service, sample_appointment_data):
        """Test that sensitive data is properly handled."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="appointment_metric_123")

            await appointment_service.record_appointment_metrics(sample_appointment_data)

            call_args = mock_collection.insert_one.call_args[0][0]

            # Verify no direct PHI is stored
            assert "patient_name" not in call_args
            assert "phone_number" not in call_args
            assert "email" not in call_args

            # Verify only anonymized/aggregated data is stored
            assert "patient_id" in call_args  # Anonymized ID is OK
            assert "age_group" in call_args  # Aggregated data is OK

    def test_data_anonymization(self, appointment_service):
        """Test patient data anonymization."""
        sensitive_data = {
            "patient_name": "John Doe",
            "phone": "555-1234",
            "email": "john@example.com",
            "patient_id": "patient_789",
            "age": 35
        }

        anonymized = appointment_service._anonymize_patient_data(sensitive_data)

        assert "patient_name" not in anonymized
        assert "phone" not in anonymized
        assert "email" not in anonymized
        assert anonymized["patient_id"] == "patient_789"  # ID preserved for tracking
        assert anonymized["age_group"] == "adult"  # Age converted to group

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, appointment_service, sample_appointment_data):
        """Test creation of HIPAA audit trails."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="audit_123")

            await appointment_service._create_audit_trail(
                action="data_access",
                patient_id="patient_789",
                user_id="system",
                details="Appointment metrics recorded"
            )

            mock_collection.insert_one.assert_called_once()
            call_args = mock_collection.insert_one.call_args[0][0]

            assert call_args["action"] == "data_access"
            assert call_args["patient_id"] == "patient_789"
            assert "timestamp" in call_args


class TestAppointmentAnalytics:
    """Test appointment-specific analytics functionality."""

    @pytest.mark.asyncio
    async def test_calculate_booking_success_rate(self, appointment_service):
        """Test booking success rate calculation."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            mock_data = [
                {"booking_confidence": 0.9, "completion_status": "completed"},
                {"booking_confidence": 0.8, "completion_status": "completed"},
                {"booking_confidence": 0.3, "completion_status": "failed"},
                {"booking_confidence": 0.7, "completion_status": "completed"}
            ]
            mock_collection.find.return_value.to_list.return_value = mock_data

            success_rate = await appointment_service._calculate_booking_success_rate(
                tenant_id="healthcare_tenant",
                days_back=30
            )

            assert 0 <= success_rate <= 100
            assert success_rate == 75.0  # 3 out of 4 successful

    @pytest.mark.asyncio
    async def test_analyze_appointment_patterns(self, appointment_service):
        """Test appointment pattern analysis."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            mock_pattern_data = [
                {"day_of_week": "monday", "time_slot": "morning", "success": True},
                {"day_of_week": "monday", "time_slot": "morning", "success": True},
                {"day_of_week": "friday", "time_slot": "afternoon", "success": False}
            ]
            mock_collection.find.return_value.to_list.return_value = mock_pattern_data

            patterns = await appointment_service._analyze_appointment_patterns(
                tenant_id="healthcare_tenant"
            )

            assert "optimal_days" in patterns
            assert "optimal_times" in patterns
            assert isinstance(patterns["optimal_days"], list)


class TestErrorHandling:
    """Test error handling in appointment monitoring service."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, appointment_service):
        """Test handling of missing required fields."""
        invalid_data = {
            "appointment": {
                "id": "appt_12345"
                # Missing other required fields like type, scheduled_date
            }
            # Missing metadata, patient, call sections
        }

        # This should raise a ValidationError when trying to create AppointmentMetrics
        with pytest.raises(Exception):  # Could be ValidationError or ValueError
            await appointment_service.record_appointment_metrics(invalid_data)

    @pytest.mark.asyncio
    async def test_database_error_handling(self, appointment_service, sample_appointment_data):
        """Test database error handling."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception) as exc_info:
                await appointment_service.record_appointment_metrics(sample_appointment_data)

            assert "Database connection failed" in str(exc_info.value)

    def test_invalid_risk_score_calculation(self, appointment_service):
        """Test handling of invalid data in risk score calculation."""
        invalid_data = {
            "patient_history": {
                "total_appointments": 0,  # Division by zero case
                "no_shows": 0
            }
        }

        risk_score = appointment_service._calculate_no_show_risk(invalid_data)

        # Should handle gracefully and return default risk
        assert 0 <= risk_score <= 1


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_appointment_workflow(self, appointment_service, sample_appointment_data):
        """Test complete appointment monitoring workflow."""
        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="metric_123")

            # Record appointment metrics
            result = await appointment_service.record_appointment_metrics(sample_appointment_data)
            assert result == "metric_123"

            # Verify comprehensive data was stored
            call_args = mock_collection.insert_one.call_args[0][0]
            assert "no_show_risk_score" in call_args
            assert "booking_confidence" in call_args
            assert "hipaa_compliant" in call_args
            assert call_args["hipaa_compliant"] is True

    @pytest.mark.asyncio
    async def test_high_risk_patient_workflow(self, appointment_service, sample_appointment_data):
        """Test workflow for high-risk no-show patients."""
        # Modify data to simulate high-risk patient
        sample_appointment_data["patient"]["no_show_count"] = 3
        sample_appointment_data["patient"]["appointment_history_count"] = 5

        with patch('backend.services.appointment_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="metric_123")

            await appointment_service.record_appointment_metrics(sample_appointment_data)

            call_args = mock_collection.insert_one.call_args[0][0]
            # Should have moderate to high risk score for high no-show history
            assert call_args["no_show_risk_score"] > 0.2  # 3/5 no-show rate should be risky


if __name__ == "__main__":
    pytest.main([__file__])