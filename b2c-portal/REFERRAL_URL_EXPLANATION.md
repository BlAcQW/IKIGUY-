# Referral URL Explanation

**Date:** 2025-01-27

---

## The URL You're Seeing

If you see `https://kasaai.ailabsafrica.com/auth?ref=LKHG444` in your affiliate page, this is **your referral link** that you should share with others.

### Where It Appears

This URL is displayed in the **ReferralLinkGenerator** component on your affiliate dashboard. It shows:
- Your referral code: `LKHG444`
- The base URL: Currently set to homepage (`https://kasaai.ailabsafrica.com`)
- Full URL: `https://kasaai.ailabsafrica.com?ref=LKHG444`

---

## Referral Code Structure

### Format: `LKHG444`
- **4 letters** (`LKHG`) - First 4 letters of your first name (or random if not available)
- **3 digits** (`444`) - Random digits for uniqueness
- **Always uppercase**
- **Unique** - No two affiliates have the same code

### How It's Generated
```python
# If you have a first name "LKHG" (or similar)
base = first_name[:4].upper()  # "LKHG"
suffix = random.choices(digits, k=3)  # "444"
code = "LKHG444"
```

---

## How the URL Works

### When Someone Clicks Your Link

**Example:** `https://kasaai.ailabsafrica.com?ref=LKHG444`

1. **System Detects Code**
   - Extracts `LKHG444` from `?ref=` parameter
   - Stores in cookie (30 days)
   - Stores in LocalStorage (backup)

2. **Redirect Logic**
   ```
   If not logged in → /affiliates/join
   If logged in, not affiliate → /affiliates/join
   If logged in, is affiliate → /affiliates/dashboard
   ```

3. **URL Cleanup**
   - Removes `?ref=LKHG444` from URL
   - Changes to: `https://kasaai.ailabsafrica.com/affiliates/join`
   - Code remains in cookie for signup/join

4. **Code Persists**
   - Available for 30 days
   - Auto-populated in signup/join forms
   - Used for attribution when they sign up

---

## Why `/auth` in the URL?

If you're seeing `/auth?ref=LKHG444`, this could be:

1. **Old Code Version** - Previously the dashboard used `/auth` as base URL
2. **Displayed Link** - The ReferralLinkGenerator showing your shareable link
3. **Browser Address Bar** - You navigated to this URL directly

**Note:** The current code uses the homepage (`https://kasaai.ailabsafrica.com`) as the base URL, which is the correct approach.

---

## Current Implementation

### Backend API Returns:
```json
{
  "referral_code": "LKHG444",
  "base_url": "https://kasaai.ailabsafrica.com",
  "full_url": "https://kasaai.ailabsafrica.com?ref=LKHG444"
}
```

### Frontend Dashboard:
- Fetches base URL from API (not hardcoded)
- Displays: `https://kasaai.ailabsafrica.com?ref=LKHG444`
- This is the link you should share

---

## What Happens When Someone Clicks

### Scenario 1: New User (No Account)
```
1. Clicks: https://kasaai.ailabsafrica.com?ref=LKHG444
2. Redirects to: /affiliates/join
3. Code stored in cookie
4. User can sign up (code auto-populated)
5. After signup → attributed to you (LKHG444)
```

### Scenario 2: Existing User (Not Affiliate)
```
1. Clicks: https://kasaai.ailabsafrica.com?ref=LKHG444
2. Redirects to: /affiliates/join
3. Code stored in cookie
4. Code pre-filled in join form
5. User joins → you become their upline
```

### Scenario 3: Existing Affiliate
```
1. Clicks: https://kasaai.ailabsafrica.com?ref=LKHG444
2. Redirects to: /affiliates/dashboard
3. Code still tracked (for analytics)
4. No attribution (they're already an affiliate)
```

---

## Summary

**Your Referral Code:** `LKHG444`

**Your Referral Link:** `https://kasaai.ailabsafrica.com?ref=LKHG444`

**What to Share:** The link above (homepage with your code)

**What Happens:** Anyone who clicks it gets redirected to the affiliate join page with your code preserved for attribution.

---

## If You See `/auth?ref=CODE`

This is likely:
- An old cached version
- Or a link that was generated with `/auth` as base URL

**Solution:** The code has been updated to use the homepage as base URL. After rebuilding, your referral link will be:
```
https://kasaai.ailabsafrica.com?ref=LKHG444
```

Both URLs work the same way - they both redirect to `/affiliates/join` and preserve the referral code.


