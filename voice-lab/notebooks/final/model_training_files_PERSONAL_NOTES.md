  📊 Sample Rate Alignment:

  - ASR Models (16kHz): Faster Whisper, Wav2Vec2, MMS, Moshi (input)
  - Standard TTS (22kHz): Coqui XTTS, MeloTTS
  - High-Quality TTS (24kHz): Kokoro, F5-TTS, OpenVoice, ChatTTS, Moshi (output)


 Core Data Splits

  - Training data (70-80%): Main dataset for model learning
  - Validation data (10-15%): For hyperparameter tuning and monitoring during training
  - Test data (10-15%): Final evaluation, kept unseen during training

  Required Processed Files by Model Type

  ASR (Automatic Speech Recognition) Models

  - Audio files: Preprocessed (normalized, resampled to consistent sample rate)
  - Transcripts: Text transcriptions aligned with audio
  - Manifest files: JSON/CSV linking audio paths to transcripts
  - Vocabulary file: List of unique characters/words in dataset
  - Audio metadata: Duration, speaker info, quality metrics

  TTS (Text-to-Speech) Models

  - Audio files: High-quality, consistent format
  - Text files: Normalized transcripts (punctuation, numbers spelled out)
  - Speaker embeddings: For multi-speaker models
  - Phoneme alignments: Text-to-phoneme mappings
  - Prosody annotations: Stress, intonation markers

  Translation Models

  - Source text files: Preprocessed and tokenized
  - Target text files: Aligned translations
  - Vocabulary files: Source and target language vocabularies
  - Sentence alignments: Parallel corpus mappings

  Additional Processing Requirements

  - Data normalization: Consistent text formatting, audio levels
  - Quality filtering: Remove corrupted/low-quality samples
  - Speaker balancing: Ensure diverse speaker representation
  - Language-specific processing: Tone markers for Twi, dialectal variations 