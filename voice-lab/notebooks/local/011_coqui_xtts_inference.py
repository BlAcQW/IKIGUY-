#!/usr/bin/env python3
"""
Coqui XTTS Inference Script for Twi Language
Generate speech from Twi text using trained XTTS model
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

print("=" * 80)
print("🎤 COQUI XTTS INFERENCE FOR TWI LANGUAGE")
print("=" * 80)

class XTTSInference:
    """XTTS inference handler."""

    def __init__(self, model_path: str, config_path: str = None):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path) if config_path else None
        self.model = None
        self.config = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Load trained XTTS model."""
        print(f"\n📥 Loading model from: {self.model_path}")

        # Load config
        if self.config_path and self.config_path.exists():
            self.config = XttsConfig()
            self.config.load_json(str(self.config_path))
        else:
            # Try to find config in model directory
            config_file = self.model_path.parent / 'config.json'
            if config_file.exists():
                self.config = XttsConfig()
                self.config.load_json(str(config_file))
            else:
                raise ValueError(f"Config file not found. Expected at {config_file}")

        # Initialize model
        self.model = Xtts.init_from_config(self.config)
        self.model.load_checkpoint(self.config, checkpoint_path=str(self.model_path), eval=True)

        # Move to device
        self.model.to(self.device)

        print(f"   ✅ Model loaded successfully on {self.device}")

    def synthesize(
        self,
        text: str,
        speaker_wav: str,
        language: str = "tw",
        output_path: str = None,
        temperature: float = 0.65,
        length_penalty: float = 1.0,
        repetition_penalty: float = 2.0,
        top_k: int = 50,
        top_p: float = 0.85,
    ):
        """
        Synthesize speech from text.

        Args:
            text: Twi text to synthesize
            speaker_wav: Path to reference speaker audio
            language: Language code (default: 'tw' for Twi)
            output_path: Path to save output audio
            temperature: Sampling temperature (higher = more random)
            length_penalty: Length penalty for beam search
            repetition_penalty: Penalty for repeated tokens
            top_k: Top-k sampling
            top_p: Nucleus sampling threshold
        """
        print(f"\n🎙️  Synthesizing: '{text}'")

        if not Path(speaker_wav).exists():
            raise ValueError(f"Speaker reference not found: {speaker_wav}")

        # Prepare output path
        if output_path is None:
            output_dir = Path('output/tts')
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"twi_tts_{timestamp}.wav"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute speaker latents from reference
        print(f"   🔊 Computing speaker embedding from: {speaker_wav}")
        gpt_cond_latent, speaker_embedding = self.model.get_conditioning_latents(
            audio_path=[speaker_wav]
        )

        # Generate speech
        print(f"   🔄 Generating speech...")
        outputs = self.model.inference(
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            temperature=temperature,
            length_penalty=length_penalty,
            repetition_penalty=repetition_penalty,
            top_k=top_k,
            top_p=top_p,
        )

        # Save audio
        torchaudio.save(
            str(output_path),
            torch.tensor(outputs["wav"]).unsqueeze(0),
            24000,
        )

        print(f"   ✅ Audio saved to: {output_path}")

        return str(output_path)

    def batch_synthesize(
        self,
        text_file: str,
        speaker_wav: str,
        output_dir: str = "output/tts_batch",
        language: str = "tw",
    ):
        """
        Synthesize speech for multiple texts from a file.

        Args:
            text_file: Path to file with texts (one per line)
            speaker_wav: Path to reference speaker audio
            output_dir: Directory to save output files
            language: Language code
        """
        print(f"\n📄 Batch synthesis from: {text_file}")

        text_path = Path(text_file)
        if not text_path.exists():
            raise ValueError(f"Text file not found: {text_file}")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Read texts
        with open(text_path, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]

        print(f"   Found {len(texts)} texts to synthesize")

        results = []

        for i, text in enumerate(texts, 1):
            print(f"\n[{i}/{len(texts)}]")
            output_file = output_path / f"output_{i:04d}.wav"

            try:
                result_path = self.synthesize(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=language,
                    output_path=str(output_file),
                )
                results.append({'text': text, 'output': result_path, 'status': 'success'})
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({'text': text, 'output': None, 'status': 'failed', 'error': str(e)})

        # Save results manifest
        manifest_path = output_path / 'synthesis_results.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Batch synthesis complete!")
        print(f"   Results saved to: {manifest_path}")

        # Print summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        print(f"\n📊 Summary:")
        print(f"   Total: {len(results)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")

        return results

def main():
    """Main inference pipeline."""
    parser = argparse.ArgumentParser(description='XTTS Inference for Twi')
    parser.add_argument('--model', type=str, required=True, help='Path to model checkpoint')
    parser.add_argument('--config', type=str, help='Path to model config (optional)')
    parser.add_argument('--text', type=str, help='Twi text to synthesize')
    parser.add_argument('--text_file', type=str, help='File with multiple texts (one per line)')
    parser.add_argument('--speaker', type=str, required=True, help='Path to speaker reference audio')
    parser.add_argument('--output', type=str, help='Output audio file path')
    parser.add_argument('--output_dir', type=str, default='output/tts_batch', help='Output directory for batch')
    parser.add_argument('--language', type=str, default='tw', help='Language code')
    parser.add_argument('--temperature', type=float, default=0.65, help='Sampling temperature')

    args = parser.parse_args()

    # Validate inputs
    if not args.text and not args.text_file:
        parser.error("Either --text or --text_file must be provided")

    # Initialize inference
    print(f"\n⚙️  Initializing XTTS inference...")
    print(f"   Model: {args.model}")
    print(f"   Speaker reference: {args.speaker}")
    print(f"   Language: {args.language}")
    print(f"   Temperature: {args.temperature}")

    inference = XTTSInference(args.model, args.config)
    inference.load_model()

    # Run inference
    if args.text:
        # Single text synthesis
        output_path = inference.synthesize(
            text=args.text,
            speaker_wav=args.speaker,
            language=args.language,
            output_path=args.output,
            temperature=args.temperature,
        )

        print(f"\n✅ Synthesis complete!")
        print(f"   Output: {output_path}")

    elif args.text_file:
        # Batch synthesis
        results = inference.batch_synthesize(
            text_file=args.text_file,
            speaker_wav=args.speaker,
            output_dir=args.output_dir,
            language=args.language,
        )

    print("\n" + "=" * 80)
    print("🏁 INFERENCE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
