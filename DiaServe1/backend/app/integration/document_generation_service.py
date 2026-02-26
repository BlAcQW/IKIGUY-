"""
Document Generation Service for EstateFlow.

Generates invoice PDFs using ReportLab's platypus layout engine.
"""

import io
import logging
from datetime import datetime
from html import escape as html_escape
from pathlib import Path  # used in generate_pdf signature for API compatibility
from typing import Any, Dict, Union

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

logger = logging.getLogger(__name__)

# Brand colours (from invoice.html template CSS)
BRAND_NAVY = HexColor("#1e3a5f")
GRAY_TEXT = HexColor("#666666")
LIGHT_GRAY_BG = HexColor("#f3f4f6")
BLUE_ACCENT = HexColor("#3b82f6")
BLUE_LIGHT_BG = HexColor("#eff6ff")
WHITE = white
ROW_BORDER = HexColor("#e5e7eb")

STATUS_COLORS = {
    "paid": HexColor("#22c55e"),
    "sent": HexColor("#f59e0b"),
    "pending": HexColor("#f59e0b"),
    "overdue": HexColor("#ef4444"),
    "draft": HexColor("#6b7280"),
    "cancelled": HexColor("#6b7280"),
}


class DocumentGenerationService:
    """
    Generates invoice PDFs using ReportLab.

    Reads invoice and organisation data from the context dict supplied by
    InvoiceService.generate_pdf() and builds a professional PDF that matches
    the visual design of templates/invoices/invoice.html.
    """

    def _format_date(self, value: Union[datetime, str, None]) -> str:
        """Format a datetime object or ISO string to a human-readable date."""
        if isinstance(value, datetime):
            return value.strftime("%B %d, %Y")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).strftime("%B %d, %Y")
            except (ValueError, TypeError):
                return value
        return str(value) if value else ""

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        """Create all paragraph styles used in the invoice PDF."""
        base = getSampleStyleSheet()

        return {
            "company_name": ParagraphStyle(
                "CompanyName",
                parent=base["Normal"],
                fontSize=20,
                leading=24,
                textColor=BRAND_NAVY,
                fontName="Helvetica-Bold",
            ),
            "company_detail": ParagraphStyle(
                "CompanyDetail",
                parent=base["Normal"],
                fontSize=8,
                leading=12,
                textColor=GRAY_TEXT,
            ),
            "invoice_title": ParagraphStyle(
                "InvoiceTitle",
                parent=base["Normal"],
                fontSize=24,
                leading=28,
                textColor=BRAND_NAVY,
                fontName="Helvetica-Bold",
                alignment=TA_RIGHT,
            ),
            "invoice_number": ParagraphStyle(
                "InvoiceNumber",
                parent=base["Normal"],
                fontSize=11,
                leading=14,
                textColor=GRAY_TEXT,
                alignment=TA_RIGHT,
            ),
            "section_title": ParagraphStyle(
                "SectionTitle",
                parent=base["Normal"],
                fontSize=10,
                leading=14,
                textColor=BRAND_NAVY,
                fontName="Helvetica-Bold",
                spaceAfter=6,
            ),
            "body": ParagraphStyle(
                "Body",
                parent=base["Normal"],
                fontSize=9,
                leading=13,
                textColor=HexColor("#333333"),
            ),
            "body_bold": ParagraphStyle(
                "BodyBold",
                parent=base["Normal"],
                fontSize=10,
                leading=14,
                textColor=HexColor("#333333"),
                fontName="Helvetica-Bold",
            ),
            "body_gray": ParagraphStyle(
                "BodyGray",
                parent=base["Normal"],
                fontSize=9,
                leading=13,
                textColor=GRAY_TEXT,
            ),
            "body_right": ParagraphStyle(
                "BodyRight",
                parent=base["Normal"],
                fontSize=9,
                leading=13,
                textColor=HexColor("#333333"),
                alignment=TA_RIGHT,
            ),
            "footer": ParagraphStyle(
                "Footer",
                parent=base["Normal"],
                fontSize=8,
                leading=12,
                textColor=GRAY_TEXT,
                alignment=TA_CENTER,
            ),
            "notes_title": ParagraphStyle(
                "NotesTitle",
                parent=base["Normal"],
                fontSize=10,
                leading=14,
                textColor=BRAND_NAVY,
                fontName="Helvetica-Bold",
                spaceAfter=4,
            ),
            "notes_content": ParagraphStyle(
                "NotesContent",
                parent=base["Normal"],
                fontSize=9,
                leading=13,
                textColor=GRAY_TEXT,
            ),
            "property_name": ParagraphStyle(
                "PropertyName",
                parent=base["Normal"],
                fontSize=10,
                leading=14,
                textColor=BRAND_NAVY,
                fontName="Helvetica-Bold",
            ),
            "property_id": ParagraphStyle(
                "PropertyId",
                parent=base["Normal"],
                fontSize=7,
                leading=10,
                textColor=GRAY_TEXT,
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_pdf(
        self,
        template_name: str,
        template_dir: Path,
        context: Dict[str, Any],
        **kwargs,
    ) -> bytes:
        """
        Generate an invoice PDF from context data.

        Args:
            template_name: Kept for API compatibility (unused).
            template_dir: Kept for API compatibility (unused).
            context: Must contain ``invoice`` (dict) and ``organization`` (dict).

        Returns:
            PDF content as bytes.
        """
        try:
            return self._build_invoice_pdf(context)
        except Exception as e:
            logger.error("PDF generation failed: %s", e, exc_info=True)
            return self._generate_stub_pdf(context)

    # ------------------------------------------------------------------
    # PDF builder
    # ------------------------------------------------------------------

    def _build_invoice_pdf(self, context: Dict[str, Any]) -> bytes:
        invoice = context.get("invoice", {})
        org = context.get("organization", {})
        styles = self._build_styles()
        currency = invoice.get("currency", "USD")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        story: list = []
        page_width = A4[0] - 3 * cm  # usable width

        # ── Header: org info (left) + INVOICE title (right) ──────────
        esc = html_escape  # shorthand for escaping user-controlled text
        org_lines = []
        if org.get("name"):
            org_lines.append(Paragraph(esc(org["name"]), styles["company_name"]))
        detail_parts = []
        if org.get("address"):
            detail_parts.append(esc(org["address"]))
        if org.get("phone"):
            detail_parts.append(f"Phone: {esc(org['phone'])}")
        if org.get("email"):
            detail_parts.append(f"Email: {esc(org['email'])}")
        if org.get("website"):
            detail_parts.append(esc(org["website"]))
        if detail_parts:
            org_lines.append(
                Paragraph("<br/>".join(detail_parts), styles["company_detail"])
            )
        left_cell = org_lines if org_lines else [Paragraph("", styles["body"])]

        status_raw = str(invoice.get("status", "draft")).lower()
        status_color = STATUS_COLORS.get(status_raw, STATUS_COLORS["draft"])

        right_lines = [
            Paragraph("INVOICE", styles["invoice_title"]),
            Paragraph(
                esc(str(invoice.get("invoice_number", ""))), styles["invoice_number"]
            ),
            Spacer(1, 6),
            Paragraph(
                f'<font color="{status_color.hexval()}">'
                f"<b>{status_raw.upper()}</b></font>",
                ParagraphStyle(
                    "StatusBadge",
                    parent=styles["body"],
                    alignment=TA_RIGHT,
                    fontSize=9,
                ),
            ),
        ]

        header_table = Table(
            [[left_cell, right_lines]],
            colWidths=[page_width * 0.55, page_width * 0.45],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 8))

        # ── Navy divider ─────────────────────────────────────────────
        story.append(
            HRFlowable(
                width="100%", thickness=3, color=BRAND_NAVY, spaceAfter=16
            )
        )

        # ── Bill-to (left) + dates (right) ───────────────────────────
        bill_lines = [Paragraph("BILL TO", styles["section_title"])]
        if invoice.get("contact_name"):
            bill_lines.append(
                Paragraph(esc(invoice["contact_name"]), styles["body_bold"])
            )
        for field in ("contact_email", "contact_phone", "contact_address"):
            val = invoice.get(field)
            if val:
                bill_lines.append(Paragraph(esc(str(val)), styles["body_gray"]))

        meta_lines = []
        if invoice.get("invoice_date"):
            meta_lines.append(
                Paragraph(
                    f"<b>Invoice Date:</b>  {self._format_date(invoice['invoice_date'])}",
                    styles["body"],
                )
            )
        if invoice.get("due_date"):
            meta_lines.append(
                Paragraph(
                    f"<b>Due Date:</b>  {self._format_date(invoice['due_date'])}",
                    styles["body"],
                )
            )
        meta_lines.append(
            Paragraph(f"<b>Currency:</b>  {currency}", styles["body"])
        )
        if (
            status_raw == "paid"
            and invoice.get("paid_date")
        ):
            meta_lines.append(
                Paragraph(
                    f"<b>Paid Date:</b>  {self._format_date(invoice['paid_date'])}",
                    styles["body"],
                )
            )

        details_table = Table(
            [[bill_lines, meta_lines]],
            colWidths=[page_width * 0.55, page_width * 0.45],
        )
        details_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(details_table)
        story.append(Spacer(1, 16))

        # ── Property info box (conditional) ──────────────────────────
        if invoice.get("property_name"):
            prop_data = [
                [
                    Paragraph(
                        f"Property: {esc(invoice['property_name'])}",
                        styles["property_name"],
                    )
                ],
            ]
            if invoice.get("property_id"):
                prop_data.append(
                    [
                        Paragraph(
                            f"Property ID: {esc(invoice['property_id'])}",
                            styles["property_id"],
                        )
                    ]
                )
            prop_table = Table(prop_data, colWidths=[page_width])
            prop_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT_BG),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (0, 0), 8),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                        (
                            "LINEBELOW",
                            (0, 0),
                            (0, -1),
                            0,
                            BLUE_LIGHT_BG,
                        ),
                    ]
                )
            )
            story.append(prop_table)
            story.append(Spacer(1, 16))

        # ── Line items table ─────────────────────────────────────────
        col_widths = [
            page_width * 0.42,
            page_width * 0.10,
            page_width * 0.18,
            page_width * 0.12,
            page_width * 0.18,
        ]

        header_style = ParagraphStyle(
            "THdr",
            fontSize=8,
            leading=10,
            textColor=WHITE,
            fontName="Helvetica-Bold",
        )
        header_style_r = ParagraphStyle(
            "THdrR",
            parent=header_style,
            alignment=TA_RIGHT,
        )
        header_style_c = ParagraphStyle(
            "THdrC",
            parent=header_style,
            alignment=TA_CENTER,
        )

        cell_style = ParagraphStyle(
            "TCell", fontSize=8, leading=11, textColor=HexColor("#333333")
        )
        cell_style_r = ParagraphStyle(
            "TCellR", parent=cell_style, alignment=TA_RIGHT
        )
        cell_style_c = ParagraphStyle(
            "TCellC", parent=cell_style, alignment=TA_CENTER
        )

        table_data = [
            [
                Paragraph("Description", header_style),
                Paragraph("Qty", header_style_c),
                Paragraph("Unit Price", header_style_r),
                Paragraph("Tax", header_style_r),
                Paragraph("Amount", header_style_r),
            ]
        ]

        for item in invoice.get("line_items", []):
            qty = float(item.get("quantity") or 0)
            unit_price = float(item.get("unit_price") or 0)
            tax_rate = float(item.get("tax_rate") or 0)
            amount = float(item.get("amount") or qty * unit_price)
            table_data.append(
                [
                    Paragraph(esc(str(item.get("description", ""))), cell_style),
                    Paragraph(f"{qty:.2f}", cell_style_c),
                    Paragraph(f"{currency} {unit_price:,.2f}", cell_style_r),
                    Paragraph(f"{tax_rate:.1f}%", cell_style_r),
                    Paragraph(f"{currency} {amount:,.2f}", cell_style_r),
                ]
            )

        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        items_style = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # All cells
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Row borders for data rows
        for i in range(1, len(table_data)):
            items_style.append(
                ("LINEBELOW", (0, i), (-1, i), 0.5, ROW_BORDER)
            )

        items_table.setStyle(TableStyle(items_style))
        story.append(items_table)
        story.append(Spacer(1, 12))

        # ── Totals (right-aligned) ───────────────────────────────────
        subtotal = float(invoice.get("subtotal") or 0)
        tax_amount = float(invoice.get("tax_amount") or 0)
        total_amount = float(invoice.get("total_amount") or 0)

        totals_label = ParagraphStyle(
            "TotLabel", fontSize=9, leading=13, fontName="Helvetica-Bold"
        )
        totals_value = ParagraphStyle(
            "TotValue", fontSize=9, leading=13, alignment=TA_RIGHT
        )
        totals_grand_label = ParagraphStyle(
            "GrandLabel",
            fontSize=11,
            leading=15,
            fontName="Helvetica-Bold",
            textColor=WHITE,
        )
        totals_grand_value = ParagraphStyle(
            "GrandValue",
            fontSize=11,
            leading=15,
            fontName="Helvetica-Bold",
            textColor=WHITE,
            alignment=TA_RIGHT,
        )

        totals_data = [
            [
                Paragraph("Subtotal:", totals_label),
                Paragraph(f"{currency} {subtotal:,.2f}", totals_value),
            ],
            [
                Paragraph("Tax:", totals_label),
                Paragraph(f"{currency} {tax_amount:,.2f}", totals_value),
            ],
            [
                Paragraph("TOTAL:", totals_grand_label),
                Paragraph(
                    f"{currency} {total_amount:,.2f}", totals_grand_value
                ),
            ],
        ]

        totals_w = page_width * 0.40
        totals_table = Table(
            totals_data, colWidths=[totals_w * 0.45, totals_w * 0.55]
        )
        totals_style = [
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            # Subtotal / tax row borders
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, ROW_BORDER),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, ROW_BORDER),
            # Grand-total row
            ("BACKGROUND", (0, 2), (-1, 2), BRAND_NAVY),
            ("TEXTCOLOR", (0, 2), (-1, 2), WHITE),
        ]
        totals_table.setStyle(TableStyle(totals_style))

        # Right-align the totals block
        wrapper = Table(
            [[None, totals_table]],
            colWidths=[page_width - totals_w, totals_w],
        )
        wrapper.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(wrapper)
        story.append(Spacer(1, 24))

        # ── Notes / Terms ────────────────────────────────────────────
        if invoice.get("notes"):
            story.append(
                HRFlowable(
                    width="100%", thickness=0.5, color=ROW_BORDER, spaceAfter=8
                )
            )
            story.append(Paragraph("Notes", styles["notes_title"]))
            story.append(
                Paragraph(esc(str(invoice["notes"])), styles["notes_content"])
            )
            story.append(Spacer(1, 12))

        if invoice.get("terms"):
            if not invoice.get("notes"):
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=ROW_BORDER,
                        spaceAfter=8,
                    )
                )
            story.append(
                Paragraph("Terms & Conditions", styles["notes_title"])
            )
            story.append(
                Paragraph(esc(str(invoice["terms"])), styles["notes_content"])
            )
            story.append(Spacer(1, 12))

        # ── Payment info (only if unpaid + org has payment_info) ─────
        if status_raw != "paid" and org.get("payment_info"):
            pay_data = [
                [
                    Paragraph(
                        "<b>Payment Information</b>", styles["body"]
                    )
                ],
                [
                    Paragraph(
                        "<br/>".join(
                            esc(line)
                            for line in str(org["payment_info"]).split("\n")
                        ),
                        styles["body_gray"],
                    )
                ],
            ]
            pay_table = Table(pay_data, colWidths=[page_width])
            pay_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY_BG),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (0, 0), 10),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                    ]
                )
            )
            story.append(pay_table)
            story.append(Spacer(1, 16))

        # ── Footer ───────────────────────────────────────────────────
        story.append(
            HRFlowable(
                width="100%", thickness=2, color=BRAND_NAVY, spaceAfter=10
            )
        )
        story.append(
            Paragraph("Thank you for your business!", styles["footer"])
        )
        if org.get("tax_id"):
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(f"Tax ID: {esc(org['tax_id'])}", styles["footer"])
            )

        doc.build(story)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _generate_stub_pdf(self, context: Dict[str, Any]) -> bytes:
        """Generate a minimal valid PDF via ReportLab when full generation fails."""
        invoice = context.get("invoice", {})
        invoice_number = html_escape(str(invoice.get("invoice_number") or "N/A"))
        total = float(invoice.get("total_amount") or 0)
        currency = html_escape(str(invoice.get("currency") or "USD"))

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"Invoice {invoice_number}", styles["Title"]),
            Spacer(1, 20),
            Paragraph(
                f"Amount: {currency} {total:,.2f}", styles["Normal"]
            ),
        ]
        doc.build(story)
        return buf.getvalue()


def get_document_generation_service() -> DocumentGenerationService:
    """Factory function to get document generation service instance."""
    return DocumentGenerationService()
