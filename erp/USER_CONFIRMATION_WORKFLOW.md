# User Confirmation Workflow for PDF Receipts

**Status:** Best Practice Documentation
**Date:** 2025-11-03
**Version:** 1.0.0

---

## Overview

This document describes the **user confirmation workflow** for PDF receipt uploads in the ERP system. This workflow ensures data accuracy and gives users control over their expense data.

### Why User Confirmation?

❌ **Bad**: Auto-save extracted data without review
- OCR/AI can make mistakes
- User has no control
- Incorrect data enters system
- Creates data quality issues

✅ **Good**: Extract → Show → Confirm → Save
- User reviews extracted data
- Can correct mistakes
- Maintains data quality
- User stays in control

---

## Workflow Steps

```
┌─────────────────────────────────────────────────────────┐
│  1. User uploads PDF receipt                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  2. Backend extracts data (pattern or AI)               │
│     - Merchant, date, amount, tax, category, etc.       │
│     - Returns confidence score (0.0-1.0)                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  3. Frontend displays extracted data                    │
│     ✓ Show all extracted fields                         │
│     ✓ Highlight low-confidence fields                   │
│     ✓ Show PDF preview side-by-side                     │
│     ✓ Allow editing of all fields                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  4. User reviews and confirms/edits                     │
│     - Review extracted data                             │
│     - Edit incorrect fields                             │
│     - Verify confidence warnings                        │
│     - Click "Confirm & Save"                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  5. Frontend saves confirmed data                       │
│     POST /finance/expenses (confirmed data)             │
└─────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Upload Receipt (Extraction)

```http
POST /finance/expenses/upload-receipt
Content-Type: multipart/form-data

file: <PDF file>
extract_data: true
use_ai: false  # true for AI extraction (~$0.01/receipt)
```

**Response:**
```json
{
  "receipt_url": "https://storage.../receipts/...",
  "file_id": "20251103120000_a1b2c3d4",
  "uploaded_at": "2025-11-03T12:00:00Z",
  "extracted_data": {
    "merchant": "Starbucks",
    "expense_date": "2025-11-03",
    "amount": 15.50,
    "tax_amount": 1.50,
    "currency": "USD",
    "category": "restaurant",
    "payment_method": "credit_card",
    "receipt_number": "ABC123",
    "confidence": 0.85,
    "extraction_method": "pattern",  // or "ai"
    "requires_review": false  // true if confidence < 0.7
  },
  "requires_confirmation": true,  // Always true
  "extraction_method": "pattern"
}
```

**Important:**
- `requires_confirmation: true` means DO NOT auto-save
- Show extracted data to user for review
- User must explicitly confirm

### 2. Save Expense (After Confirmation)

```http
POST /finance/expenses
Content-Type: application/json

{
  "expense_date": "2025-11-03",
  "merchant": "Starbucks",
  "category": "restaurant",
  "amount": 15.50,
  "tax_amount": 1.50,
  "currency": "USD",
  "payment_method": "credit_card",
  "receipt_urls": ["https://storage.../receipts/..."],
  "notes": "Team meeting coffee"
}
```

---

## Frontend Implementation

### 1. File Upload Component

```typescript
// FileUpload.tsx
interface UploadResult {
  receipt_url: string
  extracted_data: ExtractedData
  requires_confirmation: boolean
  extraction_method: 'pattern' | 'ai'
}

interface ExtractedData {
  merchant?: string
  expense_date?: string
  amount?: number
  tax_amount?: number
  currency?: string
  category?: string
  payment_method?: string
  receipt_number?: string
  confidence?: number
  extraction_method?: string
  requires_review?: boolean
  error?: string
  message?: string
}

const FileUpload: React.FC<{
  onUploadComplete: (result: UploadResult) => void
}> = ({ onUploadComplete }) => {
  const [uploading, setUploading] = useState(false)
  const [useAI, setUseAI] = useState(false)

  const handleFileChange = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post(
        `/finance/expenses/upload-receipt?extract_data=true&use_ai=${useAI}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )

      onUploadComplete(response.data)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed: ' + error.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="file-upload">
      <label className="flex items-center space-x-2 mb-2">
        <input
          type="checkbox"
          checked={useAI}
          onChange={(e) => setUseAI(e.target.checked)}
        />
        <span className="text-sm">
          Use AI extraction (more accurate, costs $0.01)
        </span>
      </label>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
        disabled={uploading}
        className="file-input"
      />

      {uploading && <div className="spinner">Uploading and extracting...</div>}
    </div>
  )
}
```

### 2. Confirmation Modal

```typescript
// ConfirmExtractedData.tsx
interface ConfirmExtractedDataProps {
  extractedData: ExtractedData
  receiptUrl: string
  onConfirm: (confirmedData: Partial<ExpenseFormData>) => void
  onCancel: () => void
}

const ConfirmExtractedData: React.FC<ConfirmExtractedDataProps> = ({
  extractedData,
  receiptUrl,
  onConfirm,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    merchant: extractedData.merchant || '',
    expense_date: extractedData.expense_date || '',
    amount: extractedData.amount || 0,
    tax_amount: extractedData.tax_amount || 0,
    currency: extractedData.currency || 'USD',
    category: extractedData.category || '',
    payment_method: extractedData.payment_method || '',
    receipt_number: extractedData.receipt_number || ''
  })

  const confidence = extractedData.confidence || 0
  const requiresReview = extractedData.requires_review || confidence < 0.7

  const handleConfirm = () => {
    onConfirm({
      ...formData,
      receipt_urls: [receiptUrl]
    })
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-4xl">
        <h2 className="text-xl font-bold mb-4">
          Confirm Extracted Data
        </h2>

        {/* Confidence Warning */}
        {requiresReview && (
          <div className="bg-yellow-50 border border-yellow-200 p-3 rounded mb-4">
            <div className="flex items-center">
              <WarningIcon className="text-yellow-600 mr-2" />
              <div>
                <p className="font-semibold text-yellow-800">
                  Low Confidence - Please Review Carefully
                </p>
                <p className="text-sm text-yellow-700">
                  Confidence: {(confidence * 100).toFixed(0)}%
                  {confidence < 0.5 && ' - Many fields may be incorrect'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Extraction Method Info */}
        <div className="text-sm text-gray-600 mb-4">
          Extracted using: {extractedData.extraction_method === 'ai' ?
            '🤖 AI (Gemini)' : '📝 Pattern Matching'}
        </div>

        {/* Side-by-side layout */}
        <div className="grid grid-cols-2 gap-4">
          {/* Left: PDF Preview */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Receipt Preview</h3>
            <iframe
              src={receiptUrl}
              className="w-full h-96 border"
              title="Receipt Preview"
            />
          </div>

          {/* Right: Editable Form */}
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Extracted Data (Editable)</h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Merchant *
                  {!formData.merchant && (
                    <span className="text-red-500 ml-1">⚠️ Missing</span>
                  )}
                </label>
                <input
                  type="text"
                  value={formData.merchant}
                  onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="Merchant name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Date *
                  {!formData.expense_date && (
                    <span className="text-red-500 ml-1">⚠️ Missing</span>
                  )}
                </label>
                <input
                  type="date"
                  value={formData.expense_date}
                  onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Amount *
                  {!formData.amount && (
                    <span className="text-red-500 ml-1">⚠️ Missing</span>
                  )}
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tax Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.tax_amount}
                  onChange={(e) => setFormData({ ...formData, tax_amount: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="">Select category</option>
                  <option value="restaurant">Restaurant</option>
                  <option value="travel">Travel</option>
                  <option value="office_supplies">Office Supplies</option>
                  <option value="utilities">Utilities</option>
                  <option value="software">Software</option>
                  <option value="rent">Rent</option>
                  <option value="marketing">Marketing</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Payment Method</label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="">Select payment method</option>
                  <option value="cash">Cash</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="mobile_money">Mobile Money</option>
                  <option value="bank_transfer">Bank Transfer</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!formData.merchant || !formData.expense_date || !formData.amount}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            Confirm & Save Expense
          </button>
        </div>
      </div>
    </div>
  )
}
```

### 3. Integration in FinancePage

```typescript
// FinancePage.tsx (expenses tab)
const [showConfirmation, setShowConfirmation] = useState(false)
const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)

const handleFileUpload = (result: UploadResult) => {
  setUploadResult(result)

  // Always show confirmation modal
  if (result.requires_confirmation) {
    setShowConfirmation(true)
  }
}

const handleConfirmData = async (confirmedData: Partial<ExpenseFormData>) => {
  try {
    // Save expense with confirmed data
    const response = await api.post('/finance/expenses', confirmedData)

    setToast({ message: 'Expense saved successfully!', type: 'success' })
    setShowConfirmation(false)
    setUploadResult(null)
    fetchData() // Refresh expense list
  } catch (error) {
    setToast({ message: 'Failed to save expense', type: 'error' })
  }
}

const handleCancelConfirmation = () => {
  setShowConfirmation(false)
  setUploadResult(null)
  // Receipt is already uploaded, user can try again later
}

return (
  <div>
    {/* Upload component */}
    <FileUpload onUploadComplete={handleFileUpload} />

    {/* Confirmation modal */}
    {showConfirmation && uploadResult && (
      <ConfirmExtractedData
        extractedData={uploadResult.extracted_data}
        receiptUrl={uploadResult.receipt_url}
        onConfirm={handleConfirmData}
        onCancel={handleCancelConfirmation}
      />
    )}
  </div>
)
```

---

## User Experience Guidelines

### 1. Visual Indicators

**Confidence Levels:**
- 🟢 **High (≥ 0.8)**: Green checkmark, minimal warning
- 🟡 **Medium (0.5-0.8)**: Yellow warning, "Please review carefully"
- 🔴 **Low (< 0.5)**: Red warning, "Many fields may be incorrect"

**Field Indicators:**
- ✅ **Extracted successfully**: Green icon
- ⚠️ **Missing or empty**: Yellow warning icon
- ❌ **Extraction failed**: Red error icon

### 2. Best Practices

✅ **Do:**
- Always show confidence score
- Highlight missing/empty fields
- Show PDF preview side-by-side
- Allow editing all fields
- Disable "Confirm" until required fields filled
- Show extraction method (pattern vs AI)
- Provide "Cancel" option

❌ **Don't:**
- Auto-save without confirmation
- Hide confidence score
- Make fields non-editable
- Hide the original receipt
- Force AI extraction (let user choose)
- Skip validation

### 3. Error Handling

```typescript
// Handle extraction errors gracefully
if (extractedData.error) {
  return (
    <div className="bg-red-50 p-4 rounded">
      <p className="font-semibold text-red-800">
        Failed to extract data from receipt
      </p>
      <p className="text-sm text-red-700">{extractedData.message}</p>
      <p className="text-sm text-gray-600 mt-2">
        You can still manually enter the expense data. The receipt has been uploaded.
      </p>
      <button
        onClick={() => setFormData(getEmptyFormData())}
        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Enter Manually
      </button>
    </div>
  )
}
```

---

## Extraction Methods Comparison

| Feature | Pattern Matching | AI (Gemini) |
|---------|------------------|-------------|
| **Speed** | Fast (~0.5s) | Slower (~2-3s) |
| **Cost** | Free | ~$0.01 per receipt |
| **Accuracy** | Good for digital PDFs | Excellent for all types |
| **OCR Support** | Yes (Tesseract) | Yes (built-in) |
| **Best For** | Digital receipts, clear text | Scanned receipts, handwriting |
| **Field Detection** | Regex patterns | Context understanding |
| **Confidence** | 0.5-0.8 typical | 0.8-0.95 typical |

**Recommendation:**
- Default to pattern matching (free, fast)
- Offer AI as optional checkbox ("More accurate, costs $0.01")
- Use AI for problem receipts (low confidence)

---

## Database Schema

### Expense Model

```python
class Expense(BaseModel):
    expense_date: date                  # Transaction date
    merchant: str                       # Merchant/vendor name
    category: str                       # Expense category
    amount: float                       # Total amount
    tax_amount: float = 0.0            # Tax amount
    currency: str = "USD"              # Currency code
    payment_method: Optional[str]      # Payment method
    receipt_urls: List[str] = []       # Receipt URLs (can have multiple)
    receipt_number: Optional[str]      # Receipt/invoice number
    notes: Optional[str]               # Additional notes
    # ... other fields
```

**Important:**
- `receipt_urls` is an array (can attach multiple receipts)
- `merchant` is the primary vendor field (not "vendor")
- `expense_date` is the date field (not just "date")

---

## Testing

### Manual Testing

1. **Upload digital receipt**:
   ```bash
   curl -X POST "http://localhost:30034/finance/expenses/upload-receipt" \
     -H "X-API-Key: your_key" \
     -F "file=@digital_receipt.pdf" \
     -F "extract_data=true" \
     -F "use_ai=false"
   ```

2. **Upload scanned receipt with AI**:
   ```bash
   curl -X POST "http://localhost:30034/finance/expenses/upload-receipt" \
     -H "X-API-Key: your_key" \
     -F "file=@scanned_receipt.pdf" \
     -F "extract_data=true" \
     -F "use_ai=true"
   ```

3. **Verify response**:
   - Check `requires_confirmation: true`
   - Check `extracted_data` has mapped fields
   - Check `confidence` score
   - Check `extraction_method`

### Unit Tests

```python
@pytest.mark.asyncio
async def test_upload_requires_confirmation(client):
    """Test that upload always requires confirmation."""
    with open("tests/fixtures/sample_receipt.pdf", "rb") as file:
        response = await client.post(
            "/finance/expenses/upload-receipt",
            files={"file": ("receipt.pdf", file, "application/pdf")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["requires_confirmation"] is True
    assert "extracted_data" in data
```

---

## Security Considerations

1. **File Validation**: Already handled by FileUploadService
2. **User Authorization**: Organization-scoped via `OrganizationScoped`
3. **Data Sanitization**: Validate extracted data before saving
4. **Receipt URLs**: Ensure URLs are scoped to organization
5. **Cost Control**: Track AI extraction usage per organization

---

## Cost Optimization

### AI Extraction Costs

- **Gemini API**: ~$0.01 per receipt (15KB text)
- **Pattern matching**: Free

### Recommendations:

1. **Default to free extraction**
2. **Offer AI as opt-in** ("Get 20% more accuracy for $0.01")
3. **Track usage**: Monitor AI extraction costs per org
4. **Set limits**: Optional limit on AI extractions per month
5. **Smart fallback**: If pattern confidence < 0.5, suggest AI

```typescript
// Smart suggestion after pattern extraction
if (extractedData.confidence < 0.5 && !usedAI) {
  showNotification({
    type: 'info',
    message: 'Low confidence detected. Try AI extraction for better results?',
    actions: [
      { label: 'Use AI ($0.01)', onClick: () => retryWithAI() },
      { label: 'Continue', onClick: () => dismiss() }
    ]
  })
}
```

---

## Future Enhancements

1. **Batch Upload**: Upload multiple receipts at once
2. **Email Integration**: Forward receipts to email → auto-upload
3. **Mobile App**: Camera capture → upload → extract
4. **Learning System**: Learn from user corrections
5. **Templates**: Save common merchant patterns
6. **Audit Trail**: Track who confirmed/edited data

---

## Related Documentation

- [PDF Extraction Service](/opt/kasaai/apps/architecture/PDF_EXTRACTION_SERVICE.md)
- [PDF Upload Implementation](/opt/kasaai/apps/erp/PDF_UPLOAD_IMPLEMENTATION.md)
- [Shared Services README](/opt/kasaai/apps/shared/services/README.md)

---

**Last Updated:** 2025-11-03
**Maintained By:** AI Labs Africa Platform Team
