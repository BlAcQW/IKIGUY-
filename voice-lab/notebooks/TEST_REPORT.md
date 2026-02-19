# Voice Lab Data Sources Test Report

## Test Date: 2024-12-22
## HF Token: `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`

---

## 1. Helsinki-NLP Translation Model ✅ WORKING

**Model**: `Helsinki-NLP/opus-mt-en-tw`

### Test Results:
- ✅ Model loads successfully with HF token
- ✅ Translation functionality works
- ✅ Sample translation: "Hello, how are you?" → "Wiɛ, ɔkwan bɛn so na wote nka?"

### Usage:
```python
from transformers import pipeline
translator = pipeline('translation', model='Helsinki-NLP/opus-mt-en-tw', token=HF_TOKEN)
result = translator("Hello")
```

---

## 2. OPUS Corpus Extraction ⚠️ TEMPORARY ISSUE

### Test Results:
- ⚠️ OPUS server returning 503 (Service Temporarily Unavailable)
- This is a server-side issue, not a code problem
- Alternative: Use OpusTools Python package when server is back

### Affected URLs:
- JW300: `https://opus.nlpl.eu/download.php?f=JW300/v1/moses/en-tw.txt.zip`
- Monolingual: `https://opus.nlpl.eu/download.php?f=mono/tw.txt.gz`

### Recommendation:
Try again later or use cached versions if available.

---

## 3. Common Voice Dataset ⚠️ REQUIRES UPDATE

### Test Results:
- ❌ Dataset uses old script format no longer supported by HuggingFace
- Error: "Dataset scripts are no longer supported"

### Solution:
Common Voice needs to be accessed differently:
```python
# Use the new format (when available)
from datasets import load_dataset
dataset = load_dataset("mozilla-foundation/common_voice", "17.0", language="tw", token=HF_TOKEN)
```

### Alternative:
Download directly from Mozilla Common Voice website

---

## 4. MichSetHowusu Datasets ✅ WORKING

### Test Results:
- ✅ `michsethowusu/twi-emotions-corpus` - ACCESSIBLE
- ✅ `michsethowusu/english-twi_sentence-pairs` - ACCESSIBLE

### Working Datasets:
- Twi emotions corpus (430K+ samples)
- English-Twi sentence pairs
- Translation pairs with other African languages

---

## 5. AfriSpeech-200 ⚠️ REQUIRES UPDATE

### Test Results:
- ❌ Dataset uses old script format
- Error: "Dataset scripts are no longer supported"

### Solution:
Contact dataset maintainer for updated format or use alternative access method.

---

## Summary

### ✅ Working Sources (3/5):
1. Helsinki-NLP Translation Model
2. MichSetHowusu Twi Emotions Corpus
3. MichSetHowusu English-Twi Pairs

### ⚠️ Temporary Issues (1/5):
1. OPUS Corpus (server temporarily down)

### ❌ Needs Update (2/5):
1. Common Voice (old script format)
2. AfriSpeech-200 (old script format)

---

## Recommendations

1. **For Translation**: Helsinki-NLP model is fully functional - use it for data augmentation
2. **For Text Data**: MichSetHowusu datasets provide 400K+ text samples - prioritize these
3. **For OPUS**: Wait for server to be back online or use OpusTools with retry logic
4. **For Common Voice & AfriSpeech**: Check for updated versions or use alternative sources

---

## Next Steps

1. Focus on working sources (Helsinki-NLP, MichSetHowusu)
2. Implement retry logic for OPUS downloads
3. Monitor HuggingFace for dataset format updates
4. Consider downloading Common Voice directly from Mozilla

---

## Token Configuration

Your HF token is working correctly. Make sure to:
1. Keep it secure (don't commit to git)
2. Add to Google Colab secrets as `HF_TOKEN`
3. Use in all HuggingFace API calls