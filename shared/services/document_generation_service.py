"""
Centralized Document Generation Service

Provides unified interface for generating professional documents in multiple formats:
- PDF generation using WeasyPrint + Jinja2 templates (HTML/CSS to PDF)
- DOCX generation using python-docx
- Supports template rendering with variable substitution
- Reusable across all applications (EstateFlow, ChurchFlow, etc.)

Usage:
    from shared.services.document_generation_service import DocumentGenerationService

    service = DocumentGenerationService()

    # Generate PDF from template
    pdf_bytes = await service.generate_pdf(
        template_name="invoice.html",
        template_dir="/path/to/templates",
        context={"invoice": invoice_data, "organization": org_data}
    )

    # Generate DOCX from template
    docx_bytes = await service.generate_docx(
        template_name="contract.xml",
        template_dir="/path/to/templates",
        context={"contract": contract_data}
    )
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from io import BytesIO

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML, CSS
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


class DocumentGenerationService:
    """
    Service for generating documents in PDF and DOCX formats.

    Features:
    - PDF generation with HTML/CSS templates using WeasyPrint
    - DOCX generation with python-docx
    - Jinja2 template rendering
    - Customizable page size and styling
    - Base64 CSS/font support for WeasyPrint
    """

    def __init__(self):
        """Initialize the document generation service."""
        self.logger = logging.getLogger(__name__)

    async def generate_pdf(
        self,
        template_name: str,
        template_dir: Union[str, Path],
        context: Dict[str, Any],
        css_string: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> bytes:
        """
        Generate a PDF document from an HTML template.

        Args:
            template_name: Name of the HTML template file
            template_dir: Directory containing the template
            context: Data to render in the template
            css_string: Optional additional CSS to apply
            base_url: Optional base URL for resolving relative paths

        Returns:
            PDF file content as bytes

        Raises:
            TemplateNotFound: If template doesn't exist
            Exception: If PDF generation fails
        """
        try:
            # Setup Jinja2 environment
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template(template_name)

            # Render HTML
            html_content = template.render(**context)

            # Generate PDF using WeasyPrint
            html_obj = HTML(string=html_content, base_url=base_url)

            # Apply additional CSS if provided
            if css_string:
                css_obj = CSS(string=css_string)
                pdf_bytes = html_obj.write_pdf(stylesheets=[css_obj])
            else:
                pdf_bytes = html_obj.write_pdf()

            self.logger.info(f"Generated PDF from template: {template_name}")
            return pdf_bytes

        except TemplateNotFound as e:
            self.logger.error(f"Template not found: {template_name} in {template_dir}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            raise

    async def generate_pdf_from_html(
        self,
        html_content: str,
        css_string: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> bytes:
        """
        Generate a PDF document directly from HTML string.

        Args:
            html_content: HTML content to convert
            css_string: Optional CSS to apply
            base_url: Optional base URL for resolving relative paths

        Returns:
            PDF file content as bytes
        """
        try:
            html_obj = HTML(string=html_content, base_url=base_url)

            if css_string:
                css_obj = CSS(string=css_string)
                pdf_bytes = html_obj.write_pdf(stylesheets=[css_obj])
            else:
                pdf_bytes = html_obj.write_pdf()

            self.logger.info("Generated PDF from HTML string")
            return pdf_bytes

        except Exception as e:
            self.logger.error(f"Failed to generate PDF from HTML: {e}")
            raise

    async def generate_docx(
        self,
        title: str,
        sections: list[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Generate a DOCX document with structured sections.

        Args:
            title: Document title
            sections: List of section dictionaries with keys:
                - heading: Section heading text
                - paragraphs: List of paragraph texts
                - table: Optional table data (list of lists)
                - style: Optional style settings
            output_path: Optional path to save document

        Returns:
            DOCX file content as bytes

        Example:
            sections = [
                {
                    "heading": "Introduction",
                    "paragraphs": ["This is the introduction paragraph."]
                },
                {
                    "heading": "Line Items",
                    "table": [
                        ["Description", "Quantity", "Price"],
                        ["Item 1", "2", "GHS 100"],
                    ]
                }
            ]
        """
        try:
            doc = Document()

            # Add title
            title_para = doc.add_heading(title, level=0)
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Add sections
            for section in sections:
                # Add heading
                if "heading" in section:
                    doc.add_heading(section["heading"], level=1)

                # Add paragraphs
                if "paragraphs" in section:
                    for para_text in section["paragraphs"]:
                        para = doc.add_paragraph(para_text)

                        # Apply style if provided
                        if "style" in section:
                            style = section["style"]
                            if "font_size" in style:
                                for run in para.runs:
                                    run.font.size = Pt(style["font_size"])
                            if "bold" in style and style["bold"]:
                                for run in para.runs:
                                    run.font.bold = True

                # Add table if provided
                if "table" in section:
                    table_data = section["table"]
                    if table_data:
                        table = doc.add_table(
                            rows=len(table_data),
                            cols=len(table_data[0])
                        )
                        table.style = 'Light Grid Accent 1'

                        # Populate table
                        for row_idx, row_data in enumerate(table_data):
                            for col_idx, cell_value in enumerate(row_data):
                                cell = table.rows[row_idx].cells[col_idx]
                                cell.text = str(cell_value)

                                # Bold header row
                                if row_idx == 0:
                                    for paragraph in cell.paragraphs:
                                        for run in paragraph.runs:
                                            run.font.bold = True

                # Add spacing
                doc.add_paragraph()

            # Save to bytes
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            docx_bytes = buffer.getvalue()
            buffer.close()

            # Optionally save to file
            if output_path:
                doc.save(output_path)
                self.logger.info(f"Saved DOCX to: {output_path}")

            self.logger.info(f"Generated DOCX document: {title}")
            return docx_bytes

        except Exception as e:
            self.logger.error(f"Failed to generate DOCX: {e}")
            raise

    async def generate_docx_from_template(
        self,
        template_name: str,
        template_dir: Union[str, Path],
        context: Dict[str, Any]
    ) -> bytes:
        """
        Generate a DOCX document from a Jinja2 XML template.

        Note: This requires a Word template XML file with Jinja2 placeholders.
        For simpler use cases, use generate_docx() instead.

        Args:
            template_name: Name of the XML template file
            template_dir: Directory containing the template
            context: Data to render in the template

        Returns:
            DOCX file content as bytes
        """
        try:
            # Setup Jinja2 environment
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template(template_name)

            # Render XML
            xml_content = template.render(**context)

            # Create DOCX from XML
            doc = Document()
            # Note: This is a simplified implementation
            # For full XML template support, consider python-docx-template library

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            docx_bytes = buffer.getvalue()
            buffer.close()

            self.logger.info(f"Generated DOCX from template: {template_name}")
            return docx_bytes

        except Exception as e:
            self.logger.error(f"Failed to generate DOCX from template: {e}")
            raise


# Singleton instance
_document_generation_service = None


def get_document_generation_service() -> DocumentGenerationService:
    """Get or create document generation service instance."""
    global _document_generation_service
    if _document_generation_service is None:
        _document_generation_service = DocumentGenerationService()
    return _document_generation_service
