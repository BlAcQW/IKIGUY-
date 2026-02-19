# Python 3.12 Deployment Guide

## Issues and Solutions

### Problem 1: fairseq Installation Failure
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'fairseq/version.txt'`

**Root Cause**: fairseq 0.12.0 has compatibility issues with Python 3.12 during build process.

**Solutions**:
1. **Use transformers instead** (Recommended): The `transformers` library now supports MMS models directly
2. **Install from source**: `pip install git+https://github.com/facebookresearch/fairseq.git`
3. **Use Python 3.11**: Better compatibility with fairseq

### Problem 2: omegaconf Metadata Issues
**Error**: `omegaconf has invalid metadata: .* suffix can only be used with == or != operators`

**Root Cause**: omegaconf 2.0.6 has invalid metadata format that newer pip versions reject.

**Solutions**:
1. **Use compatible version**: `pip install "omegaconf>=2.0.6,<2.1"`
2. **Downgrade pip**: `pip install pip<24.1` (not recommended)

### Problem 3: numba/librosa Python 3.12 Compatibility
**Error**: `RuntimeError: Cannot install on Python version 3.12.3; only versions >=3.8,<3.12 are supported`

**Root Cause**: numba (dependency of librosa) doesn't support Python 3.12 yet.

**Solutions**:
1. **Use pydub instead** (Recommended): `pydub>=0.25.1` for audio processing
2. **Use soundfile**: Already included for audio file handling
3. **Use Python 3.11**: Better compatibility with numba/librosa

## Deployment Options

### Option 1: Without fairseq (Recommended)
```bash
cd apps/core_backend
./deploy-py312.sh
```

This uses the updated `requirements-py312.txt` which excludes fairseq and uses transformers for MMS models.

### Option 2: With fairseq from source
```bash
cd apps/core_backend
pip install -r requirements-py312-with-fairseq.txt
```

This installs fairseq from GitHub source for better Python 3.12 compatibility.

### Option 3: Manual installation
```bash
cd apps/core_backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-py312.txt

# If you need fairseq:
pip install git+https://github.com/facebookresearch/fairseq.git
pip install "omegaconf>=2.0.6,<2.1" --force-reinstall --no-deps
```

## MMS Model Integration

Since fairseq has compatibility issues, we recommend using the `transformers` library for MMS models:

```python
from transformers import AutoProcessor, AutoModel

# Load MMS model
processor = AutoProcessor.from_pretrained("facebook/mms-1b-all")
model = AutoModel.from_pretrained("facebook/mms-1b-all")

# For speech recognition
from transformers import AutoModelForCTC, AutoProcessor

processor = AutoProcessor.from_pretrained("facebook/mms-1b-all")
model = AutoModelForCTC.from_pretrained("facebook/mms-1b-all")
```

## Verification

After deployment, verify the installation:

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import fairseq" 2>/dev/null && echo "fairseq available" || echo "fairseq not available"
```

## Troubleshooting

### If deployment fails:
1. **Clear pip cache**: `pip cache purge`
2. **Remove virtual environment**: `rm -rf venv`
3. **Try alternative requirements**: Use `requirements-py312-with-fairseq.txt`
4. **Use Python 3.11**: `python3.11 -m venv venv`

### If fairseq is required:
1. Install from source: `pip install git+https://github.com/facebookresearch/fairseq.git`
2. Install compatible omegaconf: `pip install "omegaconf>=2.0.6,<2.1"`
3. Consider using Python 3.11 instead

### If librosa is required:
1. Use pydub for audio processing: `pip install pydub>=0.25.1`
2. Use soundfile for audio file handling: `pip install soundfile>=0.12.1`
3. Consider using Python 3.11 for full librosa compatibility

### Performance considerations:
- MMS models are large (~1GB+)
- Consider using model quantization for production
- Use GPU acceleration when available
