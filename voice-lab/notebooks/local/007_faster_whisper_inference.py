#!/usr/bin/env python3
"""
Faster Whisper Inference Script for Twi
Transcribe Twi audio using fine-tuned Whisper model
"""

import argparse
from pathlib import Path
import torch
import torchaudio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    pipeline
)
import json
from typing import Dict, List

print("=" * 80)
print("🎤 FASTER WHISPER INFERENCE FOR TWI")
print("=" * 80)

class WhisperInference:
    """Whisper inference handler for Twi."""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"\n📥 Loading model from: {self.model_path}")
        print(f"🔥 Device: {self.device}")

        # Load model and processor
        self.processor = WhisperProcessor.from_pretrained(str(self.model_path))
        self.model = WhisperForConditionalGeneration.from_pretrained(str(self.model_path))
        self.model.to(self.device)
        self.model.eval()

        print("✅ Model loaded successfully")

    def transcribe(
        self,
        audio_path: str,
        language: str = "tw",
        task: str = "transcribe",
        return_timestamps: bool = False
    ) -> Dict:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file
            language: Language code (default: 'tw' for Twi)
            task: 'transcribe' or 'translate'
            return_timestamps: Include word-level timestamps

        Returns:
            Dictionary with transcription and metadata
        """
        print(f"\n🎙️  Transcribing: {audio_path}")

        # Load audio
        audio_array, sample_rate = torchaudio.load(audio_path)

        # Resample to 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            audio_array = resampler(audio_array)
            sample_rate = 16000

        # Convert to mono if stereo
        if audio_array.shape[0] > 1:
            audio_array = audio_array.mean(dim=0, keepdim=True)

        # Process audio
        input_features = self.processor(
            audio_array.squeeze().numpy(),
            sampling_rate=sample_rate,
            return_tensors="pt"
        ).input_features.to(self.device)

        # Generate transcription
        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                language=language,
                task=task,
                return_timestamps=return_timestamps
            )

        # Decode
        transcription = self.processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0]

        result = {
            'text': transcription,
            'audio_path': str(audio_path),
            'language': language,
            'task': task,
            'duration': audio_array.shape[1] / sample_rate
        }

        print(f"   ✅ Transcription: \"{transcription}\"")

        return result

    def transcribe_batch(
        self,
        audio_files: List[str],
        output_path: str = None
    ) -> List[Dict]:
        """Transcribe multiple audio files."""
        print(f"\n📄 Batch transcription: {len(audio_files)} files")

        results = []

        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n[{i}/{len(audio_files)}]")

            try:
                result = self.transcribe(audio_file)
                results.append(result)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'text': '',
                    'audio_path': str(audio_file),
                    'error': str(e)
                })

        # Save results if output path specified
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Results saved to: {output_file}")

        return results

def main():
    """Main inference pipeline."""
    parser = argparse.ArgumentParser(description='Whisper Inference for Twi')

    parser.add_argument('--model', type=str, required=True,
                       help='Path to fine-tuned model')
    parser.add_argument('--audio', type=str,
                       help='Path to audio file to transcribe')
    parser.add_argument('--audio_list', type=str,
                       help='Path to file with list of audio files')
    parser.add_argument('--output', type=str,
                       help='Output JSON file path')
    parser.add_argument('--language', type=str, default='tw',
                       help='Language code (default: tw)')
    parser.add_argument('--task', type=str, default='transcribe',
                       choices=['transcribe', 'translate'],
                       help='Task type')
    parser.add_argument('--timestamps', action='store_true',
                       help='Include timestamps in output')

    args = parser.parse_args()

    # Validate inputs
    if not args.audio and not args.audio_list:
        parser.error("Either --audio or --audio_list must be provided")

    # Initialize inference
    inference = WhisperInference(args.model)

    # Run inference
    if args.audio:
        # Single file transcription
        result = inference.transcribe(
            args.audio,
            language=args.language,
            task=args.task,
            return_timestamps=args.timestamps
        )

        # Save result if output specified
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Result saved to: {output_file}")

    elif args.audio_list:
        # Batch transcription
        with open(args.audio_list, 'r') as f:
            audio_files = [line.strip() for line in f if line.strip()]

        results = inference.transcribe_batch(
            audio_files,
            output_path=args.output
        )

        print(f"\n✅ Transcribed {len(results)} files")

    print("\n" + "=" * 80)
    print("🏁 INFERENCE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
