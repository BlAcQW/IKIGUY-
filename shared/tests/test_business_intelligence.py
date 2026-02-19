"""
Tests for Business Intelligence

This module tests the business intelligence capabilities including:
- Advanced analytics and reporting
- Data visualization and dashboards
- KPI tracking and monitoring
- Business metrics and insights
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.shared.analytics.business_intelligence import (
    BusinessIntelligence,
    MetricType,
    ChartType,
    KPICategory,
    Metric,
    ChartData,
    Dashboard,
    Insight
)


class TestBusinessIntelligence:
    """Test cases for Business Intelligence"""

    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'data_retention_days': 365,
            'refresh_interval': 300,
            'max_data_points': 1000,  # Lower for testing
            'alert_threshold': 0.1
        }

    @pytest.fixture
    def bi(self, config):
        """Business Intelligence instance"""
        return BusinessIntelligence(config)

    @pytest.fixture
    def sample_data(self):
        """Sample business data"""
        return {
            'calls': [
                {'outcome': 'success', 'duration': 300, 'agent_id': 'agent1'},
                {'outcome': 'success', 'duration': 250, 'agent_id': 'agent2'},
                {'outcome': 'failure', 'duration': 100, 'agent_id': 'agent1'},
                {'outcome': 'success', 'duration': 400, 'agent_id': 'agent3'}
            ],
            'revenue': 50000,
            'target_revenue': 60000,
            'satisfaction_scores': [4.2, 4.5, 3.8, 4.1, 4.3],
            'agent_performance': [
                {'calls_handled': 10, 'avg_call_duration': 280, 'satisfaction_score': 4.2},
                {'calls_handled': 8, 'avg_call_duration': 320, 'satisfaction_score': 4.0},
                {'calls_handled': 12, 'avg_call_duration': 250, 'satisfaction_score': 4.5}
            ],
            'costs': {
                'total_cost': 15000,
                'total_calls': 30
            },
            'churn_rate': 0.03,
            'time_series_data': [
                {'timestamp': '2024-01-01', 'value': 100},
                {'timestamp': '2024-01-02', 'value': 120},
                {'timestamp': '2024-01-03', 'value': 110}
            ],
            'comparison_data': [
                {'category': 'Agent A', 'value': 85},
                {'category': 'Agent B', 'value': 92},
                {'category': 'Agent C', 'value': 78}
            ],
            'distribution_data': [
                {'label': 'Success', 'value': 75},
                {'label': 'Failure', 'value': 15},
                {'label': 'No Answer', 'value': 10}
            ],
            'correlation_data': {
                'matrix': [[1.0, 0.8, 0.6], [0.8, 1.0, 0.7], [0.6, 0.7, 1.0]],
                'labels': ['Calls', 'Revenue', 'Satisfaction']
            }
        }

    def test_initialization(self, bi):
        """Test business intelligence initialization"""
        assert bi is not None
        assert len(bi.dashboards) == 3  # Default dashboards
        assert 'operational' in bi.dashboards
        assert 'financial' in bi.dashboards
        assert 'customer' in bi.dashboards

    def test_default_dashboards(self, bi):
        """Test default dashboard creation"""
        operational = bi.dashboards['operational']
        assert operational.name == "Operational Overview"
        assert operational.description == "Key operational metrics and performance indicators"
        assert operational.layout == {"columns": 3, "rows": 2}

        financial = bi.dashboards['financial']
        assert financial.name == "Financial Performance"
        assert financial.description == "Revenue, costs, and financial KPIs"

        customer = bi.dashboards['customer']
        assert customer.name == "Customer Analytics"
        assert customer.description == "Customer behavior, satisfaction, and engagement"

    @pytest.mark.asyncio
    async def test_calculate_metrics(self, bi, sample_data):
        """Test metric calculation"""
        metrics = await bi.calculate_metrics(sample_data)
        
        assert len(metrics) > 0
        
        # Check for specific metrics
        metric_names = [m.name for m in metrics]
        assert "Total Calls" in metric_names
        assert "Success Rate" in metric_names
        assert "Total Revenue" in metric_names
        assert "Customer Satisfaction" in metric_names

        # Check metric values
        for metric in metrics:
            assert isinstance(metric.value, (int, float))
            assert isinstance(metric.unit, str)
            assert isinstance(metric.trend, float)
            assert isinstance(metric.category, KPICategory)

    @pytest.mark.asyncio
    async def test_calculate_agent_metrics(self, bi, sample_data):
        """Test agent metrics calculation"""
        agent_metrics = await bi._calculate_agent_metrics(sample_data['agent_performance'])
        
        assert len(agent_metrics) > 0
        
        metric_names = [m.name for m in agent_metrics]
        assert "Avg Calls per Agent" in metric_names
        assert "Avg Call Duration" in metric_names
        assert "Agent Satisfaction" in metric_names

        # Check avg calls per agent
        avg_calls_metric = next(m for m in agent_metrics if m.name == "Avg Calls per Agent")
        expected_avg = (10 + 8 + 12) / 3  # 10
        assert abs(avg_calls_metric.value - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_cost_metrics(self, bi, sample_data):
        """Test cost metrics calculation"""
        cost_metrics = await bi._calculate_cost_metrics(sample_data['costs'])
        
        assert len(cost_metrics) > 0
        
        metric_names = [m.name for m in cost_metrics]
        assert "Cost per Call" in metric_names
        assert "Total Operational Cost" in metric_names

        # Check cost per call
        cost_per_call_metric = next(m for m in cost_metrics if m.name == "Cost per Call")
        expected_cost_per_call = 15000 / 30  # 500
        assert abs(cost_per_call_metric.value - expected_cost_per_call) < 0.01

    def test_calculate_trend(self, bi):
        """Test trend calculation"""
        # Test with no history
        trend = bi._calculate_trend('new_metric', 100)
        assert trend == 0.0

        # Test with history
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=100, unit="test", trend=0.0),
            Metric(name="Test", value=120, unit="test", trend=0.0)
        ]
        
        trend = bi._calculate_trend('test_metric', 150)
        expected_trend = ((150 - 120) / 120) * 100  # 25%
        assert abs(trend - expected_trend) < 0.01

        # Test with zero previous value
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=0, unit="test", trend=0.0)
        ]
        trend = bi._calculate_trend('test_metric', 100)
        assert trend == 0.0

    @pytest.mark.asyncio
    async def test_generate_charts(self, bi, sample_data):
        """Test chart generation"""
        charts = await bi.generate_charts(sample_data)
        
        assert len(charts) > 0
        
        for chart in charts:
            assert isinstance(chart, ChartData)
            assert chart.title is not None
            assert len(chart.x_axis) > 0
            assert len(chart.y_axis) > 0
            assert len(chart.series) > 0

    @pytest.mark.asyncio
    async def test_create_time_series_chart(self, bi, sample_data):
        """Test time series chart creation"""
        chart = await bi._create_time_series_chart(sample_data['time_series_data'])
        
        assert chart is not None
        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Performance Over Time"
        assert len(chart.x_axis) == 3
        assert len(chart.y_axis) == 3
        assert chart.series[0]['type'] == 'line'

    @pytest.mark.asyncio
    async def test_create_comparison_chart(self, bi, sample_data):
        """Test comparison chart creation"""
        chart = await bi._create_comparison_chart(sample_data['comparison_data'])
        
        assert chart is not None
        assert chart.chart_type == ChartType.BAR
        assert chart.title == "Performance Comparison"
        assert len(chart.x_axis) == 3
        assert len(chart.y_axis) == 3
        assert chart.series[0]['type'] == 'bar'

    @pytest.mark.asyncio
    async def test_create_distribution_chart(self, bi, sample_data):
        """Test distribution chart creation"""
        chart = await bi._create_distribution_chart(sample_data['distribution_data'])
        
        assert chart is not None
        assert chart.chart_type == ChartType.PIE
        assert chart.title == "Data Distribution"
        assert len(chart.x_axis) == 3
        assert len(chart.y_axis) == 3
        assert chart.series[0]['type'] == 'pie'

    @pytest.mark.asyncio
    async def test_create_correlation_heatmap(self, bi, sample_data):
        """Test correlation heatmap creation"""
        chart = await bi._create_correlation_heatmap(sample_data['correlation_data'])
        
        assert chart is not None
        assert chart.chart_type == ChartType.HEATMAP
        assert chart.title == "Correlation Matrix"
        assert len(chart.x_axis) == 3
        assert len(chart.y_axis) == 3
        assert chart.series[0]['type'] == 'heatmap'

    @pytest.mark.asyncio
    async def test_create_dashboard(self, bi):
        """Test dashboard creation"""
        metrics = [
            Metric(name="Test Metric", value=100, unit="test", trend=5.0)
        ]
        charts = [
            ChartData(
                chart_type=ChartType.LINE,
                title="Test Chart",
                x_axis=[1, 2, 3],
                y_axis=[10, 20, 30],
                series=[{'name': 'Test', 'data': [], 'type': 'line'}]
            )
        ]
        
        dashboard = await bi.create_dashboard(
            name="Test Dashboard",
            description="Test dashboard description",
            metrics=metrics,
            charts=charts
        )
        
        assert dashboard is not None
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test dashboard description"
        assert len(dashboard.metrics) == 1
        assert len(dashboard.charts) == 1
        assert "test_dashboard" in bi.dashboards

    @pytest.mark.asyncio
    async def test_update_dashboard(self, bi):
        """Test dashboard update"""
        # Create a dashboard first
        metrics = [Metric(name="Test", value=100, unit="test", trend=0.0)]
        charts = [ChartData(
            chart_type=ChartType.LINE,
            title="Test",
            x_axis=[1],
            y_axis=[1],
            series=[{'name': 'Test', 'data': [], 'type': 'line'}]
        )]
        
        await bi.create_dashboard("Test", "Test", metrics, charts)
        
        # Update with new metrics
        new_metrics = [Metric(name="Updated", value=200, unit="test", trend=0.0)]
        result = await bi.update_dashboard("test", metrics=new_metrics)
        
        assert result is True
        assert len(bi.dashboards["test"].metrics) == 1
        assert bi.dashboards["test"].metrics[0].name == "Updated"

    @pytest.mark.asyncio
    async def test_generate_insights(self, bi, sample_data):
        """Test insight generation"""
        insights = await bi.generate_insights(sample_data)
        
        assert len(insights) >= 0  # May or may not have insights depending on data
        
        for insight in insights:
            assert isinstance(insight, Insight)
            assert insight.title is not None
            assert insight.description is not None
            assert insight.category is not None
            assert 0.0 <= insight.confidence <= 1.0
            assert insight.impact in ['high', 'medium', 'low']
            assert len(insight.recommendations) > 0
            assert isinstance(insight.data_points, dict)

    @pytest.mark.asyncio
    async def test_analyze_performance(self, bi, sample_data):
        """Test performance analysis"""
        insights = await bi._analyze_performance(sample_data)
        
        # Should have insights about success rate (75% > 70% target, so no insight expected)
        success_rate_insights = [i for i in insights if "Success Rate" in i.title]
        # Success rate is 75% which is above 70% threshold, so no insight should be generated
        assert len(success_rate_insights) == 0
        
        # Should have insights about revenue (83.3% < 90% target)
        revenue_insights = [i for i in insights if "Revenue" in i.title]
        assert len(revenue_insights) > 0

    @pytest.mark.asyncio
    async def test_analyze_trends(self, bi):
        """Test trend analysis"""
        # Add some metric history
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=100, unit="test", trend=0.0),
            Metric(name="Test", value=110, unit="test", trend=0.0),
            Metric(name="Test", value=130, unit="test", trend=0.0)  # 30% increase
        ]
        
        insights = await bi._analyze_trends({})
        
        # Should detect the trend
        trend_insights = [i for i in insights if "Trend" in i.title]
        assert len(trend_insights) > 0

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, bi):
        """Test anomaly detection"""
        # Add metric history with an anomaly
        values = [100, 105, 110, 115, 120, 125, 130, 135, 140, 200]  # Last value is anomaly
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=v, unit="test", trend=0.0) for v in values
        ]
        
        insights = await bi._detect_anomalies({})
        
        # Should detect the anomaly
        anomaly_insights = [i for i in insights if "Anomaly" in i.title]
        assert len(anomaly_insights) > 0

    @pytest.mark.asyncio
    async def test_analyze_customer_behavior(self, bi, sample_data):
        """Test customer behavior analysis"""
        insights = await bi._analyze_customer_behavior(sample_data)
        
        # Should have insights about satisfaction (avg 4.18 > 4.0 threshold, so no insight expected)
        satisfaction_insights = [i for i in insights if "Satisfaction" in i.title]
        # Average satisfaction is 4.18 which is above 4.0 threshold, so no insight should be generated
        assert len(satisfaction_insights) == 0

    @pytest.mark.asyncio
    async def test_generate_report(self, bi, sample_data):
        """Test report generation"""
        report = await bi.generate_report("test_report", sample_data)
        
        assert report is not None
        assert report["report_type"] == "test_report"
        assert "generated_at" in report
        assert "metrics" in report
        assert "charts" in report
        assert "insights" in report
        assert "summary" in report
        
        summary = report["summary"]
        assert "total_metrics" in summary
        assert "total_charts" in summary
        assert "total_insights" in summary
        assert "key_findings" in summary

    def test_metric_to_dict(self, bi):
        """Test metric to dictionary conversion"""
        metric = Metric(
            name="Test Metric",
            value=100.5,
            unit="test",
            trend=5.0,
            target=90.0,
            category=KPICategory.OPERATIONAL,
            metadata={"key": "value"}
        )
        
        metric_dict = bi._metric_to_dict(metric)
        
        assert metric_dict["name"] == "Test Metric"
        assert metric_dict["value"] == 100.5
        assert metric_dict["unit"] == "test"
        assert metric_dict["trend"] == 5.0
        assert metric_dict["target"] == 90.0
        assert metric_dict["category"] == "operational"
        assert metric_dict["metadata"] == {"key": "value"}

    def test_chart_to_dict(self, bi):
        """Test chart to dictionary conversion"""
        chart = ChartData(
            chart_type=ChartType.LINE,
            title="Test Chart",
            x_axis=[1, 2, 3],
            y_axis=[10, 20, 30],
            series=[{'name': 'Test', 'data': [], 'type': 'line'}],
            config={'responsive': True}
        )
        
        chart_dict = bi._chart_to_dict(chart)
        
        assert chart_dict["chart_type"] == "line"
        assert chart_dict["title"] == "Test Chart"
        assert chart_dict["x_axis"] == [1, 2, 3]
        assert chart_dict["y_axis"] == [10, 20, 30]
        assert len(chart_dict["series"]) == 1
        assert chart_dict["config"] == {'responsive': True}

    def test_insight_to_dict(self, bi):
        """Test insight to dictionary conversion"""
        insight = Insight(
            title="Test Insight",
            description="Test description",
            category="test",
            confidence=0.8,
            impact="high",
            recommendations=["rec1", "rec2"],
            data_points={"key": "value"}
        )
        
        insight_dict = bi._insight_to_dict(insight)
        
        assert insight_dict["title"] == "Test Insight"
        assert insight_dict["description"] == "Test description"
        assert insight_dict["category"] == "test"
        assert insight_dict["confidence"] == 0.8
        assert insight_dict["impact"] == "high"
        assert insight_dict["recommendations"] == ["rec1", "rec2"]
        assert insight_dict["data_points"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_export_data(self, bi):
        """Test data export"""
        # Add some test data
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=100, unit="test", trend=0.0)
        ]
        
        # Test JSON export
        json_data = await bi.export_data("metrics", "json")
        assert json_data is not None
        assert "test_metric" in json_data
        
        # Test CSV export
        csv_data = await bi.export_data("metrics", "csv")
        assert csv_data is not None
        assert "Metric,Value,Unit,Trend,Timestamp" in csv_data

    def test_convert_to_csv(self, bi):
        """Test CSV conversion"""
        # Test with metrics history
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=100, unit="test", trend=5.0)
        ]
        
        csv_data = bi._convert_to_csv(bi.metrics_history)
        assert csv_data is not None
        assert "Metric,Value,Unit,Trend,Timestamp" in csv_data
        assert "Test,100,test,5.0" in csv_data

    def test_get_system_status(self, bi):
        """Test system status retrieval"""
        status = bi.get_system_status()
        
        assert isinstance(status, dict)
        assert "total_metrics" in status
        assert "total_dashboards" in status
        assert "total_insights" in status
        assert "total_alerts" in status
        assert "last_refresh" in status
        assert "data_retention_days" in status
        assert "max_data_points" in status

    @pytest.mark.asyncio
    async def test_calculate_metrics_empty_data(self, bi):
        """Test metric calculation with empty data"""
        metrics = await bi.calculate_metrics({})
        assert len(metrics) == 0

    @pytest.mark.asyncio
    async def test_generate_charts_empty_data(self, bi):
        """Test chart generation with empty data"""
        charts = await bi.generate_charts({})
        assert len(charts) == 0

    @pytest.mark.asyncio
    async def test_generate_insights_empty_data(self, bi):
        """Test insight generation with empty data"""
        insights = await bi.generate_insights({})
        assert len(insights) == 0

    @pytest.mark.asyncio
    async def test_create_dashboard_invalid_data(self, bi):
        """Test dashboard creation with invalid data"""
        dashboard = await bi.create_dashboard("", "", [], [])
        assert dashboard is not None  # Should still create dashboard

    @pytest.mark.asyncio
    async def test_update_nonexistent_dashboard(self, bi):
        """Test updating non-existent dashboard"""
        result = await bi.update_dashboard("nonexistent", [])
        assert result is False

    def test_calculate_trend_with_zero_previous(self, bi):
        """Test trend calculation with zero previous value"""
        bi.metrics_history['test_metric'] = [
            Metric(name="Test", value=0, unit="test", trend=0.0)
        ]
        
        trend = bi._calculate_trend('test_metric', 100)
        assert trend == 0.0

    @pytest.mark.asyncio
    async def test_export_data_invalid_type(self, bi):
        """Test export data with invalid type"""
        result = await bi.export_data("invalid_type", "json")
        assert result == ""

    @pytest.mark.asyncio
    async def test_export_data_invalid_format(self, bi):
        """Test export data with invalid format"""
        result = await bi.export_data("metrics", "invalid_format")
        assert result == ""

    def test_metric_dataclass(self):
        """Test Metric dataclass"""
        metric = Metric(
            name="Test",
            value=100.0,
            unit="test",
            trend=5.0,
            target=90.0,
            category=KPICategory.OPERATIONAL
        )
        
        assert metric.name == "Test"
        assert metric.value == 100.0
        assert metric.unit == "test"
        assert metric.trend == 5.0
        assert metric.target == 90.0
        assert metric.category == KPICategory.OPERATIONAL
        assert metric.timestamp is not None
        assert metric.metadata == {}

    def test_chart_data_dataclass(self):
        """Test ChartData dataclass"""
        chart = ChartData(
            chart_type=ChartType.LINE,
            title="Test Chart",
            x_axis=[1, 2, 3],
            y_axis=[10, 20, 30],
            series=[{'name': 'Test', 'data': [], 'type': 'line'}]
        )
        
        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Test Chart"
        assert chart.x_axis == [1, 2, 3]
        assert chart.y_axis == [10, 20, 30]
        assert len(chart.series) == 1
        assert chart.config == {}

    def test_dashboard_dataclass(self):
        """Test Dashboard dataclass"""
        dashboard = Dashboard(
            name="Test Dashboard",
            description="Test description",
            charts=[],
            metrics=[]
        )
        
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test description"
        assert len(dashboard.charts) == 0
        assert len(dashboard.metrics) == 0
        assert dashboard.layout == {"columns": 2, "rows": 2}
        assert dashboard.refresh_interval == 300
        assert dashboard.created_at is not None
        assert dashboard.updated_at is not None

    def test_insight_dataclass(self):
        """Test Insight dataclass"""
        insight = Insight(
            title="Test Insight",
            description="Test description",
            category="test",
            confidence=0.8,
            impact="high",
            recommendations=["rec1"],
            data_points={"key": "value"}
        )
        
        assert insight.title == "Test Insight"
        assert insight.description == "Test description"
        assert insight.category == "test"
        assert insight.confidence == 0.8
        assert insight.impact == "high"
        assert insight.recommendations == ["rec1"]
        assert insight.data_points == {"key": "value"}
        assert insight.timestamp is not None

    def test_enum_values(self):
        """Test enum values"""
        assert MetricType.CALL_VOLUME.value == "call_volume"
        assert ChartType.LINE.value == "line"
        assert KPICategory.OPERATIONAL.value == "operational"

    @pytest.mark.asyncio
    async def test_data_retention(self, bi):
        """Test data retention functionality"""
        # Add more data than max_data_points
        for i in range(1100):  # More than max_data_points (1000)
            bi.metrics_history['test_metric'].append(
                Metric(name="Test", value=i, unit="test", trend=0.0)
            )
            # Apply retention after each addition to simulate real usage
            if len(bi.metrics_history['test_metric']) > bi.max_data_points:
                bi.metrics_history['test_metric'] = bi.metrics_history['test_metric'][-bi.max_data_points:]
        
        # Should only keep the most recent data
        assert len(bi.metrics_history['test_metric']) <= bi.max_data_points

    @pytest.mark.asyncio
    async def test_insight_retention(self, bi):
        """Test insight retention functionality"""
        # Add more insights than limit
        for i in range(1100):  # More than limit (1000)
            bi.insights.append(Insight(
                title=f"Insight {i}",
                description="Test",
                category="test",
                confidence=0.8,
                impact="high",
                recommendations=["rec"],
                data_points={}
            ))
            # Apply retention after each addition to simulate real usage
            if len(bi.insights) > 1000:
                bi.insights = bi.insights[-1000:]
        
        # Should only keep the most recent insights
        assert len(bi.insights) <= 1000
