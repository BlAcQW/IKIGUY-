
# Run this script in Google Colab to verify data processing

from google.colab import drive
import pandas as pd
from pathlib import Path
import os

# Mount Google Drive
drive.mount('/content/drive')

# Set base directory
BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')

print("=" * 60)
print("VERIFYING GOOGLE DRIVE DATA PROCESSING")
print("=" * 60)

# Check for processed data
processed_dir = BASE_DIR / 'processed'
metadata_dir = BASE_DIR / 'metadata'

# Check metadata
metadata_files = [
    'all_datasets_processed.csv',
    'processed_data_enhanced.csv',
    'train_split.csv',
    'val_split.csv',
    'test_split.csv'
]

print("\n📊 Checking metadata files:")
for file in metadata_files:
    path = metadata_dir / file
    if path.exists():
        df = pd.read_csv(path)
        print(f"  ✅ {file}: {len(df)} samples")
    else:
        print(f"  ❌ {file}: Not found")

# Check processed audio directories
print("\n🎵 Checking processed audio directories:")
if processed_dir.exists():
    for dataset_dir in processed_dir.iterdir():
        if dataset_dir.is_dir():
            audio_files = list(dataset_dir.glob('**/*.wav'))
            print(f"  - {dataset_dir.name}: {len(audio_files)} audio files")

# Check for main processed CSV
main_csv = metadata_dir / 'all_datasets_processed.csv'
if main_csv.exists():
    df = pd.read_csv(main_csv)
    print(f"\n✅ PROCESSING SUCCESSFUL!")
    print(f"  Total samples: {len(df)}")
    print(f"  Datasets: {df['dataset'].nunique() if 'dataset' in df else 'N/A'}")
    print(f"  Ready for training: YES")
else:
    print(f"\n❌ PROCESSING NOT COMPLETE")
    print("  Please run the data processing notebook on Colab")
