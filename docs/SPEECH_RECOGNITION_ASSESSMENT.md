# AgriMind — Hindi & Marathi Speech Recognition & Voice Assessment

**Date:** October 19, 2026  
**Document Status:** Architectural Investigation & Verification Report  
**Phase:** Phase 7 — Hindi and Marathi Voice Assistant  

---

## 1. Executive Summary

This document evaluates speech recognition (STT) and speech synthesis (TTS) capabilities for Hindi (`hi-IN`) and Marathi (`mr-IN`) within AgriMind, contrasting browser-native Web Speech APIs with open-source server-side models such as AI4Bharat IndicConformer.

**Key Finding:**  
Browser-native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition` and `speechSynthesis`) delivers zero-latency, zero-cost, and zero-storage voice interactions on the vast majority of mobile and desktop browsers used by Indian farmers (notably Chrome on Android). For unsupported environments or client platforms lacking native Marathi TTS voice packs, AgriMind enforces graceful runtime fallbacks (editable transcript verification, fallback system voices, and full typed text input) without adding expensive, resource-heavy backend model dependencies.

---

## 2. Browser & Platform Support Matrix

| Platform / Browser | Speech Recognition (`hi-IN`) | Speech Recognition (`mr-IN`) | Speech Synthesis (TTS) | Remarks |
| :--- | :--- | :--- | :--- | :--- |
| **Chrome on Android** | **Supported** (Google Cloud) | **Supported** (Google Cloud) | **Supported** (System Indic voices) | Optimal target for farmers. High accuracy on colloquial agricultural terms. |
| **Chrome / Edge (Desktop Windows/macOS)** | **Supported** (Google/Microsoft Cloud) | **Supported** (Google Cloud) | **Variable** (`hi-IN` common; `mr-IN` requires language pack) | Speech recognition works well online. If Marathi TTS is absent, AgriMind falls back to Hindi/Indic voice with user notification. |
| **Safari (iOS / macOS)** | **Partial** (`hi-IN` supported) | **Unsupported / Unreliable** | **Supported** (`hi-IN` native) | Safari does not reliably support Marathi recognition. AgriMind flags this via `language-not-supported` and falls back to typed input. |
| **Firefox (Desktop / Android)** | **Disabled by default** | **Disabled by default** | **Supported** (OS voices) | Web Speech recognition is disabled by default in Firefox config. AgriMind falls back cleanly to typed input. |

---

## 3. Privacy, Data Retention & Cost Profile

1. **No Backend Audio Ingestion:**
   - AgriMind does not record, stream, or store farmer audio recordings on the backend.
   - Recognition is performed entirely on the client through the browser's native API.
2. **Cloud Speech Service Disclosure:**
   - Chrome, Edge, and Safari route speech audio through their respective vendor cloud services (Google, Microsoft, Apple) to transcribe speech.
   - AgriMind includes an explicit in-app Privacy & Voice Notice explaining that audio may be processed by the browser vendor and that an active internet connection is required.
3. **Zero Additional Cost:**
   - No paid third-party speech API keys (e.g. Google Cloud Speech-to-Text or Azure Speech) are required.

---

## 4. Open-Source Alternative Investigation: AI4Bharat IndicConformer

For environments where browser-based speech recognition cannot adequately support Marathi or where offline air-gapped deployments are required, open-source models were assessed:

### AI4Bharat IndicConformer (ASR)
- **Model Overview:** Developed by AI4Bharat (IIT Madras), trained on 10,000+ hours of Indian speech covering 22 scheduled Indian languages, including Hindi and Marathi.
- **Architecture:** Conformer (convolution-augmented Transformer) optimized for Indic phonetics and accented speech.
- **Model Size:** ~250M to 600M parameters (checkpoint sizes: ~1.2 GB to 2.4 GB).
- **Compute & Memory Requirements:**
  - **RAM:** Minimum 4 GB to 8 GB dedicated memory for model inference.
  - **CPU Latency:** 2.0s to 5.5s per 5-second audio snippet on modern multi-core x86/ARM CPUs.
  - **GPU Latency:** < 250ms on NVIDIA T4 / V100 / A10.
- **Licensing:** MIT / CC BY 4.0 (permits commercial and educational use).

### Tradeoff Assessment & Architectural Recommendation

| Dimension | Browser-Native Web Speech API (AgriMind Phase 7) | Self-Hosted AI4Bharat IndicConformer |
| :--- | :--- | :--- |
| **Deployment Footprint** | **0 MB added to container image** | +2.5 GB to 4.0 GB container image |
| **Server RAM Requirement** | **Baseline 250 MB (FastAPI)** | Minimum 4 GB – 8 GB dedicated |
| **Hosting Cost Impact** | **$0 / month** | +$35 to $90 / month for GPU/High-RAM instance |
| **Farmer Experience** | Instant, interactive transcription on mobile devices | Network audio upload latency + server queuing delay |
| **Privacy** | Audio processed by browser vendor cloud | Audio remains strictly within private container |
| **Marathi Accuracy** | High on Android Chrome; limited on Safari | Consistently high across all clients |

**Decision:**
For Phase 7, the browser-native Web Speech API with editable transcript review, clear runtime state management, and reliable typed fallback is the optimal choice for cost-efficiency, speed, and farmer usability. If future enterprise or government deployments demand air-gapped offline speech recognition, IndicConformer can be introduced as an optional containerized sidecar service.

---

## 5. Acceptance Verification

1. **Transcript Editable Before Sending:** The captured transcript populates the text field, allowing the farmer to review and correct misheard crop or nutrient names before submitting.
2. **Spoken Output & Stop Controls:** Assistant messages offer an inline "Read aloud" button with audio wave indicators and a global "Stop audio" button.
3. **Microphone Indicator Safety:** Recognition stops cleanly on `onend`, `onerror`, or manual cancellation, ensuring the mic indicator never stays active.
4. **Typed Fallback:** Farmers can type their question at any time, even when voice recognition is unavailable.
5. **Deterministic Safeguards:** Translating explanations into Hindi or Marathi never modifies underlying soil test values, crop scores, or fertilizer recommendations.
