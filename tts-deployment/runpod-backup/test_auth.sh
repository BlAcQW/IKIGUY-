#!/bin/bash
# Test authentication with corrected cache directories

# Configure cache directories
export HF_HOME=/workspace/.cache/huggingface
export WANDB_DIR=/workspace/.cache/wandb
export TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers
export HF_DATASETS_CACHE=/workspace/.cache/huggingface/datasets

# Create directories
mkdir -p $HF_HOME $WANDB_DIR $TRANSFORMERS_CACHE $HF_DATASETS_CACHE

# Activate venv
source /workspace/venv/bin/activate

# Set tokens
export HF_TOKEN=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
export WANDB_API_KEY=4945245393f4e0b9997521b6bbfa8800e05ded8f

echo '=============================================='
echo '🔐 Testing Authentication with /workspace Cache'
echo '=============================================='
echo ''

echo '1️⃣ Testing Hugging Face authentication...'
huggingface-cli login --token $HF_TOKEN
echo ''

echo '2️⃣ Testing Weights & Biases authentication...'
wandb login $WANDB_API_KEY
echo ''

echo '3️⃣ Testing NaijaVoices dataset access (Hausa - small sample)...'
python3 << 'PYEOF'
import os
from datasets import load_dataset

try:
    ds = load_dataset(
        "naijavoices/naijavoices-dataset",
        "hausa-batch-1",
        split="train[:10]",  # Just 10 samples
        cache_dir=os.environ.get("HF_DATASETS_CACHE")
    )
    print(f"   ✅ SUCCESS: Loaded {len(ds)} samples from NaijaVoices (Hausa)")
    print(f"   Sample keys: {list(ds[0].keys())}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
PYEOF
echo ''

echo '4️⃣ Testing Common Voice dataset access (Hausa - small sample)...'
python3 << 'PYEOF'
import os
from datasets import load_dataset

try:
    ds = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "ha",
        split="train[:10]",  # Just 10 samples
        cache_dir=os.environ.get("HF_DATASETS_CACHE"),
        trust_remote_code=True
    )
    print(f"   ✅ SUCCESS: Loaded {len(ds)} samples from Common Voice (Hausa)")
    print(f"   Sample keys: {list(ds[0].keys())}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
PYEOF
echo ''

echo '=============================================='
echo '✅ Authentication Test Complete'
echo '=============================================='
echo ''
echo 'Cache directory disk usage:'
du -sh /workspace/.cache
