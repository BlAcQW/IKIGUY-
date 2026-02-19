# TASKS.md: Voice AI for Twi/Akan

This document breaks down the project plan into actionable tasks.

---

### Phase 1: ASR Foundation (The "Ears") - (Target: Q4 2025)

* [ ] **Environment Setup**
    * [ ] Set up a GitHub repository for the project.
    * [ ] Create a Python virtual environment with necessary libraries (`transformers`, `datasets`, `faster-whisper`, `torch`).
    * [ ] Set up a Google Colab notebook for experimentation.
* [ ] **Data Acquisition & Preprocessing**
    * [ ] Download the Ashesi University Financial Inclusion Speech Dataset.
    * [ ] Download the `twi-speech-text-parallel-multispeaker` dataset from Hugging Face.
    * [ ] Write scripts to unify the data formats.
    * [ ] Write a script to clean transcriptions (normalize text, check for errors).
    * [ ] Split the combined dataset into `train`, `validation`, and `test` sets.
* [ ] **Model Fine-Tuning**
    * [ ] Load the pre-trained `faster-whisper` model.
    * [ ] Write and debug the fine-tuning script.
    * [ ] Run the fine-tuning process on Colab or a cloud GPU.
* [ ] **Evaluation**
    * [ ] Write an evaluation script to calculate Word Error Rate (WER) on the test set.
    * [ ] Log results and analyze errors to identify areas for improvement.
    * [ ] Save the final fine-tuned model weights.

---

### Phase 2: TTS Voice Creation (The "Voice") - (Target: Q4 2025 - Q1 2026)

* [ ] **Data Curation**
    * [ ] From the available datasets, select a single speaker with high-quality, clean audio.
    * [ ] Write a script to segment the selected audio into short clips (3-15 seconds).
    * [ ] Manually verify the transcription for at least 1,000 clips.
* [ ] **Environment Setup**
    * [ ] Clone the `Coqui TTS` repository.
    * [ ] Set up the environment and install its dependencies.
    * [ ] Set up cloud GPU instance (e.g., on Runpod or Lambda Labs).
* [ ] **Model Training**
    * [ ] Format the curated dataset according to Coqui TTS specifications.
    * [ ] Configure the model training parameters (`config.json`).
    * [ ] Launch the TTS model training process.
    * [ ] Monitor training progress using TensorBoard.
* [ ] **Evaluation & Synthesis**
    * [ ] After training, use the model to synthesize test sentences.
    * [ ] Conduct informal listening tests to evaluate voice naturalness (MOS).
    * [ ] Fine-tune model parameters and retrain if necessary.
    * [ ] Save the final TTS model.

---

### Phase 3: NLU and Integration (The "Brain") - (Target: Q1 2026)

* [ ] **Intent Definition**
    * [ ] Define a small set of 5-10 intents for the MVP (e.g., `greet`, `ask_weather`, `ask_proverb`).
    * [ ] Create a small dataset of example sentences for each intent in Twi/Akan.
* [ ] **NLU Model Training**
    * [ ] Choose a multilingual transformer model from Hugging Face.
    * [ ] Write and run a script to fine-tune the model for intent classification.
    * [ ] Evaluate the NLU model's accuracy.
* [ ] **Pipeline Integration**
    * [ ] Write a Python script that connects the models: ASR -> NLU -> TTS.
    * [ ] Create simple logic for generating text responses based on classified intent.

---

### Phase 4: MVP and Deployment - (Target: Q2 2026)

* [ ] **Application Development**
    * [ ] Choose a framework (`Gradio` or `Streamlit`).
    * [ ] Build a simple user interface with a "Record Audio" button and a text/audio output area.
    * [ ] Connect the integrated AI pipeline (from Phase 3) to the UI.
* [ ] **Containerization & Deployment**
    * [ ] Write a `Dockerfile` to package the application and all its dependencies.
    * [ ] Deploy the container to a service like Hugging Face Spaces or a cloud provider.
* [ ] **Project Documentation**
    * [ ] Create a `README.md` for the project with setup and usage instructions.
    * [ ] Publish the final models to Hugging Face Hub.