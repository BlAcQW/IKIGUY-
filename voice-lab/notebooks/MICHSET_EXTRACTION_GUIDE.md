# MichSet Audio Extraction Guide 🎵

## 🚨 **Problem:** 
Your notebooks have paths to audio files that don't exist yet - they're still in Arrow format and need extraction with torchcodec.

## 🛠️ **Solution:** 
I've created scripts that will install torchcodec and extract real audio files from MichSet datasets.

---

## 🚀 **Quick Fix (Recommended)**

### **Option 1: Run the Complete Batch Script**
```batch
# In Windows Command Prompt:
cd "C:\Projects\kasaai-v2\apps\voice-lab\notebooks"
fix_michset_complete.bat
```

**What it does:**
- ✅ Installs torchcodec and all dependencies
- ✅ Extracts audio from MichSet Arrow datasets  
- ✅ Creates real WAV files at expected paths
- ✅ Updates ASR and TTS data splits
- ✅ Verifies everything works

### **Option 2: Run Python Scripts Manually**
```python
# Install and extract:
python quick_michset_fix.py

# Or full pipeline:
python install_torchcodec_and_extract_michset.py
```

---

## 📊 **What You'll Get**

### **Before (Current State):**
```
❌ Audio files: 0% available (estimated paths only)
❌ ASR training: Will fail (no audio files)
❌ TTS training: Will fail (no audio files)
```

### **After (Post-Extraction):**
```
✅ Audio files: 50-100+ real WAV files extracted
✅ ASR training: Ready with real Twi audio
✅ TTS training: Ready with real Twi audio  
✅ Both notebooks: Full functionality
```

---

## 🎯 **Expected Results**

### **Extraction Output:**
```
🎵 Processing twi_multispeaker_audio_transcribed...
  📊 Total samples: 28,063, Processing: 50
  ✅ Extracted: 45 audio files
  📊 Avg duration: 3.2s
  Total audio: 144s

📁 Updated ASR splits with real audio:
  train.csv: 36 samples  
  validation.csv: 4 samples
  test.csv: 5 samples

🎉 SUCCESS! Notebooks ready for real audio training!
```

### **File Structure Created:**
```
G:/My Drive/voice-lab-data/
├── processed/
│   └── michset_audio_extracted/
│       └── twi_multispeaker_audio_transcribed/
│           ├── test_001.wav
│           ├── test_002.wav  
│           ├── ...
│           ├── test_metadata.csv
│           └── metadata.txt
└── splits/
    ├── train.csv (with real audio paths)
    ├── validation.csv (with real audio paths)
    └── test.csv (with real audio paths)
```

---

## 🔧 **Troubleshooting**

### **If torchcodec installation fails:**
```bash
# Try conda:
conda install -c conda-forge torchcodec

# Or specific pip version:
pip install --upgrade torch
pip install torchcodec

# Or check environment:
python -c "import torch; print(torch.__version__)"
```

### **If MichSet datasets aren't found:**
```
Expected location: G:/My Drive/voice-lab-data/raw/michsethowusu/
```
Make sure the MichSet datasets were downloaded properly in Phase 1.

### **If extraction fails:**
- Check available disk space (needs ~500MB)
- Verify Google Drive is mounted/accessible
- Try with smaller sample size in script

---

## 🎉 **Success Verification**

### **Test that it worked:**
```python
import pandas as pd
from pathlib import Path

# Check ASR splits
train_df = pd.read_csv("G:/My Drive/voice-lab-data/splits/train.csv")
print(f"Train samples: {len(train_df)}")

# Check first audio file exists
first_audio = Path(train_df.iloc[0]['audio'])
print(f"First audio exists: {first_audio.exists()}")
```

### **If successful, you should see:**
```
Train samples: 36
First audio exists: True
```

---

## 🚀 **Next Steps**

### **Once extraction completes:**
1. **✅ ASR Training:** Open `004_phase2_asr_development.ipynb`
   - Data loading will now find real audio files
   - Training pipeline will work with actual Twi speech
   
2. **✅ TTS Training:** Open `005_phase3_tts_development.ipynb`  
   - TTS datasets will have real audio-text pairs
   - Voice synthesis training ready

3. **📈 Scale Up:** For production training:
   - Increase sample limits in extraction scripts
   - Wait for Bible TTS completion (~93k samples)
   - Run full extraction pipeline

---

## ⚡ **Quick Start**

**Just run this and you're done:**
```batch
fix_michset_complete.bat
```

**Then test your notebooks - they should now work with real audio files!** 🎊