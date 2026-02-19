#!/usr/bin/env python3
"""
Test available Common Voice datasets on HuggingFace
"""

from datasets import load_dataset
from huggingface_hub import list_datasets

def test_common_voice_datasets():
    """Test which Common Voice datasets are available"""
    print("🔍 SEARCHING FOR AVAILABLE COMMON VOICE DATASETS")
    print("=" * 60)
    
    hf_token = "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"
    
    # Search for Mozilla Common Voice datasets
    datasets = list_datasets(search="common_voice", author="mozilla-foundation")
    
    print("📋 Found Common Voice datasets:")
    for dataset in datasets:
        print(f"  - {dataset.id}")
    
    # Test specific datasets that might work
    datasets_to_test = [
        ("mozilla-foundation/common_voice_11_0", "tw"),
        ("mozilla-foundation/common_voice_11_0", "ak"), 
        ("mozilla-foundation/common_voice_10_0", "tw"),
        ("mozilla-foundation/common_voice_9_0", "tw")
    ]
    
    for dataset_name, lang_code in datasets_to_test:
        print(f"\n📥 Testing {dataset_name} with language '{lang_code}'...")
        
        try:
            # Try to load just the config info first
            from datasets import get_dataset_config_names
            configs = get_dataset_config_names(dataset_name, token=hf_token)
            
            if lang_code in configs:
                print(f"  ✅ Language '{lang_code}' is available")
                
                # Try to load a small sample
                dataset = load_dataset(
                    dataset_name, 
                    lang_code, 
                    split="train[:10]",  # Just 10 samples
                    token=hf_token
                )
                
                print(f"  ✅ Successfully loaded sample!")
                print(f"    📄 Samples: {len(dataset)}")
                print(f"    🏷️ Features: {list(dataset.features.keys())}")
                
                if len(dataset) > 0:
                    sample = dataset[0]
                    print(f"    📝 Sample text: {sample.get('sentence', 'N/A')[:100]}...")
                
                return dataset_name, lang_code, dataset
                
            else:
                print(f"  ❌ Language '{lang_code}' not available")
                print(f"    Available languages: {configs[:10]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n❌ No working Common Voice datasets found for Twi/Akan")
    return None, None, None

def test_alternative_datasets():
    """Test alternative speech datasets that might have Twi/Akan"""
    print(f"\n🔍 SEARCHING FOR ALTERNATIVE TWII/AKAN DATASETS")
    print("=" * 60)
    
    hf_token = "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"
    
    alternative_datasets = [
        "google/fleurs",  # Multilingual speech dataset
        "facebook/multilingual_librispeech",  # MLS dataset
        "openslr/slr86",  # African languages
    ]
    
    for dataset_name in alternative_datasets:
        print(f"\n📥 Testing {dataset_name}...")
        
        try:
            # Try to get config names
            from datasets import get_dataset_config_names
            configs = get_dataset_config_names(dataset_name, token=hf_token)
            
            # Look for Twi/Akan related configs
            twi_configs = [c for c in configs if any(x in c.lower() for x in ['tw', 'ak', 'twi', 'akan', 'ghana'])]
            
            if twi_configs:
                print(f"  ✅ Found Twi/Akan configs: {twi_configs}")
                
                # Try to load one
                config = twi_configs[0]
                dataset = load_dataset(
                    dataset_name,
                    config,
                    split="train[:5]",
                    token=hf_token
                )
                
                print(f"  ✅ Loaded {len(dataset)} samples from {config}")
                print(f"    🏷️ Features: {list(dataset.features.keys())}")
                
                return dataset_name, config, dataset
                
            else:
                print(f"  ❌ No Twi/Akan configs found")
                print(f"    Available configs: {configs[:10]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None, None, None

if __name__ == "__main__":
    # Test Common Voice first
    dataset_name, lang_code, dataset = test_common_voice_datasets()
    
    # If no Common Voice found, try alternatives
    if dataset is None:
        dataset_name, lang_code, dataset = test_alternative_datasets()
    
    if dataset is not None:
        print(f"\n🎯 SUCCESS! Found working dataset:")
        print(f"  📊 Dataset: {dataset_name}")
        print(f"  🏷️ Config: {lang_code}")
        print(f"  📄 Samples: {len(dataset)}")
        
        # Save the working configuration
        import json
        from pathlib import Path
        
        metadata_dir = Path('./data/metadata')
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        config_info = {
            'working_dataset': dataset_name,
            'working_config': lang_code,
            'sample_count': len(dataset),
            'features': list(dataset.features.keys()),
            'test_date': '2025-09-05'
        }
        
        with open(metadata_dir / 'working_hf_dataset.json', 'w') as f:
            json.dump(config_info, f, indent=2)
        
        print(f"  ✅ Config saved to: {metadata_dir / 'working_hf_dataset.json'}")
    else:
        print(f"\n❌ No working Twi/Akan datasets found")