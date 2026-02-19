"""
Document Generation Service (Stub) for EstateFlow.

Provides a local stub for PDF/document generation that was previously
handled by a shared centralized service.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentGenerationService:
    """
    Stub document generation service.

    Generates basic PDF content. Real implementation would use
    WeasyPrint, wkhtmltopdf, or a similar library.
    """

    async def generate_pdf(
        self,
        template_name: str,
        template_dir: Path,
        context: Dict[str, Any],
        **kwargs
    ) -> bytes:
        """
        Generate PDF from HTML template.

        Args:
            template_name: Name of the HTML template file
            template_dir: Directory containing templates
            context: Template context variables

        Returns:
            PDF content as bytes
        """
        try:
            from jinja2 import Environment, FileSystemLoader

            # Try to render the HTML template
            template_path = template_dir / template_name
            if template_path.exists():
                env = Environment(loader=FileSystemLoader(str(template_dir)))
                template = env.get_template(template_name)
                html_content = template.render(**context)

                # Try to convert HTML to PDF using weasyprint if available
                try:
                    from weasyprint import HTML
                    pdf_bytes = HTML(string=html_content).write_pdf()
                    return pdf_bytes
                except ImportError:
                    logger.warning(
                        "weasyprint not installed. Returning HTML as bytes. "
                        "Install with: pip install weasyprint"
                    )
                    return html_content.encode("utf-8")
            else:
                logger.warning(f"Template not found: {template_path}")
                # Return a minimal PDF stub
                return self._generate_stub_pdf(context)

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return self._generate_stub_pdf(context)

    def _generate_stub_pdf(self, context: Dict[str, Any]) -> bytes:
        """Generate a minimal stub PDF when template rendering fails."""
        invoice = context.get("invoice", {})
        invoice_number = invoice.get("invoice_number", "N/A")
        total = invoice.get("total_amount", 0)
        currency = invoice.get("currency", "USD")

        # Minimal valid PDF
        content = f"Invoice {invoice_number} - {currency} {total}"
        return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n% {content}\n%%EOF".encode()


def get_document_generation_service() -> DocumentGenerationService:
    """Factory function to get document generation service instance."""
    return DocumentGenerationService()
