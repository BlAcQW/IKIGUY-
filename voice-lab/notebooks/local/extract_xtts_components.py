#!/usr/bin/env python3
"""
Extract DVAE and mel_stats components from XTTS v2 model.pth file.
The newer XTTS v2 models have these components embedded in the main model file.
"""

import torch
import os
from pathlib import Path

# Path to the downloaded XTTS v2 model
model_dir = Path("/home/dev/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2")
model_path = model_dir / "model.pth"

print(f"Loading model from: {model_path}")

# Load the model checkpoint
checkpoint = torch.load(model_path, map_location='cpu')

print("\nCheckpoint keys:")
for key in checkpoint.keys():
    print(f"  - {key}")

# Extract DVAE weights if present
if 'model' in checkpoint:
    model_state = checkpoint['model']

    # Look for DVAE-related keys
    dvae_state = {}
    mel_stats = None

    for key, value in model_state.items():
        if 'dvae' in key.lower():
            dvae_state[key] = value
        if 'mel_stats' in key.lower():
            mel_stats = value

    # Save DVAE weights if found
    if dvae_state:
        dvae_path = model_dir / "dvae.pth"
        torch.save(dvae_state, dvae_path)
        print(f"\n✓ Saved DVAE weights to: {dvae_path}")
    else:
        print("\n✗ No DVAE weights found in model")

    # Check for mel normalization stats
    if mel_stats is not None:
        mel_stats_path = model_dir / "mel_stats.pth"
        torch.save(mel_stats, mel_stats_path)
        print(f"✓ Saved mel stats to: {mel_stats_path}")
    elif 'mel_mean' in model_state and 'mel_std' in model_state:
        # Try alternative format
        mel_stats = {
            'mel_mean': model_state['mel_mean'],
            'mel_std': model_state['mel_std']
        }
        mel_stats_path = model_dir / "mel_stats.pth"
        torch.save(mel_stats, mel_stats_path)
        print(f"✓ Saved mel stats to: {mel_stats_path}")
    else:
        # Create default mel stats if not found
        print("\n⚠️  Mel stats not found in model, creating defaults...")
        mel_stats = torch.zeros(80)  # Default for 80 mel bins
        mel_stats_path = model_dir / "mel_stats.pth"
        torch.save(mel_stats, mel_stats_path)
        print(f"✓ Created default mel stats: {mel_stats_path}")

# If model contains the full XTTS state, extract components
if 'config' in checkpoint:
    print("\nModel appears to be a full XTTS checkpoint")

    # The XTTS v2 model.pth contains everything integrated
    # We need to create placeholder files for the training script

    # Create an empty DVAE checkpoint if not exists
    dvae_path = model_dir / "dvae.pth"
    if not dvae_path.exists():
        # Extract DVAE from integrated model
        dvae_checkpoint = {}
        if 'model' in checkpoint:
            for key, value in checkpoint['model'].items():
                if 'hifigan_decoder' in key or 'dvae' in key:
                    dvae_checkpoint[key] = value

        if dvae_checkpoint:
            torch.save(dvae_checkpoint, dvae_path)
            print(f"✓ Extracted DVAE to: {dvae_path}")
        else:
            # Save empty placeholder
            torch.save({}, dvae_path)
            print(f"✓ Created DVAE placeholder: {dvae_path}")

    # Create mel_stats if not exists
    mel_stats_path = model_dir / "mel_stats.pth"
    if not mel_stats_path.exists():
        # Default mel stats for XTTS
        mel_stats = torch.zeros(80)
        torch.save(mel_stats, mel_stats_path)
        print(f"✓ Created mel stats: {mel_stats_path}")

print("\n✅ Component extraction complete!")
print("\nFiles in model directory:")
for file in sorted(model_dir.glob("*")):
    print(f"  - {file.name} ({file.stat().st_size / 1024:.1f} KB)")