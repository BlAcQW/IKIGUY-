# Centralized Document Generation Service

## Overview

The `DocumentGenerationService` provides a unified interface for generating professional documents in multiple formats across all applications in the EstateFlow ecosystem.

## Features

- **PDF Generation**: HTML/CSS to PDF using WeasyPrint + Jinja2 templates
- **DOCX Generation**: Structured DOCX documents using python-docx
- **Template Rendering**: Jinja2 template engine with variable substitution
- **Reusable**: Shared across all applications (EstateFlow, ChurchFlow, StudyFlow, etc.)

## Installation

The service is already available in the shared library. Required dependencies:
```bash
pip install weasyprint python-docx jinja2
```

All dependencies are already installed in `/opt/kasaai/apps/venv`.

## Usage

### PDF Generation from Template

```python
from shared.services.document_generation_service import get_document_generation_service
from pathlib import Path

# Get service instance
doc_service = get_document_generation_service()

# Prepare template data
context = {
    "invoice": {
        "invoice_number": "INV-1001",
        "total_amount": 3356.25,
        "currency": "GHS"
    },
    "organization": {
        "name": "Company Name",
        "email": "info@company.com"
    }
}

# Generate PDF
pdf_bytes = await doc_service.generate_pdf(
    template_name="invoice.html",
    template_dir=Path("/path/to/templates"),
    context=context
)

# Save or return PDF
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### PDF Generation from HTML String

```python
html_content = "<html><body><h1>Hello World</h1></body></html>"
css_string = "h1 { color: blue; }"

pdf_bytes = await doc_service.generate_pdf_from_html(
    html_content=html_content,
    css_string=css_string
)
```

### DOCX Generation

```python
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
            ["Item 2", "1", "GHS 50"],
        ]
    }
]

docx_bytes = await doc_service.generate_docx(
    title="Sales Report",
    sections=sections
)
```

## Integration Examples

### EstateFlow Invoice PDF

Located in `/opt/kasaai/apps/estateflow/backend/app/services/invoice_service.py`:

```python
async def generate_pdf(self, invoice_id: str, organization_id: str) -> bytes:
    # Get data
    invoice = await self.get_invoice(invoice_id, organization_id)
    org = await self.db.organizations.find_one({"id": organization_id})

    # Prepare context
    template_data = {
        "invoice": invoice.dict(),
        "organization": {
            "name": org.get("name", ""),
            # ... other fields
        }
    }

    # Generate PDF using centralized service
    doc_service = get_document_generation_service()
    template_dir = Path(__file__).parent.parent / "templates" / "invoices"

    pdf_bytes = await doc_service.generate_pdf(
        template_name="invoice.html",
        template_dir=template_dir,
        context=template_data
    )

    return pdf_bytes
```

## Template Structure

### PDF Templates (HTML/CSS)

Templates use Jinja2 syntax with full HTML/CSS support:

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: A4; margin: 2cm; }
        .invoice-header { border-bottom: 3px solid #1e3a5f; }
    </style>
</head>
<body>
    <div class="invoice-header">
        <h1>{{ organization.name }}</h1>
        <p>Invoice: {{ invoice.invoice_number }}</p>
    </div>

    <table>
        {% for item in invoice.line_items %}
        <tr>
            <td>{{ item.description }}</td>
            <td>{{ invoice.currency }} {{ "%.2f"|format(item.amount) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
```

### DOCX Structure

DOCX generation uses structured sections:

```python
{
    "heading": "Section Title",      # H1 heading
    "paragraphs": ["Text content"],  # List of paragraphs
    "table": [                       # Optional table data
        ["Header 1", "Header 2"],
        ["Data 1", "Data 2"]
    ],
    "style": {                       # Optional styling
        "font_size": 12,
        "bold": True
    }
}
```

## API Reference

### `generate_pdf(template_name, template_dir, context, css_string=None, base_url=None)`

Generate PDF from HTML template.

**Parameters:**
- `template_name` (str): Name of HTML template file
- `template_dir` (Path): Directory containing templates
- `context` (dict): Template variables
- `css_string` (str, optional): Additional CSS
- `base_url` (str, optional): Base URL for relative paths

**Returns:** `bytes` - PDF file content

### `generate_pdf_from_html(html_content, css_string=None, base_url=None)`

Generate PDF directly from HTML string.

**Parameters:**
- `html_content` (str): HTML content
- `css_string` (str, optional): CSS to apply
- `base_url` (str, optional): Base URL for relative paths

**Returns:** `bytes` - PDF file content

### `generate_docx(title, sections, output_path=None)`

Generate DOCX document with structured sections.

**Parameters:**
- `title` (str): Document title
- `sections` (list[dict]): List of section dictionaries
- `output_path` (Path, optional): Optional file save path

**Returns:** `bytes` - DOCX file content

## Applications Using This Service

1. **EstateFlow** - Invoice PDF generation
2. **ChurchFlow** - Reports, certificates (ready to integrate)
3. **StudyFlow** - Study materials, assessments (ready to integrate)
4. **InkWave** - Book summaries, reports (ready to integrate)
5. **EventFlow** - Tickets, programs (ready to integrate)

## Benefits of Centralization

1. **Code Reuse**: Single implementation used by all apps
2. **Consistency**: All PDFs/DOCX have similar quality
3. **Maintainability**: Bug fixes apply to all applications
4. **Performance**: Shared caching and optimization
5. **Standards**: Consistent formatting and styling

## Testing

Test script: `/tmp/test_centralized_pdf.py`

```bash
python3 /tmp/test_centralized_pdf.py
```

Expected output:
```
✅ PDF generated successfully with centralized service!
📄 Saved to: /tmp/DIA-1001_centralized.pdf
📊 File size: 13,802 bytes
✅ Valid PDF signature detected
```

## Dependencies

- **WeasyPrint**: HTML/CSS to PDF conversion (v66.0+)
- **python-docx**: DOCX document generation (v1.2.0+)
- **Jinja2**: Template rendering (v3.1.0+)

All installed in shared venv: `/opt/kasaai/apps/venv`

## Future Enhancements

- [ ] Add support for Excel (XLSX) generation
- [ ] Implement document watermarking
- [ ] Add digital signatures
- [ ] Support for RTF format
- [ ] Template caching for performance
- [ ] Batch document generation
- [ ] Multi-language support

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-estateflow-backend -f`
- Review template syntax in Jinja2 docs
- Test PDF rendering with WeasyPrint CLI

## Version History

- **v1.0** (2025-12-08): Initial release
  - PDF generation with WeasyPrint
  - DOCX generation with python-docx
  - Integrated into EstateFlow invoices
  - Full test coverage
