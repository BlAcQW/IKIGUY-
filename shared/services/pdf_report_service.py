"""
PDF Report Generation Service

Creates professional PDF reports for profit margin analytics using ReportLab.
Includes summary statistics, provider breakdowns, and trend visualizations.
"""
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class PDFReportService:
    """
    Service for generating PDF reports of analytics data.

    Features:
    - Professional report layout
    - Summary statistics with visual indicators
    - Provider breakdown tables
    - Customizable date ranges and filters
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the PDF report service.

        Args:
            db: AsyncIOMotor database instance
        """
        self.db = db
        self.collection = db.internal_cost_tracking

    async def generate_pdf_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        providers: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        include_details: bool = True
    ) -> bytes:
        """
        Generate a PDF report of profit margin analytics.

        Args:
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            providers: List of providers to include (optional, all if None)
            tenant_id: Tenant ID for filtering (optional, admin sees all)
            include_details: Whether to include detailed transaction list

        Returns:
            PDF file content as bytes
        """
        try:
            # Fetch data
            query = self._build_query(start_date, end_date, providers, tenant_id)
            cursor = self.collection.find(query).sort("timestamp", -1)
            records = await cursor.to_list(length=None)

            # Generate PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Build content
            story = []
            styles = getSampleStyleSheet()

            # Add custom styles
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=30
            ))

            styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2d3748'),
                spaceAfter=12,
                spaceBefore=12
            ))

            # Title
            story.append(Paragraph("Profit Margin Analytics Report", styles['CustomTitle']))
            story.append(Spacer(1, 0.2 * inch))

            # Report metadata
            story.append(self._create_metadata_section(start_date, end_date, styles))
            story.append(Spacer(1, 0.3 * inch))

            # Summary section
            story.append(Paragraph("Executive Summary", styles['SectionHeader']))
            story.append(self._create_summary_table(records))
            story.append(Spacer(1, 0.3 * inch))

            # Provider breakdown
            story.append(Paragraph("Provider Performance", styles['SectionHeader']))
            story.append(self._create_provider_table(records))
            story.append(Spacer(1, 0.3 * inch))

            # Detailed transactions (if requested)
            if include_details and records:
                story.append(PageBreak())
                story.append(Paragraph("Detailed Transactions", styles['SectionHeader']))
                story.append(Spacer(1, 0.2 * inch))
                story.append(self._create_details_table(records[:100]))  # Limit to 100 records

                if len(records) > 100:
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(
                        f"<i>Note: Showing first 100 of {len(records)} transactions</i>",
                        styles['Normal']
                    ))

            # Build PDF
            doc.build(story)

            pdf_content = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated PDF report with {len(records)} records")
            return pdf_content

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

    def _build_query(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        providers: Optional[List[str]],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build MongoDB query from parameters."""
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

        return query

    def _create_metadata_section(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        styles
    ) -> Table:
        """Create report metadata section."""
        data = [
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]

        if start_date:
            data.append(["Start Date:", start_date.strftime("%Y-%m-%d")])
        if end_date:
            data.append(["End Date:", end_date.strftime("%Y-%m-%d")])

        table = Table(data, colWidths=[2 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
        ]))

        return table

    def _create_summary_table(self, records: List[Dict]) -> Table:
        """Create summary statistics table."""
        if not records:
            return Table([["No data available"]])

        # Calculate metrics
        total_revenue = sum(r.get("customer_charge", 0) for r in records)
        total_costs = sum(r.get("actual_cost", 0) for r in records)
        total_profit = total_revenue - total_costs
        margin_percentage = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Determine margin status
        margin_color = self._get_margin_color(margin_percentage)

        data = [
            ["Metric", "Value", "Status"],
            ["Total Revenue", f"GHS {total_revenue:,.2f}", ""],
            ["Total Costs", f"GHS {total_costs:,.2f}", ""],
            ["Total Profit", f"GHS {total_profit:,.2f}", ""],
            ["Profit Margin", f"{margin_percentage:.2f}%", self._get_margin_status(margin_percentage)],
            ["Transaction Count", f"{len(records):,}", ""],
        ]

        table = Table(data, colWidths=[2 * inch, 2 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),

            # Highlight profit margin row
            ('BACKGROUND', (0, 4), (-1, 4), margin_color),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ]))

        return table

    def _create_provider_table(self, records: List[Dict]) -> Table:
        """Create provider breakdown table."""
        if not records:
            return Table([["No data available"]])

        # Calculate provider stats
        provider_stats = {}
        for record in records:
            provider = record.get("provider", "unknown")

            if provider not in provider_stats:
                provider_stats[provider] = {
                    "revenue": 0,
                    "costs": 0,
                    "profit": 0,
                    "count": 0
                }

            revenue = record.get("customer_charge", 0)
            cost = record.get("actual_cost", 0)

            provider_stats[provider]["revenue"] += revenue
            provider_stats[provider]["costs"] += cost
            provider_stats[provider]["profit"] += (revenue - cost)
            provider_stats[provider]["count"] += 1

        # Build table data
        data = [
            ["Provider", "Revenue", "Costs", "Profit", "Margin", "Txns"]
        ]

        for provider, stats in sorted(provider_stats.items(), key=lambda x: x[1]["profit"], reverse=True):
            margin = (stats["profit"] / stats["revenue"] * 100) if stats["revenue"] > 0 else 0

            data.append([
                provider.upper(),
                f"GHS {stats['revenue']:,.2f}",
                f"GHS {stats['costs']:,.2f}",
                f"GHS {stats['profit']:,.2f}",
                f"{margin:.2f}%",
                f"{stats['count']:,}"
            ])

        table = Table(data, colWidths=[1.2 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 1 * inch, 0.8 * inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        return table

    def _create_details_table(self, records: List[Dict]) -> Table:
        """Create detailed transactions table."""
        data = [
            ["Date", "Provider", "Service", "Revenue", "Cost", "Profit", "Margin"]
        ]

        for record in records:
            revenue = record.get("customer_charge", 0)
            cost = record.get("actual_cost", 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0

            timestamp = record.get("timestamp")
            date_str = timestamp.strftime("%Y-%m-%d") if timestamp else "N/A"

            data.append([
                date_str,
                record.get("provider", "").upper()[:8],
                record.get("service_type", "")[:10],
                f"₵{revenue:.2f}",
                f"₵{cost:.2f}",
                f"₵{profit:.2f}",
                f"{margin:.1f}%"
            ])

        table = Table(data, colWidths=[0.9 * inch, 0.8 * inch, 1 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.7 * inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

            # Body
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        return table

    def _get_margin_color(self, margin: float) -> colors.Color:
        """Get color based on margin percentage."""
        if margin < 0:
            return colors.HexColor('#fee2e2')  # Red
        elif margin < 10:
            return colors.HexColor('#fef3c7')  # Yellow
        elif margin < 25:
            return colors.HexColor('#d1fae5')  # Light green
        else:
            return colors.HexColor('#a7f3d0')  # Green

    def _get_margin_status(self, margin: float) -> str:
        """Get status text based on margin percentage."""
        if margin < 0:
            return "⚠️ LOSING MONEY"
        elif margin < 10:
            return "⚠️ Low"
        elif margin < 25:
            return "✓ Moderate"
        else:
            return "✓ Healthy"


# Singleton instance
_pdf_service_instance = None


def get_pdf_report_service(db: AsyncIOMotorDatabase) -> PDFReportService:
    """Get or create PDF report service instance."""
    global _pdf_service_instance
    if _pdf_service_instance is None:
        _pdf_service_instance = PDFReportService(db)
    return _pdf_service_instance
