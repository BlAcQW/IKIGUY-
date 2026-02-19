# Complete Voice Lab Data Inventory

## Summary of ALL Available Twi Data

### ✅ PROCESSED DATA

#### 1. **MichSetHowusu English-Twi Pairs** (PROCESSED)
- **Location**: `raw/michsethowusu/`
- **Content**: 4,037,439 sentence pairs
- **Format**: Parquet file (287 MB)
- **Status**: ✅ Fully processed into train/val/test splits
- **Additional**: 
  - Arrow format audio data in subdirectories
  - Multispeaker recordings for Twi, Akuapem, Fante

#### 2. **Financial Inclusion Audio** (PROCESSED)
- **Location**: `raw/financial_inclusion/`
- **Dialects**:
  - Akuapem Twi: 28,564 files (train: 25,636, test: 2,928)
  - Asante Twi: 31,251 files (train: 28,064, test: 3,187)
  - Fante: 28,809 files (train: 25,853, test: 2,956)
- **Total**: ~88,624 audio files with transcripts
- **Format**: OGG audio + CSV metadata
- **Status**: ✅ Manifests created, needs transcript alignment fix

#### 3. **Bible TTS** (IDENTIFIED, NOT FULLY PROCESSED)
- **Location**: `raw/bibletts/`
- **Content**:
  - Akuapem Twi: ~50,424 FLAC files with text
  - Asante Twi: ~43,258 FLAC files with text
- **Total**: ~93,682 audio-text pairs
- **Format**: FLAC audio + TXT transcripts
- **Status**: ⚠️ Structure identified, needs full processing

### 🔄 UNPROCESSED/PARTIALLY PROCESSED DATA

#### 4. **Common Voice Twi** (EXTRACTED, NOT PROCESSED)
- **Location**: `raw/common_voice/cv-corpus-22.0-delta-2025-06-20-tw/`
- **Content**: Twi speech dataset
- **Files**: clips folder, validated_sentences.tsv
- **Status**: 📦 Extracted but not processed

#### 5. **JW300 Parallel Corpus** (NOT EXTRACTED)
- **Location**: `raw/jw300/`
- **Content**: opus-2020-01-08.zip (260 MB)
- **Status**: 📦 Needs extraction

#### 6. **African Whisper** (MINIMAL CONTENT)
- **Location**: `raw/african_whisper/`
- **Content**: Documentation and test files
- **Status**: ℹ️ Mostly documentation

#### 7. **MichSetHowusu Audio (Arrow Format)**
- **Location**: `raw/michsethowusu/*/`
- **Subdirectories**:
  - `twi_multispeaker_audio_transcribed/`
  - `akuapem_multispeaker_audio_transcribed/`
  - `fante_multispeaker_audio_transcribed/`
- **Format**: Arrow files (HuggingFace dataset format)
- **Status**: 🔄 Needs conversion from Arrow to usable format

### 📊 TOTAL DATA STATISTICS

| Category | Count | Status |
|----------|--------|--------|
| **Text Pairs** | 4,037,439 | ✅ Processed |
| **Financial Inclusion Audio** | ~88,624 | ✅ Processed |
| **Bible TTS Audio** | ~93,682 | ⚠️ Identified |
| **Common Voice** | Unknown | 📦 Extracted |
| **JW300** | Unknown | 📦 Not extracted |
| **MichSetHowusu Arrow** | Unknown | 🔄 Needs conversion |

### 🎯 IMMEDIATE ACTIONS NEEDED

1. **Process Bible TTS fully** - Create complete manifests for 93K files
2. **Process Common Voice Twi** - Extract and organize clips
3. **Extract JW300** - Unzip and process parallel text
4. **Convert Arrow datasets** - Convert MichSetHowusu audio from Arrow format
5. **Fix FI transcript alignment** - Match audio filenames with metadata

### 💾 STORAGE SUMMARY

- **Raw Data**: ~31 GB
- **Processed Data**: ~5-10 GB
- **Total Google Drive Usage**: ~36-41 GB

### 🚀 READY FOR TRAINING

With current processed data, you can train:
1. **Translation Model**: 4M+ sentence pairs (READY)
2. **ASR Model**: 88K+ audio files (READY with fixes)
3. **TTS Model**: Text + limited audio (PARTIAL)
4. **Language Model**: 973K unique sentences (READY)

### 📝 NOTES

- All processed data in: `G:\My Drive\voice-lab-data\processed\`
- Training manifests in: `processed\training_manifests\`
- Normalized text in: `processed\text_data_normalized\`
- The EnhancedTwiTextProcessor is available for text normalization