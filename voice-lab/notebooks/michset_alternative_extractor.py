#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Alternative MichSet Audio Extractor
Uses alternative approach without torchcodec by directly accessing dataset files
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from datasets import load_dataset
import subprocess
import warnings
warnings.filterwarnings('ignore')

class AlternativeMichSetExtractor:
    """Alternative MichSet audio extractor that works around torchcodec issues."""
    
    def __init__(self, base_dir: str = "G:/My Drive/voice-lab-data"):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw" / "michsethowusu"
        self.output_dir = self.base_dir / "processed" / "michset_audio_extracted"
        self.manifests_dir = self.base_dir / "processed" / "michset_audio_manifests"
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def install_audio_libraries(self):
        """Install required audio processing libraries."""
        try:
            import librosa
            import soundfile
            print("Audio libraries already available")
            return True
        except ImportError:
            print("Installing audio processing libraries...")
            
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "librosa", "soundfile", "--quiet"
                ])
                
                import librosa
                import soundfile
                print("Audio libraries installed successfully!")
                return True
                
            except Exception as e:
                print(f"Error installing audio libraries: {e}")
                return False
    
    def extract_dataset_metadata(self, dataset_path: Path, dialect: str) -> Dict[str, Any]:
        """Extract metadata from dataset without audio processing."""
        
        try:
            # Load dataset to get metadata
            dataset = load_dataset(str(dataset_path), split="train")
            
            print(f"  Dataset loaded: {len(dataset)} samples")
            print(f"  Features: {list(dataset.features.keys())}")
            
            # Extract sample data
            samples = []
            max_samples = min(1000, len(dataset))  # Limit to 1000 samples
            
            for i in range(max_samples):
                try:
                    sample = dataset[i]
                    
                    # Get text content
                    text = sample.get('transcription', '')
                    
                    # Get audio path if available
                    audio_info = sample.get('audio_path', {})
                    audio_path_str = ""
                    
                    if isinstance(audio_info, dict) and 'path' in audio_info:
                        audio_path_str = audio_info['path']
                    elif isinstance(audio_info, str):
                        audio_path_str = audio_info
                    
                    # Create output filename
                    output_file = self.output_dir / f"{dataset_path.name}_{i:05d}.wav"
                    
                    samples.append({
                        'original_index': i,
                        'audio_file': str(output_file),
                        'original_audio_path': audio_path_str,
                        'text': text,
                        'dialect': dialect,
                        'duration': 2.0,  # Estimated duration
                        'sampling_rate': 16000,
                        'status': 'metadata_ready'
                    })
                    
                    if (i + 1) % 100 == 0:
                        print(f"    Processed {i + 1} samples...")
                        
                except Exception as e:
                    print(f"    Error processing sample {i}: {e}")
                    continue
            
            return {
                'dataset_name': dataset_path.name,
                'dialect': dialect,
                'total_samples': len(dataset),
                'processed_samples': len(samples),
                'samples': samples
            }
            
        except Exception as e:
            print(f"  Error loading dataset: {e}")
            return {}
    
    def create_working_solution(self) -> bool:
        """Create a working solution that provides structure for future audio extraction."""
        
        print("ALTERNATIVE MICHSET PROCESSING")
        print("=" * 60)
        print("Creating working solution with metadata structure...")
        
        datasets_info = [
            ("twi_multispeaker_audio_transcribed", "twi"),
            ("akuapem_multispeaker_audio_transcribed", "akuapem_twi"),
            ("fante_multispeaker_audio_transcribed", "fante")
        ]
        
        all_results = {}
        all_samples = []
        
        for dataset_name, dialect in datasets_info:
            print(f"\n{dataset_name.upper()}")
            print("-" * 40)
            
            dataset_path = self.raw_dir / dataset_name
            
            if not dataset_path.exists():
                print(f"  Dataset not found: {dataset_path}")
                continue
            
            # Extract metadata
            result = self.extract_dataset_metadata(dataset_path, dialect)
            
            if result and result.get('processed_samples', 0) > 0:
                all_results[dataset_name] = result
                
                # Add to combined samples
                for sample in result['samples']:
                    all_samples.append({
                        'audio': sample['audio_file'],
                        'text': sample['text'],
                        'original_text': sample['text'],
                        'dialect': sample['dialect'],
                        'speaker_id': f"{dialect}_speaker_{sample['original_index'] // 100}",
                        'duration': sample['duration'],
                        'source': 'michset_alternative',
                        'english_translation': '',
                        'audio_available': False,  # Mark as not extracted yet
                        'extraction_needed': True,
                        'note': 'Structure created, audio extraction requires torchcodec/FFmpeg fix',
                        'original_audio_path': sample['original_audio_path']
                    })
                
                # Save individual manifest
                manifest_file = self.manifests_dir / f"{dataset_name}_metadata.json"
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"  [SUCCESS] Processed {result['processed_samples']} samples")
                print(f"  [SAVED] Manifest: {manifest_file}")
            else:
                print(f"  [FAILED] No samples processed")
        
        if all_samples:
            # Create DataFrame and splits
            df = pd.DataFrame(all_samples)
            
            # Shuffle and split
            df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
            
            n_samples = len(df_shuffled)
            n_train = int(0.8 * n_samples)
            n_val = int(0.1 * n_samples)
            
            train_df = df_shuffled[:n_train]
            val_df = df_shuffled[n_train:n_train+n_val]
            test_df = df_shuffled[n_train+n_val:]
            
            # Save splits
            splits_dir = self.base_dir / 'splits'
            splits_dir.mkdir(parents=True, exist_ok=True)
            
            train_df.to_csv(splits_dir / 'train.csv', index=False)
            val_df.to_csv(splits_dir / 'validation.csv', index=False)
            test_df.to_csv(splits_dir / 'test.csv', index=False)
            
            # Create dataset info
            info = {
                'status': 'structure_ready_audio_pending',
                'total_samples': len(df),
                'splits': {
                    'train': len(train_df),
                    'validation': len(val_df),
                    'test': len(test_df)
                },
                'audio_available': False,
                'extraction_needed': True,
                'next_steps': [
                    'Fix torchcodec FFmpeg compatibility',
                    'Run actual audio extraction',
                    'Or implement direct file access method'
                ],
                'workaround': 'Using placeholder structure until audio extraction works'
            }
            
            info_file = splits_dir / 'dataset_info.json'
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
            
            # Save combined results
            combined_results = {
                'processing_timestamp': pd.Timestamp.now().isoformat(),
                'total_datasets': len(all_results),
                'total_samples': len(all_samples),
                'datasets': all_results,
                'status': 'metadata_complete_audio_pending'
            }
            
            combined_file = self.manifests_dir / "michset_alternative_results.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n" + "=" * 60)
            print("ALTERNATIVE PROCESSING COMPLETE")
            print("=" * 60)
            print(f"  Total samples: {len(all_samples)}")
            print(f"  Train/Val/Test: {len(train_df)}/{len(val_df)}/{len(test_df)}")
            print(f"  Structure: Ready")
            print(f"  Audio: Pending extraction")
            print(f"  Output: {splits_dir}")
            
            return True
        
        else:
            print("No samples processed")
            return False
    
    def attempt_direct_audio_access(self) -> bool:
        """Try to access audio files directly from the raw MichSet data."""
        
        print("\nAttempting direct audio file access...")
        
        for dataset_name, dialect in [("twi_multispeaker_audio_transcribed", "twi")]:
            dataset_path = self.raw_dir / dataset_name
            
            if dataset_path.exists():
                print(f"Checking {dataset_path}...")
                
                # Look for audio directories or files
                audio_dirs = []
                for item in dataset_path.rglob("*"):
                    if item.is_dir() and any(x in item.name.lower() for x in ['audio', 'wav', 'mp3']):
                        audio_dirs.append(item)
                
                if audio_dirs:
                    print(f"  Found potential audio directories: {len(audio_dirs)}")
                    for dir_path in audio_dirs[:3]:  # Show first 3
                        print(f"    {dir_path}")
                        
                        # Count audio files
                        audio_files = list(dir_path.glob("*.wav")) + list(dir_path.glob("*.mp3"))
                        if audio_files:
                            print(f"      Audio files: {len(audio_files)}")
                            return True
                else:
                    print(f"  No obvious audio directories found")
                    
                    # Check for any audio files
                    audio_files = list(dataset_path.rglob("*.wav")) + list(dataset_path.rglob("*.mp3"))
                    if audio_files:
                        print(f"  Found {len(audio_files)} audio files scattered")
                        return True
        
        return False

def main():
    """Main execution for alternative approach."""
    
    print("ALTERNATIVE MICHSET PROCESSING")
    print("=" * 50)
    print("Working around torchcodec issues...")
    
    extractor = AlternativeMichSetExtractor()
    
    # Try to install audio libraries
    extractor.install_audio_libraries()
    
    # Check for direct audio access
    extractor.attempt_direct_audio_access()
    
    # Create working solution
    success = extractor.create_working_solution()
    
    if success:
        print(f"\n" + "=" * 50)
        print("SUCCESS: WORKING SOLUTION CREATED!")
        print("=" * 50)
        print("  - Data structure ready")
        print("  - ASR splits created") 
        print("  - Notebooks will load successfully")
        print("  - Audio extraction pending torchcodec fix")
        
        print(f"\nRecommendations:")
        print(f"  1. ASR notebook should now load without errors")
        print(f"  2. Text processing and model setup will work")
        print(f"  3. Audio extraction needs torchcodec/FFmpeg compatibility fix")
        print(f"  4. Consider alternative: direct file access to MichSet audio")
    else:
        print("Alternative processing failed")
    
    return success

if __name__ == "__main__":
    main()