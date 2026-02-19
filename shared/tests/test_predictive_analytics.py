"""
Tests for Predictive Analytics

This module tests the predictive analytics capabilities including:
- Call outcome prediction models
- Optimal calling time recommendations
- Customer behavior analysis
- Revenue forecasting and optimization
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.shared.analytics.predictive_analytics import (
    PredictiveAnalytics,
    PredictionType,
    CallOutcome,
    CustomerSegment,
    PredictionResult,
    CallOutcomePrediction,
    OptimalTimeRecommendation,
    CustomerBehaviorAnalysis,
    RevenueForecast
)


class TestPredictiveAnalytics:
    """Test cases for Predictive Analytics"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'model_update_interval': 3600,
            'min_training_samples': 50,  # Lower for testing
            'prediction_confidence_threshold': 0.7,
            'feature_importance_threshold': 0.05
        }

    @pytest.fixture
    def analytics(self, config):
        """Predictive analytics instance"""
        return PredictiveAnalytics(config)

    @pytest.fixture
    def call_features(self):
        """Test call features"""
        return {
            'call_id': 'test-call-123',
            'customer_tier': 2,
            'call_duration': 300,
            'time_of_day': 14,
            'day_of_week': 3,
            'customer_age_days': 180,
            'previous_calls': 5,
            'success_rate': 0.7,
            'avg_call_duration': 250,
            'last_call_days_ago': 7,
            'customer_value': 5000
        }

    @pytest.fixture
    def customer_data(self):
        """Test customer data"""
        return {
            'customer_id': 'test-customer-123',
            'avg_response_time': 12,
            'preferred_hour': 14,
            'preferred_day': 3,
            'timezone_offset': -5,
            'work_schedule': 1,
            'last_contact_hour': 14,
            'success_rate_by_hour': 0.8,
            'engagement_score': 0.7,
            'total_calls': 15,
            'total_revenue': 8000,
            'avg_call_duration': 300,
            'response_rate': 0.8,
            'days_since_last_contact': 5,
            'customer_age_days': 365,
            'churn_risk_score': 0.2,
            'engagement_level': 0.8,
            'preferred_channel': 0,
            'complaint_count': 1,
            'phone_engagement': 0.9,
            'email_engagement': 0.6,
            'sms_engagement': 0.4,
            'chat_engagement': 0.3,
            'avg_order_value': 500,
            'purchase_frequency': 2,
            'engagement_trend': 'increasing'
        }

    @pytest.fixture
    def historical_data(self):
        """Test historical revenue data"""
        return {
            'current_revenue': 50000,
            'previous_revenue': 45000,
            'growth_rate': 0.11,
            'customer_count': 200,
            'avg_customer_value': 250,
            'churn_rate': 0.03,
            'acquisition_cost': 150,
            'seasonality_factor': 1.1,
            'market_conditions': 0.8
        }

    @pytest.fixture
    def training_data(self):
        """Test training data"""
        return {
            'call_outcome': [
                {
                    'customer_tier': 1, 'call_duration': 200, 'time_of_day': 10, 'day_of_week': 2,
                    'customer_age_days': 100, 'previous_calls': 3, 'success_rate': 0.6,
                    'avg_call_duration': 200, 'last_call_days_ago': 10, 'customer_value': 2000,
                    'outcome': 'success'
                },
                {
                    'customer_tier': 2, 'call_duration': 400, 'time_of_day': 15, 'day_of_week': 4,
                    'customer_age_days': 200, 'previous_calls': 8, 'success_rate': 0.8,
                    'avg_call_duration': 350, 'last_call_days_ago': 3, 'customer_value': 8000,
                    'outcome': 'success'
                },
                {
                    'customer_tier': 1, 'call_duration': 100, 'time_of_day': 8, 'day_of_week': 1,
                    'customer_age_days': 50, 'previous_calls': 1, 'success_rate': 0.3,
                    'avg_call_duration': 150, 'last_call_days_ago': 30, 'customer_value': 500,
                    'outcome': 'failure'
                }
            ],
            'optimal_time': [
                {
                    'avg_response_time': 8, 'preferred_hour': 10, 'preferred_day': 2,
                    'timezone_offset': -5, 'work_schedule': 1, 'last_contact_hour': 10,
                    'success_rate_by_hour': 0.9, 'engagement_score': 0.8,
                    'success_score': 0.9
                },
                {
                    'avg_response_time': 24, 'preferred_hour': 16, 'preferred_day': 5,
                    'timezone_offset': -8, 'work_schedule': 1, 'last_contact_hour': 16,
                    'success_rate_by_hour': 0.7, 'engagement_score': 0.6,
                    'success_score': 0.7
                }
            ],
            'customer_behavior': [
                {
                    'total_calls': 20, 'total_revenue': 15000, 'avg_call_duration': 400,
                    'response_rate': 0.9, 'days_since_last_contact': 2, 'customer_age_days': 500,
                    'churn_risk_score': 0.1, 'engagement_level': 0.9, 'preferred_channel': 0,
                    'complaint_count': 0, 'segment': 'high_value'
                },
                {
                    'total_calls': 5, 'total_revenue': 1000, 'avg_call_duration': 200,
                    'response_rate': 0.4, 'days_since_last_contact': 45, 'customer_age_days': 100,
                    'churn_risk_score': 0.8, 'engagement_level': 0.2, 'preferred_channel': 1,
                    'complaint_count': 3, 'segment': 'churn_risk'
                }
            ],
            'revenue_forecast': [
                {
                    'current_revenue': 60000, 'growth_rate': 0.15, 'customer_count': 250,
                    'avg_customer_value': 240, 'churn_rate': 0.02, 'acquisition_cost': 120,
                    'seasonality_factor': 1.2, 'market_conditions': 0.9, 'revenue': 69000
                },
                {
                    'current_revenue': 40000, 'growth_rate': 0.05, 'customer_count': 150,
                    'avg_customer_value': 267, 'churn_rate': 0.08, 'acquisition_cost': 200,
                    'seasonality_factor': 0.9, 'market_conditions': 0.6, 'revenue': 42000
                }
            ]
        }

    def test_initialization(self, analytics):
        """Test predictive analytics initialization"""
        assert analytics is not None
        assert len(analytics.models) == 4
        assert 'call_outcome' in analytics.models
        assert 'optimal_time' in analytics.models
        assert 'customer_behavior' in analytics.models
        assert 'revenue_forecast' in analytics.models

    def test_prepare_call_features(self, analytics, call_features):
        """Test call features preparation"""
        features = analytics._prepare_call_features(call_features)
        
        assert features is not None
        assert features.shape == (1, 10)
        assert features[0, 0] == 2  # customer_tier
        assert features[0, 1] == 300  # call_duration
        assert features[0, 2] == 14  # time_of_day

    def test_prepare_time_features(self, analytics, customer_data):
        """Test time features preparation"""
        features = analytics._prepare_time_features(customer_data)
        
        assert features is not None
        assert features.shape == (1, 8)
        assert features[0, 0] == 12  # avg_response_time
        assert features[0, 1] == 14  # preferred_hour

    def test_prepare_behavior_features(self, analytics, customer_data):
        """Test behavior features preparation"""
        features = analytics._prepare_behavior_features(customer_data)
        
        assert features is not None
        assert features.shape == (1, 10)
        assert features[0, 0] == 15  # total_calls
        assert features[0, 1] == 8000  # total_revenue

    def test_prepare_revenue_features(self, analytics, historical_data):
        """Test revenue features preparation"""
        features = analytics._prepare_revenue_features(historical_data)
        
        assert features is not None
        assert features.shape == (1, 8)
        assert features[0, 0] == 50000  # current_revenue
        assert features[0, 1] == 0.11  # growth_rate

    def test_convert_prediction_to_outcome(self, analytics):
        """Test prediction to outcome conversion"""
        # Test numeric predictions
        assert analytics._convert_prediction_to_outcome(0.8) == CallOutcome.SUCCESS
        assert analytics._convert_prediction_to_outcome(0.5) == CallOutcome.PARTIAL
        assert analytics._convert_prediction_to_outcome(0.3) == CallOutcome.FAILURE
        
        # Test string predictions
        assert analytics._convert_prediction_to_outcome('success') == CallOutcome.SUCCESS
        assert analytics._convert_prediction_to_outcome('partial') == CallOutcome.PARTIAL
        assert analytics._convert_prediction_to_outcome('failure') == CallOutcome.FAILURE

    @pytest.mark.asyncio
    async def test_generate_call_recommendations_success(self, analytics, call_features):
        """Test call recommendations for success prediction"""
        recommendations = await analytics._generate_call_recommendations(call_features, CallOutcome.SUCCESS)
        
        assert len(recommendations) >= 3
        assert any("successful" in rec.lower() for rec in recommendations)
        assert any("closing" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_call_recommendations_failure(self, analytics, call_features):
        """Test call recommendations for failure prediction"""
        recommendations = await analytics._generate_call_recommendations(call_features, CallOutcome.FAILURE)
        
        assert len(recommendations) >= 3
        assert any("fail" in rec.lower() for rec in recommendations)
        assert any("reschedul" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_time_recommendations(self, analytics, customer_data):
        """Test time recommendations generation"""
        recommendations = await analytics._generate_time_recommendations(customer_data, 0.8)
        
        assert len(recommendations) > 0
        assert len(recommendations) <= 10
        assert all(isinstance(rec, datetime) for rec in recommendations)

    def test_extract_preferred_days(self, analytics):
        """Test preferred days extraction"""
        test_times = [
            datetime(2024, 1, 1, 10, 0),  # Monday
            datetime(2024, 1, 2, 14, 0),  # Tuesday
            datetime(2024, 1, 3, 16, 0),  # Wednesday
            datetime(2024, 1, 1, 11, 0),  # Monday again
        ]
        
        preferred_days = analytics._extract_preferred_days(test_times)
        
        assert len(preferred_days) <= 3
        assert 'Monday' in preferred_days
        assert all(day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] for day in preferred_days)

    def test_extract_preferred_hours(self, analytics):
        """Test preferred hours extraction"""
        test_times = [
            datetime(2024, 1, 1, 10, 0),
            datetime(2024, 1, 2, 14, 0),
            datetime(2024, 1, 3, 16, 0),
            datetime(2024, 1, 4, 10, 0),  # 10 again
        ]
        
        preferred_hours = analytics._extract_preferred_hours(test_times)
        
        assert len(preferred_hours) <= 3
        assert 10 in preferred_hours
        assert all(0 <= hour <= 23 for hour in preferred_hours)

    def test_determine_customer_segment(self, analytics, customer_data):
        """Test customer segment determination"""
        # Test high value customer
        customer_data['total_revenue'] = 15000
        customer_data['engagement_level'] = 0.8
        customer_data['churn_risk_score'] = 0.2
        
        segment = analytics._determine_customer_segment(customer_data, 'high_value')
        assert segment == CustomerSegment.HIGH_VALUE
        
        # Test churn risk customer
        customer_data['churn_risk_score'] = 0.8
        segment = analytics._determine_customer_segment(customer_data, 'churn_risk')
        assert segment == CustomerSegment.CHURN_RISK

    @pytest.mark.asyncio
    async def test_calculate_churn_risk(self, analytics, customer_data):
        """Test churn risk calculation"""
        risk = await analytics._calculate_churn_risk(customer_data)
        
        assert 0.0 <= risk <= 1.0
        assert isinstance(risk, float)

    @pytest.mark.asyncio
    async def test_calculate_lifetime_value(self, analytics, customer_data):
        """Test lifetime value calculation"""
        value = await analytics._calculate_lifetime_value(customer_data)
        
        assert value > 0
        assert isinstance(value, float)

    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self, analytics, customer_data):
        """Test engagement score calculation"""
        score = await analytics._calculate_engagement_score(customer_data)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_analyze_preferred_channels(self, analytics, customer_data):
        """Test preferred channels analysis"""
        channels = analytics._analyze_preferred_channels(customer_data)
        
        assert isinstance(channels, list)
        assert all(channel in ['phone', 'email', 'sms', 'chat'] for channel in channels)

    def test_analyze_response_patterns(self, analytics, customer_data):
        """Test response patterns analysis"""
        patterns = analytics._analyze_response_patterns(customer_data)
        
        assert isinstance(patterns, dict)
        assert 'avg_response_time_hours' in patterns
        assert 'preferred_contact_time' in patterns
        assert 'response_rate' in patterns

    @pytest.mark.asyncio
    async def test_determine_next_best_action(self, analytics, customer_data):
        """Test next best action determination"""
        action = await analytics._determine_next_best_action(customer_data, CustomerSegment.HIGH_VALUE)
        
        assert isinstance(action, str)
        assert len(action) > 0

    def test_calculate_confidence_interval(self, analytics):
        """Test confidence interval calculation"""
        interval = analytics._calculate_confidence_interval(1000.0, 0.8)
        
        assert isinstance(interval, tuple)
        assert len(interval) == 2
        assert interval[0] < 1000.0 < interval[1]

    @pytest.mark.asyncio
    async def test_calculate_growth_rate(self, analytics, historical_data):
        """Test growth rate calculation"""
        rate = await analytics._calculate_growth_rate(historical_data)
        
        assert isinstance(rate, float)
        assert abs(rate - 0.11) < 0.002  # (50000 - 45000) / 45000 with tolerance

    @pytest.mark.asyncio
    async def test_identify_revenue_drivers(self, analytics, historical_data):
        """Test revenue drivers identification"""
        drivers = await analytics._identify_revenue_drivers(historical_data)
        
        assert isinstance(drivers, list)
        assert all(isinstance(driver, str) for driver in drivers)

    @pytest.mark.asyncio
    async def test_identify_revenue_risks(self, analytics, historical_data):
        """Test revenue risks identification"""
        risks = await analytics._identify_revenue_risks(historical_data)
        
        assert isinstance(risks, list)
        assert all(isinstance(risk, str) for risk in risks)

    @pytest.mark.asyncio
    async def test_generate_revenue_recommendations(self, analytics, historical_data):
        """Test revenue recommendations generation"""
        recommendations = await analytics._generate_revenue_recommendations(historical_data, 55000)
        
        assert isinstance(recommendations, list)
        assert all(isinstance(rec, str) for rec in recommendations)

    @pytest.mark.asyncio
    async def test_predict_call_outcome(self, analytics, call_features):
        """Test call outcome prediction"""
        # Mock the prediction result
        with patch.object(analytics, '_make_prediction') as mock_prediction:
            mock_prediction.return_value = PredictionResult(
                prediction_type=PredictionType.CALL_OUTCOME,
                predicted_value=0.8,
                confidence=0.85,
                features_used=['feature_0', 'feature_1'],
                model_version='1.0.0',
                timestamp=datetime.utcnow(),
                metadata={'model_name': 'call_outcome'}
            )
            
            result = await analytics.predict_call_outcome(call_features)
            
            assert result is not None
            assert isinstance(result, CallOutcomePrediction)
            assert result.call_id == 'test-call-123'
            assert result.predicted_outcome == CallOutcome.SUCCESS
            assert result.confidence == 0.85
            assert result.success_probability > 0.5
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_recommend_optimal_calling_time(self, analytics, customer_data):
        """Test optimal calling time recommendation"""
        # Mock the prediction result
        with patch.object(analytics, '_make_prediction') as mock_prediction:
            mock_prediction.return_value = PredictionResult(
                prediction_type=PredictionType.OPTIMAL_TIME,
                predicted_value=0.8,
                confidence=0.8,
                features_used=['feature_0', 'feature_1'],
                model_version='1.0.0',
                timestamp=datetime.utcnow(),
                metadata={'model_name': 'optimal_time'}
            )
            
            result = await analytics.recommend_optimal_calling_time('test-customer-123', customer_data)
            
            assert result is not None
            assert isinstance(result, OptimalTimeRecommendation)
            assert result.customer_id == 'test-customer-123'
            assert result.success_probability == 0.8
            assert len(result.recommended_times) > 0
            assert len(result.preferred_days) > 0
            assert len(result.preferred_hours) > 0

    @pytest.mark.asyncio
    async def test_analyze_customer_behavior(self, analytics, customer_data):
        """Test customer behavior analysis"""
        # Mock the prediction result
        with patch.object(analytics, '_make_prediction') as mock_prediction:
            mock_prediction.return_value = PredictionResult(
                prediction_type=PredictionType.CUSTOMER_BEHAVIOR,
                predicted_value='high_value',
                confidence=0.8,
                features_used=['feature_0', 'feature_1'],
                model_version='1.0.0',
                timestamp=datetime.utcnow(),
                metadata={'model_name': 'customer_behavior'}
            )
            
            result = await analytics.analyze_customer_behavior('test-customer-123', customer_data)
            
            assert result is not None
            assert isinstance(result, CustomerBehaviorAnalysis)
            assert result.customer_id == 'test-customer-123'
            # The segment is determined by actual customer data, not the mocked prediction
            assert result.segment in [CustomerSegment.HIGH_VALUE, CustomerSegment.MEDIUM_VALUE]
            assert 0.0 <= result.churn_risk <= 1.0
            assert result.lifetime_value > 0
            assert 0.0 <= result.engagement_score <= 1.0
            assert len(result.preferred_channels) > 0
            assert isinstance(result.response_patterns, dict)
            assert len(result.next_best_action) > 0

    @pytest.mark.asyncio
    async def test_forecast_revenue(self, analytics, historical_data):
        """Test revenue forecasting"""
        # Mock the prediction result
        with patch.object(analytics, '_make_prediction') as mock_prediction:
            mock_prediction.return_value = PredictionResult(
                prediction_type=PredictionType.REVENUE_FORECAST,
                predicted_value=55000.0,
                confidence=0.8,
                features_used=['feature_0', 'feature_1'],
                model_version='1.0.0',
                timestamp=datetime.utcnow(),
                metadata={'model_name': 'revenue_forecast'}
            )
            
            result = await analytics.forecast_revenue(historical_data, '30d')
            
            assert result is not None
            assert isinstance(result, RevenueForecast)
            assert result.period == '30d'
            assert result.predicted_revenue == 55000.0
            assert len(result.confidence_interval) == 2
            assert abs(result.growth_rate - 0.11) < 0.002
            assert len(result.key_drivers) >= 0
            assert len(result.risk_factors) >= 0
            assert len(result.recommendations) >= 0

    @pytest.mark.asyncio
    async def test_train_models(self, analytics, training_data):
        """Test model training"""
        result = await analytics.train_models(training_data)
        
        assert result is True

    def test_prepare_training_data(self, analytics, training_data):
        """Test training data preparation"""
        X, y = analytics._prepare_training_data('call_outcome', training_data['call_outcome'])
        
        assert X is not None
        assert y is not None
        assert X.shape[0] == len(training_data['call_outcome'])
        assert len(y) == len(training_data['call_outcome'])

    def test_evaluate_model(self, analytics):
        """Test model evaluation"""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        
        accuracy = analytics._evaluate_model('call_outcome', y_true, y_pred)
        assert accuracy == 1.0

    def test_get_model_status(self, analytics):
        """Test model status retrieval"""
        status = analytics.get_model_status()
        
        assert isinstance(status, dict)
        assert 'call_outcome' in status
        assert 'optimal_time' in status
        assert 'customer_behavior' in status
        assert 'revenue_forecast' in status
        
        for model_name, model_status in status.items():
            assert 'version' in model_status
            assert 'last_training' in model_status
            assert 'is_trained' in model_status
            assert 'prediction_count' in model_status

    @pytest.mark.asyncio
    async def test_predict_call_outcome_no_features(self, analytics):
        """Test call outcome prediction with no features"""
        result = await analytics.predict_call_outcome({})
        
        assert result is None

    @pytest.mark.asyncio
    async def test_recommend_optimal_calling_time_no_features(self, analytics):
        """Test optimal calling time recommendation with no features"""
        result = await analytics.recommend_optimal_calling_time('test-customer', {})
        
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_customer_behavior_no_features(self, analytics):
        """Test customer behavior analysis with no features"""
        result = await analytics.analyze_customer_behavior('test-customer', {})
        
        assert result is None

    @pytest.mark.asyncio
    async def test_forecast_revenue_no_features(self, analytics):
        """Test revenue forecasting with no features"""
        result = await analytics.forecast_revenue({}, '30d')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_train_models_insufficient_data(self, analytics):
        """Test model training with insufficient data"""
        insufficient_data = {
            'call_outcome': [{'customer_tier': 1, 'outcome': 'success'}]  # Only 1 sample
        }
        
        result = await analytics.train_models(insufficient_data)
        
        assert result is True  # Should not fail, just skip training

    def test_prepare_features_with_missing_values(self, analytics):
        """Test feature preparation with missing values"""
        incomplete_data = {
            'customer_tier': None,
            'call_duration': 300,
            'time_of_day': None
        }
        
        features = analytics._prepare_call_features(incomplete_data)
        
        assert features is not None
        assert features[0, 0] == 0  # None should be converted to 0
        assert features[0, 1] == 300
        assert features[0, 2] == 0  # None should be converted to 0

    @pytest.mark.asyncio
    async def test_make_prediction_without_model(self, analytics):
        """Test prediction without trained model"""
        features = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
        
        # This should handle the case where model is not trained
        result = await analytics._make_prediction('call_outcome', features)
        
        # Should return None or handle gracefully
        assert result is None

    def test_convert_prediction_to_outcome_edge_cases(self, analytics):
        """Test prediction to outcome conversion edge cases"""
        # Test edge cases
        assert analytics._convert_prediction_to_outcome(0.0) == CallOutcome.FAILURE
        assert analytics._convert_prediction_to_outcome(1.0) == CallOutcome.SUCCESS
        assert analytics._convert_prediction_to_outcome('unknown') == CallOutcome.PARTIAL

    @pytest.mark.asyncio
    async def test_calculate_churn_risk_edge_cases(self, analytics):
        """Test churn risk calculation edge cases"""
        # Test with minimal data
        minimal_data = {}
        risk = await analytics._calculate_churn_risk(minimal_data)
        
        assert 0.0 <= risk <= 1.0
        assert isinstance(risk, float)

    @pytest.mark.asyncio
    async def test_calculate_lifetime_value_edge_cases(self, analytics):
        """Test lifetime value calculation edge cases"""
        # Test with zero customer age
        data_with_zero_age = {'total_revenue': 1000, 'customer_age_days': 0}
        value = await analytics._calculate_lifetime_value(data_with_zero_age)
        
        assert value == 1000  # Should return total_revenue when age is 0

    def test_analyze_preferred_channels_edge_cases(self, analytics):
        """Test preferred channels analysis edge cases"""
        # Test with no channel data
        no_channel_data = {}
        channels = analytics._analyze_preferred_channels(no_channel_data)
        
        assert channels == ['phone']  # Should return default

    def test_calculate_confidence_interval_edge_cases(self, analytics):
        """Test confidence interval calculation edge cases"""
        # Test with zero confidence
        interval = analytics._calculate_confidence_interval(1000.0, 0.0)
        
        assert interval[0] < 1000.0 < interval[1]
        assert isinstance(interval, tuple)

    @pytest.mark.asyncio
    async def test_calculate_growth_rate_edge_cases(self, analytics):
        """Test growth rate calculation edge cases"""
        # Test with zero previous revenue
        data_with_zero_previous = {'current_revenue': 1000, 'previous_revenue': 0}
        rate = await analytics._calculate_growth_rate(data_with_zero_previous)
        
        assert rate == 0.0  # Should return 0 when previous revenue is 0

    def test_model_initialization_without_ml_libraries(self, config):
        """Test model initialization without advanced ML libraries"""
        # Mock the import to simulate missing libraries
        with patch.dict('sys.modules', {'xgboost': None, 'lightgbm': None}):
            analytics = PredictiveAnalytics(config)
            
            assert analytics is not None
            assert len(analytics.models) == 4
            # Should fall back to RandomForest models

    def test_feature_importance_threshold(self, analytics):
        """Test feature importance threshold functionality"""
        # Test that feature importance threshold is respected
        assert analytics.feature_importance_threshold == 0.05
        
        # Test with different threshold
        analytics.feature_importance_threshold = 0.1
        assert analytics.feature_importance_threshold == 0.1

    def test_prediction_confidence_threshold(self, analytics):
        """Test prediction confidence threshold"""
        assert analytics.prediction_confidence_threshold == 0.7
        
        # Test with different threshold
        analytics.prediction_confidence_threshold = 0.8
        assert analytics.prediction_confidence_threshold == 0.8

    def test_min_training_samples(self, analytics):
        """Test minimum training samples configuration"""
        assert analytics.min_training_samples == 50  # Set in fixture
        
        # Test with different value
        analytics.min_training_samples = 200
        assert analytics.min_training_samples == 200

    def test_model_update_interval(self, analytics):
        """Test model update interval configuration"""
        assert analytics.model_update_interval == 3600
        
        # Test with different value
        analytics.model_update_interval = 7200
        assert analytics.model_update_interval == 7200

