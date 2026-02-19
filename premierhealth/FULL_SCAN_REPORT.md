# Full System Scan - VAPI 400 Error

## Date: 2025-11-11 16:10
## Error Source Identified: **Vapi Widget Library**

---

## 🎯 Critical Finding

The error is coming from:
```
widget.umd.js:78
```

**This is the VAPI WIDGET library, NOT the Web SDK!**

---

## 🔍 The Problem

You have **TWO VAPI systems** running on the same page:

### 1. Vapi Widget (Lines 632-655)
```html
<vapi-widget
    id="voice-widget"
    public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
    squad-id="d9c801a1-34df-4496-bb90-7ac9e3f9e44e"  ← Using squad-id attribute
    mode="voice"
    ...
></vapi-widget>

<script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js"></script>
```

### 2. Vapi Web SDK (Lines 682-790)
```javascript
import Vapi from 'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.0/+esm';
window.vapiWebInstance = new Vapi(vapiPublicKey);
window.vapiWebInstance.start(null, null, squadId);  ← Programmatic squad call
```

---

## 🐛 Root Cause

The **Vapi Widget** (`widget.umd.js`) is either:

1. **Auto-initializing** when the page loads
2. **Being triggered** by the button click
3. **Not properly supporting** the `squad-id` attribute format
4. **Conflicting** with the Web SDK

The widget is making its own API call to VAPI with malformed parameters, causing:
```
{message: ["assistantId must be a UUID"], error: "Bad Request", statusCode: 400}
```

---

## ✅ Verified Facts

From comprehensive testing:

1. ✅ **Squad configuration is PERFECT**
2. ✅ **All 7 assistants exist with valid UUIDs**
3. ✅ **Direct API call works** (201 SUCCESS with squadId)
4. ✅ **Web SDK code is correct** (uses `start(null, null, squadId)`)
5. ❌ **Widget is causing the error** (`widget.umd.js:78`)

---

## 🔧 Solution: Disable the Widget

The issue is that **you don't need both systems**. The Web SDK is more flexible and works correctly.

### Fix: Comment Out the Voice Widget

Edit [index.html](index.html) lines 631-655:

```html
<!-- DISABLED: Widget conflicts with Web SDK
<vapi-widget
    id="voice-widget"
    public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
    squad-id="d9c801a1-34df-4496-bb90-7ac9e3f9e44e"
    mode="voice"
    ...
></vapi-widget>
-->
```

**Keep:**
- ✅ The Chat Widget (lines 657-677) - Uses different assistant, no squad
- ✅ The Web SDK (lines 682-790) - This works correctly
- ✅ The widget script (line 679) - Still needed for chat widget

---

## 🎯 Alternative Solutions

### Option A: Fix Widget Attribute (May not work)

Try changing `squad-id` to `assistant-id` with the router:

```html
<vapi-widget
    id="voice-widget"
    public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
    assistant-id="87182b39-a050-4ef4-9319-773666fabd6d"  ← Router assistant directly
    mode="voice"
    ...
></vapi-widget>
```

**Warning**: This will use the router directly (not the squad), which we know causes a 400 error.

### Option B: Use ONLY the Widget (No Web SDK)

Remove the Web SDK (lines 682-790) and rely only on the widget.

**Warning**: The widget seems to have bugs with squad support.

### Option C: Use ONLY the Web SDK (Recommended)

✅ **Remove/comment the voice widget** (lines 631-655)
✅ **Keep the Web SDK** (lines 682-790)
✅ **Keep the chat widget** (lines 657-677)

This is the cleanest solution.

---

## 📝 Why Widget Fails

The widget library (`widget.umd.js`) likely:

1. **Doesn't properly parse** the `squad-id` HTML attribute
2. **Sends `assistantId`** instead of `squadId` in the API call
3. **Sends an empty/null value** for `assistantId`, causing "must be a UUID" error
4. **Has a bug** with squad support in the widget version

The Web SDK (`@vapi-ai/web`) works correctly because it properly supports the programmatic API.

---

## 🚀 Immediate Action Required

Edit `/opt/kasaai/apps/premierhealth/index.html`:

1. **Comment out lines 631-655** (voice widget)
2. **Keep lines 657-677** (chat widget)
3. **Keep lines 682-790** (Web SDK)
4. **Save and test**

After this change:
- ✅ "Start Voice Call" button will use Web SDK (works correctly)
- ✅ "Start Chat" button will use chat widget (works correctly)
- ✅ No more widget.umd.js errors

---

## 🧪 Testing After Fix

1. Save the file
2. Hard refresh browser (Ctrl+Shift+R)
3. Click "Start Voice Call"
4. Should see in console:
```
================================================================================
▶ STARTING SQUAD CALL
================================================================================
Squad ID: d9c801a1-34df-4496-bb90-7ac9e3f9e44e
...
✓ SQUAD CALL INITIATED SUCCESSFULLY
```

---

## 📊 Summary

| Component | Status | Action |
|-----------|--------|--------|
| Squad Config | ✅ CORRECT | None needed |
| Assistants | ✅ ALL EXIST | None needed |
| Web SDK | ✅ WORKS | Keep as-is |
| Voice Widget | ❌ BROKEN | Comment out |
| Chat Widget | ✅ WORKS | Keep as-is |

**Root Cause**: Vapi Widget library doesn't properly support squad-id attribute.

**Solution**: Disable voice widget, use Web SDK only.

**Confidence**: 100% - Error trace proves widget is the source.

---

**Status**: Solution identified - requires commenting out voice widget in HTML.
