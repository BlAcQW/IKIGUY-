#!/usr/bin/env python3
"""
Test new Common Voice loading approaches
"""

def test_direct_huggingface_hub():
    """Test using HuggingFace Hub directly"""
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
        
        print("🔍 Testing direct HuggingFace Hub access...")
        
        hf_token = "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"
        repo_id = "mozilla-foundation/common_voice_17_0"
        
        # List files in the repository
        print("📂 Listing files in Common Voice 17.0 repository...")
        files = list_repo_files(repo_id, token=hf_token)
        
        # Look for Twi-related files
        twi_files = [f for f in files if 'tw' in f.lower()][:10]
        
        print(f"📁 Found {len(files)} total files")
        print(f"🎯 Found {len(twi_files)} Twi-related files:")
        for f in twi_files:
            print(f"  - {f}")
            
        if twi_files:
            # Try downloading a small file
            sample_file = twi_files[0]
            print(f"\n📥 Attempting to download: {sample_file}")
            
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=sample_file,
                token=hf_token
            )
            
            print(f"✅ Downloaded to: {local_path}")
            return True
            
    except Exception as e:
        print(f"❌ HuggingFace Hub direct access failed: {e}")
        return False

def test_streaming_approach():
    """Test streaming dataset approach"""
    try:
        from datasets import load_dataset
        
        print("\n🔄 Testing streaming approach...")
        
        hf_token = "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"
        
        # Try streaming with trust_remote_code
        dataset = load_dataset(
            "mozilla-foundation/common_voice_17_0",
            "tw",
            split="train",
            streaming=True,
            trust_remote_code=True,
            token=hf_token
        )
        
        print("✅ Streaming dataset loaded!")
        
        # Get first sample
        sample = next(iter(dataset))
        print("📝 Sample keys:", list(sample.keys()))
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming approach failed: {e}")
        return False

def test_parquet_files():
    """Test loading parquet files directly"""
    try:
        from huggingface_hub import list_repo_files
        import pandas as pd
        from huggingface_hub import hf_hub_download
        
        print("\n📊 Testing parquet file approach...")
        
        hf_token = "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"
        repo_id = "mozilla-foundation/common_voice_17_0"
        
        # Look for parquet files
        files = list_repo_files(repo_id, token=hf_token)
        parquet_files = [f for f in files if f.endswith('.parquet') and 'tw' in f][:5]
        
        print(f"📁 Found {len(parquet_files)} Twi parquet files:")
        for f in parquet_files:
            print(f"  - {f}")
            
        if parquet_files:
            # Download and read first parquet file
            sample_parquet = parquet_files[0]
            print(f"\n📥 Downloading {sample_parquet}...")
            
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=sample_parquet,
                token=hf_token
            )
            
            # Read with pandas
            df = pd.read_parquet(local_path)
            print(f"✅ Loaded parquet file!")
            print(f"  📊 Shape: {df.shape}")
            print(f"  🏷️ Columns: {list(df.columns)}")
            
            if len(df) > 0:
                print(f"  📝 Sample sentence: {df.iloc[0].get('sentence', 'N/A')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Parquet approach failed: {e}")
        return False

def main():
    """Test different approaches to access Common Voice 17.0"""
    print("🧪 TESTING NEW COMMON VOICE ACCESS METHODS")
    print("=" * 60)
    
    methods = [
        ("Direct HuggingFace Hub", test_direct_huggingface_hub),
        ("Streaming with trust_remote_code", test_streaming_approach),
        ("Direct Parquet Files", test_parquet_files)
    ]
    
    for method_name, method_func in methods:
        print(f"\n🔬 {method_name}")
        print("-" * 40)
        
        try:
            success = method_func()
            if success:
                print(f"✅ {method_name} WORKS!")
                break
        except Exception as e:
            print(f"❌ {method_name} failed with exception: {e}")
    
    print(f"\n📋 Summary: Testing complete")

if __name__ == "__main__":
    main()