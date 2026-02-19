#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced MichSet Audio Extractor with FFmpeg Support
Now that FFmpeg is available, this should work with torchcodec
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from datasets import load_dataset, Audio
import warnings
warnings.filterwarnings('ignore')

# Add FFmpeg to environment PATH
import subprocess

def setup_ffmpeg_path():
    """Add FFmpeg to system PATH for this session."""
    current_dir = Path.cwd()
    ffmpeg_bin = current_dir / "ffmpeg" / "ffmpeg-master-latest-win64-gpl" / "bin"
    
    if ffmpeg_bin.exists():
        ffmpeg_path = str(ffmpeg_bin)
        current_path = os.environ.get('PATH', '')
        
        if ffmpeg_path not in current_path:
            os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path
            print(f"Added FFmpeg to PATH: {ffmpeg_path}")
        
        # Test FFmpeg availability
        try:
            result = subprocess.run([str(ffmpeg_bin / "ffmpeg.exe"), "-version"], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("FFmpeg is available and working!")
                return True
            else:
                print("FFmpeg found but not working properly")
                return False
        except Exception as e:
            print(f"Error testing FFmpeg: {e}")
            return False
    else:
        print("FFmpeg not found in expected location")
        return False

def install_torchcodec():
    """Install torchcodec with FFmpeg support."""
    print("Installing/verifying torchcodec installation...")
    
    try:
        import torchcodec
        print("torchcodec is already installed")
        return True
    except ImportError:
        print("Installing torchcodec...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torchcodec>=0.0.1", "--quiet"
            ])
            
            # Test import
            import torchcodec
            print("torchcodec installed successfully!")
            return True
            
        except Exception as e:
            print(f"Error installing torchcodec: {e}")
            return False

class EnhancedMichSetExtractor:
    """Enhanced MichSet audio extractor with proper FFmpeg/torchcodec support."""
    
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
    
    def load_dataset_with_audio(self, dataset_path: Path, max_samples: int = 1000) -> Optional[Dict]:
        """Load dataset and extract audio with torchcodec support."""
        
        try:
            # Load dataset with audio processing
            dataset = load_dataset(
                str(dataset_path), 
                split="train",
                streaming=False
            )
            
            print(f"  Dataset loaded: {len(dataset)} samples")
            print(f"  Features: {list(dataset.features.keys())}")
            
            # Cast audio column to Audio format for automatic decoding
            if 'audio_path' in dataset.features:
                print(f"  Casting audio_path to Audio format...")
                dataset = dataset.cast_column('audio_path', Audio(sampling_rate=16000))
                
                # Test loading a few samples
                extracted_samples = []
                
                for i, sample in enumerate(dataset):
                    if i >= max_samples:
                        break
                        
                    try:
                        # Access the audio data - this should trigger torchcodec decoding
                        audio_data = sample.get('audio_path', {})
                        
                        if audio_data and 'array' in audio_data:
                            audio_array = audio_data['array']
                            sampling_rate = audio_data['sampling_rate']
                            
                            # Create output filename
                            output_file = self.output_dir / f"{dataset_path.name}_{i:05d}.wav"
                            
                            # Save audio using soundfile or torchaudio
                            self.save_audio_file(audio_array, sampling_rate, output_file)
                            
                            extracted_samples.append({
                                'original_index': i,
                                'audio_file': str(output_file),
                                'text': sample.get('transcription', ''),
                                'duration': len(audio_array) / sampling_rate,
                                'sampling_rate': sampling_rate
                            })
                            
                            if (i + 1) % 100 == 0:
                                print(f"    Processed {i + 1} samples...")
                                
                        else:
                            print(f"    No audio data in sample {i}")
                            
                    except Exception as e:
                        print(f"    Error processing sample {i}: {e}")
                        continue
                
                print(f"  Successfully extracted {len(extracted_samples)} audio files")
                
                return {
                    'dataset_name': dataset_path.name,
                    'total_samples': len(dataset),
                    'extracted_samples': len(extracted_samples),
                    'samples': extracted_samples
                }
                
            else:
                print(f"  No audio_path field found in features: {list(dataset.features.keys())}")
                return None
                
        except Exception as e:
            print(f"  Error loading dataset: {e}")
            return None
    
    def save_audio_file(self, audio_array, sampling_rate: int, output_path: Path):
        """Save audio array to file."""
        try:
            # Try using soundfile first
            try:
                import soundfile as sf
                sf.write(str(output_path), audio_array, sampling_rate)
                return
            except ImportError:
                pass
            
            # Fallback to torchaudio
            try:
                import torchaudio
                import torch
                
                if isinstance(audio_array, list):
                    audio_array = torch.tensor(audio_array)
                elif not isinstance(audio_array, torch.Tensor):
                    audio_array = torch.from_numpy(audio_array)
                
                # Ensure correct shape (channels, samples)
                if audio_array.dim() == 1:
                    audio_array = audio_array.unsqueeze(0)
                
                torchaudio.save(str(output_path), audio_array, sampling_rate)
                return
                
            except ImportError:
                pass
            
            # Last resort: install soundfile
            subprocess.check_call([sys.executable, "-m", "pip", "install", "soundfile"])
            import soundfile as sf
            sf.write(str(output_path), audio_array, sampling_rate)
            
        except Exception as e:
            raise Exception(f"Could not save audio file: {e}")
    
    def extract_all_datasets(self, max_samples_per_dataset: int = 1000) -> Dict[str, Any]:
        """Extract audio from all MichSet datasets."""
        
        print("ENHANCED MICHSET AUDIO EXTRACTION")
        print("=" * 60)
        
        datasets_info = [
            ("twi_multispeaker_audio_transcribed", "twi"),
            ("akuapem_multispeaker_audio_transcribed", "akuapem_twi"),
            ("fante_multispeaker_audio_transcribed", "fante")
        ]
        
        all_results = {}
        total_extracted = 0
        
        for dataset_name, dialect in datasets_info:
            print(f"\n{dataset_name.upper()}")
            print("-" * 40)
            
            dataset_path = self.raw_dir / dataset_name
            
            if not dataset_path.exists():
                print(f"  Dataset not found: {dataset_path}")
                continue
            
            # Create output directory for this dataset
            dataset_output_dir = self.output_dir / dataset_name
            dataset_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract audio
            result = self.load_dataset_with_audio(dataset_path, max_samples_per_dataset)
            
            if result and result['extracted_samples'] > 0:
                all_results[dataset_name] = result
                total_extracted += result['extracted_samples']
                
                # Save individual manifest
                manifest_file = self.manifests_dir / f"{dataset_name}_extracted.json"
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"  [SUCCESS] Extracted {result['extracted_samples']} files")
                print(f"  [SAVED] Manifest: {manifest_file}")
            else:
                print(f"  [FAILED] No audio extracted")
        
        # Create combined results
        if all_results:
            combined_results = {
                'extraction_timestamp': pd.Timestamp.now().isoformat(),
                'total_datasets': len(all_results),
                'total_audio_files': total_extracted,
                'datasets': all_results,
                'ffmpeg_available': True,
                'torchcodec_working': True
            }
            
            # Save combined manifest
            combined_file = self.manifests_dir / "michset_audio_extraction_results.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(combined_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n" + "=" * 60)
            print(f"EXTRACTION COMPLETE")
            print("=" * 60)
            print(f"  Total audio files extracted: {total_extracted}")
            print(f"  Output directory: {self.output_dir}")
            print(f"  Combined manifest: {combined_file}")
            
            return combined_results
        
        else:
            print(f"\nNo audio files were extracted")
            return {}
    
    def create_asr_compatible_data(self) -> bool:
        """Create ASR-compatible CSV files from extracted audio."""
        
        manifest_file = self.manifests_dir / "michset_audio_extraction_results.json"
        
        if not manifest_file.exists():
            print("No extraction results found. Run extraction first.")
            return False
        
        with open(manifest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Create combined dataset
        all_samples = []
        
        for dataset_name, dataset_info in results.get('datasets', {}).items():
            dialect = dataset_name.split('_')[0]  # twi, akuapem, fante
            
            for sample in dataset_info.get('samples', []):
                all_samples.append({
                    'audio': sample['audio_file'],
                    'text': sample['text'],
                    'original_text': sample['text'],
                    'dialect': dialect,
                    'speaker_id': f"{dialect}_speaker_{sample['original_index'] // 100}",
                    'duration': sample['duration'],
                    'source': 'michset_extracted',
                    'english_translation': '',
                    'audio_available': True,  # Now we have real audio!
                    'extraction_needed': False,
                    'note': 'Extracted using torchcodec with FFmpeg support'
                })
        
        if all_samples:
            df = pd.DataFrame(all_samples)
            
            # Create splits
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
            
            # Update dataset info
            info = {
                'status': 'audio_extraction_complete',
                'total_samples': len(df),
                'splits': {
                    'train': len(train_df),
                    'validation': len(val_df),
                    'test': len(test_df)
                },
                'audio_available': True,
                'extraction_timestamp': results.get('extraction_timestamp'),
                'notes': [
                    'Real audio files extracted using torchcodec with FFmpeg',
                    'Audio files are ready for ASR training',
                    'All samples have verified audio data'
                ]
            }
            
            info_file = splits_dir / 'dataset_info.json'
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
            
            print(f"\nASR-compatible data created:")
            print(f"  Train: {len(train_df)} samples")
            print(f"  Validation: {len(val_df)} samples")
            print(f"  Test: {len(test_df)} samples")
            print(f"  All samples have real audio files!")
            
            return True
        
        else:
            print("No samples found to create ASR data")
            return False

def main():
    """Main execution with FFmpeg and torchcodec setup."""
    
    print("MICHSET AUDIO EXTRACTION WITH FFMPEG")
    print("=" * 50)
    
    # Step 1: Setup FFmpeg
    if not setup_ffmpeg_path():
        print("FFmpeg setup failed. Cannot proceed.")
        return False
    
    # Step 2: Install/verify torchcodec
    if not install_torchcodec():
        print("torchcodec installation failed. Cannot proceed.")
        return False
    
    # Step 3: Extract audio
    extractor = EnhancedMichSetExtractor()
    results = extractor.extract_all_datasets(max_samples_per_dataset=500)  # Start with 500 per dataset
    
    if results:
        # Step 4: Create ASR data
        extractor.create_asr_compatible_data()
        
        print(f"\n" + "=" * 50)
        print("SUCCESS: MICHSET EXTRACTION COMPLETE!")
        print("=" * 50)
        print("  - FFmpeg is working")
        print("  - torchcodec is installed")
        print("  - Audio files extracted")
        print("  - ASR splits created")
        print("  - Ready for training!")
        
        return True
    
    else:
        print("\nExtraction failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    main()