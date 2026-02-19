#!/usr/bin/env python
"""
Create final training manifests for all models
Combines text and audio data into ready-to-use formats
"""

import pandas as pd
from pathlib import Path
import json

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
TEXT_DIR = PROCESSED_DIR / "text_data"
AUDIO_DIR = PROCESSED_DIR / "audio_data"
MANIFESTS_DIR = PROCESSED_DIR / "training_manifests"
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

print("CREATING TRAINING MANIFESTS")
print("=" * 50)

# 1. Translation Model Manifests
print("\n1. TRANSLATION MODEL MANIFESTS")
print("-" * 30)

for split in ['train', 'val', 'test']:
    split_file = TEXT_DIR / f"{split}_pairs.parquet"
    
    if split_file.exists():
        df = pd.read_parquet(split_file)
        print(f"\n  {split.upper()} split: {len(df):,} pairs")
        
        # Create JSONL manifest for translation training
        manifest_path = MANIFESTS_DIR / f"translation_{split}.jsonl"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            for idx, row in df.iterrows():
                entry = {
                    'id': f"{split}_{idx}",
                    'source': row['English'],
                    'target': row['Twi'],
                    'score': row.get('similarity', 1.0)
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
                # Write sample entries for first 10
                if idx < 10 and split == 'train':
                    print(f"    Sample {idx}: EN: '{entry['source'][:50]}...'")
        
        print(f"  [SAVED] translation_{split}.jsonl")
        
        # Also create TSV format for certain frameworks
        tsv_path = MANIFESTS_DIR / f"translation_{split}.tsv"
        df[['English', 'Twi']].to_csv(tsv_path, sep='\t', index=False, header=False)
        print(f"  [SAVED] translation_{split}.tsv")

# 2. ASR Model Manifests
print("\n2. ASR MODEL MANIFESTS")
print("-" * 30)

audio_manifest_path = AUDIO_DIR / "audio_manifest.csv"
if audio_manifest_path.exists():
    audio_df = pd.read_csv(audio_manifest_path)
    
    # Filter for files with transcriptions
    transcribed = audio_df[audio_df.get('transcription', pd.Series()).notna()] if 'transcription' in audio_df.columns else pd.DataFrame()
    
    if not transcribed.empty:
        print(f"\n  Files with transcriptions: {len(transcribed):,}")
        
        # Create ASR manifest
        for split in ['train', 'test']:
            split_data = transcribed[transcribed['split'] == split]
            
            if not split_data.empty:
                asr_manifest = []
                for _, row in split_data.iterrows():
                    asr_manifest.append({
                        'audio_filepath': row['audio_path'],
                        'text': row['transcription'],
                        'duration': -1,  # Will be calculated during training
                        'language': row['language']
                    })
                
                # Save ASR manifest
                asr_path = MANIFESTS_DIR / f"asr_{split}.json"
                with open(asr_path, 'w', encoding='utf-8') as f:
                    json.dump(asr_manifest, f, ensure_ascii=False, indent=2)
                
                print(f"  [SAVED] asr_{split}.json ({len(asr_manifest)} files)")
    else:
        print("  [WARNING] No transcribed audio files found")
        print("  Creating placeholder ASR manifests from audio list...")
        
        # Create placeholder manifests without transcriptions
        for split in ['train', 'test']:
            split_data = audio_df[audio_df['split'] == split]
            
            if not split_data.empty:
                asr_manifest = []
                for _, row in split_data.head(100).iterrows():  # Sample 100
                    asr_manifest.append({
                        'audio_filepath': row['audio_path'],
                        'text': "",  # Empty, needs transcription
                        'duration': -1,
                        'language': row['language'],
                        'needs_transcription': True
                    })
                
                asr_path = MANIFESTS_DIR / f"asr_{split}_placeholder.json"
                with open(asr_path, 'w', encoding='utf-8') as f:
                    json.dump(asr_manifest, f, ensure_ascii=False, indent=2)
                
                print(f"  [SAVED] asr_{split}_placeholder.json ({len(asr_manifest)} files)")

# 3. Language Model Manifests
print("\n3. LANGUAGE MODEL MANIFESTS")
print("-" * 30)

# Create monolingual Twi corpus for language modeling
train_file = TEXT_DIR / "train_pairs.parquet"
if train_file.exists():
    df = pd.read_parquet(train_file)
    
    # Extract Twi texts
    twi_texts = df['Twi'].dropna()
    
    # Save as text file for language modeling
    lm_path = MANIFESTS_DIR / "lm_twi_corpus.txt"
    with open(lm_path, 'w', encoding='utf-8') as f:
        for text in twi_texts:
            f.write(text + '\n')
    
    print(f"  [SAVED] lm_twi_corpus.txt ({len(twi_texts):,} sentences)")
    
    # Also create a deduplicated version
    unique_texts = twi_texts.drop_duplicates()
    lm_unique_path = MANIFESTS_DIR / "lm_twi_corpus_unique.txt"
    with open(lm_unique_path, 'w', encoding='utf-8') as f:
        for text in unique_texts:
            f.write(text + '\n')
    
    print(f"  [SAVED] lm_twi_corpus_unique.txt ({len(unique_texts):,} unique sentences)")

# 4. Create combined statistics
print("\n4. CREATING SUMMARY STATISTICS")
print("-" * 30)

summary = {
    'text_data': {},
    'audio_data': {},
    'manifests_created': []
}

# Text statistics
if (TEXT_DIR / "statistics.json").exists():
    with open(TEXT_DIR / "statistics.json", 'r') as f:
        text_stats = json.load(f)
        summary['text_data'] = text_stats

# Audio statistics
if (AUDIO_DIR / "audio_statistics.json").exists():
    with open(AUDIO_DIR / "audio_statistics.json", 'r') as f:
        audio_stats = json.load(f)
        summary['audio_data'] = audio_stats

# List created manifests
for manifest_file in MANIFESTS_DIR.glob('*'):
    if manifest_file.is_file():
        summary['manifests_created'].append({
            'name': manifest_file.name,
            'size_mb': manifest_file.stat().st_size / (1024 * 1024)
        })

# Save summary
summary_path = MANIFESTS_DIR / "training_summary.json"
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("\n[SAVED] training_summary.json")

# 5. Create README
print("\n5. CREATING README")
print("-" * 30)

readme_content = f"""# Voice Lab Training Manifests

## Overview
This directory contains ready-to-use training manifests for Twi language models.

## Available Data

### Translation (English-Twi)
- **Train**: {summary['text_data'].get('train_size', 'N/A'):,} pairs
- **Validation**: {summary['text_data'].get('val_size', 'N/A'):,} pairs  
- **Test**: {summary['text_data'].get('test_size', 'N/A'):,} pairs
- **Vocabulary**: {summary['text_data'].get('vocab_size', 'N/A'):,} words

### Audio (ASR/TTS)
- **Total Files**: {summary['audio_data'].get('total_audio_files', 'N/A'):,}
- **Total Size**: {summary['audio_data'].get('total_size_gb', 0):.2f} GB
- **Languages**: Fante, Twi, Ewe

## Manifest Files

### Translation Training
- `translation_train.jsonl` - Training data in JSONL format
- `translation_val.jsonl` - Validation data in JSONL format
- `translation_test.jsonl` - Test data in JSONL format
- `translation_*.tsv` - Same data in TSV format

### ASR Training
- `asr_train.json` - Training audio with transcriptions
- `asr_test.json` - Test audio with transcriptions
- `asr_*_placeholder.json` - Audio files needing transcription

### Language Modeling
- `lm_twi_corpus.txt` - Full Twi text corpus
- `lm_twi_corpus_unique.txt` - Deduplicated Twi sentences

## Usage Examples

### Fine-tune mT5 for Translation
```python
from transformers import MT5ForConditionalGeneration, MT5Tokenizer

model = MT5ForConditionalGeneration.from_pretrained("google/mt5-small")
tokenizer = MT5Tokenizer.from_pretrained("google/mt5-small")

# Load training data
with open("translation_train.jsonl", "r") as f:
    train_data = [json.loads(line) for line in f]
```

### Fine-tune Whisper for ASR
```python
from transformers import WhisperForConditionalGeneration

model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

# Load ASR manifest
with open("asr_train.json", "r") as f:
    asr_data = json.load(f)
```

## Data Quality
- Text pairs have similarity scores for quality filtering
- Audio files include metadata where available
- All data is split into train/val/test sets

## Next Steps
1. Upload manifests to training environment (Colab/Cloud)
2. Preprocess audio to 16kHz mono WAV
3. Tokenize text data for model input
4. Begin model training

Generated: {pd.Timestamp.now().isoformat()}
"""

readme_path = MANIFESTS_DIR / "README.md"
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("[SAVED] README.md")

# Final summary
print("\n" + "=" * 50)
print("MANIFEST CREATION COMPLETE!")
print("=" * 50)

print(f"\nLocation: {MANIFESTS_DIR}")
print("\nCreated manifests:")
for manifest in summary['manifests_created']:
    print(f"  - {manifest['name']} ({manifest['size_mb']:.2f} MB)")

print("\nReady for model training!")
print("\nRecommended next steps:")
print("  1. Upload manifests to Google Colab")
print("  2. Install transformers, datasets libraries")
print("  3. Start with translation model (fastest to train)")
print("  4. Then train ASR model with audio data")
print("  5. Finally train TTS model if needed")