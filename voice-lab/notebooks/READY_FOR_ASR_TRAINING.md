# ASR Training Data Ready!

## Available Data for Training

### 1. Financial Inclusion Audio (Processed)
- **Location**: `G:\My Drive\voice-lab-data\processed\audio_data\`
- **Files**: 
  - `audio_manifest_train.csv` - 25,853 audio files
  - `audio_manifest_test.csv` - 2,956 audio files
- **Languages**: Fante (currently processed)
- **Note**: Audio paths available, transcriptions in original metadata

### 2. MichSet Audio (Metadata Ready)
- **Location**: `G:\My Drive\voice-lab-data\processed\michset_audio_manifests\`
- **Datasets**:
  - Twi: 31,250 samples (28,063 train, 3,187 test)
  - Akuapem: 28,564 samples
  - Fante: 28,593 samples
- **Total**: ~88,407 samples
- **Note**: Arrow format, needs HuggingFace datasets library for extraction

### 3. Bible TTS (Processing)
- **Location**: `G:\My Drive\voice-lab-data\raw\bibletts\`
- **Content**: ~93,682 FLAC files with .txt transcripts
- **Status**: Background processing initiated

### 4. Text Data (Fully Processed)
- **Location**: `G:\My Drive\voice-lab-data\processed\text_data\`
- **Content**: 4M+ English-Twi sentence pairs
- **Can be used for**: Synthetic TTS → ASR training

## How to Use with 004_phase2_asr_development.ipynb

### Option 1: Use Financial Inclusion Audio
```python
# In the notebook, modify the data loading section:
import pandas as pd
from pathlib import Path

BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')
audio_manifest = pd.read_csv(BASE_DIR / 'processed/audio_data/audio_manifest_train.csv')

# Load transcriptions from original metadata
fi_metadata = pd.read_csv(BASE_DIR / 'raw/financial_inclusion/fante_90/fisd-fanti-90p/data.csv')

# Match audio files with transcriptions
# ... matching logic ...
```

### Option 2: Use MichSet with HuggingFace
```python
from datasets import load_from_disk

# Load MichSet Arrow datasets
dataset_path = '/content/drive/MyDrive/voice-lab-data/raw/michsethowusu/twi_multispeaker_audio_transcribed'
dataset = load_from_disk(dataset_path)

# This gives you 28,063 training samples with audio_path and transcription
train_data = dataset['train']
test_data = dataset['test']
```

### Option 3: Wait for Bible TTS (Best Quality)
- 93,682 FLAC files with perfect text alignment
- Professional recordings
- Best for high-quality ASR training

## Quick Start for ASR Training

1. **Mount Drive in Colab**:
```python
from google.colab import drive
drive.mount('/content/drive')
```

2. **Install Dependencies**:
```python
!pip install datasets transformers faster-whisper
!pip install librosa soundfile jiwer
```

3. **Load MichSet Data** (Easiest):
```python
from datasets import load_from_disk

BASE = '/content/drive/MyDrive/voice-lab-data/raw/michsethowusu'
twi_dataset = load_from_disk(f'{BASE}/twi_multispeaker_audio_transcribed')

print(f"Train: {len(twi_dataset['train'])} samples")
print(f"Test: {len(twi_dataset['test'])} samples")
```

4. **Start Training**:
- Use the Whisper fine-tuning section in the notebook
- Or use Faster-Whisper for quick inference

## Summary

| Dataset | Samples | Status | Transcriptions |
|---------|---------|--------|----------------|
| Financial Inclusion | 28,809 | ✅ Audio paths ready | Need matching |
| MichSet | 88,407 | ✅ Metadata ready | ✅ Available |
| Bible TTS | ~93,682 | 🔄 Processing | ✅ Available |
| Text Only | 4M+ | ✅ Ready | ✅ Available |

**Recommendation**: Start with MichSet data using HuggingFace datasets - it's the easiest to use and has both audio paths and transcriptions ready!