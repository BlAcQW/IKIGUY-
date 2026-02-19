"""
Process MichSetHowusu Arrow format datasets
Handles both local Arrow files and HuggingFace downloads
"""

from pathlib import Path
import pandas as pd
from tqdm import tqdm
import json

def process_michsethowusu_arrow(raw_dir: Path, output_dir: Path = None):
    """
    Process MichSetHowusu datasets in Arrow format.
    
    Args:
        raw_dir: Path to raw data directory containing michsethowusu folder
        output_dir: Optional output directory for processed data
    
    Returns:
        List of processed samples with audio arrays and text
    """
    
    print("\n" + "="*60)
    print("PROCESSING MICHSETHOWUSU ARROW DATASETS")
    print("="*60)
    
    michset_samples = []
    michset_base = raw_dir / 'michsethowusu'
    
    if michset_base.exists():
        print(f"✅ Found MichSetHowusu directory: {michset_base}")
        
        # Look for Arrow dataset directories
        arrow_dirs = [
            michset_base / 'twi_multispeaker_audio_transcribed' / 'train',
            michset_base / 'akuapem_multispeaker_audio_transcribed' / 'train', 
            michset_base / 'fante_multispeaker_audio_transcribed' / 'train'
        ]
        
        for arrow_dir in arrow_dirs:
            if arrow_dir.exists():
                print(f"\n📁 Processing {arrow_dir.parent.name}...")
                
                # Check for Arrow files
                arrow_files = list(arrow_dir.glob('*.arrow'))
                if arrow_files:
                    print(f"  Found {len(arrow_files)} Arrow files")
                    
                    try:
                        from datasets import load_from_disk
                        
                        # Load dataset from Arrow files
                        dataset = load_from_disk(str(arrow_dir))
                        print(f"  ✅ Loaded {len(dataset)} samples from Arrow files")
                        
                        # Show dataset structure
                        if len(dataset) > 0:
                            print(f"  Features: {list(dataset.features.keys())}")
                            sample = dataset[0]
                            print(f"  Sample keys: {list(sample.keys())}")
                            
                            # Check audio structure
                            if 'audio' in sample:
                                audio = sample['audio']
                                if isinstance(audio, dict):
                                    print(f"  Audio has keys: {list(audio.keys())}")
                                    if 'array' in audio:
                                        print(f"  Audio array shape: {len(audio['array'])}")
                                    if 'sampling_rate' in audio:
                                        print(f"  Sampling rate: {audio['sampling_rate']} Hz")
                        
                        # Process samples
                        max_samples = min(500, len(dataset))
                        
                        for i in tqdm(range(max_samples), desc=f"Extracting {arrow_dir.parent.name}"):
                            sample = dataset[i]
                            
                            # Extract text (handle different column names)
                            text = sample.get('text') or sample.get('sentence') or sample.get('transcript', '')
                            
                            # Extract audio
                            audio_data = sample.get('audio')
                            if audio_data:
                                if isinstance(audio_data, dict):
                                    audio_array = audio_data.get('array', [])
                                    sampling_rate = audio_data.get('sampling_rate', 16000)
                                else:
                                    audio_array = audio_data
                                    sampling_rate = 16000
                                
                                # Determine language/dialect
                                if 'akuapem' in arrow_dir.parent.name.lower():
                                    language = 'akuapem_twi'
                                elif 'fante' in arrow_dir.parent.name.lower():
                                    language = 'fante'
                                else:
                                    language = 'twi'
                                
                                # Calculate duration
                                duration = len(audio_array) / sampling_rate if sampling_rate > 0 else 0
                                
                                # Add to samples
                                michset_samples.append({
                                    'audio': audio_array,
                                    'text': text,
                                    'sampling_rate': sampling_rate,
                                    'language': language,
                                    'split': 'train',
                                    'dataset': arrow_dir.parent.name,
                                    'speaker_id': sample.get('speaker_id', 'unknown'),
                                    'duration': duration,
                                    'gender': sample.get('gender', ''),
                                    'age': sample.get('age', '')
                                })
                        
                        print(f"  ✅ Extracted {max_samples} samples")
                        
                        # Save metadata if output_dir provided
                        if output_dir:
                            metadata_path = output_dir / f"{arrow_dir.parent.name}_metadata.json"
                            metadata_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            metadata = {
                                'dataset': arrow_dir.parent.name,
                                'total_samples': len(dataset),
                                'processed_samples': max_samples,
                                'features': list(dataset.features.keys()),
                                'language': language
                            }
                            
                            with open(metadata_path, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2)
                            
                            print(f"  💾 Saved metadata to {metadata_path}")
                        
                    except ImportError:
                        print("  ❌ Error: datasets library not installed")
                        print("  Install with: pip install datasets pyarrow")
                    except Exception as e:
                        print(f"  ❌ Error loading Arrow files: {e}")
                else:
                    print(f"  ⚠️ No Arrow files found in {arrow_dir}")
            else:
                print(f"  ⚠️ Directory not found: {arrow_dir}")
    else:
        print(f"❌ MichSetHowusu directory not found at {michset_base}")
        
        # Offer HuggingFace fallback
        print("\n💡 To download from HuggingFace, use:")
        print("   from datasets import load_dataset")
        print("   dataset = load_dataset('michsethowusu/twi_multispeaker_audio_transcribed', token=True)")
    
    # Summary
    print(f"\n" + "="*60)
    print(f"MICHSETHOWUSU PROCESSING COMPLETE")
    print(f"="*60)
    print(f"✅ Total samples extracted: {len(michset_samples)}")
    
    if michset_samples:
        # Calculate statistics
        total_duration = sum(s['duration'] for s in michset_samples)
        languages = {}
        for s in michset_samples:
            lang = s['language']
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"📊 Total audio duration: {total_duration/60:.2f} minutes")
        print(f"🗣️ Language distribution:")
        for lang, count in languages.items():
            print(f"   - {lang}: {count} samples")
        
        # Show sample text examples
        print(f"\n📝 Sample texts:")
        for i, sample in enumerate(michset_samples[:3]):
            if sample['text']:
                text_preview = sample['text'][:100] + "..." if len(sample['text']) > 100 else sample['text']
                print(f"   {i+1}. [{sample['language']}] {text_preview}")
    
    return michset_samples


def main():
    """Main function to run MichSetHowusu processing."""
    
    # Paths
    if Path("G:/My Drive/voice-lab-data/raw").exists():
        # Google Drive mounted
        raw_dir = Path("G:/My Drive/voice-lab-data/raw")
        output_dir = Path("G:/My Drive/voice-lab-data/processed/michsethowusu")
    else:
        # Local development
        raw_dir = Path("./data/raw")
        output_dir = Path("./data/processed/michsethowusu")
    
    print(f"📂 Raw data directory: {raw_dir}")
    print(f"📂 Output directory: {output_dir}")
    
    # Process datasets
    samples = process_michsethowusu_arrow(raw_dir, output_dir)
    
    # Save sample list for reference
    if samples and output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame for easier analysis
        df = pd.DataFrame([{
            'dataset': s['dataset'],
            'language': s['language'],
            'text': s['text'],
            'duration': s['duration'],
            'sampling_rate': s['sampling_rate'],
            'speaker_id': s['speaker_id']
        } for s in samples])
        
        # Save as CSV
        csv_path = output_dir / 'michsethowusu_samples.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"\n💾 Saved sample list to {csv_path}")
        
        # Show summary statistics
        print(f"\n📊 Dataset Summary:")
        print(df.groupby(['dataset', 'language']).agg({
            'duration': ['count', 'sum', 'mean'],
            'text': lambda x: x.str.len().mean()
        }))
    
    return samples


if __name__ == "__main__":
    samples = main()
    print(f"\n✅ Processing complete! Extracted {len(samples)} samples.")