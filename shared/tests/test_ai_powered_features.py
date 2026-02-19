"""
Tests for AI-Powered Features

This module tests the AI-powered features including:
- Intelligent call routing
- Real-time conversation analytics
- Automated call summarization
- AI-powered objection handling
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.shared.ai.ai_powered_features import (
    AIPoweredFeatures,
    CallOutcome,
    ObjectionType,
    ConversationSentiment,
    CallRoutingDecision,
    ConversationAnalytics,
    CallSummary,
    ObjectionResponse
)


class TestAIPoweredFeatures:
    """Test cases for AI-Powered Features"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'sentiment_threshold': 0.6,
            'engagement_threshold': 0.5,
            'objection_confidence_threshold': 0.7,
            'routing_confidence_threshold': 0.8
        }

    @pytest.fixture
    def ai_features(self, config):
        """AI features instance"""
        return AIPoweredFeatures(config)

    @pytest.fixture
    def call_id(self):
        """Test call ID"""
        return "test-call-123"

    @pytest.fixture
    def conversation_text(self):
        """Test conversation text"""
        return "Hello, I'm interested in your product but it seems expensive. Can you tell me more about the pricing?"

    @pytest.fixture
    def call_context(self):
        """Test call context"""
        return {
            'priority': 'high',
            'customer_tier': 'enterprise',
            'call_type': 'sales',
            'geographic_location': 'US',
            'expected_duration': 300
        }

    @pytest.fixture
    def available_providers(self):
        """Test available providers"""
        return ['provider_1', 'provider_2', 'provider_3']

    @pytest.mark.asyncio
    async def test_start_call_analytics(self, ai_features, call_id):
        """Test starting call analytics"""
        result = await ai_features.start_call_analytics(call_id)
        assert result is True
        assert call_id in ai_features.active_calls

    @pytest.mark.asyncio
    async def test_stop_call_analytics(self, ai_features, call_id):
        """Test stopping call analytics"""
        # Start analytics first
        await ai_features.start_call_analytics(call_id)
        
        # Stop analytics
        result = await ai_features.stop_call_analytics(call_id)
        assert result is True
        assert call_id not in ai_features.active_calls

    @pytest.mark.asyncio
    async def test_stop_call_analytics_nonexistent(self, ai_features, call_id):
        """Test stopping analytics for non-existent call"""
        result = await ai_features.stop_call_analytics(call_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_analyze_conversation(self, ai_features, call_id, conversation_text):
        """Test conversation analysis"""
        # Start analytics
        await ai_features.start_call_analytics(call_id)
        
        # Analyze conversation
        analytics = await ai_features.analyze_conversation(call_id, conversation_text)
        
        assert analytics is not None
        assert analytics.call_id == call_id
        assert analytics.sentiment in [ConversationSentiment.POSITIVE, ConversationSentiment.NEGATIVE, ConversationSentiment.NEUTRAL]
        assert analytics.sentiment_score >= 0.0
        assert analytics.engagement_level >= 0.0
        assert analytics.risk_score >= 0.0
        assert isinstance(analytics.key_topics, list)
        assert isinstance(analytics.action_items, list)

    @pytest.mark.asyncio
    async def test_analyze_conversation_no_analytics_started(self, ai_features, call_id, conversation_text):
        """Test conversation analysis without starting analytics"""
        analytics = await ai_features.analyze_conversation(call_id, conversation_text)
        assert analytics is None

    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, ai_features):
        """Test sentiment analysis with positive text"""
        text = "This is great! I love this product and it's amazing."
        result = await ai_features._analyze_sentiment(text)
        
        assert result['sentiment'] == ConversationSentiment.POSITIVE
        assert result['score'] > 0.0
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, ai_features):
        """Test sentiment analysis with negative text"""
        text = "This is terrible! I hate this product and it's awful."
        result = await ai_features._analyze_sentiment(text)
        
        assert result['sentiment'] == ConversationSentiment.NEGATIVE
        assert result['score'] > 0.0
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, ai_features):
        """Test sentiment analysis with neutral text"""
        text = "This is a product. It has features."
        result = await ai_features._analyze_sentiment(text)
        
        assert result['sentiment'] == ConversationSentiment.NEUTRAL
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_detect_objections_price(self, ai_features):
        """Test objection detection for price"""
        text = "This is too expensive and costs too much money."
        result = await ai_features._detect_objections(text)
        
        assert result['detected'] is True
        assert result['type'] == ObjectionType.PRICE
        assert result['confidence'] > 0.0

    @pytest.mark.asyncio
    async def test_detect_objections_time(self, ai_features):
        """Test objection detection for time"""
        text = "I'm too busy right now, maybe later or tomorrow."
        result = await ai_features._detect_objections(text)
        
        assert result['detected'] is True
        assert result['type'] == ObjectionType.TIME
        assert result['confidence'] > 0.0

    @pytest.mark.asyncio
    async def test_detect_objections_no_objection(self, ai_features):
        """Test objection detection with no objection"""
        text = "This is a normal conversation without any objections."
        result = await ai_features._detect_objections(text)
        
        assert result['detected'] is False
        assert result['type'] is None
        assert result['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_extract_topics(self, ai_features):
        """Test topic extraction"""
        text = "I'm interested in your product features and pricing options. Can you tell me more about the implementation?"
        topics = await ai_features._extract_topics(text)
        
        assert isinstance(topics, list)
        assert len(topics) <= 5
        assert all(isinstance(topic, str) for topic in topics)

    @pytest.mark.asyncio
    async def test_calculate_engagement(self, ai_features, call_id):
        """Test engagement calculation"""
        # Start analytics
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        # Add some conversation history
        for i in range(5):
            call_state['conversation_history'].append({
                'text': f"Message {i} with some content",
                'timestamp': datetime.utcnow() + timedelta(seconds=i)
            })
        
        engagement = await ai_features._calculate_engagement(call_state)
        assert 0.0 <= engagement <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_engagement_empty_history(self, ai_features, call_id):
        """Test engagement calculation with empty history"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        engagement = await ai_features._calculate_engagement(call_state)
        assert engagement == 0.0

    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, ai_features, call_id):
        """Test risk score calculation"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        # Add some sentiment history
        call_state['sentiment_history'].append({
            'sentiment': ConversationSentiment.NEGATIVE,
            'score': 0.8,
            'timestamp': datetime.utcnow()
        })
        
        objection_result = {
            'detected': True,
            'type': ObjectionType.PRICE,
            'confidence': 0.8,
            'all_objections': []
        }
        
        risk_score = await ai_features._calculate_risk_score(call_state, objection_result)
        assert 0.0 <= risk_score <= 1.0

    @pytest.mark.asyncio
    async def test_extract_action_items(self, ai_features):
        """Test action item extraction"""
        text = "I need to review this. I will call you back. We should schedule a meeting."
        action_items = await ai_features._extract_action_items(text)
        
        assert isinstance(action_items, list)
        assert len(action_items) <= 3
        assert all(isinstance(item, str) for item in action_items)

    @pytest.mark.asyncio
    async def test_generate_call_summary(self, ai_features, call_id):
        """Test call summary generation"""
        # Start analytics
        await ai_features.start_call_analytics(call_id)
        
        # Add conversation history
        call_state = ai_features.active_calls[call_id]
        call_state['conversation_history'].append({
            'text': "Hello, I'm interested in your product. It looks great!",
            'timestamp': datetime.utcnow()
        })
        call_state['conversation_history'].append({
            'text': "The price seems reasonable. I need to think about it.",
            'timestamp': datetime.utcnow()
        })
        
        # Generate summary
        summary = await ai_features.generate_call_summary(call_id)
        
        assert summary is not None
        assert summary.call_id == call_id
        assert isinstance(summary.summary, str)
        assert isinstance(summary.key_points, list)
        assert isinstance(summary.action_items, list)
        assert summary.sentiment in [ConversationSentiment.POSITIVE, ConversationSentiment.NEGATIVE, ConversationSentiment.NEUTRAL]
        assert summary.outcome in [CallOutcome.SUCCESS, CallOutcome.FAILURE, CallOutcome.PARTIAL]
        assert summary.duration >= 0.0
        assert isinstance(summary.participants, list)
        assert isinstance(summary.topics_discussed, list)
        assert isinstance(summary.objections_handled, list)
        assert isinstance(summary.next_steps, list)

    @pytest.mark.asyncio
    async def test_generate_call_summary_no_conversation(self, ai_features, call_id):
        """Test call summary generation with no conversation"""
        await ai_features.start_call_analytics(call_id)
        
        summary = await ai_features.generate_call_summary(call_id)
        assert summary is None

    @pytest.mark.asyncio
    async def test_generate_summary(self, ai_features):
        """Test summary generation"""
        text = "This is a long conversation about a product. The customer is interested. They have questions about pricing. The product seems to meet their needs."
        summary = await ai_features._generate_summary(text)
        
        assert isinstance(summary, str)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_extract_key_points(self, ai_features):
        """Test key point extraction"""
        text = "This is important. The main thing is quality. The key factor is price. This is critical for success."
        key_points = await ai_features._extract_key_points(text)
        
        assert isinstance(key_points, list)
        assert len(key_points) <= 5
        assert all(isinstance(point, str) for point in key_points)

    @pytest.mark.asyncio
    async def test_determine_call_outcome_success(self, ai_features, call_id):
        """Test call outcome determination for success"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        # Add positive sentiment history
        for _ in range(3):
            call_state['sentiment_history'].append({
                'sentiment': ConversationSentiment.POSITIVE,
                'score': 0.8,
                'timestamp': datetime.utcnow()
            })
        
        outcome = await ai_features._determine_call_outcome(call_state)
        assert outcome == CallOutcome.SUCCESS

    @pytest.mark.asyncio
    async def test_determine_call_outcome_failure(self, ai_features, call_id):
        """Test call outcome determination for failure"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        # Add negative sentiment history
        for _ in range(3):
            call_state['sentiment_history'].append({
                'sentiment': ConversationSentiment.NEGATIVE,
                'score': 0.8,
                'timestamp': datetime.utcnow()
            })
        
        outcome = await ai_features._determine_call_outcome(call_state)
        assert outcome == CallOutcome.FAILURE

    @pytest.mark.asyncio
    async def test_generate_next_steps_success(self, ai_features, call_id):
        """Test next steps generation for success"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        next_steps = await ai_features._generate_next_steps(call_state, CallOutcome.SUCCESS)
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert all(isinstance(step, str) for step in next_steps)

    @pytest.mark.asyncio
    async def test_generate_next_steps_failure(self, ai_features, call_id):
        """Test next steps generation for failure"""
        await ai_features.start_call_analytics(call_id)
        call_state = ai_features.active_calls[call_id]
        
        next_steps = await ai_features._generate_next_steps(call_state, CallOutcome.FAILURE)
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert all(isinstance(step, str) for step in next_steps)

    @pytest.mark.asyncio
    async def test_generate_objection_response_price(self, ai_features):
        """Test objection response generation for price"""
        response = await ai_features.generate_objection_response(ObjectionType.PRICE, "The price is too high")
        
        assert response is not None
        assert response.objection_type == ObjectionType.PRICE
        assert isinstance(response.response_text, str)
        assert response.confidence > 0.0
        assert isinstance(response.suggested_approach, str)
        assert isinstance(response.follow_up_questions, list)
        assert response.success_probability > 0.0

    @pytest.mark.asyncio
    async def test_generate_objection_response_time(self, ai_features):
        """Test objection response generation for time"""
        response = await ai_features.generate_objection_response(ObjectionType.TIME, "I'm too busy")
        
        assert response is not None
        assert response.objection_type == ObjectionType.TIME
        assert isinstance(response.response_text, str)
        assert response.confidence > 0.0
        assert isinstance(response.suggested_approach, str)
        assert isinstance(response.follow_up_questions, list)
        assert response.success_probability > 0.0

    @pytest.mark.asyncio
    async def test_generate_objection_response_unknown_type(self, ai_features):
        """Test objection response generation for unknown type"""
        # Create a custom objection type that's not in the predefined responses
        class CustomObjectionType:
            pass
        
        response = await ai_features.generate_objection_response(CustomObjectionType(), "Custom objection")
        assert response is None

    @pytest.mark.asyncio
    async def test_intelligent_call_routing(self, ai_features, call_context, available_providers):
        """Test intelligent call routing"""
        decision = await ai_features.intelligent_call_routing(call_context, available_providers)
        
        assert decision is not None
        assert decision.provider_id in available_providers
        assert 0.0 <= decision.confidence <= 1.0
        assert isinstance(decision.reasoning, str)
        assert isinstance(decision.factors, dict)
        assert 'timestamp' in decision.__dict__

    @pytest.mark.asyncio
    async def test_intelligent_call_routing_no_providers(self, ai_features, call_context):
        """Test intelligent call routing with no providers"""
        decision = await ai_features.intelligent_call_routing(call_context, [])
        assert decision is None

    @pytest.mark.asyncio
    async def test_analyze_routing_factors(self, ai_features, call_context):
        """Test routing factors analysis"""
        factors = await ai_features._analyze_routing_factors(call_context)
        
        assert isinstance(factors, dict)
        assert 'priority' in factors
        assert 'geographic_location' in factors
        assert 'call_type' in factors
        assert 'customer_tier' in factors
        assert 'time_of_day' in factors
        assert 'expected_duration' in factors
        assert all(0.0 <= value <= 1.0 for value in factors.values())

    @pytest.mark.asyncio
    async def test_calculate_provider_score(self, ai_features):
        """Test provider score calculation"""
        factors = {
            'priority': 0.8,
            'customer_tier': 0.9,
            'geographic_location': 0.3,
            'call_type': 0.6,
            'time_of_day': 0.2,
            'expected_duration': 0.4
        }
        
        score = await ai_features._calculate_provider_score('provider_1', factors)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_routing_reasoning(self, ai_features):
        """Test routing reasoning generation"""
        factors = {
            'priority': 0.8,
            'customer_tier': 0.9,
            'call_type': 'sales'
        }
        
        reasoning = await ai_features._generate_routing_reasoning('provider_1', factors, 0.85)
        assert isinstance(reasoning, str)
        assert 'provider_1' in reasoning
        assert '0.85' in reasoning

    @pytest.mark.asyncio
    async def test_register_analytics_callback(self, ai_features, call_id):
        """Test analytics callback registration"""
        def test_callback(analytics):
            pass
        
        ai_features.register_analytics_callback(call_id, test_callback)
        assert call_id in ai_features.analytics_callbacks
        assert test_callback in ai_features.analytics_callbacks[call_id]

    @pytest.mark.asyncio
    async def test_unregister_analytics_callback(self, ai_features, call_id):
        """Test analytics callback unregistration"""
        def test_callback(analytics):
            pass
        
        # Register first
        ai_features.register_analytics_callback(call_id, test_callback)
        
        # Unregister
        ai_features.unregister_analytics_callback(call_id, test_callback)
        assert test_callback not in ai_features.analytics_callbacks[call_id]

    @pytest.mark.asyncio
    async def test_emit_analytics_event(self, ai_features, call_id):
        """Test analytics event emission"""
        # Start analytics
        await ai_features.start_call_analytics(call_id)
        
        # Create test analytics
        analytics = ConversationAnalytics(
            call_id=call_id,
            sentiment=ConversationSentiment.POSITIVE,
            sentiment_score=0.8,
            engagement_level=0.7,
            objection_detected=False,
            objection_type=None,
            objection_confidence=0.0,
            key_topics=['product', 'pricing'],
            action_items=['follow up'],
            risk_score=0.2,
            timestamp=datetime.utcnow()
        )
        
        # Test emission (should not raise errors)
        await ai_features._emit_analytics_event(call_id, analytics)

    @pytest.mark.asyncio
    async def test_emit_analytics_event_with_callback(self, ai_features, call_id):
        """Test analytics event emission with callback"""
        # Start analytics
        await ai_features.start_call_analytics(call_id)
        
        # Create test callback
        callback_called = False
        def test_callback(analytics):
            nonlocal callback_called
            callback_called = True
            assert analytics.call_id == call_id
        
        # Register callback
        ai_features.register_analytics_callback(call_id, test_callback)
        
        # Create test analytics
        analytics = ConversationAnalytics(
            call_id=call_id,
            sentiment=ConversationSentiment.POSITIVE,
            sentiment_score=0.8,
            engagement_level=0.7,
            objection_detected=False,
            objection_type=None,
            objection_confidence=0.0,
            key_topics=['product', 'pricing'],
            action_items=['follow up'],
            risk_score=0.2,
            timestamp=datetime.utcnow()
        )
        
        # Emit event
        await ai_features._emit_analytics_event(call_id, analytics)
        assert callback_called

    def test_call_outcome_enum(self):
        """Test CallOutcome enum values"""
        assert CallOutcome.SUCCESS.value == "success"
        assert CallOutcome.FAILURE.value == "failure"
        assert CallOutcome.PARTIAL.value == "partial"
        assert CallOutcome.NO_ANSWER.value == "no_answer"
        assert CallOutcome.BUSY.value == "busy"
        assert CallOutcome.VOICEMAIL.value == "voicemail"

    def test_objection_type_enum(self):
        """Test ObjectionType enum values"""
        assert ObjectionType.PRICE.value == "price"
        assert ObjectionType.TIME.value == "time"
        assert ObjectionType.NEED.value == "need"
        assert ObjectionType.AUTHORITY.value == "authority"
        assert ObjectionType.COMPETITION.value == "competition"
        assert ObjectionType.QUALITY.value == "quality"
        assert ObjectionType.TRUST.value == "trust"
        assert ObjectionType.URGENCY.value == "urgency"

    def test_conversation_sentiment_enum(self):
        """Test ConversationSentiment enum values"""
        assert ConversationSentiment.POSITIVE.value == "positive"
        assert ConversationSentiment.NEGATIVE.value == "negative"
        assert ConversationSentiment.NEUTRAL.value == "neutral"
        assert ConversationSentiment.MIXED.value == "mixed"

    def test_call_routing_decision_dataclass(self):
        """Test CallRoutingDecision dataclass"""
        decision = CallRoutingDecision(
            provider_id="test_provider",
            confidence=0.85,
            reasoning="Test reasoning",
            factors={'priority': 0.8},
            timestamp=datetime.utcnow()
        )
        
        assert decision.provider_id == "test_provider"
        assert decision.confidence == 0.85
        assert decision.reasoning == "Test reasoning"
        assert decision.factors == {'priority': 0.8}

    def test_conversation_analytics_dataclass(self):
        """Test ConversationAnalytics dataclass"""
        analytics = ConversationAnalytics(
            call_id="test_call",
            sentiment=ConversationSentiment.POSITIVE,
            sentiment_score=0.8,
            engagement_level=0.7,
            objection_detected=False,
            objection_type=None,
            objection_confidence=0.0,
            key_topics=['topic1', 'topic2'],
            action_items=['action1'],
            risk_score=0.2,
            timestamp=datetime.utcnow()
        )
        
        assert analytics.call_id == "test_call"
        assert analytics.sentiment == ConversationSentiment.POSITIVE
        assert analytics.sentiment_score == 0.8
        assert analytics.engagement_level == 0.7
        assert analytics.objection_detected is False
        assert analytics.key_topics == ['topic1', 'topic2']
        assert analytics.action_items == ['action1']
        assert analytics.risk_score == 0.2

    def test_call_summary_dataclass(self):
        """Test CallSummary dataclass"""
        summary = CallSummary(
            call_id="test_call",
            summary="Test summary",
            key_points=['point1', 'point2'],
            action_items=['action1'],
            sentiment=ConversationSentiment.POSITIVE,
            outcome=CallOutcome.SUCCESS,
            duration=300.0,
            participants=['Caller', 'Agent'],
            topics_discussed=['topic1'],
            objections_handled=['objection1'],
            next_steps=['step1'],
            timestamp=datetime.utcnow()
        )
        
        assert summary.call_id == "test_call"
        assert summary.summary == "Test summary"
        assert summary.key_points == ['point1', 'point2']
        assert summary.action_items == ['action1']
        assert summary.sentiment == ConversationSentiment.POSITIVE
        assert summary.outcome == CallOutcome.SUCCESS
        assert summary.duration == 300.0
        assert summary.participants == ['Caller', 'Agent']
        assert summary.topics_discussed == ['topic1']
        assert summary.objections_handled == ['objection1']
        assert summary.next_steps == ['step1']

    def test_objection_response_dataclass(self):
        """Test ObjectionResponse dataclass"""
        response = ObjectionResponse(
            objection_type=ObjectionType.PRICE,
            response_text="Test response",
            confidence=0.85,
            suggested_approach="Test approach",
            follow_up_questions=['question1', 'question2'],
            success_probability=0.75,
            timestamp=datetime.utcnow()
        )
        
        assert response.objection_type == ObjectionType.PRICE
        assert response.response_text == "Test response"
        assert response.confidence == 0.85
        assert response.suggested_approach == "Test approach"
        assert response.follow_up_questions == ['question1', 'question2']
        assert response.success_probability == 0.75


if __name__ == "__main__":
    pytest.main([__file__])
