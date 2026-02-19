"""
Metabase dashboard service for helpdesk analytics visualization.
Creates and manages comprehensive dashboards for SLA, FRT, CSAT, and operational metrics.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)

class MetabaseDashboardService:
    """Service for creating and managing Metabase dashboards."""

    def __init__(self):
        self.metabase_url = "https://metabase.ailabsafrica.com"
        self.session_token = None  # TODO: Implement authentication
        self.timeout = aiohttp.ClientTimeout(total=30)

    def create_helpdesk_dashboard_config(self, company_name: str, helpdesk_id: str) -> Dict[str, Any]:
        """
        Create comprehensive Metabase dashboard configuration for helpdesk analytics.

        Args:
            company_name: Company name for dashboard
            helpdesk_id: Helpdesk ID for data filtering

        Returns:
            Complete dashboard configuration
        """
        dashboard_config = {
            "name": f"{company_name} - Helpdesk Analytics Dashboard",
            "description": f"Comprehensive analytics dashboard for {company_name} helpdesk operations including SLA, performance, and customer satisfaction metrics.",
            "parameters": [
                {
                    "id": "date_range",
                    "name": "Date Range",
                    "type": "date/range",
                    "default": "past30days"
                },
                {
                    "id": "helpdesk_id_filter",
                    "name": "Helpdesk ID",
                    "type": "category",
                    "default": helpdesk_id
                }
            ],
            "cards": [
                self._create_overview_cards(),
                self._create_sla_performance_cards(),
                self._create_customer_satisfaction_cards(),
                self._create_operational_metrics_cards(),
                self._create_trend_analysis_cards(),
                self._create_escalation_analysis_cards()
            ],
            "width": 18,
            "auto_apply_filters": True,
            "enable_embedding": True,
            "cache_ttl": 300  # 5 minutes cache
        }

        return dashboard_config

    def _create_overview_cards(self) -> List[Dict[str, Any]]:
        """Create overview KPI cards for the dashboard."""
        return [
            {
                "id": "total_calls_kpi",
                "name": "Total Calls",
                "description": "Total number of calls in selected period",
                "visualization_settings": {
                    "graph.dimensions": ["timestamp"],
                    "graph.metrics": ["count"],
                    "scalar.field": "count",
                    "scalar.switch_positive": "arrow",
                    "scalar.compact_primary_number": True
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [["count"]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ]
                    },
                    "type": "query"
                },
                "display": "scalar",
                "position": {"col": 0, "row": 0, "sizeX": 3, "sizeY": 3}
            },
            {
                "id": "first_contact_resolution_rate",
                "name": "First Contact Resolution Rate",
                "description": "Percentage of issues resolved on first contact",
                "visualization_settings": {
                    "scalar.field": "fcr_rate",
                    "scalar.suffix": "%",
                    "scalar.switch_positive": "arrow"
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [
                            ["*",
                                ["/",
                                    ["count-where", ["=", ["field", "escalated", None], False]],
                                    ["count"]
                                ],
                                100
                            ]
                        ],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ]
                    },
                    "type": "query"
                },
                "display": "scalar",
                "position": {"col": 3, "row": 0, "sizeX": 3, "sizeY": 3}
            },
            {
                "id": "avg_customer_satisfaction",
                "name": "Average Customer Satisfaction",
                "description": "Average CSAT score from customer feedback",
                "visualization_settings": {
                    "scalar.field": "avg_satisfaction",
                    "scalar.suffix": "/5",
                    "scalar.switch_positive": "arrow"
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "customer_feedback",
                        "aggregation": [["avg", ["field", "rating", None]]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "created_at", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ]
                    },
                    "type": "query"
                },
                "display": "scalar",
                "position": {"col": 6, "row": 0, "sizeX": 3, "sizeY": 3}
            },
            {
                "id": "sla_compliance_rate",
                "name": "Overall SLA Compliance",
                "description": "Percentage of SLA targets met",
                "visualization_settings": {
                    "scalar.field": "sla_compliance",
                    "scalar.suffix": "%",
                    "scalar.switch_positive": "arrow"
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "sla_metrics",
                        "aggregation": [
                            ["*",
                                ["/",
                                    ["+",
                                        ["sum", ["field", "first_response_sla_met", None]],
                                        ["sum", ["field", "resolution_sla_met", None]]
                                    ],
                                    ["*", ["count"], 2]
                                ],
                                100
                            ]
                        ],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "period_date", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ]
                    },
                    "type": "query"
                },
                "display": "scalar",
                "position": {"col": 9, "row": 0, "sizeX": 3, "sizeY": 3}
            }
        ]

    def _create_sla_performance_cards(self) -> List[Dict[str, Any]]:
        """Create SLA performance monitoring cards."""
        return [
            {
                "id": "first_response_time_trend",
                "name": "First Response Time Trend",
                "description": "Daily trend of average first response time vs SLA target",
                "visualization_settings": {
                    "graph.dimensions": ["date"],
                    "graph.metrics": ["avg_first_response_time", "sla_target"],
                    "line.interpolate": "linear",
                    "line.marker_enabled": True,
                    "graph.goal_line": 1.0
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "daily_sla_metrics",
                        "aggregation": [
                            ["avg", ["field", "first_response_time_hours", None]],
                            ["avg", ["field", "first_response_sla_target", None]]
                        ],
                        "breakout": [["field", "date", {"temporal-unit": "day"}]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "date", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["asc", ["field", "date", {"temporal-unit": "day"}]]]
                    },
                    "type": "query"
                },
                "display": "line",
                "position": {"col": 0, "row": 3, "sizeX": 9, "sizeY": 4}
            },
            {
                "id": "resolution_time_distribution",
                "name": "Resolution Time Distribution",
                "description": "Distribution of resolution times vs SLA target",
                "visualization_settings": {
                    "graph.dimensions": ["resolution_time_bucket"],
                    "graph.metrics": ["count"],
                    "bar.series_colors": {"Within SLA": "#509EE3", "SLA Breach": "#ED6E6E"}
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [["count"]],
                        "breakout": [
                            ["case",
                                [
                                    [["<=", ["field", "resolution_time_hours", None], 24], "Within SLA"],
                                    [["else"], "SLA Breach"]
                                ]
                            ]
                        ],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"],
                            ["not-null", ["field", "resolution_time_hours", None]]
                        ]
                    },
                    "type": "query"
                },
                "display": "bar",
                "position": {"col": 9, "row": 3, "sizeX": 9, "sizeY": 4}
            },
            {
                "id": "sla_violations_table",
                "name": "Recent SLA Violations",
                "description": "Detailed view of recent SLA violations and reasons",
                "visualization_settings": {
                    "table.pivot_column": None,
                    "table.cell_column": None
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "sla_violations",
                        "fields": [
                            ["field", "call_id", None],
                            ["field", "violation_type", None],
                            ["field", "target_time", None],
                            ["field", "actual_time", None],
                            ["field", "reason", None],
                            ["field", "created_at", None]
                        ],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "created_at", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["desc", ["field", "created_at", None]]],
                        "limit": 10
                    },
                    "type": "query"
                },
                "display": "table",
                "position": {"col": 0, "row": 7, "sizeX": 18, "sizeY": 4}
            }
        ]

    def _create_customer_satisfaction_cards(self) -> List[Dict[str, Any]]:
        """Create customer satisfaction monitoring cards."""
        return [
            {
                "id": "csat_score_trend",
                "name": "CSAT Score Trend",
                "description": "Daily customer satisfaction score trend",
                "visualization_settings": {
                    "graph.dimensions": ["date"],
                    "graph.metrics": ["avg_csat"],
                    "line.interpolate": "cardinal",
                    "line.marker_enabled": True,
                    "graph.goal_line": 4.5
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "customer_feedback",
                        "aggregation": [["avg", ["field", "rating", None]]],
                        "breakout": [["field", "created_at", {"temporal-unit": "day"}]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "created_at", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["asc", ["field", "created_at", {"temporal-unit": "day"}]]]
                    },
                    "type": "query"
                },
                "display": "line",
                "position": {"col": 0, "row": 11, "sizeX": 9, "sizeY": 4}
            },
            {
                "id": "rating_distribution",
                "name": "Rating Distribution",
                "description": "Distribution of customer ratings",
                "visualization_settings": {
                    "graph.dimensions": ["rating"],
                    "graph.metrics": ["count"],
                    "pie.show_legend": True,
                    "pie.show_total": True
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "customer_feedback",
                        "aggregation": [["count"]],
                        "breakout": [["field", "rating", None]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "created_at", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["asc", ["field", "rating", None]]]
                    },
                    "type": "query"
                },
                "display": "pie",
                "position": {"col": 9, "row": 11, "sizeX": 9, "sizeY": 4}
            }
        ]

    def _create_operational_metrics_cards(self) -> List[Dict[str, Any]]:
        """Create operational performance cards."""
        return [
            {
                "id": "call_volume_trend",
                "name": "Daily Call Volume",
                "description": "Daily trend of incoming call volume",
                "visualization_settings": {
                    "graph.dimensions": ["date"],
                    "graph.metrics": ["call_count"],
                    "line.interpolate": "linear",
                    "line.marker_enabled": True
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [["count"]],
                        "breakout": [["field", "timestamp", {"temporal-unit": "day"}]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["asc", ["field", "timestamp", {"temporal-unit": "day"}]]]
                    },
                    "type": "query"
                },
                "display": "line",
                "position": {"col": 0, "row": 15, "sizeX": 9, "sizeY": 4}
            },
            {
                "id": "intent_breakdown",
                "name": "Call Intent Breakdown",
                "description": "Distribution of call intents",
                "visualization_settings": {
                    "graph.dimensions": ["intent"],
                    "graph.metrics": ["count"],
                    "bar.series_colors": {
                        "information_request": "#509EE3",
                        "technical_support": "#88BF4D",
                        "billing_inquiry": "#F9CF48",
                        "complaint": "#ED6E6E"
                    }
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [["count"]],
                        "breakout": [["field", "intent", None]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["desc", ["aggregation", 0]]]
                    },
                    "type": "query"
                },
                "display": "bar",
                "position": {"col": 9, "row": 15, "sizeX": 9, "sizeY": 4}
            }
        ]

    def _create_trend_analysis_cards(self) -> List[Dict[str, Any]]:
        """Create trend analysis cards for performance monitoring."""
        return [
            {
                "id": "escalation_rate_trend",
                "name": "Escalation Rate Trend",
                "description": "Daily escalation rate trend",
                "visualization_settings": {
                    "graph.dimensions": ["date"],
                    "graph.metrics": ["escalation_rate"],
                    "line.interpolate": "linear",
                    "line.marker_enabled": True,
                    "graph.goal_line": 15.0
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [
                            ["*",
                                ["/",
                                    ["count-where", ["=", ["field", "escalated", None], True]],
                                    ["count"]
                                ],
                                100
                            ]
                        ],
                        "breakout": [["field", "timestamp", {"temporal-unit": "day"}]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["asc", ["field", "timestamp", {"temporal-unit": "day"}]]]
                    },
                    "type": "query"
                },
                "display": "line",
                "position": {"col": 0, "row": 19, "sizeX": 18, "sizeY": 4}
            }
        ]

    def _create_escalation_analysis_cards(self) -> List[Dict[str, Any]]:
        """Create escalation analysis cards."""
        return [
            {
                "id": "escalation_reasons",
                "name": "Top Escalation Reasons",
                "description": "Most common reasons for escalation",
                "visualization_settings": {
                    "graph.dimensions": ["escalation_reason"],
                    "graph.metrics": ["count"],
                    "bar.series_colors": {"Complex Issue": "#ED6E6E", "Low Confidence": "#F9CF48"}
                },
                "dataset_query": {
                    "database": 1,
                    "query": {
                        "source-table": "helpdesk_call_logs",
                        "aggregation": [["count"]],
                        "breakout": [["field", "escalation_reason", None]],
                        "filter": [
                            "and",
                            ["=", ["field", "helpdesk_id", None], "{{helpdesk_id_filter}}"],
                            ["=", ["field", "escalated", None], True],
                            ["between", ["field", "timestamp", None], "{{date_range.start}}", "{{date_range.end}}"]
                        ],
                        "order-by": [["desc", ["aggregation", 0]]],
                        "limit": 10
                    },
                    "type": "query"
                },
                "display": "bar",
                "position": {"col": 0, "row": 23, "sizeX": 18, "sizeY": 4}
            }
        ]

    def create_executive_summary_dashboard(self, company_name: str) -> Dict[str, Any]:
        """
        Create executive summary dashboard with high-level KPIs.

        Args:
            company_name: Company name for dashboard

        Returns:
            Executive dashboard configuration
        """
        return {
            "name": f"{company_name} - Executive Helpdesk Summary",
            "description": "Executive-level overview of helpdesk performance and key metrics",
            "parameters": [
                {
                    "id": "time_period",
                    "name": "Time Period",
                    "type": "date/range",
                    "default": "past7days"
                }
            ],
            "cards": [
                {
                    "id": "executive_scorecard",
                    "name": "Helpdesk Scorecard",
                    "display": "gauge",
                    "visualization_settings": {
                        "gauge.segments": [
                            {"min": 0, "max": 70, "color": "#ED6E6E", "label": "Needs Improvement"},
                            {"min": 70, "max": 85, "color": "#F9CF48", "label": "Good"},
                            {"min": 85, "max": 100, "color": "#88BF4D", "label": "Excellent"}
                        ]
                    }
                }
            ],
            "width": 12,
            "enable_embedding": True,
            "cache_ttl": 600  # 10 minutes cache for executive dashboard
        }

    async def deploy_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy dashboard configuration to Metabase.

        Args:
            dashboard_config: Complete dashboard configuration

        Returns:
            Deployment result with dashboard URL
        """
        try:
            # Simulate dashboard deployment
            # In production, use actual Metabase API
            dashboard_id = f"dashboard_{hash(dashboard_config['name']) % 10000}"

            logger.info(f"Deploying dashboard: {dashboard_config['name']}")

            deployment_result = {
                "success": True,
                "dashboard_id": dashboard_id,
                "dashboard_url": f"{self.metabase_url}/dashboard/{dashboard_id}",
                "embed_url": f"{self.metabase_url}/embed/dashboard/{dashboard_id}",
                "created_at": datetime.utcnow().isoformat(),
                "cards_count": len(dashboard_config.get("cards", [])),
                "refresh_schedule": "Every 5 minutes"
            }

            return deployment_result

        except Exception as e:
            logger.error(f"Error deploying dashboard: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_dashboard_schema(self) -> Dict[str, Any]:
        """
        Get the required database schema for Metabase dashboards.

        Returns:
            Database schema requirements
        """
        return {
            "tables": [
                {
                    "name": "helpdesk_call_logs",
                    "description": "Main table for call logs and outcomes",
                    "columns": [
                        {"name": "call_id", "type": "VARCHAR", "description": "Unique call identifier"},
                        {"name": "helpdesk_id", "type": "VARCHAR", "description": "Helpdesk identifier"},
                        {"name": "customer_phone", "type": "VARCHAR", "description": "Customer phone number"},
                        {"name": "customer_email", "type": "VARCHAR", "description": "Customer email"},
                        {"name": "transcript", "type": "TEXT", "description": "Call transcript"},
                        {"name": "intent", "type": "VARCHAR", "description": "Classified call intent"},
                        {"name": "rag_confidence", "type": "DECIMAL", "description": "RAG response confidence"},
                        {"name": "escalated", "type": "BOOLEAN", "description": "Whether call was escalated"},
                        {"name": "escalation_reason", "type": "VARCHAR", "description": "Reason for escalation"},
                        {"name": "resolution_time_hours", "type": "DECIMAL", "description": "Time to resolution in hours"},
                        {"name": "timestamp", "type": "TIMESTAMP", "description": "Call timestamp"}
                    ]
                },
                {
                    "name": "customer_feedback",
                    "description": "Customer satisfaction ratings and feedback",
                    "columns": [
                        {"name": "feedback_id", "type": "VARCHAR", "description": "Unique feedback identifier"},
                        {"name": "call_id", "type": "VARCHAR", "description": "Related call ID"},
                        {"name": "helpdesk_id", "type": "VARCHAR", "description": "Helpdesk identifier"},
                        {"name": "rating", "type": "INTEGER", "description": "Customer rating (1-5)"},
                        {"name": "feedback_text", "type": "TEXT", "description": "Customer feedback text"},
                        {"name": "created_at", "type": "TIMESTAMP", "description": "Feedback timestamp"}
                    ]
                },
                {
                    "name": "sla_metrics",
                    "description": "SLA performance tracking",
                    "columns": [
                        {"name": "metric_id", "type": "VARCHAR", "description": "Unique metric identifier"},
                        {"name": "helpdesk_id", "type": "VARCHAR", "description": "Helpdesk identifier"},
                        {"name": "period_date", "type": "DATE", "description": "Metric period date"},
                        {"name": "first_response_sla_met", "type": "DECIMAL", "description": "First response SLA compliance rate"},
                        {"name": "resolution_sla_met", "type": "DECIMAL", "description": "Resolution SLA compliance rate"},
                        {"name": "avg_first_response_time", "type": "DECIMAL", "description": "Average first response time in hours"},
                        {"name": "avg_resolution_time", "type": "DECIMAL", "description": "Average resolution time in hours"}
                    ]
                }
            ],
            "views": [
                {
                    "name": "daily_sla_metrics",
                    "description": "Daily aggregated SLA metrics",
                    "sql": """
                        SELECT
                            DATE(timestamp) as date,
                            helpdesk_id,
                            AVG(first_response_time_hours) as avg_first_response_time,
                            AVG(resolution_time_hours) as avg_resolution_time,
                            1.0 as first_response_sla_target,
                            24.0 as resolution_sla_target
                        FROM helpdesk_call_logs
                        WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY DATE(timestamp), helpdesk_id
                    """
                }
            ],
            "indexes": [
                {"table": "helpdesk_call_logs", "columns": ["helpdesk_id", "timestamp"]},
                {"table": "customer_feedback", "columns": ["helpdesk_id", "created_at"]},
                {"table": "sla_metrics", "columns": ["helpdesk_id", "period_date"]}
            ]
        }

# Global service instance
metabase_dashboard_service = MetabaseDashboardService()