# PDF Extraction & File Upload Services

**Status:** ✅ Implemented
**Location:** `@shared/services/`
**Last Updated:** 2025-11-03
**Version:** 1.0.0

---

## Overview

This document describes the PDF extraction and file upload services available in the shared services library. These services enable applications to:

1. **Extract structured data from PDF receipts and invoices**
2. **Upload files to cloud storage with validation**
3. **Auto-fill expense forms from uploaded receipts**

These services are designed to be reusable across all applications in the KasaAI ecosystem.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│            (ERP, ChurchFlow, EventFlow, etc.)           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Shared Services Layer                  │
├──────────────────────────┬──────────────────────────────┤
│  PDF Extraction Service  │  File Upload Service         │
│  - Pattern matching      │  - Validation                │
│  - OCR support           │  - Cloud storage             │
│  - AI extraction         │  - URL generation            │
└──────────────────────────┴──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                    │
├──────────────────────────┬──────────────────────────────┤
│  pdfplumber/pytesseract  │  Hetzner Storage Box         │
│  (PDF processing)        │  (File storage)              │
└──────────────────────────┴──────────────────────────────┘
```

---

## PDF Extraction Service

### Location
`@shared/services/pdf_extraction_service.py`

### Purpose
Extract structured expense data from PDF receipts and invoices, including:
- Merchant/vendor name
- Transaction date
- Total amount
- Tax amount
- Currency
- Category (inferred)
- Payment method
- Receipt number

### Features

#### 1. Multiple Extraction Methods
- **Text-based extraction**: For digital PDFs using pdfplumber
- **OCR extraction**: For scanned receipts using Tesseract
- **Pattern matching**: Regex-based extraction of common formats
- **AI extraction**: Optional LLM-powered extraction (coming soon)

#### 2. Confidence Scoring
Each extraction includes a confidence score (0.0-1.0) based on:
- Number of fields successfully extracted
- Data quality and consistency
- Pattern match strength

#### 3. Multi-language Support
- Configurable OCR language (`eng`, `fra`, `spa`, etc.)
- Extensible pattern matching for different locales

---

### Usage

#### Basic Usage

```python
from apps.shared.services.pdf_extraction_service import (
    get_pdf_extraction_service,
    PDFExtractionError
)

# Get service instance
pdf_service = get_pdf_extraction_service(use_ocr=True)

# Extract data from PDF
with open("receipt.pdf", "rb") as pdf_file:
    expense_data = await pdf_service.extract_from_pdf(pdf_file)

# Access extracted fields
print(f"Merchant: {expense_data.merchant}")
print(f"Amount: {expense_data.amount}")
print(f"Date: {expense_data.date}")
print(f"Confidence: {expense_data.confidence}")

# Convert to dict
data_dict = expense_data.to_dict()
```

#### With FastAPI

```python
from fastapi import UploadFile, File
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service
import io

@router.post("/upload-receipt")
async def upload_receipt(file: UploadFile = File(...)):
    # Read file content
    content = await file.read()

    # Extract data
    pdf_service = get_pdf_extraction_service(use_ocr=True)
    pdf_file = io.BytesIO(content)
    expense_data = await pdf_service.extract_from_pdf(pdf_file)

    return expense_data.to_dict()
```

---

### Data Structure

#### ExpenseData Class

```python
class ExpenseData:
    merchant: Optional[str]           # "Starbucks", "Amazon", etc.
    date: Optional[date]               # Transaction date
    amount: Optional[Decimal]          # Total amount
    tax_amount: Optional[Decimal]      # Tax amount (if found)
    currency: str                      # "USD", "GHS", "EUR", etc.
    category: Optional[str]            # "restaurant", "office_supplies", etc.
    items: List[Dict[str, Any]]        # Line items (if found)
    payment_method: Optional[str]      # "credit_card", "cash", etc.
    receipt_number: Optional[str]      # Receipt/invoice number
    raw_text: Optional[str]            # Raw extracted text
    confidence: float                  # Extraction confidence (0.0-1.0)
```

---

### Extraction Patterns

#### Date Patterns
- `MM/DD/YYYY` or `DD/MM/YYYY`
- `YYYY-MM-DD`
- `Month DD, YYYY` (e.g., "Jan 15, 2025")
- `DD Month YYYY` (e.g., "15 Jan 2025")

#### Amount Patterns
- `Total: $XX.XX`
- `Amount: XX.XX`
- `Grand Total: XX.XX`
- Last dollar amount on line

#### Tax Patterns
- `Tax: $XX.XX`
- `VAT: XX.XX`
- `GST: XX.XX`

#### Category Inference
Based on keywords in receipt text:
- **Restaurant**: restaurant, cafe, coffee, food, dining, pizza
- **Travel**: uber, lyft, taxi, airline, hotel, airbnb
- **Office Supplies**: office, staples, pen, paper, printer
- **Utilities**: electric, water, gas, internet, phone
- **Software**: software, saas, subscription, cloud
- **Marketing**: advertising, ads, marketing

---

### Dependencies

```bash
pip install pdfplumber>=0.11.0
pip install pytesseract>=0.3.10
pip install Pillow>=10.0.0
pip install pdf2image>=1.16.3
```

**System Requirements:**
- Tesseract OCR installed (`sudo apt-get install tesseract-ocr`)
- Poppler utils for pdf2image (`sudo apt-get install poppler-utils`)

---

### Error Handling

```python
try:
    expense_data = await pdf_service.extract_from_pdf(pdf_file)
except PDFExtractionError as e:
    # Handle extraction error
    logger.error(f"Failed to extract PDF data: {str(e)}")
    # You can still use the uploaded file even if extraction fails
```

---

## File Upload Service

### Location
`@shared/services/file_upload_service.py`

### Purpose
Handle file uploads to cloud storage with validation, organization, and URL generation.

### Features

#### 1. File Validation
- **Size limits**: Configurable per file type (PDF: 25MB, Images: 10MB, Documents: 50MB)
- **Type validation**: MIME type and magic byte checking
- **Content validation**: Verify file integrity

#### 2. Automatic Organization
Files are organized by:
- Organization ID
- File category (receipts, invoices, documents)
- Year and month (for easy browsing)

**Path Structure:**
```
uploads/{org_id}/{category}/{year}/{month}/{file_id}.pdf
```

Example:
```
uploads/org_abc123/receipts/2025/11/20251103120000_a1b2c3d4.pdf
```

#### 3. Storage Backends
- **Hetzner Storage Box** (production)
- **Local file system** (development/fallback)

---

### Usage

#### Basic Upload

```python
from apps.shared.services.file_upload_service import (
    get_file_upload_service,
    FileUploadError,
    FileValidationError
)

# Get service instance
upload_service = await get_file_upload_service()

# Upload file
with open("receipt.pdf", "rb") as file:
    upload_info = await upload_service.upload_file(
        file=file,
        filename="receipt.pdf",
        organization_id="org_abc123",
        file_category="receipts",
        metadata={
            "uploaded_by": "user_123",
            "description": "Office supplies receipt"
        }
    )

print(f"File URL: {upload_info['url']}")
print(f"File ID: {upload_info['file_id']}")
```

#### With FastAPI

```python
from fastapi import UploadFile, File
from apps.shared.services.file_upload_service import get_file_upload_service

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    organization_id: str
):
    # Read content
    content = await file.read()

    # Upload
    upload_service = await get_file_upload_service()
    upload_info = await upload_service.upload_file(
        file=content,
        filename=file.filename,
        organization_id=organization_id,
        file_category="receipts"
    )

    return upload_info
```

---

### Upload Response

```python
{
    "file_id": "20251103120000_a1b2c3d4",
    "filename": "receipt.pdf",
    "url": "https://storage.ailabsafrica.com/uploads/org_abc/receipts/2025/11/...",
    "path": "uploads/org_abc/receipts/2025/11/20251103120000_a1b2c3d4.pdf",
    "size": 12345,
    "mime_type": "application/pdf",
    "uploaded_at": "2025-11-03T12:00:00Z",
    "organization_id": "org_abc123",
    "category": "receipts",
    "metadata": {
        "uploaded_by": "user_123"
    }
}
```

---

### Supported File Types

| Type | Extensions | Max Size | MIME Types |
|------|-----------|----------|------------|
| **PDF** | .pdf | 25 MB | application/pdf |
| **Word** | .doc, .docx | 50 MB | application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| **Excel** | .xls, .xlsx | 50 MB | application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet |
| **Images** | .jpg, .png, .gif, .webp | 10 MB | image/jpeg, image/png, image/gif, image/webp |
| **Text** | .txt, .csv | 25 MB | text/plain, text/csv |

---

### Error Handling

```python
try:
    upload_info = await upload_service.upload_file(...)
except FileValidationError as e:
    # File validation failed (wrong type, too large, corrupted)
    return {"error": "Invalid file", "message": str(e)}
except FileUploadError as e:
    # Upload failed (storage issue, network error)
    return {"error": "Upload failed", "message": str(e)}
```

---

## Integration Example: ERP Expense Upload

This example shows the complete flow of uploading a receipt and creating an expense.

### Backend Endpoint (`@erp/backend/`)

```python
@router.post("/expenses/upload-receipt")
async def upload_expense_receipt(
    file: UploadFile = File(...),
    extract_data: bool = Query(True),
    scope: OrganizationScoped = Depends(),
):
    # Read file
    file_content = await file.read()

    # Upload to storage
    upload_service = await get_file_upload_service()
    upload_info = await upload_service.upload_file(
        file=file_content,
        filename=file.filename,
        organization_id=scope.org_id,
        file_category="receipts"
    )

    # Extract data
    extracted_data = None
    if extract_data:
        pdf_service = get_pdf_extraction_service(use_ocr=True)
        pdf_file = io.BytesIO(file_content)
        expense_data = await pdf_service.extract_from_pdf(pdf_file)
        extracted_data = expense_data.to_dict()

    return {
        "receipt_url": upload_info["url"],
        "extracted_data": extracted_data
    }
```

### Frontend Usage (React/TypeScript)

```typescript
const handleFileUpload = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/finance/expenses/upload-receipt', formData)
  const { receipt_url, extracted_data } = response.data

  // Auto-fill form with extracted data
  setFormData({
    merchant: extracted_data.merchant,
    expense_date: extracted_data.date,
    amount: extracted_data.amount,
    tax_amount: extracted_data.tax_amount,
    category: extracted_data.category,
    payment_method: extracted_data.payment_method,
    receipt_urls: [receipt_url]  // Add to receipts array
  })
}
```

---

## Configuration

### Environment Variables

```bash
# Hetzner Storage Box credentials
HETZNER_STORAGE_PASSWORD=your_password_here
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de

# Storage base URL for file access
HETZNER_STORAGE_BASE_URL=https://storage.ailabsafrica.com

# OCR configuration
TESSERACT_LANGUAGE=eng  # or 'fra', 'spa', etc.
```

### Service Configuration

```python
# PDF Extraction Service
pdf_service = get_pdf_extraction_service(
    use_ocr=True,          # Enable OCR for scanned documents
    ocr_language='eng'     # Tesseract language code
)

# File Upload Service
upload_service = await get_file_upload_service(
    storage_service=hetzner_storage_box,  # Optional: provide storage instance
    base_path="uploads"                    # Base path in storage
)
```

---

## Testing

### Unit Tests

Tests are located in `@erp/backend/tests/services/`

```python
import pytest
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service
from apps.shared.services.file_upload_service import get_file_upload_service

@pytest.mark.asyncio
async def test_pdf_extraction():
    """Test PDF data extraction."""
    pdf_service = get_pdf_extraction_service(use_ocr=False)

    with open("tests/fixtures/sample_receipt.pdf", "rb") as file:
        expense_data = await pdf_service.extract_from_pdf(file)

    assert expense_data.merchant is not None
    assert expense_data.amount is not None
    assert expense_data.confidence > 0.5

@pytest.mark.asyncio
async def test_file_upload():
    """Test file upload."""
    upload_service = await get_file_upload_service()

    with open("tests/fixtures/sample_receipt.pdf", "rb") as file:
        upload_info = await upload_service.upload_file(
            file=file.read(),
            filename="test_receipt.pdf",
            organization_id="test_org",
            file_category="receipts"
        )

    assert upload_info["file_id"] is not None
    assert upload_info["url"].endswith(".pdf")
```

---

## Performance Considerations

### PDF Extraction
- **Text extraction**: ~100-500ms per page (fast)
- **OCR extraction**: ~2-5s per page (slower)
- **AI extraction**: ~1-3s (requires LLM API call, costs money)

**Recommendations:**
- Use text extraction first, fallback to OCR if needed
- Process PDFs asynchronously for better UX
- Cache extracted data to avoid re-processing

### File Upload
- **Upload time**: Depends on file size and network
- **Validation**: ~10-50ms
- **Storage**: ~100-500ms to Hetzner Storage Box

**Recommendations:**
- Show upload progress to users
- Implement chunked uploads for large files (>10MB)
- Use background tasks for post-upload processing

---

## Future Enhancements

### Planned Features
1. **AI-powered extraction** using LLMs for higher accuracy
2. **Multi-receipt processing** (batch uploads)
3. **Receipt templates** for common vendors
4. **Image receipt support** (JPEG, PNG)
5. **Email receipt parsing** (forward receipts to email)
6. **Mobile app integration** (camera capture)

### Roadmap
- **v1.1.0**: AI extraction support
- **v1.2.0**: Image receipt support
- **v1.3.0**: Batch processing
- **v2.0.0**: Mobile SDK

---

## Related Documentation
- [Developer Platform API Documentation](/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md)
- [Hetzner Storage Box Guide](/opt/kasaai/apps/shared/storage/HETZNER_STORAGE_BOX.md)
- [ERP Planning](/opt/kasaai/apps/erp/PLANNING.md)

---

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify dependencies are installed
3. Ensure Tesseract is installed system-wide
4. Check file permissions for uploads directory
5. Contact the platform team

---

**Last Updated:** 2025-11-03
**Maintainers:** AI Labs Africa Platform Team
