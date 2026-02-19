# PLANNING.md: Voice AI for Twi/Akan

## 1. Project Vision

To create an open-source, accessible, and high-quality voice interface for the Twi/Akan language, empowering developers to build voice-enabled applications for the Akan-speaking community.

## 2. Proposed Technology Stack

* **ASR Engine:** `faster-whisper`, fine-tuned on a combined dataset (Ashesi + Hugging Face).
* **TTS Engine:** `Coqui TTS`, trained on a curated, high-quality subset of the available data.
* **NLU Engine:** `Hugging Face Transformers` for intent classification.
* **Compute Environment:** `Google Colab` for initial phases, moving to `Runpod` for heavy TTS training.
* **Prototyping Framework:** `Gradio` or `Streamlit` for building a simple web demo.

## 3. Phased Development Plan

### Phase 1: ASR Foundation (The "Ears")
* **Goal:** Produce a reliable ASR model that accurately transcribes Twi/Akan speech.
* **Target Metric:** Achieve a Word Error Rate (WER) below 15% on a held-out test set.
* **Timeline:** 6 Weeks (Q4 2025)

### Phase 2: TTS Voice Creation (The "Voice")
* **Goal:** Create a natural, clear, and intelligible Twi/Akan voice.
* **Target Metric:** Achieve a Mean Opinion Score (MOS) of 3.5+ out of 5.
* **Timeline:** 8 Weeks (Q4 2025 - Q1 2026)

### Phase 3: NLU and Integration (The "Brain")
* **Goal:** Integrate the ASR and TTS models into a simple conversational loop with basic intent recognition.
* **Target Metric:** Successfully handle 5-10 predefined intents (e.g., "What's the weather?", "Tell me a proverb").
* **Timeline:** 4 Weeks (Q1 2026)

### Phase 4: MVP and Deployment
* **Goal:** Package the models into a simple, interactive web application (MVP - Minimum Viable Product).
* **Target Metric:** A deployed Gradio/Streamlit app that allows users to speak a command and hear a spoken response.
* **Timeline:** 6 Weeks (Q2 2026)

## 4. Success Metrics

* **ASR:** Word Error Rate (WER), Character Error Rate (CER).
* **TTS:** Mean Opinion Score (MOS) via subjective listening tests.
* **NLU:** Intent classification accuracy, F1-score.
* **System:** End-to-end latency (time from user speaking to AI responding).