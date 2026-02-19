# RESEARCH – Voice AI for Underrepresented Languages (Twi/Akan)

## 1. Background
- Many African languages lack robust ASR (speech-to-text) and TTS (text-to-speech) systems.
- Existing voice assistants (Alexa, Siri, Google Assistant) rarely support these languages.
- Building inclusive AI requires curated datasets, adapted models, and efficient GPU resources.

---

## 2. Existing Datasets
- **Ashesi Financial Inclusion Speech Dataset (~148h)** – Akan (Akuapem, Asante, Fante) + Ga
- **Fair-Forward Dataset (~148h)** – Financial domain, multiple dialects
- **Twi Speech-Text Parallel Dataset** (HuggingFace) – 21k pairs
- **Twi Words Parallel Dataset** (HuggingFace) – 413k pairs
- **BibleTTS** – High-quality single speaker Twi audio
- **Common Voice Twi (Mozilla)** – Crowdsourced, CC0 license
- **UGAkan Impaired Speech Dataset (~50h)** – Adds diversity & robustness
- **Lingua Libre** – Community-driven pronunciations

---

## 3. Tools & Frameworks
### ASR
- **Whisper / Faster-Whisper (CTranslate2 optimized)** – multilingual, strong baseline
- **Wav2Vec 2.0** – good for low-resource settings
- **Kaldi / SpeechBrain** – modular, flexible pipelines

### TTS
- **F5-TTS** – expressive, zero-shot, multilingual diffusion-based TTS
- **Kokoro TTS** – lightweight, multilingual, fast deployment
- **Coqui TTS** – easy to fine-tune on Twi
- **Festival/Festvox/eSpeakNG** – classic, lightweight TTS engines

### Infrastructure
- **Colab/Kaggle** – free prototyping GPUs
- **RunPod, CoreWeave, Lambda Labs, Paperspace** – scalable GPU rental
- **Local GPU rigs** – control + no quotas

---

## 4. Related Projects
- **Abena AI (Mobobi)** – Twi voice assistant, offline Android deployment
- **Masakhane NLP** – collaborative African language research
- **Proto Voice AI** – underserved language deployments

---

## 5. Knowledge Gaps
- Limited phoneme alignment for Twi
- Few pretrained TTS voices beyond BibleTTS
- Evaluation benchmarks (WER, MOS) underdeveloped for Akan languages
