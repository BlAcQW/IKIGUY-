#!/usr/bin/env python3
"""
Transformers compatibility patch for TTS library.
Fixes the LogitsWarper import issue with newer transformers versions.
"""

import sys
from transformers.generation import LogitsProcessor

# Create alias for backward compatibility
LogitsWarper = LogitsProcessor

# Monkey-patch transformers module
sys.modules['transformers'].LogitsWarper = LogitsProcessor

print("✅ Transformers compatibility patch applied: LogitsWarper -> LogitsProcessor")