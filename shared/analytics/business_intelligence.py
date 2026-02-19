"""
Business Intelligence

This module provides business intelligence capabilities including:
- Advanced analytics and reporting
- Data visualization and dashboards
- KPI tracking and monitoring
- Business metrics and insights
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
from collections import deque, defaultdict
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# For advanced BI features
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import seaborn as sns
    import matplotlib.pyplot as plt
    BI_AVAILABLE = True
except ImportError:
    BI_AVAILABLE = False
    logging.warning("Advanced BI libraries not available. Install plotly, seaborn, and matplotlib for enhanced visualizations.")


class MetricType(Enum):
    """Metric types"""
    CALL_VOLUME = "call_volume"
    SUCCESS_RATE = "success_rate"
    REVENUE = "revenue"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    AGENT_PERFORMANCE = "agent_performance"
    COST_PER_CALL = "cost_per_call"
    CONVERSION_RATE = "conversion_rate"
    CHURN_RATE = "churn_rate"


class ChartType(Enum):
    """Chart types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    DASHBOARD = "dashboard"
    GAUGE = "gauge"
    FUNNEL = "funnel"


class KPICategory(Enum):
    """KPI categories"""
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    STRATEGIC = "strategic"


@dataclass
class Metric:
    """Business metric"""
    name: str
    value: float
    unit: str
    trend: float  # Percentage change
    target: Optional[float] = None
    category: KPICategory = KPICategory.OPERATIONAL
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChartData:
    """Chart data structure"""
    chart_type: ChartType
    title: str
    x_axis: List[Any]
    y_axis: List[Any]
    series: List[Dict[str, Any]]
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class Dashboard:
    """Dashboard structure"""
    name: str
    description: str
    charts: List[ChartData]
    metrics: List[Metric]
    layout: Dict[str, Any] = None
    refresh_interval: int = 300  # 5 minutes
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.layout is None:
            self.layout = {"columns": 2, "rows": 2}


@dataclass
class Insight:
    """Business insight"""
    title: str
    description: str
    category: str
    confidence: float
    impact: str  # high, medium, low
    recommendations: List[str]
    data_points: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BusinessIntelligence:
    """Business intelligence system for advanced analytics and reporting"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

        # Configuration
        self.data_retention_days = config.get('data_retention_days', 365)
        self.refresh_interval = config.get('refresh_interval', 300)
        self.max_data_points = config.get('max_data_points', 10000)
        self.alert_threshold = config.get('alert_threshold', 0.1)  # 10% change

        # State
        self.metrics_history: Dict[str, List[Metric]] = defaultdict(list)
        self.dashboards: Dict[str, Dashboard] = {}
        self.insights: List[Insight] = []
        self.alerts: List[Dict[str, Any]] = []
        self.data_cache: Dict[str, Any] = {}
        self.last_refresh: Dict[str, datetime] = {}

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize BI components"""
        try:
            # Create default dashboards
            self._create_default_dashboards()
            
            # Initialize data processors
            self.scaler = StandardScaler()
            self.pca = PCA(n_components=3)
            self.kmeans = KMeans(n_clusters=5, random_state=42)
            
            self.logger.info("Business Intelligence system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize BI components: {e}")

    def _create_default_dashboards(self):
        """Create default dashboards"""
        try:
            # Operational Dashboard
            operational_dashboard = Dashboard(
                name="Operational Overview",
                description="Key operational metrics and performance indicators",
                charts=[],
                metrics=[],
                layout={"columns": 3, "rows": 2}
            )
            self.dashboards["operational"] = operational_dashboard

            # Financial Dashboard
            financial_dashboard = Dashboard(
                name="Financial Performance",
                description="Revenue, costs, and financial KPIs",
                charts=[],
                metrics=[],
                layout={"columns": 2, "rows": 3}
            )
            self.dashboards["financial"] = financial_dashboard

            # Customer Dashboard
            customer_dashboard = Dashboard(
                name="Customer Analytics",
                description="Customer behavior, satisfaction, and engagement",
                charts=[],
                metrics=[],
                layout={"columns": 2, "rows": 2}
            )
            self.dashboards["customer"] = customer_dashboard

        except Exception as e:
            self.logger.error(f"Failed to create default dashboards: {e}")

    async def calculate_metrics(self, data: Dict[str, Any]) -> List[Metric]:
        """
        Calculate business metrics from data

        Args:
            data: Raw business data

        Returns:
            List[Metric]: Calculated metrics
        """
        try:
            metrics = []

            # Call Volume Metrics
            if 'calls' in data:
                call_volume = len(data['calls'])
                call_volume_trend = self._calculate_trend('call_volume', call_volume)
                metrics.append(Metric(
                    name="Total Calls",
                    value=call_volume,
                    unit="calls",
                    trend=call_volume_trend,
                    category=KPICategory.OPERATIONAL
                ))

            # Success Rate Metrics
            if 'calls' in data and data['calls']:
                successful_calls = sum(1 for call in data['calls'] if call.get('outcome') == 'success')
                success_rate = (successful_calls / len(data['calls'])) * 100
                success_rate_trend = self._calculate_trend('success_rate', success_rate)
                metrics.append(Metric(
                    name="Success Rate",
                    value=success_rate,
                    unit="%",
                    trend=success_rate_trend,
                    target=85.0,
                    category=KPICategory.OPERATIONAL
                ))

            # Revenue Metrics
            if 'revenue' in data:
                revenue = data['revenue']
                revenue_trend = self._calculate_trend('revenue', revenue)
                metrics.append(Metric(
                    name="Total Revenue",
                    value=revenue,
                    unit="$",
                    trend=revenue_trend,
                    category=KPICategory.FINANCIAL
                ))

            # Customer Satisfaction Metrics
            if 'satisfaction_scores' in data and data['satisfaction_scores']:
                avg_satisfaction = np.mean(data['satisfaction_scores'])
                satisfaction_trend = self._calculate_trend('customer_satisfaction', avg_satisfaction)
                metrics.append(Metric(
                    name="Customer Satisfaction",
                    value=avg_satisfaction,
                    unit="score",
                    trend=satisfaction_trend,
                    target=4.5,
                    category=KPICategory.CUSTOMER
                ))

            # Agent Performance Metrics
            if 'agent_performance' in data:
                agent_metrics = await self._calculate_agent_metrics(data['agent_performance'])
                metrics.extend(agent_metrics)

            # Cost Metrics
            if 'costs' in data:
                cost_metrics = await self._calculate_cost_metrics(data['costs'])
                metrics.extend(cost_metrics)

            # Update metrics history
            for metric in metrics:
                self.metrics_history[metric.name].append(metric)
                # Keep only recent data
                if len(self.metrics_history[metric.name]) > self.max_data_points:
                    self.metrics_history[metric.name] = self.metrics_history[metric.name][-self.max_data_points:]

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate metrics: {e}")
            return []

    async def _calculate_agent_metrics(self, agent_data: List[Dict[str, Any]]) -> List[Metric]:
        """Calculate agent performance metrics"""
        try:
            metrics = []

            if not agent_data:
                return metrics

            # Average calls per agent
            avg_calls_per_agent = np.mean([agent.get('calls_handled', 0) for agent in agent_data])
            metrics.append(Metric(
                name="Avg Calls per Agent",
                value=avg_calls_per_agent,
                unit="calls",
                trend=self._calculate_trend('avg_calls_per_agent', avg_calls_per_agent),
                category=KPICategory.OPERATIONAL
            ))

            # Average call duration
            avg_duration = np.mean([agent.get('avg_call_duration', 0) for agent in agent_data])
            metrics.append(Metric(
                name="Avg Call Duration",
                value=avg_duration,
                unit="seconds",
                trend=self._calculate_trend('avg_call_duration', avg_duration),
                category=KPICategory.OPERATIONAL
            ))

            # Agent satisfaction scores
            if any('satisfaction_score' in agent for agent in agent_data):
                agent_satisfaction = np.mean([agent.get('satisfaction_score', 0) for agent in agent_data])
                metrics.append(Metric(
                    name="Agent Satisfaction",
                    value=agent_satisfaction,
                    unit="score",
                    trend=self._calculate_trend('agent_satisfaction', agent_satisfaction),
                    category=KPICategory.OPERATIONAL
                ))

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate agent metrics: {e}")
            return []

    async def _calculate_cost_metrics(self, cost_data: Dict[str, Any]) -> List[Metric]:
        """Calculate cost-related metrics"""
        try:
            metrics = []

            # Cost per call
            if 'total_cost' in cost_data and 'total_calls' in cost_data and cost_data['total_calls'] > 0:
                cost_per_call = cost_data['total_cost'] / cost_data['total_calls']
                metrics.append(Metric(
                    name="Cost per Call",
                    value=cost_per_call,
                    unit="$",
                    trend=self._calculate_trend('cost_per_call', cost_per_call),
                    target=2.0,
                    category=KPICategory.FINANCIAL
                ))

            # Total operational costs
            if 'total_cost' in cost_data:
                metrics.append(Metric(
                    name="Total Operational Cost",
                    value=cost_data['total_cost'],
                    unit="$",
                    trend=self._calculate_trend('total_cost', cost_data['total_cost']),
                    category=KPICategory.FINANCIAL
                ))

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate cost metrics: {e}")
            return []

    def _calculate_trend(self, metric_name: str, current_value: float) -> float:
        """Calculate trend percentage for a metric"""
        try:
            if metric_name not in self.metrics_history or not self.metrics_history[metric_name]:
                return 0.0

            # Get previous value (last entry)
            previous_value = self.metrics_history[metric_name][-1].value

            if previous_value == 0:
                return 0.0

            return ((current_value - previous_value) / previous_value) * 100

        except Exception as e:
            self.logger.error(f"Failed to calculate trend for {metric_name}: {e}")
            return 0.0

    async def generate_charts(self, data: Dict[str, Any], chart_types: List[ChartType] = None) -> List[ChartData]:
        """
        Generate charts from data

        Args:
            data: Business data
            chart_types: Types of charts to generate

        Returns:
            List[ChartData]: Generated charts
        """
        try:
            if chart_types is None:
                chart_types = [ChartType.LINE, ChartType.BAR, ChartType.PIE]

            charts = []

            # Time series chart
            if ChartType.LINE in chart_types and 'time_series_data' in data:
                line_chart = await self._create_time_series_chart(data['time_series_data'])
                if line_chart:
                    charts.append(line_chart)

            # Bar chart for comparisons
            if ChartType.BAR in chart_types and 'comparison_data' in data:
                bar_chart = await self._create_comparison_chart(data['comparison_data'])
                if bar_chart:
                    charts.append(bar_chart)

            # Pie chart for distributions
            if ChartType.PIE in chart_types and 'distribution_data' in data:
                pie_chart = await self._create_distribution_chart(data['distribution_data'])
                if pie_chart:
                    charts.append(pie_chart)

            # Heatmap for correlations
            if ChartType.HEATMAP in chart_types and 'correlation_data' in data:
                heatmap = await self._create_correlation_heatmap(data['correlation_data'])
                if heatmap:
                    charts.append(heatmap)

            return charts

        except Exception as e:
            self.logger.error(f"Failed to generate charts: {e}")
            return []

    async def _create_time_series_chart(self, time_series_data: List[Dict[str, Any]]) -> Optional[ChartData]:
        """Create time series chart"""
        try:
            if not time_series_data:
                return None

            # Extract time and value data
            times = [item.get('timestamp', '') for item in time_series_data]
            values = [item.get('value', 0) for item in time_series_data]

            return ChartData(
                chart_type=ChartType.LINE,
                title="Performance Over Time",
                x_axis=times,
                y_axis=values,
                series=[{
                    'name': 'Performance',
                    'data': list(zip(times, values)),
                    'type': 'line'
                }],
                config={'responsive': True}
            )

        except Exception as e:
            self.logger.error(f"Failed to create time series chart: {e}")
            return None

    async def _create_comparison_chart(self, comparison_data: List[Dict[str, Any]]) -> Optional[ChartData]:
        """Create comparison bar chart"""
        try:
            if not comparison_data:
                return None

            categories = [item.get('category', '') for item in comparison_data]
            values = [item.get('value', 0) for item in comparison_data]

            return ChartData(
                chart_type=ChartType.BAR,
                title="Performance Comparison",
                x_axis=categories,
                y_axis=values,
                series=[{
                    'name': 'Performance',
                    'data': list(zip(categories, values)),
                    'type': 'bar'
                }],
                config={'responsive': True}
            )

        except Exception as e:
            self.logger.error(f"Failed to create comparison chart: {e}")
            return None

    async def _create_distribution_chart(self, distribution_data: List[Dict[str, Any]]) -> Optional[ChartData]:
        """Create distribution pie chart"""
        try:
            if not distribution_data:
                return None

            labels = [item.get('label', '') for item in distribution_data]
            values = [item.get('value', 0) for item in distribution_data]

            return ChartData(
                chart_type=ChartType.PIE,
                title="Data Distribution",
                x_axis=labels,
                y_axis=values,
                series=[{
                    'name': 'Distribution',
                    'data': list(zip(labels, values)),
                    'type': 'pie'
                }],
                config={'responsive': True}
            )

        except Exception as e:
            self.logger.error(f"Failed to create distribution chart: {e}")
            return None

    async def _create_correlation_heatmap(self, correlation_data: Dict[str, Any]) -> Optional[ChartData]:
        """Create correlation heatmap"""
        try:
            if not correlation_data or 'matrix' not in correlation_data:
                return None

            matrix = correlation_data['matrix']
            labels = correlation_data.get('labels', [])

            return ChartData(
                chart_type=ChartType.HEATMAP,
                title="Correlation Matrix",
                x_axis=labels,
                y_axis=labels,
                series=[{
                    'name': 'Correlation',
                    'data': matrix,
                    'type': 'heatmap'
                }],
                config={'responsive': True}
            )

        except Exception as e:
            self.logger.error(f"Failed to create correlation heatmap: {e}")
            return None

    async def create_dashboard(self, name: str, description: str, metrics: List[Metric], 
                             charts: List[ChartData], layout: Dict[str, Any] = None) -> Dashboard:
        """
        Create a new dashboard

        Args:
            name: Dashboard name
            description: Dashboard description
            metrics: List of metrics to display
            charts: List of charts to display
            layout: Dashboard layout configuration

        Returns:
            Dashboard: Created dashboard
        """
        try:
            dashboard = Dashboard(
                name=name,
                description=description,
                charts=charts,
                metrics=metrics,
                layout=layout or {"columns": 2, "rows": 2}
            )

            self.dashboards[name.lower().replace(' ', '_')] = dashboard
            return dashboard

        except Exception as e:
            self.logger.error(f"Failed to create dashboard: {e}")
            return None

    async def update_dashboard(self, dashboard_name: str, metrics: List[Metric] = None, 
                             charts: List[ChartData] = None) -> bool:
        """
        Update an existing dashboard

        Args:
            dashboard_name: Name of dashboard to update
            metrics: New metrics to add/update
            charts: New charts to add/update

        Returns:
            bool: True if update successful
        """
        try:
            if dashboard_name not in self.dashboards:
                return False

            dashboard = self.dashboards[dashboard_name]

            if metrics:
                dashboard.metrics = metrics

            if charts:
                dashboard.charts = charts

            dashboard.updated_at = datetime.utcnow()
            return True

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")
            return False

    async def generate_insights(self, data: Dict[str, Any]) -> List[Insight]:
        """
        Generate business insights from data

        Args:
            data: Business data

        Returns:
            List[Insight]: Generated insights
        """
        try:
            insights = []

            # Performance insights
            performance_insights = await self._analyze_performance(data)
            insights.extend(performance_insights)

            # Trend insights
            trend_insights = await self._analyze_trends(data)
            insights.extend(trend_insights)

            # Anomaly insights
            anomaly_insights = await self._detect_anomalies(data)
            insights.extend(anomaly_insights)

            # Customer insights
            customer_insights = await self._analyze_customer_behavior(data)
            insights.extend(customer_insights)

            # Add insights to history
            self.insights.extend(insights)

            # Keep only recent insights
            if len(self.insights) > 1000:
                self.insights = self.insights[-1000:]

            return insights

        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            return []

    async def _analyze_performance(self, data: Dict[str, Any]) -> List[Insight]:
        """Analyze performance patterns"""
        try:
            insights = []

            # Success rate analysis
            if 'calls' in data and data['calls']:
                success_rate = sum(1 for call in data['calls'] if call.get('outcome') == 'success') / len(data['calls'])
                
                if success_rate < 0.7:
                    insights.append(Insight(
                        title="Low Success Rate Detected",
                        description=f"Call success rate is {success_rate:.1%}, below target of 70%",
                        category="performance",
                        confidence=0.8,
                        impact="high",
                        recommendations=[
                            "Review call scripts and training materials",
                            "Analyze failed calls for common patterns",
                            "Implement additional agent training"
                        ],
                        data_points={"success_rate": success_rate}
                    ))

            # Revenue analysis
            if 'revenue' in data and 'target_revenue' in data:
                revenue_achievement = data['revenue'] / data['target_revenue']
                
                if revenue_achievement < 0.9:
                    insights.append(Insight(
                        title="Revenue Below Target",
                        description=f"Revenue achievement is {revenue_achievement:.1%} of target",
                        category="financial",
                        confidence=0.9,
                        impact="high",
                        recommendations=[
                            "Review pricing strategy",
                            "Analyze conversion rates",
                            "Focus on high-value opportunities"
                        ],
                        data_points={"revenue_achievement": revenue_achievement}
                    ))

            return insights

        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {e}")
            return []

    async def _analyze_trends(self, data: Dict[str, Any]) -> List[Insight]:
        """Analyze trends in data"""
        try:
            insights = []

            # Analyze metric trends
            for metric_name, history in self.metrics_history.items():
                if len(history) >= 3:
                    recent_values = [m.value for m in history[-3:]]
                    trend = (recent_values[-1] - recent_values[0]) / recent_values[0] if recent_values[0] != 0 else 0
                    
                    if abs(trend) > 0.1:  # 10% change
                        direction = "increasing" if trend > 0 else "decreasing"
                        insights.append(Insight(
                            title=f"{metric_name} Trend",
                            description=f"{metric_name} is {direction} by {abs(trend):.1%}",
                            category="trend",
                            confidence=0.7,
                            impact="medium",
                            recommendations=[
                                f"Monitor {metric_name} closely",
                                "Investigate root causes",
                                "Adjust strategies if needed"
                            ],
                            data_points={"trend": trend, "metric": metric_name}
                        ))

            return insights

        except Exception as e:
            self.logger.error(f"Failed to analyze trends: {e}")
            return []

    async def _detect_anomalies(self, data: Dict[str, Any]) -> List[Insight]:
        """Detect anomalies in data"""
        try:
            insights = []

            # Simple anomaly detection using z-score
            for metric_name, history in self.metrics_history.items():
                if len(history) >= 10:
                    values = [m.value for m in history[-10:]]
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    
                    if std_val > 0:
                        latest_value = values[-1]
                        z_score = abs((latest_value - mean_val) / std_val)
                        
                        if z_score > 2:  # More than 2 standard deviations
                            insights.append(Insight(
                                title=f"Anomaly Detected in {metric_name}",
                                description=f"{metric_name} value {latest_value} is {z_score:.1f} standard deviations from mean",
                                category="anomaly",
                                confidence=0.8,
                                impact="medium",
                                recommendations=[
                                    "Investigate the anomaly immediately",
                                    "Check for data quality issues",
                                    "Review recent changes or events"
                                ],
                                data_points={"z_score": z_score, "metric": metric_name, "value": latest_value}
                            ))

            return insights

        except Exception as e:
            self.logger.error(f"Failed to detect anomalies: {e}")
            return []

    async def _analyze_customer_behavior(self, data: Dict[str, Any]) -> List[Insight]:
        """Analyze customer behavior patterns"""
        try:
            insights = []

            # Customer satisfaction analysis
            if 'satisfaction_scores' in data and data['satisfaction_scores']:
                avg_satisfaction = np.mean(data['satisfaction_scores'])
                
                if avg_satisfaction < 4.0:
                    insights.append(Insight(
                        title="Customer Satisfaction Concerns",
                        description=f"Average satisfaction score is {avg_satisfaction:.1f}/5.0",
                        category="customer",
                        confidence=0.9,
                        impact="high",
                        recommendations=[
                            "Review customer feedback",
                            "Improve service quality",
                            "Address common complaints"
                        ],
                        data_points={"avg_satisfaction": avg_satisfaction}
                    ))

            # Churn analysis
            if 'churn_rate' in data:
                churn_rate = data['churn_rate']
                
                if churn_rate > 0.05:  # 5% churn rate
                    insights.append(Insight(
                        title="High Customer Churn",
                        description=f"Customer churn rate is {churn_rate:.1%}",
                        category="customer",
                        confidence=0.8,
                        impact="high",
                        recommendations=[
                            "Implement retention strategies",
                            "Analyze churn reasons",
                            "Improve customer experience"
                        ],
                        data_points={"churn_rate": churn_rate}
                    ))

            return insights

        except Exception as e:
            self.logger.error(f"Failed to analyze customer behavior: {e}")
            return []

    async def generate_report(self, report_type: str, data: Dict[str, Any], 
                            format: str = "json") -> Dict[str, Any]:
        """
        Generate business report

        Args:
            report_type: Type of report to generate
            data: Business data
            format: Report format (json, html, pdf)

        Returns:
            Dict[str, Any]: Generated report
        """
        try:
            # Calculate metrics
            metrics = await self.calculate_metrics(data)
            
            # Generate charts
            charts = await self.generate_charts(data)
            
            # Generate insights
            insights = await self.generate_insights(data)

            report = {
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "metrics": [self._metric_to_dict(m) for m in metrics],
                "charts": [self._chart_to_dict(c) for c in charts],
                "insights": [self._insight_to_dict(i) for i in insights],
                "summary": {
                    "total_metrics": len(metrics),
                    "total_charts": len(charts),
                    "total_insights": len(insights),
                    "key_findings": [i.title for i in insights[:5]]
                }
            }

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return {}

    def _metric_to_dict(self, metric: Metric) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        return {
            "name": metric.name,
            "value": metric.value,
            "unit": metric.unit,
            "trend": metric.trend,
            "target": metric.target,
            "category": metric.category.value,
            "timestamp": metric.timestamp.isoformat(),
            "metadata": metric.metadata
        }

    def _chart_to_dict(self, chart: ChartData) -> Dict[str, Any]:
        """Convert chart to dictionary"""
        return {
            "chart_type": chart.chart_type.value,
            "title": chart.title,
            "x_axis": chart.x_axis,
            "y_axis": chart.y_axis,
            "series": chart.series,
            "config": chart.config
        }

    def _insight_to_dict(self, insight: Insight) -> Dict[str, Any]:
        """Convert insight to dictionary"""
        return {
            "title": insight.title,
            "description": insight.description,
            "category": insight.category,
            "confidence": insight.confidence,
            "impact": insight.impact,
            "recommendations": insight.recommendations,
            "data_points": insight.data_points,
            "timestamp": insight.timestamp.isoformat()
        }

    async def export_data(self, data_type: str, format: str = "csv") -> str:
        """
        Export data in specified format

        Args:
            data_type: Type of data to export
            format: Export format (csv, json, excel)

        Returns:
            str: Exported data
        """
        try:
            if data_type == "metrics":
                data = self.metrics_history
            elif data_type == "insights":
                data = self.insights
            elif data_type == "dashboards":
                data = self.dashboards
            else:
                return ""

            if format == "json":
                return json.dumps(data, default=str, indent=2)
            elif format == "csv":
                return self._convert_to_csv(data)
            else:
                return ""

        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return ""

    def _convert_to_csv(self, data: Any) -> str:
        """Convert data to CSV format"""
        try:
            if isinstance(data, dict):
                # Convert metrics history
                csv_lines = []
                for metric_name, history in data.items():
                    csv_lines.append(f"Metric,Value,Unit,Trend,Timestamp")
                    for metric in history:
                        csv_lines.append(f"{metric.name},{metric.value},{metric.unit},{metric.trend},{metric.timestamp}")
                    csv_lines.append("")
                return "\n".join(csv_lines)
            else:
                return ""

        except Exception as e:
            self.logger.error(f"Failed to convert to CSV: {e}")
            return ""

    def get_system_status(self) -> Dict[str, Any]:
        """Get BI system status"""
        try:
            return {
                "total_metrics": sum(len(history) for history in self.metrics_history.values()),
                "total_dashboards": len(self.dashboards),
                "total_insights": len(self.insights),
                "total_alerts": len(self.alerts),
                "last_refresh": {k: v.isoformat() for k, v in self.last_refresh.items()},
                "data_retention_days": self.data_retention_days,
                "max_data_points": self.max_data_points
            }

        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    config = {
        'data_retention_days': 365,
        'refresh_interval': 300,
        'max_data_points': 10000,
        'alert_threshold': 0.1
    }

    bi = BusinessIntelligence(config)
    print("Business Intelligence system initialized")
