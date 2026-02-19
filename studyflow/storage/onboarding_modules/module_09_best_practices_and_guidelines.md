# Module 9: Best Practices and Guidelines

**Topics Covered:** coding_standards, git_workflow, documentation

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 9. Best Practices & Guidelines

### 💻 Code Quality

**Always Follow**:

1. **PEP 8** for Python code
2. **Type Hints** everywhere (`def function(arg: str) -> int:`)
3. **Docstrings** for all functions (Google style)
4. **Error Handling** with try/except and logging
5. **Consistent Naming**: snake_case (Python), camelCase (TypeScript)

**Example**:

```python
async def get_user_wallet_balance(user_id: str, organization_id: str) -> float:
    """
    Get the current wallet balance for a user.

    Args:
        user_id: The unique identifier for the user
        organization_id: The organization the user belongs to

    Returns:
        The current balance as a float

    Raises:
        ValueError: If user not found
        DatabaseError: If database connection fails
    """
    try:
        wallet = await db.wallets.find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })

        if not wallet:
            raise ValueError(f"Wallet not found for user {user_id}")

        return wallet.get("balance", 0.0)

    except Exception as e:
        logger.error(f"Failed to get wallet balance: {e}")
        raise DatabaseError("Could not retrieve wallet balance") from e
```

---

### 🧪 Testing

**Test Requirements**:
- **Minimum**: 1 expected use case, 1 edge case, 1 failure case
- **Location**: `/tests/` folder mirroring main structure
- **Use Real Data**: Test with actual databases, not mocks (see `TEST_SUITE_ANALYSIS.md`)

**Example Test**:

```python
import pytest
from backend.services.wallet_service import get_wallet_service

@pytest.mark.asyncio
async def test_get_wallet_balance_success():
    """Test getting wallet balance for existing user."""
    service = get_wallet_service()
    balance = await service.get_balance(
        user_id="user123",
        org_id="org456"
    )
    assert balance >= 0.0

@pytest.mark.asyncio
async def test_get_wallet_balance_user_not_found():
    """Test error handling for non-existent user."""
    service = get_wallet_service()
    with pytest.raises(ValueError, match="Wallet not found"):
        await service.get_balance(
            user_id="nonexistent",
            org_id="org456"
        )
```

---

### 🌿 Git Workflow

**Commit Rules**:

1. **Create git commit** after each completed task
2. **Write clear commit messages** (imperative mood)
3. **Reference task/issue** if applicable

**Good Commit Messages**:

```bash
# Good ✅
git commit -m "Add CV upload functionality to HR employee form"
git commit -m "Fix mobile camera capture for expense receipts"
git commit -m "Update ERP TASKS.md with completed document management features"

# Bad ❌
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "work in progress"
```

**Branch Strategy**:

```bash
# Create feature branch
git checkout -b feature/add-expense-receipt-upload

# Make changes and commit
git add .
git commit -m "Add expense receipt upload with camera support"

# Push to remote
git push origin feature/add-expense-receipt-upload

# Create pull request (if applicable)
```

---

### 🌐 API Design

**RESTful Principles**:

- `GET /api/v1/users/{user_id}` - Retrieve
- `POST /api/v1/users` - Create
- `PATCH /api/v1/users/{user_id}` - Partial update
- `DELETE /api/v1/users/{user_id}` - Delete

**Response Format**:

```json
{
  "success": true,
  "data": {
    "id": "user123",
    "name": "John Doe"
  },
  "metadata": {
    "timestamp": "2025-11-07T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Error Format**:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 'user123' not found",
    "details": {
      "user_id": "user123"
    }
  },
  "metadata": {
    "timestamp": "2025-11-07T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

### 📚 Documentation

**Update These After Changes**:

1. **TASKS.md** - Mark completed tasks, add new discoveries
2. **README.md** - Update when adding features or changing setup
3. **PLANNING.md** - Update architecture when making structural changes
4. **API_DOCUMENTATION.md** - Document new endpoints

---
