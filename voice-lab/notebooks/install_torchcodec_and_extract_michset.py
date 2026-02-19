#!/usr/bin/env python
"""
Install torchcodec and extract MichSet audio files to Google Drive
This script handles the complete audio extraction pipeline
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import json
import pandas as pd
import numpy as np
from tqdm import tqdm

def install_torchcodec():
    """Install torchcodec with multiple fallback methods."""
    print("🔧 Installing torchcodec...")
    print("=" * 50)
    
    # Method 1: pip install
    try:
        print("Trying pip install...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "torchcodec"], 
                              capture_output=True, text=True, check=True)
        print("✅ torchcodec installed via pip!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pip install failed: {e.stderr}")
    
    # Method 2: conda install
    try:
        print("Trying conda install...")
        result = subprocess.run(["conda", "install", "-y", "-c", "conda-forge", "torchcodec"], 
                              capture_output=True, text=True, check=True)
        print("✅ torchcodec installed via conda!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Conda install failed: {e}")
    
    # Method 3: pip with --upgrade
    try:
        print("Trying pip install with upgrade...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "torchcodec"], 
                              capture_output=True, text=True, check=True)
        print("✅ torchcodec installed with upgrade!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pip upgrade failed: {e.stderr}")
    
    # Method 4: Install dependencies and try again
    try:
        print("Installing dependencies first...")
        deps = ["torch", "torchaudio", "datasets", "librosa", "soundfile"]
        for dep in deps:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", dep], 
                         capture_output=True, text=True, check=True)
        
        # Try torchcodec again
        result = subprocess.run([sys.executable, "-m", "pip", "install", "torchcodec"], 
                              capture_output=True, text=True, check=True)
        print("✅ torchcodec installed after dependency update!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation with dependencies failed: {e.stderr}")
    
    print("❌ All installation methods failed!")
    return False

def verify_installation():
    """Verify torchcodec installation."""
    print("\n🔍 Verifying torchcodec installation...")
    try:
        import torchcodec
        print(f"✅ torchcodec successfully imported: {torchcodec.__version__}")
        return True
    except ImportError as e:
        print(f"❌ torchcodec import failed: {e}")
        return False

def install_required_packages():
    """Install all required packages for audio processing."""
    print("\n📦 Installing required packages...")
    
    packages = [
        "torch", 
        "torchaudio",
        "datasets",
        "librosa",
        "soundfile", 
        "tqdm",
        "pandas",
        "numpy"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package], 
                         capture_output=True, text=True, check=True)
            print(f"  ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ {package} installation failed: {e.stderr[:100]}")
    
    print("✅ Package installation complete!")

def extract_michset_audio():
    """Extract audio from MichSet Arrow datasets."""
    print("\n🎵 MICHSET AUDIO EXTRACTION")
    print("=" * 50)
    
    # Import required libraries
    try:
        import torchcodec
        import torch
        import librosa
        import soundfile as sf
        from datasets import load_from_disk
        print("✅ All required libraries imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Setup paths
    BASE_DIR = Path("G:/My Drive/voice-lab-data")
    MICHSET_DIR = BASE_DIR / "raw" / "michsethowusu"
    OUTPUT_DIR = BASE_DIR / "processed" / "michset_audio_extracted"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Base directory: {BASE_DIR}")
    print(f"MichSet directory: {MICHSET_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Define datasets to process
    datasets_to_process = [
        ("twi_multispeaker_audio_transcribed", "twi"),
        ("akuapem_multispeaker_audio_transcribed", "akuapem_twi"),
        ("fante_multispeaker_audio_transcribed", "fante")
    ]
    
    extraction_results = {}
    total_extracted = 0
    
    for dataset_name, dialect in datasets_to_process:
        dataset_path = MICHSET_DIR / dataset_name
        
        print(f"\n🎯 Processing {dataset_name}...")
        print(f"Path: {dataset_path}")
        print(f"Exists: {dataset_path.exists()}")
        
        if not dataset_path.exists():
            print(f"❌ Dataset not found: {dataset_name}")
            extraction_results[dataset_name] = {"status": "missing", "extracted": 0}
            continue
        
        try:
            # Load dataset
            print("  Loading dataset...")
            dataset = load_from_disk(str(dataset_path))
            
            if 'train' not in dataset:
                print("  ❌ No training split found")
                extraction_results[dataset_name] = {"status": "no_train", "extracted": 0}
                continue
            
            train_data = dataset['train']
            total_samples = len(train_data)
            max_samples = min(1000, total_samples)  # Limit for processing speed
            
            print(f"  📊 Dataset info:")
            print(f"    Total samples: {total_samples}")
            print(f"    Processing: {max_samples}")
            print(f"    Features: {train_data.features}")
            
            # Create output directory for this dataset
            dataset_output_dir = OUTPUT_DIR / dataset_name
            dataset_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract audio files
            extracted_files = []
            failed_count = 0
            
            print(f"  🔄 Extracting audio files...")
            
            for i in tqdm(range(max_samples), desc=f"Extracting {dataset_name}"):
                try:
                    sample = train_data[i]
                    
                    # Get audio data
                    audio_data = None
                    sample_rate = 16000
                    
                    if 'audio' in sample:
                        audio_info = sample['audio']
                        if isinstance(audio_info, dict):
                            if 'array' in audio_info:
                                audio_data = audio_info['array']
                                sample_rate = audio_info.get('sampling_rate', 16000)
                            elif 'path' in audio_info:
                                # Try to load from path
                                audio_path = audio_info['path']
                                try:
                                    audio_data, sample_rate = librosa.load(audio_path, sr=16000)
                                except:
                                    continue
                        else:
                            # Direct audio array
                            audio_data = audio_info
                    
                    elif 'audio_path' in sample:
                        # Try to load from audio_path
                        audio_path = sample['audio_path']
                        try:
                            audio_data, sample_rate = librosa.load(audio_path, sr=16000)
                        except:
                            continue
                    
                    if audio_data is None:
                        failed_count += 1
                        continue
                    
                    # Get transcription
                    transcription = sample.get('transcription', '').strip()
                    if len(transcription) == 0:
                        failed_count += 1
                        continue
                    
                    # Convert to numpy array
                    if not isinstance(audio_data, np.ndarray):
                        audio_data = np.array(audio_data, dtype=np.float32)
                    
                    # Resample if needed
                    if sample_rate != 16000:
                        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
                        sample_rate = 16000
                    
                    # Quality checks
                    duration = len(audio_data) / sample_rate
                    if duration < 0.5 or duration > 15.0:
                        failed_count += 1
                        continue
                    
                    if np.max(np.abs(audio_data)) < 0.01:  # Silent audio
                        failed_count += 1
                        continue
                    
                    # Save audio file
                    output_filename = f"{dataset_name}_{i:05d}.wav"
                    output_path = dataset_output_dir / output_filename
                    
                    # Save with soundfile
                    sf.write(str(output_path), audio_data, sample_rate)
                    
                    # Store metadata
                    extracted_files.append({
                        'audio_file': str(output_path),
                        'transcription': transcription,
                        'duration': duration,
                        'sample_rate': sample_rate,
                        'original_index': i,
                        'dataset': dataset_name,
                        'dialect': dialect
                    })
                    
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:  # Only print first few errors
                        print(f"    Error at sample {i}: {str(e)[:50]}")
                    continue
            
            # Save metadata
            if extracted_files:
                # Save detailed metadata
                metadata_df = pd.DataFrame(extracted_files)
                metadata_csv_path = dataset_output_dir / 'extracted_metadata.csv'
                metadata_df.to_csv(metadata_csv_path, index=False)
                
                # Create TTS-ready metadata.txt (for TTS notebook compatibility)
                tts_metadata_lines = []
                for _, row in metadata_df.iterrows():
                    audio_file = row['audio_file']
                    text = str(row['transcription']).replace('|', '-')  # Remove pipes
                    speaker_id = f"{dataset_name}_speaker"
                    tts_metadata_lines.append(f"{audio_file}|{text}|{speaker_id}")
                
                tts_metadata_path = dataset_output_dir / 'metadata.txt'
                with open(tts_metadata_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(tts_metadata_lines))
                
                # Save extraction summary
                summary = {
                    'dataset_name': dataset_name,
                    'dialect': dialect,
                    'total_samples': total_samples,
                    'processed_samples': max_samples,
                    'extracted_files': len(extracted_files),
                    'failed_extractions': failed_count,
                    'success_rate': len(extracted_files) / max_samples * 100,
                    'avg_duration': metadata_df['duration'].mean(),
                    'total_duration': metadata_df['duration'].sum(),
                    'output_directory': str(dataset_output_dir)
                }
                
                summary_path = dataset_output_dir / 'extraction_summary.json'
                with open(summary_path, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                print(f"  ✅ Extraction complete!")
                print(f"    Extracted: {len(extracted_files)} files")
                print(f"    Failed: {failed_count}")
                print(f"    Success rate: {len(extracted_files)/max_samples*100:.1f}%")
                print(f"    Avg duration: {metadata_df['duration'].mean():.2f}s")
                print(f"    Total audio: {metadata_df['duration'].sum()/60:.1f} minutes")
                
                extraction_results[dataset_name] = {
                    'status': 'success',
                    'extracted': len(extracted_files),
                    'failed': failed_count,
                    'output_dir': str(dataset_output_dir)
                }
                
                total_extracted += len(extracted_files)
                
            else:
                print(f"  ❌ No files extracted from {dataset_name}")
                extraction_results[dataset_name] = {
                    'status': 'no_files',
                    'extracted': 0,
                    'failed': failed_count
                }
                
        except Exception as e:
            print(f"  ❌ Dataset processing failed: {str(e)}")
            extraction_results[dataset_name] = {
                'status': 'error',
                'error': str(e),
                'extracted': 0
            }
    
    return extraction_results, total_extracted

def update_asr_and_tts_paths(extraction_results, total_extracted):
    """Update ASR and TTS data paths with extracted audio."""
    print(f"\n🔄 UPDATING ASR AND TTS DATA PATHS")
    print("=" * 50)
    
    BASE_DIR = Path("G:/My Drive/voice-lab-data")
    SPLITS_DIR = BASE_DIR / 'splits'
    TTS_READY_DIR = BASE_DIR / 'processed' / 'tts_ready'
    EXTRACTED_DIR = BASE_DIR / 'processed' / 'michset_audio_extracted'
    
    if total_extracted == 0:
        print("❌ No audio files extracted - cannot update paths")
        return False
    
    # Create updated ASR splits with real audio paths
    print("📁 Creating ASR splits with real audio paths...")
    
    all_audio_metadata = []
    
    # Collect all extracted metadata
    for dataset_name, result in extraction_results.items():
        if result.get('status') == 'success':
            metadata_file = EXTRACTED_DIR / dataset_name / 'extracted_metadata.csv'
            if metadata_file.exists():
                df = pd.read_csv(metadata_file)
                df['audio'] = df['audio_file']  # Map to expected column name
                df['text'] = df['transcription']  # Map to expected column name
                all_audio_metadata.append(df)
    
    if all_audio_metadata:
        # Combine all metadata
        combined_df = pd.concat(all_audio_metadata, ignore_index=True)
        
        # Shuffle and split
        combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        n_samples = len(combined_df)
        n_train = int(0.8 * n_samples)
        n_val = int(0.1 * n_samples)
        
        train_df = combined_df[:n_train]
        val_df = combined_df[n_train:n_train+n_val]
        test_df = combined_df[n_train+n_val:]
        
        # Save ASR splits
        SPLITS_DIR.mkdir(parents=True, exist_ok=True)
        
        train_df[['audio', 'text', 'dialect', 'duration']].to_csv(
            SPLITS_DIR / 'train.csv', index=False
        )
        val_df[['audio', 'text', 'dialect', 'duration']].to_csv(
            SPLITS_DIR / 'validation.csv', index=False
        )
        test_df[['audio', 'text', 'dialect', 'duration']].to_csv(
            SPLITS_DIR / 'test.csv', index=False
        )
        
        print(f"  ✅ ASR splits updated:")
        print(f"    train.csv: {len(train_df)} samples")
        print(f"    validation.csv: {len(val_df)} samples")
        print(f"    test.csv: {len(test_df)} samples")
        
        # Create TTS-ready structure
        print("\n📁 Creating TTS-ready structure...")
        
        TTS_READY_DIR.mkdir(parents=True, exist_ok=True)
        
        # Map datasets to dialects
        dataset_mapping = {
            'twi_multispeaker_audio_transcribed': 'asante_twi',
            'akuapem_multispeaker_audio_transcribed': 'akuapem_twi',
            'fante_multispeaker_audio_transcribed': 'fante'
        }
        
        tts_total = 0
        
        for dataset_name, dialect in dataset_mapping.items():
            if dataset_name in extraction_results and extraction_results[dataset_name].get('status') == 'success':
                source_metadata = EXTRACTED_DIR / dataset_name / 'metadata.txt'
                target_dir = TTS_READY_DIR / dialect
                target_dir.mkdir(parents=True, exist_ok=True)
                
                if source_metadata.exists():
                    # Copy metadata.txt
                    import shutil
                    shutil.copy2(source_metadata, target_dir / 'metadata.txt')
                    
                    # Count samples
                    with open(source_metadata, 'r', encoding='utf-8') as f:
                        sample_count = len(f.readlines())
                        tts_total += sample_count
                        print(f"    ✅ {dialect}: {sample_count} samples")
        
        print(f"  ✅ TTS structure updated: {tts_total} total samples")
        
        return True
    
    return False

def main():
    """Main execution function."""
    print("🚀 MICHSET AUDIO EXTRACTION PIPELINE")
    print("=" * 60)
    print("This script will:")
    print("1. Install torchcodec and dependencies")
    print("2. Extract audio from MichSet Arrow datasets")
    print("3. Update ASR and TTS data paths")
    print("4. Verify everything works")
    print("=" * 60)
    
    # Step 1: Install required packages
    install_required_packages()
    
    # Step 2: Install torchcodec
    if not install_torchcodec():
        print("\n❌ CRITICAL ERROR: torchcodec installation failed!")
        print("Manual installation required:")
        print("  conda install -c conda-forge torchcodec")
        print("  or")
        print("  pip install torchcodec")
        return False
    
    # Step 3: Verify installation
    if not verify_installation():
        print("\n❌ CRITICAL ERROR: torchcodec verification failed!")
        return False
    
    # Step 4: Extract MichSet audio
    extraction_results, total_extracted = extract_michset_audio()
    
    # Step 5: Update paths
    if total_extracted > 0:
        update_success = update_asr_and_tts_paths(extraction_results, total_extracted)
        
        # Step 6: Final summary
        print(f"\n" + "=" * 60)
        print("🎉 EXTRACTION PIPELINE COMPLETE!")
        print("=" * 60)
        
        print(f"\n📊 Final Results:")
        print(f"  Total audio files extracted: {total_extracted}")
        
        for dataset_name, result in extraction_results.items():
            if result.get('status') == 'success':
                print(f"    {dataset_name}: {result['extracted']} files")
        
        if update_success:
            print(f"\n✅ SUCCESS: All data paths updated!")
            print(f"  📄 ASR notebook: Ready with real audio files")
            print(f"  📄 TTS notebook: Ready with real audio files")
            print(f"  🎯 Both notebooks can now train with actual audio!")
        else:
            print(f"\n⚠️ Partial success: Audio extracted but path update failed")
        
        print(f"\n🚀 Next steps:")
        print(f"  1. Open 004_phase2_asr_development.ipynb")
        print(f"  2. Run ASR training with real audio")
        print(f"  3. Open 005_phase3_tts_development.ipynb")
        print(f"  4. Run TTS training with real audio")
        
        return True
        
    else:
        print(f"\n❌ EXTRACTION FAILED: No audio files extracted")
        print("Check the error messages above for troubleshooting")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎊 ALL DONE! Your MichSet audio files are ready for training!")
    else:
        print(f"\n💥 Something went wrong. Check the output for details.")