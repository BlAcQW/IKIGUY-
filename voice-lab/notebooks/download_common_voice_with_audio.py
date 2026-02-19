"""
Download Common Voice Twi dataset WITH AUDIO FILES
Two methods provided: Direct download or HuggingFace streaming
"""

import os
import sys
from pathlib import Path
from datasets import load_dataset, Audio
import pandas as pd
from tqdm import tqdm
import soundfile as sf
import numpy as np

# ==============================================================================
# METHOD 1: Download Full Common Voice Dataset with Audio using HuggingFace
# ==============================================================================

def download_common_voice_full(output_dir="./common_voice_twi_full"):
    """
    Download the complete Common Voice Twi dataset with audio files.
    This will download all audio files locally.
    
    Requirements:
    1. HuggingFace account
    2. Accept dataset terms at: https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0
    3. Login: huggingface-cli login
    """
    
    print("=" * 60)
    print("DOWNLOADING COMMON VOICE TWI WITH AUDIO")
    print("=" * 60)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download all splits with audio
        print("\nDownloading Common Voice 17.0 Twi dataset...")
        print("This will download audio files - may take a while!")
        
        splits_to_download = {
            'train': None,
            'validation': None,
            'test': None
        }
        
        for split_name in splits_to_download.keys():
            print(f"\n📥 Downloading {split_name} split...")
            
            # Load with audio files
            dataset = load_dataset(
                "mozilla-foundation/common_voice_17_0",
                "tw",  # Twi language code
                split=split_name,
                token=True,  # Use your HF token
                trust_remote_code=True
            )
            
            splits_to_download[split_name] = dataset
            
            print(f"  ✓ {split_name}: {len(dataset)} samples")
            
            # Save to disk for offline use
            save_path = output_path / split_name
            dataset.save_to_disk(str(save_path))
            print(f"  💾 Saved to {save_path}")
            
            # Save some audio files as WAV for verification
            samples_dir = output_path / f"{split_name}_samples"
            samples_dir.mkdir(exist_ok=True)
            
            print(f"  🎵 Extracting sample audio files...")
            for i in range(min(10, len(dataset))):
                sample = dataset[i]
                
                # Audio is in sample['audio'] with 'array' and 'sampling_rate'
                audio_array = sample['audio']['array']
                sampling_rate = sample['audio']['sampling_rate']
                
                # Save as WAV
                wav_path = samples_dir / f"sample_{i:04d}.wav"
                sf.write(wav_path, audio_array, sampling_rate)
                
                # Save corresponding text
                text_path = samples_dir / f"sample_{i:04d}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(sample['sentence'])
            
            print(f"  ✓ Saved {min(10, len(dataset))} sample files to {samples_dir}")
        
        # Create summary
        total_samples = sum(len(ds) for ds in splits_to_download.values())
        
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE!")
        print("=" * 60)
        print(f"Total samples: {total_samples:,}")
        print(f"Location: {output_path}")
        print("\nSplits:")
        for split, dataset in splits_to_download.items():
            print(f"  - {split}: {len(dataset):,} samples")
        
        return splits_to_download
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in: huggingface-cli login")
        print("2. Accept dataset terms at: https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0")
        print("3. Check your internet connection")
        return None


# ==============================================================================
# METHOD 2: Stream Common Voice with Audio (No Full Download)
# ==============================================================================

def stream_common_voice_audio(max_samples=100, output_dir="./common_voice_stream"):
    """
    Stream Common Voice Twi dataset without downloading everything.
    Good for processing samples on-the-fly or limited storage.
    """
    
    print("=" * 60)
    print("STREAMING COMMON VOICE TWI WITH AUDIO")
    print("=" * 60)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Stream the dataset
        print("\n🌐 Streaming Common Voice dataset...")
        dataset = load_dataset(
            "mozilla-foundation/common_voice_17_0",
            "tw",
            split="train",
            streaming=True,  # Enable streaming
            token=True,
            trust_remote_code=True
        )
        
        # Process streamed samples
        samples_processed = []
        audio_dir = output_path / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        print(f"\n📡 Processing up to {max_samples} samples...")
        
        for idx, sample in enumerate(tqdm(dataset, total=max_samples)):
            if idx >= max_samples:
                break
            
            # Extract audio and text
            audio_array = sample['audio']['array']
            sampling_rate = sample['audio']['sampling_rate']
            text = sample['sentence']
            
            # Save audio as WAV
            audio_path = audio_dir / f"cv_tw_{idx:05d}.wav"
            sf.write(audio_path, audio_array, sampling_rate)
            
            # Store metadata
            samples_processed.append({
                'id': idx,
                'audio_path': str(audio_path),
                'text': text,
                'sampling_rate': sampling_rate,
                'duration': len(audio_array) / sampling_rate,
                'client_id': sample.get('client_id', ''),
                'age': sample.get('age', ''),
                'gender': sample.get('gender', ''),
                'accent': sample.get('accent', '')
            })
        
        # Save metadata
        df = pd.DataFrame(samples_processed)
        metadata_path = output_path / "metadata.csv"
        df.to_csv(metadata_path, index=False, encoding='utf-8')
        
        print(f"\n✅ Processed {len(samples_processed)} samples")
        print(f"📁 Audio files: {audio_dir}")
        print(f"📊 Metadata: {metadata_path}")
        
        # Show statistics
        print("\n📈 Statistics:")
        print(f"  Average duration: {df['duration'].mean():.2f} seconds")
        print(f"  Total duration: {df['duration'].sum() / 60:.2f} minutes")
        if 'gender' in df.columns:
            print(f"  Gender distribution: {df['gender'].value_counts().to_dict()}")
        
        return df
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in: huggingface-cli login")
        print("2. Accept dataset terms")
        print("3. Check your internet connection")
        return None


# ==============================================================================
# METHOD 3: Process Existing Dataset from HuggingFace Cache
# ==============================================================================

def load_from_cache(cache_dir=None):
    """
    Load Common Voice from HuggingFace cache if already downloaded.
    """
    
    print("=" * 60)
    print("LOADING COMMON VOICE FROM CACHE")
    print("=" * 60)
    
    try:
        # Try to load from cache
        dataset = load_dataset(
            "mozilla-foundation/common_voice_17_0",
            "tw",
            split="train",
            token=True,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        
        print(f"✅ Loaded {len(dataset)} samples from cache")
        
        # Show sample
        sample = dataset[0]
        print(f"\nSample:")
        print(f"  Text: {sample['sentence'][:100]}...")
        print(f"  Audio shape: {sample['audio']['array'].shape}")
        print(f"  Sampling rate: {sample['audio']['sampling_rate']}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Could not load from cache: {e}")
        return None


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("Common Voice Twi Audio Download Options")
    print("=" * 60)
    print("1. Download full dataset (requires more storage)")
    print("2. Stream samples (no full download)")
    print("3. Load from cache (if previously downloaded)")
    print()
    
    # Check for command line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        # Full download
        print("\n📥 FULL DOWNLOAD SELECTED")
        print("Note: This will download the complete dataset with audio files.")
        print("Storage required: Several GB")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm == 'y':
            datasets = download_common_voice_full()
            if datasets:
                print("\n✅ Success! You can now use the downloaded dataset offline.")
        
    elif choice == "2":
        # Streaming
        print("\n📡 STREAMING SELECTED")
        num_samples = input("How many samples to process? (default 100): ").strip()
        num_samples = int(num_samples) if num_samples else 100
        
        df = stream_common_voice_audio(max_samples=num_samples)
        if df is not None:
            print("\n✅ Success! Audio files and metadata saved.")
    
    elif choice == "3":
        # Load from cache
        print("\n💾 LOADING FROM CACHE")
        dataset = load_from_cache()
        if dataset:
            print("\n✅ Successfully loaded from cache!")
    
    else:
        print("Invalid choice. Please run again with option 1, 2, or 3.")
    
    print("\n" + "=" * 60)
    print("IMPORTANT NOTES:")
    print("=" * 60)
    print("1. You must be logged in to HuggingFace: huggingface-cli login")
    print("2. Accept terms at: https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0")
    print("3. The dataset includes audio arrays and metadata")
    print("4. Audio is provided at original sampling rate (usually 48kHz)")
    print("5. You may need to resample to 16kHz for ASR training")