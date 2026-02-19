# 🚀 Quick Start Guide - Enhanced Voice Lab Pipeline

## ⏱ 5-Minute Setup (Google Colab)

### Step 1: Open Google Colab
1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Upload or create a new notebook

### Step 2: Mount Google Drive & Setup
```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Setup working directory
import os
BASE_PATH = '/content/drive/MyDrive/voice-lab-data/'
os.makedirs(BASE_PATH, exist_ok=True)
os.chdir(BASE_PATH)
print(f"Working directory: {os.getcwd()}")

# Install packages
!pip install -q torch torchaudio transformers
!pip install -q librosa soundfile pandas numpy tqdm
!pip install -q TTS speechbrain evaluate matplotlib seaborn tabulate
```

### Step 3: Clone/Upload Notebooks
```python
# If using Git (recommended)
!git clone https://github.com/your-org/kasaai-v2.git
!cp -r kasaai-v2/apps/voice-lab/notebooks/* ./

# OR manually upload the notebook files to your Google Drive
```

### Step 4: Run Data Processing (REQUIRED FIRST)
```python
# This processes all your raw data into optimized formats
%run final/002_enhanced_multi_rate_data_processing.ipynb
```

### Step 5: Train Your First Model
```python
# Example: Train Coqui XTTS for Twi voice synthesis
%run final/010_coqui_training_enhanced.ipynb
```

---

## 📁 File Organization (Google Drive)

Create this structure in your Google Drive:
```
MyDrive/
└── voice-lab-data/
    ├── notebooks/                   # Upload all .ipynb files here
    │   ├── final/
    │   │   ├── 002_enhanced_multi_rate_data_processing.ipynb
    │   │   └── 010_coqui_training_enhanced.ipynb
    │   ├── 015_openvoice_training.ipynb
    │   └── 016_vibe_voice_training.ipynb
    ├── raw/                         # Your raw datasets
    │   ├── bibletts/
    │   ├── financial_inclusion/
    │   └── michsethowusu/
    └── processed/                   # Generated automatically
        ├── processed_audio/
        └── manifests/
```

---

## 🎯 Common Use Cases

### Use Case 1: Train TTS Model for New Language
```python
# 1. Add your language data to raw/ folder
# 2. Update dataset configuration in data processing notebook
datasets_to_scan = [
    {
        "name": "your_language_dataset",
        "type": "bibletts",  # or appropriate type
        "path": "raw/your_language_data"
    }
]

# 3. Run data processing
%run final/002_enhanced_multi_rate_data_processing.ipynb

# 4. Train TTS model
%run final/010_coqui_training_enhanced.ipynb
```

### Use Case 2: Evaluate ASR Models
```python
# 1. Ensure data processing is complete
# 2. Run ASR comparison
%run 010_unified_asr_comparison_enhanced.ipynb

# Results will be in: processed/results/asr_comparison/
```

### Use Case 3: Add New Model Architecture
```python
# 1. Create new training notebook (copy existing one)
!cp 015_openvoice_training.ipynb 017_your_model_training.ipynb

# 2. Modify model loading and training logic
# 3. Update configuration for your model requirements
```

---

## ⚡ Platform-Specific Quick Starts

### Kaggle
```python
# Setup for Kaggle
import os
from pathlib import Path

BASE_PATH = Path('/kaggle/working/voice-lab-data')
BASE_PATH.mkdir(exist_ok=True)
os.chdir(BASE_PATH)

# Upload datasets as Kaggle datasets or use API
import kaggle
kaggle.api.dataset_download_files('your-dataset', path='raw/', unzip=True)
```

### Local Machine
```bash
# Clone repository
git clone https://github.com/your-org/kasaai-v2.git
cd kasaai-v2/apps/voice-lab/notebooks

# Install dependencies
pip install -r requirements.txt

# Setup data directory
mkdir -p data/{raw,processed,models,output}
```

---

## 🔍 Verification Checklist

After setup, verify everything works:

- [ ] **Data Processing**: `processed/manifests/` contains CSV files
- [ ] **Audio Processing**: `processed/processed_audio/` has 3 subdirectories (asr_16k, tts_22k, tts_24k)
- [ ] **Statistics**: `processed/statistics.json` exists with dataset info
- [ ] **Model Training**: Training runs without errors
- [ ] **Results**: Evaluation notebooks produce charts and reports

---

## 🆘 Quick Troubleshooting

### Problem: "No data found"
**Solution**: Check raw data paths and file permissions
```python
# Debug data loading
from pathlib import Path
raw_path = Path('/content/drive/MyDrive/voice-lab-data/raw')
print(f"Raw data exists: {raw_path.exists()}")
print(f"Contents: {list(raw_path.glob('*'))}")
```

### Problem: "CUDA out of memory"
**Solution**: Reduce batch size
```python
# In any training notebook, modify:
config.batch_size = 1  # Reduce from default
config.gradient_accumulation_steps = 4  # Accumulate gradients
```

### Problem: "Model loading failed"
**Solution**: Check internet connection and HuggingFace access
```python
# Test model download
from transformers import AutoModel
try:
    model = AutoModel.from_pretrained("facebook/wav2vec2-base")
    print("✅ Model loading works")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
```

### Problem: "Runtime disconnected"
**Solution**: Save checkpoints frequently
```python
# Add to training loops
if step % 1000 == 0:
    torch.save(model.state_dict(), f'checkpoint_step_{step}.pt')
    print(f"Checkpoint saved at step {step}")
```

---

## 📊 Expected Outputs

### After Data Processing
```
processed/manifests/asr_16k_dataset.csv: 1000-50000+ rows
processed/manifests/tts_22k_dataset.csv: 1000-50000+ rows  
processed/manifests/tts_24k_dataset.csv: 1000-50000+ rows
processed/statistics.json: Dataset statistics
```

### After Model Training
```
models/[model_name]/checkpoints/: Model files
models/[model_name]/config.json: Training config
output/[model_name]/logs/: Training logs
```

### After Evaluation
```
results/asr_comparison/enhanced_benchmark_report.md: Performance analysis
results/asr_comparison/enhanced_model_comparison.png: Comparison charts
results/asr_comparison/enhanced_benchmark_results.json: Detailed metrics
```

---

## 🎓 Next Steps

1. **Read Full Documentation**: `README_ENHANCED_PIPELINE.md`
2. **Join Team Discussions**: Share results and get feedback
3. **Experiment**: Try different models and datasets
4. **Contribute**: Add new models or improve existing ones
5. **Deploy**: Move best models to production

---

## 🔗 Key Resources

- **Full Documentation**: `README_ENHANCED_PIPELINE.md`
- **Task Tracking**: `TASKS.md`
- **Model Comparisons**: Results in `processed/results/`
- **Training Configs**: Each notebook has detailed configuration

---

**Need Help?** Check the troubleshooting section or ask your team! 🙋‍♀️

*Last Updated: January 2025*