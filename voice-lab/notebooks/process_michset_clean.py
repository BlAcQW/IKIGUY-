#!/usr/bin/env python
"""
Clean processing of MichSetHowusu 4M+ English-Twi pairs
No Unicode symbols - Windows compatible
"""

import pandas as pd
from pathlib import Path
import json
from collections import Counter
import numpy as np

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING MICHSETHOWUSU 4M+ ENGLISH-TWI PAIRS")
print("=" * 50)

# Process the text dataset
michset_dir = RAW_DIR / "michsethowusu"
pairs_file = michset_dir / "english_twi_4M_pairs.parquet"

if not pairs_file.exists():
    print(f"ERROR: File not found: {pairs_file}")
    exit(1)

print(f"\nLoading {pairs_file.name}...")
df_pairs = pd.read_parquet(pairs_file)
print(f"Loaded {len(df_pairs):,} sentence pairs")

# Check columns
print(f"\nColumns: {df_pairs.columns.tolist()}")

# Filter by quality if similarity column exists
if 'similarity' in df_pairs.columns:
    # Process in chunks for memory efficiency
    print("\nFiltering high quality pairs (similarity > 0.8)...")
    high_quality = df_pairs[df_pairs['similarity'] > 0.8]
    print(f"High quality pairs: {len(high_quality):,}")
else:
    high_quality = df_pairs
    print("\nNo similarity column found, using all pairs")

# Create splits
print("\nCreating train/val/test splits...")

# Shuffle data
print("Shuffling data...")
high_quality = high_quality.sample(frac=1, random_state=42).reset_index(drop=True)

# Calculate split sizes
n_total = len(high_quality)
n_test = int(0.1 * n_total)  # 10% test
n_val = int(0.09 * n_total)  # 9% validation
n_train = n_total - n_test - n_val  # ~81% train

# Split
test = high_quality.iloc[:n_test]
val = high_quality.iloc[n_test:n_test+n_val]
train = high_quality.iloc[n_test+n_val:]

print(f"\nSplit sizes:")
print(f"  Train: {len(train):,} pairs ({len(train)/n_total*100:.1f}%)")
print(f"  Val:   {len(val):,} pairs ({len(val)/n_total*100:.1f}%)")
print(f"  Test:  {len(test):,} pairs ({len(test)/n_total*100:.1f}%)")

# Save splits
text_dir = PROCESSED_DIR / "text_data"
text_dir.mkdir(exist_ok=True)

print("\nSaving split files...")
train.to_parquet(text_dir / "train_pairs.parquet")
print(f"  [SAVED] train_pairs.parquet")

val.to_parquet(text_dir / "val_pairs.parquet")
print(f"  [SAVED] val_pairs.parquet")

test.to_parquet(text_dir / "test_pairs.parquet")
print(f"  [SAVED] test_pairs.parquet")

# Save samples as CSV
print("\nSaving sample CSV files...")
train.head(1000).to_csv(text_dir / "train_sample.csv", index=False, encoding='utf-8-sig')
print(f"  [SAVED] train_sample.csv (1000 samples)")

val.head(100).to_csv(text_dir / "val_sample.csv", index=False, encoding='utf-8-sig')
print(f"  [SAVED] val_sample.csv (100 samples)")

test.head(100).to_csv(text_dir / "test_sample.csv", index=False, encoding='utf-8-sig')
print(f"  [SAVED] test_sample.csv (100 samples)")

# Create vocabulary
print("\nBuilding Twi vocabulary...")

# Find the Twi column
twi_column = None
for col in train.columns:
    if 'twi' in col.lower():
        twi_column = col
        break

if twi_column is None:
    # Assume second column is Twi if not found
    twi_column = train.columns[1]
    print(f"Warning: Using column '{twi_column}' as Twi text")
else:
    print(f"Using column '{twi_column}' for Twi text")

# Build vocabulary from training set
vocab = Counter()
twi_texts = train[twi_column].dropna()
total_texts = len(twi_texts)
sample_size = min(500000, total_texts)  # Process up to 500K texts

print(f"Processing {sample_size:,} texts for vocabulary...")

for i, text in enumerate(twi_texts.head(sample_size)):
    if isinstance(text, str):
        words = text.lower().split()
        vocab.update(words)
    
    # Progress indicator
    if (i + 1) % 100000 == 0:
        print(f"  Processed {i+1:,} / {sample_size:,} texts...")

# Save vocabulary
vocab_file = text_dir / "twi_vocab.txt"
with open(vocab_file, 'w', encoding='utf-8') as f:
    for word, count in vocab.most_common(50000):
        f.write(f"{word}\t{count}\n")

print(f"\n[SAVED] Vocabulary: {len(vocab):,} unique words (top 50K saved)")

# Create character-level vocabulary
print("\nBuilding character vocabulary...")
char_vocab = Counter()

for text in twi_texts.head(100000):
    if isinstance(text, str):
        char_vocab.update(text)

# Save character vocabulary
char_vocab_file = text_dir / "twi_char_vocab.txt"
with open(char_vocab_file, 'w', encoding='utf-8') as f:
    for char, count in char_vocab.most_common():
        if char.strip():  # Skip whitespace
            f.write(f"{char}\t{count}\n")

print(f"[SAVED] Character vocabulary: {len(char_vocab)} unique characters")

# Save statistics
print("\nSaving statistics...")
stats = {
    "total_pairs": len(df_pairs),
    "high_quality_pairs": len(high_quality),
    "train_size": len(train),
    "val_size": len(val),
    "test_size": len(test),
    "vocab_size": len(vocab),
    "char_vocab_size": len(char_vocab),
    "processing_date": pd.Timestamp.now().isoformat(),
    "twi_column_used": twi_column
}

stats_file = text_dir / "statistics.json"
with open(stats_file, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

print("[SAVED] statistics.json")

# Create a summary report
print("\n" + "=" * 50)
print("PROCESSING COMPLETE!")
print("=" * 50)

print(f"\nData location: {PROCESSED_DIR}")
print("\nDataset Statistics:")
print("-" * 30)
for key, value in stats.items():
    if isinstance(value, int):
        print(f"  {key}: {value:,}")
    elif key == "processing_date":
        print(f"  {key}: {value}")

print("\nFiles Created:")
print("-" * 30)
print(f"  {text_dir}/")
print(f"    - train_pairs.parquet ({len(train):,} pairs)")
print(f"    - val_pairs.parquet ({len(val):,} pairs)")
print(f"    - test_pairs.parquet ({len(test):,} pairs)")
print(f"    - train_sample.csv (1000 samples)")
print(f"    - val_sample.csv (100 samples)")
print(f"    - test_sample.csv (100 samples)")
print(f"    - twi_vocab.txt ({min(50000, len(vocab)):,} words)")
print(f"    - twi_char_vocab.txt ({len(char_vocab)} chars)")
print(f"    - statistics.json")

print("\nNext Steps:")
print("-" * 30)
print("1. Process audio data from Financial Inclusion dataset")
print("2. Extract JW300 and Common Voice archives")
print("3. Upload to Google Colab for model training")
print("4. Train translation model with these pairs")
print("5. Fine-tune ASR/TTS models with audio data")

print("\n[SUCCESS] Ready for model training!")