# RESEARCH.md: Voice AI for Twi/Akan

## 1. Project Goal

To develop a foundational, open-source voice AI solution for the Twi/Akan language. The initial aim is to create robust Speech-to-Text (ASR) and Text-to-Speech (TTS) models that can serve as a basis for various applications, such as voice assistants, transcription services, and accessibility tools.

## 2. Core Component Analysis

### 2.1. Automatic Speech Recognition (ASR / Speech-to-Text)

The "ears" of the system. Converts spoken Twi/Akan into text.

* **Primary Candidates:**
    * **Meta MMS (Massively Multilingual Speech):**
        * *Pros:* Extremely broad language support out-of-the-box (~1,100 languages for ASR). A great zero-shot or few-shot starting point.
        * *Cons:* May have lower accuracy for Twi/Akan compared to a specifically fine-tuned model.
    * **OpenAI Whisper (and `faster-whisper`):**
        * *Pros:* Excellent performance with fine-tuning. `faster-whisper` provides significant speed and memory improvements. Strong community support. The `akan-whisper-model` on Hugging Face is a proven starting point.
        * *Cons:* Requires a dedicated fine-tuning process.

* **Conclusion:** `faster-whisper` is the most promising candidate due to its balance of high performance, optimization, and the existence of a pre-tuned Akan model to build upon.

### 2.2. Text-to-Speech (TTS)

The "voice" of the system. Converts text into natural-sounding Twi/Akan speech.

* **Primary Candidates:**
    * **Coqui TTS:**
        * *Pros:* State-of-the-art voice quality. Excellent for voice cloning and creating custom, high-quality voices. Strong open-source community and tools for training.
        * *Cons:* Requires significant training data and computational resources to create a new voice from scratch.
    * **Meta MMS:**
        * *Pros:* Provides TTS for over 1,100 languages, likely including Twi/Akan. A good baseline to have a voice working quickly.
        * *Cons:* Voice quality might be generic and less natural than a dedicated model like one trained with Coqui.
    * **Other Models (f5-tts, Chatterbox, CSM):**
        * *Pros:* Offer advanced features like zero-shot voice cloning and emotional control.
        * *Cons:* May be more experimental or have less documentation for training on a new language.

* **Conclusion:** `Coqui TTS` is the best choice for the long-term goal of creating a high-quality, unique voice. `Meta MMS` can serve as a useful fallback or initial prototype voice.

### 2.3. Natural Language Understanding (NLU)

The "brain" of the system. Interprets the transcribed text to understand user intent.

* **Primary Candidates:**
    * **Hugging Face Transformers:** Use multilingual models like `bert-base-multilingual-cased` or `XLM-RoBERTa` and fine-tune them on a Twi/Akan dataset for tasks like intent classification or entity recognition.
    * **Rasa NLU:** An open-source framework specifically designed for building conversational AI, including intent and entity recognition.
* **Conclusion:** Start with a fine-tuned Transformer model from Hugging Face for simplicity and flexibility.

## 3. Available Datasets

* **Ashesi University Financial Inclusion Speech Dataset:**
    * *Contents:* ~148 hours of speech for Akan (Akuapem Twi, Asante Twi, Fante) and Ga.
    * *Usefulness:* Excellent for both ASR fine-tuning and training a primary TTS model due to its size and domain focus.
* **Hugging Face `twi-speech-text-parallel-multispeaker`:**
    * *Contents:* ~21,000 paired audio recordings and transcriptions.
    * *Usefulness:* A strong supplemental dataset for ASR and TTS.
* **Mozilla Common Voice:**
    * *Contents:* Crowdsourced voice data. The Twi/Akan collection may be small but is constantly growing.
    * *Usefulness:* Good for augmenting training data with diverse voices.

## 4. Computational Resources

* **Initial Prototyping:** Google Colab (Free/Pro tiers) is sufficient for initial experiments and fine-tuning smaller models.
* **Intensive Training:** For training large TTS models (like Coqui) from scratch, a dedicated cloud GPU service is recommended.
    * **Options:** Runpod, Lambda Labs, Vast.ai, Paperspace, or major providers (AWS, GCP, Azure).

## 5. Key Challenges & Open Questions

* **Dialectal Variation:** Akan has multiple dialects. Datasets need to be curated and models may need to be trained to handle this variation.
* **Data Quality:** Audio quality, background noise, and transcription accuracy across all datasets must be verified.
* **Orthography:** Ensure consistent spelling and use of diacritics in text data.
* **Evaluation Metrics:** How will success be measured?
    * *ASR:* Word Error Rate (WER)
    * *TTS:* Mean Opinion Score (MOS)