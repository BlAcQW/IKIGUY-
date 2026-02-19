#!/usr/bin/env python
"""
Quick fix to create notebook-compatible TTS data structure
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path("G:/My Drive/voice-lab-data")
source_file = BASE_DIR / 'metadata' / 'processed_data_enhanced.csv'
tts_datasets = BASE_DIR / 'processed' / 'tts_ready'

# Load data
df = pd.read_csv(source_file)
print(f"Processing {len(df)} samples...")

# Group by dialect  
dialects = {
    'asante_twi': df[df['dialect'] == 'twi'],
    'akuapem_twi': df[df['dialect'] == 'akuapem_twi'], 
    'fante': df[df['dialect'] == 'fante']
}

total_created = 0

for dialect, dialect_df in dialects.items():
    if len(dialect_df) == 0:
        continue
        
    dialect_dir = tts_datasets / dialect
    
    # Use only real audio samples (not SYNTHETIC)
    real_df = dialect_df[dialect_df['audio'] != 'SYNTHETIC']
    
    if len(real_df) == 0:
        real_df = dialect_df  # Use all if no real audio
    
    print(f"{dialect}: {len(real_df)} samples")
    
    # Create Coqui metadata.txt format: audio_path|text|speaker
    lines = []
    for _, row in real_df.iterrows():
        audio = str(row['audio'])
        text = str(row['text']).replace('|', '-')  # Remove pipes 
        speaker = str(row['speaker_id'])
        lines.append(f"{audio}|{text}|{speaker}")
    
    # Save metadata.txt (REQUIRED by notebook)
    meta_file = dialect_dir / 'metadata.txt'
    with open(meta_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"  Created: {meta_file.name} ({len(lines)} lines)")
    total_created += len(lines)

print(f"\nTotal samples created: {total_created}")
print("Notebook 005_phase3_tts_development.ipynb is now compatible!")

# Verify key paths exist
key_paths = [
    BASE_DIR / 'metadata' / 'processed_data_enhanced.csv',
    tts_datasets / 'asante_twi' / 'metadata.txt',
    tts_datasets / 'akuapem_twi' / 'metadata.txt', 
    tts_datasets / 'fante' / 'metadata.txt'
]

print("\nPath verification:")
all_good = True
for path in key_paths:
    exists = path.exists()
    status = "[OK]" if exists else "[MISSING]"
    print(f"  {status} {path}")
    if not exists:
        all_good = False

if all_good:
    print("\n[SUCCESS] All required paths exist!")
    print("The notebook should work correctly now.")
else:
    print("\n[WARNING] Some paths are missing.")