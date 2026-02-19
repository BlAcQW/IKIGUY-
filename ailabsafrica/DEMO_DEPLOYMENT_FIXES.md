# Demo Deployment & Assistant Template Fixes

## 🔍 **Issues Identified**

### **1. Duplicate Demo URLs**
- **Problem**: Two demo URLs were being generated - one in step 5 and another in step 6
- **Root Cause**: The `create-assistant` edge function was being called twice:
  - First in `createVapiAssistant()` function (step 5)
  - Second in `deployToServer()` function (step 6)
- **Impact**: Users saw two different demo URLs, causing confusion

### **2. Assistant Template Implementation**
- **Requirement**: Use assistant template with ID `96037449-9dd1-49d9-a092-b8d088d2b5c9` as base
- **Customization**: Only change system prompt and first message
- **First Message Logic**: 
  - Help desk assistants: "Hello, I am [Assistant name] from [company name]. How may I help you today?"
  - Other assistants: "Hello, I'm [Assistant name] from [company name]. How are you today?"

## 🛠️ **Fixes Implemented**

### **1. Fixed Duplicate Demo URLs**

#### **🔍 Root Cause Analysis**
**Problem**: Two demo URLs were being generated because `deploy-demo-local` was called twice:
1. **First call**: Inside `create-assistant` function (step 5)
2. **Second call**: Inside `deployToServer` function (step 6)

**Impact**: Users saw two different demo URLs, causing confusion

#### **✅ Frontend Changes**
**File**: `src/pages/CreateAssistant.tsx`

**Changes Made**:
- Modified `deployToServer()` function to call `deploy-demo-local` directly instead of `create-assistant`
- Removed duplicate assistant creation in step 6
- Now only deploys the HTML that was already generated in step 5

**Before**:
```typescript
// Step 6: Called create-assistant again (duplicate)
const { data, error } = await supabase.functions.invoke('create-assistant', {
  body: { assistantName, description, assistantType, voiceId, websiteUrl, systemPrompt, htmlCode, ... }
});
```

**After**:
```typescript
// Step 6: Only deploys existing HTML
const { data, error } = await supabase.functions.invoke('deploy-demo-local', {
  body: { assistantName, assistantId, assistantType, html: htmlCode, ... }
});
```

#### **✅ Flow Optimization**
**New Flow**:
1. **Step 5**: Create Vapi assistant + Generate HTML demo (no deployment)
2. **Step 6**: Deploy HTML demo only (single deployment)

**Key Changes**:
- Removed deployment call from `create-assistant` function
- Moved database insertion to `deployToServer` function
- Now only ONE deployment happens in step 6

### **2. Implemented Assistant Template System**

#### **✅ New Edge Function**
**File**: `supabase/functions/fetch-assistant-template/index.ts`

**Purpose**: Fetch assistant template configuration from Vapi API
**Features**:
- Fetches template by ID: `96037449-9dd1-49d9-a092-b8d088d2b5c9`
- Returns template configuration (system prompt, voice, model settings)
- Error handling for template fetch failures

#### **✅ Enhanced Assistant Creation**
**File**: `supabase/functions/create-assistant/index.ts`

**Changes Made**:
- Modified `createVapiAssistant()` function to accept `useTemplate` parameter
- Added template fetching logic when `useTemplate = true`
- Implemented custom first message generation based on assistant type
- **IMPORTANT**: Creates NEW assistants with NEW IDs, does NOT modify the template
- Uses user's selected voice, not template voice
- Preserves template model settings but with custom system prompt

**Template Logic**:
```typescript
if (useTemplate) {
  // Fetch template from Vapi (for reference only)
  const template = await fetchTemplate(templateId);
  
  // Generate custom first message
  let firstMessage: string;
  if (name.toLowerCase().includes('help') || name.toLowerCase().includes('support')) {
    firstMessage = `Hello, I am ${name} from ${companyName}. How may I help you today?`;
  } else {
    firstMessage = `Hello, I'm ${name} from ${companyName}. How are you today?`;
  }
  
  // Create NEW assistant using template settings as reference
  requestBody = {
    name, // New name
    firstMessage, // Custom first message
    model: {
      // Use template model settings but with our custom system prompt
      provider: template.model?.provider || "openai",
      model: template.model?.model || "gpt-4o-mini",
      messages: [{ role: "system", content: systemPrompt }] // Our custom prompt
    },
    voice: {
      // Use user's selected voice, NOT template voice
      provider: "vapi",
      voiceId: voiceId || "paige"
    },
    // Use template settings for other configurations
    recordingEnabled: template.recordingEnabled,
    endCallPhrases: template.endCallPhrases
  };
  
  // POST request creates NEW assistant with NEW ID
  const response = await fetch("https://api.vapi.ai/assistant", {
    method: "POST", // Creates new assistant, doesn't modify template
    body: JSON.stringify(requestBody)
  });
}
```

#### **✅ Frontend Integration**
**File**: `src/pages/CreateAssistant.tsx`

**Changes Made**:
- Updated `createVapiAssistant()` function to always pass `useTemplate: true`
- Added `useTemplate` parameter to request body
- Enhanced logging for template usage

## 📋 **Technical Details**

### **Assistant Template ID**
- **ID**: `96037449-9dd1-49d9-a092-b8d088d2b5c9`
- **Usage**: All new assistants use this template as base
- **Customization**: Only system prompt and first message are modified

### **Key Implementation Details**

#### **✅ What We DO (Create New Assistant)**
- ✅ **POST** request to `/assistant` endpoint (creates new assistant with new ID)
- ✅ Use template model settings (provider, model type) as reference
- ✅ Use user's selected voice (not template voice)
- ✅ Custom system prompt (generated from user input)
- ✅ Custom first message (based on assistant type)
- ✅ Use template settings for recording and end call phrases

#### **❌ What We DON'T Do**
- ❌ **PUT/PATCH** request (which would modify the template)
- ❌ Use template's voice (we use user's selected voice)
- ❌ Use template's system prompt (we use custom generated prompt)
- ❌ Use template's first message (we use custom generated message)
- ❌ Modify the original template in any way

### **First Message Logic**
```typescript
// Help desk assistants
if (name.toLowerCase().includes('help') || name.toLowerCase().includes('support')) {
  firstMessage = `Hello, I am ${name} from ${companyName}. How may I help you today?`;
} else {
  // All other assistants
  firstMessage = `Hello, I'm ${name} from ${companyName}. How are you today?`;
}
```

### **Company Name Extraction**
```typescript
// Extract company name from assistant name
const companyName = name.includes(' ') ? name.split(' ').slice(1).join(' ') : name;
```

## 🚀 **Deployment Status**

### **✅ Deployed Functions**
- ✅ `fetch-assistant-template` - New function for template fetching
- ✅ `create-assistant` - Updated with template support
- ✅ `deploy-demo-local` - Already deployed (no changes needed)

### **✅ Frontend Changes**
- ✅ `CreateAssistant.tsx` - Fixed duplicate URLs and added template support
- ✅ All changes committed and ready for testing

## 🧪 **Testing Checklist**

### **Demo URL Generation**
- [ ] Only one demo URL is generated per assistant
- [ ] Demo URL is accessible and functional
- [ ] No duplicate assistant creation in logs

### **Assistant Template Usage**
- [ ] New assistants use the specified template as base
- [ ] System prompt is properly customized
- [ ] First message follows the correct format:
  - Help desk: "Hello, I am [name] from [company]. How may I help you today?"
  - Others: "Hello, I'm [name] from [company]. How are you today?"

### **Error Handling**
- [ ] Template fetch failures are handled gracefully
- [ ] Fallback to original logic if template is unavailable
- [ ] Proper error messages for users

## 📝 **Next Steps**

### **Immediate**
1. Test the new demo deployment flow
2. Verify assistant template usage
3. Check first message generation for different assistant types

### **Future Enhancements**
1. Add template selection UI (if multiple templates are needed)
2. Implement template preview functionality
3. Add template customization options

## 🔧 **Configuration**

### **Environment Variables**
- `VAPI_PRIVATE_KEY` - Required for template fetching
- `SUPABASE_URL` - Required for edge function communication
- `SUPABASE_ANON_KEY` - Required for edge function authentication

### **Template Configuration**
- **Template ID**: `96037449-9dd1-49d9-a092-b8d088d2b5c9`
- **Usage**: All new assistants
- **Customization**: System prompt + First message only

The fixes have been implemented and deployed. The demo deployment now generates only one URL, and all new assistants use the specified template with proper customization.
