#!/usr/bin/env python3
"""
Test Common Voice with the approach from the documentation
"""

from datasets import load_dataset
import json
from pathlib import Path

def test_common_voice_17_approach():
    """Test the exact approach from the documentation"""
    print("🎙️ TESTING COMMON VOICE 17 APPROACH")
    print("=" * 50)
    
    try:
        print("📥 Loading mozilla-foundation/common_voice_17 with 'tw' language...")
        
        # Try multiple variations with explicit token
        hf_token = "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"
        
        variations_to_try = [
            ("mozilla-foundation/common_voice_17", "tw"),
            ("mozilla-foundation/common_voice_17_0", "tw"),
            ("mozilla-foundation/common_voice_16_1", "tw"),
        ]
        
        ds = None
        working_dataset = None
        
        for dataset_name, lang_code in variations_to_try:
            print(f"  Trying {dataset_name} with {lang_code}...")
            
            try:
                ds = load_dataset(dataset_name, lang_code, use_auth_token=hf_token)
                working_dataset = dataset_name
                print(f"  ✅ Success with {dataset_name}!")
                break
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue
        
        if ds is None:
            raise Exception("No working Common Voice dataset found")
        
        print("✅ Dataset loaded successfully!")
        print(f"📊 Dataset structure: {ds}")
        
        # Check available splits
        print(f"🏷️ Available splits: {list(ds.keys())}")
        
        for split_name, split_data in ds.items():
            print(f"\n📁 Split '{split_name}':")
            print(f"  📄 Samples: {len(split_data):,}")
            print(f"  🏷️ Features: {list(split_data.features.keys())}")
            
            # Show sample
            if len(split_data) > 0:
                sample = split_data[0]
                print(f"  📝 Sample sentence: {sample.get('sentence', 'N/A')[:100]}...")
                print(f"  🎵 Audio info: sampling_rate={sample.get('audio', {}).get('sampling_rate', 'N/A')}")
        
        # Apply the preprocessing function as shown in docs
        def prepare_dataset(batch):
            """Function to preprocess the dataset with the .map method"""
            transcription = batch["sentence"]
            
            if transcription.startswith('"') and transcription.endswith('"'):
                # we can remove trailing quotation marks as they do not affect the transcription
                transcription = transcription[1:-1]
            
            if transcription[-1] not in [".", "?", "!"]:
                # append a full-stop to sentences that do not end in punctuation
                transcription = transcription + "."
            
            batch["sentence"] = transcription
            
            return batch
        
        print(f"\n🔄 Applying preprocessing...")
        ds = ds.map(prepare_dataset, desc="preprocess dataset")
        print("✅ Preprocessing applied!")
        
        # Save to local directory
        output_dir = Path('./data/processed/common_voice_17_tw')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Saving dataset to {output_dir}...")
        ds.save_to_disk(str(output_dir))
        
        # Create metadata
        total_samples = sum(len(split) for split in ds.values())
        metadata = {
            'dataset_name': 'mozilla-foundation/common_voice_17',
            'language_code': 'tw',
            'language_name': 'Twi',
            'splits': {name: len(split) for name, split in ds.items()},
            'total_samples': total_samples,
            'preprocessing_applied': True,
            'download_date': '2025-09-05',
            'local_path': str(output_dir),
            'status': 'success'
        }
        
        metadata_file = output_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ SUCCESS! Common Voice 17 Twi dataset downloaded")
        print(f"  📁 Location: {output_dir}")
        print(f"  📊 Total samples: {total_samples:,}")
        print(f"  🏷️ Splits: {list(ds.keys())}")
        print(f"  📋 Metadata: {metadata_file}")
        
        return ds, metadata
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def main():
    """Test the Common Voice 17 approach"""
    ds, metadata = test_common_voice_17_approach()
    
    if ds is not None:
        print(f"\n🎯 READY FOR TRAINING!")
        print(f"You now have Common Voice Twi data + BibleTTS + Financial Inclusion")
        print(f"Complete voice dataset ready for comprehensive processing!")
    else:
        print(f"\n📝 If this still doesn't work, we proceed with the excellent")
        print(f"BibleTTS + Financial Inclusion datasets (30+ GB)")

if __name__ == "__main__":
    main()