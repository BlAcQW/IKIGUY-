# Whisper + PEFT LoRA Training Fix

## Problem

When training Whisper models with PEFT LoRA, the following error occurred:

```
TypeError: WhisperForConditionalGeneration.forward() got an unexpected keyword argument 'input_ids'
```

## Root Cause

The issue was caused by setting `task_type=TaskType.SEQ_2_SEQ_LM` in the `LoraConfig`. This caused PEFT to wrap the Whisper model with `PeftModelForSeq2SeqLM`, which is designed for text-to-text models that use `input_ids` (like T5, BART).

Whisper is a speech-to-text model that uses `input_features` (mel spectrograms) as input, NOT `input_ids`. The PEFT wrapper was trying to inject `input_ids` into the forward pass, causing the error.

## Solution

**Remove the `task_type` parameter from `LoraConfig`** to use the base `PeftModel` class instead:

### Before (Broken):
```python
lora_config = LoraConfig(
    r=config.lora_r,
    lora_alpha=config.lora_alpha,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=config.lora_dropout,
    bias="none",
    task_type=TaskType.SEQ_2_SEQ_LM  # ❌ This breaks Whisper!
)
```

### After (Fixed):
```python
lora_config = LoraConfig(
    r=config.lora_r,
    lora_alpha=config.lora_alpha,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=config.lora_dropout,
    bias="none"
    # task_type removed - let PEFT use base PeftModel ✅
)
```

## References

- GitHub Issue: https://github.com/huggingface/peft/issues/1988
- Fix confirmed by multiple users in the PEFT repository
- Quote from PEFT maintainer: "There's currently no specific task for a model like Whisper. It is a sequence-to-sequence model but when using WhisperForConditionalGeneration it is not a language model."

## Environment

- `peft==0.12.0`
- `transformers==4.43.0`
- `accelerate==0.34.0`
- Model: `openai/whisper-large-v3`

## Date Fixed

2025-10-22
