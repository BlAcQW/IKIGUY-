"""
Analytics Service for KasaAI Developer Platform.

This service provides analytics capabilities using the shared analytics library,
with developer-specific optimizations and extensions.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

# Use centralized import configuration
try:
    from .import_config import get_analytics_engine, get_storage_backend
    AnalyticsEngine = get_analytics_engine()
    MemoryStorageBackend = get_storage_backend()
    from apps.shared.analytics.business_intelligence import (
        BusinessIntelligence, MetricType, ChartType, KPICategory,
        Metric, ChartData, Dashboard, Report, KPITracker
    )
    from apps.shared.analytics.predictive_analytics import (
        PredictiveAnalytics, PredictionType, CallOutcome, CustomerSegment,
        PredictionResult, CallOutcomePrediction, OptimalTimeRecommendation
    )
    from apps.shared.storage import StorageConfig
    SHARED_LIBRARY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Shared analytics library not available: {e}")
    SHARED_LIBRARY_AVAILABLE = False
    # Create placeholder classes for fallback
    class BusinessIntelligence: pass
    class PredictiveAnalytics: pass
    class MemoryStorageBackend: pass
    class StorageConfig: pass


class DeveloperAnalyticsService:
    """
    Developer Platform Analytics Service.
    
    Provides analytics capabilities using the shared analytics library with
    developer-specific optimizations and extensions.
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        self.logger = logging.getLogger("DeveloperAnalyticsService")
        
        if not SHARED_LIBRARY_AVAILABLE:
            self.logger.warning("Using fallback analytics service - shared library not available")
            self._init_fallback()
            return
            
        if storage_backend is None:
            storage_config = StorageConfig(backend_type="memory")
            self.storage = MemoryStorageBackend(storage_config)
        else:
            self.storage = storage_backend
        
        # Initialize analytics components
        try:
            self.business_intelligence = BusinessIntelligence()
        except Exception as e:
            self.logger.warning(f"Failed to initialize business intelligence: {e}")
            self.business_intelligence = None
        
        try:
            self.predictive_analytics = PredictiveAnalytics()
        except Exception as e:
            self.logger.warning(f"Failed to initialize predictive analytics: {e}")
            self.predictive_analytics = None
        
        # Developer-specific configuration
        self.dev_config = self._load_developer_environment_config()
    
    def _init_fallback(self):
        """Initialize fallback components when shared library is not available."""
        self.storage = None
        self.business_intelligence = None
        self.predictive_analytics = None
        self.dev_config = self._load_developer_environment_config()
    
    def _load_developer_environment_config(self):
        """Load developer-specific environment configuration."""
        return {
            'analytics_enabled': os.getenv('DEV_ANALYTICS_ENABLED', 'true').lower() == 'true',
            'reports_enabled': os.getenv('DEV_REPORTS_ENABLED', 'true').lower() == 'true',
            'predictions_enabled': os.getenv('DEV_PREDICTIONS_ENABLED', 'true').lower() == 'true',
            'cache_enabled': os.getenv('DEV_ANALYTICS_CACHE_ENABLED', 'true').lower() == 'true',
            'cache_ttl': int(os.getenv('DEV_ANALYTICS_CACHE_TTL', '3600')),
            'log_level': os.getenv('DEV_ANALYTICS_LOG_LEVEL', 'INFO')
        }
    
    async def start(self):
        """Start the analytics service."""
        self.logger.info("Starting Developer Analytics Service")
    
    async def stop(self):
        """Stop the analytics service."""
        self.logger.info("Stopping Developer Analytics Service")
    
    async def create_dashboard(
        self,
        dashboard_config: Dict[str, Any],
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a dashboard."""
        if not SHARED_LIBRARY_AVAILABLE or self.business_intelligence is None:
            return {
                "dashboard_id": f"fallback_dashboard_{datetime.now().timestamp()}",
                "name": dashboard_config.get("name", "Fallback Dashboard"),
                "status": "fallback_created",
                "metrics_count": len(metrics)
            }
        
        try:
            result = await self.business_intelligence.create_dashboard(
                config=dashboard_config,
                metrics=metrics
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def generate_report(
        self,
        report_type: str,
        data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a report."""
        if not SHARED_LIBRARY_AVAILABLE or self.business_intelligence is None:
            return {
                "report_id": f"fallback_report_{datetime.now().timestamp()}",
                "type": report_type,
                "status": "fallback_generated",
                "data_points": len(data)
            }
        
        try:
            result = await self.business_intelligence.generate_report(
                report_type=report_type,
                data=data,
                config=config or {}
            )
            return result
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def track_kpi(
        self,
        kpi_name: str,
        value: float,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track a KPI."""
        if not SHARED_LIBRARY_AVAILABLE or self.business_intelligence is None:
            return {
                "kpi_id": f"fallback_kpi_{datetime.now().timestamp()}",
                "name": kpi_name,
                "value": value,
                "category": category,
                "status": "fallback_tracked"
            }
        
        try:
            result = await self.business_intelligence.track_kpi(
                kpi_name=kpi_name,
                value=value,
                category=category,
                metadata=metadata or {}
            )
            return result
        except Exception as e:
            self.logger.error(f"Error tracking KPI: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def predict_call_outcome(
        self,
        call_data: Dict[str, Any],
        model_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Predict call outcome."""
        if not SHARED_LIBRARY_AVAILABLE or self.predictive_analytics is None:
            return {
                "prediction": "fallback_success",
                "confidence": 0.5,
                "call_data": call_data,
                "status": "fallback_prediction"
            }
        
        try:
            result = await self.predictive_analytics.predict_call_outcome(
                call_data=call_data,
                model_config=model_config or {}
            )
            return result
        except Exception as e:
            self.logger.error(f"Error predicting call outcome: {e}")
            return {"error": str(e), "prediction": "unknown"}
    
    async def get_developer_analytics_config(self) -> Dict[str, Any]:
        """Get developer analytics configuration."""
        return {
            "config": self.dev_config,
            "shared_library_available": SHARED_LIBRARY_AVAILABLE,
            "components": {
                "business_intelligence": self.business_intelligence is not None,
                "predictive_analytics": self.predictive_analytics is not None
            }
        }
