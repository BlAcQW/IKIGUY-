"""
PDF Generation Service for Invoices.

Generates professional, branded PDF invoices from HTML templates.
"""

import logging
from datetime import datetime, date
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from app.models.finance import Invoice
from apps.shared.models.organization import Organization

logger = logging.getLogger(__name__)


class InvoicePDFService:
    """Service for generating invoice PDFs."""

    def __init__(self):
        """Initialize PDF service with Jinja2 template environment."""
        # Set up template directory
        template_dir = Path(__file__).parent.parent / "templates"
        template_dir.mkdir(exist_ok=True)

        # Configure Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add custom filters
        self.env.filters["currency"] = self._format_currency
        self.env.filters["date"] = self._format_date

        # Font configuration for WeasyPrint
        self.font_config = FontConfiguration()

    def _format_currency(self, amount: float, symbol: str = "$", position: str = "before") -> str:
        """
        Format currency value.

        Args:
            amount: Amount to format
            symbol: Currency symbol
            position: Symbol position (before/after)

        Returns:
            Formatted currency string
        """
        formatted = f"{amount:,.2f}"
        if position == "before":
            return f"{symbol}{formatted}"
        else:
            return f"{formatted}{symbol}"

    def _format_date(self, dt: datetime | date | str, date_format: str = "%Y-%m-%d") -> str:
        """
        Format date value.

        Args:
            dt: Date to format
            date_format: Date format string

        Returns:
            Formatted date string
        """
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return dt

        if isinstance(dt, datetime):
            return dt.strftime(date_format)
        elif isinstance(dt, date):
            return dt.strftime(date_format)

        return str(dt)

    def _format_address(self, address_dict: Optional[dict]) -> str:
        """
        Format structured address into string.

        Args:
            address_dict: Address dictionary

        Returns:
            Formatted address string
        """
        if not address_dict:
            return ""

        parts = []
        if address_dict.get("street"):
            parts.append(address_dict["street"])
        if address_dict.get("street2"):
            parts.append(address_dict["street2"])

        city_state_zip = []
        if address_dict.get("city"):
            city_state_zip.append(address_dict["city"])
        if address_dict.get("state"):
            city_state_zip.append(address_dict["state"])
        if address_dict.get("postal_code"):
            city_state_zip.append(address_dict["postal_code"])

        if city_state_zip:
            parts.append(", ".join(city_state_zip))

        if address_dict.get("country"):
            parts.append(address_dict["country"])

        return "<br>".join(parts)

    def generate_invoice_pdf(
        self,
        invoice: Invoice,
        organization: Organization,
        customer: dict,
    ) -> bytes:
        """
        Generate PDF from invoice data.

        Args:
            invoice: Invoice model
            organization: Organization model with branding
            customer: Customer dictionary

        Returns:
            PDF bytes

        Raises:
            Exception: If template rendering or PDF generation fails
        """
        try:
            # Load template
            template = self.env.get_template("invoice.html")

            # Prepare customer address
            customer_address_str = ""
            if customer.get("street_address") or customer.get("city"):
                address_parts = []
                if customer.get("street_address"):
                    address_parts.append(customer["street_address"])
                city_line = []
                if customer.get("city"):
                    city_line.append(customer["city"])
                if customer.get("state"):
                    city_line.append(customer["state"])
                if customer.get("postal_code"):
                    city_line.append(customer["postal_code"])
                if city_line:
                    address_parts.append(", ".join(city_line))
                if customer.get("country"):
                    address_parts.append(customer["country"])
                customer_address_str = "<br>".join(address_parts)

            # Prepare organization address
            org_address_str = ""
            if organization.billing_address:
                org_address_str = self._format_address(
                    organization.billing_address.model_dump() if hasattr(organization.billing_address, "model_dump") else organization.billing_address
                )
            elif organization.address:
                org_address_str = organization.address.replace("\n", "<br>")

            # Calculate line items if needed
            line_items = invoice.line_items if invoice.line_items else []

            # Render HTML
            html_content = template.render(
                invoice=invoice,
                organization=organization,
                customer=customer,
                customer_address=customer_address_str,
                org_address=org_address_str,
                line_items=line_items,
                today=datetime.now(),
            )

            # Custom CSS for styling
            css_styles = CSS(
                string=f"""
                @page {{
                    size: A4;
                    margin: 1cm;
                }}

                body {{
                    font-family: 'Helvetica', 'Arial', sans-serif;
                    font-size: 10pt;
                    line-height: 1.5;
                    color: #333;
                }}

                .header {{
                    color: {organization.primary_color or '#0066CC'};
                }}

                .accent {{
                    color: {organization.accent_color or '#00CC66'};
                }}
                """,
                font_config=self.font_config,
            )

            # Generate PDF
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf(
                stylesheets=[css_styles], font_config=self.font_config
            )

            logger.info(
                f"Generated PDF for invoice {invoice.invoice_number} "
                f"(organization: {organization.id})"
            )

            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to generate PDF for invoice {invoice.id}: {str(e)}")
            raise


# Singleton instance
_pdf_service = None


def get_pdf_service() -> InvoicePDFService:
    """Get or create PDF service singleton."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = InvoicePDFService()
    return _pdf_service
