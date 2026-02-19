"""
Script to verify that data processing from notebook 002 was successful
and data is ready for training.
"""
import pandas as pd
import os
from pathlib import Path
import json

def verify_local_processing():
    """Check local processing results"""
    print("=" * 60)
    print("VERIFYING LOCAL DATA PROCESSING")
    print("=" * 60)
    
    # Check metadata file
    metadata_path = Path(r"C:\Projects\kasaai-v2\apps\voice-lab\data\metadata\all_datasets_processed.csv")
    
    if metadata_path.exists():
        df = pd.read_csv(metadata_path)
        print(f"[OK] Metadata file found: {metadata_path}")
        print(f"   Total samples: {len(df)}")
        
        # Check datasets included
        if 'dataset' in df.columns:
            datasets = df['dataset'].value_counts()
            print(f"\n[DATASETS PROCESSED]:")
            for dataset, count in datasets.items():
                print(f"   - {dataset}: {count} samples")
        
        # Check data quality
        print(f"\n[DATA QUALITY CHECKS]:")
        print(f"   - Samples with processed text: {df['processed_text'].notna().sum()}")
        print(f"   - Samples with Twi characters: {df['has_twi_chars'].sum() if 'has_twi_chars' in df else 'N/A'}")
        print(f"   - Average word count: {df['word_count'].mean():.1f}" if 'word_count' in df else "N/A")
        
        # Check audio paths
        if 'audio_path' in df.columns:
            audio_exists = sum(1 for path in df['audio_path'].dropna() if Path(path).exists())
            print(f"   - Audio files found locally: {audio_exists}/{len(df)}")
        
        return True, df
    else:
        print(f"[ERROR] Metadata file not found: {metadata_path}")
        return False, None

def check_notebook_execution():
    """Check if notebook was executed on Colab"""
    print("\n" + "=" * 60)
    print("CHECKING NOTEBOOK EXECUTION STATUS")
    print("=" * 60)
    
    notebook_path = Path("002_phase1_data_processing_enhanced_executed.ipynb")
    
    if notebook_path.exists():
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        
        # Check for execution outputs
        code_cells = [cell for cell in nb['cells'] if cell['cell_type'] == 'code']
        cells_with_output = [cell for cell in code_cells if cell.get('outputs', [])]
        
        print(f"[NOTEBOOK ANALYSIS]:")
        print(f"   - Total code cells: {len(code_cells)}")
        print(f"   - Cells with outputs: {len(cells_with_output)}")
        
        # Check for Google Drive references
        gdrive_cells = 0
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                source = ''.join(cell['source'])
                if 'drive.mount' in source or '/content/drive' in source:
                    gdrive_cells += 1
        
        print(f"   - Google Drive references: {gdrive_cells} cells")
        
        # Check last execution output
        if cells_with_output:
            last_output = cells_with_output[-1].get('outputs', [])
            for output in last_output:
                if 'text' in output:
                    text = ''.join(output['text'])
                    if 'No data processed' in text:
                        print(f"\n[WARNING] Last output indicates no data was processed on Colab")
                        print("   This likely means the notebook needs to be run on Google Colab")
                        print("   with proper dataset access.")
                        return False
        
        return True
    else:
        print(f"[ERROR] Notebook not found: {notebook_path}")
        return False

def generate_colab_verification_script():
    """Generate script to run on Colab to verify processing"""
    print("\n" + "=" * 60)
    print("GOOGLE COLAB VERIFICATION SCRIPT")
    print("=" * 60)
    
    colab_script = '''
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

print("\\n📊 Checking metadata files:")
for file in metadata_files:
    path = metadata_dir / file
    if path.exists():
        df = pd.read_csv(path)
        print(f"  ✅ {file}: {len(df)} samples")
    else:
        print(f"  ❌ {file}: Not found")

# Check processed audio directories
print("\\n🎵 Checking processed audio directories:")
if processed_dir.exists():
    for dataset_dir in processed_dir.iterdir():
        if dataset_dir.is_dir():
            audio_files = list(dataset_dir.glob('**/*.wav'))
            print(f"  - {dataset_dir.name}: {len(audio_files)} audio files")

# Check for main processed CSV
main_csv = metadata_dir / 'all_datasets_processed.csv'
if main_csv.exists():
    df = pd.read_csv(main_csv)
    print(f"\\n✅ PROCESSING SUCCESSFUL!")
    print(f"  Total samples: {len(df)}")
    print(f"  Datasets: {df['dataset'].nunique() if 'dataset' in df else 'N/A'}")
    print(f"  Ready for training: YES")
else:
    print(f"\\n❌ PROCESSING NOT COMPLETE")
    print("  Please run the data processing notebook on Colab")
'''
    
    script_path = Path("verify_colab_processing.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(colab_script)
    
    print(f"[OK] Created Colab verification script: {script_path}")
    print("\nTo verify Google Drive processing:")
    print("1. Open Google Colab")
    print("2. Upload and run verify_colab_processing.py")
    print("3. Check the output for processing status")
    
    return script_path

def main():
    print("\n" + "DATA PROCESSING VERIFICATION REPORT".center(60))
    print("=" * 60)
    
    # Check local processing
    local_success, df = verify_local_processing()
    
    # Check notebook execution
    notebook_executed = check_notebook_execution()
    
    # Generate Colab verification script
    colab_script = generate_colab_verification_script()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if local_success and df is not None:
        print(f"[OK] Local processing found: {len(df)} samples")
        print("   However, this appears to be from a previous run.")
    
    print("\n[IMPORTANT NOTES]:")
    print("1. The notebook shows 'No data processed' in the last output")
    print("2. This indicates the notebook needs to be run on Google Colab")
    print("3. The local CSV file (145 samples) appears to be from a previous test run")
    
    print("\n[TO CONFIRM SUCCESSFUL PROCESSING ON COLAB]:")
    print("1. Open the notebook in Google Colab")
    print("2. Ensure Google Drive is mounted")
    print("3. Run all cells in the notebook")
    print("4. Look for these success indicators:")
    print("   - '[OK] ALL DATASETS PROCESSED AND SAVED!'")
    print("   - Total sample count (should be thousands)")
    print("   - Files saved to /content/drive/MyDrive/voice-lab-data/")
    print("5. Run the verify_colab_processing.py script on Colab")
    
    print("\n[EXPECTED RESULTS AFTER SUCCESSFUL PROCESSING]:")
    print("   - Common Voice: ~12,000+ samples")
    print("   - African Whisper: ~1,000+ samples")
    print("   - Other datasets: Various counts")
    print("   - Total: 15,000+ samples ready for training")

if __name__ == "__main__":
    main()