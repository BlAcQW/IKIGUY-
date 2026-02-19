



Here’s a compact, builder-friendly overview. I split it into three tables (STT, TTS, Telephony) and then explain where **Meta MMS** sits and how it compares.

# STT (speech → text)

| Provider / Model                     | Deploy style          |   Streaming? | Language reach (approx) | Notable strengths / use-cases                                                  |
| ------------------------------------ | --------------------- | -----------: | ----------------------: | ------------------------------------------------------------------------------ |
| **Google Speech-to-Text v2**         | Cloud                 |          Yes |                    100+ | Mature SDKs, robust streaming for voice agents. ([Google Cloud][1])            |
| **Azure Speech to Text**             | Cloud / containers    |          Yes |                    100+ | Realtime + batch, enterprise integration. ([Microsoft Learn][2])               |
| **Amazon Transcribe**                | Cloud                 |          Yes |                    Many | HTTP/2 & WebSocket streaming options. ([AWS Documentation][3])                 |
| **Deepgram**                         | Cloud                 |          Yes |                     30+ | Strong realtime accuracy/latency; easy WebSocket APIs. ([Deepgram Docs][4])    |
| **Speechmatics**                     | Cloud / on-prem       |          Yes |                  50–55+ | Broad multilingual coverage; enterprise features. ([docs.speechmatics.com][5]) |
| **OpenAI Whisper / faster-whisper**  | Self-host             | Via your app |                     90+ | Open-source baseline with good accuracy; tuneable. ([OpenAI Help Center][6])   |
| **NVIDIA Riva (Parakeet/Conformer)** | On-prem (GPU)         |          Yes |                     20+ | Production-grade low-latency pipelines on your infra. ([NVIDIA Docs][7])       |
| **Vosk**                             | On-device / self-host | Via your app |                     20+ | Lightweight offline recognition (Pi/Android/iOS). ([Alpha Cephei][8])          |

*Sources for this table: Google streaming docs; Azure STT; Amazon Transcribe streaming; Deepgram live streaming; Speechmatics languages; Whisper FAQ; NVIDIA Riva performance; Vosk overview.* ([Google Cloud][1], [Microsoft Learn][2], [AWS Documentation][3], [Deepgram Docs][4], [docs.speechmatics.com][5], [OpenAI Help Center][6], [NVIDIA Docs][7], [Alpha Cephei][8])

---

# TTS (text → speech)

| Provider / Model           | Deploy style       | Realtime streaming? | Voice cloning?              | Notes                                                                                |
| -------------------------- | ------------------ | ------------------- | --------------------------- | ------------------------------------------------------------------------------------ |
| **Google Cloud TTS**       | Cloud              | Yes (stream)        | No                          | Large catalog (WaveNet/Neural), SSML control. ([Google Cloud][9])                    |
| **Azure Neural TTS**       | Cloud / containers | Yes                 | Custom neural voices        | Styles/roles; “HD” voices available. ([Microsoft Learn][10])                         |
| **Amazon Polly**           | Cloud              | Yes                 | No (custom lexicons)        | Standard/Neural/Generative engines. ([AWS Documentation][11])                        |
| **ElevenLabs**             | Cloud              | Yes                 | **Instant/Pro cloning**     | Multilingual, simple API. ([ElevenLabs][12])                                         |
| **Play.ht**                | Cloud              | Yes                 | **Instant cloning (\~30s)** | Creator-friendly tools + streaming. ([PlayHT Text to Speech API][13], [Play.ht][14]) |
| **Deepgram Aura TTS**      | Cloud              | Yes                 | No                          | WebSocket streaming TTS. ([Deepgram Docs][15])                                       |
| **Coqui XTTS**             | Self-host          | Yes (via your app)  | **Few-sec sample**          | Open-source cross-lingual cloning. ([Coqui AI][16], [Hugging Face][17])              |
| **NVIDIA Riva Magpie TTS** | On-prem (GPU)      | Yes                 | Customizable                | Enterprise-grade on your infra. ([NVIDIA][18], [NVIDIA Docs][19])                    |

*Sources for this table: Google TTS (SSML/voices); Azure TTS; Amazon Polly; ElevenLabs; Play.ht; Deepgram TTS; Coqui XTTS; NVIDIA Riva Magpie.* ([Google Cloud][9], [Microsoft Learn][10], [AWS Documentation][11], [ElevenLabs][12], [PlayHT Text to Speech API][13], [Play.ht][14], [Deepgram Docs][15], [Coqui AI][16], [Hugging Face][17], [NVIDIA][18], [NVIDIA Docs][19])

---

# Telephony & voice transport (to connect phone calls to AI)

| Provider                                      | Key capability                                               | Why it matters                                                                                   |
| --------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Twilio Voice – Media Streams / `<Stream>`** | Forks raw call audio to your WebSocket (uni/bi-directional). | Essential for realtime STT→LLM→TTS “voice agents.” ([Twilio][20])                                |
| **Telnyx Programmable Voice**                 | Media forking over secure WebSockets; JS/WebRTC SDKs.        | Low-latency streaming and return audio; good for agents. ([Telnyx Developers][21], [Telnyx][22]) |
| **Vonage (Nexmo) Voice API**                  | NCCO call control + WebSocket audio.                         | Simple call flows + realtime audio access. ([Vonage API Developer][23])                          |

---

# Where does **Meta MMS** fit? How it compares

**What it is:** Open research models from Meta (“Massively Multilingual Speech”) that cover \~**1,107 languages** for **ASR** *and* **TTS**, plus **LID** for **\~4,000** languages. Released for non-commercial use (CC-BY-NC 4.0). ([Meta AI][24], [Hugging Face][25], [파이토치 한국 사용자 모임][26])

**How it compares (at a glance):**

* **Coverage vs others:** MMS massively outscales commercial APIs on *breadth* (especially long-tail languages). Whisper covers \~90+; Speechmatics \~50–55+; clouds vary by feature. MMS aims at 1,107 languages. ([Hugging Face][25], [docs.speechmatics.com][5], [Microsoft Learn][2])
* **Deployment:** MMS is **self-hosted** models (no managed API). You’ll package them for batch or streaming yourself; great for research, pilots, or when cloud vendors don’t support your language. (Meta blog + HF docs describe the models, not a hosted service.) ([Meta AI][24], [Hugging Face][25])
* **Architecture & data:** ASR uses **wav2vec 2.0** self-supervised pretraining; training leveraged widely translated religious readings to reach many languages. This is why coverage is huge even with scarce labeled data. ([arXiv][27], [Hugging Face][25])
* **Latency & UX:** Out of the box, MMS is **not a turnkey realtime agent**; you add streaming chunks, VAD, and buffering to hit sub-second round-trip. Commercial stacks (Deepgram/Google/Azure) provide polished streaming endpoints already. (Docs show turnkey streaming for those.) ([Google Cloud][1], [Deepgram Docs][4], [Microsoft Learn][2])
* **Licensing:** MMS weights/code are **CC-BY-NC 4.0** (non-commercial). For commercial SaaS you’ll need permission or different models (e.g., Speechmatics/Deepgram/Google/Azure; or open-source like Whisper/Coqui with permissive licenses). ([파이토치 한국 사용자 모임][26])

**Bottom line:**

* Pick **MMS** when you need **long-tail language coverage** (pilot, research, humanitarian, or internal/non-commercial use) and you’re comfortable hosting models.
* Pick **cloud ASR/TTS** (Google/Azure/Deepgram + ElevenLabs/Play.ht) when you need **reliable realtime**, low ops burden, and commercial terms.
* Pick **on-prem** (NVIDIA Riva + Coqui/Whisper) when you need **data control** and SLA-grade performance on your own GPUs. ([NVIDIA Docs][7], [NVIDIA][18])

If you want, tell me your target languages (e.g., Twi), latency budget, and whether you prefer cloud vs on-prem—I’ll shortlist a concrete combo and wiring diagram for your agents.

[1]: https://cloud.google.com/speech-to-text/v2/docs/streaming-recognize?utm_source=chatgpt.com "Transcribe audio from streaming input"
[2]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/index-speech-to-text?utm_source=chatgpt.com "Speech to text documentation - Tutorials, API Reference"
[3]: https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html?utm_source=chatgpt.com "Transcribing streaming audio"
[4]: https://developers.deepgram.com/docs/live-streaming-audio?utm_source=chatgpt.com "Getting Started"
[5]: https://docs.speechmatics.com/speech-to-text/languages?utm_source=chatgpt.com "Languages"
[6]: https://help.openai.com/en/articles/7031512-whisper-audio-api-faq?utm_source=chatgpt.com "Whisper Audio API FAQ"
[7]: https://docs.nvidia.com/deeplearning/riva/user-guide/docs/asr/asr-performance.html?utm_source=chatgpt.com "Performance — NVIDIA Riva"
[8]: https://alphacephei.com/vosk/?utm_source=chatgpt.com "VOSK Offline Speech Recognition API"
[9]: https://cloud.google.com/text-to-speech/docs/ssml?utm_source=chatgpt.com "Speech Synthesis Markup Language (SSML)"
[10]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech?utm_source=chatgpt.com "Text to speech overview - Speech service - Azure AI services"
[11]: https://docs.aws.amazon.com/polly/latest/dg/neural-voices.html?utm_source=chatgpt.com "Neural voices - Amazon Polly"
[12]: https://elevenlabs.io/docs/product-guides/voices/voice-cloning/instant-voice-cloning?utm_source=chatgpt.com "Instant Voice Cloning | ElevenLabs Documentation"
[13]: https://docs.play.ht/?utm_source=chatgpt.com "Quickstart - Play.ht"
[14]: https://play.ht/?utm_source=chatgpt.com "#1 Free AI Voice Generator, Text to Speech, & AI Voice Over"
[15]: https://developers.deepgram.com/docs/tts-websocket-streaming?utm_source=chatgpt.com "Real-Time TTS with WebSockets"
[16]: https://docs.coqui.ai/en/latest/models/xtts.html?utm_source=chatgpt.com "TTS 0.22.0 documentation"
[17]: https://huggingface.co/coqui/XTTS-v2?utm_source=chatgpt.com "coqui/XTTS-v2"
[18]: https://www.nvidia.com/en-us/ai-data-science/products/riva/?utm_source=chatgpt.com "Riva | Speech and Translation AI"
[19]: https://docs.nvidia.com/nim/riva/tts/latest/performance.html?utm_source=chatgpt.com "Performance — NVIDIA NIM Riva TTS"
[20]: https://www.twilio.com/docs/voice/media-streams?utm_source=chatgpt.com "Media Streams Overview"
[21]: https://developers.telnyx.com/docs/voice/programmable-voice/media-streaming?utm_source=chatgpt.com "Media Streaming over Websockets"
[22]: https://telnyx.com/products/webrtc?utm_source=chatgpt.com "WebRTC Voice SDK: powering real-time communication"
[23]: https://developer.vonage.com/en/voice/voice-api/ncco-reference?utm_source=chatgpt.com "Vonage NCCO - API Reference"
[24]: https://ai.meta.com/blog/multilingual-model-speech-recognition/?utm_source=chatgpt.com "Introducing speech-to-text, text-to-speech, and more for ... - Meta AI"
[25]: https://huggingface.co/docs/transformers/en/model_doc/mms?utm_source=chatgpt.com "MMS"
[26]: https://discuss.pytorch.kr/t/meta-1100-mms-massively-multilingual-speech/1618 "Meta, 1100개 이상의 언어에 대한 음성-텍스트, 텍스트-음성 변환 모델 MMS(Massively Multilingual Speech) 공개 - 읽을거리&정보공유 - 파이토치 한국 사용자 모임"
[27]: https://arxiv.org/pdf/2305.13516?utm_source=chatgpt.com "Scaling speech technology to 1000+ languages"






    Meta’s MMS‑TTS project covers more than 1,000 languages and includes prebuilt voices for Ga (gaa), Ewe (ewe), Hausa (hau), and Dagbani (dag), making it a direct drop‑in alongside the existing Twi (aka) voice.

    Coqui XTTS‑v2 offers cross‑lingual, multispeaker synthesis; it can be fine‑tuned with modest training data to support Ga, Ewe, Hausa, or Dagbani if native voices are desired.

    Mainstream commercial services (e.g., Microsoft Azure, Google Cloud, or NVIDIA Riva) and open frameworks like Mozilla TTS/VITS can also be trained or configured to support these languages when paired with suitable datasets.





awesome — here’s a compact, **cloud vs. on-prem** view for the languages you named. I split STT and TTS so it’s readable, then explain where **Meta MMS** fits.

# STT (speech-to-text)

| Language       | Good cloud options                          | On-prem options                                                 | Notes                                                                                                                                                                                       |
| -------------- | ------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Twi (Akan)** | (none mainstream)                           | **Meta MMS ASR**, **Whisper (fine-tune)**                       | Akan is not widely offered by big cloud STT. MMS explicitly covers **Akan**; Whisper can work but typically needs domain data to reach good WER. ([dl.fbaipublicfiles.com][1]) ([arXiv][2]) |
| **Ewe**        | (none mainstream)                           | **Meta MMS ASR**, **Whisper (fine-tune)**                       | Similar story to Akan; MMS has coverage; Whisper quality improves with Ewe data. ([dl.fbaipublicfiles.com][1]) ([arXiv][2])                                                                 |
| **Ga**         | (very limited)                              | **Meta MMS ASR** (Ga/Dangme family), **Whisper (fine-tune)**    | Ga is low-resource in commercial STT; MMS lists Ga/Dangme family; expect to fine-tune. ([dl.fbaipublicfiles.com][1]) ([arXiv][2])                                                           |
| **Yorùbá**     | **Google STT v2 (yo-NG)**                   | **Meta MMS ASR**, **Whisper** (+ strong gains with Yorùbá data) | Google now lists Yorùbá; research shows Whisper/MMS improve a lot with Yorùbá datasets. ([Google Cloud][3], [arXiv][4])                                                                     |
| **Swahili**    | **AWS Transcribe**, **Speechmatics**        | **Meta MMS ASR**, **Whisper**                                   | Both AWS and Speechmatics support Swahili; on-prem options also solid. ([AWS Documentation][5])                                                                                             |
| **Xhosa**      | **Google STT v2 (xh-ZA)**, **Speechmatics** | **Meta MMS ASR**, **Whisper**                                   | Cloud support exists, but recent work still finds variability in Xhosa ASR quality; test on your audio. ([Google Cloud][3], [ACL Anthology][6])                                             |

# TTS (text-to-speech)

| Language       | Good cloud options                             | On-prem options                                                            | Notes                                                                                                                        |
| -------------- | ---------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Twi (Akan)** | (none mainstream)                              | **Meta MMS TTS**, **Coqui TTS** (ready-made Twi models), **BibleTTS** data | Coqui released Asante & Akuapem Twi models; MMS TTS also covers Akan. ([GitHub][7], [ISCA Archive][8], [Hugging Face][9])    |
| **Ewe**        | (none mainstream)                              | **Meta MMS TTS**, **Coqui TTS** (Ewe)                                      | Coqui shipped an Ewe TTS; MMS TTS supports Ewe. ([GitHub][7], [Hugging Face][9])                                             |
| **Ga**         | (none mainstream)                              | **Meta MMS TTS** (family coverage)                                         | Expect to fine-tune/curate voices; MMS has very broad coverage but quality varies by language. ([dl.fbaipublicfiles.com][1]) |
| **Yorùbá**     | (none mainstream)                              | **Meta MMS TTS**, **Coqui TTS** (Yorùbá)                                   | Coqui has Yorùbá voices; MMS TTS includes **yor**. ([GitHub][7], [Hugging Face][9])                                          |
| **Swahili**    | **Azure Neural TTS** (Kenya & Tanzania voices) | **Meta MMS TTS**                                                           | Azure lists multiple Swahili neural voices; MMS TTS is an offline alternative. ([JSON2Video][10], [Hugging Face][9])         |
| **Xhosa**      | (none mainstream)                              | **Meta MMS TTS**                                                           | Use MMS TTS or train with Coqui on Xhosa data. ([Hugging Face][9])                                                           |

---

## Where **Meta MMS** fits (and how it compares)

* **Coverage:** MMS spans *\~1,100+* languages for **ASR and TTS**, including **Akan (Twi)**, **Ewe**, **Yorùbá**, **Swahili**, and **Xhosa**—far beyond typical cloud catalogs. ([arXiv][2], [Hugging Face][9])
* **Quality:** Tremendous breadth, but quality varies by language and domain (many models were trained with read speech). For several low-resource African languages, MMS (and well-tuned Whisper) can outperform generic baselines, but you should benchmark on your audio. ([arXiv][2], [ACL Anthology][6])
* **Deployment:** Fully **on-prem/offline** — great for data privacy and low connectivity. (Hugging Face/FAIRSEQ checkpoints.) ([Hugging Face][9])
* **Licensing:** **MMS TTS** models are **CC-BY-NC 4.0** → *non-commercial* out of the box. For commercial TTS use, seek permission or use alternatives (e.g., Azure for Swahili or train Coqui with your own data). ([Hugging Face][9])

---

## Quick picks (cloud vs. on-prem)

* **Swahili:** Cloud **AWS Transcribe** (STT) + **Azure Neural TTS**; On-prem **MMS**/**Whisper** + **MMS TTS**. ([AWS Documentation][5], [JSON2Video][10])
* **Xhosa:** Cloud **Google STT v2**/**Speechmatics**; TTS via **MMS TTS** or train **Coqui**. ([Google Cloud][3])
* **Yorùbá:** Cloud **Google STT v2**; TTS via **Coqui** or **MMS TTS** (watch licensing). On-prem **Whisper/MMS** for STT performs well with local data. ([Google Cloud][3], [GitHub][7], [arXiv][4])
* **Twi (Akan), Ewe, Ga:** Go **on-prem first**: **MMS** (ASR+TTS) and **Coqui TTS** models (Twi/Ewe). For production, plan a small fine-tune with your accents/domain. ([GitHub][7], [dl.fbaipublicfiles.com][1])

---

### Extra references (language lists)

* **Google STT v2** now lists **Yorùbá (yo-NG)** and **Xhosa (xh-ZA)**. ([Google Cloud][3])
* **Speechmatics** language list includes **Swahili** (and other African languages).
* **AWS Transcribe** documents **Swahili** support. ([AWS Documentation][5])
* **Azure Neural TTS** has **Swahili** voices (KE, TZ). ([JSON2Video][10])
* **Coqui TTS** shipped models for **Ewe**, **Yorùbá**, **Asante/Akuapem Twi**; **BibleTTS** provides open Twi/Ewe/Yorùbá corpora. ([GitHub][7], [ISCA Archive][8])
* **MMS**: project paper + language coverage & TTS model card. ([arXiv][2], [dl.fbaipublicfiles.com][1], [Hugging Face][9])

---

If you want, I can tailor a **“pick & stack”** per language (SDKs, pricing, and deployment notes), or spin up a tiny Bake-off plan (5–10 audio mins per language) so you can see WER/voice naturalness before committing.

[1]: https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html "MMS"
[2]: https://arxiv.org/abs/2305.13516?utm_source=chatgpt.com "Scaling Speech Technology to 1,000+ Languages"
[3]: https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages?utm_source=chatgpt.com "Speech-to-Text V2 supported languages bookmark_border"
[4]: https://arxiv.org/abs/2505.20564?utm_source=chatgpt.com "The NaijaVoices Dataset: Cultivating Large-Scale, High-Quality, Culturally-Rich Speech Data for African Languages"
[5]: https://docs.aws.amazon.com/transcribe/latest/dg/charsets.html?utm_source=chatgpt.com "Character sets for custom vocabularies and vocabulary filters"
[6]: https://aclanthology.org/2025.cl4health-1.14.pdf?utm_source=chatgpt.com "Benchmarking IsiXhosa Automatic Speech Recognition ..."
[7]: https://github.com/coqui-ai/TTS/discussions/1513?utm_source=chatgpt.com "v0.6.2 models · coqui-ai TTS · Discussion #1513"
[8]: https://www.isca-archive.org/interspeech_2022/meyer22c_interspeech.pdf?utm_source=chatgpt.com "BibleTTS: a large, high-fidelity, multilingual, and uniquely ..."
[9]: https://huggingface.co/facebook/mms-tts "facebook/mms-tts · Hugging Face"
[10]: https://json2video.com/ai-voices/azure/voices/?utm_source=chatgpt.com "Azure Text to Speech - Voices List"




perfect — here’s your **shortlist (cloud vs. on-prem) per language** and a **bite-size bake-off plan** you can run this week.

# Picks & stacks (by language)

| Language       | Cloud STT (prod-ready)            | Cloud TTS (prod-ready)                           | On-prem STT                                  | On-prem TTS                                          | Notes                                                                                                                                                                                                              |
| -------------- | --------------------------------- | ------------------------------------------------ | -------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Twi (Akan)** | —                                 | —                                                | **Meta MMS ASR** or **Whisper** (fine-tuned) | **MMS TTS** (CC-BY-NC) or **Coqui TTS** (Twi models) | Twi not in major clouds yet; MMS covers Akan; Coqui shipped Asante/Akuapem Twi models; BibleTTS datasets help. ([arXiv][1], [GitHub][2], [Hugging Face][3])                                                        |
| **Ewe**        | —                                 | —                                                | **MMS ASR** or **Whisper** (fine-tuned)      | **MMS TTS** (CC-BY-NC) or **Coqui TTS** (Ewe)        | Similar to Twi; rely on MMS/Coqui + BibleTTS data. ([arXiv][1], [GitHub][2])                                                                                                                                       |
| **Ga**         | —                                 | —                                                | **MMS ASR**                                  | **MMS TTS**                                          | Low-resource commercially; MMS lists Ga/Dangme family. ([arXiv][1])                                                                                                                                                |
| **Yorùbá**     | **Google STT v2** (`yo-NG`)       | —                                                | **MMS ASR** or **Whisper**                   | **MMS TTS** or **Coqui TTS** (Yorùbá)                | Google v2 explicitly lists Yorùbá; Coqui released Yorùbá TTS; MMS has Yorùbá TTS. ([Google Cloud][4], [GitHub][2], [Hugging Face][5])                                                                              |
| **Swahili**    | **Google STT v2** (`sw`, `sw-KE`) | **Azure Neural TTS** (Zuri/Rafiki, Rehema/Daudi) | **MMS ASR** or **Whisper**                   | **MMS TTS**                                          | Google v2 lists Swahili; Azure ships multiple Swahili neural voices. (AWS Transcribe supports Swahili mostly as **batch**; check streaming fit.) ([Google Cloud][4], [Microsoft Learn][6], [AWS Documentation][7]) |
| **Xhosa**      | **Google STT v2** (`xh-ZA`)       | —                                                | **MMS ASR** or **Whisper**                   | **MMS TTS**                                          | Google v2 has Xhosa; for TTS use MMS or train Coqui. ([Google Cloud][4])                                                                                                                                           |

> **Licensing watch-out:** MMS models (ASR & TTS) are released under **CC-BY-NC 4.0** (non-commercial). For paid deployments, either secure permission or use permissively licensed/self-trained Coqui models. ([Hugging Face][8])

---

## Reference links (for the stacks above)

* **Google STT v2 language list** — shows **Yorùbá, Xhosa, Swahili** entries and codes. ([Google Cloud][4])
* **Azure Speech (language & voice support)** — lists **Swahili** voices (sw-KE Zuri/Rafiki; sw-TZ Rehema/Daudi). ([Microsoft Learn][6])
* **AWS Transcribe languages** — **Swahili** supported (mostly batch; verify streaming before choosing). ([AWS Documentation][7])
* **MMS (paper + model cards)** — **\~1,107 languages** ASR/TTS; **CC-BY-NC** license. ([arXiv][1], [Hugging Face][8])
* **Coqui African languages** — release notes and **Twi/Ewe/Yorùbá** TTS models + **BibleTTS** datasets. ([GitHub][2], [coqui.ai][9], [Hugging Face][10])

---

# Mini bake-off plan (5–10 mins audio per language)

**Goal:** pick a production combo per language with measured **WER**, **latency**, and **TTS naturalness**.

1. **Data prep (same utterances across systems)**

* Record 5–10 min per language (2 speakers, mixed accents; telephony 8 kHz + wideband 16 kHz).
* Add **domain words** (names, places, policy terms). For Twi/Ewe/Yorùbá use a subset from **BibleTTS** + your campaign/business phrases. ([Hugging Face][10])

2. **ASR tracks (simultaneous)**

* **Cloud track:** Google STT v2 streaming (codes: `yo-NG`, `xh-ZA`, `sw`/`sw-KE`).
* **On-prem track:** Whisper (or **faster-whisper**) vs **MMS ASR** on a single GPU; run both on the same audio.

**Measure:**

* **Latency:** end-to-end round-trip (mic→partial transcript ms).
* **Accuracy:** **WER/CER** vs reference.
* **Robustness:** code-switching, names, noisy segments.

3. **TTS tracks**

* **Cloud (where available):** Azure Swahili voices (sw-KE, sw-TZ).
* **On-prem:** **MMS TTS** and **Coqui XTTS** (few-sec voice cloning) with the same test sentences.

**Rate:** subjective **MOS** (1–5) on clarity, prosody, and identity match.

4. **Telephony realism**

* Pipe both tracks through your SIP/WebRTC: Twilio/Telnyx or your trunk, at 8 kHz, to see degradation and barge-in behavior.

5. **Decide & document**

* Pick per language: **(STT engine, TTS engine, telephony path)** + **fallback**.
* Note license: MMS = **non-commercial**; Coqui/BibleTTS models and data have **open licenses** (often **CC-BY-SA**; check per model). ([Hugging Face][10])

---

## My recommended default wiring (keeps your stack consistent)

* **Yorùbá / Xhosa / Swahili (cloud-first):**
  Telephony/WebRTC → **Google STT v2 (streaming)** → LLM agent → **Azure TTS** (Swahili) or on-prem TTS where cloud isn’t available → back to call. ([Google Cloud][4], [Microsoft Learn][6])

* **Twi / Ewe / Ga (on-prem-first):**
  Telephony/WebRTC → **MMS ASR** (or **Whisper** fine-tuned) → LLM agent → **Coqui XTTS** (preferred for commercial) or **MMS TTS** (non-commercial) → back to call. ([Hugging Face][11], [arXiv][1])

If you want, I’ll turn this into a **checklist + docker-compose** that spins up MMS/Whisper/XTTS locally and a tiny Node gateway for Google/Azure so you can run the bake-off in one go.

[1]: https://arxiv.org/pdf/2305.13516?utm_source=chatgpt.com "Scaling speech technology to 1000+ languages"
[2]: https://github.com/coqui-ai/TTS/discussions/1513?utm_source=chatgpt.com "v0.6.2 models · coqui-ai TTS · Discussion #1513"
[3]: https://huggingface.co/datasets/hci-lab-dcug/bibletts-asante-twi-max29secs-total9hrs-sr22050?utm_source=chatgpt.com "hci-lab-dcug/bibletts-asante-twi-max29secs-total9hrs- ..."
[4]: https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages "Speech-to-Text V2 supported languages  |  Cloud Speech-to-Text V2 documentation  |  Google Cloud"
[5]: https://huggingface.co/facebook/mms-tts-yor?utm_source=chatgpt.com "facebook/mms-tts-yor"
[6]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support "Language support - Speech service - Azure AI services | Microsoft Learn"
[7]: https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html "Supported languages and language-specific features - Amazon Transcribe"
[8]: https://huggingface.co/facebook/mms-tts?utm_source=chatgpt.com "facebook/mms-tts"
[9]: https://coqui.ai/blog/tts/african-languages-dataset-collaboration/?utm_source=chatgpt.com "Data and models for African langauges / Blog / Coqui"
[10]: https://huggingface.co/papers/2207.03546?utm_source=chatgpt.com "Paper page - BibleTTS: a large, high-fidelity, multilingual ..."
[11]: https://huggingface.co/coqui/XTTS-v2?utm_source=chatgpt.com "coqui/XTTS-v2"




Great question. Think of **Asterisk** and **FreeSWITCH** as your own on-prem/cloud PBX/SBC/media servers. With **Vapi** in the mix, you only need them if you want specific control/features that Vapi doesn’t aim to be (queues, SIP phones, conferencing, custom dialplans), or when a carrier forces a topology where you must terminate the trunk yourself.

## Where they fit (three common patterns)

1. **Pure Vapi (no Asterisk/FreeSWITCH) — simplest**

* **Flow:** AirtelTigo → Vapi (SIP URI) → your Vapi agent → (optional) transfer to mobile/PSTN.
* **Use when:** You just need AI IVR/agents, recordings, transcripts, and PSTN—fastest go-live.
* **Asterisk/FS role:** Not used.

2. **PBX behind Vapi — agents on SIP extensions**

* **Flow:** AirtelTigo → Vapi (AI front door) → transfer/bridge to **Asterisk/FS** extensions (1001, 1002, …) or queues.
* **Use when:** You want **SIP hardphones/softphones**, hunt groups, call queues, ring strategies, internal extension dialing, call center stats.
* **Setup notes:**

  * Keep AirtelTigo trunk **direct to Vapi**.
  * Vapi transfers calls to `sip:1001@pbx.yourdomain.com` (your **FS/Asterisk**).
  * Your PBX handles agent login/queues/recordings; Vapi still gives you transcripts and AI.

3. **PBX/SBC in front of Vapi — when the carrier requires it (VPN or IP-auth quirks)**

* **Flow:** AirtelTigo → **Asterisk/FreeSWITCH** (as SBC) → Vapi (BYO SIP trunk)
* **Use when:** AirtelTigo insists on **VPN/registration** or a dedicated enterprise edge, or you want **topology hiding, header normalization, transcoding (e.g., G.729)**.
* **Setup notes:**

  * Add your **Asterisk/FS public IP** as an allowed **gateway** in the Vapi credential.
  * Your PBX forwards inbound DID calls to `sip:+233…@<credentialId>.sip.vapi.ai`.
  * Extra hop = more to manage; only do this if you must.

## What each is best at

* **Asterisk:** classic PBX features (queues, IVR, AMI/ARI for custom logic), simple call center, SIP phones.
* **FreeSWITCH:** high-scale media (conferencing, wide codec support), robust B2BUA, great as an SBC/media server.
* **Both:** can register to carriers, do header rewrites, NAT traversal, **SRTP/TLS**, **DTMF**, recording, and **G.729** (licensing/codec modules permitting).

## Quick decision guide

* **Just AI campaigns/IVR with AirtelTigo numbers?** Use **Pure Vapi**.
* **Need SIP agents/queues/internal extensions?** Put **Asterisk/FS behind Vapi** and transfer calls to extensions.
* **Carrier forcing VPN/registration to your gear?** Put **Asterisk/FS in front** as an SBC and forward to Vapi.

If you tell me which of the three you want, I can generate a starter config (e.g., FreeSWITCH `dialplan` + Sofia profile or Asterisk `pjsip.conf` + `extensions.conf`) to route calls to/from Vapi and AirtelTigo.

