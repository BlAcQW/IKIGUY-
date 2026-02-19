"""
Unit tests for Developer Analytics Service.

Tests the Developer Platform Analytics service that uses the shared analytics library.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ..services.analytics_service import DeveloperAnalyticsService
from apps.shared.analytics.business_intelligence import KPICategory, ChartType
from apps.shared.storage import MemoryStorageBackend, StorageConfig


class TestDeveloperAnalyticsService:
    """Test cases for DeveloperAnalyticsService."""
    
    @pytest.fixture
    def analytics_service(self):
        """Create an analytics service instance for testing."""
        return DeveloperAnalyticsService()
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage backend."""
        return Mock(spec=MemoryStorageBackend)
    
    @pytest.fixture
    def analytics_service_with_mock_storage(self, mock_storage):
        """Create an analytics service with mock storage."""
        return DeveloperAnalyticsService(storage_backend=mock_storage)
    
    # Initialization Tests
    def test_initialization(self, analytics_service):
        """Test service initialization."""
        assert analytics_service.logger is not None
        assert analytics_service.storage is not None
        assert analytics_service.business_intelligence is not None
        assert analytics_service.predictive_analytics is not None
        assert analytics_service.dev_config is not None
    
    def test_initialization_with_custom_storage(self, mock_storage):
        """Test service initialization with custom storage."""
        service = DeveloperAnalyticsService(storage_backend=mock_storage)
        assert service.storage == mock_storage
    
    def test_environment_config_loading(self, analytics_service):
        """Test environment configuration loading."""
        config = analytics_service.dev_config
        assert "analytics_cache_enabled" in config
        assert "analytics_offline_mode" in config
        assert "analytics_performance_monitoring" in config
        assert "analytics_error_reporting" in config
        assert "analytics_auto_update" in config
        assert "analytics_grace_period_hours" in config
        assert "analytics_max_concurrent_requests" in config
        assert "analytics_request_timeout" in config
        assert "analytics_fallback_enabled" in config
    
    # Start/Stop Tests
    @pytest.mark.asyncio
    async def test_start_service(self, analytics_service):
        """Test starting the service."""
        with patch.object(analytics_service.business_intelligence, 'initialize', new_callable=AsyncMock) as mock_init:
            await analytics_service.start()
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_service(self, analytics_service):
        """Test stopping the service."""
        with patch.object(analytics_service.business_intelligence, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            await analytics_service.stop()
            mock_cleanup.assert_called_once()
    
    # Business Intelligence Tests
    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, analytics_service):
        """Test successful dashboard creation."""
        dashboard_config = {"title": "Test Dashboard", "layout": "grid"}
        metrics = [{"name": "revenue", "value": 1000}]
        
        with patch.object(analytics_service.business_intelligence, 'create_dashboard', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"dashboard_id": "test_dash", "status": "created"}
            
            result = await analytics_service.create_dashboard(dashboard_config, metrics)
            
            assert result["dashboard_id"] == "test_dash"
            assert result["status"] == "created"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_dashboard_fallback(self, analytics_service):
        """Test dashboard creation with fallback."""
        analytics_service.dev_config["analytics_fallback_enabled"] = True
        dashboard_config = {"title": "Test Dashboard", "layout": "grid"}
        metrics = [{"name": "revenue", "value": 1000}]
        
        with patch.object(analytics_service.business_intelligence, 'create_dashboard', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Dashboard error")
            
            result = await analytics_service.create_dashboard(dashboard_config, metrics)
            
            assert result["status"] == "fallback"
            assert "fallback" in result["message"]
    
    @pytest.mark.asyncio
    async def test_generate_report_success(self, analytics_service):
        """Test successful report generation."""
        data = {"revenue": 1000, "calls": 50}
        
        with patch.object(analytics_service.business_intelligence, 'generate_report', new_callable=AsyncMock) as mock_report:
            mock_report.return_value = {"report_id": "test_report", "content": "Report content"}
            
            result = await analytics_service.generate_report("revenue", data)
            
            assert result["report_id"] == "test_report"
            assert result["content"] == "Report content"
            mock_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_kpi_success(self, analytics_service):
        """Test successful KPI tracking."""
        with patch.object(analytics_service.business_intelligence, 'track_kpi', new_callable=AsyncMock) as mock_track:
            mock_track.return_value = {"kpi_id": "test_kpi", "status": "tracked"}
            
            result = await analytics_service.track_kpi(
                "revenue", 1000.0, KPICategory.FINANCIAL
            )
            
            assert result["kpi_id"] == "test_kpi"
            assert result["status"] == "tracked"
            mock_track.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_kpi_summary_success(self, analytics_service):
        """Test successful KPI summary retrieval."""
        with patch.object(analytics_service.business_intelligence, 'get_kpi_summary', new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = {"total_kpis": 5, "summary": "KPI summary"}
            
            result = await analytics_service.get_kpi_summary(KPICategory.FINANCIAL)
            
            assert result["total_kpis"] == 5
            assert result["summary"] == "KPI summary"
            mock_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chart_success(self, analytics_service):
        """Test successful chart creation."""
        data = {"x": [1, 2, 3], "y": [10, 20, 30]}
        
        with patch.object(analytics_service.business_intelligence, 'create_chart', new_callable=AsyncMock) as mock_chart:
            mock_chart.return_value = {"chart_id": "test_chart", "url": "chart_url"}
            
            result = await analytics_service.create_chart(ChartType.LINE, data)
            
            assert result["chart_id"] == "test_chart"
            assert result["url"] == "chart_url"
            mock_chart.assert_called_once()
    
    # Predictive Analytics Tests
    @pytest.mark.asyncio
    async def test_predict_call_outcome_success(self, analytics_service):
        """Test successful call outcome prediction."""
        call_data = {"customer_id": "123", "call_history": [{"outcome": "success"}]}
        
        with patch.object(analytics_service.predictive_analytics, 'predict_call_outcome', new_callable=AsyncMock) as mock_predict:
            mock_predict.return_value = {"predicted_outcome": "success", "confidence": 0.85}
            
            result = await analytics_service.predict_call_outcome(call_data)
            
            assert result["predicted_outcome"] == "success"
            assert result["confidence"] == 0.85
            mock_predict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_call_outcome_fallback(self, analytics_service):
        """Test call outcome prediction with fallback."""
        analytics_service.dev_config["analytics_fallback_enabled"] = True
        call_data = {"customer_id": "123", "call_history": [{"outcome": "success"}]}
        
        with patch.object(analytics_service.predictive_analytics, 'predict_call_outcome', new_callable=AsyncMock) as mock_predict:
            mock_predict.side_effect = Exception("Prediction error")
            
            result = await analytics_service.predict_call_outcome(call_data)
            
            assert result["predicted_outcome"] == "unknown"
            assert result["confidence"] == 0.0
            assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_get_optimal_calling_time_success(self, analytics_service):
        """Test successful optimal calling time recommendation."""
        customer_data = {"customer_id": "123", "timezone": "UTC"}
        
        with patch.object(analytics_service.predictive_analytics, 'get_optimal_calling_time', new_callable=AsyncMock) as mock_time:
            mock_time.return_value = {"recommended_times": ["09:00", "14:00"], "success_probability": 0.8}
            
            result = await analytics_service.get_optimal_calling_time(customer_data)
            
            assert result["recommended_times"] == ["09:00", "14:00"]
            assert result["success_probability"] == 0.8
            mock_time.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_customer_behavior_success(self, analytics_service):
        """Test successful customer behavior analysis."""
        customer_data = {"customer_id": "123", "purchase_history": [{"amount": 100}]}
        
        with patch.object(analytics_service.predictive_analytics, 'analyze_customer_behavior', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"behavior_type": "high_value", "confidence": 0.9}
            
            result = await analytics_service.analyze_customer_behavior(customer_data, "purchase")
            
            assert result["behavior_type"] == "high_value"
            assert result["confidence"] == 0.9
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_forecast_revenue_success(self, analytics_service):
        """Test successful revenue forecasting."""
        historical_data = [{"month": "2023-01", "revenue": 1000}, {"month": "2023-02", "revenue": 1200}]
        
        with patch.object(analytics_service.predictive_analytics, 'forecast_revenue', new_callable=AsyncMock) as mock_forecast:
            mock_forecast.return_value = {"forecast": 1500, "confidence": 0.85}
            
            result = await analytics_service.forecast_revenue(historical_data, "monthly")
            
            assert result["forecast"] == 1500
            assert result["confidence"] == 0.85
            mock_forecast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_segment_customers_success(self, analytics_service):
        """Test successful customer segmentation."""
        customer_data = [{"id": "1", "value": 1000}, {"id": "2", "value": 500}]
        segmentation_criteria = {"value_threshold": 750}
        
        with patch.object(analytics_service.predictive_analytics, 'segment_customers', new_callable=AsyncMock) as mock_segment:
            mock_segment.return_value = {"segments": [{"name": "high_value", "customers": ["1"]}]}
            
            result = await analytics_service.segment_customers(customer_data, segmentation_criteria)
            
            assert "segments" in result
            assert len(result["segments"]) == 1
            assert result["segments"][0]["name"] == "high_value"
            mock_segment.assert_called_once()
    
    # Developer-specific Tests
    @pytest.mark.asyncio
    async def test_get_developer_analytics_config(self, analytics_service):
        """Test getting developer analytics configuration."""
        with patch.object(analytics_service, '_get_performance_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {"response_time": 0.15}
            
            result = await analytics_service.get_developer_analytics_config()
            
            assert "config" in result
            assert "cache_status" in result
            assert "offline_status" in result
            assert "performance_metrics" in result
            assert result["performance_metrics"]["response_time"] == 0.15
    
    @pytest.mark.asyncio
    async def test_validate_developer_analytics_config_success(self, analytics_service):
        """Test successful analytics configuration validation."""
        result = await analytics_service.validate_developer_analytics_config()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_developer_analytics_config_missing_key(self, analytics_service):
        """Test analytics configuration validation with missing key."""
        del analytics_service.dev_config["analytics_cache_enabled"]
        
        result = await analytics_service.validate_developer_analytics_config()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_offline_analytics_status(self, analytics_service):
        """Test getting offline analytics status."""
        result = await analytics_service.get_offline_analytics_status()
        
        assert result["offline_mode"] == analytics_service.dev_config["analytics_offline_mode"]
        assert "grace_period_hours" in result
        assert "last_sync" in result
    
    @pytest.mark.asyncio
    async def test_sync_analytics_with_core(self, analytics_service):
        """Test syncing analytics with core."""
        result = await analytics_service.sync_analytics_with_core("http://core:8000", "token123")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_analytics_metrics(self, analytics_service):
        """Test getting analytics metrics."""
        result = await analytics_service.get_analytics_metrics("tenant123")
        
        assert result["tenant_id"] == "tenant123"
        assert "timestamp" in result
        assert "config" in result
        assert "cache_status" in result
    
    @pytest.mark.asyncio
    async def test_export_analytics_data_success(self, analytics_service):
        """Test successful analytics data export."""
        result = await analytics_service.export_analytics_data("tenant123", "revenue", "json")
        
        assert isinstance(result, str)
        export_data = eval(result)  # Convert string back to dict
        assert export_data["tenant_id"] == "tenant123"
        assert export_data["data_type"] == "revenue"
        assert export_data["format"] == "json"
    
    @pytest.mark.asyncio
    async def test_export_analytics_data_error(self, analytics_service):
        """Test analytics data export with error."""
        with patch('json.dumps', side_effect=Exception("Export error")):
            result = await analytics_service.export_analytics_data("tenant123", "revenue", "json")
            
            assert isinstance(result, str)
            error_data = eval(result)
            assert "error" in error_data
    
    @pytest.mark.asyncio
    async def test_batch_analyze_data_success(self, analytics_service):
        """Test successful batch data analysis."""
        data_batch = [{"text": "positive"}, {"text": "negative"}]
        
        with patch.object(analytics_service.business_intelligence, 'analyze_sentiment', new_callable=AsyncMock) as mock_sentiment:
            mock_sentiment.side_effect = [
                {"sentiment": "positive", "score": 0.8},
                {"sentiment": "negative", "score": 0.7}
            ]
            
            results = await analytics_service.batch_analyze_data(data_batch, "sentiment")
            
            assert len(results) == 2
            assert results[0]["sentiment"] == "positive"
            assert results[1]["sentiment"] == "negative"
    
    @pytest.mark.asyncio
    async def test_batch_analyze_data_unknown_type(self, analytics_service):
        """Test batch data analysis with unknown type."""
        data_batch = [{"text": "test"}]
        
        results = await analytics_service.batch_analyze_data(data_batch, "unknown_type")
        
        assert len(results) == 1
        assert "error" in results[0]
        assert "Unknown analysis type" in results[0]["error"]
    
    @pytest.mark.asyncio
    async def test_batch_analyze_data_error(self, analytics_service):
        """Test batch data analysis with error."""
        data_batch = [{"text": "test"}]
        
        with patch.object(analytics_service.business_intelligence, 'analyze_sentiment', new_callable=AsyncMock) as mock_sentiment:
            mock_sentiment.side_effect = Exception("Analysis error")
            
            results = await analytics_service.batch_analyze_data(data_batch, "sentiment")
            
            assert len(results) == 1
            assert "error" in results[0]
            assert "Analysis error" in results[0]["error"]
    
    # Helper Method Tests
    def test_get_cache_status(self, analytics_service):
        """Test getting cache status."""
        status = analytics_service._get_cache_status()
        
        assert "enabled" in status
        assert "cache_size" in status
        assert "cache_ttl" in status
        assert status["enabled"] == analytics_service.dev_config["analytics_cache_enabled"]
        assert status["cache_size"] == 0
    
    def test_get_offline_status(self, analytics_service):
        """Test getting offline status."""
        status = analytics_service._get_offline_status()
        
        assert "enabled" in status
        assert "grace_period_hours" in status
        assert "fallback_enabled" in status
        assert status["enabled"] == analytics_service.dev_config["analytics_offline_mode"]
        assert status["grace_period_hours"] == analytics_service.dev_config["analytics_grace_period_hours"]
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, analytics_service):
        """Test getting performance metrics."""
        result = await analytics_service._get_performance_metrics()
        
        assert "cache_hit_rate" in result
        assert "response_time_avg" in result
        assert "error_rate" in result
        assert "timestamp" in result
        assert result["cache_hit_rate"] == 0.85
        assert result["response_time_avg"] == 0.15
        assert result["error_rate"] == 0.02
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_error(self, analytics_service):
        """Test getting performance metrics with error."""
        with patch('datetime.utcnow', side_effect=Exception("Time error")):
            result = await analytics_service._get_performance_metrics()
            
            assert "error" in result
            assert "Time error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_last_sync_time(self, analytics_service):
        """Test getting last sync time."""
        result = await analytics_service._get_last_sync_time()
        assert result is not None
        assert isinstance(result, str)
    
    # Edge Cases and Error Handling
    @pytest.mark.asyncio
    async def test_all_fallback_scenarios(self, analytics_service):
        """Test all fallback scenarios when analytics_fallback_enabled is True."""
        analytics_service.dev_config["analytics_fallback_enabled"] = True
        
        # Test dashboard creation fallback
        with patch.object(analytics_service.business_intelligence, 'create_dashboard', side_effect=Exception("Error")):
            result = await analytics_service.create_dashboard({}, [])
            assert result["status"] == "fallback"
        
        # Test report generation fallback
        with patch.object(analytics_service.business_intelligence, 'generate_report', side_effect=Exception("Error")):
            result = await analytics_service.generate_report("test", {})
            assert result["status"] == "fallback"
        
        # Test KPI tracking fallback
        with patch.object(analytics_service.business_intelligence, 'track_kpi', side_effect=Exception("Error")):
            result = await analytics_service.track_kpi("test", 100, KPICategory.FINANCIAL)
            assert result["status"] == "fallback"
        
        # Test KPI summary fallback
        with patch.object(analytics_service.business_intelligence, 'get_kpi_summary', side_effect=Exception("Error")):
            result = await analytics_service.get_kpi_summary()
            assert result["status"] == "fallback"
        
        # Test chart creation fallback
        with patch.object(analytics_service.business_intelligence, 'create_chart', side_effect=Exception("Error")):
            result = await analytics_service.create_chart(ChartType.LINE, {})
            assert result["status"] == "fallback"
        
        # Test call outcome prediction fallback
        with patch.object(analytics_service.predictive_analytics, 'predict_call_outcome', side_effect=Exception("Error")):
            result = await analytics_service.predict_call_outcome({})
            assert result["predicted_outcome"] == "unknown"
            assert result["fallback"] is True
        
        # Test optimal calling time fallback
        with patch.object(analytics_service.predictive_analytics, 'get_optimal_calling_time', side_effect=Exception("Error")):
            result = await analytics_service.get_optimal_calling_time({})
            assert result["recommended_times"] == []
            assert result["fallback"] is True
        
        # Test customer behavior analysis fallback
        with patch.object(analytics_service.predictive_analytics, 'analyze_customer_behavior', side_effect=Exception("Error")):
            result = await analytics_service.analyze_customer_behavior({}, "test")
            assert result["behavior_analysis"] == "unavailable"
            assert result["fallback"] is True
        
        # Test revenue forecasting fallback
        with patch.object(analytics_service.predictive_analytics, 'forecast_revenue', side_effect=Exception("Error")):
            result = await analytics_service.forecast_revenue([], "monthly")
            assert result["forecast"] == "unavailable"
            assert result["fallback"] is True
        
        # Test customer segmentation fallback
        with patch.object(analytics_service.predictive_analytics, 'segment_customers', side_effect=Exception("Error")):
            result = await analytics_service.segment_customers([], {})
            assert result["segments"] == []
            assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_configuration_validation_edge_cases(self, analytics_service):
        """Test configuration validation edge cases."""
        # Test with empty config
        analytics_service.dev_config = {}
        result = await analytics_service.validate_developer_analytics_config()
        assert result is False
        
        # Test with partial config
        analytics_service.dev_config = {"analytics_cache_enabled": True}
        result = await analytics_service.validate_developer_analytics_config()
        assert result is False
        
        # Test with invalid config values
        analytics_service.dev_config = {
            "analytics_cache_enabled": "invalid",
            "analytics_offline_mode": "invalid",
            "analytics_performance_monitoring": "invalid",
            "analytics_error_reporting": "invalid",
            "analytics_auto_update": "invalid",
            "analytics_grace_period_hours": "invalid",
            "analytics_max_concurrent_requests": "invalid",
            "analytics_request_timeout": "invalid",
            "analytics_fallback_enabled": "invalid"
        }
        result = await analytics_service.validate_developer_analytics_config()
        assert result is False
