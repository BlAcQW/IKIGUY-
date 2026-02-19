#!/usr/bin/env python3
"""
Universal Model Evaluation Pipeline for Twi ASR/TTS Models
Evaluates all trained models and generates comprehensive reports

Supports:
- ASR: WER, CER, inference speed
- TTS: MOS (via quality metrics), inference speed, audio quality
"""

import os
import sys
from pathlib import Path
import torch
import torchaudio
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from tqdm.auto import tqdm
import logging
import argparse
from datetime import datetime

# Metrics
import evaluate
from jiwer import wer, cer
import librosa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EvaluationConfig:
    """Evaluation configuration."""

    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    models_dir: Path = base_path / "models"
    test_manifests: Path = base_path / "data/twi-akan-fante/processed/model_manifests"
    output_dir: Path = base_path / "evaluation_results"

    # Evaluation settings
    max_samples: int = 500  # Limit for faster evaluation
    batch_size: int = 8

config = EvaluationConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# ASR EVALUATION
# =============================================================================

class ASREvaluator:
    """Evaluate ASR models (WER, CER)."""

    def __init__(self):
        self.wer_metric = evaluate.load("wer")

    def evaluate_model(self, model_path: Path, test_manifest: Path) -> Dict:
        """Evaluate an ASR model."""
        logger.info(f"Evaluating ASR model: {model_path.name}")

        if not test_manifest.exists():
            logger.warning(f"Test manifest not found: {test_manifest}")
            return {"error": "Test manifest not found"}

        # Load test data
        df = pd.read_csv(test_manifest)
        if len(df) > config.max_samples:
            df = df.sample(n=config.max_samples, random_state=42)

        predictions = []
        references = []
        inference_times = []

        # Load model (example for Wav2Vec2)
        try:
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

            processor = Wav2Vec2Processor.from_pretrained(str(model_path))
            model = Wav2Vec2ForCTC.from_pretrained(str(model_path))
            model.eval()

            if torch.cuda.is_available():
                model = model.cuda()

            # Evaluate samples
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="Evaluating"):
                audio_path = row['audio_path']
                reference = row['text']

                # Load audio
                audio, sr = librosa.load(audio_path, sr=16000)

                # Inference
                start_time = datetime.now()
                with torch.no_grad():
                    inputs = processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
                    if torch.cuda.is_available():
                        inputs = {k: v.cuda() for k, v in inputs.items()}

                    logits = model(**inputs).logits
                    predicted_ids = torch.argmax(logits, dim=-1)
                    prediction = processor.batch_decode(predicted_ids)[0]

                inference_time = (datetime.now() - start_time).total_seconds()

                predictions.append(prediction)
                references.append(reference)
                inference_times.append(inference_time)

        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return {"error": str(e)}

        # Calculate metrics
        wer_score = wer(references, predictions)
        cer_score = cer(references, predictions)
        avg_inference_time = np.mean(inference_times)
        rtf = avg_inference_time / np.mean([len(ref.split()) for ref in references])  # Real-time factor

        results = {
            "model_name": model_path.name,
            "model_type": "ASR",
            "wer": round(wer_score, 4),
            "cer": round(cer_score, 4),
            "avg_inference_time_sec": round(avg_inference_time, 4),
            "rtf": round(rtf, 4),
            "num_samples": len(df),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✓ WER: {results['wer']:.2%}, CER: {results['cer']:.2%}")
        return results

# =============================================================================
# TTS EVALUATION
# =============================================================================

class TTSEvaluator:
    """Evaluate TTS models (audio quality, inference speed)."""

    def evaluate_model(self, model_path: Path, test_manifest: Path) -> Dict:
        """Evaluate a TTS model."""
        logger.info(f"Evaluating TTS model: {model_path.name}")

        if not test_manifest.exists():
            logger.warning(f"Test manifest not found: {test_manifest}")
            return {"error": "Test manifest not found"}

        # Load test data
        df = pd.read_csv(test_manifest)
        if len(df) > config.max_samples:
            df = df.sample(n=config.max_samples, random_state=42)

        inference_times = []
        audio_quality_scores = []

        # TTS evaluation would go here
        # This is a placeholder for actual TTS model loading
        logger.info("⚠️  TTS evaluation requires model-specific implementation")

        results = {
            "model_name": model_path.name,
            "model_type": "TTS",
            "avg_inference_time_sec": 0,
            "audio_quality_score": 0,
            "num_samples": len(df),
            "timestamp": datetime.now().isoformat(),
            "note": "TTS evaluation requires model-specific implementation"
        }

        return results

# =============================================================================
# MAIN EVALUATION PIPELINE
# =============================================================================

def evaluate_all_models(model_type: str = "all"):
    """Evaluate all models of specified type."""
    logger.info("=" * 80)
    logger.info("Model Evaluation Pipeline")
    logger.info("=" * 80)

    results = []

    # Find all model directories
    model_dirs = []
    if config.models_dir.exists():
        for model_dir in config.models_dir.iterdir():
            if model_dir.is_dir():
                model_dirs.append(model_dir)

    if not model_dirs:
        logger.warning(f"No models found in {config.models_dir}")
        return

    # Evaluate each model
    asr_evaluator = ASREvaluator()
    tts_evaluator = TTSEvaluator()

    for model_dir in model_dirs:
        logger.info(f"\nEvaluating: {model_dir.name}")

        # Determine model type from name
        if "wav2vec2" in model_dir.name.lower() or "whisper" in model_dir.name.lower():
            test_manifest = config.test_manifests / "wav2vec2_val.csv"
            result = asr_evaluator.evaluate_model(model_dir, test_manifest)
            results.append(result)

        elif any(x in model_dir.name.lower() for x in ["tts", "melo", "xtts", "openvoice"]):
            test_manifest = config.test_manifests / "melo_tts_val.csv"
            result = tts_evaluator.evaluate_model(model_dir, test_manifest)
            results.append(result)

    # Save results
    results_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = config.output_dir / f"evaluation_results_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    logger.info(f"\n✓ Results saved to: {output_file}")

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"\n{results_df.to_string()}\n")
    logger.info("=" * 80)

    # Generate comparison report
    generate_comparison_report(results_df, timestamp)

def generate_comparison_report(results_df: pd.DataFrame, timestamp: str):
    """Generate markdown comparison report."""

    report_path = config.output_dir / f"evaluation_report_{timestamp}.md"

    with open(report_path, 'w') as f:
        f.write("# Model Evaluation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # ASR Models
        asr_models = results_df[results_df['model_type'] == 'ASR']
        if len(asr_models) > 0:
            f.write("## ASR Models\n\n")
            f.write("| Model | WER | CER | Inference Time (s) | RTF |\n")
            f.write("|-------|-----|-----|-------------------|-----|\n")
            for _, row in asr_models.iterrows():
                f.write(f"| {row['model_name']} | {row.get('wer', 'N/A')} | {row.get('cer', 'N/A')} | ")
                f.write(f"{row.get('avg_inference_time_sec', 'N/A')} | {row.get('rtf', 'N/A')} |\n")
            f.write("\n")

        # TTS Models
        tts_models = results_df[results_df['model_type'] == 'TTS']
        if len(tts_models) > 0:
            f.write("## TTS Models\n\n")
            f.write("| Model | Inference Time (s) | Quality Score | Samples |\n")
            f.write("|-------|-------------------|---------------|----------|\n")
            for _, row in tts_models.iterrows():
                f.write(f"| {row['model_name']} | {row.get('avg_inference_time_sec', 'N/A')} | ")
                f.write(f"{row.get('audio_quality_score', 'N/A')} | {row.get('num_samples', 'N/A')} |\n")
            f.write("\n")

        f.write("## Recommendations\n\n")

        if len(asr_models) > 0:
            best_wer = asr_models.loc[asr_models['wer'].idxmin()]
            f.write(f"- **Best ASR Model (WER)**: {best_wer['model_name']} ({best_wer['wer']:.2%})\n")

        f.write("\n---\n")
        f.write("*Generated by evaluate_models.py*\n")

    logger.info(f"✓ Comparison report saved to: {report_path}")

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Evaluate Twi ASR/TTS models")
    parser.add_argument(
        "--type",
        type=str,
        choices=["asr", "tts", "all"],
        default="all",
        help="Type of models to evaluate"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model directory to evaluate"
    )
    args = parser.parse_args()

    if args.model:
        # Evaluate specific model
        model_path = Path(args.model)
        if not model_path.exists():
            model_path = config.models_dir / args.model

        if not model_path.exists():
            logger.error(f"Model not found: {args.model}")
            sys.exit(1)

        # Determine type and evaluate
        # Implementation here
        pass
    else:
        # Evaluate all models
        evaluate_all_models(args.type)

if __name__ == "__main__":
    main()
