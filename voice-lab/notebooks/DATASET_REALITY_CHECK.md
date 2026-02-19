# Dataset Reality Check - What Actually Has Audio Data

## Summary of Findings

After exploring the datasets in Google Drive, here's what actually contains audio data:

### ✅ WORKING DATASETS WITH AUDIO

#### 1. **BibleTTS** ✅✅✅ BEST QUALITY
- **Location**: `voice-lab-data/raw/bibletts/`
- **Audio files**: 46,841 FLAC files (25,212 Akuapem + 21,629 Asante)
- **Format**: High-quality FLAC at 48kHz
- **Status**: READY TO USE
- **Folders**: `akuapem-twi/` and `asante-twi/` (with hyphens!)

#### 2. **Financial Inclusion** ✅✅ GOOD
- **Location**: `voice-lab-data/raw/financial_inclusion/`
- **Audio files**: Thousands of OGG files
- **Structure**: Nested folders like `fante_10/fisd-fanti-10p/audios/`
- **Status**: READY TO USE (paths updated in notebook)

#### 3. **MichSetHowusu** ⚠️ NEEDS PROCESSING
- **Location**: `voice-lab-data/raw/michsethowusu/`
- **Format**: Apache Arrow files (not raw audio)
- **Content**: Audio embedded in Arrow format
- **Status**: Requires HuggingFace datasets library to extract

### ❌ NO AUDIO DATA

#### 4. **Common Voice** ❌ METADATA ONLY
- **Location**: `voice-lab-data/raw/common_voice/`
- **Problem**: Downloaded version has 0 MP3 files!
- **Content**: 49,159 text sentences but NO audio clips
- **Fix**: Need to re-download with audio or use HuggingFace streaming

#### 5. **African Whisper** ❌ CODE ONLY
- **Location**: `voice-lab-data/raw/african_whisper/`
- **Reality**: GitHub repository with Python code
- **Audio files**: ZERO - it's a framework, not a dataset

#### 6. **AfriSpeech-200** ❌ NOT DOWNLOADED
- **Status**: Not found in Google Drive
- **Note**: Would be accented English anyway, not native Twi

#### 7. **JW300** ❌ TEXT ONLY
- **Content**: Parallel text translations
- **Audio files**: ZERO - pure text corpus

#### 8. **Lingua Libre** ❌ NOT FOUND
- **Status**: Not downloaded to Google Drive

## Actual Available Audio Data

| Dataset | Audio Files | Format | Quality | Ready? |
|---------|------------|--------|---------|--------|
| BibleTTS Akuapem | 25,212 | FLAC | Studio | ✅ |
| BibleTTS Asante | 21,629 | FLAC | Studio | ✅ |
| Financial Inclusion | Thousands | OGG | Good | ✅ |
| MichSetHowusu | ~60,000 | Arrow | Good | ⚠️ |
| Common Voice | 0 | - | - | ❌ |
| African Whisper | 0 | - | - | ❌ |
| AfriSpeech-200 | 0 | - | - | ❌ |
| JW300 | 0 | - | - | ❌ |
| Lingua Libre | 0 | - | - | ❌ |

## Recommendations

### For Immediate Processing:
1. **Use BibleTTS** - Already extracted, highest quality
2. **Use Financial Inclusion** - Ready with correct paths
3. **Fix Common Voice** - Either:
   - Download full dataset with audio
   - Use HuggingFace streaming with `audio=True`
4. **Process MichSetHowusu** - Use HuggingFace datasets library

### Skip These:
- African Whisper (no data)
- JW300 (text only)
- AfriSpeech-200 (not relevant)
- Lingua Libre (not found)

## Updated Notebook Fixes

The `002_phase1_data_processing_enhanced.ipynb` has been updated with:
1. ✅ Correct BibleTTS paths (using hyphens: `akuapem-twi`, `asante-twi`)
2. ✅ Correct Financial Inclusion nested structure
3. ✅ Added `raw_dir = DIRS['raw']` definition
4. ✅ Common Voice streaming support
5. ✅ MichSetHowusu Arrow file processing

## Next Steps

1. **Run the notebook** with the datasets that actually have audio
2. **Fix Common Voice** by downloading with audio
3. **Process MichSetHowusu** Arrow files
4. **Ignore** datasets without audio data

## Total Realistic Audio Data:
- **BibleTTS**: ~47,000 files ✅
- **Financial Inclusion**: ~10,000+ files ✅
- **MichSetHowusu**: ~60,000 files (needs extraction) ⚠️
- **Common Voice**: Potentially thousands (needs proper download) ⚠️

**Current ready-to-use**: ~57,000+ audio files
**Potential with fixes**: ~120,000+ audio files