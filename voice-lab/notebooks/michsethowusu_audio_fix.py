"""
Fix for MichSetHowusu audio decoding in Google Colab
Add this to your notebook before processing MichSetHowusu datasets
"""

# Install required audio libraries
def install_audio_libraries():
    """Install libraries needed for audio decoding in Colab."""
    import subprocess
    import sys
    
    print("Installing audio decoding libraries...")
    
    # Try different audio libraries
    libraries = [
        'soundfile',
        'librosa',
        'torchaudio',
        'pyaudio'
    ]
    
    for lib in libraries:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', lib])
            print(f"  ✅ Installed {lib}")
        except:
            print(f"  ⚠️ Could not install {lib}")
    
    print("Audio libraries installation complete")


def process_michsethowusu_with_fallback(raw_dir, max_samples=500):
    """
    Process MichSetHowusu datasets with proper error handling.
    
    Args:
        raw_dir: Path to raw data directory
        max_samples: Maximum samples to process per dataset
    
    Returns:
        List of processed samples
    """
    from pathlib import Path
    from datasets import load_dataset, load_from_disk
    from tqdm import tqdm
    import numpy as np
    
    print("\n" + "="*60)
    print("PROCESSING MICHSETHOWUSU DATASETS (WITH AUDIO FIX)")
    print("="*60)
    
    michset_samples = []
    
    # MichSetHowusu datasets
    michset_configs = [
        {
            'name': 'twi_multispeaker_audio_transcribed',
            'hf_path': 'michsethowusu/twi_multispeaker_audio_transcribed',
            'language': 'twi'
        },
        {
            'name': 'akuapem_multispeaker_audio_transcribed',
            'hf_path': 'michsethowusu/akuapem_multispeaker_audio_transcribed',
            'language': 'akuapem_twi'
        },
        {
            'name': 'fante_multispeaker_audio_transcribed',
            'hf_path': 'michsethowusu/fante_multispeaker_audio_transcribed',
            'language': 'fante'
        }
    ]
    
    for config in michset_configs:
        print(f"\n📁 Processing {config['name']}...")
        dataset = None
        
        # Method 1: Try local Arrow files first
        local_path = Path(raw_dir) / 'michsethowusu' / config['name'] / 'train'
        if local_path.exists():
            try:
                print(f"  Loading from local Arrow files...")
                dataset = load_from_disk(str(local_path))
                print(f"  ✅ Loaded {len(dataset)} samples from local files")
            except Exception as e:
                print(f"  ⚠️ Could not load local files: {e}")
        
        # Method 2: Try HuggingFace if local failed
        if dataset is None:
            try:
                print(f"  Downloading from HuggingFace...")
                dataset = load_dataset(config['hf_path'], split="train", token=True)
                print(f"  ✅ Downloaded {len(dataset)} samples")
            except Exception as e:
                print(f"  ⚠️ Could not download: {e}")
                continue
        
        # Process the dataset
        if dataset:
            # Check dataset structure
            print(f"  Features: {list(dataset.features.keys())}")
            
            # Determine column names
            text_col = None
            audio_col = None
            
            # Common column name variations
            text_candidates = ['text', 'transcription', 'sentence', 'transcript']
            audio_candidates = ['audio', 'audio_path', 'path', 'file']
            
            for col in text_candidates:
                if col in dataset.features:
                    text_col = col
                    break
            
            for col in audio_candidates:
                if col in dataset.features:
                    audio_col = col
                    break
            
            print(f"  Text column: {text_col}, Audio column: {audio_col}")
            
            # Process samples
            samples_to_process = min(max_samples, len(dataset))
            successful = 0
            
            for i in tqdm(range(samples_to_process), 
                         desc=f"Processing {config['name']}"):
                try:
                    sample = dataset[i]
                    
                    # Get text
                    text = sample.get(text_col, '') if text_col else ''
                    
                    # Handle audio based on type
                    audio_data = sample.get(audio_col) if audio_col else None
                    
                    if audio_data:
                        # Case 1: Audio is already an array with metadata
                        if isinstance(audio_data, dict) and 'array' in audio_data:
                            audio_array = audio_data['array']
                            sampling_rate = audio_data.get('sampling_rate', 16000)
                            
                            michset_samples.append({
                                'audio': audio_array,
                                'text': text,
                                'sampling_rate': sampling_rate,
                                'language': config['language'],
                                'dataset': config['name'],
                                'has_audio': True
                            })
                            successful += 1
                            
                        # Case 2: Audio is a file path
                        elif isinstance(audio_data, str):
                            # Store path for later processing
                            michset_samples.append({
                                'audio_path': audio_data,
                                'text': text,
                                'language': config['language'],
                                'dataset': config['name'],
                                'has_audio': False,
                                'needs_loading': True
                            })
                            successful += 1
                            
                        # Case 3: Audio is a numpy array
                        elif isinstance(audio_data, (list, np.ndarray)):
                            michset_samples.append({
                                'audio': np.array(audio_data),
                                'text': text,
                                'sampling_rate': 16000,  # Assume 16kHz
                                'language': config['language'],
                                'dataset': config['name'],
                                'has_audio': True
                            })
                            successful += 1
                    else:
                        # No audio data, just save text
                        if text:
                            michset_samples.append({
                                'text': text,
                                'language': config['language'],
                                'dataset': config['name'],
                                'has_audio': False
                            })
                            
                except Exception as e:
                    # Skip problematic samples
                    continue
            
            print(f"  ✅ Successfully processed {successful}/{samples_to_process} samples")
    
    # Summary
    print(f"\n" + "="*60)
    print(f"MICHSETHOWUSU PROCESSING COMPLETE")
    print(f"="*60)
    print(f"Total samples extracted: {len(michset_samples)}")
    
    # Statistics
    with_audio = sum(1 for s in michset_samples if s.get('has_audio', False))
    needs_loading = sum(1 for s in michset_samples if s.get('needs_loading', False))
    text_only = len(michset_samples) - with_audio - needs_loading
    
    print(f"  - With audio arrays: {with_audio}")
    print(f"  - With audio paths (need loading): {needs_loading}")
    print(f"  - Text only: {text_only}")
    
    # Language distribution
    languages = {}
    for s in michset_samples:
        lang = s.get('language', 'unknown')
        languages[lang] = languages.get(lang, 0) + 1
    
    print(f"\nLanguage distribution:")
    for lang, count in languages.items():
        print(f"  - {lang}: {count} samples")
    
    return michset_samples


# For use in Colab notebook
if __name__ == "__main__":
    # Example usage
    import os
    
    # Install libraries
    install_audio_libraries()
    
    # Set paths
    if os.path.exists('/content/drive/MyDrive/voice-lab-data/raw'):
        raw_dir = '/content/drive/MyDrive/voice-lab-data/raw'
    else:
        raw_dir = './data/raw'
    
    # Process datasets
    samples = process_michsethowusu_with_fallback(raw_dir, max_samples=100)
    
    print(f"\n✅ Ready to use {len(samples)} MichSetHowusu samples!")