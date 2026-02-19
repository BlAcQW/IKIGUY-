# Referral URL Structure & Redirect Flow

**Date:** 2025-01-27

---

## Referral Code Structure

### Format
Referral codes follow this pattern:

**Primary Format:**
- **4 uppercase letters** (from user's first name) + **3 random digits**
- Example: `ALFRED001`, `JOHN123`, `MARY456`

**Fallback Format:**
- If first name not available: **4 random uppercase letters** + **3 random digits**
- Example: `ABCD123`, `XYZW789`

**Final Fallback:**
- If uniqueness fails: **8 random alphanumeric characters**
- Example: `A1B2C3D4`, `X9Y8Z7W6`

### Validation Rules
- Length: 4-20 characters
- Characters: Alphanumeric only (A-Z, 0-9)
- Case: Always uppercase
- Uniqueness: Must be unique across all affiliates

### Code Generation Logic
```python
# Primary: First name + random digits
if user.first_name:
    base = user.first_name[:4].upper()  # "ALFRED" → "ALFR"
    suffix = random.choices(digits, k=3)  # "001"
    code = "ALFR001"

# Fallback: Random letters + digits
else:
    base = random.choices(uppercase, k=4)  # "ABCD"
    suffix = random.choices(digits, k=3)   # "123"
    code = "ABCD123"
```

---

## Referral URL Structure

### Base URL
```
https://kasaai.ailabsafrica.com
```

### Standard Referral URL Format
```
https://kasaai.ailabsafrica.com?ref=ALFRED001
```

### URL Components
```
https://kasaai.ailabsafrica.com  ← Base domain
?ref=ALFRED001                   ← Query parameter with referral code
```

### With Additional Parameters
```
https://kasaai.ailabsafrica.com?ref=ALFRED001&utm_source=instagram&utm_campaign=q1_2025
```

**Components:**
- `?ref=ALFRED001` - Referral code (required)
- `&utm_source=instagram` - Traffic source (optional)
- `&utm_campaign=q1_2025` - Campaign name (optional)

### Alternative URL Paths (All Work)
The referral code works on any page:
```
https://kasaai.ailabsafrica.com?ref=ALFRED001
https://kasaai.ailabsafrica.com/signup?ref=ALFRED001
https://kasaai.ailabsafrica.com/pricing?ref=ALFRED001
https://kasaai.ailabsafrica.com/features?ref=ALFRED001
```

---

## How the URL Leads to Affiliate Page

### Step-by-Step Flow

#### 1. **User Clicks Referral Link**
```
User clicks: https://kasaai.ailabsafrica.com?ref=ALFRED001
```

#### 2. **Page Loads & Tracking Starts**
- `ReferralTracker` component in `App.tsx` runs on every page load
- Calls `trackReferralClick()` function
- Detects `?ref=ALFRED001` in URL

#### 3. **Code Processing**
```typescript
// In referral-tracking.ts
const refParam = searchParams.get('ref');  // Gets "ALFRED001"
```

**Actions taken:**
1. ✅ Stores code in cookie (`kasaai_ref`)
2. ✅ Stores code in LocalStorage (backup)
3. ✅ Tracks click on backend API
4. ✅ Extracts UTM parameters (if any)

#### 4. **Redirect Decision Logic**

The system checks user status and redirects accordingly:

```typescript
// Check if already on affiliate page (avoid loops)
if (currentPath.includes('/affiliates/')) {
    // Don't redirect - already there
    return;
}

// Check authentication
if (isAuthenticated) {
    // Check if user is already an affiliate
    if (user is affiliate) {
        → Redirect to: /affiliates/dashboard
    } else {
        → Redirect to: /affiliates/join
    }
} else {
    // Not logged in
    → Redirect to: /affiliates/join
}
```

#### 5. **Redirect Execution**
```typescript
// In App.tsx - ReferralTracker component
const result = await trackReferralClick();

if (result.shouldRedirect && result.redirectPath) {
    navigate(result.redirectPath);  // React Router navigation
}
```

#### 6. **URL Cleanup**
After redirect, the `?ref=ALFRED001` parameter is removed from URL:
```typescript
// Clean URL (remove ref parameter) for better UX
const cleanUrl = new URL(window.location.href);
cleanUrl.searchParams.delete('ref');
window.history.replaceState({}, '', cleanUrl.toString());
```

**Result:** URL changes from:
```
https://kasaai.ailabsafrica.com?ref=ALFRED001
```
To:
```
https://kasaai.ailabsafrica.com/affiliates/join
```

---

## Redirect Scenarios

### Scenario 1: Not Logged In
```
1. User clicks: https://kasaai.ailabsafrica.com?ref=ALFRED001
2. System detects: Not authenticated
3. Redirects to: /affiliates/join
4. Code stored in cookie/LocalStorage
5. User can sign up (code auto-populated)
```

### Scenario 2: Logged In, Not an Affiliate
```
1. User clicks: https://kasaai.ailabsafrica.com?ref=ALFRED001
2. System detects: Authenticated but not affiliate
3. Redirects to: /affiliates/join
4. Code stored in cookie/LocalStorage
5. Code pre-filled in join form
6. User can join program
```

### Scenario 3: Logged In, Already an Affiliate
```
1. User clicks: https://kasaai.ailabsafrica.com?ref=ALFRED001
2. System detects: Already an affiliate
3. Redirects to: /affiliates/dashboard
4. Code still tracked (for analytics)
5. User sees their dashboard
```

### Scenario 4: Already on Affiliate Page
```
1. User clicks: https://kasaai.ailabsafrica.com/affiliates/join?ref=ALFRED001
2. System detects: Already on /affiliates/ page
3. No redirect (avoids loop)
4. Code stored in cookie/LocalStorage
5. Code auto-populated in form
```

---

## Code Storage & Persistence

### Storage Locations
1. **Cookie** (`kasaai_ref`)
   - Expires: 30 days
   - Path: `/` (entire site)
   - Secure: Yes (HTTPS only)
   - SameSite: Lax

2. **LocalStorage** (`kasaai_ref`)
   - Backup storage
   - Survives cookie clearing
   - Same 30-day expiry logic

### Storage Format
```json
{
  "referral_code": "ALFRED001",
  "timestamp": 1706371200000,
  "utm_params": {
    "utm_source": "instagram",
    "utm_campaign": "q1_2025"
  },
  "landing_page": "/"
}
```

---

## Complete Flow Diagram

```
User clicks referral link
    ↓
https://kasaai.ailabsafrica.com?ref=ALFRED001
    ↓
ReferralTracker detects ?ref= parameter
    ↓
Store code in cookie + LocalStorage
    ↓
Track click on backend API
    ↓
Check user status
    ├─ Not logged in → /affiliates/join
    ├─ Logged in, not affiliate → /affiliates/join
    └─ Logged in, is affiliate → /affiliates/dashboard
    ↓
Navigate to appropriate page
    ↓
Remove ?ref= from URL (clean URL)
    ↓
Code remains in cookie for signup/join
```

---

## Example URLs

### Basic Referral Link
```
https://kasaai.ailabsafrica.com?ref=ALFRED001
```

### With UTM Tracking
```
https://kasaai.ailabsafrica.com?ref=ALFRED001&utm_source=instagram&utm_campaign=q1_2025&utm_medium=social
```

### Direct to Signup Page
```
https://kasaai.ailabsafrica.com/signup?ref=ALFRED001
```

### Direct to Pricing Page
```
https://kasaai.ailabsafrica.com/pricing?ref=ALFRED001
```

**Note:** All of these URLs will redirect to `/affiliates/join` (or `/affiliates/dashboard` if already an affiliate) after processing the referral code.

---

## Technical Implementation

### Frontend Files
- `src/App.tsx` - ReferralTracker component
- `src/lib/referral-tracking.ts` - Core tracking logic
- `src/components/auth/MongoSignupForm.tsx` - Auto-population

### Backend Files
- `backend/routes/affiliates.py` - Referral code API
- `backend/services/affiliate_service.py` - Code generation

### Key Functions
```typescript
// Track referral click and determine redirect
trackReferralClick() → { shouldRedirect: boolean, redirectPath?: string }

// Store referral code
storeReferralData(code, utmParams) → void

// Get referral code
getReferralCode() → string | null
```

---

## Summary

**Referral Code Format:**
- `ALFRED001` (4 letters + 3 digits)
- Always uppercase
- Unique per affiliate

**URL Format:**
- `https://kasaai.ailabsafrica.com?ref=ALFRED001`
- Works on any page path

**Redirect Flow:**
1. User clicks link with `?ref=CODE`
2. Code stored in cookie/LocalStorage
3. System checks user status
4. Redirects to `/affiliates/join` or `/affiliates/dashboard`
5. URL cleaned (removes `?ref=` parameter)
6. Code persists for signup/join

**Result:** Seamless experience where clicking any referral link automatically takes users to the appropriate affiliate page with their referral code preserved.


