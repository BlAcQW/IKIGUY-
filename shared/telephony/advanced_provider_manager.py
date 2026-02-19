"""
Advanced Provider Manager

This module provides advanced provider management features including:
- Real-time provider switching
- Quality-based routing
- Cost optimization algorithms
- Geographic routing optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict, deque

from .interfaces import TelephonyPort, TelephonyEvent
from .models import CallContext, ProviderSettings, ProviderHealth


class RoutingStrategy(Enum):
    """Routing strategy types"""
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    BALANCED = "balanced"
    GEOGRAPHIC = "geographic"
    FAILOVER = "failover"


class ProviderQuality(Enum):
    """Provider quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


@dataclass
class ProviderMetrics:
    """Provider performance metrics"""
    provider_id: str
    success_rate: float
    average_response_time: float
    cost_per_minute: float
    error_rate: float
    uptime_percentage: float
    last_updated: datetime
    call_count: int
    total_duration: float
    geographic_coverage: List[str]
    supported_features: List[str]


@dataclass
class RoutingDecision:
    """Routing decision result"""
    provider_id: str
    strategy: RoutingStrategy
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_quality: ProviderQuality


class AdvancedProviderManager:
    """Advanced provider management with intelligent routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[str, TelephonyPort] = {}
        self.health_status: Dict[str, bool] = {}
        self.metrics: Dict[str, ProviderMetrics] = {}
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.call_history: deque = deque(maxlen=10000)  # Keep last 10k calls
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Configuration
        self.health_check_interval = config.get('health_check_interval', 30)  # seconds
        self.metrics_window = config.get('metrics_window', 3600)  # 1 hour
        self.min_success_rate = config.get('min_success_rate', 0.95)
        self.max_response_time = config.get('max_response_time', 2000)  # ms
        self.cost_weight = config.get('cost_weight', 0.3)
        self.quality_weight = config.get('quality_weight', 0.4)
        self.geographic_weight = config.get('geographic_weight', 0.3)
        
        # Start background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_update_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the advanced provider manager"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._metrics_update_task = asyncio.create_task(self._metrics_update_loop())
        self.logger.info("Advanced provider manager started")
    
    async def stop(self):
        """Stop the advanced provider manager"""
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._metrics_update_task:
            self._metrics_update_task.cancel()
        self.logger.info("Advanced provider manager stopped")
    
    async def register_provider(self, name: str, provider: TelephonyPort) -> None:
        """Register a telephony provider"""
        self.providers[name] = provider
        self.health_status[name] = True
        
        # Initialize metrics
        self.metrics[name] = ProviderMetrics(
            provider_id=name,
            success_rate=1.0,
            average_response_time=0.0,
            cost_per_minute=0.0,
            error_rate=0.0,
            uptime_percentage=100.0,
            last_updated=datetime.utcnow(),
            call_count=0,
            total_duration=0.0,
            geographic_coverage=[],
            supported_features=[]
        )
        
        self.logger.info(f"Registered provider: {name}")
    
    async def unregister_provider(self, name: str) -> None:
        """Unregister a telephony provider"""
        if name in self.providers:
            del self.providers[name]
        if name in self.health_status:
            del self.health_status[name]
        if name in self.metrics:
            del self.metrics[name]
        
        self.logger.info(f"Unregistered provider: {name}")
    
    async def get_best_provider(self, context: CallContext) -> RoutingDecision:
        """
        Select best provider based on advanced routing algorithms
        
        Args:
            context: Call context with destination, preferences, etc.
            
        Returns:
            RoutingDecision: Best provider selection with reasoning
        """
        try:
            # Get available providers
            available_providers = [
                provider_id for provider_id, is_healthy in self.health_status.items()
                if is_healthy and provider_id in self.providers
            ]
            
            if not available_providers:
                raise ValueError("No healthy providers available")
            
            # Determine routing strategy based on context
            strategy = self._determine_routing_strategy(context)
            
            # Get provider scores based on strategy
            provider_scores = await self._calculate_provider_scores(
                available_providers, context, strategy
            )
            
            if not provider_scores:
                raise ValueError("No providers meet the criteria")
            
            # Select best provider
            best_provider_id = max(provider_scores, key=lambda x: x[1])[0]
            best_score = max(provider_scores, key=lambda x: x[1])[1]
            
            # Get provider metrics for decision details
            provider_metrics = self.metrics.get(best_provider_id)
            
            # Calculate estimated cost and quality
            estimated_cost = provider_metrics.cost_per_minute if provider_metrics else 0.0
            estimated_quality = self._calculate_quality_level(provider_metrics) if provider_metrics else ProviderQuality.UNKNOWN
            
            # Generate reasoning
            reasoning = self._generate_routing_reasoning(
                best_provider_id, strategy, provider_metrics, context
            )
            
            return RoutingDecision(
                provider_id=best_provider_id,
                strategy=strategy,
                confidence=best_score,
                reasoning=reasoning,
                estimated_cost=estimated_cost,
                estimated_quality=estimated_quality
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get best provider: {e}")
            # Fallback to first available provider
            available_providers = list(self.providers.keys())
            if available_providers:
                return RoutingDecision(
                    provider_id=available_providers[0],
                    strategy=RoutingStrategy.FAILOVER,
                    confidence=0.5,
                    reasoning=f"Fallback due to error: {str(e)}",
                    estimated_cost=0.0,
                    estimated_quality=ProviderQuality.UNKNOWN
                )
            raise
    
    async def switch_provider(self, call_id: str, new_provider: str, reason: str = "") -> bool:
        """
        Switch provider for active call with real-time switching
        
        Args:
            call_id: Unique call identifier
            new_provider: Name of new provider to switch to
            reason: Reason for switching
            
        Returns:
            bool: True if provider switch was successful
        """
        try:
            if call_id not in self.active_calls:
                raise ValueError(f"Call {call_id} not found")
            
            if new_provider not in self.providers:
                raise ValueError(f"Provider {new_provider} not found")
            
            current_call = self.active_calls[call_id]
            old_provider = current_call.get('provider_id')
            
            # Perform provider switch
            success = await self._perform_provider_switch(call_id, old_provider, new_provider)
            
            if success:
                # Update call information
                current_call['provider_id'] = new_provider
                current_call['provider_switches'] = current_call.get('provider_switches', 0) + 1
                current_call['switch_history'] = current_call.get('switch_history', [])
                current_call['switch_history'].append({
                    'timestamp': datetime.utcnow(),
                    'from_provider': old_provider,
                    'to_provider': new_provider,
                    'reason': reason
                })
                
                self.logger.info(f"Successfully switched call {call_id} from {old_provider} to {new_provider}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to switch provider for call {call_id}: {e}")
            return False
    
    async def get_provider_health(self, provider_id: str) -> Dict[str, Any]:
        """Get detailed provider health status"""
        try:
            if provider_id not in self.providers:
                return {'error': 'Provider not found'}
            
            provider = self.providers[provider_id]
            metrics = self.metrics.get(provider_id)
            
            # Perform health check
            health = await provider.health_check()
            
            # Combine with metrics
            health_data = {
                'provider_id': provider_id,
                'is_healthy': health.is_healthy,
                'last_check': health.last_check,
                'response_time_ms': health.response_time_ms,
                'cost_per_minute': health.cost_per_minute,
                'supported_regions': health.supported_regions,
                'features': health.features,
                'metrics': {
                    'success_rate': metrics.success_rate if metrics else 0.0,
                    'average_response_time': metrics.average_response_time if metrics else 0.0,
                    'error_rate': metrics.error_rate if metrics else 0.0,
                    'uptime_percentage': metrics.uptime_percentage if metrics else 0.0,
                    'call_count': metrics.call_count if metrics else 0,
                    'total_duration': metrics.total_duration if metrics else 0.0
                } if metrics else {}
            }
            
            return health_data
            
        except Exception as e:
            self.logger.error(f"Failed to get health for provider {provider_id}: {e}")
            return {'error': str(e)}
    
    async def get_routing_analytics(self) -> Dict[str, Any]:
        """Get routing analytics and insights"""
        try:
            analytics = {
                'total_calls': len(self.call_history),
                'active_calls': len(self.active_calls),
                'provider_performance': {},
                'routing_decisions': defaultdict(int),
                'switch_events': 0,
                'average_call_duration': 0.0,
                'success_rate_by_provider': {},
                'cost_analysis': {},
                'geographic_distribution': defaultdict(int)
            }
            
            # Calculate provider performance
            for provider_id, metrics in self.metrics.items():
                analytics['provider_performance'][provider_id] = {
                    'success_rate': metrics.success_rate,
                    'average_response_time': metrics.average_response_time,
                    'cost_per_minute': metrics.cost_per_minute,
                    'error_rate': metrics.error_rate,
                    'uptime_percentage': metrics.uptime_percentage,
                    'call_count': metrics.call_count,
                    'total_duration': metrics.total_duration
                }
            
            # Calculate routing decisions
            for call in self.call_history:
                strategy = call.get('routing_strategy', 'unknown')
                analytics['routing_decisions'][strategy] += 1
                
                if call.get('provider_switches', 0) > 0:
                    analytics['switch_events'] += call['provider_switches']
                
                duration = call.get('duration', 0)
                if duration > 0:
                    analytics['average_call_duration'] += duration
            
            if analytics['total_calls'] > 0:
                analytics['average_call_duration'] /= analytics['total_calls']
            
            # Calculate success rates
            for provider_id in self.providers.keys():
                provider_calls = [c for c in self.call_history if c.get('provider_id') == provider_id]
                if provider_calls:
                    successful_calls = [c for c in provider_calls if c.get('status') == 'completed']
                    analytics['success_rate_by_provider'][provider_id] = len(successful_calls) / len(provider_calls)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get routing analytics: {e}")
            return {'error': str(e)}
    
    def _determine_routing_strategy(self, context: CallContext) -> RoutingStrategy:
        """Determine routing strategy based on call context"""
        cost_pref = context.cost_preference
        quality_pref = context.quality_preference
        geographic_region = context.geographic_region
        
        # Check geographic routing first
        if geographic_region and geographic_region != 'global':
            return RoutingStrategy.GEOGRAPHIC
        elif cost_pref == 'minimal' and quality_pref == 'minimal':
            return RoutingStrategy.COST_OPTIMIZED
        elif quality_pref == 'maximum' and cost_pref == 'maximum':
            return RoutingStrategy.QUALITY_OPTIMIZED
        else:
            return RoutingStrategy.BALANCED
    
    async def _calculate_provider_scores(
        self, 
        available_providers: List[str], 
        context: CallContext, 
        strategy: RoutingStrategy
    ) -> List[Tuple[str, float]]:
        """Calculate provider scores based on routing strategy"""
        scores = []
        
        for provider_id in available_providers:
            metrics = self.metrics.get(provider_id)
            if not metrics:
                continue
            
            # Check minimum requirements - use default values if not set
            success_rate = metrics.success_rate if metrics.success_rate > 0 else 1.0
            response_time = metrics.average_response_time if metrics.average_response_time > 0 else 100.0
            
            if success_rate < self.min_success_rate:
                continue
            
            if response_time > self.max_response_time:
                continue
            
            # Calculate score based on strategy
            if strategy == RoutingStrategy.COST_OPTIMIZED:
                score = self._calculate_cost_score(metrics, context)
            elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
                score = self._calculate_quality_score(metrics, context)
            elif strategy == RoutingStrategy.GEOGRAPHIC:
                score = self._calculate_geographic_score(metrics, context)
            elif strategy == RoutingStrategy.BALANCED:
                score = self._calculate_balanced_score(metrics, context)
            else:
                score = 0.5  # Default score
            
            scores.append((provider_id, score))
        
        return scores
    
    def _calculate_cost_score(self, metrics: ProviderMetrics, context: CallContext) -> float:
        """Calculate cost-optimized score"""
        # Lower cost = higher score
        costs = [m.cost_per_minute for m in self.metrics.values() if m.cost_per_minute > 0]
        if costs:
            max_cost = max(costs)
            if max_cost > 0:
                cost_score = 1.0 - (metrics.cost_per_minute / max_cost)
            else:
                cost_score = 1.0
        else:
            cost_score = 1.0
        
        # Factor in success rate
        success_score = metrics.success_rate if metrics.success_rate > 0 else 1.0
        
        # Weighted combination
        return (cost_score * 0.7) + (success_score * 0.3)
    
    def _calculate_quality_score(self, metrics: ProviderMetrics, context: CallContext) -> float:
        """Calculate quality-optimized score"""
        # Higher success rate = higher score
        success_score = metrics.success_rate if metrics.success_rate > 0 else 1.0
        
        # Lower response time = higher score
        response_times = [m.average_response_time for m in self.metrics.values() if m.average_response_time > 0]
        if response_times:
            max_response_time = max(response_times)
            if max_response_time > 0:
                response_score = 1.0 - (metrics.average_response_time / max_response_time)
            else:
                response_score = 1.0
        else:
            response_score = 1.0
        
        # Higher uptime = higher score
        uptime_score = metrics.uptime_percentage / 100.0
        
        # Weighted combination
        return (success_score * 0.5) + (response_score * 0.3) + (uptime_score * 0.2)
    
    def _calculate_geographic_score(self, metrics: ProviderMetrics, context: CallContext) -> float:
        """Calculate geographic routing score"""
        if not context.geographic_region:
            return 0.5
        
        # Check if provider supports the geographic region
        if context.geographic_region in metrics.geographic_coverage:
            geographic_score = 1.0
        else:
            geographic_score = 0.0
        
        # Factor in quality and cost
        quality_score = self._calculate_quality_score(metrics, context)
        cost_score = self._calculate_cost_score(metrics, context)
        
        # Weighted combination with high geographic weight
        return (geographic_score * 0.6) + (quality_score * 0.25) + (cost_score * 0.15)
    
    def _calculate_balanced_score(self, metrics: ProviderMetrics, context: CallContext) -> float:
        """Calculate balanced score considering all factors"""
        cost_score = self._calculate_cost_score(metrics, context)
        quality_score = self._calculate_quality_score(metrics, context)
        
        # Weighted combination based on preferences
        if context.cost_preference == 'minimal':
            cost_weight = 0.6
            quality_weight = 0.4
        elif context.quality_preference == 'maximum':
            cost_weight = 0.3
            quality_weight = 0.7
        else:
            cost_weight = 0.5
            quality_weight = 0.5
        
        return (cost_score * cost_weight) + (quality_score * quality_weight)
    
    def _calculate_quality_level(self, metrics: ProviderMetrics) -> ProviderQuality:
        """Calculate quality level based on metrics"""
        if metrics.success_rate >= 0.98 and metrics.average_response_time <= 500:
            return ProviderQuality.EXCELLENT
        elif metrics.success_rate >= 0.95 and metrics.average_response_time <= 1000:
            return ProviderQuality.GOOD
        elif metrics.success_rate >= 0.90 and metrics.average_response_time <= 2000:
            return ProviderQuality.FAIR
        elif metrics.success_rate < 0.90 or metrics.average_response_time > 2000:
            return ProviderQuality.POOR
        else:
            return ProviderQuality.UNKNOWN
    
    def _generate_routing_reasoning(
        self, 
        provider_id: str, 
        strategy: RoutingStrategy, 
        metrics: ProviderMetrics, 
        context: CallContext
    ) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasons = []
        
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            reasons.append(f"Cost-optimized routing selected {provider_id}")
            reasons.append(f"Cost per minute: ${metrics.cost_per_minute:.4f}")
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            reasons.append(f"Quality-optimized routing selected {provider_id}")
            reasons.append(f"Success rate: {metrics.success_rate:.1%}")
            reasons.append(f"Response time: {metrics.average_response_time:.0f}ms")
        elif strategy == RoutingStrategy.GEOGRAPHIC:
            reasons.append(f"Geographic routing selected {provider_id}")
            reasons.append(f"Supports region: {context.geographic_region}")
        elif strategy == RoutingStrategy.BALANCED:
            reasons.append(f"Balanced routing selected {provider_id}")
            reasons.append(f"Balanced cost and quality preferences")
        
        reasons.append(f"Overall success rate: {metrics.success_rate:.1%}")
        reasons.append(f"Uptime: {metrics.uptime_percentage:.1f}%")
        
        return "; ".join(reasons)
    
    async def _perform_provider_switch(self, call_id: str, old_provider: str, new_provider: str) -> bool:
        """Perform the actual provider switch for a call"""
        try:
            # This is a simplified implementation
            # In a real system, this would involve:
            # 1. Bridging the call to the new provider
            # 2. Maintaining call state
            # 3. Handling any audio/video streams
            # 4. Ensuring seamless transition
            
            # For now, we'll simulate a successful switch
            await asyncio.sleep(0.1)  # Simulate switch time
            
            # Update metrics
            if old_provider in self.metrics:
                self.metrics[old_provider].call_count -= 1
            
            if new_provider in self.metrics:
                self.metrics[new_provider].call_count += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to perform provider switch: {e}")
            return False
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                for provider_id, provider in self.providers.items():
                    try:
                        health = await provider.health_check()
                        self.health_status[provider_id] = health.is_healthy
                        
                        # Update metrics
                        if provider_id in self.metrics:
                            self.metrics[provider_id].uptime_percentage = (
                                100.0 if health.is_healthy else 0.0
                            )
                            self.metrics[provider_id].last_updated = datetime.utcnow()
                    
                    except Exception as e:
                        self.logger.error(f"Health check failed for {provider_id}: {e}")
                        self.health_status[provider_id] = False
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _metrics_update_loop(self):
        """Background metrics update loop"""
        while True:
            try:
                # Update metrics based on call history
                cutoff_time = datetime.utcnow() - timedelta(seconds=self.metrics_window)
                
                for provider_id in self.providers.keys():
                    if provider_id not in self.metrics:
                        continue
                    
                    # Get recent calls for this provider
                    recent_calls = [
                        call for call in self.call_history
                        if call.get('provider_id') == provider_id and 
                        call.get('start_time', datetime.utcnow()) > cutoff_time
                    ]
                    
                    if recent_calls:
                        # Calculate success rate
                        successful_calls = [c for c in recent_calls if c.get('status') == 'completed']
                        success_rate = len(successful_calls) / len(recent_calls)
                        
                        # Calculate average response time
                        response_times = [c.get('response_time', 0) for c in recent_calls if c.get('response_time')]
                        avg_response_time = statistics.mean(response_times) if response_times else 0.0
                        
                        # Calculate error rate
                        error_calls = [c for c in recent_calls if c.get('status') == 'failed']
                        error_rate = len(error_calls) / len(recent_calls)
                        
                        # Update metrics
                        self.metrics[provider_id].success_rate = success_rate
                        self.metrics[provider_id].average_response_time = avg_response_time
                        self.metrics[provider_id].error_rate = error_rate
                        self.metrics[provider_id].last_updated = datetime.utcnow()
                
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics update loop error: {e}")
                await asyncio.sleep(60)
    
    def record_call_result(self, call_id: str, provider_id: str, status: str, duration: float = 0.0, response_time: float = 0.0):
        """Record call result for metrics calculation"""
        try:
            call_data = {
                'call_id': call_id,
                'provider_id': provider_id,
                'status': status,
                'duration': duration,
                'response_time': response_time,
                'start_time': datetime.utcnow() - timedelta(seconds=duration),
                'end_time': datetime.utcnow()
            }
            
            self.call_history.append(call_data)
            
            # Update provider metrics
            if provider_id in self.metrics:
                metrics = self.metrics[provider_id]
                metrics.call_count += 1
                metrics.total_duration += duration
                
        except Exception as e:
            self.logger.error(f"Failed to record call result: {e}")
