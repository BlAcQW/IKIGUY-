#!/bin/bash
"""
Voice Cloning Script using Coqui TTS API
Uses the running Coqui Docker container's API to generate voice clones
"""

set -e

# Configuration
REFERENCE_VOICE="/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav"
TWI_TEXT_FILE="/opt/kasaai/apps/voice-lab/voices/text/twi_text_1.md"
TWI_TEXT_FILE_SHORT="/opt/kasaai/apps/voice-lab/voices/text/twi_text_1_short.md"
OUTPUT_DIR="/opt/kasaai/apps/voice-lab/clones/coqui"
COQUI_API="http://localhost:8005"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Voice Cloning with Coqui TTS API${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Check if reference voice exists
if [ ! -f "$REFERENCE_VOICE" ]; then
    echo -e "${RED}Error: Reference voice not found: $REFERENCE_VOICE${NC}"
    exit 1
fi

# Load Twi text
if [ ! -f "$TWI_TEXT_FILE" ]; then
    echo -e "${RED}Error: Twi text file not found: $TWI_TEXT_FILE${NC}"
    exit 1
fi

TWI_TEXT=$(cat "$TWI_TEXT_FILE")
echo -e "${GREEN}✓ Loaded Twi text (${#TWI_TEXT} characters)${NC}"
echo -e "Text preview: ${TWI_TEXT:0:100}...\n"

# Check Coqui API health
echo -e "${BLUE}Checking Coqui API health...${NC}"
if ! curl -s -f "$COQUI_API/health" > /dev/null; then
    echo -e "${RED}Error: Coqui API not responding at $COQUI_API${NC}"
    echo -e "${RED}Make sure the Coqui container is running: docker ps | grep coqui${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Coqui API is healthy${NC}\n"

# List available models
echo -e "${BLUE}Checking available models...${NC}"
curl -s "$COQUI_API/models" | python3 -m json.tool
echo ""

# ===================================================================
# Generate with default XTTS v2 model
# ===================================================================
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Generating with XTTS v2 model${NC}"
echo -e "${BLUE}=================================${NC}\n"

OUTPUT_FILE_V2="$OUTPUT_DIR/juliet_xtts_v2_${TIMESTAMP}.wav"

echo -e "Synthesizing with XTTS v2..."
curl -X POST "$COQUI_API/synthesize_with_reference" \
    -F "text=$TWI_TEXT" \
    -F "reference_audio=@$REFERENCE_VOICE" \
    -F "language=en" \
    -F "temperature=0.7" \
    -F "speed=1.0" \
    --output "$OUTPUT_FILE_V2" \
    --progress-bar

if [ -f "$OUTPUT_FILE_V2" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE_V2" | cut -f1)
    echo -e "\n${GREEN}✓ XTTS v2 output saved: $OUTPUT_FILE_V2 ($FILE_SIZE)${NC}"
else
    echo -e "\n${RED}✗ Failed to generate XTTS v2 output${NC}"
fi

# ===================================================================
# Try to switch to Twi model if available
# ===================================================================
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Attempting to use Twi model${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Check if Twi model exists
if [ -d "/opt/kasaai/apps/voice-lab/models/xtts_twi_v1_inference" ]; then
    echo -e "Switching to Twi model..."

    # Try to switch model via API
    SWITCH_RESULT=$(curl -s -X POST "$COQUI_API/models/switch" \
        -H "Content-Type: application/json" \
        -d '{"model_id": "xtts_twi_v1_inference"}')

    echo "$SWITCH_RESULT" | python3 -m json.tool

    # Check if switch was successful
    if echo "$SWITCH_RESULT" | grep -q "success"; then
        echo -e "\n${GREEN}✓ Switched to Twi model${NC}\n"

        # Generate with Twi model (using shorter text due to 250 char limit)
        # Note: Twi model uses 'en' language code despite being trained on Twi
        TWI_TEXT_SHORT=$(cat "$TWI_TEXT_FILE_SHORT")
        OUTPUT_FILE_TWI="$OUTPUT_DIR/juliet_twi_model_${TIMESTAMP}.wav"

        echo -e "Synthesizing with Twi model (using 'en' language code and short text <250 chars)..."
        echo -e "Text length: ${#TWI_TEXT_SHORT} characters"
        curl -X POST "$COQUI_API/synthesize_with_reference" \
            -F "text=$TWI_TEXT_SHORT" \
            -F "reference_audio=@$REFERENCE_VOICE" \
            -F "language=en" \
            -F "temperature=0.7" \
            -F "speed=1.0" \
            --output "$OUTPUT_FILE_TWI" \
            --progress-bar

        if [ -f "$OUTPUT_FILE_TWI" ]; then
            FILE_SIZE=$(du -h "$OUTPUT_FILE_TWI" | cut -f1)
            echo -e "\n${GREEN}✓ Twi model output saved: $OUTPUT_FILE_TWI ($FILE_SIZE)${NC}"
        else
            echo -e "\n${RED}✗ Failed to generate Twi model output${NC}"
        fi

        # Switch back to default model
        echo -e "\nSwitching back to XTTS v2..."
        curl -s -X POST "$COQUI_API/models/switch" \
            -H "Content-Type: application/json" \
            -d '{"model_id": "xtts_v2"}' > /dev/null
    else
        echo -e "\n${RED}✗ Failed to switch to Twi model${NC}"
    fi
else
    echo -e "${RED}Twi model not found at /opt/kasaai/apps/voice-lab/models/xtts_twi_v1_inference${NC}"
    echo -e "Skipping Twi model generation..."
fi

# ===================================================================
# Summary
# ===================================================================
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}VOICE CLONING COMPLETE${NC}"
echo -e "${BLUE}=================================${NC}\n"

echo -e "Reference voice: $REFERENCE_VOICE"
echo -e "Output directory: $OUTPUT_DIR\n"
echo -e "Generated files:"

for file in "$OUTPUT_DIR"/juliet_*_${TIMESTAMP}.wav; do
    if [ -f "$file" ]; then
        FILE_SIZE=$(du -h "$file" | cut -f1)
        echo -e "  ${GREEN}✓${NC} $(basename "$file") ($FILE_SIZE)"
    fi
done

echo -e "\n${BLUE}=================================${NC}\n"
