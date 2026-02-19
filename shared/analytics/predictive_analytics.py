"""
Predictive Analytics

This module provides predictive analytics capabilities including:
- Call outcome prediction models
- Optimal calling time recommendations
- Customer behavior analysis
- Revenue forecasting and optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
from collections import deque
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, mean_squared_error, r2_score

# For advanced ML features
try:
    import xgboost as xgb
    import lightgbm as lgb
    from sklearn.linear_model import LogisticRegression, LinearRegression
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Advanced ML libraries not available. Install xgboost and lightgbm for enhanced predictions.")


class PredictionType(Enum):
    """Prediction types"""
    CALL_OUTCOME = "call_outcome"
    OPTIMAL_TIME = "optimal_time"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    REVENUE_FORECAST = "revenue_forecast"


class CallOutcome(Enum):
    """Call outcome types"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"


class CustomerSegment(Enum):
    """Customer segment types"""
    HIGH_VALUE = "high_value"
    MEDIUM_VALUE = "medium_value"
    LOW_VALUE = "low_value"
    CHURN_RISK = "churn_risk"
    GROWTH_POTENTIAL = "growth_potential"


@dataclass
class PredictionResult:
    """Prediction result"""
    prediction_type: PredictionType
    predicted_value: Any
    confidence: float
    features_used: List[str]
    model_version: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class CallOutcomePrediction:
    """Call outcome prediction"""
    call_id: str
    predicted_outcome: CallOutcome
    confidence: float
    success_probability: float
    failure_probability: float
    key_factors: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class OptimalTimeRecommendation:
    """Optimal calling time recommendation"""
    customer_id: str
    recommended_times: List[datetime]
    success_probability: float
    preferred_days: List[str]
    preferred_hours: List[int]
    timezone: str
    confidence: float
    timestamp: datetime


@dataclass
class CustomerBehaviorAnalysis:
    """Customer behavior analysis"""
    customer_id: str
    segment: CustomerSegment
    churn_risk: float
    lifetime_value: float
    engagement_score: float
    preferred_channels: List[str]
    response_patterns: Dict[str, Any]
    next_best_action: str
    timestamp: datetime


@dataclass
class RevenueForecast:
    """Revenue forecast"""
    period: str
    predicted_revenue: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    key_drivers: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    timestamp: datetime


class PredictiveAnalytics:
    """Predictive analytics for call outcomes and customer behavior"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        # Configuration
        self.model_update_interval = config.get('model_update_interval', 3600)  # 1 hour
        self.min_training_samples = config.get('min_training_samples', 100)
        self.prediction_confidence_threshold = config.get('prediction_confidence_threshold', 0.7)
        self.feature_importance_threshold = config.get('feature_importance_threshold', 0.05)

        # State
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: Dict[str, List[str]] = {}
        self.model_versions: Dict[str, str] = {}
        self.last_training: Dict[str, datetime] = {}
        self.prediction_history: Dict[str, List[PredictionResult]] = {}

        # Initialize models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize prediction models"""
        try:
            # Call outcome prediction model
            if ML_AVAILABLE:
                self.models['call_outcome'] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
            else:
                self.models['call_outcome'] = RandomForestClassifier(
                    n_estimators=50,
                    max_depth=5,
                    random_state=42
                )

            # Optimal time prediction model
            self.models['optimal_time'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                random_state=42
            )

            # Customer behavior model
            if ML_AVAILABLE:
                self.models['customer_behavior'] = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            else:
                self.models['customer_behavior'] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=8,
                    random_state=42
                )

            # Revenue forecasting model
            if ML_AVAILABLE:
                self.models['revenue_forecast'] = lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            else:
                self.models['revenue_forecast'] = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=8,
                    random_state=42
                )

            # Initialize scalers and encoders
            for model_name in self.models.keys():
                self.scalers[model_name] = StandardScaler()
                self.label_encoders[model_name] = LabelEncoder()
                self.feature_names[model_name] = []
                self.model_versions[model_name] = "1.0.0"
                self.last_training[model_name] = datetime.utcnow()

            self.logger.info("Predictive analytics models initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize models: {e}")

    async def predict_call_outcome(self, call_features: Dict[str, Any]) -> Optional[CallOutcomePrediction]:
        """
        Predict call outcome

        Args:
            call_features: Call features for prediction

        Returns:
            CallOutcomePrediction: Predicted call outcome
        """
        try:
            # Prepare features
            features = self._prepare_call_features(call_features)
            
            if features is None:
                return None

            # Make prediction
            prediction_result = await self._make_prediction('call_outcome', features)
            
            if not prediction_result:
                return None

            # Convert prediction to outcome
            predicted_outcome = self._convert_prediction_to_outcome(prediction_result.predicted_value)
            
            # Calculate probabilities
            success_prob = prediction_result.confidence if predicted_outcome == CallOutcome.SUCCESS else 1.0 - prediction_result.confidence
            failure_prob = 1.0 - success_prob

            # Generate recommendations
            recommendations = await self._generate_call_recommendations(call_features, predicted_outcome)

            return CallOutcomePrediction(
                call_id=call_features.get('call_id', 'unknown'),
                predicted_outcome=predicted_outcome,
                confidence=prediction_result.confidence,
                success_probability=success_prob,
                failure_probability=failure_prob,
                key_factors=prediction_result.features_used[:5],  # Top 5 factors
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Failed to predict call outcome: {e}")
            return None

    async def recommend_optimal_calling_time(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[OptimalTimeRecommendation]:
        """
        Recommend optimal calling time

        Args:
            customer_id: Customer identifier
            customer_data: Customer data for analysis

        Returns:
            OptimalTimeRecommendation: Optimal calling time recommendation
        """
        try:
            # Prepare features
            features = self._prepare_time_features(customer_data)
            
            if features is None:
                return None

            # Make prediction
            prediction_result = await self._make_prediction('optimal_time', features)
            
            if not prediction_result:
                return None

            # Generate time recommendations
            recommended_times = await self._generate_time_recommendations(customer_data, prediction_result.predicted_value)
            
            # Extract preferred days and hours
            preferred_days = self._extract_preferred_days(recommended_times)
            preferred_hours = self._extract_preferred_hours(recommended_times)

            return OptimalTimeRecommendation(
                customer_id=customer_id,
                recommended_times=recommended_times,
                success_probability=prediction_result.confidence,
                preferred_days=preferred_days,
                preferred_hours=preferred_hours,
                timezone=customer_data.get('timezone', 'UTC'),
                confidence=prediction_result.confidence,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Failed to recommend optimal calling time: {e}")
            return None

    async def analyze_customer_behavior(self, customer_id: str, customer_data: Dict[str, Any]) -> Optional[CustomerBehaviorAnalysis]:
        """
        Analyze customer behavior

        Args:
            customer_id: Customer identifier
            customer_data: Customer data for analysis

        Returns:
            CustomerBehaviorAnalysis: Customer behavior analysis
        """
        try:
            # Prepare features
            features = self._prepare_behavior_features(customer_data)
            
            if features is None:
                return None

            # Make prediction
            prediction_result = await self._make_prediction('customer_behavior', features)
            
            if not prediction_result:
                return None

            # Determine customer segment
            segment = self._determine_customer_segment(customer_data, prediction_result.predicted_value)
            
            # Calculate additional metrics
            churn_risk = await self._calculate_churn_risk(customer_data)
            lifetime_value = await self._calculate_lifetime_value(customer_data)
            engagement_score = await self._calculate_engagement_score(customer_data)
            
            # Analyze patterns
            preferred_channels = self._analyze_preferred_channels(customer_data)
            response_patterns = self._analyze_response_patterns(customer_data)
            next_best_action = await self._determine_next_best_action(customer_data, segment)

            return CustomerBehaviorAnalysis(
                customer_id=customer_id,
                segment=segment,
                churn_risk=churn_risk,
                lifetime_value=lifetime_value,
                engagement_score=engagement_score,
                preferred_channels=preferred_channels,
                response_patterns=response_patterns,
                next_best_action=next_best_action,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze customer behavior: {e}")
            return None

    async def forecast_revenue(self, historical_data: Dict[str, Any], forecast_period: str = "30d") -> Optional[RevenueForecast]:
        """
        Forecast revenue

        Args:
            historical_data: Historical revenue data
            forecast_period: Forecast period (e.g., "30d", "90d", "1y")

        Returns:
            RevenueForecast: Revenue forecast
        """
        try:
            # Prepare features
            features = self._prepare_revenue_features(historical_data)
            
            if features is None:
                return None

            # Make prediction
            prediction_result = await self._make_prediction('revenue_forecast', features)
            
            if not prediction_result:
                return None

            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(prediction_result.predicted_value, prediction_result.confidence)
            
            # Calculate growth rate
            growth_rate = await self._calculate_growth_rate(historical_data)
            
            # Analyze drivers and risks
            key_drivers = await self._identify_revenue_drivers(historical_data)
            risk_factors = await self._identify_revenue_risks(historical_data)
            recommendations = await self._generate_revenue_recommendations(historical_data, prediction_result.predicted_value)

            return RevenueForecast(
                period=forecast_period,
                predicted_revenue=prediction_result.predicted_value,
                confidence_interval=confidence_interval,
                growth_rate=growth_rate,
                key_drivers=key_drivers,
                risk_factors=risk_factors,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Failed to forecast revenue: {e}")
            return None

    async def train_models(self, training_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Train prediction models

        Args:
            training_data: Training data for each model type

        Returns:
            bool: True if training successful
        """
        try:
            for model_name, data in training_data.items():
                if model_name not in self.models:
                    continue

                if len(data) < self.min_training_samples:
                    self.logger.warning(f"Insufficient training data for {model_name}: {len(data)} samples")
                    continue

                # Prepare training data
                X, y = self._prepare_training_data(model_name, data)
                
                if X is None or y is None:
                    continue

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Scale features
                X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                X_test_scaled = self.scalers[model_name].transform(X_test)

                # Train model
                self.models[model_name].fit(X_train_scaled, y_train)

                # Evaluate model
                y_pred = self.models[model_name].predict(X_test_scaled)
                accuracy = self._evaluate_model(model_name, y_test, y_pred)

                # Update model version and timestamp
                self.model_versions[model_name] = f"{self.model_versions[model_name].split('.')[0]}.{int(time.time())}.0"
                self.last_training[model_name] = datetime.utcnow()

                self.logger.info(f"Trained {model_name} model with accuracy: {accuracy:.3f}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to train models: {e}")
            return False

    def _prepare_call_features(self, call_features: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare call features for prediction"""
        try:
            # Extract relevant features
            features = [
                call_features.get('customer_tier', 0),
                call_features.get('call_duration', 0),
                call_features.get('time_of_day', 12),
                call_features.get('day_of_week', 1),
                call_features.get('customer_age_days', 0),
                call_features.get('previous_calls', 0),
                call_features.get('success_rate', 0.5),
                call_features.get('avg_call_duration', 300),
                call_features.get('last_call_days_ago', 30),
                call_features.get('customer_value', 0)
            ]

            # Handle missing values
            features = [f if f is not None else 0 for f in features]
            
            return np.array(features).reshape(1, -1)

        except Exception as e:
            self.logger.error(f"Failed to prepare call features: {e}")
            return None

    def _prepare_time_features(self, customer_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare time features for prediction"""
        try:
            # Extract relevant features
            features = [
                customer_data.get('avg_response_time', 24),
                customer_data.get('preferred_hour', 14),
                customer_data.get('preferred_day', 3),
                customer_data.get('timezone_offset', 0),
                customer_data.get('work_schedule', 1),
                customer_data.get('last_contact_hour', 12),
                customer_data.get('success_rate_by_hour', 0.5),
                customer_data.get('engagement_score', 0.5)
            ]

            # Handle missing values
            features = [f if f is not None else 0 for f in features]
            
            return np.array(features).reshape(1, -1)

        except Exception as e:
            self.logger.error(f"Failed to prepare time features: {e}")
            return None

    def _prepare_behavior_features(self, customer_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare behavior features for prediction"""
        try:
            # Extract relevant features
            features = [
                customer_data.get('total_calls', 0),
                customer_data.get('total_revenue', 0),
                customer_data.get('avg_call_duration', 300),
                customer_data.get('response_rate', 0.5),
                customer_data.get('days_since_last_contact', 30),
                customer_data.get('customer_age_days', 0),
                customer_data.get('churn_risk_score', 0.5),
                customer_data.get('engagement_level', 0.5),
                customer_data.get('preferred_channel', 0),
                customer_data.get('complaint_count', 0)
            ]

            # Handle missing values
            features = [f if f is not None else 0 for f in features]
            
            return np.array(features).reshape(1, -1)

        except Exception as e:
            self.logger.error(f"Failed to prepare behavior features: {e}")
            return None

    def _prepare_revenue_features(self, historical_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare revenue features for prediction"""
        try:
            # Extract relevant features
            features = [
                historical_data.get('current_revenue', 0),
                historical_data.get('growth_rate', 0),
                historical_data.get('customer_count', 0),
                historical_data.get('avg_customer_value', 0),
                historical_data.get('churn_rate', 0),
                historical_data.get('acquisition_cost', 0),
                historical_data.get('seasonality_factor', 1),
                historical_data.get('market_conditions', 0.5)
            ]

            # Handle missing values
            features = [f if f is not None else 0 for f in features]
            
            return np.array(features).reshape(1, -1)

        except Exception as e:
            self.logger.error(f"Failed to prepare revenue features: {e}")
            return None

    async def _make_prediction(self, model_name: str, features: np.ndarray) -> Optional[PredictionResult]:
        """Make prediction using specified model"""
        try:
            if model_name not in self.models:
                return None

            # Scale features
            features_scaled = self.scalers[model_name].transform(features)
            
            # Make prediction
            prediction = self.models[model_name].predict(features_scaled)[0]
            
            # Get prediction probabilities/confidence
            if hasattr(self.models[model_name], 'predict_proba'):
                probabilities = self.models[model_name].predict_proba(features_scaled)[0]
                confidence = max(probabilities)
            else:
                confidence = 0.8  # Default confidence for regression models

            # Get feature importance
            if hasattr(self.models[model_name], 'feature_importances_'):
                feature_importance = self.models[model_name].feature_importances_
                important_features = [f"feature_{i}" for i, imp in enumerate(feature_importance) if imp > self.feature_importance_threshold]
            else:
                important_features = [f"feature_{i}" for i in range(features.shape[1])]

            return PredictionResult(
                prediction_type=PredictionType(model_name),
                predicted_value=prediction,
                confidence=confidence,
                features_used=important_features,
                model_version=self.model_versions[model_name],
                timestamp=datetime.utcnow(),
                metadata={'model_name': model_name}
            )

        except Exception as e:
            self.logger.error(f"Failed to make prediction for {model_name}: {e}")
            return None

    def _convert_prediction_to_outcome(self, prediction: Any) -> CallOutcome:
        """Convert prediction value to call outcome"""
        try:
            if isinstance(prediction, (int, float)):
                if prediction > 0.7:
                    return CallOutcome.SUCCESS
                elif prediction > 0.4:
                    return CallOutcome.PARTIAL
                else:
                    return CallOutcome.FAILURE
            else:
                # Handle string predictions
                prediction_str = str(prediction).lower()
                if 'success' in prediction_str:
                    return CallOutcome.SUCCESS
                elif 'partial' in prediction_str:
                    return CallOutcome.PARTIAL
                elif 'failure' in prediction_str:
                    return CallOutcome.FAILURE
                else:
                    return CallOutcome.PARTIAL

        except Exception as e:
            self.logger.error(f"Failed to convert prediction to outcome: {e}")
            return CallOutcome.PARTIAL

    async def _generate_call_recommendations(self, call_features: Dict[str, Any], predicted_outcome: CallOutcome) -> List[str]:
        """Generate call recommendations based on prediction"""
        try:
            recommendations = []

            if predicted_outcome == CallOutcome.SUCCESS:
                recommendations.extend([
                    "Call is likely to be successful - focus on closing the deal",
                    "Prepare follow-up materials for post-call engagement",
                    "Consider upselling opportunities during the call"
                ])
            elif predicted_outcome == CallOutcome.PARTIAL:
                recommendations.extend([
                    "Call may be partially successful - prepare for objections",
                    "Have alternative approaches ready",
                    "Focus on building rapport and understanding needs"
                ])
            else:  # FAILURE
                recommendations.extend([
                    "Call is likely to fail - consider rescheduling",
                    "Review customer history for better timing",
                    "Prepare strong value proposition and objection handling"
                ])

            # Add time-based recommendations
            time_of_day = call_features.get('time_of_day', 12)
            if time_of_day < 9 or time_of_day > 17:
                recommendations.append("Consider calling during business hours for better success rate")

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate call recommendations: {e}")
            return ["Review customer data and prepare accordingly"]

    async def _generate_time_recommendations(self, customer_data: Dict[str, Any], predicted_score: float) -> List[datetime]:
        """Generate time recommendations based on prediction"""
        try:
            recommendations = []
            base_time = datetime.utcnow()
            
            # Generate recommendations for next 7 days
            for day_offset in range(7):
                target_date = base_time + timedelta(days=day_offset)
                
                # Adjust based on predicted score
                if predicted_score > 0.8:
                    # High success probability - recommend multiple times
                    for hour in [9, 11, 14, 16]:
                        recommendations.append(target_date.replace(hour=hour, minute=0, second=0, microsecond=0))
                elif predicted_score > 0.6:
                    # Medium success probability - recommend 2 times
                    for hour in [10, 15]:
                        recommendations.append(target_date.replace(hour=hour, minute=0, second=0, microsecond=0))
                else:
                    # Low success probability - recommend 1 time
                    recommendations.append(target_date.replace(hour=14, minute=0, second=0, microsecond=0))

            return recommendations[:10]  # Limit to 10 recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate time recommendations: {e}")
            return []

    def _extract_preferred_days(self, recommended_times: List[datetime]) -> List[str]:
        """Extract preferred days from recommendations"""
        try:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = {}
            
            for time in recommended_times:
                day_name = days[time.weekday()]
                day_counts[day_name] = day_counts.get(day_name, 0) + 1
            
            # Return top 3 preferred days
            return sorted(day_counts.keys(), key=lambda x: day_counts[x], reverse=True)[:3]

        except Exception as e:
            self.logger.error(f"Failed to extract preferred days: {e}")
            return ['Monday', 'Tuesday', 'Wednesday']

    def _extract_preferred_hours(self, recommended_times: List[datetime]) -> List[int]:
        """Extract preferred hours from recommendations"""
        try:
            hour_counts = {}
            
            for time in recommended_times:
                hour = time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # Return top 3 preferred hours
            return sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]

        except Exception as e:
            self.logger.error(f"Failed to extract preferred hours: {e}")
            return [10, 14, 16]

    def _determine_customer_segment(self, customer_data: Dict[str, Any], prediction: Any) -> CustomerSegment:
        """Determine customer segment based on data and prediction"""
        try:
            total_revenue = customer_data.get('total_revenue', 0)
            engagement_level = customer_data.get('engagement_level', 0.5)
            churn_risk = customer_data.get('churn_risk_score', 0.5)

            if churn_risk > 0.7:
                return CustomerSegment.CHURN_RISK
            elif total_revenue > 10000 and engagement_level > 0.7:
                return CustomerSegment.HIGH_VALUE
            elif total_revenue > 1000 or engagement_level > 0.5:
                return CustomerSegment.MEDIUM_VALUE
            elif engagement_level > 0.3:
                return CustomerSegment.GROWTH_POTENTIAL
            else:
                return CustomerSegment.LOW_VALUE

        except Exception as e:
            self.logger.error(f"Failed to determine customer segment: {e}")
            return CustomerSegment.MEDIUM_VALUE

    async def _calculate_churn_risk(self, customer_data: Dict[str, Any]) -> float:
        """Calculate churn risk score"""
        try:
            risk_factors = [
                customer_data.get('days_since_last_contact', 30) / 30,  # Normalize to 0-1
                1 - customer_data.get('engagement_level', 0.5),
                customer_data.get('complaint_count', 0) / 10,  # Normalize
                1 - customer_data.get('response_rate', 0.5)
            ]
            
            return min(sum(risk_factors) / len(risk_factors), 1.0)

        except Exception as e:
            self.logger.error(f"Failed to calculate churn risk: {e}")
            return 0.5

    async def _calculate_lifetime_value(self, customer_data: Dict[str, Any]) -> float:
        """Calculate customer lifetime value"""
        try:
            total_revenue = customer_data.get('total_revenue', 0)
            avg_order_value = customer_data.get('avg_order_value', 0)
            purchase_frequency = customer_data.get('purchase_frequency', 1)
            customer_age_days = customer_data.get('customer_age_days', 365)
            
            if customer_age_days > 0:
                daily_value = total_revenue / customer_age_days
                # Project for 2 years
                return daily_value * 730
            else:
                return total_revenue

        except Exception as e:
            self.logger.error(f"Failed to calculate lifetime value: {e}")
            return customer_data.get('total_revenue', 0)

    async def _calculate_engagement_score(self, customer_data: Dict[str, Any]) -> float:
        """Calculate customer engagement score"""
        try:
            factors = [
                customer_data.get('response_rate', 0.5),
                customer_data.get('engagement_level', 0.5),
                min(customer_data.get('total_calls', 0) / 10, 1.0),  # Normalize
                min(customer_data.get('avg_call_duration', 0) / 600, 1.0)  # Normalize to 10 minutes
            ]
            
            return sum(factors) / len(factors)

        except Exception as e:
            self.logger.error(f"Failed to calculate engagement score: {e}")
            return 0.5

    def _analyze_preferred_channels(self, customer_data: Dict[str, Any]) -> List[str]:
        """Analyze preferred communication channels"""
        try:
            channels = ['phone', 'email', 'sms', 'chat']
            channel_scores = {}
            
            for channel in channels:
                score = customer_data.get(f'{channel}_engagement', 0.0)  # Default to 0.0 for edge case
                channel_scores[channel] = score
            
            # Return channels with score > 0.3
            preferred = [channel for channel, score in channel_scores.items() if score > 0.3]
            
            # If no channels meet the threshold, return default
            if not preferred:
                return ['phone']
            
            return preferred

        except Exception as e:
            self.logger.error(f"Failed to analyze preferred channels: {e}")
            return ['phone']

    def _analyze_response_patterns(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer response patterns"""
        try:
            return {
                'avg_response_time_hours': customer_data.get('avg_response_time', 24),
                'preferred_contact_time': customer_data.get('preferred_hour', 14),
                'response_rate': customer_data.get('response_rate', 0.5),
                'engagement_trend': customer_data.get('engagement_trend', 'stable')
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze response patterns: {e}")
            return {}

    async def _determine_next_best_action(self, customer_data: Dict[str, Any], segment: CustomerSegment) -> str:
        """Determine next best action for customer"""
        try:
            if segment == CustomerSegment.CHURN_RISK:
                return "Immediate re-engagement campaign"
            elif segment == CustomerSegment.HIGH_VALUE:
                return "Upsell or cross-sell opportunity"
            elif segment == CustomerSegment.GROWTH_POTENTIAL:
                return "Increase engagement and education"
            elif segment == CustomerSegment.MEDIUM_VALUE:
                return "Regular follow-up and nurturing"
            else:  # LOW_VALUE
                return "Basic engagement and value demonstration"

        except Exception as e:
            self.logger.error(f"Failed to determine next best action: {e}")
            return "Regular follow-up"

    def _calculate_confidence_interval(self, predicted_value: float, confidence: float) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""
        try:
            margin = (1 - confidence) * predicted_value * 0.2  # 20% margin
            return (predicted_value - margin, predicted_value + margin)

        except Exception as e:
            self.logger.error(f"Failed to calculate confidence interval: {e}")
            return (predicted_value * 0.8, predicted_value * 1.2)

    async def _calculate_growth_rate(self, historical_data: Dict[str, Any]) -> float:
        """Calculate revenue growth rate"""
        try:
            current_revenue = historical_data.get('current_revenue', 0)
            previous_revenue = historical_data.get('previous_revenue', 0)
            
            if previous_revenue > 0:
                return (current_revenue - previous_revenue) / previous_revenue
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"Failed to calculate growth rate: {e}")
            return 0.0

    async def _identify_revenue_drivers(self, historical_data: Dict[str, Any]) -> List[str]:
        """Identify key revenue drivers"""
        try:
            drivers = []
            
            if historical_data.get('customer_count', 0) > 100:
                drivers.append("Large customer base")
            
            if historical_data.get('avg_customer_value', 0) > 1000:
                drivers.append("High customer value")
            
            if historical_data.get('growth_rate', 0) > 0.1:
                drivers.append("Strong growth momentum")
            
            if historical_data.get('churn_rate', 1) < 0.05:
                drivers.append("Low churn rate")
            
            return drivers

        except Exception as e:
            self.logger.error(f"Failed to identify revenue drivers: {e}")
            return ["Customer growth"]

    async def _identify_revenue_risks(self, historical_data: Dict[str, Any]) -> List[str]:
        """Identify revenue risks"""
        try:
            risks = []
            
            if historical_data.get('churn_rate', 0) > 0.1:
                risks.append("High customer churn")
            
            if historical_data.get('acquisition_cost', 0) > 500:
                risks.append("High customer acquisition cost")
            
            if historical_data.get('growth_rate', 0) < 0:
                risks.append("Declining revenue")
            
            if historical_data.get('customer_count', 0) < 50:
                risks.append("Small customer base")
            
            return risks

        except Exception as e:
            self.logger.error(f"Failed to identify revenue risks: {e}")
            return ["Market competition"]

    async def _generate_revenue_recommendations(self, historical_data: Dict[str, Any], predicted_revenue: float) -> List[str]:
        """Generate revenue optimization recommendations"""
        try:
            recommendations = []
            
            if historical_data.get('churn_rate', 0) > 0.05:
                recommendations.append("Implement customer retention strategies")
            
            if historical_data.get('acquisition_cost', 0) > 300:
                recommendations.append("Optimize customer acquisition channels")
            
            if historical_data.get('avg_customer_value', 0) < 500:
                recommendations.append("Focus on increasing customer lifetime value")
            
            if predicted_revenue < historical_data.get('current_revenue', 0):
                recommendations.append("Review pricing strategy and value proposition")
            
            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate revenue recommendations: {e}")
            return ["Focus on customer growth and retention"]

    def _prepare_training_data(self, model_name: str, data: List[Dict[str, Any]]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare training data for model"""
        try:
            X = []
            y = []
            
            for record in data:
                if model_name == 'call_outcome':
                    features = self._prepare_call_features(record)
                    if features is not None:
                        X.append(features.flatten())
                        y.append(record.get('outcome', 'partial'))
                elif model_name == 'optimal_time':
                    features = self._prepare_time_features(record)
                    if features is not None:
                        X.append(features.flatten())
                        y.append(record.get('success_score', 0.5))
                elif model_name == 'customer_behavior':
                    features = self._prepare_behavior_features(record)
                    if features is not None:
                        X.append(features.flatten())
                        y.append(record.get('segment', 'medium_value'))
                elif model_name == 'revenue_forecast':
                    features = self._prepare_revenue_features(record)
                    if features is not None:
                        X.append(features.flatten())
                        y.append(record.get('revenue', 0))
            
            if not X or not y:
                return None, None
            
            # Encode labels for classification models
            if model_name in ['call_outcome', 'customer_behavior']:
                y = self.label_encoders[model_name].fit_transform(y)
            
            return np.array(X), np.array(y)

        except Exception as e:
            self.logger.error(f"Failed to prepare training data for {model_name}: {e}")
            return None, None

    def _evaluate_model(self, model_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Evaluate model performance"""
        try:
            if model_name in ['call_outcome', 'customer_behavior']:
                return accuracy_score(y_true, y_pred)
            else:
                return r2_score(y_true, y_pred)

        except Exception as e:
            self.logger.error(f"Failed to evaluate model {model_name}: {e}")
            return 0.0

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        try:
            status = {}
            
            for model_name in self.models.keys():
                status[model_name] = {
                    'version': self.model_versions[model_name],
                    'last_training': self.last_training[model_name].isoformat(),
                    'is_trained': hasattr(self.models[model_name], 'feature_importances_'),
                    'prediction_count': len(self.prediction_history.get(model_name, []))
                }
            
            return status

        except Exception as e:
            self.logger.error(f"Failed to get model status: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    config = {
        'model_update_interval': 3600,
        'min_training_samples': 100,
        'prediction_confidence_threshold': 0.7,
        'feature_importance_threshold': 0.05
    }

    analytics = PredictiveAnalytics(config)
    print("Predictive Analytics initialized")

