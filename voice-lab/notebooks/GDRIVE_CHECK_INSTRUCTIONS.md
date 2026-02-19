# Google Drive Data Verification Instructions

## Option 1: Check via Google Colab (RECOMMENDED)

This is the easiest way to verify your Google Drive data:

1. **Open Google Colab**: https://colab.research.google.com/

2. **Create a new notebook** or upload `check_gdrive_colab.py`

3. **Run this code** in a cell:

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Check voice-lab-data
import os
from pathlib import Path

BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')

if BASE_DIR.exists():
    print(f"✅ Found: {BASE_DIR}")
    
    # Check raw data
    raw_dir = BASE_DIR / 'raw'
    if raw_dir.exists():
        print(f"\n📁 Raw datasets found:")
        for dataset in raw_dir.iterdir():
            if dataset.is_dir():
                file_count = sum(1 for _ in dataset.rglob('*') if _.is_file())
                print(f"  - {dataset.name}: {file_count} files")
    
    # Check processed data
    metadata = BASE_DIR / 'metadata' / 'all_datasets_processed.csv'
    if metadata.exists():
        import pandas as pd
        df = pd.read_csv(metadata)
        print(f"\n✅ Processed data found: {len(df)} samples")
    else:
        print(f"\n⚠️ No processed data found yet")
        print("   Run the processing notebook to process raw data")
else:
    print(f"❌ Directory not found: {BASE_DIR}")
    print("   Please create 'voice-lab-data' folder in Google Drive")
```

## Option 2: Check from Local Machine

1. **Run the verification script**:
```bash
python check_gdrive_data.py
```

Note: This requires Google OAuth authentication and may open a browser window.

## Expected Directory Structure

Your Google Drive should have this structure:

```
Google Drive/
└── MyDrive/
    └── voice-lab-data/
        ├── raw/                 # Raw datasets
        │   ├── common_voice_twi/
        │   ├── african_whisper/
        │   ├── afrispeech_200/
        │   ├── lingua_libre/
        │   ├── jw300/
        │   ├── bibletis/
        │   ├── financial_inclusion/
        │   └── michsethowusu/
        ├── processed/           # Will be created after processing
        └── metadata/            # Will contain CSV files after processing
```

## What to Look For

### ✅ Data is Ready if:
- `raw/` directory exists with datasets
- At least 5-6 dataset folders present
- Total audio files > 1,000

### ⚠️ Need to Process if:
- `raw/` data exists but no `processed/` folder
- No `metadata/all_datasets_processed.csv` file
- Last processing shows < 1,000 samples

### ❌ Need to Upload Data if:
- No `voice-lab-data` folder in Google Drive
- `raw/` directory is empty or missing
- Fewer than 3 dataset folders

## Next Steps

### If Data is Available:
1. Open `002_phase1_data_processing_enhanced.ipynb` in Google Colab
2. Mount Google Drive
3. Run all cells
4. Wait for "✅ ALL DATASETS PROCESSED AND SAVED!" message

### If Data is Missing:
1. Create `voice-lab-data/raw/` in Google Drive
2. Upload dataset folders
3. Then run the processing notebook

## Quick Colab Test

Copy and run this in Google Colab to quickly check:

```python
!ls -la /content/drive/MyDrive/voice-lab-data/raw/ 2>/dev/null || echo "Folder not found - please mount drive first"
```