#!/bin/bash
# Data Preparation Script for RunPod
# Prepares Twi-Fante data for MeloTTS training

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Preparing Twi-Fante Data for MeloTTS Training         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Configuration
SOURCE_DATA="/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full"
DEST_DATA="/workspace/data/twi_full"

# Check if source data exists
if [ ! -d "${SOURCE_DATA}" ]; then
    echo "❌ Error: Source data not found at ${SOURCE_DATA}"
    exit 1
fi

# Create destination directory
mkdir -p "${DEST_DATA}"

# Copy data files
echo "📦 Copying data files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Copy config (optimized version)
if [ -f "${SOURCE_DATA}/config.json" ]; then
    cp "${SOURCE_DATA}/config.json" "${DEST_DATA}/config.json"
    echo "✓ Copied config.json"
fi

# Copy training and validation lists
if [ -f "${SOURCE_DATA}/train.list" ]; then
    cp "${SOURCE_DATA}/train.list" "${DEST_DATA}/train.list"
    TRAIN_COUNT=$(wc -l < "${DEST_DATA}/train.list")
    echo "✓ Copied train.list (${TRAIN_COUNT} samples)"
fi

if [ -f "${SOURCE_DATA}/val.list" ]; then
    cp "${SOURCE_DATA}/val.list" "${DEST_DATA}/val.list"
    VAL_COUNT=$(wc -l < "${DEST_DATA}/val.list")
    echo "✓ Copied val.list (${VAL_COUNT} samples)"
fi

# Copy audio files
if [ -d "${SOURCE_DATA}/train_wavs" ]; then
    echo ""
    echo "📁 Copying audio files (this may take a while)..."
    mkdir -p "${DEST_DATA}/train_wavs"
    rsync -avh --progress "${SOURCE_DATA}/train_wavs/" "${DEST_DATA}/train_wavs/"
    AUDIO_COUNT=$(find "${DEST_DATA}/train_wavs" -name "*.wav" | wc -l)
    AUDIO_SIZE=$(du -sh "${DEST_DATA}/train_wavs" | cut -f1)
    echo "✓ Copied ${AUDIO_COUNT} audio files (${AUDIO_SIZE})"
fi

if [ -d "${SOURCE_DATA}/val_wavs" ]; then
    mkdir -p "${DEST_DATA}/val_wavs"
    rsync -avh --progress "${SOURCE_DATA}/val_wavs/" "${DEST_DATA}/val_wavs/"
    echo "✓ Copied validation audio files"
fi

echo ""
echo "✅ Data preparation complete!"
echo ""
echo "📊 Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Destination: ${DEST_DATA}"
echo "Training samples: ${TRAIN_COUNT}"
echo "Validation samples: ${VAL_COUNT}"
echo "Total audio files: ${AUDIO_COUNT}"
echo "Total size: ${AUDIO_SIZE}"
echo ""
echo "🚀 Ready to train!"
echo "Run: bash train_on_runpod.sh"
