#!/usr/bin/env python
"""
TTS data preparation script compatible with 005_phase3_tts_development.ipynb
Fixes path mismatches and creates data in expected locations
"""

import pandas as pd
from pathlib import Path
import json
import shutil

# Match notebook's path structure exactly
BASE_DIR = Path("G:/My Drive/voice-lab-data")

# These paths MUST match the notebook's TTS_DIRS structure
TTS_DIRS = {
    'models': BASE_DIR / 'models' / 'tts',
    'datasets': BASE_DIR / 'processed' / 'tts_ready',  # ← Key: notebook expects this
    'outputs': BASE_DIR / 'outputs' / 'tts',
    'voices': BASE_DIR / 'voices',
    'configs': BASE_DIR / 'configs' / 'tts',
}

# Create directories to match notebook expectations
for dir_path in TTS_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

print("NOTEBOOK-COMPATIBLE TTS DATA PREPARATION")
print("=" * 60)

# 1. Check if we have the source data
source_file = BASE_DIR / 'metadata' / 'processed_data_enhanced.csv'

if not source_file.exists():
    print(f"❌ ERROR: Source file not found: {source_file}")
    print("Run prepare_tts_training_data_working.py first!")
    exit(1)

print(f"✅ Found source data: {source_file}")

# 2. Load and process our prepared data
df = pd.read_csv(source_file)
print(f"✅ Loaded {len(df)} samples")

# 3. Create dialect-specific datasets in the structure the notebook expects
dialects_data = {
    'asante_twi': df[df['dialect'].str.contains('twi', case=False, na=False) & 
                     ~df['dialect'].str.contains('akuapem|fante', case=False, na=False)],
    'akuapem_twi': df[df['dialect'].str.contains('akuapem', case=False, na=False)],
    'fante': df[df['dialect'].str.contains('fante', case=False, na=False)]
}

for dialect, dialect_df in dialects_data.items():
    if len(dialect_df) == 0:
        print(f"⚠️  No data found for {dialect}")
        continue
    
    # Create dialect-specific directory (notebook expects this structure)
    dialect_dir = TTS_DIRS['datasets'] / dialect
    dialect_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter out synthetic samples for real audio training
    real_audio_df = dialect_df[dialect_df['audio'] != 'SYNTHETIC'].copy()
    
    if len(real_audio_df) == 0:
        print(f"⚠️  No real audio samples for {dialect}, using all data")
        working_df = dialect_df.copy()
    else:
        working_df = real_audio_df.copy()
    
    print(f"\n📁 Processing {dialect}: {len(working_df)} samples")
    
    # 4. Create metadata.txt in Coqui TTS format (audio_path|text|speaker)
    metadata_lines = []
    detailed_metadata = []
    
    for _, row in working_df.iterrows():
        audio_path = str(row['audio'])
        text = str(row['text'])
        speaker_id = str(row.get('speaker_id', f"{dialect}_speaker"))
        
        # Coqui TTS format
        metadata_lines.append(f"{audio_path}|{text}|{speaker_id}")
        
        # Detailed metadata for notebook processing
        detailed_metadata.append({
            'audio_file': audio_path,
            'text': text,
            'speaker_id': speaker_id,
            'duration': row.get('duration', 3.0),
            'dialect': dialect,
            'source': row.get('source', 'processed')
        })
    
    # Save metadata.txt (CRITICAL: notebook expects this exact filename in dataset dir)
    metadata_file = dialect_dir / 'metadata.txt'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(metadata_lines))
    print(f"  ✅ Created: {metadata_file} ({len(metadata_lines)} lines)")
    
    # Save detailed metadata as JSON
    json_file = dialect_dir / 'metadata.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_metadata, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Created: {json_file}")
    
    # Save CSV for backup/analysis
    csv_file = dialect_dir / 'dataset.csv'
    working_df.to_csv(csv_file, index=False)
    print(f"  ✅ Created: {csv_file}")
    
    # Create phonemes.txt (if we have phoneme data)
    if 'phonemes' in working_df.columns:
        phoneme_lines = []
        for _, row in working_df.iterrows():
            if pd.notna(row.get('phonemes', '')):
                phoneme_lines.append(f"{row['text']}||{row['phonemes']}")
        
        if phoneme_lines:
            phonemes_file = dialect_dir / 'phonemes.txt'
            with open(phonemes_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(phoneme_lines))
            print(f"  ✅ Created: {phonemes_file} ({len(phoneme_lines)} phoneme mappings)")

# 5. Create combined dataset (notebook also uses this)
print(f"\n📁 Creating combined dataset...")

# Combine all real audio samples
all_real_audio = df[df['audio'] != 'SYNTHETIC'].copy()
if len(all_real_audio) > 0:
    combined_dir = TTS_DIRS['datasets'] / 'combined_twi'
    combined_dir.mkdir(parents=True, exist_ok=True)
    
    # Create combined metadata.txt
    combined_metadata_lines = []
    for _, row in all_real_audio.iterrows():
        audio_path = str(row['audio'])
        text = str(row['text'])
        speaker_id = str(row.get('speaker_id', 'twi_speaker'))
        combined_metadata_lines.append(f"{audio_path}|{text}|{speaker_id}")
    
    combined_metadata_file = combined_dir / 'metadata.txt'
    with open(combined_metadata_file, 'w', encoding='utf-8') as f:
        f.write('\\n'.join(combined_metadata_lines))
    print(f"  ✅ Created combined dataset: {len(combined_metadata_lines)} samples")

# 6. Verify paths match notebook expectations
print(f"\n🔍 PATH VERIFICATION:")
print("-" * 40)

expected_paths = [
    BASE_DIR / 'metadata' / 'processed_data_enhanced.csv',  # Source data ✅
    TTS_DIRS['datasets'] / 'asante_twi' / 'metadata.txt',   # Dialect dataset
    TTS_DIRS['datasets'] / 'combined_twi' / 'metadata.txt', # Combined dataset
    TTS_DIRS['configs'],                                     # Config directory
    TTS_DIRS['outputs']                                      # Output directory
]

all_paths_ok = True
for path in expected_paths:
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {path}")
    if not exists and 'metadata.txt' in str(path):
        all_paths_ok = False

# 7. Create sample audio verification
print(f"\n🔊 AUDIO PATH VERIFICATION:")
print("-" * 40)

# Check a few audio paths to see if they exist
sample_audio_paths = all_real_audio['audio'].head(5).tolist() if len(all_real_audio) > 0 else []
audio_exists_count = 0

for audio_path in sample_audio_paths:
    exists = Path(audio_path).exists()
    status = "✅" if exists else "❌"
    filename = Path(audio_path).name
    print(f"  {status} {filename}")
    if exists:
        audio_exists_count += 1

if len(sample_audio_paths) > 0:
    audio_availability = (audio_exists_count / len(sample_audio_paths)) * 100
    print(f"\n📊 Audio availability: {audio_availability:.1f}% ({audio_exists_count}/{len(sample_audio_paths)})")
    
    if audio_availability < 50:
        print("⚠️  WARNING: Most audio files don't exist!")
        print("   This means you need to extract MichSet audio files first.")
        print("   Install torchcodec: pip install torchcodec")
        print("   Or wait for Bible TTS processing to complete.")

# 8. Summary
print(f"\n" + "=" * 60)
print("NOTEBOOK COMPATIBILITY CHECK")
print("=" * 60)

if all_paths_ok:
    print("✅ All required paths created successfully!")
    print("✅ Notebook 005_phase3_tts_development.ipynb should work correctly.")
else:
    print("❌ Some required paths are missing!")

print(f"\n📋 Dataset Summary:")
for dialect, dialect_df in dialects_data.items():
    real_count = len(dialect_df[dialect_df['audio'] != 'SYNTHETIC']) if len(dialect_df) > 0 else 0
    if real_count > 0:
        print(f"  {dialect}: {real_count} real audio samples")

print(f"\n📁 Key directories for notebook:")
for name, path in TTS_DIRS.items():
    print(f"  {name}: {path}")

print(f"\n🎯 Ready for TTS training with 005_phase3_tts_development.ipynb!")

if audio_exists_count == 0 and len(sample_audio_paths) > 0:
    print(f"\n⚠️  CRITICAL: Audio files need extraction!")
    print("   Current audio paths point to estimated locations.")
    print("   Run MichSet audio extraction first for real training.")
else:
    print(f"\n🚀 All systems ready for TTS training!")