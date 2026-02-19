#!/bin/bash
"""
OpenVoice Voice Cloning Test - Juliet Bawuah
Tests voice cloning with both Twi and English text
"""

set -e

# Configuration
REFERENCE_VOICE="/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav"
TWI_TEXT="Wo tumi de Ghana kasa Twi no di dwuma ma w'adwen mu nsɛm adi mu yiye. Twi yɛ kasa a ɛda so reyɛ den wɔ Amansan mu, na ɛma nnipa tumi kasa ahotɔ mu na wɔte wɔn ho ase. Sɛ yɛde Twi ka nsɛm a, ɛma yɛtumi kyerɛ yɛn amammerɛ."
ENGLISH_TEXT="You can use the Ghanaian language Twi for effective communication in your daily life. Twi is a language that continues to thrive in the nation, and it allows people to speak comfortably and understand each other. When we speak in Twi, we can express our culture, values and excellence."
OPENVOICE_API="http://localhost:8003"
OUTPUT_DIR="/opt/kasaai/apps/voice-lab/clones/openvoice"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}OpenVoice Voice Cloning Test${NC}"
echo -e "${BLUE}=========================================${NC}\n"

# Check reference voice exists
if [ ! -f "$REFERENCE_VOICE" ]; then
    echo -e "${RED}Error: Reference voice not found: $REFERENCE_VOICE${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Reference voice found${NC}"

# Check OpenVoice API health
echo -e "\n${BLUE}Checking OpenVoice API...${NC}"
if ! curl -s -f "$OPENVOICE_API/health" > /dev/null; then
    echo -e "${RED}Error: OpenVoice API not responding${NC}"
    exit 1
fi
echo -e "${GREEN}✓ OpenVoice API healthy${NC}\n"

# =============================================
# Test 1: Twi Text
# =============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Test 1: Juliet + Twi Text${NC}"
echo -e "${BLUE}=========================================${NC}\n"

OUTPUT_TWI="$OUTPUT_DIR/juliet_openvoice_twi_${TIMESTAMP}.wav"

echo -e "Synthesizing Twi text with voice cloning..."
echo -e "Text: ${TWI_TEXT:0:100}...\n"

curl -X POST "$OPENVOICE_API/clone_voice" \
    -F "text=$TWI_TEXT" \
    -F "reference_audio=@$REFERENCE_VOICE" \
    -F "language=English" \
    -F "speed=1.0" \
    --output "$OUTPUT_TWI" \
    --progress-bar

if [ -f "$OUTPUT_TWI" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_TWI" | cut -f1)
    DURATION=$(ffmpeg -i "$OUTPUT_TWI" 2>&1 | grep "Duration" | awk '{print $2}' | tr -d ',')
    echo -e "\n${GREEN}✓ Twi test complete${NC}"
    echo -e "  File: $OUTPUT_TWI"
    echo -e "  Size: $FILE_SIZE"
    echo -e "  Duration: $DURATION"
else
    echo -e "\n${RED}✗ Twi test failed${NC}"
fi

# =============================================
# Test 2: English Text
# =============================================
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}Test 2: Juliet + English Text${NC}"
echo -e "${BLUE}=========================================${NC}\n"

OUTPUT_ENG="$OUTPUT_DIR/juliet_openvoice_english_${TIMESTAMP}.wav"

echo -e "Synthesizing English text with voice cloning..."
echo -e "Text: ${ENGLISH_TEXT:0:100}...\n"

curl -X POST "$OPENVOICE_API/clone_voice" \
    -F "text=$ENGLISH_TEXT" \
    -F "reference_audio=@$REFERENCE_VOICE" \
    -F "language=English" \
    -F "speed=1.0" \
    --output "$OUTPUT_ENG" \
    --progress-bar

if [ -f "$OUTPUT_ENG" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_ENG" | cut -f1)
    DURATION=$(ffmpeg -i "$OUTPUT_ENG" 2>&1 | grep "Duration" | awk '{print $2}' | tr -d ',')
    echo -e "\n${GREEN}✓ English test complete${NC}"
    echo -e "  File: $OUTPUT_ENG"
    echo -e "  Size: $FILE_SIZE"
    echo -e "  Duration: $DURATION"
else
    echo -e "\n${RED}✗ English test failed${NC}"
fi

# =============================================
# Summary
# =============================================
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}=========================================${NC}\n"

echo -e "Reference Voice: $REFERENCE_VOICE"
echo -e "Output Directory: $OUTPUT_DIR\n"

echo -e "Generated Files:"
for file in "$OUTPUT_DIR"/juliet_openvoice_*_${TIMESTAMP}.wav; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        DUR=$(ffmpeg -i "$file" 2>&1 | grep "Duration" | awk '{print $2}' | tr -d ',')
        echo -e "  ${GREEN}✓${NC} $(basename "$file") - $SIZE - $DUR"
    fi
done

echo -e "\n${BLUE}=========================================${NC}\n"
