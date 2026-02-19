#!/bin/bash

# Deploy script for Python 3.12 with dependency fixes
set -e

echo "🚀 Deploying Core Backend with Python 3.12..."

# Check if we're in the right directory
if [ ! -f "requirements-py312.txt" ]; then
    echo "❌ Error: requirements-py312.txt not found. Please run this script from the core_backend directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.12 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and setuptools
echo "⬆️ Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install dependencies without fairseq first
echo "📥 Installing core dependencies..."
pip install -r requirements-py312.txt

# Check if fairseq is needed and install from source if required
if grep -q "fairseq" requirements-py312.txt; then
  echo "⚠️ fairseq detected in requirements. Installing from source for Python 3.12 compatibility..."
  
  # Install fairseq from source
  pip install git+https://github.com/facebookresearch/fairseq.git
  
  # Install omegaconf with specific version to avoid metadata issues
  echo "🔧 Installing omegaconf with compatible version..."
  pip install "omegaconf>=2.0.6,<2.1" --force-reinstall --no-deps
  
  echo "✅ fairseq installed from source successfully!"
else
  echo "ℹ️ fairseq not required. Using transformers for MMS models instead."
fi

# Check if librosa is needed and provide alternative
if grep -q "librosa" requirements-py312.txt; then
  echo "⚠️ librosa detected in requirements. Installing pydub as alternative for Python 3.12 compatibility..."
  
  # Install pydub as alternative to librosa
  pip install pydub>=0.25.1
  
  echo "✅ pydub installed as librosa alternative successfully!"
else
  echo "ℹ️ librosa not required. Using pydub and soundfile for audio processing."
fi

# Verify installation
echo "🔍 Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"

# Check if fairseq was installed
if python -c "import fairseq" 2>/dev/null; then
    echo "✅ fairseq successfully imported!"
else
    echo "ℹ️ fairseq not available - using transformers for MMS models"
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the server: python -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo "2. Or use the development server: python -m uvicorn main:app --reload"
echo ""
echo "🔧 If you encounter issues:"
echo "- Try the alternative requirements: pip install -r requirements-py312-with-fairseq.txt"
echo "- Or use Python 3.11 for better fairseq compatibility"
