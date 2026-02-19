# Fix: Blank Fields When Editing Expenses

## Problem
When editing expenses in the ERP application, form fields (especially dates) were appearing blank even though the data existed in the database.

## Root Causes

### 1. Backend Date Serialization Issue
**File:** `/opt/kasaai/apps/erp/backend/app/models/base.py`

The date encoder was incorrectly converting `date` objects to `datetime` objects before serialization:

```python
# BEFORE (INCORRECT)
date: lambda v: datetime.combine(v, datetime.min.time()) if isinstance(v, date) else v

# AFTER (CORRECT)
date: lambda v: v.isoformat() if isinstance(v, date) else v
```

**Impact:** The API was returning dates with timestamps (e.g., `"2025-11-12T00:00:00Z"`) instead of simple date strings (`"2025-11-12"`), which HTML date inputs couldn't parse.

### 2. Frontend Date Format Handling
**File:** `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx`

The `handleEdit` function wasn't normalizing date formats when populating the edit form. Added a helper function to convert various date formats to YYYY-MM-DD:

```typescript
const handleEdit = (item: any) => {
  setSelectedItem(item)

  // Normalize date fields for form inputs
  const normalizedData = { ...item }

  // Helper function to convert date to YYYY-MM-DD format
  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return ''
      return date.toISOString().split('T')[0]
    } catch {
      return ''
    }
  }

  // Normalize dates based on active tab (expenses, transactions, invoices, budgets)
  switch (activeTab) {
    case 'expenses':
      if (normalizedData.expense_date) {
        normalizedData.expense_date = formatDate(normalizedData.expense_date)
      }
      break
    // ... other cases
  }

  setFormData(normalizedData)
  setIsModalOpen(true)
}
```

### 3. Numeric Field Handling
**File:** `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx`

Changed `|| ''` to `?? ''` for numeric and date fields to properly handle `0` values and empty strings:

```typescript
// BEFORE: Would show blank if amount is 0
value={formData.amount || ''}

// AFTER: Shows 0 correctly
value={formData.amount ?? ''}
```

Applied to fields:
- `expense_date`
- `merchant`
- `category`
- `amount`
- `tax_amount`
- `currency`
- `description`
- `payment_method`
- `status`

## Testing

### Database Test
Created `/opt/kasaai/apps/erp/backend/tests/test_expense_date_format.py` to verify:
- ✅ Dates stored as `datetime` objects in MongoDB
- ✅ Dates can be formatted to YYYY-MM-DD
- ✅ All expense fields are preserved

### API Test
Created `/opt/kasaai/apps/erp/backend/tests/test_api_date_format.py` to verify:
- ✅ API returns dates in YYYY-MM-DD format (not datetime with timestamps)
- ✅ Dates can be parsed by HTML date inputs

## Changes Made

### Backend
1. `app/models/base.py` - Fixed date serialization (line 33)
2. `tests/test_expense_date_format.py` - Database date format test (new)
3. `tests/test_api_date_format.py` - API date format test (new)
4. `tests/test_expense_edit_fix.py` - Comprehensive integration test (new)

### Frontend
1. `src/pages/FinancePage.tsx`:
   - Updated `handleEdit()` function (lines 192-242)
   - Fixed expense form field bindings (lines 1019, 1030, 1042, 1062, 1076, 1084, 1100, 1113, 1127)

## Deployment

### Backend
```bash
sudo systemctl restart kasaai-erp-backend
sudo systemctl status kasaai-erp-backend
```

### Frontend
```bash
cd /opt/kasaai/apps/erp/frontend
npm run build
```

## Manual Testing Steps

1. Open ERP frontend: https://dev-erp.ailabsafrica.com
2. Navigate to Finance & Accounting → Expenses tab
3. Click "Edit" on any expense
4. Verify all fields are populated correctly:
   - ✅ Expense Date shows the correct date
   - ✅ Merchant/Vendor name appears
   - ✅ Category is selected
   - ✅ Amount shows correct value (including 0)
   - ✅ Tax Amount shows correct value
   - ✅ Currency is selected
   - ✅ Description is populated
   - ✅ Payment Method is selected
   - ✅ Status is selected

## Impact

This fix resolves the issue for:
- ✅ Expenses (expense_date)
- ✅ Transactions (transaction_date)
- ✅ Invoices (issue_date, due_date)
- ✅ Budgets (period_start, period_end)

All tabs now properly display and edit date fields.

## Status

**COMPLETED** ✅

- [x] Backend date serialization fixed
- [x] Frontend date normalization implemented
- [x] Numeric field handling corrected
- [x] Tests created and passing
- [x] Frontend built
- [x] Backend restarted
- [x] Ready for testing

## Notes

- The fix uses TypeScript's nullish coalescing operator (`??`) which is more appropriate than logical OR (`||`) for form fields
- Date normalization handles both ISO format with timestamps and YYYY-MM-DD strings
- The solution is backward-compatible with existing data
