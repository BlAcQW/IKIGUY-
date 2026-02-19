"""
Google Colab script to check raw data in Google Drive
Run this directly in Google Colab for easiest access
"""

# Run this cell first to mount Google Drive
from google.colab import drive
import pandas as pd
from pathlib import Path
import os

# Mount Google Drive
drive.mount('/content/drive')

# Set base directory
BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')

print("=" * 60)
print("GOOGLE DRIVE DATA VERIFICATION - COLAB VERSION")
print("=" * 60)

# Check if base directory exists
if not BASE_DIR.exists():
    print(f"\n[ERROR] Directory not found: {BASE_DIR}")
    print("Please ensure 'voice-lab-data' folder exists in your Google Drive")
else:
    print(f"\n[OK] Found base directory: {BASE_DIR}")
    
    # Check directory structure
    print("\n" + "=" * 60)
    print("DIRECTORY STRUCTURE")
    print("=" * 60)
    
    for item in BASE_DIR.iterdir():
        if item.is_dir():
            print(f"\n[DIR] {item.name}/")
            # Count items in subdirectory
            sub_items = list(item.iterdir())
            print(f"      Contains {len(sub_items)} items")

    # Check RAW data specifically
    print("\n" + "=" * 60)
    print("RAW DATASETS CHECK")
    print("=" * 60)
    
    raw_dir = BASE_DIR / 'raw'
    
    if raw_dir.exists():
        print(f"\n[OK] Raw directory found: {raw_dir}")
        
        expected_datasets = [
            'common_voice_twi',
            'african_whisper', 
            'afrispeech_200',
            'lingua_libre',
            'jw300',
            'bibletis',
            'financial_inclusion',
            'michsethowusu'
        ]
        
        print("\nDatasets in /raw directory:")
        dataset_summary = {}
        
        for dataset_dir in raw_dir.iterdir():
            if dataset_dir.is_dir():
                # Count files recursively
                file_count = 0
                total_size = 0
                audio_count = 0
                text_count = 0
                
                for root, dirs, files in os.walk(dataset_dir):
                    file_count += len(files)
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            total_size += file_path.stat().st_size
                            if file.endswith(('.mp3', '.wav', '.flac', '.m4a')):
                                audio_count += 1
                            elif file.endswith(('.txt', '.csv', '.tsv', '.json')):
                                text_count += 1
                        except:
                            pass
                
                size_gb = total_size / (1024**3)
                status = "[READY]" if dataset_dir.name.lower() in [d.lower() for d in expected_datasets] else "[UNKNOWN]"
                
                print(f"  {status} {dataset_dir.name}:")
                print(f"         Files: {file_count} total ({audio_count} audio, {text_count} text)")
                print(f"         Size: {size_gb:.2f} GB")
                
                dataset_summary[dataset_dir.name] = {
                    'files': file_count,
                    'audio': audio_count,
                    'text': text_count,
                    'size_gb': size_gb
                }
        
        # Check dataset availability
        print("\n" + "=" * 60)
        print("DATASET AVAILABILITY SUMMARY")
        print("=" * 60)
        
        found_datasets = list(dataset_summary.keys())
        for dataset in expected_datasets:
            if any(dataset.lower() in found.lower() for found in found_datasets):
                matching = [f for f in found_datasets if dataset.lower() in f.lower()][0]
                info = dataset_summary[matching]
                print(f"  [OK] {dataset}: {info['audio']} audio files")
            else:
                print(f"  [MISSING] {dataset}")
        
        total_audio = sum(d['audio'] for d in dataset_summary.values())
        total_size = sum(d['size_gb'] for d in dataset_summary.values())
        
        print(f"\nTOTAL:")
        print(f"  Datasets: {len(found_datasets)}")
        print(f"  Audio files: {total_audio:,}")
        print(f"  Total size: {total_size:.2f} GB")
        
        if total_audio > 1000:
            print("\n[OK] SUFFICIENT DATA AVAILABLE FOR PROCESSING!")
            print("     You can now run the processing notebook")
        else:
            print("\n[WARNING] Limited data available")
            print("          You may want to add more datasets")
    
    else:
        print(f"\n[ERROR] Raw directory not found: {raw_dir}")
        print("        Please upload raw datasets to Google Drive")

    # Check PROCESSED data
    print("\n" + "=" * 60)
    print("PROCESSED DATA CHECK")
    print("=" * 60)
    
    processed_dir = BASE_DIR / 'processed'
    metadata_dir = BASE_DIR / 'metadata'
    
    if processed_dir.exists():
        processed_datasets = list(processed_dir.iterdir())
        print(f"\n[OK] Processed directory found with {len(processed_datasets)} datasets")
        
        for dataset in processed_datasets[:5]:  # Show first 5
            if dataset.is_dir():
                file_count = len(list(dataset.glob('**/*')))
                print(f"  - {dataset.name}: {file_count} files")
    else:
        print(f"\n[INFO] No processed directory found yet")
        print("       Will be created when you run the processing notebook")
    
    if metadata_dir.exists():
        metadata_files = list(metadata_dir.glob('*.csv'))
        print(f"\n[OK] Metadata directory found with {len(metadata_files)} files")
        
        # Check for main processed file
        main_csv = metadata_dir / 'all_datasets_processed.csv'
        if main_csv.exists():
            df = pd.read_csv(main_csv)
            print(f"\n[OK] PREVIOUS PROCESSING FOUND!")
            print(f"     Total samples: {len(df):,}")
            print(f"     Datasets: {df['dataset'].nunique() if 'dataset' in df else 'N/A'}")
            
            if len(df) > 10000:
                print("\n[OK] DATA IS READY FOR TRAINING!")
            else:
                print("\n[INFO] Processing exists but may need to be re-run")
                print("       for complete dataset")
    else:
        print(f"\n[INFO] No metadata directory found yet")

print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)

if BASE_DIR.exists() and raw_dir.exists() and total_audio > 1000:
    print("\n1. Raw data is available and ready for processing")
    print("2. Open notebook 002_phase1_data_processing_enhanced.ipynb in Colab")
    print("3. Run all cells to process the data")
    print("4. Processing will create:")
    print("   - Normalized audio files")
    print("   - Text preprocessing and phonemes")
    print("   - Train/val/test splits")
    print("   - Metadata CSV files")
else:
    print("\n1. Ensure voice-lab-data folder exists in Google Drive")
    print("2. Upload raw datasets to voice-lab-data/raw/")
    print("3. Then run the processing notebook")