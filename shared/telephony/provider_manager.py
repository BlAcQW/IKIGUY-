"""
Provider Manager

This module provides enhanced provider management with switching logic and health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .interfaces import TelephonyPort, TelephonyEvent
from .models import CallContext, ProviderHealth, ProviderSettings
from .adapters import VapiAdapter, VonageAdapter, TelnyxAdapter, SipAdapter


class ProviderSelectionStrategy(Enum):
    """Provider selection strategies"""
    ROUND_ROBIN = "round_robin"
    HEALTH_BASED = "health_based"
    COST_BASED = "cost_based"
    QUALITY_BASED = "quality_based"
    GEOGRAPHIC = "geographic"


@dataclass
class ProviderInfo:
    """Provider information and status"""
    name: str
    adapter: TelephonyPort
    settings: ProviderSettings
    health: ProviderHealth
    last_used: datetime
    success_count: int = 0
    failure_count: int = 0
    total_calls: int = 0
    average_cost: float = 0.0
    average_quality: float = 0.0


class EnhancedProviderManager:
    """Enhanced provider management with switching logic and health monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger("ProviderManager")
        self.providers: Dict[str, ProviderInfo] = {}
        self.active_calls: Dict[str, str] = {}  # call_id -> provider_name
        self.selection_strategy = ProviderSelectionStrategy.HEALTH_BASED
        self.health_check_interval = 300  # 5 minutes
        self._health_check_task: Optional[asyncio.Task] = None
        self._current_provider_index = 0
        
    async def start(self):
        """Start the provider manager"""
        self.logger.info("Starting provider manager")
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        
        # Initialize providers from config
        await self._initialize_providers()
        
    async def stop(self):
        """Stop the provider manager"""
        self.logger.info("Stopping provider manager")
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all providers
        for provider_info in self.providers.values():
            try:
                await provider_info.adapter.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting provider {provider_info.name}: {e}")
    
    async def _initialize_providers(self):
        """Initialize providers from configuration"""
        provider_configs = self.config.get('providers', {})
        
        for name, config in provider_configs.items():
            try:
                await self._register_provider(name, config)
            except Exception as e:
                self.logger.error(f"Failed to initialize provider {name}: {e}")
    
    async def _register_provider(self, name: str, config: Dict[str, Any]):
        """Register a provider with the manager"""
        try:
            # Create provider settings
            settings = ProviderSettings(
                provider_id=name,
                api_key=config.get('api_key'),
                api_secret=config.get('api_secret'),
                base_url=config.get('base_url'),
                timeout_seconds=config.get('timeout_seconds', 30),
                retry_attempts=config.get('retry_attempts', 3),
                enabled=config.get('enabled', True),
                priority=config.get('priority', 5),
                cost_multiplier=config.get('cost_multiplier', 1.0),
                max_concurrent_calls=config.get('max_concurrent_calls'),
                webhook_url=config.get('webhook_url'),
                webhook_secret=config.get('webhook_secret'),
                custom_settings=config.get('custom_settings', {})
            )
            
            # Create adapter based on provider type
            provider_type = config.get('type', 'vapi').lower()
            if provider_type == 'vapi':
                adapter = VapiAdapter(settings)
            elif provider_type == 'vonage':
                adapter = VonageAdapter(settings)
            elif provider_type == 'telnyx':
                adapter = TelnyxAdapter(settings)
            elif provider_type == 'sip':
                adapter = SipAdapter(settings)
            else:
                raise ValueError(f"Unknown provider type: {provider_type}")
            
            # Connect to provider
            connected = await adapter.connect()
            if not connected:
                self.logger.warning(f"Failed to connect to provider {name}")
            
            # Create provider info
            provider_info = ProviderInfo(
                name=name,
                adapter=adapter,
                settings=settings,
                health=ProviderHealth(
                    provider_id=name,
                    is_healthy=connected,
                    last_check=datetime.utcnow()
                ),
                last_used=datetime.utcnow()
            )
            
            self.providers[name] = provider_info
            self.logger.info(f"Registered provider: {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register provider {name}: {e}")
            raise
    
    async def get_best_provider(self, context: CallContext) -> TelephonyPort:
        """
        Select best provider based on strategy and context
        
        Args:
            context: Call context information
            
        Returns:
            TelephonyPort: Best available provider
        """
        available_providers = [
            info for info in self.providers.values()
            if info.settings.enabled and info.health.is_healthy
        ]
        
        if not available_providers:
            raise Exception("No healthy providers available")
        
        # Select provider based on strategy
        if self.selection_strategy == ProviderSelectionStrategy.ROUND_ROBIN:
            selected = self._round_robin_select(available_providers)
        elif self.selection_strategy == ProviderSelectionStrategy.HEALTH_BASED:
            selected = self._health_based_select(available_providers)
        elif self.selection_strategy == ProviderSelectionStrategy.COST_BASED:
            selected = self._cost_based_select(available_providers, context)
        elif self.selection_strategy == ProviderSelectionStrategy.QUALITY_BASED:
            selected = self._quality_based_select(available_providers)
        elif self.selection_strategy == ProviderSelectionStrategy.GEOGRAPHIC:
            selected = self._geographic_select(available_providers, context)
        else:
            selected = available_providers[0]
        
        # Update provider usage
        selected.last_used = datetime.utcnow()
        selected.total_calls += 1
        
        self.logger.info(f"Selected provider: {selected.name} for call to {context.destination}")
        return selected.adapter
    
    def _round_robin_select(self, providers: List[ProviderInfo]) -> ProviderInfo:
        """Round-robin provider selection"""
        if not providers:
            raise Exception("No providers available")
        
        selected = providers[self._current_provider_index % len(providers)]
        self._current_provider_index += 1
        return selected
    
    def _health_based_select(self, providers: List[ProviderInfo]) -> ProviderInfo:
        """Health-based provider selection"""
        # Sort by health score (response time, error rate, etc.)
        def health_score(provider: ProviderInfo) -> float:
            score = 100.0
            
            # Penalize high response time
            if provider.health.response_time_ms:
                score -= min(provider.health.response_time_ms / 100, 50)
            
            # Penalize high error rate
            if provider.health.error_rate:
                score -= provider.health.error_rate
            
            # Bonus for recent success
            if provider.success_count > 0:
                success_rate = provider.success_count / (provider.success_count + provider.failure_count)
                score += success_rate * 20
            
            return max(score, 0)
        
        return max(providers, key=health_score)
    
    def _cost_based_select(self, providers: List[ProviderInfo], context: CallContext) -> ProviderInfo:
        """Cost-based provider selection"""
        if context.cost_preference == "low":
            return min(providers, key=lambda p: p.average_cost or p.health.cost_per_minute or float('inf'))
        elif context.cost_preference == "high":
            return max(providers, key=lambda p: p.average_cost or p.health.cost_per_minute or 0)
        else:
            # Balanced - consider both cost and quality
            def cost_quality_score(provider: ProviderInfo) -> float:
                cost = provider.average_cost or provider.health.cost_per_minute or 0.02
                quality = provider.average_quality or 0.5
                return quality / cost  # Higher quality, lower cost = better score
            
            return max(providers, key=cost_quality_score)
    
    def _quality_based_select(self, providers: List[ProviderInfo]) -> ProviderInfo:
        """Quality-based provider selection"""
        return max(providers, key=lambda p: p.average_quality or 0.5)
    
    def _geographic_select(self, providers: List[ProviderInfo], context: CallContext) -> ProviderInfo:
        """Geographic-based provider selection"""
        target_region = context.geographic_region
        
        if target_region:
            # Find providers that support the target region
            regional_providers = [
                p for p in providers
                if target_region in p.health.supported_regions
            ]
            
            if regional_providers:
                return self._health_based_select(regional_providers)
        
        # Fall back to health-based selection
        return self._health_based_select(providers)
    
    async def switch_provider(self, call_id: str, new_provider: str) -> bool:
        """
        Switch provider for active call
        
        Args:
            call_id: Unique call identifier
            new_provider: Name of new provider to switch to
            
        Returns:
            bool: True if provider switch was successful
        """
        try:
            if call_id not in self.active_calls:
                raise ValueError(f"Call {call_id} not found")
            
            if new_provider not in self.providers:
                raise ValueError(f"Provider {new_provider} not found")
            
            old_provider_name = self.active_calls[call_id]
            old_provider_info = self.providers[old_provider_name]
            new_provider_info = self.providers[new_provider]
            
            # End call on old provider
            await old_provider_info.adapter.hangup(call_id)
            
            # Update call tracking
            self.active_calls[call_id] = new_provider
            
            self.logger.info(f"Switched call {call_id} from {old_provider_name} to {new_provider}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch provider for call {call_id}: {e}")
            return False
    
    async def get_provider_health(self, provider_id: str) -> ProviderHealth:
        """
        Get provider health status
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            ProviderHealth: Provider health information
        """
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not found")
        
        provider_info = self.providers[provider_id]
        
        # Perform health check
        health = await provider_info.adapter.health_check()
        provider_info.health = health
        
        return health
    
    async def get_all_provider_health(self) -> Dict[str, ProviderHealth]:
        """Get health status for all providers"""
        health_status = {}
        
        for name, provider_info in self.providers.items():
            try:
                health_status[name] = await self.get_provider_health(name)
            except Exception as e:
                self.logger.error(f"Failed to get health for provider {name}: {e}")
                health_status[name] = ProviderHealth(
                    provider_id=name,
                    is_healthy=False,
                    last_check=datetime.utcnow(),
                    error_rate=100.0
                )
        
        return health_status
    
    async def record_call_success(self, call_id: str, duration: float, cost: float, quality: float = 0.8):
        """Record successful call metrics"""
        if call_id in self.active_calls:
            provider_name = self.active_calls[call_id]
            provider_info = self.providers[provider_name]
            
            provider_info.success_count += 1
            provider_info.average_cost = self._update_average(provider_info.average_cost, cost)
            provider_info.average_quality = self._update_average(provider_info.average_quality, quality)
            
            self.logger.debug(f"Recorded success for call {call_id} on provider {provider_name}")
    
    async def record_call_failure(self, call_id: str, error: str):
        """Record failed call metrics"""
        if call_id in self.active_calls:
            provider_name = self.active_calls[call_id]
            provider_info = self.providers[provider_name]
            
            provider_info.failure_count += 1
            
            self.logger.debug(f"Recorded failure for call {call_id} on provider {provider_name}: {error}")
    
    def _update_average(self, current_avg: float, new_value: float) -> float:
        """Update running average"""
        if current_avg == 0:
            return new_value
        return (current_avg + new_value) / 2
    
    async def _health_monitor_loop(self):
        """Health monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for provider_info in self.providers.values():
                    try:
                        health = await provider_info.adapter.health_check()
                        provider_info.health = health
                        
                        if not health.is_healthy:
                            self.logger.warning(f"Provider {provider_info.name} is unhealthy")
                        
                    except Exception as e:
                        self.logger.error(f"Health check failed for provider {provider_info.name}: {e}")
                        provider_info.health.is_healthy = False
                        provider_info.health.error_rate = 100.0
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitor loop: {e}")
    
    async def dial(self, to: str, from_: str, **kwargs) -> str:
        """
        Initiate a call using the best available provider
        
        Args:
            to: Destination phone number
            from_: Source phone number or DID
            **kwargs: Additional call parameters
            
        Returns:
            str: Unique call identifier
        """
        try:
            # Create call context
            context = CallContext(
                destination=to,
                source=from_,
                tenant_id=kwargs.get('tenant_id', 'default'),
                campaign_id=kwargs.get('campaign_id'),
                cost_preference=kwargs.get('cost_preference', 'balanced'),
                quality_preference=kwargs.get('quality_preference', 'balanced'),
                geographic_region=kwargs.get('geographic_region'),
                metadata=kwargs
            )
            
            # Get best provider
            provider = await self.get_best_provider(context)
            
            # Initiate call
            call_id = await provider.dial(to, from_, **kwargs)
            
            # Track the call
            provider_name = next(name for name, info in self.providers.items() if info.adapter == provider)
            self.active_calls[call_id] = provider_name
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate call: {e}")
            raise
    
    async def hangup(self, call_id: str) -> bool:
        """
        End a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            bool: True if call was successfully ended
        """
        try:
            if call_id not in self.active_calls:
                raise ValueError(f"Call {call_id} not found")
            
            provider_name = self.active_calls[call_id]
            provider_info = self.providers[provider_name]
            
            success = await provider_info.adapter.hangup(call_id)
            
            if success:
                del self.active_calls[call_id]
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to end call {call_id}: {e}")
            return False
    
    async def get_events(self, call_id: str) -> List[TelephonyEvent]:
        """
        Get events for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            List[TelephonyEvent]: List of telephony events
        """
        try:
            if call_id not in self.active_calls:
                return []
            
            provider_name = self.active_calls[call_id]
            provider_info = self.providers[provider_name]
            
            return await provider_info.adapter.get_events(call_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get events for call {call_id}: {e}")
            return []
    
    async def get_costs(self, call_id: str) -> Dict[str, float]:
        """
        Get cost breakdown for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Dict[str, float]: Cost breakdown by component
        """
        try:
            if call_id not in self.active_calls:
                return {}
            
            provider_name = self.active_calls[call_id]
            provider_info = self.providers[provider_name]
            
            return await provider_info.adapter.get_costs(call_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get costs for call {call_id}: {e}")
            return {}
