# TASKS – Voice AI for Twi/Akan

## Sprint 1 – Research & Setup
- [ ] Collect and catalog datasets (Ashesi, BibleTTS, Common Voice Twi)
- [ ] Preprocess audio (normalize, trim, remove noise)
- [ ] Prepare Colab notebook for Faster-Whisper testing
- [ ] Benchmark Whisper vs Faster-Whisper on sample Twi data

## Sprint 2 – ASR Development
- [ ] Fine-tune Whisper small/medium on Twi datasets
- [ ] Train Wav2Vec2 baseline for comparison
- [ ] Evaluate WER on Twi transcriptions
- [ ] Document results in RESEARCH.md

## Sprint 3 – TTS Development
- [ ] Train baseline Coqui TTS on BibleTTS
- [ ] Experiment with Kokoro TTS on Twi corpora
- [ ] Test F5-TTS for expressive synthesis
- [ ] Evaluate output quality (MOS survey with native speakers)

## Sprint 4 – Prototype Integration
- [ ] Build web demo (React frontend + FastAPI backend)
- [ ] Add microphone input for ASR
- [ ] Add Twi TTS playback
- [ ] Host backend with GPU inference (RunPod/Colab/Cloud)

## Sprint 5 – Expansion
- [ ] Add Akuapem vs Asante dialect support
- [ ] Collect additional recordings (crowdsourced)
- [ ] Extend TTS voices (male + female speakers)
- [ ] Prepare mobile deployment (Android/iOS)

## Ongoing
- [ ] Monitor new datasets (Masakhane, Lacuna Fund, Common Voice updates)
- [ ] Engage with Twi linguists/community for evaluation
- [ ] Explore adding NLU intent detection (for conversational assistants)
