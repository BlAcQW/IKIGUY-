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
  
  
  
       ## 🎉 Comprehensive XTTS Optimization Complete!

       ### What This Notebook Provides:

       #### 🔄 **Comprehensive Data Integration**
       - **33+ TTS datasets** from the complete data inventory
       - **Multi-speaker support** with automatic speaker embeddings
       - **Multi-dialect Twi support** (Asante, Akuapem, Fante, Ga)
       - **Quality filtering** and dataset balancing

       #### 🎭 **Advanced Voice Cloning**
       - **XTTS-v2 optimization** for zero-shot voice cloning
       - **SpeechBrain speaker recognition** for high-quality embeddings
       - **Multi-speaker inference** with batch processing
       - **Performance benchmarking** with real-time factor analysis

       #### 🎓 **Production-Ready Training**
       - **Optimized training pipeline** with mixed precision
       - **Speaker-balanced train/validation splits**
       - **Comprehensive configuration** for multi-language support
       - **Training script generation** for immediate deployment

       #### 📊 **Comprehensive Analytics**
       - **Speaker statistics** and dataset analysis
       - **Performance benchmarking** across different text lengths
       - **Quality metrics** and success rate tracking
       - **Export capabilities** for production deployment

       ### Key Features Implemented:

       1. **ComprehensiveTTSDataLoader**: Processes all TTS inventory data
       2. **OptimizedXTTSConfig**: Enhanced configuration for Twi languages
       3. **AdvancedXTTSTrainer**: Full training pipeline with speaker embeddings
       4. **OptimizedXTTSInference**: Voice cloning and multi-speaker synthesis
       5. **Production Pipeline**: Export, benchmarking, and deployment tools

       ### Ready for Production:
       - ✅ **Training scripts** generated and ready to execute
       - ✅ **Model export** functions for deployment
       - ✅ **Performance benchmarking** tools
       - ✅ **Voice cloning** capabilities tested
       - ✅ **Multi-language** support (Twi, English, and more)

       ### Next Steps:
       1. **Execute training** using generated scripts
       2. **Monitor performance** with TensorBoard/WandB
       3. **Deploy models** using export functions
       4. **Scale inference** for production workloads
	   
	   
	   import os

# --- Please verify this is your main project folder in Google Drive ---
BASE_PATH = '/content/drive/MyDrive/voice-lab-data'
# --------------------------------------------------------------------

print(f"🔍 Scanning for data directories inside: {BASE_PATH}\n")

found_audio_dirs = []
if os.path.exists(BASE_PATH):
    # Walk through the directory tree
    for root, dirs, files in os.walk(BASE_PATH):
        # We are looking for the final parent folder containing audio files
        if any(f.endswith(('.wav', '.mp3', '.ogg', '.flac')) for f in files):
            found_audio_dirs.append(root)
else:
    print(f"❌ ERROR: The base path '{BASE_PATH}' does not exist. Please check the path and try again.")

if found_audio_dirs:
    print("✅ Found the following directories containing audio files:")
    # Print the paths relative to the base path for easier debugging
    for d in sorted(found_audio_dirs):
        relative_path = os.path.relpath(d, BASE_PATH)
        print(f"  - {relative_path}")
else:
    print("🤷 No directories containing .wav, .mp3, .ogg, or .flac files were found.")
    print("   Please ensure the BASE_PATH is correct and that your Drive is fully mounted.")
	   
	   
	   
	   .ogg, .mp3, .wav, .flac:
	   raw/african_whisper/tests

- raw/bibletts/akuapem-twi/dev/EZR

- raw/bibletts/akuapem-twi/test/COL

- raw/bibletts/akuapem-twi/train/1CH

- raw/bibletts/akuapem-twi/train/1CO

- raw/bibletts/akuapem-twi/train/1JN

- raw/bibletts/akuapem-twi/train/1KI

- raw/bibletts/akuapem-twi/train/1PE

- raw/bibletts/akuapem-twi/train/1SA

- raw/bibletts/akuapem-twi/train/1TH

- raw/bibletts/akuapem-twi/train/1TI

- raw/bibletts/akuapem-twi/train/2CH

- raw/bibletts/akuapem-twi/train/2JN

- raw/bibletts/akuapem-twi/train/2KI

- raw/bibletts/akuapem-twi/train/2PE

- raw/bibletts/akuapem-twi/train/2SA

- raw/bibletts/akuapem-twi/train/2TH

- raw/bibletts/akuapem-twi/train/2TI

- raw/bibletts/akuapem-twi/train/3JN

- raw/bibletts/akuapem-twi/train/ACT

- raw/bibletts/akuapem-twi/train/AMO

- raw/bibletts/akuapem-twi/train/DAN

- raw/bibletts/akuapem-twi/train/DEU

- raw/bibletts/akuapem-twi/train/ECC

- raw/bibletts/akuapem-twi/train/EST

- raw/bibletts/akuapem-twi/train/EXO

- raw/bibletts/akuapem-twi/train/EZK

- raw/bibletts/akuapem-twi/train/GAL

- raw/bibletts/akuapem-twi/train/GEN

- raw/bibletts/akuapem-twi/train/HAB

- raw/bibletts/akuapem-twi/train/HAG

- raw/bibletts/akuapem-twi/train/HEB

- raw/bibletts/akuapem-twi/train/HOS

- raw/bibletts/akuapem-twi/train/ISA

- raw/bibletts/akuapem-twi/train/JAS

- raw/bibletts/akuapem-twi/train/JDG

- raw/bibletts/akuapem-twi/train/JER

- raw/bibletts/akuapem-twi/train/JHN

- raw/bibletts/akuapem-twi/train/JOB

- raw/bibletts/akuapem-twi/train/JOL

- raw/bibletts/akuapem-twi/train/JON

- raw/bibletts/akuapem-twi/train/JOS

- raw/bibletts/akuapem-twi/train/JUD

- raw/bibletts/akuapem-twi/train/LAM

- raw/bibletts/akuapem-twi/train/LEV

- raw/bibletts/akuapem-twi/train/LUK

- raw/bibletts/akuapem-twi/train/MAL

- raw/bibletts/akuapem-twi/train/MAT

- raw/bibletts/akuapem-twi/train/MIC

- raw/bibletts/akuapem-twi/train/NAM

- raw/bibletts/akuapem-twi/train/NEH

- raw/bibletts/akuapem-twi/train/NUM

- raw/bibletts/akuapem-twi/train/OBA

- raw/bibletts/akuapem-twi/train/PHM

- raw/bibletts/akuapem-twi/train/PHP

- raw/bibletts/akuapem-twi/train/PRO

- raw/bibletts/akuapem-twi/train/PSA

- raw/bibletts/akuapem-twi/train/REV

- raw/bibletts/akuapem-twi/train/ROM

- raw/bibletts/akuapem-twi/train/RUT

- raw/bibletts/akuapem-twi/train/SNG

- raw/bibletts/akuapem-twi/train/TIT

- raw/bibletts/akuapem-twi/train/ZEC

- raw/bibletts/akuapem-twi/train/ZEP

- raw/bibletts/asante-twi/dev/EZR

- raw/bibletts/asante-twi/test/COL

- raw/bibletts/asante-twi/train/1CH

- raw/bibletts/asante-twi/train/1CO

- raw/bibletts/asante-twi/train/1JN

- raw/bibletts/asante-twi/train/1KI

- raw/bibletts/asante-twi/train/1PE

- raw/bibletts/asante-twi/train/1SA

- raw/bibletts/asante-twi/train/1TH

- raw/bibletts/asante-twi/train/1TI

- raw/bibletts/asante-twi/train/2CH

- raw/bibletts/asante-twi/train/2JN

- raw/bibletts/asante-twi/train/2KI

- raw/bibletts/asante-twi/train/2PE

- raw/bibletts/asante-twi/train/2SA

- raw/bibletts/asante-twi/train/2TH

- raw/bibletts/asante-twi/train/2TI

- raw/bibletts/asante-twi/train/3JN

- raw/bibletts/asante-twi/train/ACT

- raw/bibletts/asante-twi/train/AMO

- raw/bibletts/asante-twi/train/DAN

- raw/bibletts/asante-twi/train/DEU

- raw/bibletts/asante-twi/train/ECC

- raw/bibletts/asante-twi/train/EPH

- raw/bibletts/asante-twi/train/EST

- raw/bibletts/asante-twi/train/EXO

- raw/bibletts/asante-twi/train/EZK

- raw/bibletts/asante-twi/train/GAL

- raw/bibletts/asante-twi/train/GEN

- raw/bibletts/asante-twi/train/HAB

- raw/bibletts/asante-twi/train/HAG

- raw/bibletts/asante-twi/train/HEB

- raw/bibletts/asante-twi/train/HOS

- raw/bibletts/asante-twi/train/ISA

- raw/bibletts/asante-twi/train/JAS

- raw/bibletts/asante-twi/train/JDG

- raw/bibletts/asante-twi/train/JER

- raw/bibletts/asante-twi/train/JHN

- raw/bibletts/asante-twi/train/JOB

- raw/bibletts/asante-twi/train/JOL

- raw/bibletts/asante-twi/train/JON

- raw/bibletts/asante-twi/train/JOS

- raw/bibletts/asante-twi/train/JUD

- raw/bibletts/asante-twi/train/LAM

- raw/bibletts/asante-twi/train/LEV

- raw/bibletts/asante-twi/train/LUK

- raw/bibletts/asante-twi/train/MAL

- raw/bibletts/asante-twi/train/MAT

- raw/bibletts/asante-twi/train/MIC

- raw/bibletts/asante-twi/train/NAM

- raw/bibletts/asante-twi/train/NEH

- raw/bibletts/asante-twi/train/NUM

- raw/bibletts/asante-twi/train/OBA

- raw/bibletts/asante-twi/train/PHM

- raw/bibletts/asante-twi/train/PHP

- raw/bibletts/asante-twi/train/PRO

- raw/bibletts/asante-twi/train/PSA

- raw/bibletts/asante-twi/train/REV

- raw/bibletts/asante-twi/train/ROM

- raw/bibletts/asante-twi/train/RUT

- raw/bibletts/asante-twi/train/SNG

- raw/bibletts/asante-twi/train/TIT

- raw/bibletts/asante-twi/train/ZEC

- raw/bibletts/asante-twi/train/ZEP

- raw/financial_inclusion/akuapem_twi_10/__MACOSX/fisd-akuapim-twi-10p/audios

- raw/financial_inclusion/akuapem_twi_10/fisd-akuapim-twi-10p/audios

- raw/financial_inclusion/akuapem_twi_90/__MACOSX/fisd-akuapim-twi-90p/audios

- raw/financial_inclusion/akuapem_twi_90/fisd-akuapim-twi-90p/audios

- raw/financial_inclusion/asante_twi_10/__MACOSX/fisd-asanti-twi-10p/audios

- raw/financial_inclusion/asante_twi_10/fisd-asanti-twi-10p/audios

- raw/financial_inclusion/asante_twi_90/__MACOSX/fisd-asanti-twi-90p/audios

- raw/financial_inclusion/asante_twi_90/fisd-asanti-twi-90p/audios

- raw/financial_inclusion/fante_10/__MACOSX/fisd-fanti-10p/audios

- raw/financial_inclusion/fante_10/fisd-fanti-10p/audios

- raw/financial_inclusion/fante_90/__MACOSX/fisd-fanti-90p/audios

- raw/financial_inclusion/fante_90/fisd-fanti-90p/audios


arror files:
  - raw/michsethowusu/akuapem_multispeaker_audio_transcribed/test
  - raw/michsethowusu/akuapem_multispeaker_audio_transcribed/train
  - raw/michsethowusu/fante_multispeaker_audio_transcribed/test
  - raw/michsethowusu/fante_multispeaker_audio_transcribed/train
  - raw/michsethowusu/ga_multispeaker_audio_transcribed/test
  - raw/michsethowusu/ga_multispeaker_audio_transcribed/train
  - raw/michsethowusu/translations/english-twi_sentence-pairs/train
  - raw/michsethowusu/translations/hausa-twi_sentence-pairs/train
  - raw/michsethowusu/translations/swahili-twi_sentence-pairs/train
  - raw/michsethowusu/twi-emotions-corpus/train
  - raw/michsethowusu/twi-speech-text-parallel-multispeaker/train
  - raw/michsethowusu/twi_multispeaker_audio_transcribed/test
  - raw/michsethowusu/twi_multispeaker_audio_transcribed/train
  
  
  
  sample of bibletts:


------------------------------

📁 Directory: raw/bibletts/akuapem-twi/train/TIT

- TIT_001_Verse_001.flac

- TIT_001_Verse_001.txt

- TIT_001_Verse_002.flac

- TIT_001_Verse_002.txt

------------------------------

📁 Directory: raw/bibletts/akuapem-twi/train/ZEC

- ZEC_001_Verse_001.flac

- ZEC_001_Verse_001.txt

- ZEC_001_Verse_003.flac

- ZEC_001_Verse_003.txt

------------------------------

📁 Directory: raw/bibletts/akuapem-twi/train/ZEP

- ZEP_001_Verse_001.flac

- ZEP_001_Verse_001.txt

- ZEP_001_Verse_002.flac

- ZEP_001_Verse_002.txt

------------------------------

📁 Directory: raw/bibletts/asante-twi/dev/EZR

- EZR_001_Verse_001.flac

- EZR_001_Verse_001.txt

- EZR_001_Verse_003.flac

- EZR_001_Verse_003.txt

------------------------------

📁 Directory: raw/bibletts/asante-twi/test/COL

- COL_001_Verse_001.flac

- COL_001_Verse_001.txt

- COL_001_Verse_005.flac

- COL_001_Verse_005.txt

------------------------------

📁 Directory: raw/bibletts/asante-twi/train/1CH

- 1CH_001_Verse_008.flac

- 1CH_001_Verse_008.txt

- 1CH_001_Verse_009.flac

- 1CH_001_Verse_009.txt

------------------------------

📁 Directory: raw/bibletts/asante-twi/train/1CO

- 1CO_001_Verse_001.flac

- 1CO_001_Verse_001.txt

- 1CO_001_Verse_002.flac

- 1CO_001_Verse_002.txt


...


the others:

- ZEP_001_Verse_003.flac

- ZEP_001_Verse_003.txt

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_10/__MACOSX/fisd-akuapim-twi-10p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_10/__MACOSX/fisd-akuapim-twi-10p/audios

- ._AkuapemTwiFm18-GO1C7wOd-Tmp002-LIniBG.ogg

- ._AkuapemTwiFm18-GO1C7wOd-Tmp004-li5QsF.ogg

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_10/fisd-akuapim-twi-10p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_10/fisd-akuapim-twi-10p/audios

- AkuapemTwiFm18-GO1C7wOd-Tmp002-LIniBG.ogg

- AkuapemTwiFm18-GO1C7wOd-Tmp004-li5QsF.ogg

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_90/__MACOSX/fisd-akuapim-twi-90p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_90/__MACOSX/fisd-akuapim-twi-90p/audios

- ._AkuapemTwiFm18-GO1C7wOd-Tmp001-LUzv7C.ogg

- ._AkuapemTwiFm18-GO1C7wOd-Tmp001-hdXhtY.ogg

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_90/fisd-akuapim-twi-90p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/akuapem_twi_90/fisd-akuapim-twi-90p/audios

- AkuapemTwiFm18-GO1C7wOd-Tmp001-LUzv7C.ogg

- AkuapemTwiFm18-GO1C7wOd-Tmp001-hdXhtY.ogg

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_10/__MACOSX/fisd-asanti-twi-10p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_10/__MACOSX/fisd-asanti-twi-10p/audios

- ._AsantiTwiFm18-MHdyb4ij-Tmp002-YvH2jV.ogg

- ._AsantiTwiFm18-MHdyb4ij-Tmp004-2TlVsB.ogg

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_10/fisd-asanti-twi-10p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_10/fisd-asanti-twi-10p/audios

- AsantiTwiFm18-MHdyb4ij-Tmp002-YvH2jV.ogg

- AsantiTwiFm18-MHdyb4ij-Tmp004-2TlVsB.ogg

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_90/__MACOSX/fisd-asanti-twi-90p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_90/__MACOSX/fisd-asanti-twi-90p/audios

- ._AsantiTwiFm18-MHdyb4ij-Tmp001-6afLtE.ogg

- ._AsantiTwiFm18-MHdyb4ij-Tmp003-WxTZFG.ogg

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_90/fisd-asanti-twi-90p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/asante_twi_90/fisd-asanti-twi-90p/audios

- AsantiTwiFm18-MHdyb4ij-Tmp001-6afLtE.ogg

- AsantiTwiFm18-MHdyb4ij-Tmp003-WxTZFG.ogg

------------------------------

📁 Directory: raw/financial_inclusion/fante_10/__MACOSX/fisd-fanti-10p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/fante_10/__MACOSX/fisd-fanti-10p/audios

- ._FantiFm16-EBbYRv1F-Tmp013-M2xE4W.ogg

- ._FantiFm16-EBbYRv1F-Tmp034-xrYqcj.ogg

------------------------------

📁 Directory: raw/financial_inclusion/fante_10/fisd-fanti-10p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/fante_10/fisd-fanti-10p/audios

- FantiFm16-EBbYRv1F-Tmp013-M2xE4W.ogg

- FantiFm16-EBbYRv1F-Tmp034-xrYqcj.ogg

------------------------------

📁 Directory: raw/financial_inclusion/fante_90/__MACOSX/fisd-fanti-90p

- ._data.csv

------------------------------

📁 Directory: raw/financial_inclusion/fante_90/__MACOSX/fisd-fanti-90p/audios

- ._FantiFm16-EBbYRv1F-Tmp001-KRX8MC.ogg

- ._FantiFm16-EBbYRv1F-Tmp002-zxqbTS.ogg

------------------------------

📁 Directory: raw/financial_inclusion/fante_90/fisd-fanti-90p

- data.csv

------------------------------

📁 Directory: raw/financial_inclusion/fante_90/fisd-fanti-90p/audios

- FantiFm16-EBbYRv1F-Tmp001-KRX8MC.ogg

- FantiFm16-EBbYRv1F-Tmp002-zxqbTS.ogg

------------------------------

📁 Directory: raw/michsethowusu

- english_twi_sample_1000.csv

------------------------------

📁 Directory: raw/michsethowusu/akuapem_multispeaker_audio_transcribed/test

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/akuapem_multispeaker_audio_transcribed/train

- data-00000-of-00008.arrow

- data-00001-of-00008.arrow

------------------------------

📁 Directory: raw/michsethowusu/fante_multispeaker_audio_transcribed/test

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/fante_multispeaker_audio_transcribed/train

- data-00000-of-00009.arrow

- data-00001-of-00009.arrow

------------------------------

📁 Directory: raw/michsethowusu/ga_multispeaker_audio_transcribed/test

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/ga_multispeaker_audio_transcribed/train

- data-00000-of-00009.arrow

- data-00001-of-00009.arrow

------------------------------

📁 Directory: raw/michsethowusu/translations/english-twi_sentence-pairs/train

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/translations/hausa-twi_sentence-pairs/train

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/translations/swahili-twi_sentence-pairs/train

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/twi-emotions-corpus/train

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/twi-speech-text-parallel-multispeaker/train

- data-00000-of-00014.arrow

- data-00001-of-00014.arrow

------------------------------

📁 Directory: raw/michsethowusu/twi_multispeaker_audio_transcribed/test

- data-00000-of-00001.arrow

------------------------------

📁 Directory: raw/michsethowusu/twi_multispeaker_audio_transcribed/train

- data-00000-of-00007.arrow

- data-00001-of-00007.arrow

------------------------------

📁 Directory: raw/translation_models

- translation_examples.csv 