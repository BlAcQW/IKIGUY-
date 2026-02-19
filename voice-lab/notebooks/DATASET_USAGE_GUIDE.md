# Twi Voice Dataset Usage Guide

## Available Datasets Summary

### 1. **Common Voice 17.0 Twi** ✅
- **Source**: Mozilla Foundation
- **Access**: https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0
- **Language Code**: `tw`
- **Format**: MP3 audio with transcriptions
- **Features**: Age, gender, accent metadata
- **Size**: Variable (streaming available)

**How to use:**
```python
from datasets import load_dataset

# Full download
dataset = load_dataset(
    "mozilla-foundation/common_voice_17_0",
    "tw",
    token=True  # Requires HF login
)

# Streaming (no download)
dataset = load_dataset(
    "mozilla-foundation/common_voice_17_0",
    "tw",
    streaming=True,
    token=True
)
```

### 2. **MichSetHowusu Datasets** ✅
- **Source**: HuggingFace user with 971 Twi datasets
- **Format**: Arrow files with embedded audio
- **Datasets**:
  - `twi_multispeaker_audio_transcribed` (28K samples)
  - `akuapem_multispeaker_audio_transcribed` (25K samples)
  - `fante_multispeaker_audio_transcribed` (10K samples)
  - `twi-emotions-corpus` (430K text samples)

**How to use:**
```python
from datasets import load_dataset

# Load from HuggingFace
dataset = load_dataset(
    "michsethowusu/twi_multispeaker_audio_transcribed",
    token=True
)

# Load from local Arrow files (if in Google Drive)
from datasets import load_from_disk
dataset = load_from_disk("path/to/arrow/files")
```

### 3. **BibleTTS** ✅
- **Source**: OpenSLR
- **Location**: `voice-lab-data/raw/bibletts/`
- **Folders**: `akuapem-twi/`, `asante-twi/`
- **Format**: FLAC files at 48kHz
- **Count**: 46,841 audio files total
- **Quality**: Studio quality recordings

### 4. **Financial Inclusion** ✅
- **Source**: Ashesi University
- **Location**: `voice-lab-data/raw/financial_inclusion/`
- **Structure**: `{language}_{split}/fisd-{language}-{split}p/audios/`
- **Format**: OGG files
- **Languages**: Akuapem Twi, Asante Twi, Fante

### 5. **African Whisper** ❌
- **Type**: Framework/Model repository (not a dataset)
- **Content**: Code files only, no audio data
- **Use**: ASR model training framework

## Dataset Status in Google Drive

| Dataset | Audio Files | Text Files | Format | Ready |
|---------|------------|------------|--------|-------|
| BibleTTS Akuapem | 25,212 | ✓ | FLAC | ✅ |
| BibleTTS Asante | 21,629 | ✓ | FLAC | ✅ |
| Financial Inclusion | Thousands | ✓ | OGG | ✅ |
| MichSetHowusu | Arrow format | ✓ | Arrow | ⚠️ |
| Common Voice | Streamable | ✓ | MP3 | ✅ |
| African Whisper | 0 | 0 | N/A | ❌ |

## Processing Pipeline

### Step 1: Authentication
```bash
# Login to HuggingFace for Common Voice and MichSetHowusu
huggingface-cli login

# Mount Google Drive in Colab
from google.colab import drive
drive.mount('/content/drive')
```

### Step 2: Load Datasets in Notebook

The updated `002_phase1_data_processing_enhanced.ipynb` now includes:
- **Cell 15**: BibleTTS processing (corrected paths with hyphens)
- **Cell 16**: Financial Inclusion processing (corrected nested structure)
- **Cell 17**: Common Voice streaming
- **Cell 18**: MichSetHowusu Arrow files

### Step 3: Run Processing
```python
# In Google Colab
!python 002_phase1_data_processing_enhanced.ipynb
```

## Common Issues & Solutions

### Issue 1: Common Voice Authentication
**Error**: "Requires authentication"
**Solution**: 
1. Run `huggingface-cli login`
2. Accept terms at https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0

### Issue 2: MichSetHowusu Arrow Files
**Error**: "Cannot load Arrow files"
**Solution**: Load directly from HuggingFace or use `load_from_disk()` for local files

### Issue 3: Financial Inclusion Paths
**Error**: "Path not found"
**Solution**: Use nested structure: `financial_inclusion/fante_10/fisd-fanti-10p/audios/`

### Issue 4: BibleTTS Folder Names
**Error**: "bibletts/asante_twi not found"
**Solution**: Use hyphens: `bibletts/asante-twi`

## Recommended Processing Order

1. **BibleTTS** - Highest quality, already extracted
2. **Financial Inclusion** - Good quality, domain-specific
3. **Common Voice** - Community quality, diverse speakers
4. **MichSetHowusu** - Large volume, requires HF access

## Next Steps

1. Run `001_phase1_data_acquisition.ipynb` to download datasets
2. Run `002_phase1_data_processing_enhanced.ipynb` to process all data
3. Check outputs in `voice-lab-data/processed/`
4. Proceed to Phase 2: ASR Training