# Voice Lab Dataset Status Report
**Date**: 2024-12-22
**Location**: G:\My Drive\voice-lab-data\raw

## ✅ EXISTING DATASETS

### 1. BibleTTS ✅
- **Location**: `/bibletts/`
- **Content**: 
  - akuapem-twi (directory with audio files)
  - asante-twi (directory with audio files)
  - Archive files: akuapem_twi.tar.gz, asante_twi.tar.gz
- **Status**: Complete, ready for processing

### 2. Financial Inclusion ✅
- **Location**: `/financial_inclusion/`
- **Content**: 
  - All 6 subdatasets present (fante_10/90, asante_twi_10/90, akuapem_twi_10/90)
  - Each contains audio files in `fisd-*/audios/` directories
  - CSV files named `data.csv` (not transcript.csv)
- **Status**: Complete, needs CSV path correction in processing

### 3. Common Voice ⚠️
- **Location**: `/common_voice/`
- **Content**: 
  - Archive: cv-corpus-22.0-delta-2025-06-20-tw.tar.gz (exists)
  - Extracted directory: cv-corpus-22.0-delta-2025-06-20-tw
- **Status**: Archive present but needs proper extraction
- **Action Required**: Extract train/test/validation splits

### 4. MichSetHowusu ✅
- **Location**: `/michsethowusu/`
- **Content**:
  - twi_multispeaker_audio_transcribed ✅
  - akuapem_multispeaker_audio_transcribed ✅
  - fante_multispeaker_audio_transcribed ✅
  - ga_multispeaker_audio_transcribed ✅
  - Missing: english-twi_sentence-pairs (due to dataset format issues)
- **Status**: Audio datasets present, text pairs need alternative download

### 5. JW300 ⚠️
- **Location**: `/jw300/`
- **Content**:
  - opus-2020-01-08.zip (273 MB archive)
  - Needs extraction
- **Status**: Archive present, needs extraction
- **Alternative**: Can use GhanaNLP preprocessed version

### 6. African Whisper ✅
- **Location**: `/african_whisper/`
- **Content**: Full repository cloned with code and models
- **Status**: Complete

### 7. AfriSpeech ❌
- **Location**: `/afrispeech/`
- **Content**: Empty (only desktop.ini)
- **Status**: Needs alternative download method
- **Issue**: Dataset uses old HuggingFace script format

### 8. Alternative Sources 🆕
- **Location**: `/alternative_sources/`
- **Content**: To be populated with:
  - GhanaNLP preprocessed JW300
  - Bible translations
  - Combined corpus

## 📊 SUMMARY

| Dataset | Status | Action Required |
|---------|--------|-----------------|
| BibleTTS | ✅ Ready | None |
| Financial Inclusion | ✅ Ready | Update CSV filename in code |
| Common Voice | ⚠️ Archive exists | Extract splits |
| MichSetHowusu | ✅ Partial | Download text pairs separately |
| JW300 | ⚠️ Archive exists | Extract or use alternatives |
| African Whisper | ✅ Ready | None |
| AfriSpeech | ❌ Missing | Use alternative sources |
| Translation Models | 🆕 New | Generate with notebook |
| OPUS Corpora | 🆕 New | Use alternative downloads |

## 🎯 NEXT STEPS

1. **Extract Archives**:
   ```bash
   # Extract JW300
   unzip opus-2020-01-08.zip
   
   # Extract Common Voice
   tar -xzf cv-corpus-22.0-delta-2025-06-20-tw.tar.gz
   ```

2. **Download Alternatives**:
   - GhanaNLP JW300 preprocessed data
   - Bible corpus translations
   - MichSetHowusu text pairs via direct API

3. **Create Combined Corpus**:
   - Merge all text sources
   - Remove duplicates
   - Create train/val/test splits

4. **Run Phase 2 Processing**:
   - Use `002_phase1_data_processing_enhanced.ipynb`
   - Process audio to 16kHz mono
   - Align text with audio
   - Create manifest files

## 📈 ESTIMATED DATA VOLUME

- **Audio**: ~50-100 hours (BibleTTS + Financial Inclusion + MichSetHowusu)
- **Text**: ~500K+ sentences (after extraction and alternatives)
- **Parallel Pairs**: ~100K+ (JW300 + translations)

## ✅ READY FOR PHASE 2

With the existing datasets and planned alternatives, you have sufficient data to:
1. Train ASR model (50+ hours audio)
2. Train TTS model (high-quality BibleTTS)
3. Fine-tune translation models (parallel texts)
4. Create comprehensive Twi voice technology