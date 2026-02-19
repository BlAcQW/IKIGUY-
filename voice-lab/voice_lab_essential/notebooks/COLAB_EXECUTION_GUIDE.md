# 📚 Google Colab Execution Guide for Twi/Akan Voice Technology Project

## 🚀 Quick Start - Execution Order

Run the notebooks in this **exact order** for the complete pipeline:

### Phase 1: Data Preparation
1. **`000_enhanced_twi_processor.py`** - Upload this first (core module - REQUIRED!)
2. **`001_phase1_data_acquisition.ipynb`** - Download datasets
3. **`002_phase1_data_processing_enhanced.ipynb`** - Process data with enhanced features
4. **`003_use_enhanced_processor.ipynb`** - Test enhanced processing

### Phase 2: Model Development  
5. **`004_phase2_asr_development.ipynb`** - Train ASR models (requires GPU)

---

## 📋 Detailed Instructions for Each Notebook

### 🔧 **Step 0: Upload Core Module**
**File:** `000_enhanced_twi_processor.py`

```python
# In Colab, first upload this file:
from google.colab import files
uploaded = files.upload()  # Select 000_enhanced_twi_processor.py

# IMPORTANT: After uploading, rename to remove the number prefix:
!mv 000_enhanced_twi_processor.py enhanced_twi_processor.py

# Or clone from repo and rename:
!git clone https://github.com/your-repo/voice-lab.git
!cp voice-lab/notebooks/000_enhanced_twi_processor.py enhanced_twi_processor.py
```

---

### 📥 **Step 1: Data Acquisition**
**File:** `001_phase1_data_acquisition.ipynb`
**Runtime:** CPU is sufficient
**Duration:** 15-30 minutes

**What it does:**
- Downloads BibleTTS datasets (Asante & Akuapem Twi)
- Downloads Financial Inclusion dataset
- Sets up directory structure
- Validates downloads

**Before running:**
```python
# Mount Google Drive for persistent storage
from google.colab import drive
drive.mount('/content/drive')

# Create base directory
!mkdir -p /content/drive/MyDrive/voice-lab-data
```

**Expected output:**
- Downloaded ~2-5GB of audio data
- Created folder structure in Drive
- Metadata CSV files generated

---

### 🔄 **Step 2: Enhanced Data Processing**
**File:** `002_phase1_data_processing_enhanced.ipynb`
**Runtime:** CPU (GPU optional for faster processing)
**Duration:** 30-60 minutes

**What it does:**
- Audio normalization (16kHz, mono)
- Enhanced text processing:
  - Numbers → Twi words (e.g., 25 → "aduonu ne nnum")
  - Currency conversion (GH₵500 → "ahanum Ghana sidi")
  - Date/time processing (Monday → "Dwowda")
  - Phoneme generation (IPA transcription)
  - Abbreviation expansion (Dr. → "Dokota")
- Creates train/val/test splits
- Generates augmented data

**Required packages:**
```python
!pip install librosa soundfile webrtcvad pydub
!pip install pandas numpy tqdm
!pip install audiomentations
```

**Key settings to verify:**
```python
# Check dialect setting
text_processor = EnhancedTwiTextProcessor(dialect='asante')  # or 'akuapem', 'fante'

# Verify paths
BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')
```

**Expected output:**
- Processed audio in `processed/` folder
- Phoneme files in `phonemes/` folder
- Split CSVs in `splits/` folder
- Enhanced metadata with phoneme mappings

---

### 🧪 **Step 3: Test Enhanced Features**
**File:** `003_use_enhanced_processor.ipynb`
**Runtime:** CPU
**Duration:** 2-5 minutes

**What it does:**
- Demonstrates all enhanced processing features
- Tests number, date, currency conversion
- Shows phoneme generation
- Validates dialect handling

**Test examples included:**
```python
# Number conversion
"The price is GH₵250" → "The price is ahannu ne aduonum Ghana sidi"

# Date/time processing
"Monday at 10:30 AM" → "Dwowda at anɔpa dɔn edu ne simma aduasa"

# Abbreviation expansion
"Dr. Mensah from KNUST" → "Dokota Mensah from Kwame Nkrumah Nyansapɔ ne Mfiridwuma Suapɔn"

# Phoneme generation
"Akwaaba" → "akʷaaba" (IPA)
```

---

### 🎯 **Step 4: ASR Model Development**
**File:** `004_phase2_asr_development.ipynb`
**Runtime:** **GPU REQUIRED** (T4 or better)
**Duration:** 2-6 hours

**Enable GPU:**
1. Runtime → Change runtime type
2. Hardware accelerator → GPU (T4/V100/A100)
3. Save

**What it does:**
- Builds Wav2Vec2 ASR model
- Fine-tunes on Twi data
- Implements CTC loss training
- Evaluates with WER/CER metrics

**GPU memory management:**
```python
# Clear cache periodically
import torch
torch.cuda.empty_cache()

# Use smaller batch sizes if OOM
batch_size = 8  # Reduce if needed
```

**Model checkpoints:**
```python
# Save to Drive to prevent loss
checkpoint_dir = '/content/drive/MyDrive/voice-lab-checkpoints'
```

---

## 💡 Tips for Colab Usage

### 1. **Prevent Timeout**
```python
# Keep session alive
function ClickConnect(){
    console.log("Keeping alive..."); 
    document.querySelector("colab-toolbar-button").click()
}
setInterval(ClickConnect, 60000)
```

### 2. **Handle Large Files**
```python
# Use chunked processing for large datasets
chunk_size = 1000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process(chunk)
```

### 3. **Monitor Resources**
```python
# Check GPU usage
!nvidia-smi

# Check RAM
!free -h

# Check disk space
!df -h
```

### 4. **Save Outputs to Drive**
```python
# Auto-save important results
import shutil
shutil.copy('results.csv', '/content/drive/MyDrive/voice-lab-results/')
```

---

## 📊 Expected Results After Full Pipeline

After running all notebooks, you should have:

1. **Data Assets:**
   - 10,000+ processed audio files
   - Corresponding text transcriptions
   - IPA phoneme mappings
   - Train/val/test splits (70/15/15)

2. **Enhanced Features:**
   - Twi number system (0-1,000,000+)
   - Currency in 4 formats (GH₵, $, €, £)
   - Date/time in Twi
   - Phonetic transcriptions
   - Multi-dialect support

3. **Model Outputs:**
   - Trained Wav2Vec2 model
   - Performance metrics (WER < 30% target)
   - Model checkpoints
   - Inference-ready model

4. **Directory Structure:**
```
/content/drive/MyDrive/voice-lab-data/
├── raw/                 # Original datasets
├── processed/           # Normalized audio
├── phonemes/           # IPA transcriptions
├── splits/             # Train/val/test CSVs
├── augmented/          # Augmented samples
├── metadata/           # Processing records
└── checkpoints/        # Model saves
```

---

## 🔥 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Out of memory** | Reduce batch size, clear cache, use CPU for processing |
| **Module not found** | Upload `enhanced_twi_processor.py` first |
| **Drive not mounted** | Run `drive.mount('/content/drive')` |
| **Session timeout** | Use keep-alive script, save checkpoints frequently |
| **Slow processing** | Enable GPU, use batch processing |
| **Audio format error** | Install `ffmpeg`: `!apt install ffmpeg` |

---

## 🎯 Quick Test Commands

```python
# Test enhanced processor is working
from enhanced_twi_processor import EnhancedTwiTextProcessor
processor = EnhancedTwiTextProcessor()
result = processor.process_text("I have GH₵100 on Monday")
print(result['processed'])
# Should output: "I have ɔha Ghana sidi on Dwowda"

# Check GPU availability
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# Verify data paths
import os
data_path = '/content/drive/MyDrive/voice-lab-data'
print(f"Data exists: {os.path.exists(data_path)}")
print(f"Contents: {os.listdir(data_path) if os.path.exists(data_path) else 'Not found'}")
```

---

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Ensure all prerequisites are installed
3. Verify file paths and permissions
4. Check Colab resource limits
5. Review error messages carefully

**Ready to build Twi/Akan voice technology! 🚀**