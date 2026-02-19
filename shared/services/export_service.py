"""
Export Service for Analytics Data

Provides CSV and PDF export functionality for profit margin analytics.
Supports on-demand exports and scheduled report generation.
"""
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting analytics data to various formats.

    Features:
    - CSV export with custom column selection
    - Summary and detailed views
    - Date range filtering
    - Provider filtering
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the export service.

        Args:
            db: AsyncIOMotor database instance
        """
        self.db = db
        self.collection = db.internal_cost_tracking

    async def export_to_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        providers: Optional[List[str]] = None,
        include_summary: bool = True,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Export analytics data to CSV format.

        Args:
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            providers: List of providers to include (optional, all if None)
            include_summary: Whether to include summary section
            tenant_id: Tenant ID for filtering (deprecated, use organization_id)
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            CSV string content
        """
        try:
            # Use organization_id if provided, fallback to tenant_id for backward compatibility
            filter_id = organization_id or tenant_id

            # Build query
            query: Dict[str, Any] = {}

            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date

            if providers:
                query["provider"] = {"$in": providers}

            if filter_id:
                query["tenant_id"] = filter_id

            # Fetch data
            cursor = self.collection.find(query).sort("timestamp", -1)
            records = await cursor.to_list(length=None)

            # Generate CSV
            output = io.StringIO()

            # Write summary section if requested
            if include_summary:
                await self._write_summary_section(output, records)
                output.write("\n\n")

            # Write detailed records
            await self._write_detailed_section(output, records)

            csv_content = output.getvalue()
            output.close()

            logger.info(f"Generated CSV export with {len(records)} records for organization={filter_id}")
            return csv_content

        except Exception as e:
            logger.error(f"Failed to export to CSV for organization={organization_id or tenant_id}: {e}")
            raise

    async def _write_summary_section(self, output: io.StringIO, records: List[Dict]):
        """Write summary statistics section to CSV."""
        output.write("PROFIT MARGIN SUMMARY\n")
        output.write("=" * 80 + "\n\n")

        if not records:
            output.write("No data available\n")
            return

        # Calculate overall metrics
        total_revenue = sum(r.get("customer_charge", 0) for r in records)
        total_costs = sum(r.get("actual_cost", 0) for r in records)
        total_profit = total_revenue - total_costs
        margin_percentage = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Write overall summary
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Revenue", f"GHS {total_revenue:.2f}"])
        writer.writerow(["Total Costs", f"GHS {total_costs:.2f}"])
        writer.writerow(["Total Profit", f"GHS {total_profit:.2f}"])
        writer.writerow(["Profit Margin", f"{margin_percentage:.2f}%"])
        writer.writerow(["Transaction Count", len(records)])

        # Get date range
        if records:
            dates = [r.get("timestamp") for r in records if r.get("timestamp")]
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                writer.writerow(["Date Range", f"{min_date.date()} to {max_date.date()}"])

        output.write("\n")

        # Provider breakdown
        output.write("BREAKDOWN BY PROVIDER\n")
        provider_stats = self._calculate_provider_stats(records)

        writer.writerow([
            "Provider",
            "Revenue (GHS)",
            "Costs (GHS)",
            "Profit (GHS)",
            "Margin (%)",
            "Transactions"
        ])

        for provider, stats in sorted(provider_stats.items()):
            writer.writerow([
                provider.upper(),
                f"{stats['revenue']:.2f}",
                f"{stats['costs']:.2f}",
                f"{stats['profit']:.2f}",
                f"{stats['margin']:.2f}",
                stats['count']
            ])

    async def _write_detailed_section(self, output: io.StringIO, records: List[Dict]):
        """Write detailed transaction records to CSV."""
        output.write("DETAILED TRANSACTIONS\n")
        output.write("=" * 80 + "\n\n")

        writer = csv.writer(output)

        # Headers
        headers = [
            "Date",
            "Provider",
            "Service Type",
            "Customer Charge (GHS)",
            "Actual Cost (GHS)",
            "Profit (GHS)",
            "Margin (%)",
            "Tenant ID",
            "Call ID"
        ]
        writer.writerow(headers)

        # Records
        for record in records:
            revenue = record.get("customer_charge", 0)
            cost = record.get("actual_cost", 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0

            timestamp = record.get("timestamp")
            date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

            row = [
                date_str,
                record.get("provider", "").upper(),
                record.get("service_type", ""),
                f"{revenue:.2f}",
                f"{cost:.2f}",
                f"{profit:.2f}",
                f"{margin:.2f}",
                record.get("tenant_id", ""),
                record.get("call_id", "")
            ]
            writer.writerow(row)

    def _calculate_provider_stats(self, records: List[Dict]) -> Dict[str, Dict]:
        """Calculate statistics per provider."""
        stats = {}

        for record in records:
            provider = record.get("provider", "unknown")

            if provider not in stats:
                stats[provider] = {
                    "revenue": 0,
                    "costs": 0,
                    "profit": 0,
                    "margin": 0,
                    "count": 0
                }

            revenue = record.get("customer_charge", 0)
            cost = record.get("actual_cost", 0)

            stats[provider]["revenue"] += revenue
            stats[provider]["costs"] += cost
            stats[provider]["profit"] += (revenue - cost)
            stats[provider]["count"] += 1

        # Calculate margins
        for provider, data in stats.items():
            if data["revenue"] > 0:
                data["margin"] = (data["profit"] / data["revenue"]) * 100

        return stats

    async def get_export_preview(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        providers: Optional[List[str]] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a preview of what will be exported.

        Returns:
            Dictionary with preview statistics
        """
        try:
            # Build query
            query: Dict[str, Any] = {}

            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date

            if providers:
                query["provider"] = {"$in": providers}

            if tenant_id:
                query["tenant_id"] = tenant_id

            # Count records
            total_records = await self.collection.count_documents(query)

            # Get date range
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "min_date": {"$min": "$timestamp"},
                        "max_date": {"$max": "$timestamp"},
                        "total_revenue": {"$sum": "$customer_charge"},
                        "total_costs": {"$sum": "$actual_cost"}
                    }
                }
            ]

            result = await self.collection.aggregate(pipeline).to_list(length=1)

            if result:
                data = result[0]
                total_revenue = data.get("total_revenue", 0)
                total_costs = data.get("total_costs", 0)

                return {
                    "total_records": total_records,
                    "date_range": {
                        "start": data.get("min_date"),
                        "end": data.get("max_date")
                    },
                    "summary": {
                        "total_revenue": total_revenue,
                        "total_costs": total_costs,
                        "total_profit": total_revenue - total_costs,
                        "estimated_size_kb": total_records * 0.5  # Rough estimate
                    }
                }
            else:
                return {
                    "total_records": 0,
                    "date_range": None,
                    "summary": {
                        "total_revenue": 0,
                        "total_costs": 0,
                        "total_profit": 0,
                        "estimated_size_kb": 0
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get export preview: {e}")
            raise


# Singleton instance
_export_service_instance = None


def get_export_service(db: AsyncIOMotorDatabase) -> ExportService:
    """Get or create export service instance."""
    global _export_service_instance
    if _export_service_instance is None:
        _export_service_instance = ExportService(db)
    return _export_service_instance
