"""
Document Export Service for Knowledge Base.
Handles exporting documents in various formats: JSON, CSV, PDF, and original file format.
"""

import os
import io
import csv
import json
import logging
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    ORIGINAL = "original"


class DocumentExportService:
    """Service for exporting knowledge base documents in various formats."""

    def __init__(self):
        """Initialize the document export service."""
        pass

    @staticmethod
    def _to_iso_string(dt_value) -> Optional[str]:
        """
        Convert datetime value to ISO format string.
        Handles both datetime objects and ISO string formats.

        Args:
            dt_value: datetime object or ISO string

        Returns:
            ISO format string or None
        """
        if dt_value is None:
            return None
        if isinstance(dt_value, str):
            return dt_value  # Already a string
        if isinstance(dt_value, datetime):
            return dt_value.isoformat()
        return str(dt_value)

    @staticmethod
    def _to_formatted_string(dt_value, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Convert datetime value to formatted string.
        Handles both datetime objects and ISO string formats.

        Args:
            dt_value: datetime object or ISO string
            fmt: strftime format string

        Returns:
            Formatted datetime string or empty string
        """
        if dt_value is None:
            return ""
        if isinstance(dt_value, datetime):
            return dt_value.strftime(fmt)
        if isinstance(dt_value, str):
            try:
                # Parse ISO string and format it
                dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                return dt.strftime(fmt)
            except:
                return dt_value  # Return as-is if parsing fails
        return str(dt_value)

    async def export_documents_json(
        self,
        documents: List[Dict[str, Any]],
        include_metadata: bool = True,
        include_versions: bool = False
    ) -> str:
        """
        Export documents to JSON format.

        Args:
            documents: List of document dictionaries
            include_metadata: Whether to include full metadata
            include_versions: Whether to include version history

        Returns:
            JSON string with exported documents
        """
        try:
            export_data = []

            for doc in documents:
                doc_data = {
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "category": doc.get("category"),
                    "tags": doc.get("tags", []),
                    "source": doc.get("source"),
                    "status": doc.get("status"),
                    "created_at": self._to_iso_string(doc.get("created_at")),
                    "updated_at": self._to_iso_string(doc.get("updated_at")),
                }

                if include_metadata:
                    metadata = doc.get("metadata", {})
                    doc_data["metadata"] = {
                        "word_count": metadata.get("word_count", 0),
                        "character_count": metadata.get("character_count", 0),
                        "chunk_count": metadata.get("chunk_count", 0),
                        "query_count": metadata.get("query_count", 0),
                        "reference_count": metadata.get("reference_count", 0),
                        "filename": metadata.get("filename"),
                    }

                if include_versions and doc.get("versions"):
                    doc_data["versions"] = [
                        {
                            "version_number": v.get("version_number"),
                            "title": v.get("title"),
                            "changed_by": v.get("changed_by"),
                            "change_reason": v.get("change_reason"),
                            "created_at": self._to_iso_string(v.get("created_at")),
                        }
                        for v in doc.get("versions", [])
                    ]

                export_data.append(doc_data)

            return json.dumps(export_data, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    async def export_documents_csv(
        self,
        documents: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """
        Export documents to CSV format.

        Args:
            documents: List of document dictionaries
            include_metadata: Whether to include metadata columns

        Returns:
            CSV string with exported documents
        """
        try:
            output = io.StringIO()

            # Define CSV headers
            headers = [
                "ID",
                "Title",
                "Content Preview",
                "Category",
                "Tags",
                "Source",
                "Status",
                "Created At",
                "Updated At",
            ]

            if include_metadata:
                headers.extend([
                    "Word Count",
                    "Character Count",
                    "Chunk Count",
                    "Query Count",
                    "Reference Count",
                ])

            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()

            for doc in documents:
                # Truncate content for preview (200 chars)
                content = doc.get("content", "")
                content_preview = content[:200] + "..." if len(content) > 200 else content

                # Join tags with semicolons
                tags = "; ".join(doc.get("tags", []))

                row_data = {
                    "ID": doc.get("id", ""),
                    "Title": doc.get("title", ""),
                    "Content Preview": content_preview,
                    "Category": doc.get("category", ""),
                    "Tags": tags,
                    "Source": doc.get("source", ""),
                    "Status": doc.get("status", ""),
                    "Created At": self._to_formatted_string(doc.get("created_at")),
                    "Updated At": self._to_formatted_string(doc.get("updated_at")),
                }

                if include_metadata:
                    metadata = doc.get("metadata", {})
                    row_data.update({
                        "Word Count": metadata.get("word_count", 0),
                        "Character Count": metadata.get("character_count", 0),
                        "Chunk Count": metadata.get("chunk_count", 0),
                        "Query Count": metadata.get("query_count", 0),
                        "Reference Count": metadata.get("reference_count", 0),
                    })

                writer.writerow(row_data)

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    async def export_document_pdf(
        self,
        document: Dict[str, Any],
        include_metadata: bool = True
    ) -> bytes:
        """
        Export a single document to PDF format.

        Args:
            document: Document dictionary
            include_metadata: Whether to include metadata in header

        Returns:
            PDF file bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT, TA_CENTER

            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

            # Container for PDF elements
            elements = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1d2e'),
                spaceAfter=12,
                alignment=TA_CENTER,
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#4a5568'),
                spaceAfter=8,
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                textColor=colors.HexColor('#2d3748'),
                alignment=TA_LEFT,
                spaceAfter=10,
            )

            # Title
            title = Paragraph(document.get("title", "Untitled Document"), title_style)
            elements.append(title)
            elements.append(Spacer(1, 0.2*inch))

            # Metadata table
            if include_metadata:
                metadata_data = [
                    ["Category:", document.get("category", "N/A")],
                    ["Source:", document.get("source", "N/A")],
                    ["Status:", document.get("status", "N/A")],
                    ["Tags:", ", ".join(document.get("tags", []))],
                    ["Created:", self._to_formatted_string(document.get("created_at")) or "N/A"],
                ]

                doc_metadata = document.get("metadata", {})
                if doc_metadata.get("word_count"):
                    metadata_data.append(["Word Count:", str(doc_metadata.get("word_count", 0))])

                metadata_table = Table(metadata_data, colWidths=[1.5*inch, 5*inch])
                metadata_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3748')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))

                elements.append(metadata_table)
                elements.append(Spacer(1, 0.3*inch))

            # Content heading
            content_heading = Paragraph("Content", heading_style)
            elements.append(content_heading)
            elements.append(Spacer(1, 0.1*inch))

            # Content (handle long text by splitting into paragraphs)
            content = document.get("content", "")

            # Split content by newlines and create paragraphs
            paragraphs = content.split('\n')
            for para_text in paragraphs:
                if para_text.strip():
                    # Escape special characters for XML
                    para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    para = Paragraph(para_text, body_style)
                    elements.append(para)

            # Build PDF
            doc.build(elements)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except ImportError:
            logger.error("ReportLab not installed. Install with: pip install reportlab")
            raise Exception("PDF export requires reportlab library")
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise

    async def get_original_file(
        self,
        document: Dict[str, Any]
    ) -> Optional[tuple[bytes, str, str]]:
        """
        Retrieve the original uploaded file if available.

        Args:
            document: Document dictionary

        Returns:
            Tuple of (file_bytes, filename, mime_type) or None if not available
        """
        try:
            metadata = document.get("metadata", {})
            original_path = metadata.get("original_file_path")
            filename = metadata.get("filename")
            mime_type = metadata.get("file_type", "application/octet-stream")

            if not original_path or not os.path.exists(original_path):
                # File not available, return content as text file instead
                logger.warning(f"Original file not found, returning content as text")
                content = document.get("content", "")
                file_bytes = content.encode('utf-8')
                filename = f"{document.get('title', 'document')}.txt"
                mime_type = "text/plain"
                return (file_bytes, filename, mime_type)

            # Read original file
            with open(original_path, 'rb') as f:
                file_bytes = f.read()

            return (file_bytes, filename, mime_type)

        except Exception as e:
            logger.error(f"Error retrieving original file: {str(e)}")
            raise

    async def export_bulk_documents(
        self,
        documents: List[Dict[str, Any]],
        export_format: ExportFormat,
        include_metadata: bool = True,
        include_versions: bool = False
    ) -> tuple[bytes, str, str]:
        """
        Export multiple documents in the specified format.

        Args:
            documents: List of document dictionaries
            export_format: Export format (JSON, CSV, PDF not supported for bulk)
            include_metadata: Whether to include metadata
            include_versions: Whether to include version history (JSON only)

        Returns:
            Tuple of (file_bytes, filename, mime_type)

        Raises:
            ValueError: If PDF format is requested for bulk export
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            if export_format == ExportFormat.JSON:
                json_str = await self.export_documents_json(
                    documents,
                    include_metadata=include_metadata,
                    include_versions=include_versions
                )
                file_bytes = json_str.encode('utf-8')
                filename = f"documents_export_{timestamp}.json"
                mime_type = "application/json"

            elif export_format == ExportFormat.CSV:
                csv_str = await self.export_documents_csv(
                    documents,
                    include_metadata=include_metadata
                )
                file_bytes = csv_str.encode('utf-8')
                filename = f"documents_export_{timestamp}.csv"
                mime_type = "text/csv"

            elif export_format == ExportFormat.PDF:
                raise ValueError("PDF export is only supported for single documents. Use JSON or CSV for bulk export.")

            elif export_format == ExportFormat.ORIGINAL:
                raise ValueError("Original format export is only supported for single documents.")

            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            return (file_bytes, filename, mime_type)

        except Exception as e:
            logger.error(f"Error in bulk export: {str(e)}")
            raise


# Singleton instance
document_export_service = DocumentExportService()
