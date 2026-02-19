"""
PDF Receipt Generation Service for Wallet Transactions.

Generates professional PDF receipts for:
- Deposits
- Withdrawals
- Usage charges
"""

import logging
import io
import os
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class PDFReceiptService:
    """Service for generating PDF receipts for wallet transactions."""

    def __init__(self):
        """Initialize PDF receipt service."""
        self.company_name = "KasaAI Flow"
        self.company_address = "AI Labs Africa\nAccra, Ghana"
        self.company_email = "support@ailabsafrica.com"
        self.company_website = os.getenv("FRONTEND_URL", "https://kasaai.ailabsafrica.com")
        logger.info("PDF receipt service initialized")

    async def generate_transaction_receipt(
        self,
        transaction_data: Dict[str, Any]
    ) -> bytes:
        """
        Generate PDF receipt for a transaction.

        Args:
            transaction_data: Transaction details including:
                - id: Transaction ID
                - transaction_type: Type (deposit, withdrawal, etc.)
                - status: Transaction status
                - amount: Transaction amount
                - currency: Currency code
                - processing_fee: Fee charged
                - total_amount: Total amount
                - description: Transaction description
                - payment_method_display: Payment method used
                - created_at: Creation timestamp
                - completed_at: Completion timestamp
                - user_email: User email address
                - balance_before: Balance before transaction
                - balance_after: Balance after transaction

        Returns:
            PDF file as bytes
        """
        try:
            # Import ReportLab components
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.platypus import PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

            # Build content
            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=12,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=6
            )

            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666')
            )

            # Header
            story.append(Paragraph(self.company_name, title_style))
            story.append(Paragraph("Payment Receipt", heading_style))
            story.append(Spacer(1, 0.2*inch))

            # Receipt metadata
            receipt_number = f"RCP-{transaction_data.get('id', '')[:8].upper()}"
            issue_date = datetime.now().strftime("%B %d, %Y")

            meta_data = [
                ["Receipt Number:", receipt_number],
                ["Issue Date:", issue_date],
                ["Transaction ID:", transaction_data.get('id', 'N/A')[:16] + "..."],
            ]

            meta_table = Table(meta_data, colWidths=[2*inch, 3.5*inch])
            meta_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#666666')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 0.3*inch))

            # Billing information
            story.append(Paragraph("Billing Information", heading_style))
            story.append(Spacer(1, 0.1*inch))

            billing_data = [
                ["Email:", transaction_data.get('user_email', 'N/A')],
                ["Payment Method:", transaction_data.get('payment_method_display', 'N/A')],
                ["Transaction Date:", self._format_datetime(transaction_data.get('completed_at'))],
            ]

            billing_table = Table(billing_data, colWidths=[2*inch, 3.5*inch])
            billing_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#666666')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(billing_table)
            story.append(Spacer(1, 0.3*inch))

            # Transaction details
            story.append(Paragraph("Transaction Details", heading_style))
            story.append(Spacer(1, 0.1*inch))

            currency = transaction_data.get('currency', 'USD')
            amount = float(transaction_data.get('amount', 0))
            processing_fee = float(transaction_data.get('processing_fee', 0))
            total_amount = float(transaction_data.get('total_amount', 0))

            # Transaction table
            tx_data = [
                ["Description", "Amount"],
                [
                    transaction_data.get('description', 'Wallet Top-Up'),
                    self._format_currency(amount, currency)
                ],
                ["Processing Fee", self._format_currency(processing_fee, currency)],
                ["", ""],  # Spacer row
                ["Total", self._format_currency(total_amount, currency)],
            ]

            tx_table = Table(tx_data, colWidths=[4*inch, 2*inch])
            tx_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),

                # Data rows
                ('ALIGN', (0, 1), (0, -2), 'LEFT'),
                ('ALIGN', (1, 1), (1, -2), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#333333')),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#667eea')),
                ('ALIGN', (0, -1), (0, -1), 'LEFT'),
                ('ALIGN', (1, -1), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, -1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10),

                # Grid
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#dddddd')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#667eea')),
            ]))
            story.append(tx_table)
            story.append(Spacer(1, 0.3*inch))

            # Balance information
            if transaction_data.get('balance_after') is not None:
                story.append(Paragraph("Account Balance", heading_style))
                story.append(Spacer(1, 0.1*inch))

                balance_before = float(transaction_data.get('balance_before', 0))
                balance_after = float(transaction_data.get('balance_after', 0))

                balance_data = [
                    ["Balance Before:", self._format_currency(balance_before, currency)],
                    ["Balance After:", self._format_currency(balance_after, currency)],
                ]

                balance_table = Table(balance_data, colWidths=[2*inch, 2*inch])
                balance_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#10b981')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(balance_table)
                story.append(Spacer(1, 0.3*inch))

            # Status badge
            status = transaction_data.get('status', 'unknown').upper()
            status_color = colors.HexColor('#10b981') if status == 'COMPLETED' else colors.HexColor('#f59e0b')
            status_text = f'<b><font color="white" size="11">STATUS: {status}</font></b>'
            status_para = Paragraph(status_text, normal_style)

            status_table = Table([[status_para]], colWidths=[2*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), status_color),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ]))
            story.append(status_table)
            story.append(Spacer(1, 0.5*inch))

            # Footer
            footer_text = f"""
            <para align="center">
            <b>{self.company_name}</b><br/>
            {self.company_address.replace(chr(10), '<br/>')}<br/>
            Email: {self.company_email} | Website: {self.company_website}<br/>
            <br/>
            <i>Thank you for using KasaAI Flow!</i><br/>
            <i>This is an automatically generated receipt.</i>
            </para>
            """
            story.append(Paragraph(footer_text, normal_style))

            # Build PDF
            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated PDF receipt for transaction {transaction_data.get('id')}")
            return pdf_bytes

        except ImportError as e:
            logger.error(f"ReportLab not installed: {e}")
            raise Exception("PDF generation library not available. Install reportlab package.")
        except Exception as e:
            logger.error(f"Failed to generate PDF receipt: {e}")
            raise

    def _format_currency(self, amount: float, currency: str) -> str:
        """Format currency amount."""
        return f"{currency} {amount:,.2f}"

    def _format_datetime(self, dt_string: Optional[str]) -> str:
        """Format datetime string."""
        if not dt_string:
            return "N/A"
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p UTC")
        except:
            return dt_string


# Global instance
pdf_receipt_service = PDFReceiptService()
