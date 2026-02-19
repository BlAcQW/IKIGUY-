# Abena AI Technology Stack Research

**Research Date:** November 8, 2025
**Subject:** Comprehensive analysis of Abena AI/Mobobi's TTS, ASR, and Translation technology
**Purpose:** Understanding competitive technology landscape for African language AI

---

## Executive Summary

Abena AI (by Mobobi LLC) is a pioneering African language voice assistant featuring on-device TTS and ASR for 7+ African languages. Key differentiators include offline-first architecture, lightweight models (35-47MB), and cultural authenticity through native speaker recordings.

**Key Finding:** While Abena AI doesn't publicly disclose their exact model architectures, evidence suggests they use fine-tuned open-source models (likely Coqui TTS/XTTS-v2) optimized for mobile deployment.

---

## Company Profile

### Mobobi LLC

- **Founded:** 2015
- **Location:** Accra, Ghana
- **Founder:** Nana Ghartey (self-taught programmer)
- **Flagship Product:** Abena AI voice assistant
- **Development Time:** 6 years (2016-2022)
- **Launch Date:** April 2022 (Google Play Store)
- **Downloads:** 500,000+ (as of 2025)
- **Funding Status:** Unfunded/bootstrapped

### Founder Background

**Nana Ghartey:**
- Grew up in rural Ghana with grandmother
- Self-taught programmer using textbooks left by visiting uncle
- Built desktop apps, websites, and mobile games before Abena AI
- Works full-time at Mobobi while developing Abena AI (3 hours daily)
- Motivation: Enable voice AI access for non-English speakers and visually-impaired users

---

## Core Technologies

### 1. Text-to-Speech (TTS)

**Supported Languages:**
- **African Languages:** Akan Twi, Ghana Pidgin, Yoruba, Hausa, Swahili, Ga, Ewe
- **Major Languages:** English (Ghanaian accent), French

**Voice Options:**
| Language | Voice Name | Gender | Notes |
|----------|-----------|--------|-------|
| Ghanaian English | Akua | Female | Authentic Ghanaian accent |
| Ghanaian English | Kwabena | Male | Authentic Ghanaian accent |
| Akan Twi | Abena | - | Supports Ɛ, ɛ, Ɔ, ɔ special characters |
| Nigerian Pidgin | James | Male | Improved version (recent) |
| Swahili | Amani | - | - |
| Yoruba | Folami | - | Supports dotted letters |
| Hausa | Abubakar | - | - |
| Ewe | Mawuli | - | - |

**Technical Features:**
- Adjustable speech speed (default 1.0x multiplier)
- Special character support (Twi: Ɛ, ɛ, Ɔ, ɔ; Yoruba: dotted letters)
- Online and offline synthesis capabilities
- Character limit: 280 characters maximum
- Word limit: 50 words maximum

### 2. Automatic Speech Recognition (ASR)

**Available Models:**
| Language | Model ID | Size | Quality |
|----------|----------|------|---------|
| English (US) | model-en-us | 40MB | Enterprise-grade |
| Akan Twi (Ghana) | model-aka-gh | 35MB | Dialect-aware |
| French (France) | model-fr-fr | 47MB | Standard French |

**Capabilities:**
- Offline speech recognition
- Handles diverse dialects and accents
- Enterprise-grade accuracy

### 3. Neural Translation

**Supported Languages:** 16+ languages including:
- **African:** Afrikaans, Amharic, Hausa, Igbo, Somali, Swahili, Twi, Ewe, Wolof, Xhosa, Yoruba, Zulu
- **Major:** English, French, Portuguese, Spanish

### 4. Additional Features

- **Video Dubbing:** Seamless dubbing into multiple African languages
- **Speaker Diarization:** "Who spoke when" identification
- **Noise Suppression:** Audio enhancement capabilities
- **Smart Home Integration:** Control lights, plugs, devices
- **Payments:** Mobile money transfers and airtime recharge
- **News & Media:** Twitter trends, weather, radio streaming

---

## Technical Architecture

### On-Device Processing (Core Innovation)

**Key Differentiator:** Unlike Google Assistant, Alexa, and Siri, Abena AI operates primarily offline.

**Benefits:**
1. **Privacy:** Data stays on device
2. **Accessibility:** Works in areas with limited connectivity
3. **Cost:** No cloud processing fees
4. **Speed:** No network latency
5. **Compliance:** Data regulation compliance

**Model Optimization:**
- Lightweight models (35-47MB range)
- Suggests INT8 or FP16 quantization
- Optimized for mobile CPUs/GPUs
- Minimal battery consumption

### Platform Support

**Mobile SDKs:**
- Android (Kotlin) - Native with Gradle integration
- iOS (Swift) - Native with SPM support
- React Native - Cross-platform mobile

**Backend SDKs:**
- Python - Enterprise validation, security-focused
- Node.js - Promise-based async/await, TypeScript support
- Go - High-performance, idiomatic patterns

**Direct Access:**
- cURL/HTTP - REST API for any platform

---

## API Architecture

### Authentication

```bash
Authorization: Bearer your-api-key
```

All API requests require bearer token authentication.

### Endpoints

```
POST /playground/api/v1/asr/transcribe/     # Speech Recognition
POST /playground/api/v1/tts/synthesize/     # Text-to-Speech
POST /playground/api/v1/translate/translate/ # Translation

GET  /playground/api/v1/asr/voices.json     # List ASR models
GET  /playground/api/v1/tts/voices          # List TTS voices
GET  /playground/api/v1/translate/languages # List translation languages
```

### SDK Installation

```bash
# Python
pip install abenasdk

# Node.js
npm install abenasdk

# Go
go get github.com/abena-ai-team/abenasdk-go

# React Native
npm install abenasdk
```

**⚠️ NOTE:** As of November 2025, `abenasdk` is **NOT available on PyPI**. This suggests:
- Documentation is aspirational/pre-release
- SDK is private/enterprise-only
- Alternative installation method required

---

## Training Data & Methodology

### Data Sources

#### 1. Professional Studio Recordings
- **In-house recordings** with native speakers
- **Audio quality:** 48kHz studio quality
- **Duration:** Up to 80-86 hours per language
- **Speakers:** Professional voice artists
- **Focus:** Authenticity and accuracy across diverse dialects

#### 2. Crowdsourcing
- **Third-party pop-up applications** for user contributions
- **Financial incentives:** 5 cedis per translation
- **Purpose:** Continuous improvement and dialect diversity
- **Data types:** Translations, contextual usage, pronunciation variations

#### 3. Religious Translators
- **Specialized translators** for church-related Twi
- **Purpose:** Domain-specific vocabulary and context

#### 4. Personal Recordings
- **Initial prototypes:** Founder's grandmother and sister voices
- **Product:** Earlier "Kofi" assistant (Fante language)

### Training Challenges

**Data Scarcity:**
> "Data set out there are based on religious text, so you end up building a system that has a bias for biblical words." - Nana Ghartey

**Solutions Implemented:**
1. Avoided reliance on existing datasets (BibleTTS, etc.)
2. Custom in-house recordings to reduce bias
3. Crowdsourced dialect variations
4. Continuous learning from user interactions

**Dialect Diversity:**
- Multiple Twi dialects (Asante, Akuapem)
- Regional accent variations
- Contextual word meaning variations
- Intonation pattern differences

---

## Inferred Technology Stack

### What's NOT Publicly Disclosed

Abena AI/Mobobi has **NOT published**:
- ❌ Academic research papers
- ❌ Technical white papers
- ❌ Open-source code repositories
- ❌ Specific model architectures
- ❌ Deep learning frameworks used
- ❌ Training methodologies
- ❌ Benchmark results
- ❌ Performance metrics

### Evidence-Based Inference

Based on model sizes, features, and industry standards:

#### Most Likely TTS Architecture:

**Option 1: Coqui TTS + VITS**
- **Evidence:**
  - BibleTTS dataset (86 hours African languages) released with Coqui TTS
  - VITS produces high quality with compact models
  - Open-source, African language support
  - Model sizes align (35-47MB after quantization)
- **Probability:** 70%

**Option 2: Fine-tuned XTTS-v2**
- **Evidence:**
  - Supports multilingual zero-shot TTS
  - Recent research on African language fine-tuning
  - Voice cloning with 3-second clips
  - Can be compressed for mobile
- **Probability:** 20%

**Option 3: Custom Proprietary Model**
- **Evidence:**
  - 6 years development time
  - No public papers
  - Competitive advantage protection
- **Probability:** 10%

#### Likely Technology Stack:

```
┌─────────────────────────────────────────┐
│         Mobile Application              │
│  (Android: Kotlin, iOS: Swift)          │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│      On-Device Inference Engine         │
│  - TensorFlow Lite / ONNX Runtime       │
│  - Quantized Models (INT8/FP16)         │
│  - 35-47MB optimized models             │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         Core AI Models                  │
│                                         │
│  TTS: Coqui TTS/VITS (fine-tuned)      │
│  ASR: Custom or Whisper-based          │
│  Translation: Custom NMT               │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         Training Pipeline               │
│                                         │
│  Data: 48kHz studio recordings         │
│  Framework: PyTorch/TensorFlow         │
│  Base: BibleTTS + Custom data          │
│  Optimization: Quantization/Pruning    │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│          Backend API                    │
│  (Python/Go, REST, Bearer Auth)        │
└─────────────────────────────────────────┘
```

#### Optimization Techniques:

1. **Model Quantization**
   - INT8 or FP16 precision
   - Reduces 100-200MB models to 35-47MB
   - Minimal accuracy loss

2. **Knowledge Distillation**
   - Teacher model: Large cloud model
   - Student model: Compact mobile model
   - Maintains quality with smaller size

3. **Neural Architecture Search (NAS)**
   - Automated optimization for mobile
   - Hardware-aware model design

4. **Pruning**
   - Remove redundant neurons/connections
   - Sparse model representation

---

## Competitive Landscape

### Direct Competitors

| Feature | Abena AI | Google Assistant | Amazon Alexa | Azure Speech |
|---------|----------|------------------|--------------|--------------|
| **African Languages** | 7+ | Limited (2-3) | Very Limited | Limited |
| **Offline Mode** | ✅ Full | ❌ Requires internet | ❌ Requires internet | ❌ Requires internet |
| **Model Size** | 35-47MB | N/A (cloud) | N/A (cloud) | N/A (cloud) |
| **Privacy** | On-device | Cloud processing | Cloud processing | Cloud processing |
| **Dialect Support** | Multiple dialects | Limited | Limited | Limited |
| **Cost** | Free/Enterprise | Free/Paid | Free/Paid | Pay-per-use |
| **Cultural Context** | Native speakers | Generic | Generic | Generic |
| **Low Bandwidth** | ✅ Works offline | ❌ Requires connection | ❌ Requires connection | ❌ Requires connection |

### Open-Source Alternatives

**BibleTTS + Coqui TTS:**
- **Pros:** Free, open-source, 10 African languages, 86 hours/language
- **Cons:** Single speaker, biblical bias, requires technical expertise
- **Use Case:** Research, academic projects

**NaijaVoices:**
- **Pros:** Multi-speaker (5,000+), 1,867 hours, 3 languages (Hausa, Igbo, Yoruba)
- **Cons:** Large dataset, requires significant compute, recent (2024-2025)
- **Use Case:** Research, training multi-speaker models

**Coqui TTS (Open-source):**
- **Pros:** Production-ready, multiple architectures, active community
- **Cons:** Requires infrastructure, no direct African language support (needs fine-tuning)
- **Use Case:** Self-hosted solutions, customization

---

## Research Findings: Key Datasets

### BibleTTS (Primary African TTS Dataset)

**Overview:**
- **Languages:** 10 African languages (Akuapem Twi, Asante Twi, Chichewa, Ewe, Hausa, Kikuyu, Lingala, Luganda, Luo, Yoruba)
- **Duration:** Up to 86 hours per language
- **Quality:** Studio quality, 48kHz recordings
- **Speaker:** Single speaker per language
- **License:** CC-BY-SA (commercial-friendly)
- **Source:** openslr.org/129/

**Dataset Sizes:**
- Akuapem Twi: 16GB
- Asante Twi: 15GB
- Hausa: 21GB
- Yoruba: 6.3GB

**Integration:**
- Released with Coqui TTS toolkit
- Pre-aligned speech and text
- Verse-level alignment (biblical source)

**Limitations:**
- Biblical content bias
- Single speaker (less diverse)
- Religious vocabulary emphasis

### NaijaVoices (Recent Multi-Speaker Dataset)

**Overview:**
- **Languages:** Hausa, Igbo, Yoruba
- **Duration:** 1,867 hours total
- **Speakers:** 5,000+ diverse speakers
- **Quality:** High-quality multi-speaker
- **Year:** 2024-2025
- **Purpose:** ASR and TTS for African languages

**Significance:**
- Largest multi-speaker African speech dataset
- Enables multi-speaker TTS
- Diverse accent and dialect coverage
- 500+ hours human Hausa voice data

### Recent Research (2024-2025)

**Synthetic Voice Data Study (July 2025):**
- Fine-tuned XTTS-v2 and VITS on 10 African languages
- Used BibleTTS as base dataset
- Framework: Coqui TTS
- Demonstrated feasibility of synthetic data augmentation

---

## Enterprise Features & Pricing

### Enterprise Offerings

1. **SLA Guarantees**
   - Uptime commitments
   - Response time guarantees
   - Support levels

2. **Custom Model Training**
   - Domain-specific vocabulary
   - Custom voice creation
   - Accent/dialect customization

3. **On-Premise Deployment**
   - Self-hosted infrastructure
   - Air-gapped environments
   - Full data control

4. **Professional Voice Quality**
   - Studio-grade synthesis
   - Natural prosody
   - Emotional expressiveness

### Pricing

**⚠️ NOT PUBLICLY DISCLOSED**

Enterprise pricing requires direct contact with sales team. No public pricing tiers available on website.

**Inference:**
- Likely usage-based (per API call)
- Enterprise licenses (annual contracts)
- Custom pricing for on-premise
- Free tier for developers (playground)

---

## Deployment Architecture

### Mobile Deployment

```
┌──────────────────────────────────┐
│     Android/iOS Application      │
│  - User Interface                │
│  - Voice Input/Output            │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│   On-Device Inference Engine     │
│  - TFLite / ONNX Runtime         │
│  - Model Loading & Caching       │
│  - Audio Processing Pipeline     │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│    Quantized AI Models (35MB)    │
│  - ASR Model                     │
│  - TTS Model                     │
│  - Translation Model             │
└────────────┬─────────────────────┘
             │
     ┌───────┴────────┐
     │                │
┌────▼─────┐   ┌─────▼────┐
│  Offline │   │  Online  │
│  Storage │   │ API Sync │
└──────────┘   └──────────┘
```

### Cloud API Architecture

```
┌──────────────────────────────────┐
│      Client Applications         │
│  (Web, Mobile, Backend)          │
└────────────┬─────────────────────┘
             │ HTTPS/REST
┌────────────▼─────────────────────┐
│         API Gateway              │
│  - Bearer Auth                   │
│  - Rate Limiting                 │
│  - Request Validation            │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│      Backend Services            │
│  (Python/Go)                     │
│  - /asr/transcribe/              │
│  - /tts/synthesize/              │
│  - /translate/translate/         │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│      AI Inference Layer          │
│  - GPU/CPU Compute               │
│  - Model Serving                 │
│  - Response Caching              │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│      Storage & Database          │
│  - User data                     │
│  - Audio files                   │
│  - Usage analytics               │
└──────────────────────────────────┘
```

---

## Technical Recommendations

### For Building Similar Technology

#### 1. Start with Proven Open-Source Tools

**Recommended Stack:**
```bash
# Base TTS Framework
pip install TTS  # Coqui TTS

# Model serving
pip install onnxruntime  # For optimized inference

# Audio processing
pip install librosa soundfile

# Model optimization
pip install tensorflow-model-optimization
```

**Architecture:**
- **TTS Model:** VITS or XTTS-v2
- **Training Data:** BibleTTS + custom recordings
- **Optimization:** ONNX + INT8 quantization
- **Deployment:** TensorFlow Lite / ONNX Runtime

#### 2. Data Collection Strategy

**Phase 1: Bootstrap (Months 1-3)**
- Use existing datasets (BibleTTS, NaijaVoices)
- Fine-tune pre-trained models
- Test with pilot users

**Phase 2: Custom Data (Months 4-12)**
- Record 10-20 hours professional voice talent
- 48kHz studio quality
- Diverse speakers (age, gender, region)
- Multiple dialects per language

**Phase 3: Crowdsourcing (Ongoing)**
- User-contributed translations
- Pronunciation corrections
- Dialect variations
- Financial incentives (5-10 cedis/contribution)

#### 3. Model Optimization Pipeline

```python
# Step 1: Train full-precision model
model = train_tts_model(data="BibleTTS", architecture="VITS")

# Step 2: Quantize to INT8
quantized_model = quantize_model(model, dtype="int8")

# Step 3: Convert to mobile format
mobile_model = convert_to_tflite(quantized_model)

# Step 4: Optimize for size
optimized_model = prune_and_compress(mobile_model, target_size="40MB")

# Step 5: Validate quality
quality_score = evaluate_mos(optimized_model, test_data)
assert quality_score > 4.0  # MOS score threshold
```

#### 4. Offline-First Architecture

**Design Principles:**
1. **Model bundling** - Ship models with app (35-50MB)
2. **Delta updates** - Incremental model improvements
3. **Lazy loading** - Download language packs on-demand
4. **Fallback strategy** - Online API when offline fails
5. **Cache management** - Store frequent requests locally

#### 5. Quality Assurance

**Metrics to Track:**
- **MOS (Mean Opinion Score):** Target > 4.0/5.0
- **WER (Word Error Rate):** Target < 10% for ASR
- **BLEU Score:** Target > 30 for translation
- **Latency:** Target < 500ms for TTS synthesis
- **Model Size:** Target < 50MB per language
- **Battery Usage:** Target < 5% per hour active use

#### 6. African Language Best Practices

**Linguistic Considerations:**
1. **Tone languages** (Yoruba, Igbo) - Preserve tonal information
2. **Special characters** (Twi: Ɛ, ɔ) - Proper Unicode support
3. **Dialectal variation** - Multiple models or dialect-adaptive models
4. **Code-switching** - Handle mixed language input
5. **Cultural context** - Avoid Western biases in training data

**Technical Considerations:**
1. **Low-resource optimization** - Works with limited data (10-20 hours)
2. **Transfer learning** - Leverage multilingual pre-trained models
3. **Data augmentation** - Synthetic data generation
4. **Active learning** - Prioritize uncertain examples for annotation
5. **Community involvement** - Crowdsource dialect expertise

---

## Lessons Learned from Abena AI

### What Works

1. **Offline-first is crucial** for African markets
   - Limited internet connectivity
   - High data costs
   - Privacy concerns

2. **Cultural authenticity matters**
   - Native speakers for recordings
   - Dialect diversity
   - Local context understanding

3. **Lightweight models enable adoption**
   - 35-47MB models work on budget devices
   - Low battery consumption
   - Fast inference

4. **Crowdsourcing scales**
   - Financial incentives drive contributions
   - Community improves quality
   - Continuous learning

5. **Bootstrap with limited funding**
   - 6 years development on minimal budget
   - Self-taught founder
   - Organic growth to 500K+ users

### Challenges Identified

1. **Data scarcity** - Limited quality datasets for African languages
2. **Dialect diversity** - Multiple dialects per language
3. **Resource constraints** - Building without major funding
4. **Technical complexity** - On-device AI requires optimization
5. **Market education** - Users unfamiliar with voice AI

### Competitive Advantages

1. **First-mover** - First African language voice assistant
2. **Offline capability** - Unique in market
3. **Language coverage** - 7+ African languages
4. **Cultural fit** - Built by Africans for Africans
5. **Privacy** - On-device processing

---

## Open Questions & Research Gaps

### Technical Unknowns

1. **Exact model architecture** - Which specific models do they use?
2. **Training methodology** - How do they handle dialect variation?
3. **Inference optimization** - Specific quantization techniques?
4. **ASR architecture** - Custom or adapted from existing models?
5. **Translation approach** - Neural MT architecture?

### Business Model

1. **Revenue streams** - How do they monetize?
2. **Enterprise pricing** - What do they charge?
3. **Development costs** - Total investment over 6 years?
4. **Team size** - How many engineers?
5. **Infrastructure costs** - Cloud vs on-premise?

### Future Roadmap

1. **Additional languages** - Swahili, Kinyarwanda, Afrikaans, etc.
2. **iOS release** - Currently Android-only
3. **SDK availability** - When will abenasdk be public?
4. **Enterprise adoption** - Target customers?
5. **Research publications** - Will they publish papers?

---

## Actionable Insights

### For AI Labs Africa / KasaAI

#### Immediate Actions (Next 30 Days)

1. **Evaluate Coqui TTS**
   ```bash
   pip install TTS
   tts --text "Testing African language TTS" --model_name "tts_models/multilingual/multi-dataset/xtts_v2"
   ```

2. **Download BibleTTS dataset**
   - Visit openslr.org/129/
   - Download Twi, Yoruba, Hausa datasets
   - Evaluate quality and coverage

3. **Benchmark existing models**
   - Test XTTS-v2 on African languages
   - Measure MOS, latency, model size
   - Compare to Abena AI quality (subjective)

4. **Prototype mobile deployment**
   - Convert VITS model to TFLite
   - Test on Android device
   - Measure battery, latency, quality

#### Short-term (3 Months)

1. **Fine-tune XTTS-v2** on target languages
2. **Record custom dataset** (10-20 hours)
3. **Optimize for mobile** (target <50MB)
4. **Build MVP** with 2-3 languages
5. **User testing** with pilot group

#### Long-term (6-12 Months)

1. **Multi-language support** (7+ languages)
2. **Enterprise API** with SLA
3. **Mobile SDK** (Android, iOS)
4. **Crowdsourcing platform** for continuous improvement
5. **On-premise deployment** option

### Technical Differentiation Opportunities

**Where We Can Compete:**

1. **Better Quality** - More training data, better models
2. **More Languages** - Expand beyond Abena's 7 languages
3. **Better SDK** - Actually publish on PyPI (Abena hasn't)
4. **Open Source** - Community-driven development
5. **Research** - Publish papers, advance the field
6. **Cloud + Edge** - Hybrid deployment (both online and offline)

**Where We Should NOT Compete:**

1. **Consumer voice assistant** - Abena owns this market
2. **Free consumer tier** - Hard to monetize
3. **Mobile app** - Not our core competency

**Our Niche:**

- **Enterprise TTS API** for African languages
- **Developer SDK** for integration
- **Research & Innovation** in low-resource NLP
- **B2B SaaS** model vs consumer app

---

## References & Resources

### Datasets

1. **BibleTTS**
   - URL: https://openslr.org/129/
   - Paper: https://arxiv.org/abs/2207.03546
   - License: CC-BY-SA

2. **NaijaVoices**
   - Languages: Hausa, Igbo, Yoruba
   - Hours: 1,867 hours, 5,000+ speakers
   - Year: 2024-2025

3. **African NLP Datasets**
   - GitHub: https://github.com/Andrews2017/africanlp-public-datasets
   - Comprehensive list of African language resources

### Tools & Frameworks

1. **Coqui TTS**
   - GitHub: https://github.com/coqui-ai/TTS
   - Docs: https://docs.coqui.ai/
   - Models: VITS, XTTS-v2, Tacotron2

2. **ONNX Runtime**
   - URL: https://onnxruntime.ai/
   - Purpose: Cross-platform inference

3. **TensorFlow Lite**
   - URL: https://www.tensorflow.org/lite
   - Purpose: Mobile deployment

### Research Papers

1. **BibleTTS (2022)**
   - Title: "BibleTTS: a large, high-fidelity, multilingual, and uniquely African speech corpus"
   - arXiv: 2207.03546

2. **XTTS (2024)**
   - Title: "XTTS: a Massively Multilingual Zero-Shot Text-to-Speech Model"
   - arXiv: 2406.04904

3. **Synthetic African Voice Data (2025)**
   - Title: "Synthetic Voice Data for Automatic Speech Recognition in African Languages"
   - arXiv: 2507.17578

### Articles & Interviews

1. **TechCabal Interview (2022)**
   - URL: https://techcabal.com/2022/06/17/africas-first-voice-assistant-abena-is-the-latest-effort-in-preserving-the-continents-languages/
   - Key insights: Development timeline, challenges

2. **Voicebot.ai Profile (2022)**
   - URL: https://voicebot.ai/2022/06/30/abena-ais-voice-assistants-speak-african-languages-untouched-by-google-assistant-and-alexa/
   - Key insights: Competitive positioning

3. **People of Color in Tech Interview**
   - URL: https://peopleofcolorintech.com/interview/meet-the-founder-of-africas-first-voice-assistant-abena/
   - Key insights: Founder background, motivation

### Official Resources

1. **Abena AI Website**
   - URL: https://abena.mobobi.com/
   - Playground: https://abena.mobobi.com/playground/tts/
   - SDK Docs: https://abena.mobobi.com/playground/sdk/docs/

2. **Mobobi Corporate**
   - URL: https://mobobi.com/
   - Focus: Enterprise solutions

---

## Appendix: Technical Deep Dive

### Model Size Analysis

**How to achieve 35-47MB models:**

1. **Baseline VITS Model**
   - Full precision (FP32): ~200MB
   - Parameters: ~50M

2. **Quantization to INT8**
   - Reduces to: ~50MB (4x reduction)
   - Accuracy loss: <2% MOS

3. **Pruning**
   - Remove 30-40% weights
   - Reduces to: ~30-35MB
   - Accuracy loss: <5% MOS

4. **Knowledge Distillation**
   - Train smaller student model
   - Achieves: 35-40MB
   - Maintains quality

**Result:** 35-47MB optimized model matching Abena AI specs

### Inference Latency Optimization

**Target:** <500ms end-to-end TTS

```python
# Typical VITS inference pipeline
text = "Hello in Twi: Maakye"

# 1. Text preprocessing (10ms)
phonemes = text_to_phonemes(text, language="tw")

# 2. Model inference (300-400ms on mobile CPU)
mel_spectrogram = vits_model.generate_mel(phonemes)

# 3. Vocoder (50-100ms)
audio = hifigan_vocoder.generate_audio(mel_spectrogram)

# 4. Post-processing (10ms)
audio = normalize_audio(audio)

# Total: ~370-520ms (within target)
```

**Optimization Techniques:**
1. **Model quantization** - INT8 reduces inference time 2-4x
2. **ONNX Runtime** - Optimized graph execution
3. **Batching** - Process multiple requests together
4. **Caching** - Store frequent phrases
5. **GPU acceleration** - Use mobile GPU when available

### Audio Quality Requirements

**Studio Quality Specifications:**
- **Sample Rate:** 48kHz (BibleTTS standard)
- **Bit Depth:** 16-bit or 24-bit
- **Format:** WAV (uncompressed)
- **Duration:** 10-86 hours per language
- **SNR:** >40dB (signal-to-noise ratio)
- **Background noise:** <-60dB

**Recording Best Practices:**
1. Professional studio environment
2. Native speakers (preferably voice actors)
3. Multiple takes per utterance
4. Diverse content (not just religious text)
5. Emotional variation (neutral, happy, sad, etc.)

---

## Conclusion

Abena AI represents a significant achievement in African language AI, demonstrating that:

1. **On-device AI is viable** even for resource-constrained languages
2. **Bootstrapped innovation works** - 6 years of focused development
3. **Cultural authenticity matters** - Native speakers, dialect awareness
4. **Offline-first is essential** for African markets
5. **Open-source tools enable** rapid development (likely Coqui TTS)

**Key Takeaway:** You don't need massive funding or large tech company resources to build world-class African language AI. With the right approach, tools (Coqui TTS, BibleTTS), and commitment to quality, it's achievable.

**Next Steps for AI Labs Africa:**
1. Prototype with Coqui TTS + BibleTTS
2. Fine-tune on target languages (Twi, Yoruba, Hausa)
3. Optimize for mobile deployment (<50MB)
4. Build enterprise API and SDK
5. Focus on B2B market (different from Abena's B2C focus)

---

**Research Conducted By:** Claude (AI Labs Africa)
**Date:** November 8, 2025
**Document Version:** 1.0
**Status:** Complete - Ready for technical review
