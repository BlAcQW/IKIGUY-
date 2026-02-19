#!/usr/bin/env python3
"""
Prepare FULL Twi dataset for MeloTTS training
- Resample 16kHz → 44.1kHz
- Create metadata.list in MeloTTS format
- Process all available samples (100K train + 2K val)
"""

import os
import pandas as pd
import torchaudio
from pathlib import Path
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SOURCE_MANIFEST = "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/melo_tts_train.csv"
VAL_MANIFEST = "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/melo_tts_val.csv"
OUTPUT_DIR = "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/melo_tts_44k_full"
METADATA_OUTPUT = "/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full/metadata.list"

TARGET_SR = 44100
SOURCE_SR = 22050  # Full dataset is 22.05kHz (not 16kHz)

# Number of samples to use - can adjust based on needs
# Set to None to use ALL available samples (212K train + 11K val)
NUM_TRAIN_SAMPLES = None  # Use ALL 212K samples (or set to 50000, 100000, etc.)
NUM_VAL_SAMPLES = None    # Use ALL 11K validation samples

def resample_and_copy(source_path, target_path, source_sr=22050, target_sr=44100):
    """Resample audio file from source_sr to target_sr"""
    try:
        # Load audio
        audio, sr = torchaudio.load(source_path)

        # Verify source sample rate
        if sr != source_sr:
            logger.warning(f"Expected {source_sr}Hz, got {sr}Hz for {source_path}")

        # Resample to 44.1kHz
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(sr, target_sr)
            audio = resampler(audio)

        # Convert to mono if stereo
        if audio.shape[0] > 1:
            audio = audio.mean(dim=0, keepdim=True)

        # Save resampled audio
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        torchaudio.save(target_path, audio, target_sr)

        return True
    except Exception as e:
        logger.error(f"Error processing {source_path}: {e}")
        return False

def create_metadata_list(manifest_csv, output_wavs_dir, num_samples, split_name="train"):
    """
    Create MeloTTS metadata.list from CSV manifest
    Format: path/to/audio.wav|<speaker_name>|<language_code>|<text>
    """
    logger.info(f"Loading {split_name} manifest: {manifest_csv}")
    df = pd.read_csv(manifest_csv)

    if num_samples is not None:
        df = df.head(num_samples)

    logger.info(f"Processing {len(df)} {split_name} samples...")

    metadata_entries = []
    successful = 0
    failed = 0

    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {split_name}"):
        source_audio = row['audio_path']
        text = row['text']

        # Create output path with absolute path
        filename = f"{split_name}_{idx:06d}.wav"
        target_audio = os.path.join(output_wavs_dir, filename)

        # Resample and save
        if resample_and_copy(source_audio, target_audio, SOURCE_SR, TARGET_SR):
            # MeloTTS format with absolute path: audio_path|speaker|language|text
            metadata_entry = f"{target_audio}|TWI-Speaker|EN|{text}"
            metadata_entries.append(metadata_entry)
            successful += 1
        else:
            failed += 1

    logger.info(f"{split_name}: Successfully processed {successful}/{len(df)} files ({failed} failed)")

    return metadata_entries

def main():
    """Main preparation function"""

    logger.info("=" * 80)
    logger.info("Preparing FULL Twi Dataset for MeloTTS Training")
    logger.info("=" * 80)
    logger.info(f"Source sample rate: {SOURCE_SR}Hz")
    logger.info(f"Target sample rate: {TARGET_SR}Hz")
    logger.info(f"Train samples: {NUM_TRAIN_SAMPLES if NUM_TRAIN_SAMPLES else 'ALL'}")
    logger.info(f"Val samples: {NUM_VAL_SAMPLES if NUM_VAL_SAMPLES else 'ALL'}")
    logger.info("=" * 80)

    # Create output directories
    train_wavs_dir = os.path.join(OUTPUT_DIR, "train_wavs")
    val_wavs_dir = os.path.join(OUTPUT_DIR, "val_wavs")
    os.makedirs(train_wavs_dir, exist_ok=True)
    os.makedirs(val_wavs_dir, exist_ok=True)

    # Create metadata directory
    os.makedirs(os.path.dirname(METADATA_OUTPUT), exist_ok=True)

    # Process training data
    logger.info("\n📊 Processing TRAINING data...")
    train_metadata = create_metadata_list(
        SOURCE_MANIFEST,
        train_wavs_dir,
        NUM_TRAIN_SAMPLES,
        "train"
    )

    # Process validation data
    logger.info("\n📊 Processing VALIDATION data...")
    val_metadata = create_metadata_list(
        VAL_MANIFEST,
        val_wavs_dir,
        NUM_VAL_SAMPLES,
        "val"
    )

    # Combine and save metadata
    all_metadata = train_metadata + val_metadata

    logger.info(f"\n💾 Saving metadata to: {METADATA_OUTPUT}")
    with open(METADATA_OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_metadata))

    logger.info("\n" + "=" * 80)
    logger.info("✅ Dataset preparation complete!")
    logger.info(f"📁 Audio files: {OUTPUT_DIR}")
    logger.info(f"📄 Metadata: {METADATA_OUTPUT}")
    logger.info(f"📊 Total samples: {len(all_metadata):,}")
    logger.info(f"📊 Training: {len(train_metadata):,}")
    logger.info(f"📊 Validation: {len(val_metadata):,}")
    logger.info("=" * 80)
    logger.info("\n🚀 Next steps:")
    logger.info("1. cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo")
    logger.info("2. python preprocess_text.py --metadata data/twi_full/metadata.list --clean")
    logger.info("3. Update train/val lists")
    logger.info("4. bash train.sh data/twi_full/config.json 1")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
