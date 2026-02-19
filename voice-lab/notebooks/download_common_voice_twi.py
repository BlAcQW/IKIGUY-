"""
Download Mozilla Common Voice 17.0 Twi dataset
"""

from datasets import load_dataset
import pandas as pd
from pathlib import Path

# Method 1: Direct download with authentication
def download_common_voice_twi():
    """Download Common Voice Twi dataset."""
    
    print("Downloading Common Voice 17.0 Twi dataset...")
    
    # Load the dataset - requires HuggingFace login
    # Run first: huggingface-cli login
    dataset = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "tw",  # Twi language code
        cache_dir="./cv_cache",
        token=True  # Uses your HF token
    )
    
    print(f"Dataset splits:")
    for split in dataset.keys():
        print(f"  {split}: {len(dataset[split])} samples")
    
    # Save locally
    dataset.save_to_disk("./common_voice_twi")
    
    # Extract some samples to check
    train_df = dataset['train'].to_pandas()
    print(f"\nSample data:")
    print(train_df[['sentence', 'path']].head())
    
    return dataset

# Method 2: Stream to avoid large download
def stream_common_voice_twi():
    """Stream Common Voice Twi for exploration."""
    
    from datasets import load_dataset
    
    # Use streaming to explore without downloading everything
    dataset = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "tw",
        split="train",
        streaming=True,
        token=True
    )
    
    # Get first 100 samples
    samples = []
    for i, sample in enumerate(dataset):
        if i >= 100:
            break
        samples.append({
            'text': sample['sentence'],
            'audio_path': sample['path'],
            'age': sample.get('age', ''),
            'gender': sample.get('gender', ''),
            'accent': sample.get('accent', '')
        })
    
    df = pd.DataFrame(samples)
    print(f"Collected {len(df)} samples")
    print(df.head())
    
    return df

if __name__ == "__main__":
    # First login to HuggingFace:
    # Run in terminal: huggingface-cli login
    
    # Then download
    try:
        dataset = download_common_voice_twi()
        print("✅ Download complete!")
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying streaming mode...")
        df = stream_common_voice_twi()