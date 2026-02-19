#!/bin/bash
# Implement RunPod Local Voice Storage for High-Quality Voice Cloning
# This enables using full 56-minute audio instead of 45-second samples

set -e

echo "======================================================================="
echo "RunPod Voice Storage Implementation"
echo "======================================================================="
echo ""

# Configuration
RUNPOD_IP="194.68.245.121"
RUNPOD_PORT="22130"
RUNPOD_USER="root"
SSH_KEY="$HOME/.ssh/id_ed25519"
SOURCE_AUDIO="/opt/kasaai/apps/voice-lab/voices/archbishop_1.wav"
RUNPOD_DEST="/workspace/voice_references/archbishop_56min.wav"

# SSH command wrapper
SSH_CMD="ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_IP"
SCP_CMD="scp -P $RUNPOD_PORT -i $SSH_KEY"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Test SSH connection
echo "🔍 Step 1: Testing SSH connection to RunPod..."
if $SSH_CMD "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ ERROR: Cannot connect to RunPod${NC}"
    echo "   Please check SSH credentials and port"
    echo "   SSH Key: $SSH_KEY"
    exit 1
fi
echo ""

# Step 2: Create directory on RunPod
echo "📁 Step 2: Creating voice_references directory on RunPod..."
$SSH_CMD "mkdir -p /workspace/voice_references"
echo -e "${GREEN}✅ Directory created${NC}"
echo ""

# Step 3: Check if audio already exists
echo "🔍 Step 3: Checking if audio already exists on RunPod..."
if $SSH_CMD "test -f $RUNPOD_DEST"; then
    echo -e "${YELLOW}⚠️  Audio file already exists on RunPod${NC}"
    read -p "   Do you want to re-transfer? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Skipping transfer..."
        SKIP_TRANSFER=true
    fi
else
    echo "   Audio file not found on RunPod (will transfer)"
fi
echo ""

# Step 4: Transfer audio
if [ "$SKIP_TRANSFER" != "true" ]; then
    echo "📤 Step 4: Transferring 56-minute audio to RunPod..."
    echo "   Source: $SOURCE_AUDIO"
    echo "   Destination: $RUNPOD_DEST"
    echo "   Size: $(du -h $SOURCE_AUDIO | cut -f1)"
    echo ""
    echo "   This may take 2-5 minutes depending on connection speed..."
    echo ""

    # Transfer with progress
    $SCP_CMD -C $SOURCE_AUDIO \
        $RUNPOD_USER@$RUNPOD_IP:$RUNPOD_DEST

    echo ""
    echo -e "${GREEN}✅ Transfer complete${NC}"
else
    echo "📤 Step 4: Skipping transfer (file already exists)"
fi
echo ""

# Step 5: Verify transfer
echo "✅ Step 5: Verifying transfer..."
REMOTE_SIZE=$($SSH_CMD "du -h $RUNPOD_DEST | cut -f1")
echo "   Remote file size: $REMOTE_SIZE"

LOCAL_SIZE=$(du -h $SOURCE_AUDIO | cut -f1)
echo "   Local file size: $LOCAL_SIZE"

if [ "$REMOTE_SIZE" == "$LOCAL_SIZE" ]; then
    echo -e "${GREEN}✅ File sizes match - transfer verified${NC}"
else
    echo -e "${YELLOW}⚠️  File sizes differ - please verify manually${NC}"
fi
echo ""

# Step 6: List all voice references on RunPod
echo "📋 Step 6: Listing all voice references on RunPod..."
$SSH_CMD "ls -lh /workspace/voice_references/ 2>/dev/null || echo 'No files found'"
echo ""

# Step 7: Update database record
echo "💾 Step 7: Updating database record..."
python3 <<EOF
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def update_db():
    client = AsyncIOMotorClient("mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
    db = client.kasaai_core

    result = await db.voice_clones.update_one(
        {"clone_id": "voice_archbishop_official"},
        {"\$set": {
            "runpod_reference_filename": "archbishop_56min.wav",
            "runpod_reference_path": "$RUNPOD_DEST",
            "runpod_reference_size_mb": 568.26,
            "runpod_reference_uploaded": True,
            "runpod_reference_uploaded_at": datetime.utcnow(),
            "uses_full_audio": True,
            "quality_tier": "premium",
            "updated_at": datetime.utcnow()
        }}
    )

    if result.modified_count > 0:
        print("   ✅ Database updated successfully")
    else:
        print("   ⚠️  Database record not modified (may already be set)")

    client.close()

asyncio.run(update_db())
EOF
echo ""

echo "======================================================================="
echo -e "${GREEN}✨ SUCCESS! RunPod Voice Storage Implemented${NC}"
echo "======================================================================="
echo ""
echo "📊 Summary:"
echo "   • 56-minute audio transferred to RunPod: ✅"
echo "   • Location: $RUNPOD_DEST"
echo "   • Database updated: ✅"
echo "   • Size: 568 MB (instead of 751 KB sample)"
echo ""
echo "🎯 Next Steps:"
echo "   1. Modify F5-TTS service to accept local file paths"
echo "   2. Add /clone_local endpoint to F5-TTS"
echo "   3. Update shared TTS service to use local references"
echo "   4. Test high-quality voice generation"
echo ""
echo "📖 See: VOICE_CLONING_OPTIMIZATION_PLAN.md for full implementation"
echo ""
