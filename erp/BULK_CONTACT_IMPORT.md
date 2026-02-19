# Bulk Contact Import Feature

## Overview
Added bulk contact import functionality to CRM that allows importing contacts from Excel/CSV files with minimal data requirements. Can handle files with just phone numbers and gradually enrich data later.

## Backend Implementation

### 1. New Schemas (`app/schemas/crm.py`)
- **ContactImportRow**: Schema for minimal contact data (phone, email, name, etc. - all optional)
- **ContactBulkImportRequest**: Request schema for bulk import
- **ContactBulkImportResult**: Response schema with import statistics

### 2. New Helper Module (`app/api/routes/crm_bulk_import.py`)
- **parse_excel_file()**: Parses Excel/CSV files with flexible column naming
  - Supports variations: phone/Phone Number/mobile/cell
  - Supports: email, first_name/FirstName, last_name/LastName, company, job_title, notes
  - Handles both .xlsx and .csv files
  - Skips empty rows automatically

- **bulk_import_contacts()**: Imports contacts into CRM
  - Creates or finds customer to associate contacts with
  - Handles minimal required data (uses placeholders for missing required fields)
  - Supports duplicate detection
  - Returns detailed statistics

### 3. New API Endpoints (`app/api/routes/crm.py`)

#### POST /crm/contacts/bulk-import/file
Accepts Excel or CSV file upload.

**Query Parameters:**
- `customer_name` (optional): Name of customer to associate contacts with (default: "Imported Contacts")
- `skip_duplicates` (optional): Skip duplicate phone numbers (default: true)

**Example minimal CSV:**
```csv
phone
+233501234567
+233509876543
+1234567890
```

**Example with more data:**
```csv
phone,first_name,last_name,company,email
+233501234567,John,Doe,Acme Inc,john@acme.com
+233509876543,Jane,Smith,Tech Corp,jane@tech.com
```

**Response:**
```json
{
  "total_rows": 10,
  "successful": 8,
  "failed": 1,
  "skipped": 1,
  "customer_id": "cust_123",
  "created_contact_ids": ["cont_1", "cont_2", ...],
  "errors": [{"row": 5, "error": "Invalid email format"}]
}
```

#### POST /crm/contacts/bulk-import/json
Accepts JSON array of contacts (alternative to file upload).

**Request Body:**
```json
{
  "contacts": [
    {"phone": "+233501234567"},
    {"phone": "+233509876543", "first_name": "John", "last_name": "Doe"}
  ],
  "customer_name": "Imported Contacts",
  "skip_duplicates": true
}
```

#### GET /crm/contacts/bulk-import/template
Downloads a template Excel file with example data showing all supported columns.

## Features

### Flexible Column Mapping
The system recognizes multiple column name variations:
- **Phone**: phone, phone_number, mobile, mobile_number, cell, cell_phone
- **Email**: email, e-mail, email_address
- **First Name**: first_name, firstname, given_name
- **Last Name**: last_name, lastname, surname, family_name
- **Company**: company, company_name, organization
- **Job Title**: job_title, title, position, role
- **Notes**: notes, comments, description

### Minimal Data Requirements
- Accepts files with **just phone numbers**
- Uses placeholders for missing required fields:
  - first_name: "Contact" (if missing)
  - last_name: "#1", "#2", etc. (if missing)
  - email: "contact1@placeholder.local" (if missing)
- Company name stored in notes field if provided

### Customer Association
- Automatically creates or finds a customer named "Imported Contacts" (or custom name)
- All imported contacts associated with this customer
- Enables organizing imported contacts together

### Duplicate Handling
- Optional duplicate detection based on phone numbers
- Skips duplicates by default
- Returns count of skipped records

### Error Handling
- Detailed error reporting per row
- Continues processing even if some rows fail
- Returns statistics: successful, failed, skipped counts

## Usage Examples

### 1. Simple Phone Number List
Create a CSV file with just phone numbers:
```csv
phone
+233501234567
+233509876543
+233551234567
```

Upload via API or frontend - contacts will be created with placeholder names.

### 2. Enriched Contact List
Create an Excel file with more data:
```
Phone Number | First Name | Last Name | Company      | Email
+233501234567| John       | Doe       | Acme Inc     | john@acme.com
+233509876543| Jane       | Smith     | Tech Corp    | jane@tech.com
+233551234567| Bob        | Johnson   | Retail Store |
```

### 3. Gradual Enrichment
1. Import contacts with just phone numbers
2. Later, update contacts individually with:
   - Names
   - Emails
   - Company information
   - Job titles
   - Notes

## Database Schema
Contacts are stored with these fields:
```python
{
  "id": "cont_uuid",
  "organization_id": "org_123",
  "customer_id": "cust_imported",
  "first_name": "Contact",      # Placeholder if not provided
  "last_name": "#1",             # Placeholder if not provided
  "email": "contact1@placeholder.local",  # Placeholder if not provided
  "phone": "+233501234567",      # From import
  "mobile": null,
  "job_title": null,
  "notes": "Imported from bulk upload. Company: N/A",
  "is_primary": false,
  "is_active": true,
  "created_at": "2025-11-03T...",
  "created_by": "user_123"
}
```

## Dependencies Added
- `pandas>=2.0.0` - Excel/CSV parsing
- `openpyxl>=3.1.0` - Excel file support

## Testing

### Test with cURL:
```bash
# Upload file
curl -X POST http://localhost:8000/api/v1/crm/contacts/bulk-import/file \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -F "file=@contacts.csv" \
  -F "customer_name=My Contacts" \
  -F "skip_duplicates=true"

# Download template
curl -X GET http://localhost:8000/api/v1/crm/contacts/bulk-import/template \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o template.xlsx
```

### Test with Python:
```python
import requests

# Upload file
with open('contacts.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/crm/contacts/bulk-import/file',
        files={'file': f},
        params={'customer_name': 'Imported Contacts'},
        headers={
            'Authorization': 'Bearer YOUR_TOKEN',
            'X-Organization-ID': 'YOUR_ORG_ID'
        }
    )
    print(response.json())
```

## Future Enhancements
1. **Frontend UI**: Add upload button and progress indicator to CRM page
2. **Background Jobs**: Handle large imports (10,000+) via background tasks
3. **Validation Rules**: Add phone number format validation
4. **Deduplication Strategy**: More sophisticated duplicate detection (fuzzy matching)
5. **Import History**: Track import sessions and allow rollback
6. **Field Mapping UI**: Allow users to map columns interactively
7. **Auto-enrichment**: Integration with contact data APIs to auto-fill missing info
8. **Import Templates**: Predefined templates for different use cases

## Notes
- All imports are organization-scoped
- Contacts can be edited individually after import to add missing data
- The "Imported Contacts" customer serves as a container for organizing imported data
- Duplicate detection is optional and based on phone number matching
- Import is synchronous; for large files, consider implementing async processing
