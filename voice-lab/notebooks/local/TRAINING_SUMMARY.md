# Twi TTS Model Training - Archive

> **⚠️ OUTDATED DOCUMENTATION**
> This file contains historical information from an earlier training approach.
> **For current MeloTTS training instructions, see:** `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/MELOTTS_TWI_TRAINING.md`

---

## Current Training Approach (2025-10-07)

**Sample Rate**: 44.1kHz (MeloTTS standard)
**Dataset**: Full Twi dataset (212K training + 11K validation)
**Architecture**: VITS-based with BERT embeddings
**Documentation**: See `MELOTTS_TWI_TRAINING.md` for complete guide

---

## Historical Summary (Archive)

This section contains information from a previous training iteration using 16kHz audio. The information below is **no longer current** but preserved for reference.

### Previous Issues (Now Resolved with New Approach)

The old training approach had several issues:
1. **Sampling Rate**: Used 16kHz (now using 44.1kHz standard)
2. **Dataset Size**: Used 50K-100K samples (now using full 212K dataset)
3. **Memory Leaks**: Evaluation slowdowns (resolved in new architecture)
4. **Data Preparation**: Complex resampling pipeline (simplified in new approach)

### Migration to Current System

All training has been migrated to the new MeloTTS-based system with:
- Native 44.1kHz audio processing
- Complete dataset utilization (212K samples)
- Optimized BERT embedding pipeline
- Improved training stability

---

## For Current Training Instructions

**See:** `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/MELOTTS_TWI_TRAINING.md`

**Key Files:**
- Data preparation: `/opt/kasaai/apps/voice-lab/notebooks/local/prepare_twi_full_dataset.py`
- BERT embeddings: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/preprocess_text_melo_tts.py`
- Training: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/train.sh`
- Configuration: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full/config.json`

---

**Last Updated**: 2025-10-07
**Status**: Archived - See MELOTTS_TWI_TRAINING.md for current documentation
