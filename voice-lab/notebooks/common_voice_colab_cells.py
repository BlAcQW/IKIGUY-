# ============================================================================
# GOOGLE COLAB NOTEBOOK CELLS FOR COMMON VOICE TWI WITH AUDIO
# Copy these cells into your Google Colab notebook
# ============================================================================

# %%
# CELL 1: Setup and Authentication
!pip install -q datasets soundfile librosa
!huggingface-cli login --token YOUR_HF_TOKEN_HERE  # Replace with your token

# %%
# CELL 2: Import libraries
from datasets import load_dataset, Audio
import soundfile as sf
import pandas as pd
from pathlib import Path
from tqdm.auto import tqdm
import numpy as np
import librosa

# For Google Colab
from google.colab import drive
drive.mount('/content/drive')

# %%
# CELL 3: Quick Test - Stream a Few Samples with Audio
"""
Quick test to verify Common Voice audio is working
"""

# Stream a few samples to test
print("Testing Common Voice Twi audio streaming...")

dataset = load_dataset(
    "mozilla-foundation/common_voice_17_0",
    "tw",
    split="train",
    streaming=True,
    token=True
)

# Get 5 samples
samples = []
for i, sample in enumerate(dataset):
    if i >= 5:
        break
    
    print(f"\nSample {i+1}:")
    print(f"  Text: {sample['sentence'][:50]}...")
    print(f"  Audio shape: {sample['audio']['array'].shape}")
    print(f"  Sampling rate: {sample['audio']['sampling_rate']} Hz")
    
    samples.append(sample)

print("\n✅ Audio streaming is working!")

# %%
# CELL 4: Download Common Voice Twi Dataset with Audio (Full Download)
"""
Download the complete Common Voice Twi dataset with audio files
This will take time and storage space!
"""

# Set output directory in Google Drive
output_dir = Path('/content/drive/MyDrive/voice-lab-data/raw/common_voice_audio')
output_dir.mkdir(parents=True, exist_ok=True)

# Download all splits
splits = ['train', 'validation', 'test']
cv_datasets = {}

for split in splits:
    print(f"\n📥 Downloading {split} split...")
    
    # Download with audio
    dataset = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "tw",
        split=split,
        token=True
    )
    
    cv_datasets[split] = dataset
    
    # Save to disk
    save_path = output_dir / split
    dataset.save_to_disk(str(save_path))
    
    print(f"✅ {split}: {len(dataset)} samples saved to {save_path}")

print(f"\n✅ Total samples downloaded: {sum(len(ds) for ds in cv_datasets.values())}")

# %%
# CELL 5: Process and Convert Audio to WAV Files
"""
Convert Common Voice audio to WAV files for processing
"""

# Process train split as example
train_dataset = cv_datasets['train']

# Output directory for WAV files
wav_dir = output_dir / 'wav_files' / 'train'
wav_dir.mkdir(parents=True, exist_ok=True)

# Process first 100 samples (adjust as needed)
num_samples = min(100, len(train_dataset))
metadata = []

print(f"Converting {num_samples} samples to WAV...")

for i in tqdm(range(num_samples)):
    sample = train_dataset[i]
    
    # Get audio and text
    audio_array = sample['audio']['array']
    sampling_rate = sample['audio']['sampling_rate']
    text = sample['sentence']
    
    # Save as WAV
    wav_path = wav_dir / f"cv_tw_{i:06d}.wav"
    sf.write(wav_path, audio_array, sampling_rate)
    
    # Save metadata
    metadata.append({
        'file': wav_path.name,
        'text': text,
        'duration': len(audio_array) / sampling_rate,
        'sampling_rate': sampling_rate,
        'client_id': sample.get('client_id', ''),
        'age': sample.get('age', ''),
        'gender': sample.get('gender', ''),
        'accent': sample.get('accent', '')
    })

# Save metadata
metadata_df = pd.DataFrame(metadata)
metadata_df.to_csv(wav_dir.parent / 'train_metadata.csv', index=False)

print(f"✅ Converted {num_samples} audio files")
print(f"📁 WAV files: {wav_dir}")
print(f"📊 Metadata: {wav_dir.parent / 'train_metadata.csv'}")

# %%
# CELL 6: Stream and Process Without Full Download (Memory Efficient)
"""
Stream Common Voice and process samples without downloading everything
Good for limited storage or quick experiments
"""

# Output directory
stream_output = Path('/content/drive/MyDrive/voice-lab-data/raw/common_voice_streamed')
stream_output.mkdir(parents=True, exist_ok=True)

# Stream dataset
dataset = load_dataset(
    "mozilla-foundation/common_voice_17_0",
    "tw",
    split="train",
    streaming=True,
    token=True
)

# Process samples
max_samples = 500  # Adjust as needed
processed_samples = []

print(f"Streaming and processing {max_samples} samples...")

for idx, sample in enumerate(tqdm(dataset, total=max_samples)):
    if idx >= max_samples:
        break
    
    # Get audio
    audio_array = sample['audio']['array']
    sampling_rate = sample['audio']['sampling_rate']
    
    # Resample to 16kHz for ASR
    if sampling_rate != 16000:
        audio_array = librosa.resample(
            audio_array,
            orig_sr=sampling_rate,
            target_sr=16000
        )
        sampling_rate = 16000
    
    # Save audio
    audio_path = stream_output / 'audio' / f"sample_{idx:06d}.wav"
    audio_path.parent.mkdir(exist_ok=True)
    sf.write(audio_path, audio_array, sampling_rate)
    
    # Save text
    text_path = stream_output / 'text' / f"sample_{idx:06d}.txt"
    text_path.parent.mkdir(exist_ok=True)
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(sample['sentence'])
    
    # Collect metadata
    processed_samples.append({
        'id': idx,
        'audio_file': audio_path.name,
        'text_file': text_path.name,
        'text': sample['sentence'],
        'duration': len(audio_array) / sampling_rate,
        'gender': sample.get('gender', ''),
        'age': sample.get('age', ''),
        'accent': sample.get('accent', '')
    })

# Save metadata
metadata_df = pd.DataFrame(processed_samples)
metadata_df.to_csv(stream_output / 'metadata.csv', index=False)

print(f"\n✅ Processed {len(processed_samples)} samples")
print(f"📁 Output directory: {stream_output}")
print(f"📊 Total duration: {metadata_df['duration'].sum()/60:.2f} minutes")

# %%
# CELL 7: Load Previously Downloaded Dataset
"""
Load Common Voice dataset if already downloaded
"""

# Path to saved dataset
saved_path = Path('/content/drive/MyDrive/voice-lab-data/raw/common_voice_audio/train')

if saved_path.exists():
    from datasets import load_from_disk
    
    # Load from disk
    dataset = load_from_disk(str(saved_path))
    
    print(f"✅ Loaded {len(dataset)} samples from disk")
    
    # Show sample
    sample = dataset[0]
    print(f"\nSample:")
    print(f"  Text: {sample['sentence'][:100]}...")
    print(f"  Audio available: {'audio' in sample}")
    
    if 'audio' in sample:
        print(f"  Audio shape: {sample['audio']['array'].shape}")
        print(f"  Sampling rate: {sample['audio']['sampling_rate']}")
else:
    print(f"❌ Dataset not found at {saved_path}")
    print("Run the download cells first!")

# %%
# CELL 8: Integrate with Your Processing Pipeline
"""
Example of integrating Common Voice with your existing processing pipeline
"""

from pathlib import Path

# Your existing processing function
def process_common_voice_for_training():
    """Process Common Voice audio for ASR training"""
    
    # Load dataset
    dataset = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "tw",
        split="train",
        streaming=True,  # or False for full download
        token=True
    )
    
    all_samples = []
    
    for i, sample in enumerate(tqdm(dataset, desc="Processing Common Voice")):
        if i >= 1000:  # Limit for demo
            break
        
        # Extract audio and text
        audio = sample['audio']['array']
        sr = sample['audio']['sampling_rate']
        text = sample['sentence']
        
        # Resample to 16kHz if needed
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        # Add to your training data format
        all_samples.append({
            'audio': audio,
            'text': text,
            'sampling_rate': sr,
            'dataset': 'common_voice',
            'language': 'twi',
            'speaker_id': sample.get('client_id', 'unknown'),
            'gender': sample.get('gender', ''),
            'age': sample.get('age', ''),
            'accent': sample.get('accent', '')
        })
    
    print(f"✅ Processed {len(all_samples)} Common Voice samples")
    return all_samples

# Run processing
cv_samples = process_common_voice_for_training()

# Add to your existing all_samples list
# all_samples.extend(cv_samples)