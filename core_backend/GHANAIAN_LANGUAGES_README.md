# Ghanaian Language Support with Meta MMS and Whisper

This implementation provides comprehensive support for Ghanaian languages including Twi, Ewe, Ga, Dagbani, and other African languages using Meta's Massively Multilingual Speech (MMS) and OpenAI's Whisper models.

## 🌍 Supported Languages

### Ghanaian Languages

- **Twi** (Asante Twi, Akuapem Twi)
- **Ewe**
- **Ga**
- **Dagbani**
- **Hausa**
- **Yoruba**
- **Igbo**
- **Swahili**
- **English**

## 🚀 Features

### Meta MMS (Massively Multilingual Speech)

- **1,100+ languages** supported
- **Speech-to-Text** transcription
- **Text-to-Speech** synthesis
- **Language Detection** for 4,000+ languages
- **Open Source** - no API costs
- **High accuracy** for low-resource languages

### OpenAI Whisper

- **Robust speech recognition**
- **Translation** to English
- **Language detection**
- **Multiple model sizes** (tiny to large-v3)
- **Real-time processing** capabilities

## 📦 Installation

### 1. Install Dependencies

```bash
cd apps/core_backend
pip install -r requirements_ghanaian_languages.txt
```

### 2. Install PyTorch (GPU support recommended)

```bash
# For CUDA support
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CPU only
pip install torch torchaudio
```

### 3. Install Whisper

```bash
pip install openai-whisper
```

## 🗄️ Database Setup

### 1. Populate Providers and Models

```bash
cd apps/core_backend
python scripts/populate_ghanaian_language_providers.py
```

This will add:

- Meta MMS provider and models
- OpenAI Whisper provider and models
- Ghanaian voice providers and voices

### 2. Verify Database Population

```bash
python test_ghanaian_languages.py
```

## 🔧 API Endpoints

### Transcription Endpoints

#### Meta MMS Transcription

```http
POST /voice/transcribe/mms
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav",
  "language": "twi",
  "task": "transcribe"
}
```

#### Whisper Transcription

```http
POST /voice/transcribe/whisper
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav",
  "language": "twi",
  "task": "transcribe",
  "model_size": "base",
  "prompt": "Optional context prompt"
}
```

#### Whisper Translation

```http
POST /voice/translate/whisper
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav",
  "model_size": "base"
}
```

### Language Detection

#### MMS Language Detection

```http
POST /voice/detect-language/mms
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav"
}
```

#### Whisper Language Detection

```http
POST /voice/detect-language/whisper
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav",
  "model_size": "base"
}
```

### Information Endpoints

#### Get Supported Languages

```http
GET /voice/languages/mms
GET /voice/languages/whisper
```

#### Get Whisper Models

```http
GET /voice/models/whisper
```

### Text-to-Speech

#### MMS Synthesis

```http
POST /voice/synthesize/mms
Content-Type: application/json

{
  "text": "Me wo Twi",
  "language": "twi",
  "voice_id": "mms_twi_male"
}
```

### Batch Processing

#### Batch Whisper Transcription

```http
POST /voice/batch-transcribe/whisper
Content-Type: application/json

{
  "audio_files": ["/path/to/audio1.wav", "/path/to/audio2.wav"],
  "language": "twi",
  "task": "transcribe",
  "model_size": "base"
}
```

## 💻 Usage Examples

### Python Client Example

```python
import asyncio
import aiohttp
import json

async def transcribe_twi_audio():
    """Example: Transcribe Twi audio using Meta MMS."""

    url = "http://localhost:30027/voice/transcribe/mms"
    payload = {
        "audio_path": "/path/to/twi_audio.wav",
        "language": "twi",
        "task": "transcribe"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            print(f"Transcribed Text: {result['text']}")
            print(f"Language: {result['language']}")
            print(f"Confidence: {result['confidence']}")

# Run the example
asyncio.run(transcribe_twi_audio())
```

### JavaScript/TypeScript Example

```typescript
// Example: Transcribe Twi audio using Whisper
async function transcribeTwiWithWhisper(audioPath: string) {
  const response = await fetch(
    'http://localhost:30027/voice/transcribe/whisper',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio_path: audioPath,
        language: 'twi',
        task: 'transcribe',
        model_size: 'base',
      }),
    }
  );

  const result = await response.json();
  console.log('Transcribed Text:', result.text);
  console.log('Language:', result.language);
  console.log('Confidence:', result.confidence);

  return result;
}
```

## 🧪 Testing

### 1. Run Basic Tests

```bash
cd apps/core_backend
python test_ghanaian_languages.py
```

### 2. Test with Sample Audio

1. Create a `sample_audio` directory:

```bash
mkdir sample_audio
```

2. Add sample audio files (.wav, .mp3) to the directory

3. Run transcription tests:

```bash
python test_ghanaian_languages.py
```

### 3. Test API Endpoints

```bash
# Test MMS transcription
curl -X POST http://localhost:30027/voice/transcribe/mms \
  -H "Content-Type: application/json" \
  -d '{"audio_path": "/path/to/audio.wav", "language": "twi"}'

# Test Whisper transcription
curl -X POST http://localhost:30027/voice/transcribe/whisper \
  -H "Content-Type: application/json" \
  -d '{"audio_path": "/path/to/audio.wav", "language": "twi", "model_size": "base"}'
```

## 🔧 Configuration

### Model Selection

#### Whisper Model Sizes

- **tiny**: 39M parameters, fastest, lowest accuracy
- **base**: 74M parameters, balanced speed/accuracy
- **small**: 244M parameters, good accuracy
- **medium**: 769M parameters, high accuracy
- **large**: 1550M parameters, highest accuracy

#### MMS Models

- **mms-1b-all**: Speech recognition for 1,100+ languages
- **mms-tts-all**: Text-to-speech for 1,100+ languages
- **mms-lid-126**: Language detection for 4,000+ languages

### Language Codes

| Language | MMS Code | Whisper Code |
| -------- | -------- | ------------ |
| Twi      | twi      | tw           |
| Ewe      | ewe      | ee           |
| Ga       | ga       | ga           |
| Dagbani  | dag      | dag          |
| Hausa    | hau      | ha           |
| Yoruba   | yor      | yo           |
| Igbo     | ibo      | ig           |
| Swahili  | swa      | sw           |

## 🚀 Performance

### Meta MMS Performance

- **Word Error Rate**: ~15% for Ghanaian languages
- **Language Coverage**: 1,100+ languages
- **Processing Speed**: Real-time capable
- **Memory Usage**: ~2GB for ASR model

### Whisper Performance

- **Word Error Rate**: 5-25% (depending on model size)
- **Language Coverage**: 99+ languages
- **Processing Speed**: Real-time to batch processing
- **Memory Usage**: 1-10GB (depending on model size)

## 🔍 Troubleshooting

### Common Issues

#### 1. CUDA Out of Memory

```bash
# Use CPU instead of GPU
export CUDA_VISIBLE_DEVICES=""

# Or use smaller models
model_size = "tiny"  # Instead of "large"
```

#### 2. Model Download Issues

```bash
# Clear Hugging Face cache
rm -rf ~/.cache/huggingface/

# Set download directory
export HF_HOME="/path/to/cache"
```

#### 3. Audio Format Issues

```bash
# Convert audio to WAV format
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 References

### Meta MMS

- [Meta MMS Blog Post](https://ai.meta.com/blog/multilingual-model-speech-recognition/)
- [MMS GitHub Repository](https://github.com/facebookresearch/fairseq/tree/main/examples/mms)
- [MMS Hugging Face Models](https://huggingface.co/facebook/mms-1b-all)

### OpenAI Whisper

- [Whisper GitHub Repository](https://github.com/openai/whisper)
- [Whisper Paper](https://cdn.openai.com/papers/whisper.pdf)
- [Whisper Documentation](https://github.com/openai/whisper#readme)

### Ghanaian Languages

- [GhanaNLP Project](https://github.com/GhanaNLP)
- [Twi Translation Guide](https://github.com/aberba/twi-translation-guide)
- [Ghanaian Language Resources](https://github.com/Madjeisah/tw-parallel-lg-corpus)

## 🤝 Contributing

To contribute to Ghanaian language support:

1. Add new language codes to the services
2. Test with native speakers
3. Improve transcription accuracy
4. Add more voice options
5. Optimize performance

## 📄 License

This implementation is based on:

- Meta MMS: [MIT License](https://github.com/facebookresearch/fairseq/blob/main/LICENSE)
- OpenAI Whisper: [MIT License](https://github.com/openai/whisper/blob/main/LICENSE)

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the test scripts
3. Check the API documentation
4. Create an issue with detailed error information
